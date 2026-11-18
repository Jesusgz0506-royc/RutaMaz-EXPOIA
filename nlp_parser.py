import json
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    from google import genai
    from google.genai import types
    GENAI_DISPONIBLE = True
except ImportError:
    GENAI_DISPONIBLE = False


ZONAS_VALIDAS = [
    "El Faro e Isla de la Piedra",
    "Centro Histórico y Olas Altas",
    "Malecón",
    "Zona Dorada",
    "Cerritos y Marina",
]

CATEGORIAS_VALIDAS = ["mariscos", "playa", "mirador", "cultura", "entretenimiento"]

PALABRAS_CATEGORIA = {
    "mariscos": ["marisco", "mariscos", "comer", "ceviche", "aguachile", "pescado", "zarandeado", "restaurante", "hambre", "cenar", "almorzar", "tacos"],
    "playa": ["playa", "playas", "nadar", "mar", "arena", "isla", "sol", "surf", "kayak", "palapa"],
    "mirador": ["mirador", "vista", "foto", "fotos", "atardecer", "faro", "caminar", "paseo", "monumento", "letras"],
    "cultura": ["cultura", "historia", "teatro", "catedral", "plazuela", "machado", "clavadista", "artesanias", "museo", "centro"],
    "entretenimiento": ["acuario", "diversion", "familia", "niños", "pinguinos", "entretenimiento", "show"],
}

PALABRAS_ZONA = {
    "El Faro e Isla de la Piedra": ["faro", "creston", "isla de la piedra", "piedra", "embarcadero", "mirador de cristal"],
    "Centro Histórico y Olas Altas": ["centro", "olas altas", "machado", "catedral", "clavadista", "venadito", "peralta"],
    "Malecón": ["malecon", "malecón", "acuario", "valentinos", "pescador", "monumento a la familia"],
    "Zona Dorada": ["zona dorada", "dorada", "gaviotas", "venados", "sabalo", "muchacho alegre", "jaiba"],
    "Cerritos y Marina": ["cerritos", "marina", "brujas", "yates", "norte"],
}


def _extraer_numeros(texto: str):
    """Extrae presupuesto en pesos y tiempo libre en minutos desde texto natural."""
    t = texto.lower()
    presupuesto = None
    tiempo_min = None

    # Buscar presupuesto ($500, 500 pesos, presupuesto de 600, etc.)
    match_dinero = re.search(r"\$\s*(\d+(?:\.\d+)?)|(\d+(?:\.\d+)?)\s*(?:pesos|mxn|varos|lana|presupuesto)", t)
    if not match_dinero:
        match_dinero = re.search(r"presupuesto\s*(?:de)?\s*\$?\s*(\d+(?:\.\d+)?)", t)
    if match_dinero:
        val = next((g for g in match_dinero.groups() if g is not None), None)
        if val:
            presupuesto = int(float(val))

    # Buscar tiempo (3 horas, 2.5 hrs, 90 minutos, etc.)
    match_horas = re.search(r"(\d+(?:\.\d+)?)\s*(?:hora|horas|hr|hrs)\b", t)
    match_mins = re.search(r"(\d+)\s*(?:minuto|minutos|min|mins)\b", t)

    if match_horas:
        tiempo_min = int(float(match_horas.group(1)) * 60)
    if match_mins:
        tiempo_min = (tiempo_min or 0) + int(match_mins.group(1))

    return presupuesto, tiempo_min


