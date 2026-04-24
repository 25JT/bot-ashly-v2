import pygetwindow as gw
import pyautogui
import time

def analizar_entorno():
    """Retorna un mapa detallado de ventanas con posiciones y estados."""
    try:
        windows = gw.getWindowsWithTitle('')
        ventana_activa = gw.getActiveWindow()
        lista_ventanas = []
        
        for w in windows:
            if not w.title.strip(): continue
            
            estado = "normal"
            if w.isMinimized: estado = "minimizado"
            elif w.isMaximized: estado = "maximizado"
            
            # Coordenadas del centro para un clic rápido si es necesario
            centro = [w.left + w.width // 2, w.top + w.height // 2]
            
            lista_ventanas.append({
                "titulo": w.title,
                "box": {"x": w.left, "y": w.top, "w": w.width, "h": w.height},
                "centro": centro,
                "estado": estado,
                "es_activa": (ventana_activa and w.title == ventana_activa.title)
            })
            
        return {
            "ventanas": lista_ventanas,
            "resolucion": list(pyautogui.size()),
            "fecha_hora": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"error": f"Error al analizar ventanas: {str(e)}"}