import json
import re
import unicodedata
import urllib.request
import folium
import streamlit as st
from streamlit_folium import st_folium
from optimizador import generar_plan_turistico

# Catálogo de respaldo por si datos_mazatlan.py no está presente
LUGARES_RESPALDO = [
    {
        "id": "mirador_cristal",
        "nombre": "Mirador de Cristal",
        "zona": "El Faro e Isla de la Piedra",
        "categoria": "Mirador",
        "precio": 50,
        "tiempo_min": 30,
        "calificacion": 9.4,
        "descripcion": "Puente con piso transparente en la cima del Cerro del Crestón.",
        "lat": 23.1778,
        "lon": -106.4256,
    },
    {
        "id": "faro_mazatlan",
        "nombre": "Faro de Mazatlán",
        "zona": "El Faro e Isla de la Piedra",
        "categoria": "Naturaleza",
        "precio": 0,
        "tiempo_min": 60,
        "calificacion": 9.3,
        "descripcion": "Sendero natural hasta uno de los faros naturales más altos del mundo.",
        "lat": 23.1782,
        "lon": -106.4261,
    },
    {
        "id": "isla_piedra",
        "nombre": "Playa Isla de la Piedra",
        "zona": "El Faro e Isla de la Piedra",
        "categoria": "Playa",
        "precio": 180,
        "tiempo_min": 90,
        "calificacion": 9.0,
        "descripcion": "Cruce en lancha y palapas frente al mar con pescado zarandeado.",
        "lat": 23.1825,
        "lon": -106.4045,
    },
    {
        "id": "teatro_angela_peralta",
        "nombre": "Teatro Ángela Peralta",
        "zona": "Centro Histórico y Olas Altas",
        "categoria": "Cultura",
        "precio": 100,
        "tiempo_min": 45,
        "calificacion": 9.2,
        "descripcion": "Recinto histórico del siglo XIX con recorridos guiados y galerías.",
        "lat": 23.1972,
        "lon": -106.4234,
    },
    {
        "id": "plazuela_machado",
        "nombre": "Plazuela Machado",
        "zona": "Centro Histórico y Olas Altas",
        "categoria": "Cultura",
        "precio": 150,
        "tiempo_min": 45,
        "calificacion": 9.3,
        "descripcion": "Corazón cultural del Centro Histórico con arquitectura neoclásica y cafés.",
        "lat": 23.1966,
        "lon": -106.4241,
    },
    {
        "id": "clavadista_mazatlan",
        "nombre": "El Clavadista de Mazatlán",
        "zona": "Centro Histórico y Olas Altas",
        "categoria": "Cultura",
        "precio": 50,
        "tiempo_min": 30,
        "calificacion": 9.1,
        "descripcion": "Espectáculo tradicional de saltos desde el acantilado hacia las rocas.",
        "lat": 23.2004,
        "lon": -106.4268,
    },
    {
        "id": "olas_altas",
        "nombre": "Paseo Olas Altas y Monumento al Venado",
        "zona": "Centro Histórico y Olas Altas",
        "categoria": "Playa",
        "precio": 80,
        "tiempo_min": 40,
        "calificacion": 8.9,
        "descripcion": "Tramo histórico del malecón ideal para caminar al atardecer.",
        "lat": 23.1948,
        "lon": -106.4265,
    },
    {
        "id": "mariscos_centro",
        "nombre": "Ceviches y Aguachiles del Centro",
        "zona": "Centro Histórico y Olas Altas",
        "categoria": "Mariscos",
        "precio": 220,
        "tiempo_min": 50,
        "calificacion": 9.2,
        "descripcion": "Especialidad sinaloense de aguachile verde, ceviche de sierra y tostadas.",
        "lat": 23.1989,
        "lon": -106.4218,
    },
    {
        "id": "gran_acuario",
        "nombre": "Gran Acuario Mazatlán Mar de Cortés",
        "zona": "Malecón y Acuario",
        "categoria": "Naturaleza",
        "precio": 380,
        "tiempo_min": 90,
        "calificacion": 9.5,
        "descripcion": "El acuario más grande de México dedicado a la biodiversidad del Mar de Cortés.",
        "lat": 23.2268,
        "lon": -106.4264,
    },
    {
        "id": "parque_central",
        "nombre": "Parque Central Mazatlán",
        "zona": "Malecón y Acuario",
        "categoria": "Naturaleza",
        "precio": 0,
        "tiempo_min": 40,
        "calificacion": 8.8,
        "descripcion": "Laguna urbana, ciclovía y áreas verdes junto al Malecón.",
        "lat": 23.2252,
        "lon": -106.4245,
    },
    {
        "id": "mariscos_malecon",
        "nombre": "Mariscos Frescos Frente al Malecón",
        "zona": "Malecón y Acuario",
        "categoria": "Mariscos",
        "precio": 260,
        "tiempo_min": 55,
        "calificacion": 9.1,
        "descripcion": "Cocteles de camarón, pulpo a las brasas y vista directa al Pacífico.",
        "lat": 23.2185,
        "lon": -106.4260,
    },
    {
        "id": "letras_mazatlan",
        "nombre": "Letras de Mazatlán y Monumento a la Familia",
        "zona": "Malecón y Acuario",
        "categoria": "Mirador",
        "precio": 0,
        "tiempo_min": 25,
        "calificacion": 8.9,
        "descripcion": "Parada fotográfica emblemática sobre el Malecón costero.",
        "lat": 23.2375,
        "lon": -106.4368,
    },
    {
        "id": "playa_gaviotas",
        "nombre": "Playa Gaviotas (Zona Dorada)",
        "zona": "Zona Dorada",
        "categoria": "Playa",
        "precio": 100,
        "tiempo_min": 75,
        "calificacion": 9.2,
        "descripcion": "Playa de oleaje tranquilo con vista a las Tres Islas.",
        "lat": 23.2495,
        "lon": -106.4525,
    },
    {
        "id": "mariscos_dorada",
        "nombre": "Palapa de Mariscos Zona Dorada",
        "zona": "Zona Dorada",
        "categoria": "Mariscos",
        "precio": 290,
        "tiempo_min": 60,
        "calificacion": 9.3,
        "descripcion": "Torre de mariscos, camarones coco y música banda en vivo.",
        "lat": 23.2530,
        "lon": -106.4550,
    },
    {
        "id": "museo_conchas",
        "nombre": "Museo de Conchas y Caracoles Marinos",
        "zona": "Zona Dorada",
        "categoria": "Cultura",
        "precio": 60,
        "tiempo_min": 35,
        "calificacion": 8.6,
        "descripcion": "Colección de especies marinas y artesanías locales en Zona Dorada.",
        "lat": 23.2468,
        "lon": -106.4498,
    },
    {
        "id": "marina_mazatlan",
        "nombre": "Paseo Marina Mazatlán",
        "zona": "Marina Mazatlán y Cerritos",
        "categoria": "Mirador",
        "precio": 120,
        "tiempo_min": 45,
        "calificacion": 9.0,
        "descripcion": "Muelle de yates, cafeterías y vistas panorámicas al canal de navegación.",
        "lat": 23.2795,
        "lon": -106.4650,
    },
    {
        "id": "playa_cerritos",
        "nombre": "Playa Brujas y Cerritos",
        "zona": "Marina Mazatlán y Cerritos",
        "categoria": "Playa",
        "precio": 150,
        "tiempo_min": 80,
        "calificacion": 9.1,
        "descripcion": "Extensa playa al norte ideal para surf, descanso y mariscos a pie de arena.",
        "lat": 23.2980,
        "lon": -106.4765,
    },
]

