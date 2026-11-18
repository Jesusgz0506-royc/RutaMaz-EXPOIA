import math
import networkx as nx
import pulp


def distancia_haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula la distancia geodésica real en kilómetros entre dos coordenadas GPS."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def tiempo_traslado_pulmonia(dist_km: float) -> int:
    """Estima minutos de traslado en pulmonía/auriga (25 km/h promedio + 4 min de abordaje)."""
    if dist_km < 0.3:
        return 4  # Distancia caminable
    return max(5, round((dist_km / 25.0) * 60 + 4))


def construir_grafo_mazatlan(lugares: list) -> nx.Graph:
    """Crea un grafo ponderado de Mazatlán para búsqueda heurística A*."""
    G = nx.Graph()
    for l in lugares:
        G.add_node(l["id"], **l)

    for i in range(len(lugares)):
        for j in range(i + 1, len(lugares)):
            u, v = lugares[i], lugares[j]
            dist = distancia_haversine_km(u["lat"], u["lon"], v["lat"], v["lon"])
            t_viaje = tiempo_traslado_pulmonia(dist)
            G.add_edge(u["id"], v["id"], distancia_km=round(dist, 2), tiempo_min=t_viaje)
    return G


def ordenar_ruta_astar(G: nx.Graph, seleccionados: list) -> tuple:
    """
    Capa 3: Ordena los destinos elegidos usando el algoritmo A* con heurística Haversine
    para minimizar el tiempo total de traslado.
    """
    if not seleccionados:
        return [], [], 0, 0.0

    # Iniciamos desde el punto más al sur (ej. Faro / Centro hacia Zona Dorada / Cerritos)
    pendientes = sorted(seleccionados, key=lambda x: x["lat"])
    ruta_ordenada = [pendientes.pop(0)]
    tramos = []
    tiempo_traslado_total = 0
    distancia_total = 0.0

    def heuristica(id_a, id_b):
        na, nb = G.nodes[id_a], G.nodes[id_b]
        return tiempo_traslado_pulmonia(distancia_haversine_km(na["lat"], na["lon"], nb["lat"], nb["lon"]))

    while pendientes:
        actual = ruta_ordenada[-1]
        mejor_siguiente = None
        mejor_tiempo = float("inf")
        mejor_dist = 0.0

        for candidato in pendientes:
            camino = nx.astar_path(G, actual["id"], candidato["id"], heuristic=heuristica, weight="tiempo_min")
            edge_data = G.get_edge_data(camino[0], camino[-1])
            t_tramo = edge_data["tiempo_min"]
            if t_tramo < mejor_tiempo:
                mejor_tiempo = t_tramo
                mejor_dist = edge_data["distancia_km"]
                mejor_siguiente = candidato

        ruta_ordenada.append(mejor_siguiente)
        pendientes.remove(mejor_siguiente)
        tramos.append({
            "desde": actual["nombre"],
            "hasta": mejor_siguiente["nombre"],
            "distancia_km": mejor_dist,
            "tiempo_min": mejor_tiempo,
        })
        tiempo_traslado_total += mejor_tiempo
        distancia_total += mejor_dist

    return ruta_ordenada, tramos, tiempo_traslado_total, round(distancia_total, 2)


