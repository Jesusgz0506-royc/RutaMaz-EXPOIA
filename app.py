import json
import re
import unicodedata
import urllib.parse
import urllib.request
from branca.element import MacroElement, Template
import folium
import streamlit as st
from streamlit_folium import st_folium
from optimizador import generar_plan_turistico

# Catálogo real de negocios populares y puntos emblemáticos de Mazatlán
LUGARES = [
    {
        "id": "mirador_cristal",
        "nombre": "Mirador de Cristal (Cerro del Crestón)",
        "zona": "El Faro e Isla de la Piedra",
        "categoria": "Mirador",
        "precio": 50,
        "tiempo_min": 30,
        "calificacion": 9.4,
        "direccion": "Cima del Cerro del Crestón, Calz. Joel Montes Camarena s/n",
        "especialidad": "Puente suspendido con piso de vidrio a 157 m sobre el Pacífico",
        "descripcion": "Vista panorámica de 360 grados al puerto, las Tres Islas y el litoral.",
        "lat": 23.1778,
        "lon": -106.4256,
    },
    {
        "id": "faro_mazatlan",
        "nombre": "Faro Natural de Mazatlán",
        "zona": "El Faro e Isla de la Piedra",
        "categoria": "Naturaleza",
        "precio": 0,
        "tiempo_min": 60,
        "calificacion": 9.3,
        "direccion": "Calz. Joel Montes Camarena s/n, Col. Playa Sur",
        "especialidad": "Sendero ecológico y escalinata al faro natural más alto del mundo",
        "descripcion": "Recorrido al aire libre ideal por la mañana o al caer la tarde.",
        "lat": 23.1783,
        "lon": -106.4260,
    },
    {
        "id": "letys_isla_piedra",
        "nombre": "Restaurante Lety's (Isla de la Piedra)",
        "zona": "El Faro e Isla de la Piedra",
        "categoria": "Mariscos",
        "precio": 240,
        "tiempo_min": 85,
        "calificacion": 9.2,
        "direccion": "Zona de Palapas, Playa Isla de la Piedra (cruce en lancha)",
        "especialidad": "Pescado zarandeado a las brasas, ceviche de sierra y coco frío",
        "descripcion": "Palapa tradicional frente al mar con cruce en panga desde el embarcadero.",
        "lat": 23.1828,
        "lon": -106.4048,
    },
    {
        "id": "teatro_angela_peralta",
        "nombre": "Teatro Ángela Peralta",
        "zona": "Centro Histórico y Olas Altas",
        "categoria": "Cultura",
        "precio": 100,
        "tiempo_min": 45,
        "calificacion": 9.2,
        "direccion": "Calle Carnaval #1204, Centro Histórico",
        "especialidad": "Recorrido arquitectónico por el teatro decimonónico restaurado",
        "descripcion": "Joya cultural del siglo XIX con galerías de arte y sala principal.",
        "lat": 23.1972,
        "lon": -106.4234,
    },
    {
        "id": "plazuela_machado",
        "nombre": "Plazuela Machado y Nieves Don Chepe",
        "zona": "Centro Histórico y Olas Altas",
        "categoria": "Cultura",
        "precio": 90,
        "tiempo_min": 40,
        "calificacion": 9.3,
        "direccion": "Calle Constitución y Carnaval, Centro Histórico",
        "especialidad": "Nieves de garrafa artesanales, portales coloniales y música en vivo",
        "descripcion": "Plaza principal del Centro Histórico rodeada de cafés y arquitectura neoclásica.",
        "lat": 23.1966,
        "lon": -106.4241,
    },
    {
        "id": "el_presidio",
        "nombre": "Restaurante El Presidio",
        "zona": "Centro Histórico y Olas Altas",
        "categoria": "Mariscos",
        "precio": 360,
        "tiempo_min": 65,
        "calificacion": 9.5,
        "direccion": "Calle Niños Héroes #1511, Centro Histórico",
        "especialidad": "Pulpo zarandeado, aguachile de rib-eye y coctelería de autor",
        "descripcion": "Casona histórica del siglo XIX restaurada con jardín interior y cocina sinaloense.",
        "lat": 23.1984,
        "lon": -106.4226,
    },
    {
        "id": "panama_centro",
        "nombre": "Pastelería y Restaurante Panamá (Centro)",
        "zona": "Centro Histórico y Olas Altas",
        "categoria": "Cafetería / Postres",
        "precio": 160,
        "tiempo_min": 45,
        "calificacion": 9.2,
        "direccion": "Calle Benito Juárez #1801, Centro",
        "especialidad": "Pay de guayaba, pastel de tres leches, chilaquiles y café de olla",
        "descripcion": "Clásico gastronómico sinaloense ideal para desayunar o tomar café.",
        "lat": 23.2022,
        "lon": -106.4202,
    },
    {
        "id": "clavadista_olas_altas",
        "nombre": "El Clavadista y Paseo Olas Altas",
        "zona": "Centro Histórico y Olas Altas",
        "categoria": "Cultura",
        "precio": 50,
        "tiempo_min": 30,
        "calificacion": 9.1,
        "direccion": "Paseo Claussen y Av. Olas Altas, frente a Glorieta Sánchez Taboada",
        "especialidad": "Saltos tradicionales desde el acantilado hacia las rocas del mar",
        "descripcion": "Espectáculo emblemático frente al tramo histórico del malecón.",
        "lat": 23.2004,
        "lon": -106.4268,
    },
    {
        "id": "observatorio_1873",
        "nombre": "Observatorio Mazatlán 1873",
        "zona": "Centro Histórico y Olas Altas",
        "categoria": "Mirador",
        "precio": 250,
        "tiempo_min": 60,
        "calificacion": 9.3,
        "direccion": "Paseo del Centenario #12, Cerro del Vigía",
        "especialidad": "Funicular panorámico, museo histórico, santuario de aves y sky bar",
        "descripcion": "Antiguo observatorio militar en lo alto del Cerro del Vigía con vista al mar.",
        "lat": 23.1918,
        "lon": -106.4278,
    },
    {
        "id": "gran_acuario",
        "nombre": "Gran Acuario Mazatlán Mar de Cortés",
        "zona": "Malecón y Acuario",
        "categoria": "Naturaleza",
        "precio": 380,
        "tiempo_min": 90,
        "calificacion": 9.5,
        "direccion": "Av. de los Deportes #111, Parque Central",
        "especialidad": "Tanque oceánico gigante, pingüinario y exhibición de lobos marinos",
        "descripcion": "El acuario más grande de México dedicado al ecosistema del Mar de Cortés.",
        "lat": 23.2268,
        "lon": -106.4264,
    },
    {
        "id": "mariscos_torito",
        "nombre": "Mariscos El Torito (Malecón)",
        "zona": "Malecón y Acuario",
        "categoria": "Mariscos",
        "precio": 250,
        "tiempo_min": 55,
        "calificacion": 9.3,
        "direccion": "Av. del Mar #606, frente al Malecón",
        "especialidad": "Aguachile verde, ceviche mitotero, paté de camarón y campechanas",
        "descripcion": "Marisquería tradicional mazatleca con servicio rápido y producto fresco del día.",
        "lat": 23.2148,
        "lon": -106.4258,
    },
    {
        "id": "muchacho_alegre",
        "nombre": "El Muchacho Alegre (Malecón)",
        "zona": "Malecón y Acuario",
        "categoria": "Mariscos",
        "precio": 320,
        "tiempo_min": 65,
        "calificacion": 9.4,
        "direccion": "Av. del Mar #2020, Malecón de Mazatlán",
        "especialidad": "Torre de mariscos, camarones cucaracha y banda sinaloense en vivo",
        "descripcion": "Ambiente festivo frente al malecón con vista directa al atardecer.",
        "lat": 23.2285,
        "lon": -106.4302,
    },
    {
        "id": "parque_central",
        "nombre": "Parque Central Mazatlán",
        "zona": "Malecón y Acuario",
        "categoria": "Naturaleza",
        "precio": 0,
        "tiempo_min": 40,
        "calificacion": 8.8,
        "direccion": "Av. Leonismo Internacional s/n, junto al Acuario",
        "especialidad": "Caminata junto a la laguna urbana, ciclovía y avistamiento de aves",
        "descripcion": "Pulmón verde gratuito ideal para caminar o descansar entre paradas.",
        "lat": 23.2252,
        "lon": -106.4245,
    },
    {
        "id": "letras_mazatlan",
        "nombre": "Letras de Mazatlán (Punto Valentinos)",
        "zona": "Malecón y Acuario",
        "categoria": "Mirador",
        "precio": 0,
        "tiempo_min": 25,
        "calificacion": 9.0,
        "direccion": "Av. del Mar y Av. Rafael Buelna (Punta Camarón)",
        "especialidad": "Parada fotográfica oficial con vista a toda la bahía y Zona Dorada",
        "descripcion": "Punto emblemático donde inicia la Zona Dorada y termina el Malecón.",
        "lat": 23.2375,
        "lon": -106.4368,
    },
    {
        "id": "mariscos_bahia",
        "nombre": "Mariscos Bahía (Zona Dorada)",
        "zona": "Zona Dorada",
        "categoria": "Mariscos",
        "precio": 280,
        "tiempo_min": 60,
        "calificacion": 9.4,
        "direccion": "Av. Camarón Sábalo #500, Zona Dorada",
        "especialidad": "Camarones al coco, filete relleno de mariscos y tostadas de atún",
        "descripcion": "Restaurante familiar emblemático en el corazón de la Zona Dorada.",
        "lat": 23.2498,
        "lon": -106.4518,
    },
    {
        "id": "panama_dorada",
        "nombre": "Pastelería y Restaurante Panamá (Zona Dorada)",
        "zona": "Zona Dorada",
        "categoria": "Cafetería / Postres",
        "precio": 190,
        "tiempo_min": 50,
        "calificacion": 9.3,
        "direccion": "Av. Camarón Sábalo #1900, Zona Dorada",
        "especialidad": "Pastel de guayaba, empanadas de cajeta, desayunos y comidas típicas",
        "descripcion": "Sucursal turística con panadería artesanal y platillos regionales.",
        "lat": 23.2555,
        "lon": -106.4562,
    },
    {
        "id": "playa_gaviotas",
        "nombre": "Playa Gaviotas (Zona Dorada)",
        "zona": "Zona Dorada",
        "categoria": "Playa",
        "precio": 100,
        "tiempo_min": 75,
        "calificacion": 9.2,
        "direccion": "Acceso por Calle Rodolfo T. Loaiza, Zona Dorada",
        "especialidad": "Playa de oleaje suave frente a la Isla de Venados",
        "descripcion": "Arena dorada ideal para nadar, rentar kayak o descansar bajo sombrilla.",
        "lat": 23.2485,
        "lon": -106.4525,
    },
    {
        "id": "museo_conchas",
        "nombre": "Museo de Conchas y Caracoles Marinos",
        "zona": "Zona Dorada",
        "categoria": "Cultura",
        "precio": 60,
        "tiempo_min": 35,
        "calificacion": 8.7,
        "direccion": "Av. Playa Gaviotas #407, Zona Dorada",
        "especialidad": "Colección de especies marinas del Pacífico y artesanías de concha",
        "descripcion": "Visita breve y económica dentro de la zona hotelera.",
        "lat": 23.2468,
        "lon": -106.4498,
    },
    {
        "id": "puerto_azul_marina",
        "nombre": "Mariscos Puerto Azul (Marina Mazatlán)",
        "zona": "Marina Mazatlán y Cerritos",
        "categoria": "Mariscos",
        "precio": 290,
        "tiempo_min": 60,
        "calificacion": 9.2,
        "direccion": "Av. Marina Mazatlán #2210, Marina Mazatlán",
        "especialidad": "Callo de hacha, aguachile de camarón y tacos gobernador",
        "descripcion": "Mariscos frescos en ambiente moderno cerca del muelle de yates.",
        "lat": 23.2775,
        "lon": -106.4638,
    },
    {
        "id": "marina_mazatlan",
        "nombre": "Paseo Muelle Marina Mazatlán",
        "zona": "Marina Mazatlán y Cerritos",
        "categoria": "Mirador",
        "precio": 110,
        "tiempo_min": 45,
        "calificacion": 9.0,
        "direccion": "Blvd. Marina Mazatlán, Zona de Yates y Malecón Marina",
        "especialidad": "Caminata junto a los muelles, cafés y vista al canal de navegación",
        "descripcion": "Paseo tranquilo al norte de la ciudad para tomar café y fotografías.",
        "lat": 23.2810,
        "lon": -106.4662,
    },
    {
        "id": "playa_cerritos",
        "nombre": "Playa Brujas y Cerritos",
        "zona": "Marina Mazatlán y Cerritos",
        "categoria": "Playa",
        "precio": 150,
        "tiempo_min": 80,
        "calificacion": 9.1,
        "direccion": "Av. Sábalo Cerritos s/n, Zona Norte",
        "especialidad": "Playa amplia para surf, caminatas largas y palapas locales",
        "descripcion": "Zona costera abierta al norte ideal para desconectarse del bullicio.",
        "lat": 23.2980,
        "lon": -106.4765,
    },
]

