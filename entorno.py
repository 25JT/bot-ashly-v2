"""
entorno.py - Comprensión del entorno para Ashly.
Le da contexto del sistema, procesos, portapapeles y cursor.
"""
import psutil
import pyautogui
import pyperclip
import win32gui
import win32process
import os
import time
import platform


def obtener_contexto_sistema() -> dict:
    """
    Retorna un resumen completo del entorno actual:
    - Ventana activa
    - Proceso activo
    - Posición del cursor
    - Portapapeles
    - Recursos del sistema (CPU, RAM)
    - Fecha y hora
    """
    resultado = {}

    # Ventana activa
    try:
        hwnd = win32gui.GetForegroundWindow()
        titulo_activo = win32gui.GetWindowText(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        proceso = psutil.Process(pid)
        resultado["ventana_activa"] = titulo_activo
        resultado["proceso_activo"] = proceso.name()
        resultado["pid_activo"] = pid
        resultado["ruta_ejecutable"] = proceso.exe()
    except Exception as e:
        resultado["ventana_activa"] = f"Error: {e}"

    # Posición del cursor
    try:
        pos = pyautogui.position()
        resultado["cursor"] = {"x": pos.x, "y": pos.y}
    except:
        resultado["cursor"] = "No disponible"

    # Portapapeles
    try:
        clip = pyperclip.paste()
        resultado["portapapeles"] = clip[:300] if clip else "(vacío)"
    except:
        resultado["portapapeles"] = "No disponible"

    # CPU y RAM
    try:
        resultado["cpu_uso_%"] = psutil.cpu_percent(interval=0.3)
        mem = psutil.virtual_memory()
        resultado["ram_total_gb"] = round(mem.total / (1024**3), 2)
        resultado["ram_usada_%"] = mem.percent
    except:
        resultado["cpu_uso_%"] = "No disponible"

    # Sistema operativo
    resultado["sistema"] = platform.system()
    resultado["version_os"] = platform.version()
    resultado["usuario"] = os.getlogin()

    # Fecha y hora
    resultado["fecha_hora"] = time.strftime("%Y-%m-%d %H:%M:%S")

    # Resolución de pantalla
    try:
        w, h = pyautogui.size()
        resultado["resolucion"] = f"{w}x{h}"
    except:
        resultado["resolucion"] = "No disponible"

    return resultado


def listar_procesos_activos() -> list:
    """Lista los procesos corriendo actualmente con nombre y uso de CPU/RAM."""
    procesos = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            info = proc.info
            if info['cpu_percent'] is not None or info['memory_percent'] is not None:
                procesos.append({
                    "pid": info['pid'],
                    "nombre": info['name'],
                    "cpu_%": round(info['cpu_percent'] or 0, 2),
                    "ram_%": round(info['memory_percent'] or 0, 2)
                })
        except:
            continue
    # Ordenar por uso de CPU
    return sorted(procesos, key=lambda p: p['cpu_%'], reverse=True)[:20]


def leer_portapapeles() -> str:
    """Retorna el contenido actual del portapapeles."""
    try:
        return pyperclip.paste() or "(portapapeles vacío)"
    except Exception as e:
        return f"Error al leer portapapeles: {e}"


def escribir_portapapeles(texto: str) -> str:
    """Escribe texto en el portapapeles del sistema."""
    try:
        pyperclip.copy(texto)
        return f"Texto copiado al portapapeles: '{texto[:50]}...'" if len(texto) > 50 else f"Texto copiado: '{texto}'"
    except Exception as e:
        return f"Error al escribir en portapapeles: {e}"


if __name__ == "__main__":
    import json
    print(json.dumps(obtener_contexto_sistema(), ensure_ascii=False, indent=2))
