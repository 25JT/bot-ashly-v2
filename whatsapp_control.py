import uiautomation as auto
import time
import win32_control
import teclado_pro
import cv2
import numpy as np
import pyautogui
import ctypes
import os

# DPI Awareness para que uiautomation y pyautogui usen el mismo sistema de coordenadas
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

def whatsapp_enviar_mensaje(contacto: str, mensaje: str) -> str:
    """
    Busca un contacto y envía un mensaje en WhatsApp Desktop de forma programática.
    """
    try:
        # 1. Traer WhatsApp al frente (usamos el ayudante de win32_control que es robusto)
        win32_control.controlar_ventana("WhatsApp", "enfocar")
        time.sleep(1.5)
        
        # Intentamos localizar la ventana de WhatsApp de forma más flexible pero segura
        whatsapp = None
        # Lista de clases conocidas de la aplicación de escritorio de WhatsApp
        clases_whatsapp = ["WinUIDesktopWin32WindowClass", "WhatsAppWin"]
        
        # 1. Intentar por Clase (Más seguro para evitar pestañas del navegador)
        for clase in clases_whatsapp:
            whatsapp = auto.WindowControl(searchDepth=1, ClassName=clase)
            if whatsapp.Exists(0):
                break
        
        # 2. Si no se encontró por clase, intentar por nombre asegurándonos que NO sea un navegador
        if not whatsapp or not whatsapp.Exists(0):
            for w in auto.GetRootControl().GetChildren():
                nombre = w.Name
                clase = w.ClassName
                # Debe contener WhatsApp pero NO ser un navegador común
                if "WhatsApp" in nombre and clase not in ["Chrome_WidgetWin_1", "MozillaWindowClass", "IEFrame"]:
                    whatsapp = w
                    break
        
        if not whatsapp or not whatsapp.Exists(0):
            return "Error: No se pudo localizar la aplicación de WhatsApp Desktop. Asegúrate de que la aplicación oficial esté abierta."

        # 2. Buscar el chat (Contacto o Número)
        # WhatsApp Desktop suele tener un cuadro de búsqueda al inicio
        busqueda = None
        # Lista extendida de posibles nombres para el cuadro de búsqueda
        nombres_busqueda = ["Buscar un chat o iniciar uno nuevo", "Search or start new chat", "Buscar", "Search"]
        
        for nombre in nombres_busqueda:
            busqueda = whatsapp.EditControl(Name=nombre)
            if busqueda.Exists(0):
                break
        
        if busqueda and busqueda.Exists(1):
            busqueda.Click()
            time.sleep(0.5)
            # Usamos teclado_pro para limpiar y escribir (más seguro que uiautomation en este caso)
            teclado_pro.presionar_combinacion(['ctrl', 'a'])
            teclado_pro.presionar_combinacion(['backspace'])
            teclado_pro.escribir_humanamente(contacto)
            time.sleep(1)
            teclado_pro.presionar_combinacion(['enter'])
            time.sleep(1.5)
        else:
            # Fallback: Usar el atajo Ctrl+F para buscar
            teclado_pro.presionar_combinacion(['ctrl', 'f'])
            time.sleep(0.8)
            teclado_pro.escribir_humanamente(contacto)
            time.sleep(0.5)
            teclado_pro.presionar_combinacion(['enter'])
            time.sleep(1.5)

        # 3. Escribir y enviar el mensaje
        caja_texto = None
        nombres_caja = ["Escribe un mensaje", "Escribir un mensaje", "Type a message", "Mensaje", "Escribir mensaje"]
        tipos_caja = [auto.ControlType.EditControl, auto.ControlType.DocumentControl]

        def buscar_caja_recursivo(ctrl, depth=0):
            if depth > 16:
                return None
            try:
                if ctrl.ControlType in tipos_caja:
                    name = (ctrl.Name or "").strip().lower()
                    if (name.startswith("escribe un mensaje") or
                        name.startswith("escribir un mensaje") or
                        name.startswith("type a message") or
                        name == "mensaje" or
                        "mensaje" in name or
                        "escribe" in name or
                        "type a message" in name or
                        "type" in name):
                        return ctrl
                    if not name:
                        rect = ctrl.BoundingRectangle
                        parent_rect = whatsapp.BoundingRectangle
                        if rect and rect.width() > 200 and rect.height() > 20 and rect.top >= parent_rect.bottom - 220:
                            return ctrl
            except Exception:
                pass
            for child in ctrl.GetChildren():
                res = buscar_caja_recursivo(child, depth + 1)
                if res:
                    return res
            return None

        def buscar_caja_por_coordenadas(ctrl, depth=0):
            if depth > 16:
                return None
            try:
                if ctrl.ControlType in tipos_caja:
                    rect = ctrl.BoundingRectangle
                    parent_rect = whatsapp.BoundingRectangle
                    if rect and rect.width() > 200 and rect.height() > 20 and rect.top >= parent_rect.bottom - 220:
                        return ctrl
            except Exception:
                pass
            for child in ctrl.GetChildren():
                res = buscar_caja_por_coordenadas(child, depth + 1)
                if res:
                    return res
            return None

        # Intento 1: Búsqueda recursiva con nombres conocidos y tipos editables
        caja_texto = buscar_caja_recursivo(whatsapp)

        # Intento 2: Fallback genérico por posición cerca del borde inferior
        if not caja_texto or not caja_texto.Exists(0):
            caja_texto = buscar_caja_por_coordenadas(whatsapp)

        if caja_texto and caja_texto.Exists(0):
            # Enfocar ventana y campo de texto de forma segura y precisa
            try:
                whatsapp.SetFocus()
                time.sleep(0.15)
            except Exception:
                pass

            try:
                caja_texto.SetFocus()
                time.sleep(0.15)
            except Exception:
                pass

            if caja_texto.Exists(0):
                caja_texto.Click()
                time.sleep(0.3)
        else:
            # Fallback definitivo: clickar directamente en la parte inferior del chat
            try:
                whatsapp.SetFocus()
                time.sleep(0.25)
                rect = whatsapp.BoundingRectangle
                fallback_x = rect.left + int(rect.width() * 0.7)
                fallback_y = rect.bottom - 45
                pyautogui.click(fallback_x, fallback_y)
                time.sleep(0.4)
            except Exception:
                pass

        # Borrar cualquier borrador previo para que no se mezcle el mensaje
        teclado_pro.presionar_combinacion(['ctrl', 'a'])
        time.sleep(0.1)
        teclado_pro.presionar_combinacion(['backspace'])
        time.sleep(0.15)

        # escribir mensaje
        teclado_pro.escribir_humanamente(mensaje)

        # esperar a que WhatsApp procese el texto
        time.sleep(1.2)

        # enviar ENTER REAL, asegurando que el foco siga en el cuadro de texto
        try:
            auto.SendKeys('{Enter}')
        except Exception:
            teclado_pro.presionar_combinacion(['enter'])

        time.sleep(0.5)

        # Volver a la lista de chats presionando ESC
        try:
            teclado_pro.presionar_combinacion(['esc'])
            time.sleep(0.5)
        except Exception:
            pass

        return f"Mensaje enviado a '{contacto}' exitosamente."

    except Exception as e:
        return f"Error crítico al manejar WhatsApp: {str(e)}"

