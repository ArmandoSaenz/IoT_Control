from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from modbus_client import get_relays, set_relays
from llm_client import interpretar_prompt
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/relays", tags=["Relevadores"])

class EstadoRelevador(BaseModel):
    relay_1: bool
    relay_2: bool
    relay_3: bool
    relay_4: bool

class ComandoRelevador(BaseModel):
    estado: bool = Field(..., description="true=ON, false=OFF")

class PromptComando(BaseModel):
    prompt: str = Field(..., description="Instrucción en lenguaje natural")

@router.get("/", response_model=EstadoRelevador)
async def get_all():
    try: 
        estados = get_relays()
        return EstadoRelevador(
            relay_1 = estados[1],
            relay_2 = estados[2],
            relay_3 = estados[3],
            relay_4 = estados[4]
        )
    except HTTPException as e:
        raise HTTPException(503, detail=str(e))
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@router.post("/prompt", tags=["IA"])
async def prompt_relay(cmd: PromptComando):
    """Interpreta un comando en lenguaje natural y controla los relevadores."""
    resultado = await interpretar_prompt(cmd.prompt)

    if resultado.get("error"):
        raise HTTPException(422, detail=resultado["error"])

    acciones_ejecutadas = []
    for accion in resultado.get("acciones", []):
        try:
            set_relays(accion["relay"], accion["estado"])
            acciones_ejecutadas.append({
                "relay": accion["relay"],
                "estado": accion["estado"],
                "success": True
            })
        except Exception as e:
            acciones_ejecutadas.append({
                "relay": accion["relay"],
                "estado": accion["estado"],
                "success": False,
                "error": str(e)
            })

    if not acciones_ejecutadas:
        raise HTTPException(422, detail="No se encontraron acciones válidas en la respuesta del LLM")

    return {
        "acciones": acciones_ejecutadas,
        "texto_llm": resultado.get("texto_llm", "")
    }


@router.post("/{numero}")
async def set_relay(numero: int, cmd: ComandoRelevador):
    if numero not in [1, 2, 3, 4]:
        raise HTTPException(400, "Los numeros de relevador son 1, 2, 3, 4")
    try:
        set_relays(numero, cmd.estado)
        return {
            "success": True,
            "relay": numero,
            "mensaje": f"Relevador {numero}: {'Encendido' if cmd.estado else 'Apagado'}"
        }
    except ConnectionError as e:
        raise HTTPException(503, detail=str(e))
    except Exception as e:
        raise HTTPException(500, detail=str(e))