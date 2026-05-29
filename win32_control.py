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
import uiautomation as auto

# ─── Análisis de Accesibilidad (UIAutomation) ──────────────────────

def analizar_ventana_activa() -> dict:
    """
    Detecta la ventana en primer plano y extrae los campos de texto editables usando UIAutomation.
    Retorna un diccionario con el título y la lista de campos (nombre y coordenadas centrales).
    """
    try:
        window = auto.GetForegroundControl()
        if not window:
            return {"error": "No se pudo detectar la ventana activa."}
            
        titulo = window.Name
        campos = []
        
        # Recorrer controles hijos hasta cierta profundidad (reducido a 5 para velocidad)
        for control, depth in auto.WalkControl(window, includeTop=False, maxDepth=5):
            try:
                # Controles editables típicos
                if control.ControlType in [auto.ControlType.EditControl, auto.ControlType.DocumentControl, auto.ControlType.ComboBoxControl]:
                    rect = control.BoundingRectangle
                    if rect.width() > 0 and rect.height() > 0: # Verificar visibilidad básica
                        x = (rect.left + rect.right) // 2
                        y = (rect.top + rect.bottom) // 2
                        campos.append({
                            "tipo": control.ControlTypeName,
                            "nombre": control.Name or "Sin nombre",
                            "x": x,
                            "y": y
                        })
            except Exception:
                pass # Ignorar controles que fallen al leerse

        return {
            "ventana_activa": titulo,
            "cantidad_campos_encontrados": len(campos),
            "campos_de_texto": campos
        }
    except Exception as e:
        return {"error": f"Fallo al analizar ventana con UIAutomation: {str(e)}"}

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
        try:
            # Asegurarse de que no esté minimizada, conservando el estado maximizado original si aplica
            if win32gui.IsIconic(hwnd):
                placement = win32gui.GetWindowPlacement(hwnd)
                wpf_restore = getattr(win32con, 'WPF_RESTORETOMAXIMIZED', 2)
                if placement[0] & wpf_restore:
                    win32gui.ShowWindow(hwnd, win32con.SW_SHOWMAXIMIZED)
                else:
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            # Truco para forzar el foco: enviar una pulsación de tecla virtual (Alt)
            # Esto permite que Windows nos dé permiso para cambiar la ventana de primer plano
            win32api.keybd_event(win32con.VK_MENU, 0, 0, 0) # Alt presionado
            win32gui.SetForegroundWindow(hwnd)
            win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0) # Alt soltado
            return f"Ventana '{titulo}' traída al frente."
        except Exception as e:
            # Si falla el método directo, intentar con ShowWindow únicamente
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            return f"Intento de enfoque realizado en '{titulo}'. (Nota: {str(e)})"
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


def verificar_programa_abierto(nombre: str) -> bool:
    """Retorna True si hay alguna ventana abierta que contenga 'nombre' en su título."""
    hwnd = _encontrar_ventana(nombre)
    return hwnd is not None


def analizar_barra_tareas() -> dict:
    """
    Usa UIAutomation para detectar los elementos en la barra de tareas de Windows.
    Retorna una lista de botones e iconos con sus nombres y coordenadas (x, y).
    """
    try:
        # La barra de tareas suele ser un Pane o Window con ClassName 'Shell_TrayWnd'
        taskbar = auto.Control(ClassName='Shell_TrayWnd')
        if not taskbar.Exists(0):
            # Reintento por nombre
            taskbar = auto.Control(Name='Barra de tareas')
            
        if not taskbar.Exists(0):
            return {"error": "No se pudo localizar la barra de tareas de Windows."}
            
        elementos = []
        # Caminar por los hijos de la barra de tareas (reducido a 3 para velocidad)
        for control, depth in auto.WalkControl(taskbar, includeTop=False, maxDepth=3):
            # Buscamos botones (aplicaciones ancladas o abiertas) e iconos de bandeja
            if control.ControlType in [auto.ControlType.ButtonControl, auto.ControlType.MenuItemControl]:
                nombre = control.Name
                if nombre:
                    rect = control.BoundingRectangle
                    if rect.width() > 0:
                        elementos.append({
                            "nombre": nombre,
                            "tipo": control.ControlTypeName,
                            "x": (rect.left + rect.right) // 2,
                            "y": (rect.top + rect.bottom) // 2
                        })
        
        return {
            "barra_de_tareas_encontrada": True,
            "cantidad_elementos": len(elementos),
            "elementos": elementos
        }
    except Exception as e:
        return {"error": f"Error al analizar barra de tareas: {str(e)}"}


def analizar_escritorio() -> dict:
    """
    Detecta iconos y elementos en el escritorio de Windows usando UIAutomation.
    Útil para encontrar programas que no están en la barra de tareas.
    """
    try:
        # El escritorio puede tener varios nombres dependiendo del idioma
        nombres_escritorio = ['Desktop', 'Escritorio']
        desktop_list = None
        
        for nombre in nombres_escritorio:
            desktop_list = auto.ListControl(Name=nombre)
            if desktop_list.Exists(0):
                break
        
        if not desktop_list or not desktop_list.Exists(0):
            # Fallback por clase
            desktop_list = auto.ListControl(ClassName='SysListView32')
            
        if not desktop_list.Exists(0):
            return {"error": "No se pudo localizar el contenedor de iconos del escritorio."}
            
        elementos = []
        for item in desktop_list.GetChildren():
            nombre = item.Name
            if nombre:
                rect = item.BoundingRectangle
                if rect.width() > 0:
                    elementos.append({
                        "nombre": nombre,
                        "x": (rect.left + rect.right) // 2,
                        "y": (rect.top + rect.bottom) // 2
                    })
        
        return {
            "escritorio_encontrado": True,
            "cantidad_elementos": len(elementos),
            "elementos": elementos
        }
    except Exception as e:
        return {"error": f"Error al analizar escritorio: {str(e)}"}


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