def whatsapp_obtener_ultimo_mensaje() -> str:
    """
    Intenta leer el contenido del último mensaje en el chat abierto.
    """
    try:
        win32_control.controlar_ventana("WhatsApp", "enfocar")
        time.sleep(1)
        
        # Localizar ventana de forma flexible
        whatsapp = None
        for w in auto.GetRootControl().GetChildren():
            if "WhatsApp" in w.Name:
                whatsapp = w
                break
                
        if not whatsapp:
            return "No se pudo encontrar la ventana de WhatsApp."
            
        # Los mensajes suelen estar en una lista o grupo
        mensajes = whatsapp.ListControl(Name="Lista de mensajes")
        if not mensajes.Exists(0):
            mensajes = whatsapp.GroupControl(Name="Mensajes")
            
        if mensajes.Exists(1):
            items = mensajes.GetChildren()
            if items:
                # El último suele ser el más reciente
                ultimo = items[-1]
                return f"Último mensaje detectado: {ultimo.Name}"
        
        return "No se pudo leer el contenido de los mensajes (posiblemente el chat esté vacío o no sea compatible)."
    except Exception as e:
        return f"Error al leer mensajes: {str(e)}"

def whatsapp_leer_conversacion(limite: int = 5) -> str:
    """
    Lee los últimos mensajes de la conversación activa usando un parseo basado en coordenadas robusto.
    """
    try:
        win32_control.controlar_ventana("WhatsApp", "enfocar")
        time.sleep(1)
        
        whatsapp = None
        for w in auto.GetRootControl().GetChildren():
            if "WhatsApp" in w.Name:
                whatsapp = w
                break
                
        if not whatsapp:
            return "Error: No se pudo encontrar la ventana de WhatsApp."
            
        win_rect = whatsapp.BoundingRectangle
        
        text_controls = []
        def find_texts(ctrl):
            if ctrl.ControlType == auto.ControlType.TextControl and ctrl.Name:
                text_controls.append(ctrl)
            for child in ctrl.GetChildren():
                find_texts(child)
                
        find_texts(whatsapp)
        
        # Determinar el límite del panel izquierdo dinámicamente
        # Si encontramos chats en el panel izquierdo, usamos su borde derecho como referencia
        panel_izq_borde = win_rect.left + int(win_rect.width() * 0.42)

        right_texts = []
        for txt in text_controls:
            rect = txt.BoundingRectangle
            if rect.left > panel_izq_borde and rect.bottom < win_rect.bottom - 80:
                right_texts.append(txt)
                
        if not right_texts:
            return "La conversación parece estar vacía o no se encontraron mensajes."
            
        # Ordenamos los textos por su coordenada Y para leerlos de arriba a abajo
        right_texts.sort(key=lambda t: t.BoundingRectangle.top)
        
        # Procesamos y de-duplicamos
        conversacion_lineas = []
        vistos = set()
        
        for txt in right_texts:
            val = txt.Name.strip()
            if not val:
                continue
                
            # Evitar repetir el mismo texto en la misma zona
            rect = txt.BoundingRectangle
            identificador_unico = (val, rect.top // 5) # tolerar 5px de variación vertical
            
            if identificador_unico not in vistos:
                vistos.add(identificador_unico)
                # El panel de conversación empieza después del panel izquierdo (~42%)
                conv_left = win_rect.left + int(win_rect.width() * 0.42)
                conv_center = conv_left + (win_rect.right - conv_left) // 2
                es_saliente = rect.left > conv_center
                prefijo = "[Tú]" if es_saliente else "[Contacto]"
                
                # Ignorar sistemas, cifrados y timestamps
                if any(excl in val for excl in ["cifrados de extremo", "encriptados", "Usa WhatsApp en tu", "mensajes están protegidos"]):
                    continue
                if "p. m." in val or "a. m." in val or val.lower() in ["hoy", "ayer"]:
                    continue
                    
                conversacion_lineas.append(f"{prefijo}: {val}")
                
        if not conversacion_lineas:
            return "No se pudieron formatear líneas de conversación."
            
        return "\n".join(conversacion_lineas[-limite:])
    except Exception as e:
        return f"Error al leer conversación: {str(e)}"

def whatsapp_listar_chats_recientes() -> str:
    """
    Lista los chats visibles en el panel izquierdo para ver quién ha escrito.
    """
    try:
        win32_control.controlar_ventana("WhatsApp", "enfocar")
        time.sleep(1)
        
        whatsapp = None
        for w in auto.GetRootControl().GetChildren():
            if "WhatsApp" in w.Name:
                whatsapp = w
                break
        
        if not whatsapp: return "Error: WhatsApp no está abierto."

        # Buscar la lista de chats en el panel izquierdo
        lista_chats = whatsapp.ListControl(Name="Lista de chats")
        if not lista_chats.Exists(0):
            # A veces no tiene nombre pero es una lista principal
            lista_chats = whatsapp.ListControl(searchDepth=3) 

        if not lista_chats.Exists(1):
            return "No se pudo encontrar la lista de chats recientes."

        chats = []
        for chat in lista_chats.GetChildren():
            if chat.Name:
                chats.append(f"• {chat.Name}")
        
        if not chats:
            return "No se detectaron chats en la lista."
            
        return "Chats recientes detectados:\n" + "\n".join(chats[:10])
    except Exception as e:
        return f"Error al listar chats: {str(e)}"

def whatsapp_navegar_a_seccion(seccion: str) -> str:
    """
    Navega entre las secciones de WhatsApp: 'Chats', 'Estados', 'Llamadas', 'Comunidades'.
    """
    try:
        win32_control.controlar_ventana("WhatsApp", "enfocar")
        time.sleep(0.5)
        
        whatsapp = None
        for w in auto.GetRootControl().GetChildren():
            if "WhatsApp" in w.Name:
                whatsapp = w
                break
        
        if not whatsapp: return "Error: WhatsApp no está abierto."

        # Mapeo de nombres de botones
        botones = {
            "chats": ["Chats", "Conversaciones"],
            "estados": ["Estados", "Status"],
            "llamadas": ["Llamadas", "Calls"],
            "comunidades": ["Comunidades", "Communities"]
        }
        
        objetivo = seccion.lower()
        if objetivo not in botones:
            return f"Sección '{seccion}' no reconocida. Usa: chats, estados, llamadas o comunidades."

        # Buscar el botón en la barra lateral
        for nombre in botones[objetivo]:
            btn = whatsapp.ButtonControl(Name=nombre)
            if btn.Exists(0):
                btn.Click()
                return f"Navegado a la sección '{seccion}' exitosamente."
        
        # Fallback: intentar por atajos si existen (Ctrl+Tab suele rotar)
        return f"No se encontró el botón para '{seccion}' visualmente en la barra lateral."
    except Exception as e:
        return f"Error al navegar a la sección '{seccion}': {str(e)}"

def extraer_contacto_de_nombre_chat(nombre_chat: str) -> str:
    """
    Extrae el nombre limpio del contacto quitando estados, marcas de tiempo/días
    y prefijos de mensajes no leídos del formato de accesibilidad de WhatsApp.
    """
    import re
    import unicodedata
    
    if not nombre_chat:
        return "Contacto Desconocido"
    
    # 1. Normalizar a NFC para evitar discrepancias de codificación de tildes (NFD vs NFC)
    nombre = unicodedata.normalize('NFC', nombre_chat).strip()
    
    # 2. Remover prefijos de mensajes no leídos de forma insensible a mayúsculas y acentos
    patrones_prefijos = [
        r'^\d+\s+mensajes?\s+no\s+le[ií]dos?,?\s*',
        r'^\d+\s+mensajes?\s+sin\s+leer,?\s*',
        r'^\d+\s+unread\s+messages?,?\s*',
        r'^\d+\s+unread,?\s*',
        r'^\d+\s+mensaje\s+no\s+le[ií]do,?\s*'
    ]
    
    for pat in patrones_prefijos:
        nombre = re.sub(pat, '', nombre, flags=re.IGNORECASE)
    
    nombre = nombre.lstrip(', -:;')
    
    # 2.5. Eliminar patrones de hora y fecha para evitar que dígitos de la hora/fecha se filtren en el número de teléfono
    nombre = re.sub(r'\b\d{1,2}:\d{2}(?:\s*[apAP]\.?\s*[mM]\.?)?\b', '', nombre)
    nombre = re.sub(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', '', nombre)
    nombre = nombre.strip()

    if not nombre:
        return nombre_chat.strip()
        
    # 3. Si el nombre contiene un número de teléfono con '+', priorizar su extracción limpia
    match_tel = re.search(r'(\+\d[\d\s\-]{6,20})\b', nombre)
    if match_tel:
        return match_tel.group(1).strip()
        
    # 4. Dividir por comas
    partes = nombre.split(",")
    if len(partes) > 1:
        posible_contacto = partes[0].strip()
        for pat in patrones_prefijos:
            posible_contacto = re.sub(pat, '', posible_contacto, flags=re.IGNORECASE)
        posible_contacto = posible_contacto.lstrip(', -:;')
        if posible_contacto:
            return posible_contacto

    # 5. Formato web: "Ver estado Nombre Contacto"
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

def _extraer_nombre_header_uia(ventana, win_rect):
    """Busca el nombre del contacto en el header escaneando todos los controles UIA."""
    palabras_sistema = {"en línea", "escribiendo", "en line", "online",
                        "típico", "whatsapp", "chats", "estados",
                        "llamadas", "comunidades", "buscar", "search",
                        "volver", "back", "atrás", "hoy", "ayer", "typing"}
    header_borde = win_rect.left + int(win_rect.width() * 0.42)
    candidatos = []

    def _scanner(ctrl, depth=0):
        if depth > 6:
            return
        try:
            nombre = (ctrl.Name or "").strip()
            rect = ctrl.BoundingRectangle
            if (rect.left > header_borde and
                    rect.top > win_rect.top + 15 and
                    rect.bottom < win_rect.top + 110 and
                    len(nombre) >= 3 and
                    not any(p in nombre.lower() for p in palabras_sistema)):
                candidatos.append((nombre, ctrl))
        except Exception:
            pass
        for child in ctrl.GetChildren():
            _scanner(child, depth + 1)

    _scanner(ventana)
    if not candidatos:
        return None
    candidatos.sort(key=lambda x: len(x[0]), reverse=True)
    return candidatos[0][0]


def whatsapp_detectar_nuevos_mensajes() -> dict:
    """
    Escanea los chats activos de WhatsApp Desktop en el panel izquierdo buscando mensajes no leídos.
    Implementa un algoritmo híbrido avanzado (Filtro Visual HSV + Vinculación UIA) para máxima robustez.
    1. Enfoca WhatsApp y captura la pantalla de forma proactiva.
    2. Busca por UIA nombres de chat con "mensajes no leídos" (Método A).
    3. Busca controles numéricos (badges) en UIA (Método B).
    4. Usa Visión por Computadora (HSV) en el panel izquierdo completo para detectar
       círculos verces de notificación (Método C).
    5. Si encuentra indicadores, vincula la coordenada Y con el chat UIA y lo abre.
    6. Lee la conversación y la devuelve.
    
    Retorna:
        dict: {"contacto": "Nombre", "conversacion": "Mensajes...", "exito": True} 
              o {"exito": False, "motivo": "..."} si no hay nuevos mensajes.
    """
    try:
        # 1. Traer WhatsApp al frente para poder escanearlo e interactuar
        win32_control.controlar_ventana("WhatsApp", "enfocar")
        time.sleep(1.5) # Tiempo suficiente para estabilizar la interfaz
        
        # 2. Localizar ventana de forma robusta
        whatsapp = None
        clases_whatsapp = ["WinUIDesktopWin32WindowClass", "WhatsAppWin"]
        for clase in clases_whatsapp:
            whatsapp = auto.WindowControl(searchDepth=1, ClassName=clase)
            if whatsapp.Exists(0):
                break
        
        if not whatsapp or not whatsapp.Exists(0):
            for w in auto.GetRootControl().GetChildren():
                nombre = w.Name
                clase = w.ClassName
                if "WhatsApp" in nombre and clase not in ["Chrome_WidgetWin_1", "MozillaWindowClass", "IEFrame"]:
                    whatsapp = w
                    break
                    
        if not whatsapp or not whatsapp.Exists(0):
            return {"exito": False, "motivo": "No se pudo encontrar la ventana de WhatsApp abierta."}
            
        win_rect = whatsapp.BoundingRectangle

        # ─────────────────────────────────────────────────────────────────────
        # MÉTODO A: Escaneo de nombres UIA (más fiable - era el método original)
        # WhatsApp Desktop pone en el Name del chat item texto como:
        # "3 mensajes no leídos, Juan Pérez, 10:28, Hola" o
        # "1 mensaje no leído, +57 316 5491376, ..."
        # ─────────────────────────────────────────────────────────────────────
        print("[WHATSAPP] [MÉTODO A] Escaneando nombres de chats via UIA...")

        import re as _re
        patron_no_leido = _re.compile(
            r'\d+\s+mensajes?\s+no\s+le[ií]dos?|'
            r'\d+\s+mensajes?\s+sin\s+leer|'
            r'\d+\s+unread\s+messages?|'
            r'\d+\s+unread\b'
            r'|^\d+[,\.\s]',  # También detecta nombres que empiezan con número
            _re.IGNORECASE | _re.MULTILINE
        )

        # Recolectar todos los chat items del panel izquierdo
        chats_uia = []
        tipos_chat = [
            auto.ControlType.DataItemControl,
            auto.ControlType.ListItemControl,
            auto.ControlType.GroupControl,
            auto.ControlType.CustomControl,
            auto.ControlType.PaneControl,
        ]
        panel_x_max = win_rect.left + int(win_rect.width() * 0.4)

        def find_chats_a(ctrl, depth=0):
            if depth > 16:
                return
            ct = ctrl.ControlType
            if ct in tipos_chat:
                rect = ctrl.BoundingRectangle
                # El item debe empezar en el panel izquierdo (left < 40% del ancho)
                if rect.left >= win_rect.left and rect.left <= panel_x_max:
                    if ctrl.Name and ctrl.Name.strip():
                        chats_uia.append(ctrl)
            for child in ctrl.GetChildren():
                find_chats_a(child, depth + 1)

        find_chats_a(whatsapp)

        # Si no se encontraron, buscar sin filtro de nombre (fallback)
        if not chats_uia:
            def find_chats_fallback(ctrl, depth=0):
                if depth > 12:
                    return
                ct = ctrl.ControlType
                if ct in tipos_chat:
                    rect = ctrl.BoundingRectangle
                    if (rect.left >= win_rect.left and
                            rect.left <= panel_x_max and
                            rect.height() > 20):
                        chats_uia.append(ctrl)
                for child in ctrl.GetChildren():
                    find_chats_fallback(child, depth + 1)
            find_chats_fallback(whatsapp)

        # Deduplicar por coordenada Y para evitar el mismo chat múltiples veces
        chats_uia.sort(key=lambda c: c.BoundingRectangle.top)
        chats_dedup = []
        ultima_y = -100
        for c in chats_uia:
            cy = c.BoundingRectangle.top
            if abs(cy - ultima_y) > 10:
                chats_dedup.append(c)
                ultima_y = cy
        chats_uia = chats_dedup

        print(f"[WHATSAPP] [MÉTODO A] Se encontraron {len(chats_uia)} chats en UIA.")

        # Buscar en los nombres UIA
        for chat in chats_uia:
            nombre_chat = chat.Name or ""
            if patron_no_leido.search(nombre_chat):
                contacto = extraer_contacto_de_nombre_chat(nombre_chat)
                print(f"[WHATSAPP] [MÉTODO A] ¡Mensaje no leído detectado para '{contacto}'! (texto UIA: '{nombre_chat[:80]}')")
                try:
                    # Hacer clic en el chat para abrirlo
                    rect_chat = chat.BoundingRectangle
                    click_y = rect_chat.top + rect_chat.height() // 2
                    # Click en el centro del panel izquierdo (evitando barra de navegación)
                    panel_centro = win_rect.left + int(win_rect.width() * 0.25)
                    click_x = max(panel_centro, rect_chat.left + rect_chat.width() // 2)
                    click_x = min(click_x, win_rect.left + int(win_rect.width() * 0.35))
                    whatsapp.SetFocus()
                    time.sleep(0.2)
                    pyautogui.click(click_x, click_y)
                    time.sleep(1.2)
                except Exception as e_click:
                    print(f"[WHATSAPP] [MÉTODO A] Error al hacer click: {e_click}")
                    try:
                        chat.Click()
                        time.sleep(1.2)
                    except Exception:
                        pass

                conversacion = whatsapp_leer_conversacion(limite=3)
                return {"exito": True, "contacto": contacto, "conversacion": conversacion}

        print("[WHATSAPP] [MÉTODO A] No se detectaron mensajes no leídos por nombres UIA.")

        # ─────────────────────────────────────────────────────────────────────
        # MÉTODO B: Búsqueda de controles de badge numérico en UIA
        # WhatsApp a veces expone el contador como un TextControl o Button
        # con un número ("1", "3", etc.) en la zona del badge
        # ─────────────────────────────────────────────────────────────────────
        print("[WHATSAPP] [MÉTODO B] Buscando controles de badge numérico en UIA...")

        # Límite derecho del panel izquierdo (~42% del ancho de la ventana)
        panel_izq_derecho = win_rect.left + int(win_rect.width() * 0.42)

        badges_b = []
        def find_badges_b(ctrl, depth=0):
            if depth > 15:
                return
            ct = ctrl.ControlType
            if ct in (auto.ControlType.TextControl, auto.ControlType.ButtonControl):
                nombre = (ctrl.Name or "").strip()
                rect_b = ctrl.BoundingRectangle
                # Solo controles en el panel izquierdo de chats con valor numérico de 1-999
                if (rect_b.right <= panel_izq_derecho and
                        rect_b.top > win_rect.top + 80 and
                        nombre.isdigit() and 1 <= int(nombre) <= 999):
                    badges_b.append(ctrl)
            for child in ctrl.GetChildren():
                find_badges_b(child, depth + 1)

        find_badges_b(whatsapp)
        print(f"[WHATSAPP] [MÉTODO B] Badges numéricos encontrados: {len(badges_b)}")

        for badge in badges_b:
            rect_b = badge.BoundingRectangle
            badge_cy = rect_b.top + rect_b.height() // 2

            # Buscar el chat item que contiene este badge
            chat_encontrado = None
            for chat in chats_uia:
                r = chat.BoundingRectangle
                if r.top <= badge_cy <= r.bottom:
                    chat_encontrado = chat
                    break

            nombre_chat = chat_encontrado.Name if chat_encontrado else ""
            contacto = extraer_contacto_de_nombre_chat(nombre_chat) if nombre_chat else f"Contacto en Y={badge_cy}"
            print(f"[WHATSAPP] [MÉTODO B] ¡Badge de '{badge.Name}' mensajes encontrado para '{contacto}'!")

            try:
                whatsapp.SetFocus()
                time.sleep(0.2)
                click_x_b = win_rect.left + 200  # Centro del panel izquierdo
                pyautogui.click(click_x_b, badge_cy)
                time.sleep(1.2)
            except Exception as e_b:
                print(f"[WHATSAPP] [MÉTODO B] Error al hacer click: {e_b}")

            conversacion = whatsapp_leer_conversacion(limite=3)
            return {"exito": True, "contacto": contacto, "conversacion": conversacion}

        print("[WHATSAPP] [MÉTODO B] No se encontraron badges numéricos UIA.")

        # ─────────────────────────────────────────────────────────────────────
        # MÉTODO C: Visión por computadora HSV (círculos verdes)
        # ─────────────────────────────────────────────────────────────────────
        print("[WHATSAPP] [MÉTODO C] [VISIÓN HSV] Buscando círculos verdes de mensajes entrantes...")
        try:
            screenshot = pyautogui.screenshot()
            img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            logical_w, logical_h = pyautogui.size()
            physical_h, physical_w = img.shape[:2]
            scale_x = physical_w / logical_w
            scale_y = physical_h / logical_h

            wx = win_rect.left
            wy = win_rect.top
            ww = win_rect.width()
            wh = win_rect.height()

            phys_wx = int(wx * scale_x)
            phys_wy = int(wy * scale_y)
            phys_ww = int(ww * scale_x)
            phys_wh = int(wh * scale_y)

            # ── Recorte del panel izquierdo (evitando barra de navegación) ──
            # La barra de navegación izquierda de WhatsApp tiene iconos verdes
            # que NO deben confundirse con badges de notificación.
            # El badge numérico aparece en la zona derecha de cada chat item (~x=250-380).
            nav_ancho_logico = int(80 * scale_x)  # barra de navegación ~80px
            crop_x1 = max(0, phys_wx + nav_ancho_logico)
            crop_y1 = max(0, phys_wy + int(80 * scale_y))
            # El badge está en el 30-45% del ancho de la ventana
            badge_x2_logico = int(ww * 0.45)
            crop_x2 = min(physical_w, phys_wx + int(badge_x2_logico * scale_x))
            crop_y2 = min(physical_h, phys_wy + phys_wh - int(60 * scale_y))

            crop = img[crop_y1:crop_y2, crop_x1:crop_x2]
            valid_badges = []
            if crop.size == 0:
                print("[WHATSAPP] [MÉTODO C] Recorte vacío, saltando.")
            else:
                # ── DEBUG: guardar crop ──
                debug_dir = os.path.join(os.path.dirname(__file__), "scratch")
                os.makedirs(debug_dir, exist_ok=True)
                ts = time.strftime("%H%M%S")
                cv2.imwrite(os.path.join(debug_dir, f"whatsapp_crop_{ts}.png"), crop)

                hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

                # Verde WhatsApp — rango medio (ni tan restrictivo ni tan amplio)
                lower_green = np.array([35, 70, 60])
                upper_green = np.array([90, 255, 255])

                mask = cv2.inRange(hsv, lower_green, upper_green)
                kernel = np.ones((3, 3), np.uint8)
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

                # ── DEBUG: guardar máscara ──
                cv2.imwrite(os.path.join(debug_dir, f"whatsapp_mask_{ts}.png"), mask)

                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                # Construir lista de Y ranges de los chats UIA para priorizar detecciones
                chat_y_ranges = [(ch.BoundingRectangle.top, ch.BoundingRectangle.bottom) for ch in chats_uia]
                # Área para el punto verde pequeño (~8px) hasta badge numérico (~28px)
                min_dia = 6.0
                max_dia = 28.0
                min_area = 3.14159 * (min_dia / 2) ** 2
                max_area = 3.14159 * (max_dia / 2) ** 2
                scale_area = scale_x * scale_y

                crop_debug = crop.copy()

                for c in contours:
                    area = cv2.contourArea(c)
                    x, y, w, h = cv2.boundingRect(c)
                    aspect_ratio = float(w) / max(h, 1)

                    # Validar tamaño y forma circular
                    if not (min_area * scale_area <= area <= max_area * scale_area):
                        continue
                    if not (0.6 <= aspect_ratio <= 1.8):
                        continue

                    badge_phys_x = crop_x1 + x + w // 2
                    badge_phys_y = crop_y1 + y + h // 2
                    click_x = int(badge_phys_x / scale_x)
                    click_y = int(badge_phys_y / scale_y)

                    # CHEQUEO SUAVE con UIA: si está dentro de un chat, es prioridad
                    dentro_de_chat = any(r_top <= click_y <= r_bot for r_top, r_bot in chat_y_ranges)
                    if dentro_de_chat:
                        # Válido - dentro de chat UIA
                        valid_badges.append((click_x, click_y))
                        cv2.rectangle(crop_debug, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    else:
                        # Podría ser un chat que UIA no detectó → aceptar igual
                        # pero con menor prioridad
                        valid_badges.append((click_x, click_y))
                        cv2.rectangle(crop_debug, (x, y), (x + w, y + h), (255, 255, 0), 2)

                cv2.imwrite(os.path.join(debug_dir, f"whatsapp_contours_{ts}.png"), crop_debug)

                print(f"[WHATSAPP] [MÉTODO C] Se detectaron {len(valid_badges)} círculos verdes válidos (de {len(contours)} contornos).")

            if valid_badges:
                click_x, click_y = valid_badges[0]

                # Vincular con chat UIA por coordenada Y
                chat_under = None
                for ch in chats_uia:
                    r = ch.BoundingRectangle
                    if r.top <= click_y <= r.bottom:
                        chat_under = ch
                        break

                nombre_chat = chat_under.Name if chat_under else ""

                # ── Click primero, para asegurar que el chat esté abierto ──
                whatsapp.SetFocus()
                time.sleep(0.1)
                pyautogui.click(win_rect.left + 200, click_y)
                time.sleep(1.2)

                # ── Fallback 1: título de la ventana (después del click) ──
                if not nombre_chat:
                    win_title = whatsapp.Name
                    if win_title and win_title.strip().lower() not in ("", "whatsapp"):
                        nombre_chat = win_title.strip()
                        print(f"[WHATSAPP] [MÉTODO C] Nombre desde título ventana: '{nombre_chat}'")

                # ── Fallback 2: header de la conversación vía UIA ──
                if not nombre_chat:
                    try:
                        nombre_chat = _extraer_nombre_header_uia(whatsapp, win_rect)
                        if nombre_chat:
                            print(f"[WHATSAPP] [MÉTODO C] Nombre desde header UIA: '{nombre_chat}'")
                    except Exception as e:
                        print(f"[WHATSAPP] Header UIA falló: {e}")

                # ── Fallback 3: OCR directo en el header de la conversación ──
                if not nombre_chat:
                    try:
                        import pytesseract
                        import re as _re2
                        debug_dir = os.path.join(os.path.dirname(__file__), "scratch")
                        os.makedirs(debug_dir, exist_ok=True)

                        ocr_ss = pyautogui.screenshot()
                        ocr_ss.save(os.path.join(debug_dir, "whatsapp_post_click_full.png"))

                        ocr_img = cv2.cvtColor(np.array(ocr_ss), cv2.COLOR_RGB2BGR)
                        ocr_h, ocr_w = ocr_img.shape[:2]
                        ocr_sx = ocr_w / logical_w
                        ocr_sy = ocr_h / logical_h

                        print(f"[WHATSAPP] DEBUG win_rect: left={win_rect.left}, top={win_rect.top}, w={win_rect.width()}, h={win_rect.height()}")
                        print(f"[WHATSAPP] DEBUG logical: {logical_w}x{logical_h}, físico OCR: {ocr_w}x{ocr_h}, escala: {ocr_sx}x{ocr_sy}")

                        # ── Recorte 1: línea del nombre en el header ──
                        # Enfocar solo el texto del nombre, evitando botones y la línea de estado.
                        hdr_top = win_rect.top + 46
                        hdr_bot = win_rect.top + 84
                        hdr_left = win_rect.left + int(win_rect.width() * 0.26) + 1
                        hdr_right = win_rect.left + int(win_rect.width() * 0.60) + 1
                        ol = int(hdr_left * ocr_sx)
                        or_ = int(hdr_right * ocr_sx)
                        ot = int(hdr_top * ocr_sy)
                        ob = int(hdr_bot * ocr_sy)
                        roi1 = ocr_img[ot:ob, ol:or_]
                        cv2.imwrite(os.path.join(debug_dir, "whatsapp_roi1_header.png"), roi1)
                        print(f"[WHATSAPP] DEBUG recorte1 header: x={hdr_left}-{hdr_right}, y={hdr_top}-{hdr_bot}")

                        def _es_nombre_valido(texto):
                            """Solo acepta texto con letras, dígitos, espacios, +, . y - (nombres/teléfonos válidos)."""
                            if not texto or len(texto) < 3:
                                return False
                            # Solo caracteres permitidos en nombres/teléfonos
                            if not _re2.match(r'^[a-zA-ZáéíóúñÁÉÍÓÚÑ0-9\s\.\+,\-]+$', texto):
                                return False
                            # Rechazar si son solo números
                            if _re2.match(r'^\d+$', texto):
                                return False
                            return True

                        def _preprocesar_para_ocr(roi_bgr):
                            """Mejora el ROI para OCR: escala de grises + inversión para texto claro."""
                            gray = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)
                            # Invertir si el fondo es oscuro (WhatsApp modo oscuro)
                            mean_brightness = cv2.mean(gray)[0]
                            if mean_brightness < 128:
                                gray = cv2.bitwise_not(gray)
                            return gray

                        # Intentar OCR en múltiples recortes
                        for label, roi in [("header", roi1)]:
                            if roi.size > 0:
                                roi_proc = _preprocesar_para_ocr(roi)
                                for psm in [6, 7, 3]:
                                    cfg = f'--oem 3 --psm {psm} -l spa+eng'
                                    texto = pytesseract.image_to_string(roi_proc, config=cfg).strip()
                                    lineas = [l.strip() for l in texto.split('\n') if l.strip()]
                                    candidatos = []
                                    for linea in lineas:
                                        # Separar ruido pegado con puntos: "ai. Elizabeth Verg" -> ["ai", "Elizabeth Verg"]
                                        segmentos = [s.strip() for s in _re2.split(r'\.[\s]*', linea) if s.strip()]
                                        if not segmentos:
                                            segmentos = [linea]
                                        for segmento in segmentos:
                                            limpio = _re2.sub(r'\b\d{1,2}:\d{2}\b', '', segmento).strip()
                                            limpio = _re2.sub(r'^[\s,;:.!\-]+|[\s,;:.!\-]+$', '', limpio).strip()
                                            print(f"[WHATSAPP] OCR {label} psm={psm}: '{limpio}'")
                                            if _es_nombre_valido(limpio) and len(limpio.split()) <= 4:
                                                candidatos.append(limpio)
                                    if candidatos:
                                        # Elegir el candidato más probable: el más largo, suele ser el nombre real
                                        nombre_chat = max(candidatos, key=len)
                                        print(f"[WHATSAPP] [MÉTODO C] Nombre desde OCR {label}: '{nombre_chat}'")
                                        break
                                if nombre_chat:
                                    break
                    except Exception as e_ocr:
                        print(f"[WHATSAPP] OCR header final falló: {e_ocr}")
                print(f"[WHATSAPP] Nombre chat 🚬: {nombre_chat}")
                contacto = extraer_contacto_de_nombre_chat(nombre_chat) if nombre_chat else f"Contacto en Y={click_y}"
                print(f"[WHATSAPP] [MÉTODO C] ¡Mensaje detectado para '{contacto}' en ({click_x}, {click_y})!")

                conversacion = whatsapp_leer_conversacion(limite=3)
                return {"exito": True, "contacto": contacto, "conversacion": conversacion}
            else:
                print("[WHATSAPP] [MÉTODO C] No se detectaron círculos verdes.")

        except Exception as e_cv:
            print(f"[WHATSAPP] [MÉTODO C] Error en visión HSV: {e_cv}")

        print("[WHATSAPP] No se detectaron nuevos mensajes por ningún método.")
        return {"exito": False, "motivo": "No se encontraron mensajes no leídos (sin indicadores en UIA ni círculos verdes)."}

    except Exception as e:
        return {"exito": False, "motivo": f"Error crítico al detectar mensajes: {str(e)}"}

if __name__ == "__main__":
    # Pruebas manuales
    pass
