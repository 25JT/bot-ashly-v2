"""
win32_control.py - Control de ventanas de Windows usando Win32 API.
Permite a Ashly interactuar directamente con ventanas del sistema.
"""
import win32gui
import win32con
import win32api
import win32process
import subprocess
import time

# ─── Ayudantes Internos ────────────────────────────────────────────

def _encontrar_ventana(titulo_parcial: str):
    """Busca un hwnd (handle) de ventana cuyo título contenga el texto dado."""
    resultado = []
    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            titulo = win32gui.GetWindowText(hwnd)
            if titulo_parcial.lower() in titulo.lower():
                resultado.append(hwnd)
    win32gui.EnumWindows(callback, None)
    return resultado[0] if resultado else None


# ─── Funciones Principales ─────────────────────────────────────────

def controlar_ventana(titulo: str, accion: str) -> str:
    """
    Controla una ventana por título parcial.
    Acciones: 'minimizar', 'maximizar', 'restaurar', 'cerrar', 'enfocar'
    """
    hwnd = _encontrar_ventana(titulo)
    if not hwnd:
        return f"No se encontró ninguna ventana con el título '{titulo}'."

    accion = accion.lower().strip()
    if accion == "minimizar":
        win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
        return f"Ventana '{titulo}' minimizada."
    elif accion == "maximizar":
        win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
        return f"Ventana '{titulo}' maximizada."
    elif accion == "restaurar":
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        return f"Ventana '{titulo}' restaurada."
    elif accion == "cerrar":
        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        return f"Ventana '{titulo}' cerrada."
    elif accion == "enfocar":
        win32gui.SetForegroundWindow(hwnd)
        return f"Ventana '{titulo}' traída al frente."
    else:
        return f"Acción '{accion}' no reconocida. Usa: minimizar, maximizar, restaurar, cerrar, enfocar."


def abrir_programa(comando: str) -> str:
    """
    Abre un programa o archivo usando el comando de sistema.
    Ej: 'notepad', 'calc', 'explorer', 'chrome', 'code', etc.
    """
    try:
        subprocess.Popen(comando, shell=True)
        time.sleep(1)
        return f"Programa '{comando}' iniciado correctamente."
    except Exception as e:
        return f"Error al abrir '{comando}': {e}"


def listar_ventanas_abiertas() -> list:
    """Retorna una lista de todas las ventanas visibles y sus handles."""
    ventanas = []
    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            titulo = win32gui.GetWindowText(hwnd)
            if titulo.strip():
                ventanas.append({"hwnd": hwnd, "titulo": titulo})
    win32gui.EnumWindows(callback, None)
    return ventanas


def mover_redimensionar_ventana(titulo: str, x: int, y: int, ancho: int, alto: int) -> str:
    """Mueve y redimensiona una ventana a la posición y tamaño especificados."""
    hwnd = _encontrar_ventana(titulo)
    if not hwnd:
        return f"No se encontró ninguna ventana con el título '{titulo}'."
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.MoveWindow(hwnd, x, y, ancho, alto, True)
    return f"Ventana '{titulo}' movida a ({x},{y}) con tamaño {ancho}x{alto}."


if __name__ == "__main__":
    print("Ventanas abiertas:")
    for v in listar_ventanas_abiertas():
        print(f"  [{v['hwnd']}] {v['titulo']}")