PUNTOS_INICIO = {
    "Automático (Punto más al sur de la ruta)": None,
    "🚢 Terminal de Cruceros Mazatlán": {
        "nombre": "Terminal de Cruceros Mazatlán",
        "lat": 23.1869,
        "lon": -106.4168,
    },
    "🏛️ Plazuela Machado (Centro Histórico)": {
        "nombre": "Plazuela Machado (Centro Histórico)",
        "lat": 23.1966,
        "lon": -106.4241,
    },
    "🐠 Gran Acuario Mazatlán": {
        "nombre": "Gran Acuario Mazatlán",
        "lat": 23.2268,
        "lon": -106.4264,
    },
    "📸 Letras de Mazatlán (Valentinos)": {
        "nombre": "Letras de Mazatlán (Valentinos)",
        "lat": 23.2375,
        "lon": -106.4368,
    },
    "🏖️ Zona Dorada (Av. Camarón Sábalo)": {
        "nombre": "Zona Dorada (Av. Camarón Sábalo)",
        "lat": 23.2512,
        "lon": -106.4538,
    },
    "⛵ Marina Mazatlán": {
        "nombre": "Marina Mazatlán",
        "lat": 23.2795,
        "lon": -106.4650,
    },
}

ZONAS_INFO = {
    "El Faro e Isla de la Piedra": {
        "color": "#0D9488",
        "centro": (23.180, -106.415),
        "zoom": 14,
        "polygon": [
            [23.173, -106.429],
            [23.189, -106.428],
            [23.191, -106.396],
            [23.174, -106.398],
        ],
    },
    "Centro Histórico y Olas Altas": {
        "color": "#EF4444",
        "centro": (23.198, -106.424),
        "zoom": 15,
        "polygon": [
            [23.190, -106.430],
            [23.208, -106.429],
            [23.208, -106.416],
            [23.190, -106.417],
        ],
    },
    "Malecón y Acuario": {
        "color": "#F97316",
        "centro": (23.226, -106.428),
        "zoom": 14,
        "polygon": [
            [23.209, -106.431],
            [23.240, -106.441],
            [23.241, -106.420],
            [23.209, -106.418],
        ],
    },
    "Zona Dorada": {
        "color": "#EAB308",
        "centro": (23.251, -106.453),
        "zoom": 14,
        "polygon": [
            [23.241, -106.448],
            [23.265, -106.464],
            [23.266, -106.443],
            [23.242, -106.438],
        ],
    },
    "Marina Mazatlán y Cerritos": {
        "color": "#3B82F6",
        "centro": (23.288, -106.470),
        "zoom": 13,
        "polygon": [
            [23.267, -106.466],
            [23.306, -106.485],
            [23.307, -106.454],
            [23.268, -106.450],
        ],
    },
}


