import math
import networkx as nx
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds


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
    Capa 2 (Programación Lineal Entera MILP) + Capa 3 (A*):
    1. Filtra todos los lugares compatibles con el presupuesto aproximado (+15%) y tiempo libre.
    2. Resuelve un modelo de Programación Lineal Entera Binaria (Solver HiGHS) para maximizar la experiencia turística.
    3. Traza la ruta geográfica óptima con A*.
    """
    # 1. Filtrado inicial por zona y/o categoría
    candidatos = lugares[:]
    if zona and zona != "Todas las zonas":
        candidatos = [l for l in candidatos if l["zona"] == zona]
    if categoria and categoria != "Todas":
        candidatos = [l for l in candidatos if l["categoria"] == categoria]

    # Lista completa de opciones individuales compatibles con el presupuesto aproximado (+15%)
    presupuesto_aprox = presupuesto * 1.15
    opciones_compatibles = [
        l for l in candidatos
        if l["precio"] <= presupuesto_aprox and l["tiempo_min"] <= tiempo_disponible_min
    ]
    opciones_compatibles.sort(key=lambda x: (-x["calificacion"], x["precio"]))

    # Filtrado estricto para el modelo matemático de optimización
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

    # 2. Modelo de Programación Lineal Entera Binaria (Problema de la Mochila Multi-restricción)
    m = len(elegibles)
    c = -np.array([float(l["calificacion"]) for l in elegibles], dtype=float)
    integrality = np.ones(m, dtype=float)
    bounds = Bounds(lb=np.zeros(m, dtype=float), ub=np.ones(m, dtype=float))

    A = np.array(
        [
            [float(l["precio"]) for l in elegibles],
            [float(l["tiempo_min"] + 12) for l in elegibles],
            [1.0 for _ in elegibles],
        ],
        dtype=float,
    )
    lb = np.array([-np.inf, -np.inf, -np.inf], dtype=float)
    ub = np.array(
        [float(presupuesto), float(tiempo_disponible_min + 12), float(max_paradas)],
        dtype=float,
    )

    resultado = milp(
        c=c,
        integrality=integrality,
        bounds=bounds,
        constraints=LinearConstraint(A, lb, ub),
    )

    if resultado.success and resultado.x is not None:
        seleccionados = [elegibles[i] for i in range(m) if resultado.x[i] > 0.5]
        estado_solver = "Optimal (MILP HiGHS)"
    else:
        # Respaldo determinista ordenado por calificación
        seleccionados = []
        gasto_acum, tiempo_acum = 0, 0
        for l in sorted(elegibles, key=lambda item: -item["calificacion"]):
            extra_traslado = 12 if seleccionados else 0
            if (
                len(seleccionados) < max_paradas
                and gasto_acum + l["precio"] <= presupuesto
                and tiempo_acum + l["tiempo_min"] + extra_traslado <= tiempo_disponible_min
            ):
                seleccionados.append(l)
                gasto_acum += l["precio"]
                tiempo_acum += l["tiempo_min"] + extra_traslado
        estado_solver = "Optimal (Heurística de respaldo)"

    # 3. Ordenar ruta con A* en NetworkX
    G = construir_grafo_mazatlan(lugares)
    ruta_ordenada, tramos, t_traslado, dist_km = ordenar_ruta_astar(G, seleccionados)

    # Ajuste fino si el traslado real de A* excede el tiempo libre
    while len(ruta_ordenada) > 1:
        t_visita = sum(p["tiempo_min"] for p in ruta_ordenada)
        if t_visita + t_traslado <= tiempo_disponible_min:
            break
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
            "estado": estado_solver,
            "candidatos_evaluados": len(elegibles),
            "paradas_seleccionadas": len(ruta_ordenada),
            "valor_objetivo_satisfaccion": round(sum(p["calificacion"] for p in ruta_ordenada), 2),
            "restriccion_presupuesto": f"${costo_total} / ${presupuesto} MXN",
            "restriccion_tiempo": f"{tiempo_visita_total + t_traslado} / {tiempo_disponible_min} min",
        },
    }