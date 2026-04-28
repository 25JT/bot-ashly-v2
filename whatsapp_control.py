import uiautomation as auto
import time
import win32_control

def whatsapp_enviar_mensaje(contacto: str, mensaje: str) -> str:
    """
    Busca un contacto y envía un mensaje en WhatsApp Desktop de forma programática.
    """
    try:
        # 1. Traer WhatsApp al frente
        win32_control.controlar_ventana("WhatsApp", "enfocar")
        time.sleep(1)
        
        whatsapp = auto.WindowControl(Name="WhatsApp")
        if not whatsapp.Exists(0):
            # Reintento por clase si el nombre falla
            whatsapp = auto.WindowControl(ClassName="WinUIDesktopWin32WindowClass", Name="WhatsApp")
            
        if not whatsapp.Exists(2):
            return "Error: No se pudo localizar la ventana de WhatsApp. Asegúrate de que esté abierta."

        # 2. Buscar el chat (Contacto o Número)
        # Probamos nombres comunes del cuadro de búsqueda en español e inglés
        busqueda = None
        for nombre in ["Buscar un chat o iniciar uno nuevo", "Search or start new chat", "Buscar"]:
            busqueda = whatsapp.EditControl(Name=nombre)
            if busqueda.Exists(0):
                break
        
        if busqueda and busqueda.Exists(1):
            busqueda.Click()
            # Limpiar búsqueda anterior
            busqueda.SendKeys('{Ctrl}a{BackSpace}', waitTime=0.5)
            busqueda.SendKeys(contacto, waitTime=0.5)
            time.sleep(1)
            busqueda.SendKeys('{Enter}')
            time.sleep(1)
        else:
            # Si no hay cuadro de búsqueda, intentamos Ctrl+F (atajo de búsqueda en WhatsApp)
            whatsapp.SendKeys('{Ctrl}f')
            time.sleep(0.5)
            auto.SendKeys(contacto + '{Enter}')
            time.sleep(1)

        # 3. Escribir y enviar el mensaje
        caja_texto = None
        for nombre in ["Escribe un mensaje", "Type a message", "Mensaje"]:
            caja_texto = whatsapp.EditControl(Name=nombre)
            if caja_texto.Exists(0):
                break
                
        if caja_texto and caja_texto.Exists(1):
            caja_texto.Click()
            # Escribir el mensaje (usamos SendKeys para que sea natural)
            caja_texto.SendKeys(mensaje, waitTime=0.01) # Rápido pero seguro
            time.sleep(0.5)
            caja_texto.SendKeys('{Enter}')
            return f"Mensaje enviado a '{contacto}' exitosamente."
        else:
            return "Error: No se pudo encontrar el cuadro de escritura de mensajes."

    except Exception as e:
        return f"Error crítico al manejar WhatsApp: {str(e)}"

def whatsapp_obtener_ultimo_mensaje() -> str:
    """
    Intenta leer el contenido del último mensaje en el chat abierto.
    """
    try:
        win32_control.controlar_ventana("WhatsApp", "enfocar")
        whatsapp = auto.WindowControl(Name="WhatsApp")
        
        # Los mensajes suelen estar en una lista o grupo
        # Este selector es complejo porque cambia con las versiones, pero intentamos lo más común
        mensajes = whatsapp.ListControl(Name="Lista de mensajes")
        if not mensajes.Exists(0):
            mensajes = whatsapp.GroupControl(Name="Mensajes")
            
        if mensajes.Exists(1):
            # Obtener el último hijo que sea un elemento de mensaje
            items = mensajes.GetChildren()
            if items:
                ultimo = items[-1]
                return f"Último mensaje detectado: {ultimo.Name}"
        
        return "No se pudo leer el contenido de los mensajes."
    except Exception as e:
        return f"Error al leer mensajes: {str(e)}"

if __name__ == "__main__":
    # Prueba manual: whatsapp_enviar_mensaje("Mi Numero", "Hola desde Ashly!")
    pass