def parsear_offline(texto: str, lugares: list) -> dict:
    """Motor local de PLN (sin internet): TF-IDF + Similitud del Coseno + Reglas Léxicas."""
    t = texto.lower()
    presupuesto, tiempo_min = _extraer_numeros(t)

    # 1. Detección léxica directa de categoría y zona
    categoria_detectada = None
    for cat, keywords in PALABRAS_CATEGORIA.items():
        if any(kw in t for kw in keywords):
            categoria_detectada = cat
            break

    zona_detectada = None
    for zona, keywords in PALABRAS_ZONA.items():
        if any(kw in t for kw in keywords):
            zona_detectada = zona
            break

    # 2. Similitud semántica TF-IDF contra la base de conocimiento de Mazatlán
    corpus = [
        f"{l['nombre']} {l['categoria']} {l['zona']} {l['descripcion']}"
        for l in lugares
    ]
    vectorizador = TfidfVectorizer()
    matriz_tfidf = vectorizador.fit_transform(corpus + [t])
    similitudes = cosine_similarity(matriz_tfidf[-1], matriz_tfidf[:-1]).flatten()

    indices_top = similitudes.argsort()[::-1][:3]
    top_matches = [
        {"lugar": lugares[i]["nombre"], "score": round(float(similitudes[i]), 3)}
        for i in indices_top
        if similitudes[i] > 0
    ]

    # Si no hubo palabra clave exacta pero TF-IDF encontró coincidencia semántica fuerte
    if not categoria_detectada and top_matches:
        mejor_idx = indices_top[0]
        categoria_detectada = lugares[mejor_idx]["categoria"]

    return {
        "categoria": categoria_detectada,
        "zona": zona_detectada,
        "presupuesto_detectado": presupuesto,
        "tiempo_min_detectado": tiempo_min,
        "modo_usado": "Offline Local (TF-IDF + Similitud Coseno + Regex)",
        "similitudes_top": top_matches,
    }


def analizar_peticion(texto: str, lugares: list, api_key: str = "", forzar_offline: bool = False) -> dict:
    """
    Capa 1 de IA: Traduce la petición del turista a parámetros matemáticos.
    Usa Gemini API si hay clave e internet; de lo contrario cambia automáticamente al motor Offline.
    """
    if not texto or not texto.strip():
        return {
            "categoria": None,
            "zona": None,
            "presupuesto_detectado": None,
            "tiempo_min_detectado": None,
            "modo_usado": "Sin consulta de texto",
            "similitudes_top": [],
        }

    if not forzar_offline and api_key and GENAI_DISPONIBLE:
        try:
            client = genai.Client(api_key=api_key.strip())
            prompt = f"""
            Eres un extractor de parámetros turísticos para Mazatlán, Sinaloa.
            Analiza la petición del usuario: "{texto}"

            Devuelve ÚNICAMENTE un JSON válido con estas claves exactas:
            - "categoria": una de {CATEGORIAS_VALIDAS} o null si no especifica tipo de actividad/comida.
            - "zona": una de {ZONAS_VALIDAS} o null si no menciona una zona específica.
            - "presupuesto_detectado": número entero en pesos mexicanos o null si no menciona dinero.
            - "tiempo_min_detectado": número entero en minutos (convierte horas a minutos) o null si no menciona tiempo.
            """
            respuesta = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )
            datos = json.loads(respuesta.text)
            offline_ref = parsear_offline(texto, lugares)
            return {
                "categoria": datos.get("categoria") if datos.get("categoria") in CATEGORIAS_VALIDAS else offline_ref["categoria"],
                "zona": datos.get("zona") if datos.get("zona") in ZONAS_VALIDAS else offline_ref["zona"],
                "presupuesto_detectado": datos.get("presupuesto_detectado") or offline_ref["presupuesto_detectado"],
                "tiempo_min_detectado": datos.get("tiempo_min_detectado") or offline_ref["tiempo_min_detectado"],
                "modo_usado": "Online (Gemini 2.5 Flash JSON + Respaldo TF-IDF)",
                "similitudes_top": offline_ref["similitudes_top"],
            }
        except Exception:
            # Si falla el Wi-Fi o la cuota de API en vivo, entra el modo offline sin interrumpir
            resultado = parsear_offline(texto, lugares)
            resultado["modo_usado"] = "Offline Automático (Fallback por red/API)"
            return resultado

    return parsear_offline(texto, lugares)