def generar_plan_turistico(
    lugares: list,
    presupuesto: int,
    tiempo_disponible_min: int,
    zona: str = None,
    categoria: str = None,
    max_paradas: int = 5,
) -> dict:
    """
    Capa 2 (PuLP) + Capa 3 (A*):
    1. Obtiene todos los lugares compatibles con el presupuesto aproximado (+15% tolerancia) y tiempo.
    2. Resuelve un modelo de Programación Lineal Entera (PuLP) para maximizar la experiencia turística.
    3. Traza la ruta geográfica óptima con A*.
    """
    # 1. Filtrado inicial por zona y/o categoría
    candidatos = lugares[:]
    if zona and zona != "Todas las zonas":
        candidatos = [l for l in candidatos if l["zona"] == zona]
    if categoria and categoria != "Todas":
        candidatos = [l for l in candidatos if l["categoria"] == categoria]

    # Lista completa de opciones individuales que se acomodan al presupuesto aproximado (+15%) y tiempo
    presupuesto_aprox = presupuesto * 1.15
    opciones_compatibles = [
        l for l in candidatos
        if l["precio"] <= presupuesto_aprox and l["tiempo_min"] <= tiempo_disponible_min
    ]
    opciones_compatibles.sort(key=lambda x: (-x["calificacion"], x["precio"]))

    # Filtrado estricto para el modelo matemático PuLP
    elegibles = [
        l for l in candidatos
        if l["precio"] <= presupuesto and l["tiempo_min"] <= tiempo_disponible_min
    ]

    if not elegibles:
        return {
            "ruta": [],
            "tramos": [],
            "opciones_compatibles": opciones_compatibles,
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

    # 2. Modelo de Optimización Lineal con PuLP (Problema de la Mochila Multi-restricción)
    prob = pulp.LpProblem("Optimizacion_Ruta_Mazatlan", pulp.LpMaximize)
    x = {l["id"]: pulp.LpVariable(f"visitar_{l['id']}", cat="Binary") for l in elegibles}

    # Función Objetivo: Maximizar calificación turística con ligero incentivo a variedad
    prob += pulp.lpSum(l["calificacion"] * x[l["id"]] for l in elegibles), "Maximizar_Experiencia"

    # Restricción 1: Presupuesto máximo
    prob += pulp.lpSum(l["precio"] * x[l["id"]] for l in elegibles) <= presupuesto, "Limite_Presupuesto"

    # Restricción 2: Tiempo total (estancia + promedio de 12 min de traslado entre paradas)
    prob += (
        pulp.lpSum((l["tiempo_min"] + 12) * x[l["id"]] for l in elegibles) - 12 <= tiempo_disponible_min,
        "Limite_Tiempo",
    )

    # Restricción 3: Máximo de paradas para un recorrido cómodo
    prob += pulp.lpSum(x[l["id"]] for l in elegibles) <= max_paradas, "Max_Paradas"

    prob.solve(pulp.PULP_CBC_CMD(msg=False))

    seleccionados = [l for l in elegibles if pulp.value(x[l["id"]]) == 1]

    # 3. Ordenar ruta con A* en NetworkX
    G = construir_grafo_mazatlan(lugares)
    ruta_ordenada, tramos, t_traslado, dist_km = ordenar_ruta_astar(G, seleccionados)

    # Ajuste fino si el traslado real de A* excede el tiempo libre
    while len(ruta_ordenada) > 1:
        t_visita = sum(p["tiempo_min"] for p in ruta_ordenada)
        if t_visita + t_traslado <= tiempo_disponible_min:
            break
        # Quitar el lugar de menor calificación y recalcular A*
        peor = min(ruta_ordenada, key=lambda p: p["calificacion"])
        ruta_ordenada.remove(peor)
        ruta_ordenada, tramos, t_traslado, dist_km = ordenar_ruta_astar(G, ruta_ordenada)

    costo_total = sum(p["precio"] for p in ruta_ordenada)
    tiempo_visita_total = sum(p["tiempo_min"] for p in ruta_ordenada)

    return {
        "ruta": ruta_ordenada,
        "tramos": tramos,
        "opciones_compatibles": opciones_compatibles,
        "costo_total": costo_total,
        "tiempo_visita_total": tiempo_visita_total,
        "tiempo_traslado_total": t_traslado,
        "tiempo_global_total": tiempo_visita_total + t_traslado,
        "distancia_total_km": dist_km,
        "detalle_pulp": {
            "estado": pulp.LpStatus[prob.status],
            "candidatos_evaluados": len(elegibles),
            "paradas_seleccionadas": len(ruta_ordenada),
            "valor_objetivo_satisfaccion": round(sum(p["calificacion"] for p in ruta_ordenada), 2),
            "restriccion_presupuesto": f"${costo_total} / ${presupuesto} MXN",
            "restriccion_tiempo": f"{tiempo_visita_total + t_traslado} / {tiempo_disponible_min} min",
        },
    }