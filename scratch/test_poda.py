import sys
import os
from dotenv import load_dotenv

# Asegurar encoding UTF-8
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

load_dotenv()

# Añadir el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import agente

def test_poda_y_consolidacion():
    print("=== PROBANDO SISTEMA DE PODA Y CONSOLIDACIÓN LOCAL ===")
    
    # Instanciar el agente
    a = agente.Agent()
    
    # Limpiar historial existente para iniciar la prueba
    system_prompt = a.mensajes[0]
    a.mensajes = [system_prompt]
    
    print("\n1. Simulando interacción de 11 conversaciones del usuario...")
    # Agregamos 11 pares de user/assistant para forzar la poda (> 10)
    for i in range(11):
        a.mensajes.append({"role": "user", "content": f"Mensaje número {i+1} del usuario. ¿Cómo va todo?"})
        a.mensajes.append({"role": "assistant", "content": f"Respuesta número {i+1} de Ashly. Todo funciona bien."})
    
    # Añadir un mensaje de visión con OCR simulado pesado
    a.mensajes.append({
        "role": "user",
        "content": [
            {"type": "text", "text": "--- VISIÓN DIGITAL ACTUAL ---\nTEXTO DETECTADO (OCR):\nEste es un texto OCR súper largo y pesado que queremos podar para no colapsar la CPU local en los turnos siguientes..."},
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,IMAGEN_BASE64_FINGIDA"}}
        ]
    })
    
    user_msgs_count = sum(1 for m in a.mensajes if m.get("role") == "user" and isinstance(m.get("content"), str))
    print(f"Cantidad de mensajes de usuario (texto) antes de podar: {user_msgs_count}")
    print(f"Cantidad total de mensajes en el historial: {len(a.mensajes)}")
    
    print("\n2. Ejecutando intentar_consolidar_y_podar()...")
    # Para evitar llamar a la API real en la prueba unitaria de la estructura, mockearemos extraer_aprendizaje_local
    original_extraer = a.extraer_aprendizaje_local
    a.extraer_aprendizaje_local = lambda: "Ashly aprendió a optimizar la memoria y limpiar el historial de forma automática."
    
    a.intentar_consolidar_y_podar()
    
    # Restaurar
    a.extraer_aprendizaje_local = original_extraer
    
    # Verificar resultados
    print("\n3. Verificando resultados de la poda:")
    user_msgs_post = sum(1 for m in a.mensajes if m.get("role") == "user" and isinstance(m.get("content"), str))
    print(f"Cantidad de mensajes de usuario (texto) después de podar: {user_msgs_post}")
    print(f"Cantidad total de mensajes en el historial después de podar: {len(a.mensajes)}")
    print(f"Última memoria adquirida por el agente: {a.memoria_interna[-1]}")
    
    if len(a.mensajes) <= 3 and a.memoria_interna[-1] == "Ashly aprendió a optimizar la memoria y limpiar el historial de forma automática.":
        print("\n✅ PRUEBA EXITOSA: El historial fue podado correctamente y el aprendizaje fue consolidado.")
    else:
        print("\n❌ PRUEBA FALLIDA: Revisa la lógica de conteo y filtrado en intentar_consolidar_y_podar.")

if __name__ == "__main__":
    test_poda_y_consolidacion()
