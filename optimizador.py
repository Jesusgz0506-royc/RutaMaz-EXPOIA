import math
import networkx as nx
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds


def distancia_haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def tiempo_traslado_pulmonia(dist_km: float) -> int:
    if dist_km < 0.4:
        return 4
    return max(5, round((dist_km / 25.0) * 60 + 4))


def costo_traslado_pulmonia(dist_km: float) -> int:
    if dist_km < 0.4:
        return 0
    tarifa = 60.0 + max(0.0, dist_km - 2.0) * 14.0
    return int(round(tarifa / 5.0) * 5)


def construir_grafo_mazatlan(lugares: list) -> nx.Graph:
    G = nx.Graph()
    for l in lugares:
        G.add_node(l["id"], **l)

    for i in range(len(lugares)):
        for j in range(i + 1, len(lugares)):
            u, v = lugares[i], lugares[j]
            dist = distancia_haversine_km(u["lat"], u["lon"], v["lat"], v["lon"])
            t_viaje = tiempo_traslado_pulmonia(dist)
            c_viaje = costo_traslado_pulmonia(dist)
            G.add_edge(u["id"], v["id"], distancia_km=round(dist, 2), tiempo_min=t_viaje, costo_mxn=c_viaje)
    return G


def ordenar_ruta_astar(G: nx.Graph, seleccionados: list, punto_inicio: dict = None) -> tuple:
    if not seleccionados:
        return [], [], 0, 0, 0.0

    def heuristica(id_a, id_b):
        na, nb = G.nodes[id_a], G.nodes[id_b]
        return tiempo_traslado_pulmonia(distancia_haversine_km(na["lat"], na["lon"], nb["lat"], nb["lon"]))

    ruta_ordenada = []
    tramos = []
    tiempo_traslado_total = 0
    costo_traslado_total = 0
    distancia_total = 0.0

    if punto_inicio is not None:
        pendientes = seleccionados[:]
        actual_lat = punto_inicio["lat"]
        actual_lon = punto_inicio["lon"]
        actual_nombre = punto_inicio["nombre"]
        es_primer_tramo = True

        while pendientes:
            mejor_siguiente = None
            mejor_tiempo = float("inf")
            mejor_dist = 0.0
            mejor_costo = 0

            for candidato in pendientes:
                if es_primer_tramo:
                    dist = round(distancia_haversine_km(actual_lat, actual_lon, candidato["lat"], candidato["lon"]), 2)
                    t_tramo = tiempo_traslado_pulmonia(dist)
                    c_tramo = costo_traslado_pulmonia(dist)
                else:
                    camino = nx.astar_path(G, ruta_ordenada[-1]["id"], candidato["id"], heuristic=heuristica, weight="tiempo_min")
                    edge_data = G.get_edge_data(camino[0], camino[-1])
                    dist = edge_data["distancia_km"]
                    t_tramo = edge_data["tiempo_min"]
                    c_tramo = edge_data["costo_mxn"]

                if t_tramo < mejor_tiempo:
                    mejor_tiempo = t_tramo
                    mejor_dist = dist
                    mejor_costo = c_tramo
                    mejor_siguiente = candidato

            tramos.append({
                "es_inicio": es_primer_tramo,
                "desde": actual_nombre,
                "hasta": mejor_siguiente["nombre"],
                "lat_desde": actual_lat,
                "lon_desde": actual_lon,
                "lat_hasta": mejor_siguiente["lat"],
                "lon_hasta": mejor_siguiente["lon"],
                "distancia_km": mejor_dist,
                "tiempo_min": mejor_tiempo,
                "costo_mxn": mejor_costo,
            })
            ruta_ordenada.append(mejor_siguiente)
            pendientes.remove(mejor_siguiente)
            tiempo_traslado_total += mejor_tiempo
            costo_traslado_total += mejor_costo
            distancia_total += mejor_dist

            actual_lat = mejor_siguiente["lat"]
            actual_lon = mejor_siguiente["lon"]
            actual_nombre = mejor_siguiente["nombre"]
            es_primer_tramo = False

        return ruta_ordenada, tramos, tiempo_traslado_total, costo_traslado_total, round(distancia_total, 2)

    pendientes = sorted(seleccionados, key=lambda x: x["lat"])
    ruta_ordenada = [pendientes.pop(0)]

    while pendientes:
        actual = ruta_ordenada[-1]
        mejor_siguiente = None
        mejor_tiempo = float("inf")
        mejor_dist = 0.0
        mejor_costo = 0

        for candidato in pendientes:
            camino = nx.astar_path(G, actual["id"], candidato["id"], heuristic=heuristica, weight="tiempo_min")
            edge_data = G.get_edge_data(camino[0], camino[-1])
            t_tramo = edge_data["tiempo_min"]
            if t_tramo < mejor_tiempo:
                mejor_tiempo = t_tramo
                mejor_dist = edge_data["distancia_km"]
                mejor_costo = edge_data["costo_mxn"]
                mejor_siguiente = candidato

        ruta_ordenada.append(mejor_siguiente)
        pendientes.remove(mejor_siguiente)
        tramos.append({
            "es_inicio": False,
            "desde": actual["nombre"],
            "hasta": mejor_siguiente["nombre"],
            "lat_desde": actual["lat"],
            "lon_desde": actual["lon"],
            "lat_hasta": mejor_siguiente["lat"],
            "lon_hasta": mejor_siguiente["lon"],
            "distancia_km": mejor_dist,
            "tiempo_min": mejor_tiempo,
            "costo_mxn": mejor_costo,
        })
        tiempo_traslado_total += mejor_tiempo
        costo_traslado_total += mejor_costo
        distancia_total += mejor_dist

    return ruta_ordenada, tramos, tiempo_traslado_total, costo_traslado_total, round(distancia_total, 2)