try:
    from datos_mazatlan import LUGARES
except ImportError:
    LUGARES = LUGARES_RESPALDO

ZONAS_INFO = {
    "El Faro e Isla de la Piedra": {
        "color": "#0D9488",
        "centro": (23.180, -106.415),
        "zoom": 14,
        "bounds": [[23.172, -106.432], [23.192, -106.395]],
    },
    "Centro Histórico y Olas Altas": {
        "color": "#EF4444",
        "centro": (23.198, -106.424),
        "zoom": 15,
        "bounds": [[23.193, -106.430], [23.210, -106.416]],
    },
    "Malecón y Acuario": {
        "color": "#F97316",
        "centro": (23.226, -106.428),
        "zoom": 14,
        "bounds": [[23.211, -106.439], [23.241, -106.418]],
    },
    "Zona Dorada": {
        "color": "#EAB308",
        "centro": (23.251, -106.453),
        "zoom": 14,
        "bounds": [[23.242, -106.463], [23.266, -106.440]],
    },
    "Marina Mazatlán y Cerritos": {
        "color": "#3B82F6",
        "centro": (23.288, -106.470),
        "zoom": 13,
        "bounds": [[23.268, -106.486], [23.308, -106.452]],
    },
}


def normalizar_texto(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def interpretar_pln_local(texto: str) -> dict:
    """Motor PLN local determinista (100% Offline) basado en reglas semánticas y expresiones regulares."""
    t = normalizar_texto(texto)
    resultado = {"motor": "PLN Local (Offline)"}

    # Presupuesto
    match_pesos = re.search(r"\$?\s*(\d{2,4})\s*(pesos|mxn|varos)?", t)
    if match_pesos:
        val = int(match_pesos.group(1))
        if 50 <= val <= 5000:
            resultado["presupuesto"] = min(2000, max(50, val))

    # Tiempo en horas o minutos
    match_horas = re.search(r"(\d+(?:\.\d+)?)\s*(horas|hora|hrs|hr|h)\b", t)
    match_mins = re.search(r"(\d{2,3})\s*(minutos|minuto|mins|min)\b", t)
    if match_horas:
        hrs = float(match_horas.group(1))
        resultado["horas"] = min(8.0, max(1.0, round(hrs * 2) / 2))
    elif match_mins:
        hrs = round((int(match_mins.group(1)) / 60.0) * 2) / 2
        resultado["horas"] = min(8.0, max(1.0, hrs))

    # Zona turística
    if any(k in t for k in ["faro", "creston", "isla de la piedra", "piedra"]):
        resultado["zona"] = "El Faro e Isla de la Piedra"
    elif any(k in t for k in ["centro", "machado", "olas altas", "teatro", "clavadista"]):
        resultado["zona"] = "Centro Histórico y Olas Altas"
    elif any(k in t for k in ["malecon", "acuario", "parque central"]):
        resultado["zona"] = "Malecón y Acuario"
    elif any(k in t for k in ["zona dorada", "dorada", "gaviotas"]):
        resultado["zona"] = "Zona Dorada"
    elif any(k in t for k in ["marina", "cerritos", "brujas"]):
        resultado["zona"] = "Marina Mazatlán y Cerritos"

    # Categoría
    if any(k in t for k in ["marisco", "comer", "ceviche", "aguachile", "camaron", "comida", "zarandeado"]):
        resultado["categoria"] = "Mariscos"
    elif any(k in t for k in ["cultura", "teatro", "museo", "historia", "historico", "clavadista"]):
        resultado["categoria"] = "Cultura"
    elif any(k in t for k in ["playa", "mar", "nadar", "arena", "sol"]):
        resultado["categoria"] = "Playa"
    elif any(k in t for k in ["mirador", "foto", "fotos", "vista", "atardecer"]):
        resultado["categoria"] = "Mirador"
    elif any(k in t for k in ["naturaleza", "acuario", "caminar", "sendero", "parque"]):
        resultado["categoria"] = "Naturaleza"

    return resultado


def interpretar_pln_hibrido(texto: str, modo_offline: bool, api_key: str) -> dict:
    """Combina Gemini API (si hay conexión y clave) con respaldo automático en PLN Local."""
    base = interpretar_pln_local(texto)
    if modo_offline or not api_key or not api_key.strip():
        return base

    prompt = (
        "Extrae en JSON puro los parámetros turísticos de esta petición en Mazatlán: "
        f"'{texto}'. Claves permitidas: "
        "presupuesto (int 50-2000), horas (float 1.0-8.0), "
        "zona (una de: 'Todas las zonas', 'El Faro e Isla de la Piedra', 'Centro Histórico y Olas Altas', "
        "'Malecón y Acuario', 'Zona Dorada', 'Marina Mazatlán y Cerritos'), "
        "categoria (una de: 'Todas', 'Mariscos', 'Cultura', 'Playa', 'Mirador', 'Naturaleza'). "
        "Responde únicamente con el objeto JSON."
    )
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key.strip()}"
    payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            raw_text = raw_text.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(raw_text)
            parsed["motor"] = "PLN Híbrido (Gemini + Respaldo Local)"
            base.update({k: v for k, v in parsed.items() if v is not None})
    except Exception:
        base["motor"] = "PLN Local (Respaldo automático)"
    return base


