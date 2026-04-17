# Datos para el ESP32 y modbus
ESP32_IP = "192.168.1.122"
MODBUS_PORT = 502
MODBUS_TIMEOUT = 3

# Datos para llama.cpp
LLM_BASE_URL = "http://127.0.0.1:8080"
LLM_TIMEOUT = 180  # Raspberry Pi 4B puede tardar 60-180 s en inferir

RELAY_MAP = {
    1: {"coil": 0, "pin":25, "nombre": "Relevador 1"},
    2: {"coil": 1, "pin":26, "nombre": "Relevador 2"},
    3: {"coil": 2, "pin":27, "nombre": "Relevador 3"},
    4: {"coil": 3, "pin":32, "nombre": "Relevador 4"}
}