def generar_plan_turistico(
    lugares: list,
    presupuesto: int,
    tiempo_disponible_min: int,
    zona: str = None,
    categoria: str = None,
    max_paradas: int = 5,
    punto_inicio: dict = None,
    incluir_transporte: bool = True,
) -> dict:
    candidatos = lugares[:]
    if zona and zona != "Todas las zonas":
        candidatos = [l for l in candidatos if l["zona"] == zona]
    if categoria and categoria != "Todas":
        candidatos = [l for l in candidatos if l["categoria"] == categoria]

    presupuesto_aprox = presupuesto * 1.15
    opciones_compatibles = [
        l for l in candidatos
        if l["precio"] <= presupuesto_aprox and l["tiempo_min"] <= tiempo_disponible_min
    ]
    opciones_compatibles.sort(key=lambda x: (-x["calificacion"], x["precio"]))

    elegibles = [
        l for l in candidatos
        if l["precio"] <= presupuesto and l["tiempo_min"] <= tiempo_disponible_min
    ]

    if not elegibles:
        descartados = []
        for l in candidatos:
            motivo = (
                f"Costo (${l['precio']}) excede presupuesto (${presupuesto})"
                if l["precio"] > presupuesto
                else f"Visita ({l['tiempo_min']} min) excede tiempo libre ({tiempo_disponible_min} min)"
            )
            descartados.append({
                "Lugar": l["nombre"],
                "Zona": l["zona"],
                "Costo": f"${l['precio']} MXN",
                "Tiempo": f"{l['tiempo_min']} min",
                "Motivo": motivo,
            })

        return {
            "ruta": [],
            "tramos": [],
            "opciones_compatibles": opciones_compatibles,
            "descartados": descartados,
            "costo_actividades": 0,
            "costo_transporte_total": 0,
            "costo_total": 0,
            "tiempo_visita_total": 0,
            "tiempo_traslado_total": 0,
            "tiempo_global_total": 0,
            "distancia_total_km": 0.0,
            "detalle_pulp": {
                "estado": "Infactible / Sin coincidencias estrictas",
                "candidatos_evaluados": len(candidatos),
                "restriccion_presupuesto": presupuesto,
                "restriccion_tiempo_min": tiempo_disponible_min,
            },
        }

    m = len(elegibles)
    c = -np.array([float(l["calificacion"]) for l in elegibles], dtype=float)
    integrality = np.ones(m, dtype=float)
    bounds = Bounds(lb=np.zeros(m, dtype=float), ub=np.ones(m, dtype=float))

    costo_tramo_est = 60.0 if incluir_transporte else 0.0
    holgura_costo = 0.0 if (incluir_transporte and punto_inicio is not None) else costo_tramo_est
    holgura_tiempo = 0.0 if punto_inicio is not None else 12.0

    A = np.array(
        [
            [float(l["precio"]) + costo_tramo_est for l in elegibles],
            [float(l["tiempo_min"] + 12) for l in elegibles],
            [1.0 for _ in elegibles],
        ],
        dtype=float,
    )
    lb = np.array([-np.inf, -np.inf, -np.inf], dtype=float)
    ub = np.array([float(presupuesto) + holgura_costo, float(tiempo_disponible_min) + holgura_tiempo, float(max_paradas)], dtype=float)

    resultado = milp(c=c, integrality=integrality, bounds=bounds, constraints=LinearConstraint(A, lb, ub))

    if resultado.success and resultado.x is not None:
        seleccionados = [elegibles[i] for i in range(m) if resultado.x[i] > 0.5]
        estado_solver = "Optimal (MILP HiGHS)"
    else:
        seleccionados = []
        gasto_acum, tiempo_acum = 0, 0
        for l in sorted(elegibles, key=lambda item: -item["calificacion"]):
            extra_c = int(costo_tramo_est) if (seleccionados or punto_inicio) else 0
            extra_t = 12 if (seleccionados or punto_inicio) else 0
            if (
                len(seleccionados) < max_paradas
                and gasto_acum + l["precio"] + extra_c <= presupuesto
                and tiempo_acum + l["tiempo_min"] + extra_t <= tiempo_disponible_min
            ):
                seleccionados.append(l)
                gasto_acum += l["precio"] + extra_c
                tiempo_acum += l["tiempo_min"] + extra_t
        estado_solver = "Optimal (Heurística de respaldo)"

    G = construir_grafo_mazatlan(lugares)
    ruta_ordenada, tramos, t_traslado, c_traslado, dist_km = ordenar_ruta_astar(G, seleccionados, punto_inicio=punto_inicio)

    while len(ruta_ordenada) > 1:
        c_act = sum(p["precio"] for p in ruta_ordenada)
        c_transp = c_traslado if incluir_transporte else 0
        t_visita = sum(p["tiempo_min"] for p in ruta_ordenada)
        if (c_act + c_transp <= presupuesto) and (t_visita + t_traslado <= tiempo_disponible_min):
            break
        peor = min(ruta_ordenada, key=lambda p: p["calificacion"])
        ruta_ordenada.remove(peor)
        ruta_ordenada, tramos, t_traslado, c_traslado, dist_km = ordenar_ruta_astar(G, ruta_ordenada, punto_inicio=punto_inicio)

    if len(ruta_ordenada) == 1:
        p0 = ruta_ordenada[0]
        c_tot_0 = p0["precio"] + (c_traslado if incluir_transporte else 0)
        t_tot_0 = p0["tiempo_min"] + t_traslado
        if c_tot_0 > presupuesto or t_tot_0 > tiempo_disponible_min:
            alternativa_valida = None
            for cand in sorted(elegibles, key=lambda item: -item["calificacion"]):
                r_test, tr_test, tt_test, ct_test, dk_test = ordenar_ruta_astar(G, [cand], punto_inicio=punto_inicio)
                if (
                    cand["precio"] + (ct_test if incluir_transporte else 0) <= presupuesto
                    and cand["tiempo_min"] + tt_test <= tiempo_disponible_min
                ):
                    alternativa_valida = (r_test, tr_test, tt_test, ct_test, dk_test)
                    break
            if alternativa_valida:
                ruta_ordenada, tramos, t_traslado, c_traslado, dist_km = alternativa_valida
            else:
                ruta_ordenada, tramos, t_traslado, c_traslado, dist_km = [], [], 0, 0, 0.0

    costo_actividades = sum(p["precio"] for p in ruta_ordenada)
    costo_transporte_total = c_traslado if incluir_transporte else 0
    costo_total = costo_actividades + costo_transporte_total
    tiempo_visita_total = sum(p["tiempo_min"] for p in ruta_ordenada)

    ids_elegidos = {p["id"] for p in ruta_ordenada}
    descartados = []
    for l in candidatos:
        if l["id"] in ids_elegidos:
            continue
        if l["precio"] > presupuesto:
            motivo = f"Precio (${l['precio']}) excede presupuesto (${presupuesto})"
        elif l["tiempo_min"] > tiempo_disponible_min:
            motivo = f"Duración ({l['tiempo_min']} min) excede tiempo libre ({tiempo_disponible_min} min)"
        elif len(ruta_ordenada) >= max_paradas:
            motivo = f"Límite de paradas ({max_paradas}) alcanzado; menor puntaje relativo"
        else:
            motivo = "Descartado por óptimo global MILP (combinación presupuesto/tiempo)"
        descartados.append({
            "Lugar": l["nombre"],
            "Zona": l["zona"],
            "Costo": f"${l['precio']} MXN",
            "Tiempo": f"{l['tiempo_min']} min",
            "Motivo": motivo,
        })

    return {
        "ruta": ruta_ordenada,
        "tramos": tramos,
        "opciones_compatibles": opciones_compatibles,
        "descartados": descartados,
        "costo_actividades": costo_actividades,
        "costo_transporte_total": costo_transporte_total,
        "costo_total": costo_total,
        "tiempo_visita_total": tiempo_visita_total,
        "tiempo_traslado_total": t_traslado,
        "tiempo_global_total": tiempo_visita_total + t_traslado,
        "distancia_total_km": dist_km,
        "detalle_pulp": {
            "estado": estado_solver,
            "candidatos_evaluados": len(elegibles),
            "paradas_seleccionadas": len(ruta_ordenada),
            "valor_objetivo_satisfaccion": round(sum(p["calificacion"] for p in ruta_ordenada), 2),
            "costo_actividades_mxn": costo_actividades,
            "costo_pulmonia_mxn": costo_transporte_total,
            "restriccion_presupuesto": f"${costo_total} / ${presupuesto} MXN",
            "restriccion_tiempo": f"{tiempo_visita_total + t_traslado} / {tiempo_disponible_min} min",
        },
    }