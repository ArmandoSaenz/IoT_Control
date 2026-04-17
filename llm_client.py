import httpx, json, logging, re

from config import LLM_BASE_URL, LLM_TIMEOUT

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Eres un asistente de control industrial para un tablero de 4 relevadores.
Interpreta comandos en lenguaje natural y devuelve SOLO JSON, sin texto adicional.

Relevadores: relay_1, relay_2, relay_3, relay_4
Estados: true (ON), false (OFF)

Formato SIEMPRE:
    {"acciones": [], "error": "Comando no reconocido"}

Ejemplos:
    "enciende el 1" -> {"acciones":[{"relay":"relay_1", "estado":"true"}]}
    "apaga todos" -> {"acciones":[{"relay":"relay_1", "estado":"false"},
                                  {"relay":"relay_2", "estado":"false"},
                                  {"relay":"relay_3", "estado":"false"},
                                  {"relay":"relay_4", "estado":"false"}]}
"""

RELAY_NAME_MAP= {
    "relay_1":1, "relay_2":2, "relay_3":3, "relay_4":4
}

def _extraer_json(texto: str) -> str:
    """Extrae el primer objeto JSON válido del texto del LLM."""
    # Eliminar bloques markdown (```json ... ``` o ''' ... ''')
    texto = re.sub(r"```(?:json)?\s*", "", texto)
    texto = texto.replace("'''json", "").replace("'''", "")
    # Extraer desde el primer '{' hasta el último '}'
    inicio = texto.find("{")
    fin = texto.rfind("}")
    if inicio != -1 and fin != -1 and fin >= inicio:
        return texto[inicio:fin + 1]
    return texto.strip()

def _parse_estado(valor) -> bool:
    """Convierte 'true'/'false' strings o bool a bool correctamente."""
    if isinstance(valor, bool):
        return valor
    return str(valor).strip().lower() == "true"

async def interpretar_prompt(prompt_usuario:str) -> dict:
    prompt_completo = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Comando: {prompt_usuario}\n Respuesta JSON:"
    )
    try:
        timeout = httpx.Timeout(connect=10.0, read=LLM_TIMEOUT, write=10.0, pool=5.0)
        async with httpx.AsyncClient(timeout=timeout) as c:
            resp = await c.post(
                f"{LLM_BASE_URL}/completion",
                json={
                    "prompt": prompt_completo,
                    "n_predict": 256,
                    "temperature": 0.1,
                    "stop": ["###", "Comando:"]
                }
            )
            resp.raise_for_status()
    except httpx.TimeoutException:
        return {"acciones":[], "texto_llm":"", "error":"Timeout LLM"}
    except httpx.HTTPError as e:
        return {"acciones":[], "texto_llm":"", "error":str(e)}
    
    raw = resp.json()
    texto_llm = raw.get("content", "").strip()
    logger.info(f"LLM raw response keys: {list(raw.keys())}")
    logger.info(f"LLM respondio: {texto_llm!r}")

    if not texto_llm:
        return {"acciones":[], "texto_llm":"", "error":"El LLM devolvió una respuesta vacía"}

    try:
        texto_limpio = _extraer_json(texto_llm)
        logger.info(f"JSON extraido: {texto_limpio!r}")
        respuesta_json = json.loads(texto_limpio)

        if "error" in respuesta_json:
            return {"acciones":[], "texto_llm":texto_llm, "error":respuesta_json["error"]}
        
        acciones = []
        for a in respuesta_json.get("acciones",[]):
            num = RELAY_NAME_MAP.get(a.get("relay"))
            if num:
                acciones.append({"relay": num,
                                 "estado": _parse_estado(a.get("estado", False))})
        return {"acciones":acciones, "texto_llm":texto_llm, "error":None}
        
    except json.JSONDecodeError as e:
        return {"acciones":[], "texto_llm":texto_llm, "error":f"JSON invalido:{e}"}
    
   
