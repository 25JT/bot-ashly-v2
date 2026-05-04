import uiautomation as auto
import time
import win32_control
import teclado_pro

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
        nombres_caja = ["Escribe un mensaje", "Type a message", "Mensaje", "Escribir mensaje"]
        
        for nombre in nombres_caja:
            caja_texto = whatsapp.EditControl(Name=nombre)
            if caja_texto.Exists(0):
                break
                
        if not caja_texto or not caja_texto.Exists(1):
            # Reintento: A veces el control de edición no tiene nombre pero es el único Documento o Edit principal
            caja_texto = whatsapp.DocumentControl() # En algunas versiones es un DocumentControl
            if not caja_texto.Exists(0):
                caja_texto = whatsapp.EditControl(searchDepth=2) # Intentar buscar uno genérico cerca

        if caja_texto and caja_texto.Exists(1):
            caja_texto.Click()
            time.sleep(0.5)
            teclado_pro.escribir_humanamente(mensaje)
            time.sleep(0.5)
            teclado_pro.presionar_combinacion(['enter'])
            return f"Mensaje enviado a '{contacto}' exitosamente."
        else:
            return "Error: No se pudo encontrar el cuadro de escritura de mensajes (el chat podría no haber cargado o el contacto no existe)."

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
    Lee los últimos mensajes de la conversación activa.
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

        # Intentar localizar la lista de mensajes
        mensajes_list = whatsapp.ListControl(Name="Lista de mensajes")
        if not mensajes_list.Exists(0):
            mensajes_list = whatsapp.GroupControl(Name="Mensajes")
        
        if not mensajes_list.Exists(1):
            return "No se pudo encontrar la lista de mensajes en el chat actual."

        items = mensajes_list.GetChildren()
        if not items:
            return "La conversación parece estar vacía."

        # Tomar los últimos N mensajes
        recientes = items[-limite:]
        historial = []
        for item in recientes:
            # El Name suele contener el remitente, hora y texto (formato de accesibilidad)
            historial.append(f"- {item.Name}")

        return "\n".join(historial)
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
        return f"Error al navegar en WhatsApp: {str(e)}"

if __name__ == "__main__":
    # Pruebas manuales
    pass
