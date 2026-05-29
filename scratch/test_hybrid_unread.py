import sys
import os
import time
import cv2
import numpy as np
import uiautomation as auto
import pyautogui

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def extraer_contacto_de_nombre_chat(nombre_chat: str) -> str:
    if not nombre_chat:
        return "Contacto Desconocido"
    
    # Formato nativo con comas
    partes = nombre_chat.split(",")
    if len(partes) > 1:
        return partes[0].strip()
        
    # Formato web: "Ver estado Nombre Contacto Hora Mensaje"
    nombre = nombre_chat
    if nombre.startswith("Ver estado"):
        nombre = nombre[len("Ver estado"):].strip()
        
    palabras = nombre.split()
    for i, p in enumerate(palabras):
        # Si es hora tipo "10:28"
        if ":" in p and any(c.isdigit() for c in p):
            return " ".join(palabras[:i]).strip()
        # Si es un día de la semana o Ayer/Hoy
        if p.lower() in ["ayer", "hoy", "lunes", "martes", "miércoles", "miercoles", "jueves", "viernes", "sábado", "sabado", "domingo"]:
            return " ".join(palabras[:i]).strip()
        # Si es fecha tipo 13/5/2026
        if "/" in p and sum(c.isdigit() for c in p) >= 3:
            return " ".join(palabras[:i]).strip()
            
    # Fallback: primeras 3 palabras
    return " ".join(palabras[:3]).strip()

def detectar_nuevos_mensajes_hibrido():
    print("[HIBRIDO] Iniciando detección de nuevos mensajes en WhatsApp...")
    
    # 1. Traer WhatsApp al frente
    whatsapp = None
    for w in auto.GetRootControl().GetChildren():
        if "WhatsApp" in w.Name:
            whatsapp = w
            break
            
    if not whatsapp:
        print("WhatsApp window not found!")
        return {"exito": False, "motivo": "WhatsApp window not found"}
        
    whatsapp.SetFocus()
    time.sleep(0.5)
    win_rect = whatsapp.BoundingRectangle
    
    # Obtener todos los chat items en el panel izquierdo
    chats = []
    def find_chats(ctrl):
        if ctrl.ControlType == auto.ControlType.DataItemControl and ctrl.ClassName == "x10l6tqk xh8yej3 x1g42fcv":
            chats.append(ctrl)
        for child in ctrl.GetChildren():
            find_chats(child)
            
    find_chats(whatsapp)
    print(f"Found {len(chats)} total chat items in list.")

    # ═════════════════════════════════════════════════════════════════════════
    # METODO A: Búsqueda por Accesibilidad Nativa (Text-based)
    # ═════════════════════════════════════════════════════════════════════════
    print("[METODO A] Buscando etiquetas 'no leído' / 'unread'...")
    for chat in chats:
        nombre_lc = (chat.Name or "").lower()
        es_no_leido = any(palabra in nombre_lc for palabra in ["no leido", "no leído", "no leidos", "no leídos", "unread"])
        if es_no_leido:
            contacto = extraer_contacto_de_nombre_chat(chat.Name)
            print(f"-> ¡Mensaje detectado por METODO A en chat: '{contacto}'!")
            # Clic en el chat
            rect = chat.BoundingRectangle
            pyautogui.click(rect.left + 150, rect.top + rect.height() // 2)
            return {"exito": True, "contacto": contacto, "metodo": "A"}

    # ═════════════════════════════════════════════════════════════════════════
    # METODO B: Búsqueda por Heurística de UI Automation (Tiny digit on the right)
    # ═════════════════════════════════════════════════════════════════════════
    print("[METODO B] Buscando miniatura de número a la derecha en UIA...")
    for idx, chat in enumerate(chats):
        chat_rect = chat.BoundingRectangle
        unread_candidates = []
        
        def search_badge(ctrl):
            name = (ctrl.Name or "").strip()
            if name.isdigit() and len(name) <= 3:
                rect = ctrl.BoundingRectangle
                # Debe estar en el extremo derecho del chat y ser pequeño
                if rect.left > chat_rect.left + 230 and rect.width() < 32 and rect.height() < 32:
                    unread_candidates.append((ctrl, name, rect))
            for child in ctrl.GetChildren():
                search_badge(child)
                
        search_badge(chat)
        if unread_candidates:
            contacto = extraer_contacto_de_nombre_chat(chat.Name)
            print(f"-> ¡Mensaje detectado por METODO B en chat: '{contacto}'!")
            # Click en el chat
            rect = chat.BoundingRectangle
            pyautogui.click(rect.left + 150, rect.top + rect.height() // 2)
            return {"exito": True, "contacto": contacto, "metodo": "B"}

    # ═════════════════════════════════════════════════════════════════════════
    # METODO C: Ingesta Visual de Color HSV (Computer Vision)
    # ═════════════════════════════════════════════════════════════════════════
    print("[METODO C] Buscando círculo verde visualmente...")
    try:
        screenshot = pyautogui.screenshot()
        img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        # Recortar la columna de chats (e.g. X desde left hasta left + 350)
        wx, wy, ww, wh = win_rect.left, win_rect.top, win_rect.width(), win_rect.height()
        crop_x1 = max(0, wx)
        crop_y1 = max(0, wy + 100)
        crop_x2 = min(img.shape[1], wx + 350)
        crop_y2 = min(img.shape[0], wy + wh - 80)
        
        crop = img[crop_y1:crop_y2, crop_x1:crop_x2]
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        
        # Color verde de WhatsApp en HSV
        lower_green = np.array([35, 80, 80])
        upper_green = np.array([85, 255, 255])
        
        mask = cv2.inRange(hsv, lower_green, upper_green)
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for c in contours:
            area = cv2.contourArea(c)
            x, y, w, h = cv2.boundingRect(c)
            aspect_ratio = float(w)/h
            
            # El círculo verde del badge es pequeño y redondo
            if 20 <= area <= 600 and 0.5 <= aspect_ratio <= 1.8:
                badge_x = crop_x1 + x + w // 2
                badge_y = crop_y1 + y + h // 2
                
                print(f"-> ¡Mensaje detectado por METODO C (Vision) en pantalla: ({badge_x}, {badge_y})!")
                
                # Encontrar el chat correspondiente a esta altura Y
                chat_under = None
                for ch in chats:
                    r = ch.BoundingRectangle
                    if r.top <= badge_y <= r.bottom:
                        chat_under = ch
                        break
                        
                contacto = extraer_contacto_de_nombre_chat(chat_under.Name if chat_under else "")
                print(f"   Chat identificado bajo la altura Y: '{contacto}'")
                
                # Clic en el chat item (a la izquierda de la coordenada del badge verde para no errar)
                pyautogui.click(badge_x - 100, badge_y)
                return {"exito": True, "contacto": contacto, "metodo": "C"}
                
    except Exception as e_cv:
        print(f"Error en METODO C: {e_cv}")
        
    print("[HIBRIDO] No se detectaron nuevos mensajes.")
    return {"exito": False}

if __name__ == "__main__":
    res = detectar_nuevos_mensajes_hibrido()
    print(f"Resultado final: {res}")
