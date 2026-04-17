from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException
import logging

# Importando datos de config.py
from config import ESP32_IP, MODBUS_PORT, MODBUS_TIMEOUT, RELAY_MAP

logger = logging.getLogger(__name__)

def _get_client() -> ModbusTcpClient:
    return ModbusTcpClient(host=ESP32_IP, 
                           port = MODBUS_PORT, 
                           timeout = MODBUS_TIMEOUT)

def get_relays() -> dict:
    client = _get_client()
    try:
        if not client.connect():
            raise ConnectionError(
                f"No se puedo conectar a {ESP32_IP}:{MODBUS_PORT}"
            )
        resultado = client.read_coils(address=0,
                                      count=4,
                                      device_id=1)
        if resultado.isError():
            raise ModbusException(f"Error de lectura: {resultado}")
        estados = {}
        for num, info in RELAY_MAP.items():
            estados[num] = resultado.bits[info["coil"]]
        return estados
    except Exception as e:
        logger.error(f"Error en leer relevadores: {e}")
        raise
    finally:
        client.close()

def set_relays(numero: int, estado: bool) -> bool:
    if numero not in RELAY_MAP:
        raise ValueError(f"Número de relevador no existe")
    coil_address = RELAY_MAP[numero]["coil"]
    client = _get_client()
    try:
        if not client.connect():
            raise ConnectionError(
                f"No se puedo conectar a {ESP32_IP}:{MODBUS_PORT}"
            )
        resultado = client.write_coil(address=coil_address, 
                                      value=estado,
                                      device_id=1)
        if resultado.isError():
            raise ModbusException(f"Error: {resultado}")
        logger.info(f"Relevador {numero}:{'Encendido' if estado else 'Apagado'}")
        return True
    except Exception as e:
        logger.error(f"Error escribir_relevador: {e}")    
        raise
    finally: 
        client.close()

def set_all(estados:dict) -> bool:
    client = _get_client()
    try:
        if not client.connect():
            raise ConnectionError(
                f"No se puedo conectar a {ESP32_IP}:{MODBUS_PORT}"
            )
        valores = [False] * 4
        for num, valor in estados.items():
            if num in RELAY_MAP:
                valores[RELAY_MAP[num]["coil"]] = bool(valor)
        
        resultado = client.write_coils(address=0, 
                                       values=valores, 
                                       device_id=1)
        if resultado.isError():
            raise ModbusException(f"Error: {resultado}")
        return True
    except Exception as e:
        logger.error(f"Error set_all: {e}")
        raise
    finally:
        client.close()