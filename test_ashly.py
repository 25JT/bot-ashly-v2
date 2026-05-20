import sys
import agente
import os
from dotenv import load_dotenv

# Forzar UTF-8 en la salida de consola en Windows para evitar UnicodeEncodeError con emojis
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

load_dotenv()

def test_response():
    print("Iniciando prueba de respuesta...")
    a = agente.Agent()
    
    # Simular un mensaje simple
    a.mensajes.append({"role": "user", "content": "Hola Ashly, ¿me escuchas?"})
    
    print("Generando respuesta...")
    res = a.generate_response()
    
    print(f"Respuesta de Ashly: '{res}'")
    if not res:
        print("ALERTA: La respuesta sigue siendo vacía.")
    else:
        print("ÉXITO: Respuesta recibida.")

if __name__ == "__main__":
    test_response()