def url_google_maps(lugar: dict) -> str:
    query = urllib.parse.quote(f"{lugar['nombre']} Mazatlan Sinaloa")
    return f"https://www.google.com/maps/search/?api=1&query={query}"


def normalizar_texto(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def interpretar_pln_local(texto: str) -> dict:
    """Motor PLN local determinista (100% Offline) basado en reglas semánticas y expresiones regulares."""
    t = normalizar_texto(texto)
    resultado = {"motor": "PLN Local (Offline)"}

    match_pesos = re.search(r"\$?\s*(\d{2,4})\s*(pesos|mxn|varos)?", t)
    if match_pesos:
        val = int(match_pesos.group(1))
        if 50 <= val <= 5000:
            resultado["presupuesto"] = min(2000, max(50, val))

    match_horas = re.search(r"(\d+(?:\.\d+)?)\s*(horas|hora|hrs|hr|h)\b", t)
    match_mins = re.search(r"(\d{2,3})\s*(minutos|minuto|mins|min)\b", t)
    if match_horas:
        hrs = float(match_horas.group(1))
        resultado["horas"] = min(8.0, max(1.0, round(hrs * 2) / 2))
    elif match_mins:
        hrs = round((int(match_mins.group(1)) / 60.0) * 2) / 2
        resultado["horas"] = min(8.0, max(1.0, hrs))

    # Punto de inicio si lo menciona ("salgo de...", "estoy en...", "desde...")
    if any(k in t for k in ["salgo de crucero", "terminal de cruceros", "desde el crucero"]):
        resultado["inicio"] = "🚢 Terminal de Cruceros Mazatlán"
    elif any(k in t for k in ["salgo del centro", "desde el centro", "estoy en la machado", "desde machado"]):
        resultado["inicio"] = "🏛️ Plazuela Machado (Centro Histórico)"
    elif any(k in t for k in ["salgo del acuario", "desde el acuario", "estoy en el acuario"]):
        resultado["inicio"] = "🐠 Gran Acuario Mazatlán"
    elif any(k in t for k in ["salgo de zona dorada", "desde zona dorada", "estoy en zona dorada"]):
        resultado["inicio"] = "🏖️ Zona Dorada (Av. Camarón Sábalo)"
    elif any(k in t for k in ["salgo de marina", "desde marina", "estoy en marina"]):
        resultado["inicio"] = "⛵ Marina Mazatlán"

    # Zona destino
    if any(k in t for k in ["faro", "creston", "isla de la piedra", "piedra"]):
        resultado["zona"] = "El Faro e Isla de la Piedra"
    elif any(k in t for k in ["centro", "machado", "olas altas", "teatro", "clavadista", "observatorio"]):
        resultado["zona"] = "Centro Histórico y Olas Altas"
    elif any(k in t for k in ["malecon", "acuario", "parque central", "muchacho alegre", "torito"]):
        resultado["zona"] = "Malecón y Acuario"
    elif any(k in t for k in ["zona dorada", "dorada", "gaviotas", "bahia"]):
        resultado["zona"] = "Zona Dorada"
    elif any(k in t for k in ["marina", "cerritos", "brujas", "puerto azul"]):
        resultado["zona"] = "Marina Mazatlán y Cerritos"

    # Categoría
    if any(k in t for k in ["marisco", "comer", "ceviche", "aguachile", "camaron", "zarandeado", "pulpo"]):
        resultado["categoria"] = "Mariscos"
    elif any(k in t for k in ["cafe", "cafeteria", "postre", "pastel", "pay", "panama", "desayuno", "nieve"]):
        resultado["categoria"] = "Cafetería / Postres"
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
        "categoria (una de: 'Todas', 'Mariscos', 'Cafetería / Postres', 'Cultura', 'Playa', 'Mirador', 'Naturaleza'). "
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


def generar_texto_whatsapp(plan: dict, punto_inicio_nombre: str) -> str:
    lineas = [
        "🌴 *ITINERARIO RUTAMAZ IA — MAZATLÁN* 🌴",
        f"📍 *Salida:* {punto_inicio_nombre}",
        f"💵 *Inversión total:* ${plan['costo_total']} MXN (Actividades: ${plan['costo_actividades']} + Pulmonía: ${plan['costo_transporte_total']})",
        f"⏱️ *Tiempo total:* {plan['tiempo_global_total']} min · 🚕 *Distancia:* {plan['distancia_total_km']} km",
        "----------------------------------------",
    ]
    for idx, p in enumerate(plan["ruta"], start=1):
        lineas.append(f"\n*#{idx} {p['nombre']}* ({p['zona']})")
        lineas.append(f"📌 Dirección: {p['direccion']}")
        lineas.append(f"✨ Recomendado: {p['especialidad']}")
        lineas.append(f"💰 Consumo aprox: ${p['precio']} MXN | 🕒 Estancia: {p['tiempo_min']} min")
        lineas.append(f"🗺️ Cómo llegar: {url_google_maps(p)}")
    return "\n".join(lineas)


# Configuración de página y estilos visuales
st.set_page_config(page_title="RutaMaz IA — Planificador Turístico", page_icon="🌴", layout="wide")

st.markdown(
    """
    <style>
    .hero-banner {
        background: linear-gradient(90deg, #132A4A 0%, #0F5C6E 55%, #168F85 100%);
        padding: 1.4rem 1.8rem;
        border-radius: 14px;
        margin-bottom: 1.1rem;
        color: white;
        box-shadow: 0 4px 16px rgba(0,0,0,0.25);
    }
    .hero-banner h1 {
        margin: 0;
        font-size: 1.8rem;
        font-weight: 800;
        color: #FFFFFF;
    }
    .hero-banner p {
        margin: 0.35rem 0 0 0;
        font-size: 0.94rem;
        color: #D1FAE5;
    }
    .stop-card {
        background-color: #162238;
        border: 1px solid #263859;
        border-left: 4px solid #F59E0B;
        border-radius: 10px;
        padding: 0.95rem 1.1rem;
        margin-bottom: 0.55rem;
        color: #F3F4F6;
    }
    .stop-title {
        font-size: 1.06rem;
        font-weight: 700;
        color: #FBBF24;
        margin-bottom: 0.4rem;
    }
    .badge-zona {
        display: inline-block;
        background-color: #0F766E;
        color: #ECFDF5;
        padding: 0.16rem 0.58rem;
        border-radius: 999px;
        font-size: 0.74rem;
        font-weight: 600;
        margin-right: 0.35rem;
    }
    .badge-cat {
        display: inline-block;
        background-color: #1D4ED8;
        color: #EFF6FF;
        padding: 0.16rem 0.58rem;
        border-radius: 999px;
        font-size: 0.74rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .stop-meta {
        font-size: 0.85rem;
        color: #E5E7EB;
        margin: 0.45rem 0 0.3rem 0;
    }
    .stop-addr {
        font-size: 0.83rem;
        color: #93C5FD;
        margin: 0.2rem 0;
    }
    .stop-desc {
        font-size: 0.85rem;
        color: #9CA3AF;
        margin: 0.2rem 0 0.45rem 0;
    }
    .maps-btn {
        display: inline-block;
        background-color: #10B981;
        color: #06281E !important;
        font-weight: 700;
        font-size: 0.78rem;
        padding: 0.25rem 0.65rem;
        border-radius: 6px;
        text-decoration: none;
    }
    .tramo-box {
        background-color: #1E293B;
        border: 1px dashed #38BDF8;
        border-radius: 8px;
        padding: 0.5rem 0.85rem;
        margin: 0.35rem 0 0.65rem 0;
        font-size: 0.83rem;
        color: #7DD3FC;
    }
    .tramo-inicio {
        background-color: #064E3B;
        border: 1px dashed #34D399;
        border-radius: 8px;
        padding: 0.5rem 0.85rem;
        margin: 0.2rem 0 0.65rem 0;
        font-size: 0.83rem;
        color: #A7F3D0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Estado inicial
defaults = {
    "inicio_sel": "Automático (Punto más al sur de la ruta)",
    "zona_sel": "Todas las zonas",
    "cat_sel": "Todas",
    "presupuesto_val": 750,
    "horas_val": 3.5,
    "max_paradas_val": 4,
    "incluir_transporte_val": True,
    "prompt_usuario": "",
    "ultimo_prompt_procesado": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def aplicar_ejemplo(texto: str, inicio: str, zona: str, cat: str, presup: int, hrs: float):
    st.session_state["prompt_usuario"] = texto
    st.session_state["ultimo_prompt_procesado"] = texto
    st.session_state["inicio_sel"] = inicio
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

    inicio_sel = st.selectbox(
        "🏨 ¿Desde dónde sales?",
        options=list(PUNTOS_INICIO.keys()),
        key="inicio_sel",
        help="Calcula la ruta A* partiendo exactamente desde tu hotel, crucero o punto actual.",
    )

    zonas_opciones = ["Todas las zonas"] + list(ZONAS_INFO.keys())
    zona_sel = st.selectbox(
        "📍 Sección turística destino",
        options=zonas_opciones,
        key="zona_sel",
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

    incluir_transporte = st.toggle(
        "🚕 Incluir tarifa estimada de pulmonía",
        key="incluir_transporte_val",
        help="Descuenta del presupuesto el costo estimado de traslado en pulmonía ($0 en tramos caminables).",
    )

    st.divider()
    st.markdown("### 🔌 Motor de IA y Conectividad")
    modo_offline = st.toggle(
        "Modo Offline (100% Local)",
        value=True,
        help="Opera sin internet usando el motor PLN local y optimización MILP + A*.",
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
        <p>Optimización matemática MILP + Búsqueda heurística A* con negocios reales de Mazatlán y navegación directa</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Entrada en lenguaje natural
col_txt, col_btn = st.columns([5, 1])
with col_txt:
    prompt_texto = st.text_input(
        "💬 Describe tu plan o antojo en lenguaje natural (opcional):",
        placeholder="Ej: Salgo de Zona Dorada, quiero comer mariscos con $700 pesos y tengo 3 horas...",
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
        "🦐 Mariscos desde Crucero ($750 · 3.5h)",
        on_click=aplicar_ejemplo,
        args=(
            "Salgo de crucero y quiero comer mariscos con $750 pesos en 3.5 horas",
            "🚢 Terminal de Cruceros Mazatlán",
            "Todas las zonas",
            "Mariscos",
            750,
            3.5,
        ),
        use_container_width=True,
    )
with b2:
    st.button(
        "🏛️ Cultura en Centro Histórico ($350)",
        on_click=aplicar_ejemplo,
        args=(
            "Quiero cultura en el Centro Histórico con $350",
            "🏛️ Plazuela Machado (Centro Histórico)",
            "Centro Histórico y Olas Altas",
            "Cultura",
            350,
            3.0,
        ),
        use_container_width=True,
    )
with b3:
    st.button(
        "🍰 Café y Postres en Zona Dorada ($400)",
        on_click=aplicar_ejemplo,
        args=(
            "Quiero postre o café en Zona Dorada con $400",
            "🏖️ Zona Dorada (Av. Camarón Sábalo)",
            "Zona Dorada",
            "Cafetería / Postres",
            400,
            2.5,
        ),
        use_container_width=True,
    )

# Procesar texto libre
motor_usado = "Controles directos + MILP + A*"
if prompt_texto.strip() and prompt_texto.strip() != st.session_state["ultimo_prompt_procesado"]:
    st.session_state["ultimo_prompt_procesado"] = prompt_texto.strip()
    extraido = interpretar_pln_hibrido(prompt_texto.strip(), modo_offline, api_key)
    motor_usado = extraido.get("motor", motor_usado)
    if "presupuesto" in extraido:
        presupuesto = extraido["presupuesto"]
    if "horas" in extraido:
        horas_libres = extraido["horas"]
    if "inicio" in extraido and extraido["inicio"] in PUNTOS_INICIO:
        inicio_sel = extraido["inicio"]
    if "zona" in extraido and extraido["zona"] in zonas_opciones:
        zona_sel = extraido["zona"]
    if "categoria" in extraido and extraido["categoria"] in cat_opciones:
        cat_sel = extraido["categoria"]

punto_inicio_obj = PUNTOS_INICIO.get(inicio_sel)
tiempo_disponible_min = int(horas_libres * 60)

# Ejecutar optimización matemática + ruta A*
plan = generar_plan_turistico(
    lugares=LUGARES,
    presupuesto=presupuesto,
    tiempo_disponible_min=tiempo_disponible_min,
    zona=zona_sel,
    categoria=cat_sel,
    max_paradas=max_paradas,
    punto_inicio=punto_inicio_obj,
    incluir_transporte=incluir_transporte,
)

st.markdown("---")

# Métricas superiores
m1, m2, m3, m4 = st.columns(4)
sub_costo = (
    f"Act: ${plan['costo_actividades']} + Pulmonía: ${plan['costo_transporte_total']}"
    if incluir_transporte
    else f"Límite: ${presupuesto} MXN"
)
m1.metric("💵 Inversión Total", f"${plan['costo_total']} MXN", sub_costo)
m2.metric("⏱️ Tiempo Total Ruta", f"{plan['tiempo_global_total']} min", f"Visita: {plan['tiempo_visita_total']} + Traslado: {plan['tiempo_traslado_total']} min")
m3.metric("🚕 Distancia A*", f"{plan['distancia_total_km']} km", f"{len(plan['tramos'])} tramos calculados")
m4.metric("📍 Paradas Óptimas", f"{len(plan['ruta'])} lugares", f"Evaluados: {plan['detalle_pulp']['candidatos_evaluados']}")

# Barras visuales de aprovechamiento de presupuesto y tiempo
b_prog1, b_prog2 = st.columns(2)
with b_prog1:
    pct_pres = min(1.0, plan["costo_total"] / presupuesto) if presupuesto > 0 else 0.0
    sobrante_mxn = max(0, presupuesto - plan["costo_total"])
    st.progress(
        pct_pres,
        text=f"💰 Aprovechamiento de presupuesto: {int(pct_pres * 100)}% (${plan['costo_total']} de ${presupuesto} MXN · Sobrante: ${sobrante_mxn})",
    )
with b_prog2:
    pct_tiempo = min(1.0, plan["tiempo_global_total"] / tiempo_disponible_min) if tiempo_disponible_min > 0 else 0.0
    libre_min = max(0, tiempo_disponible_min - plan["tiempo_global_total"])
    st.progress(
        pct_tiempo,
        text=f"⏳ Aprovechamiento de tiempo: {int(pct_tiempo * 100)}% ({plan['tiempo_global_total']} de {tiempo_disponible_min} min · Libre: {libre_min} min)",
    )

# Mapa a la izquierda + Detalle de ruta a la derecha
col_mapa, col_detalle = st.columns([1.15, 1])

with col_mapa:
    st.markdown("### 🗺️ Mapa Interactivo de Negocios y Rutas")

    if zona_sel != "Todas las zonas" and zona_sel in ZONAS_INFO:
        centro_lat, centro_lon = ZONAS_INFO[zona_sel]["centro"]
        zoom_ini = ZONAS_INFO[zona_sel]["zoom"]
    elif punto_inicio_obj is not None:
        centro_lat, centro_lon, zoom_ini = punto_inicio_obj["lat"], punto_inicio_obj["lon"], 13
    else:
        centro_lat, centro_lon, zoom_ini = 23.235, -106.445, 12

    mapa = folium.Map(location=[centro_lat, centro_lon], zoom_start=zoom_ini, tiles="OpenStreetMap")

    capa_zonas = folium.FeatureGroup(name="🗺️ Secciones Turísticas (5 Zonas)")
    capa_catalogo = folium.FeatureGroup(name="🏪 Negocios y Atractivos del Catálogo")
    capa_ruta = folium.FeatureGroup(name="🚀 Ruta Óptima Sugerida (A*)")

    # Polígonos costeros de las 5 secciones turísticas
    for nombre_z, info_z in ZONAS_INFO.items():
        folium.Polygon(
            locations=info_z["polygon"],
            color=info_z["color"],
            weight=2,
            fill=True,
            fill_color=info_z["color"],
            fill_opacity=0.11,
            tooltip=f"Sección: {nombre_z}",
        ).add_to(capa_zonas)

    ids_en_ruta = {p["id"] for p in plan["ruta"]}

    # Negocios y puntos del catálogo no seleccionados en la ruta
    for lugar in LUGARES:
        if lugar["id"] not in ids_en_ruta:
            link_maps = url_google_maps(lugar)
            popup_html = (
                f"<div style='min-width:210px;font-family:sans-serif;'>"
                f"<b>{lugar['nombre']}</b><br>"
                f"<span style='color:#0F766E;font-size:12px;'>{lugar['zona']} · {lugar['categoria']}</span><br>"
                f"<p style='margin:4px 0;font-size:12px;'>📌 {lugar['direccion']}</p>"
                f"<p style='margin:4px 0;font-size:12px;'>✨ {lugar['especialidad']}</p>"
                f"<b>💵 ${lugar['precio']} MXN · ⏱️ {lugar['tiempo_min']} min · ⭐ {lugar['calificacion']}</b><br>"
                f"<a href='{link_maps}' target='_blank' style='display:inline-block;margin-top:6px;padding:4px 8px;"
                f"background:#10B981;color:white;text-decoration:none;border-radius:4px;font-size:12px;'>📍 Abrir en Google Maps</a>"
                f"</div>"
            )
            folium.CircleMarker(
                location=[lugar["lat"], lugar["lon"]],
                radius=6,
                color="#1E293B",
                weight=1.5,
                fill=True,
                fill_color="#475569",
                fill_opacity=0.88,
                tooltip=f"🏪 {lugar['nombre']} (${lugar['precio']} MXN)",
                popup=folium.Popup(popup_html, max_width=260),
            ).add_to(capa_catalogo)

    # Marcador de punto de inicio si el turista eligió uno
    if punto_inicio_obj is not None:
        icono_inicio = folium.DivIcon(
            html=(
                '<div style="background-color:#10B981;color:#06281E;border:2px solid white;'
                'border-radius:14px;padding:2px 8px;font-weight:800;font-size:11px;'
                'white-space:nowrap;box-shadow:0 2px 6px rgba(0,0,0,0.45);">🚩 INICIO</div>'
            )
        )
        folium.Marker(
            location=[punto_inicio_obj["lat"], punto_inicio_obj["lon"]],
            icon=icono_inicio,
            tooltip=f"Punto de salida: {punto_inicio_obj['nombre']}",
        ).add_to(capa_ruta)

    # Línea de traslado desde punto de inicio hasta la Parada #1
    if punto_inicio_obj is not None and plan["ruta"]:
        primera = plan["ruta"][0]
        folium.PolyLine(
            locations=[[punto_inicio_obj["lat"], punto_inicio_obj["lon"]], [primera["lat"], primera["lon"]]],
            color="#10B981",
            weight=3.5,
            opacity=0.9,
            dash_array="6, 8",
            tooltip="Traslado desde tu punto de salida a Parada #1",
        ).add_to(capa_ruta)

    # Marcadores numerados y ruta óptima
    coordenadas_ruta = []
    for idx, parada in enumerate(plan["ruta"], start=1):
        coordenadas_ruta.append([parada["lat"], parada["lon"]])
        link_maps = url_google_maps(parada)
        icono_num = folium.DivIcon(
            html=(
                f'<div style="background-color:#EF4444;color:white;border:2px solid white;'
                f'border-radius:50%;width:28px;height:28px;display:flex;align-items:center;'
                f'justify-content:center;font-weight:bold;font-size:13px;'
                f'box-shadow:0 2px 6px rgba(0,0,0,0.45);">{idx}</div>'
            )
        )
        popup_parada = (
            f"<div style='min-width:220px;font-family:sans-serif;'>"
            f"<b>Parada #{idx}: {parada['nombre']}</b><br>"
            f"<p style='margin:4px 0;font-size:12px;'>📌 {parada['direccion']}</p>"
            f"<p style='margin:4px 0;font-size:12px;'>✨ {parada['especialidad']}</p>"
            f"<b>💵 ${parada['precio']} MXN · ⏱️ {parada['tiempo_min']} min</b><br>"
            f"<a href='{link_maps}' target='_blank' style='display:inline-block;margin-top:6px;padding:4px 8px;"
            f"background:#EF4444;color:white;text-decoration:none;border-radius:4px;font-size:12px;'>🧭 Ir con Google Maps</a>"
            f"</div>"
        )
        folium.Marker(
            location=[parada["lat"], parada["lon"]],
            icon=icono_num,
            tooltip=f"Parada #{idx}: {parada['nombre']}",
            popup=folium.Popup(popup_parada, max_width=270),
        ).add_to(capa_ruta)

    if len(coordenadas_ruta) > 1:
        folium.PolyLine(
            locations=coordenadas_ruta,
            color="#EF4444",
            weight=3.8,
            opacity=0.92,
            dash_array="8, 8",
        ).add_to(capa_ruta)

    capa_zonas.add_to(mapa)
    capa_catalogo.add_to(mapa)
    capa_ruta.add_to(mapa)
    folium.LayerControl(collapsed=True).add_to(mapa)

    # Leyenda flotante en el mapa
    leyenda_html = """
    {% macro html(this, kwargs) %}
    <div style="position: fixed; bottom: 20px; left: 14px; z-index: 9999;
                background-color: rgba(15, 23, 42, 0.90); color: #F8FAFC;
                padding: 8px 11px; border-radius: 8px; font-size: 11px;
                border: 1px solid #334155; line-height: 1.45;">
        <b>Secciones de Mazatlán</b><br>
        <span style="color:#14B8A6;">■</span> Faro e Isla de la Piedra<br>
        <span style="color:#EF4444;">■</span> Centro Histórico / Olas Altas<br>
        <span style="color:#F97316;">■</span> Malecón y Acuario<br>
        <span style="color:#EAB308;">■</span> Zona Dorada<br>
        <span style="color:#3B82F6;">■</span> Marina y Cerritos
    </div>
    {% endmacro %}
    """
    macro_leyenda = MacroElement()
    macro_leyenda._template = Template(leyenda_html)
    mapa.get_root().add_child(macro_leyenda)

    st_folium(mapa, use_container_width=True, height=540, returned_objects=[])

with col_detalle:
    tab_ruta, tab_compatibles, tab_razonamiento = st.tabs(
        ["🚀 Ruta Recomendada", "🏪 Negocios Compatibles", "🧠 Razonamiento IA"]
    )

    with tab_ruta:
        if not plan["ruta"]:
            st.warning(
                "No se encontró una combinación dentro de ese presupuesto y tiempo exactos "
                "(considerando traslado). Aumenta el presupuesto o revisa **Negocios Compatibles**."
            )
        else:
            # Mostrar tramo inicial si el turista eligió punto de partida
            tramos_inicio = [t for t in plan["tramos"] if t.get("es_inicio")]
            tramos_intermedios = [t for t in plan["tramos"] if not t.get("es_inicio")]

            if tramos_inicio:
                ti = tramos_inicio[0]
                costo_txt = f" · ~${ti['costo_mxn']} MXN pulmonía" if incluir_transporte else ""
                st.markdown(
                    f"""
                    <div class="tramo-inicio">
                        🚩 <b>Salida desde {ti['desde']}:</b> {ti['distancia_km']} km · ~{ti['tiempo_min']} min{costo_txt} hasta Parada #1
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            for idx, parada in enumerate(plan["ruta"], start=1):
                link_maps = url_google_maps(parada)
                st.markdown(
                    f"""
                    <div class="stop-card">
                        <div class="stop-title">Parada #{idx}: {parada['nombre']}</div>
                        <div>
                            <span class="badge-zona">{parada['zona']}</span>
                            <span class="badge-cat">{parada['categoria']}</span>
                        </div>
                        <div class="stop-meta">
                            💵 Consumo aprox: <b>${parada['precio']} MXN</b> &nbsp;|&nbsp;
                            ⏱️ Estancia: <b>{parada['tiempo_min']} min</b> &nbsp;|&nbsp;
                            ⭐ <b>{parada['calificacion']}/10</b>
                        </div>
                        <div class="stop-addr">📌 <b>Ubicación:</b> {parada['direccion']}</div>
                        <p class="stop-desc">✨ <b>Qué pedir/hacer:</b> {parada['especialidad']}</p>
                        <a class="maps-btn" href="{link_maps}" target="_blank">🧭 Abrir ubicación exacta en Google Maps</a>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if idx - 1 < len(tramos_intermedios):
                    tramo = tramos_intermedios[idx - 1]
                    costo_t = f" · ~${tramo['costo_mxn']} MXN" if incluir_transporte else ""
                    st.markdown(
                        f"""
                        <div class="tramo-box">
                            🚕 <b>Traslado A*:</b> {tramo['distancia_km']} km · ~{tramo['tiempo_min']} min en pulmonía{costo_t}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            texto_exportar = generar_texto_whatsapp(plan, inicio_sel)
            st.download_button(
                label="📲 Descargar itinerario con enlaces (listo para WhatsApp)",
                data=texto_exportar,
                file_name="Itinerario_RutaMaz_IA.txt",
                mime="text/plain",
                use_container_width=True,
            )

    with tab_compatibles:
        opciones = plan.get("opciones_compatibles", [])
        if not opciones:
            st.info("No hay negocios individuales dentro de ese rango de tiempo y presupuesto.")
        else:
            st.caption(f"Mostrando {len(opciones)} negocios/puntos compatibles con tu tiempo y presupuesto (+15%):")
            for op in opciones:
                link_op = url_google_maps(op)
                st.markdown(
                    f"**{op['nombre']}** ({op['zona']}) — `${op['precio']} MXN` · `{op['tiempo_min']} min` · ⭐ `{op['calificacion']}/10`  \n"
                    f"📌 *{op['direccion']}* — [Ver en Google Maps]({link_op})"
                )

    with tab_razonamiento:
        st.markdown("#### Formulación Matemática MILP + Búsqueda A*")
        st.write(f"**1. Capa PLN (Comprensión):** `{motor_usado}`")
        st.latex(r"\max Z = \sum_{i=1}^{n} c_i x_i \quad \text{con } x_i \in \{0, 1\}")
        st.latex(
            rf"\text{{s.a.}}\quad \sum p_i x_i + C_{{\text{{pulmonía}}}} = {plan['costo_total']} \le {presupuesto}\text{{ MXN}}, \quad "
            rf"\sum t_i x_i + T_{{A^*}} = {plan['tiempo_global_total']} \le {tiempo_disponible_min}\text{{ min}}, \quad "
            rf"\sum x_i = {len(plan['ruta'])} \le {max_paradas}"
        )
        st.json(plan["detalle_pulp"])

        if plan.get("descartados"):
            st.markdown("#### 📋 Lugares descartados por el optimizador")
            st.dataframe(plan["descartados"], use_container_width=True, hide_index=True)