# Configuración de página y estilos visuales
st.set_page_config(page_title="RutaMaz IA — Planificador Turístico", page_icon="🌴", layout="wide")

st.markdown(
    """
    <style>
    .hero-banner {
        background: linear-gradient(90deg, #132A4A 0%, #0F5C6E 55%, #168F85 100%);
        padding: 1.5rem 1.8rem;
        border-radius: 14px;
        margin-bottom: 1.2rem;
        color: white;
        box-shadow: 0 4px 16px rgba(0,0,0,0.25);
    }
    .hero-banner h1 {
        margin: 0;
        font-size: 1.85rem;
        font-weight: 800;
        color: #FFFFFF;
    }
    .hero-banner p {
        margin: 0.35rem 0 0 0;
        font-size: 0.95rem;
        color: #D1FAE5;
    }
    .stop-card {
        background-color: #162238;
        border: 1px solid #263859;
        border-left: 4px solid #F59E0B;
        border-radius: 10px;
        padding: 1rem 1.15rem;
        margin-bottom: 0.65rem;
        color: #F3F4F6;
    }
    .stop-title {
        font-size: 1.08rem;
        font-weight: 700;
        color: #FBBF24;
        margin-bottom: 0.45rem;
    }
    .badge-zona {
        display: inline-block;
        background-color: #0F766E;
        color: #ECFDF5;
        padding: 0.18rem 0.6rem;
        border-radius: 999px;
        font-size: 0.76rem;
        font-weight: 600;
        margin-right: 0.4rem;
    }
    .badge-cat {
        display: inline-block;
        background-color: #1D4ED8;
        color: #EFF6FF;
        padding: 0.18rem 0.6rem;
        border-radius: 999px;
        font-size: 0.76rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .stop-meta {
        font-size: 0.86rem;
        color: #D1D5DB;
        margin: 0.5rem 0 0.35rem 0;
    }
    .stop-desc {
        font-size: 0.88rem;
        color: #9CA3AF;
        margin: 0;
    }
    .tramo-box {
        background-color: #1E293B;
        border: 1px dashed #38BDF8;
        border-radius: 8px;
        padding: 0.55rem 0.9rem;
        margin: 0.4rem 0 0.75rem 0;
        font-size: 0.84rem;
        color: #7DD3FC;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Estado inicial
defaults = {
    "zona_sel": "Todas las zonas",
    "cat_sel": "Todas",
    "presupuesto_val": 600,
    "horas_val": 3.0,
    "max_paradas_val": 4,
    "prompt_usuario": "",
    "ultimo_prompt_procesado": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def aplicar_ejemplo(texto: str, zona: str, cat: str, presup: int, hrs: float):
    st.session_state["prompt_usuario"] = texto
    st.session_state["ultimo_prompt_procesado"] = texto
    st.session_state["zona_sel"] = zona
    st.session_state["cat_sel"] = cat
    st.session_state["presupuesto_val"] = presup
    st.session_state["horas_val"] = hrs


def limpiar_texto():
    st.session_state["prompt_usuario"] = ""
    st.session_state["ultimo_prompt_procesado"] = ""


# Barra lateral
with st.sidebar:
    st.markdown("## ⚙️ Parámetros del Turista")

    zonas_opciones = ["Todas las zonas"] + list(ZONAS_INFO.keys())
    zona_sel = st.selectbox(
        "📍 Sección turística de Mazatlán",
        options=zonas_opciones,
        key="zona_sel",
        help="Filtra los atractivos por una de las 5 secciones turísticas del puerto.",
    )

    categorias_disponibles = sorted({l["categoria"] for l in LUGARES})
    cat_opciones = ["Todas"] + categorias_disponibles
    if st.session_state["cat_sel"] not in cat_opciones:
        st.session_state["cat_sel"] = "Todas"

    cat_sel = st.selectbox(
        "🎯 Tipo de actividad o antojo",
        options=cat_opciones,
        key="cat_sel",
    )

    presupuesto = st.slider(
        "💵 Presupuesto disponible ($ MXN)",
        min_value=0,
        max_value=2000,
        step=50,
        key="presupuesto_val",
    )

    horas_libres = st.slider(
        "⏱️ Tiempo libre disponible (horas)",
        min_value=1.0,
        max_value=8.0,
        step=0.5,
        key="horas_val",
    )

    max_paradas = st.slider(
        "🛑 Máximo de paradas en la ruta",
        min_value=1,
        max_value=6,
        step=1,
        key="max_paradas_val",
    )

    st.divider()
    st.markdown("### 🔌 Motor de IA y Conectividad")
    modo_offline = st.toggle(
        "Modo Offline (100% Local)",
        value=True,
        help="Actívalo para operar sin internet usando el motor PLN local y optimización MILP + A*.",
    )
    api_key = st.text_input(
        "Gemini API Key (Opcional)",
        type="password",
        placeholder="Si se deja vacío usa el motor local",
    )

# Encabezado principal
st.markdown(
    """
    <div class="hero-banner">
        <h1>🌴 RutaMaz IA — Planificador Turístico Inteligente</h1>
        <p>Optimización matemática de presupuesto y tiempo (MILP / PuLP) + Búsqueda heurística de rutas (A*) + PLN Híbrido</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Entrada en lenguaje natural
col_txt, col_btn = st.columns([5, 1])
with col_txt:
    prompt_texto = st.text_input(
        "💬 Describe tu plan o antojo en lenguaje natural (opcional):",
        placeholder="Ej: Quiero comer mariscos con $500 pesos y tengo 3 horas libres...",
        key="prompt_usuario",
    )
with col_btn:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    st.button("🧹 Limpiar texto", on_click=limpiar_texto, use_container_width=True)

# Botones rápidos de demostración
st.caption("⚡ Ejemplos rápidos para probar en vivo:")
b1, b2, b3 = st.columns(3)
with b1:
    st.button(
        "🦐 Mariscos con $500 y 3 horas",
        on_click=aplicar_ejemplo,
        args=("Quiero comer mariscos con $500 pesos y tengo 3 horas libres", "Todas las zonas", "Mariscos", 500, 3.0),
        use_container_width=True,
    )
with b2:
    st.button(
        "🏛️ Cultura en Centro Histórico ($250)",
        on_click=aplicar_ejemplo,
        args=("Quiero cultura en el Centro Histórico con $250", "Centro Histórico y Olas Altas", "Cultura", 250, 3.0),
        use_container_width=True,
    )
with b3:
    st.button(
        "🏖️ Playa en Zona Dorada con 4 hrs",
        on_click=aplicar_ejemplo,
        args=("Plan de playa en Zona Dorada con 4 horas", "Zona Dorada", "Playa", 600, 4.0),
        use_container_width=True,
    )

# Procesar texto libre si el usuario escribió uno nuevo
motor_usado = "Controles directos + MILP + A*"
if prompt_texto.strip() and prompt_texto.strip() != st.session_state["ultimo_prompt_procesado"]:
    st.session_state["ultimo_prompt_procesado"] = prompt_texto.strip()
    extraido = interpretar_pln_hibrido(prompt_texto.strip(), modo_offline, api_key)
    motor_usado = extraido.get("motor", motor_usado)
    if "presupuesto" in extraido:
        presupuesto = extraido["presupuesto"]
    if "horas" in extraido:
        horas_libres = extraido["horas"]
    if "zona" in extraido and extraido["zona"] in zonas_opciones:
        zona_sel = extraido["zona"]
    if "categoria" in extraido and extraido["categoria"] in cat_opciones:
        cat_sel = extraido["categoria"]

# Ejecutar optimización matemática + ruta A*
tiempo_disponible_min = int(horas_libres * 60)
plan = generar_plan_turistico(
    lugares=LUGARES,
    presupuesto=presupuesto,
    tiempo_disponible_min=tiempo_disponible_min,
    zona=zona_sel,
    categoria=cat_sel,
    max_paradas=max_paradas,
)

st.markdown("---")

# Métricas superiores
m1, m2, m3, m4 = st.columns(4)
m1.metric("💵 Inversión Estimada", f"${plan['costo_total']} MXN", f"Límite: ${presupuesto}")
m2.metric("⏱️ Tiempo Total Ruta", f"{plan['tiempo_global_total']} min", f"Disponible: {tiempo_disponible_min} min")
m3.metric("🚕 Distancia A*", f"{plan['distancia_total_km']} km", f"Traslado: {plan['tiempo_traslado_total']} min")
m4.metric("📍 Paradas Óptimas", f"{len(plan['ruta'])} lugares", f"Evaluados: {plan['detalle_pulp']['candidatos_evaluados']}")

# Mapa a la izquierda + Detalle de ruta a la derecha
col_mapa, col_detalle = st.columns([1.15, 1])

with col_mapa:
    st.markdown("### 🗺️ Mapa Turístico por Secciones de Mazatlán")

    if zona_sel != "Todas las zonas" and zona_sel in ZONAS_INFO:
        centro_lat, centro_lon = ZONAS_INFO[zona_sel]["centro"]
        zoom_ini = ZONAS_INFO[zona_sel]["zoom"]
    else:
        centro_lat, centro_lon, zoom_ini = 23.235, -106.445, 12

    mapa = folium.Map(location=[centro_lat, centro_lon], zoom_start=zoom_ini, tiles="OpenStreetMap")

    # Polígonos de las 5 secciones turísticas
    for nombre_z, info_z in ZONAS_INFO.items():
        folium.Rectangle(
            bounds=info_z["bounds"],
            color=info_z["color"],
            weight=2,
            fill=True,
            fill_color=info_z["color"],
            fill_opacity=0.10,
            tooltip=f"Sección: {nombre_z}",
        ).add_to(mapa)

    ids_en_ruta = {p["id"] for p in plan["ruta"]}

    # Puntos del catálogo no seleccionados
    for lugar in LUGARES:
        if lugar["id"] not in ids_en_ruta:
            folium.CircleMarker(
                location=[lugar["lat"], lugar["lon"]],
                radius=5,
                color="#334155",
                fill=True,
                fill_color="#64748B",
                fill_opacity=0.85,
                tooltip=f"{lugar['nombre']} (${lugar['precio']} MXN · {lugar['tiempo_min']} min)",
            ).add_to(mapa)

    # Marcadores numerados y línea punteada de la ruta óptima
    coordenadas_ruta = []
    for idx, parada in enumerate(plan["ruta"], start=1):
        coordenadas_ruta.append([parada["lat"], parada["lon"]])
        icono_num = folium.DivIcon(
            html=(
                f'<div style="background-color:#EF4444;color:white;border:2px solid white;'
                f'border-radius:50%;width:28px;height:28px;display:flex;align-items:center;'
                f'justify-content:center;font-weight:bold;font-size:13px;'
                f'box-shadow:0 2px 6px rgba(0,0,0,0.45);">{idx}</div>'
            )
        )
        folium.Marker(
            location=[parada["lat"], parada["lon"]],
            icon=icono_num,
            tooltip=f"Parada #{idx}: {parada['nombre']}",
            popup=f"<b>#{idx} {parada['nombre']}</b><br>Costo: ${parada['precio']} MXN<br>Tiempo: {parada['tiempo_min']} min",
        ).add_to(mapa)

    if len(coordenadas_ruta) > 1:
        folium.PolyLine(
            locations=coordenadas_ruta,
            color="#EF4444",
            weight=3.5,
            opacity=0.9,
            dash_array="8, 8",
        ).add_to(mapa)

    st_folium(mapa, use_container_width=True, height=520, returned_objects=[])

with col_detalle:
    tab_ruta, tab_compatibles, tab_razonamiento = st.tabs(
        ["🚀 Ruta Recomendada", "📋 Opciones Compatibles", "🧠 Razonamiento IA"]
    )

    with tab_ruta:
        if not plan["ruta"]:
            st.warning(
                "No se encontró una combinación dentro de ese presupuesto y tiempo exactos. "
                "Aumenta el presupuesto o revisa la pestaña **Opciones Compatibles**."
            )
        else:
            for idx, parada in enumerate(plan["ruta"], start=1):
                st.markdown(
                    f"""
                    <div class="stop-card">
                        <div class="stop-title">Parada #{idx}: {parada['nombre']}</div>
                        <div>
                            <span class="badge-zona">{parada['zona']}</span>
                            <span class="badge-cat">{parada['categoria']}</span>
                        </div>
                        <div class="stop-meta">
                            💵 Costo aprox: <b>${parada['precio']} MXN</b> &nbsp;|&nbsp;
                            ⏱️ Visita: <b>{parada['tiempo_min']} min</b> &nbsp;|&nbsp;
                            ⭐ <b>{parada['calificacion']}/10</b>
                        </div>
                        <p class="stop-desc">{parada['descripcion']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if idx - 1 < len(plan["tramos"]):
                    tramo = plan["tramos"][idx - 1]
                    st.markdown(
                        f"""
                        <div class="tramo-box">
                            🚕 <b>Traslado A*:</b> {tramo['distancia_km']} km · ~{tramo['tiempo_min']} min en pulmonía hacia la siguiente parada
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    with tab_compatibles:
        opciones = plan.get("opciones_compatibles", [])
        if not opciones:
            st.info("No hay atractivos individuales dentro de ese rango de tiempo y presupuesto.")
        else:
            st.caption(f"Mostrando {len(opciones)} lugares compatibles con tu tiempo y presupuesto aproximado (+15%):")
            for op in opciones:
                st.markdown(
                    f"- **{op['nombre']}** ({op['zona']}) — `${op['precio']} MXN` · `{op['tiempo_min']} min` · ⭐ `{op['calificacion']}/10`"
                )

    with tab_razonamiento:
        st.markdown("#### Arquitectura Híbrida de 3 Capas")
        st.write(f"**1. Capa PLN (Comprensión):** `{motor_usado}`")
        st.json(plan["detalle_pulp"])
        st.write(
            "**3. Capa de Búsqueda Heurística (A*):** Ordena las paradas seleccionadas minimizando "
            "el tiempo de traslado en pulmonía/auriga mediante distancia geodésica Haversine."
        )