import os
import json
import time
import requests
import base64
import vision
import win32_control
from dotenv import load_dotenv

load_dotenv()

# --- Configuración de Backend ---
LMSTUDIO_URL   = "http://localhost:1234/v1"
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "e75eb02879a24cb38fc2131a0d2d6759.4uNUPc3BtiWNBPb2ekZXuM8i")
OLLAMA_MODEL   = os.getenv("OLLAMA_MODEL", "gemini-3-flash-preview")

MEMORIA_PATH = "memoria_agente.json"

def get_backend():
    """Detecta qué backend usar para el análisis."""
    try:
        response = requests.get(f"{LMSTUDIO_URL}/models", timeout=2)
        if response.status_code == 200:
            models = response.json().get("data", [])
            if models: return "lmstudio", models[0]["id"]
    except: pass
    
    if OLLAMA_API_KEY: return "ollama", OLLAMA_MODEL
    return None, None

def guardar_aprendizaje(nuevo_conocimiento):
    """Añade un aprendizaje a la memoria si no existe ya."""
    if not os.path.exists(MEMORIA_PATH):
        data = {"recompensas": 50, "conocimientos": []}
    else:
        try:
            with open(MEMORIA_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            data = {"recompensas": 50, "conocimientos": []}
    
    # Limpieza básica para evitar duplicados semánticos
    if nuevo_conocimiento not in data["conocimientos"]:
        data["conocimientos"].append(nuevo_conocimiento)
        with open(MEMORIA_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    return False

def observar_y_aprender():
    backend, model = get_backend()
    if not backend:
        print("❌ No se encontró un backend activo (LM Studio u Ollama Cloud).")
        return

    print(f"\n🕵️  MODO OBSERVADOR ACTIVADO")
    print(f"Backend: {backend} | Modelo: {model}")
    print("Ashly está observando tu pantalla para aprender tus hábitos y rutas...")
    print("Presiona Ctrl+C para detener.\n")

    while True:
        try:
            # 1. Capturar pantalla y OCR
            # Reducimos el ancho a 800 para que el modelo local procese más rápido y no dé timeout
            texto_ocr, imagen_b64 = vision.preparar_vision_data(max_width=800, forzar=True)
            
            # Intentar identificar la ventana principal para dar contexto
            contexto_ventana = "Escritorio / Desconocido"
            try:
                ventanas = win32_control.listar_ventanas_win32()
                if ventanas:
                    # El primer elemento suele ser la ventana activa o una de las principales
                    contexto_ventana = ventanas[0].get('titulo', 'Escritorio')
            except: pass

            # 2. Construir el prompt de aprendizaje
            prompt = f"""
            [MODO SOMBRA - APRENDIZAJE AUTÓNOMO]
            Estás observando la pantalla del usuario. Tu meta es aprender de sus acciones para ser una mejor asistente.
            
            CONTEXTO ACTUAL:
            - Ventana: {contexto_ventana}
            - Texto detectado: {texto_ocr[:500]}...

            INSTRUCCIONES:
            1. Mira la imagen y el texto. ¿Qué está haciendo el usuario?
            2. ¿Hay algún flujo de trabajo, botón, ruta de archivo o preferencia que debas recordar?
            3. Si detectas un aprendizaje útil, redáctalo como un 'Conocimiento Adquirido' corto.
               Ejemplo: "Ruta: El usuario abre sus proyectos desde C:/Proyectos/Ashly"
               Ejemplo: "Preferencia: En Spotify, el usuario siempre elige la playlist 'Descubrimiento Semanal'"
            4. Si lo que ves es trivial (navegación simple, nada nuevo, o pantalla de carga), responde exactamente: NADA.

            RESPUESTA:
            Solo el aprendizaje o NADA. Sin explicaciones.
            """

            # 3. Consultar a la IA
            analisis = "NADA"
            if backend == "lmstudio":
                payload = {
                    "model": model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{imagen_b64}"}}
                            ]
                        }
                    ],
                    "temperature": 0.2
                }
                # Aumentamos timeout a 120 segundos para modelos locales pesados
                response = requests.post(f"{LMSTUDIO_URL}/chat/completions", json=payload, timeout=120)
                if response.status_code == 200:
                    analisis = response.json()['choices'][0]['message']['content'].strip()
            
            elif backend == "ollama":
                try:
                    from ollama import Client
                    client = Client()
                    response = client.chat(
                        model=model,
                        messages=[{'role': 'user', 'content': prompt, 'images': [base64.b64decode(imagen_b64)]}]
                    )
                    analisis = response['message']['content'].strip()
                except ImportError:
                    print("❌ Error: Librería 'ollama' no instalada. No se puede usar el modo sombra con Ollama Cloud.")
                    break
                except Exception as e_ollama:
                    print(f"⚠️ Error en Ollama: {e_ollama}")

            # 4. Registrar aprendizaje si es válido
            if analisis.upper() != "NADA" and len(analisis) > 8:
                if guardar_aprendizaje(analisis):
                    print(f"✨ [APRENDIZAJE] {analisis}")
                else:
                    # Ya lo conocía, no imprimimos para no saturar
                    pass
            
        except KeyboardInterrupt:
            print("\n👋 Modo observador finalizado.")
            break
        except Exception as e:
            print(f"⚠️  Error en observación: {e}")

        # Intervalo de observación: Cada 20 segundos para no saturar el backend
        time.sleep(20)

if __name__ == "__main__":
    observar_y_aprender()
