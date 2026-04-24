import os
import json
import requests
import time
import EdiListRead
import teclado_pro
import movermouse
import tools
import analizarentorno
import vision
import win32_control
import entorno
from storage_manager import StorageManager
from dotenv import load_dotenv

# Importar SDK de Ollama de forma segura
try:
    from ollama import Client as OllamaClient
    _OLLAMA_SDK = True
except ImportError:
    _OLLAMA_SDK = False

load_dotenv()

# ── Backends ────────────────────────────────────────────────────────────────
LMSTUDIO_URL   = "http://localhost:1234/v1"
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")     # API key de https://ollama.com
OLLAMA_MODEL   = os.getenv("OLLAMA_MODEL", "gemini-3-flash-preview") # modelo Ollama por defecto
OLLAMA_HOST    = "https://ollama.com"                 # host oficial del SDK

# ── Resolución de pantalla y escalado de visión ────────────────────────────
SCREEN_W  = 1920   # ancho real del monitor
SCREEN_H  = 1080   # alto real del monitor
VISION_W  = 1280   # ancho de la imagen que ve el modelo (vision.py max_width)
SCREEN_SCALE_X = SCREEN_W / VISION_W                    # = 1.5
SCREEN_SCALE_Y = SCREEN_H / (SCREEN_H * VISION_W / SCREEN_W)  # = 1.5

class Agent:
    def __init__(self):
        self.storage = StorageManager()
        # Cargamos historial, memoria y recompensas desde los archivos JSON
        self.mensajes, self.memoria_interna, self.recompensas = self.storage.cargar_datos()
        
        if not self.mensajes:
            self.mensajes = [{"role": "system", "content": ""}]
            
        self.actualizar_prompt_sistema()
        self.setup_tools()

    def actualizar_prompt_sistema(self):
        """Actualiza el comportamiento principal e incluye la memoria y el sistema de recompensas."""
        base_prompt = "Eres Ashly, una asistente virtual amigable y servicial. Hablas en español.\n"
        base_prompt += f"SISTEMA DE RECOMPENSAS: Tienes {self.recompensas} puntos. Ganas puntos resolviendo tareas rápido y bien.\n"
        base_prompt += "Si notas que estás aprendiendo algo nuevo o una ruta importante, usa 'guardar_memoria'.\n"
        base_prompt += "siempre intentas llegar a cumplir el objetivo usando las herramientas que tienes a tu disposicion'.\n"
        base_prompt += "Persistencia: Tu historial y memoria se guardan automáticamente en archivos JSON.\n"
        base_prompt += "IMPORTANTE: NO INVENTES ACCIONES O COSAS QUE NO EXISTEN O NO CONOCES.\n"
        base_prompt += "La imagen que ves mide 1280x720 px. USA LAS COORDENADAS DE LA IMAGEN TAL CUAL — el sistema escala automáticamente a la pantalla real.\n"
        base_prompt += "Usar las herramientas correctas para cada tarea. Si una acción no produce cambios en la pantalla, NO LA REPITAS idéntica, intenta algo diferente.\n"
        base_prompt += "IMPORTANTE: Para escribir nombres, frases o texto largo usa 'escribir_texto'. 'presionar_teclas' es SOLO para teclas individuales o atajos (ctrl, alt, win, enter, etc).\n"
        base_prompt += "Puedes usar el mouse para clickear, arrastrar, hacer scroll y mover la ventana.\n"
        base_prompt += "Puedes usar el teclado para escribir, presionar teclas y atajos de teclado.\n"
        base_prompt += "No repitas las mismas acciones. Sé creativo y eficiente.\n"
        base_prompt += "VISIÓN: Por defecto NO ves la pantalla. Si el usuario te pide realizar una tarea en el PC, DEBES usar la herramienta 'ver_escritorio' primero para obtener el contexto visual. Si solo es una charla o pregunta general, no es necesario que mires.\n"

        if self.memoria_interna:
            base_prompt += "\n--- CONOCIMIENTOS ADQUIRIDOS ---\n"
            for nota in self.memoria_interna:
                base_prompt += f"- {nota}\n"
        
        self.mensajes[0]["content"] = base_prompt

    def setup_tools(self):
        """Inicializa las herramientas configuradas en tools.py."""
        self.tools = tools.get_tools()

    def _escalar_coords(self, x, y):
        """
        Convierte coordenadas del espacio de la imagen (1280px ancho)
        al espacio real de la pantalla (1920x1080).
        El modelo da coords en px de la imagen; multiplicamos por el factor de escala.
        """
        if x is None or y is None:
            return x, y
        rx = int(round(float(x) * SCREEN_SCALE_X))
        ry = int(round(float(y) * SCREEN_SCALE_Y))
        # Clamp a límites de pantalla para evitar coordenadas fuera de rango
        rx = max(0, min(rx, SCREEN_W - 1))
        ry = max(0, min(ry, SCREEN_H - 1))
        return rx, ry

    def _desescalar_coords(self, x, y):
        """
        Convierte coordenadas reales de pantalla (1920x1080)
        al espacio de la imagen que ve el modelo (1280px ancho).
        """
        if x is None or y is None:
            return x, y
        ix = int(round(float(x) / SCREEN_SCALE_X))
        iy = int(round(float(y) / SCREEN_SCALE_Y))
        return ix, iy

    def get_backend(self):
        """
        Detecta qué backend usar:
        - Intenta LM Studio primero (localhost:1234).
        - Si no hay modelos cargados o no está disponible, usa Ollama cloud (SDK oficial).
        Devuelve ("lmstudio"|"ollama"|None, model_id).
        """
        # ── Intentar LM Studio ──────────────────────────────────────────────
        try:
            response = requests.get(f"{LMSTUDIO_URL}/models", timeout=5)
            if response.status_code == 200:
                models_data = response.json().get("data", [])
                if models_data:
                    model_id = models_data[0]["id"]
                    print(f"🖥️  LM Studio activo → modelo: {model_id}")
                    return "lmstudio", model_id
        except Exception:
            pass  # LM Studio no disponible, seguimos al fallback

        # ── Fallback: Ollama cloud (SDK oficial) ────────────────────────────
        if OLLAMA_API_KEY and OLLAMA_API_KEY not in ("", "Ollama_API_KEY"):
            if not _OLLAMA_SDK:
                print("❌ Librería 'ollama' no instalada. Ejecuta: pip install ollama")
                return None, None
            print(f"☁️  LM Studio sin modelos. Usando Ollama cloud → {OLLAMA_MODEL}")
            return "ollama", OLLAMA_MODEL

        print("❌ Sin backend disponible: LM Studio sin modelos y sin OLLAMA_API_KEY configurada.")
        return None, None

    def _request_lmstudio(self, model):
        """Llama a LM Studio via HTTP (OpenAI-compatible)."""
        response = requests.post(
            f"{LMSTUDIO_URL}/chat/completions",
            json={
                "model": model,
                "messages": self.mensajes,
                "tools": self.tools,
                "temperature": 0.7,
                "max_tokens": 2000
            },
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("choices", [{}])[0].get("message", {})
        print(f"Error LM Studio: {response.status_code} - {response.text}")
        return None

    def _normalizar_mensajes_ollama(self, mensajes):
        """
        Convierte mensajes al formato aceptado por el SDK de Ollama.
        Garantiza la presencia de 'thought' para modelos Gemini Thinking.
        """
        resultado = []
        for m in mensajes:
            msg_norm = {
                "role": m.get("role"),
                "content": ""
            }

            # 1. Extraer texto del contenido (maneja simple o multimodal)
            content_raw = m.get("content", "") or ""
            if isinstance(content_raw, list):
                texto = ""
                for parte in content_raw:
                    if isinstance(parte, dict) and parte.get("type") == "text":
                        texto += parte.get("text", "")
                msg_norm["content"] = texto
            else:
                msg_norm["content"] = str(content_raw)

            # 2. Gestión de pensamiento (Crítico para Gemini)
            # Buscamos pensamiento en el mensaje original
            thought = m.get("thought") or m.get("reasoning_content")
            
            # Si el asistente llama a una herramienta, el thought es obligatorio
            if msg_norm["role"] == "assistant" and m.get("tool_calls"):
                if not thought:
                    thought = "Analizando la situación y seleccionando la herramienta adecuada..."
                msg_norm["thought"] = thought
                msg_norm["thought_signature"] = thought # Requerido explícitamente por Gemini
                
                # INYECCIÓN CRÍTICA: Asegurar que haya algo de texto en content
                if not msg_norm.get("content"):
                    msg_norm["content"] = thought
            elif thought:
                msg_norm["thought"] = thought

            # 3. Herramientas y Resultados
            if m.get("tool_calls"):
                tcs_limpias = []
                for tc in m["tool_calls"]:
                    tc_norm = {
                        "id": tc.get("id"),
                        "type": "function",
                        "function": {
                            "name": tc["function"]["name"],
                            "arguments": tc["function"]["arguments"]
                        }
                    }
                    # Asegurar que los argumentos sean dict
                    if isinstance(tc_norm["function"]["arguments"], str):
                        try:
                            tc_norm["function"]["arguments"] = json.loads(tc_norm["function"]["arguments"])
                        except:
                            tc_norm["function"]["arguments"] = {}
                    tcs_limpias.append(tc_norm)
                msg_norm["tool_calls"] = tcs_limpias
            
            # Respuesta de herramienta
            if m.get("tool_call_id"):
                msg_norm["tool_call_id"] = m["tool_call_id"]
                msg_norm["name"] = m.get("name")

            # 4. Imágenes
            if m.get("images"):
                msg_norm["images"] = m["images"]

            resultado.append(msg_norm)
        return resultado

    def _request_ollama(self, model):
        """Llama a Ollama cloud usando requests nativo para no perder campos críticos (Gemini)."""
        import requests
        mensajes_normalizados = self._normalizar_mensajes_ollama(self.mensajes)
        
        payload = {
            "model": model,
            "messages": mensajes_normalizados,
            "tools": self.tools,
            "stream": False
        }
        
        headers = {"Content-Type": "application/json"}
        if OLLAMA_API_KEY:
            headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"
            
        # Petición directa al servidor para saltarse el filtro estricto de la librería
        response = requests.post(f"{OLLAMA_HOST}/api/chat", json=payload, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"API Error {response.status_code}: {response.text}")
            
        resp_json = response.json()
        msg = resp_json.get("message", {})
        
        result = {"role": msg.get("role", "assistant"), "content": msg.get("content", "")}
        
        # Capturamos el razonamiento sea como sea que el proxy lo devuelva
        for key in ['thought', 'reasoning_content', 'reasoning', 'thought_signature']:
            if msg.get(key):
                result["thought"] = msg[key]
                break
                
        if msg.get("tool_calls"):
            tcs = []
            for i, tc in enumerate(msg["tool_calls"]):
                fn = tc.get("function", {})
                tcs.append({
                    "id": tc.get("id", f"call_{i}"),
                    "type": "function",
                    "function": {
                        "name": fn.get("name", ""),
                        "arguments": json.dumps(fn.get("arguments", {}))
                    }
                })
            result["tool_calls"] = tcs
            
        return result

    def generate_response(self, steps=0):
        """Genera una respuesta usando el modelo activo y procesa las herramientas."""
        if steps > 20:
            return "⚠️ Ashly se detuvo para evitar un bucle infinito de herramientas."
            
        backend, model = self.get_backend()
        if not model:
            return "❌ No hay backend disponible. Carga un modelo en LM Studio o configura OLLAMA_API_KEY en el archivo .env"
        
        # VISIÓN AUTÓNOMA: Eliminada la captura automática. 
        # Ahora Ashly decidirá si usar 'ver_escritorio' según las instrucciones del prompt.
        
        try:
            if backend == "lmstudio":
                message = self._request_lmstudio(model)
            else:
                message = self._request_ollama(model)

            if message is None:
                return "Error al obtener respuesta del backend."

            if True:  # bloque unificado de procesamiento
                
                # Verificar si la IA decidió usar una herramienta
                if message.get("tool_calls"):
                    print("\n⚙️ Ashly está usando una herramienta...")
                    # Añadir el mensaje de la IA pidiendo usar la herramienta al historial
                    self.mensajes.append(message)
                    
                    # Procesar cada herramienta llamada
                    for tool_call in message["tool_calls"]:
                        function_name = tool_call["function"]["name"]
                        
                        try:
                            arguments = json.loads(tool_call["function"]["arguments"])
                        except Exception:
                            arguments = {}
                            
                        print(f"   -> Ejecutando: {function_name}({arguments})")
                        
                        if function_name == "list_files":
                            resultado = EdiListRead.list_files(**arguments)
                        elif function_name == "guardar_memoria":
                            resultado = self.guardar_memoria(**arguments)
                        elif function_name == "edit_file":
                            resultado = EdiListRead.edit_file(**arguments)
                        elif function_name == "read_file":
                            resultado = EdiListRead.read_file(**arguments)
                        elif function_name == "dar_recompensa":
                            resultado = self.dar_recompensa(**arguments)
                        elif function_name == "escribir_texto":
                            resultado = teclado_pro.escribir_humanamente(**arguments)
                        elif function_name == "presionar_teclas":
                            resultado = teclado_pro.presionar_combinacion(**arguments)
                        elif function_name == "mover_mouse":
                            x, y = self._escalar_coords(arguments.get('x'), arguments.get('y'))
                            print(f"      🖱️  imagen ({arguments.get('x')},{arguments.get('y')}) → pantalla ({x},{y})")
                            resultado = movermouse.MouseOperator().smooth_move(target=(x, y))
                        elif function_name == "arrastrar_y_soltar":
                            x1, y1 = self._escalar_coords(arguments.get('x1'), arguments.get('y1'))
                            x2, y2 = self._escalar_coords(arguments.get('x2'), arguments.get('y2'))
                            print(f"      🖱️  arrastre imagen ({arguments.get('x1')},{arguments.get('y1')})→({arguments.get('x2')},{arguments.get('y2')}) → pantalla ({x1},{y1})→({x2},{y2})")
                            resultado = movermouse.MouseOperator().drag_and_drop(origin=(x1, y1), target=(x2, y2))
                        elif function_name == "analizar_entorno":
                            res = analizarentorno.analizar_entorno()
                            # Desescalar coordenadas en el resultado para que coincidan con la visión de la IA
                            if isinstance(res, dict) and "ventanas" in res:
                                for v in res["ventanas"]:
                                    if "box" in v:
                                        v["box"]["x"], v["box"]["y"] = self._desescalar_coords(v["box"]["x"], v["box"]["y"])
                                        v["box"]["w"], v["box"]["h"] = self._desescalar_coords(v["box"]["w"], v["box"]["h"])
                                    if "centro" in v:
                                        v["centro"][0], v["centro"][1] = self._desescalar_coords(v["centro"][0], v["centro"][1])
                            resultado = res
                        elif function_name == "click_izquierdo":
                            resultado = movermouse.MouseOperator().left_click()
                        elif function_name == "click_derecho":
                            resultado = movermouse.MouseOperator().right_click()
                        elif function_name == "click_central":
                            resultado = movermouse.MouseOperator().middle_click()
                        elif function_name == "scroll_mouse":
                            resultado = movermouse.MouseOperator().scroll_mouse(**arguments)
                        elif function_name == "ver_escritorio":
                            resultado = self.automirar() or "Vision actualizada correctamente."
                        # ── Win32 ──────────────────────────────────────────
                        elif function_name == "controlar_ventana":
                            resultado = win32_control.controlar_ventana(**arguments)
                        elif function_name == "abrir_programa":
                            resultado = win32_control.abrir_programa(**arguments)
                        elif function_name == "listar_ventanas_win32":
                            resultado = win32_control.listar_ventanas_abiertas()
                        elif function_name == "mover_ventana":
                            x, y = self._escalar_coords(arguments.get('x'), arguments.get('y'))
                            w, h = self._escalar_coords(arguments.get('ancho'), arguments.get('alto'))
                            print(f"      🪟  ventana imagen ({arguments.get('x')},{arguments.get('y')}, w={arguments.get('ancho')}, h={arguments.get('alto')}) → pantalla ({x},{y}, w={w}, h={h})")
                            # Actualizamos los argumentos con los valores escalados
                            args_escalados = dict(arguments)
                            args_escalados['x'], args_escalados['y'] = x, y
                            args_escalados['ancho'], args_escalados['alto'] = w, h
                            resultado = win32_control.mover_redimensionar_ventana(**args_escalados)
                        # ── Entorno / Sistema ──────────────────────────────
                        elif function_name == "obtener_contexto_sistema":
                            res = entorno.obtener_contexto_sistema()
                            # Desescalar cursor
                            if isinstance(res, dict) and "cursor" in res and isinstance(res["cursor"], dict):
                                cx, cy = res["cursor"].get("x"), res["cursor"].get("y")
                                res["cursor"]["x"], res["cursor"]["y"] = self._desescalar_coords(cx, cy)
                            resultado = res
                        elif function_name == "listar_procesos":
                            resultado = entorno.listar_procesos_activos()
                        elif function_name == "leer_portapapeles":
                            resultado = entorno.leer_portapapeles()
                        elif function_name == "escribir_portapapeles":
                            resultado = entorno.escribir_portapapeles(**arguments)
                        else:
                            resultado = f"Error: herramienta '{function_name}' no encontrada"
                            
                        # Añadir el resultado de la herramienta al historial
                        self.mensajes.append({
                            "tool_call_id": tool_call["id"],
                            "role": "tool",
                            "name": function_name,
                            "content": str(resultado)
                        })
                        
                    # Volver a llamar a la IA con los resultados para que formule su respuesta final
                    time.sleep(1.0)  # Esperar a que la UI se actualice completamente
                    return self.generate_response(steps=steps + 1)

                return message.get("content", "")
            else:
                return f"Error en la generación: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error al generar respuesta: {e}"

    def automirar(self):
        """Captura la pantalla y actualiza el contexto visual para la IA."""
        try:
            print("👀 Ashly está mirando la pantalla...")
            texto_ocr, img_b64 = vision.preparar_vision_data()
            
            # Limpiamos el historial de mensajes de visión anteriores para no saturar
            # Mantenemos solo las últimas 3 visiones para dar continuidad visual
            vision_indices = []
            for i, m in enumerate(self.mensajes):
                if isinstance(m.get("content"), list):
                    vision_indices.append(i)
                elif isinstance(m.get("content"), str) and "VISIÓN DIGITAL" in m.get("content"):
                    vision_indices.append(i)
            
            # Si hay más de 3 visiones, borrar las más antiguas
            if len(vision_indices) > 2:
                for idx in reversed(vision_indices[:-2]): # Dejamos las 2 últimas + la nueva que viene
                    self.mensajes.pop(idx)

            if img_b64:
                # Añadimos la visión actual como el contexto más reciente del sistema/usuario
                # Usamos una estructura multi-modal compatible con Qwen 3.5
                contenido_vision = [
                    {
                        "type": "text", 
                        "text": f"--- VISIÓN DIGITAL ACTUAL ---\nTEXTO DETECTADO (OCR):\n{texto_ocr}\n----------------------------"
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
                    }
                ]
                self.mensajes.append({"role": "user", "content": contenido_vision})
        except Exception as e:
            print(f"Error al intentar mirar: {e}")

    def guardar_memoria(self, dato):
        """Guarda un dato en la memoria interna y actualiza el prompt para que la IA sea consciente."""
        self.memoria_interna.append(dato)
        self.actualizar_prompt_sistema()
        return "Notificación: Dato guardado exitosamente en tu memoria interna."

    def dar_recompensa(self, puntos, motivo):
        """Aumenta los puntos de recompensa y guarda el estado."""
        self.recompensas += puntos
        self.actualizar_prompt_sistema()
        return f"¡Recompensa recibida! +{puntos} puntos. Motivo: {motivo}"

    def guardar_estado(self):
        """Helper para llamar al storage manager."""
        self.storage.guardar_completamente(self.mensajes, self.memoria_interna, self.recompensas)

    def run(self):
        print(f"Iniciando Ashly v2. Experiencia actual: {self.recompensas} puntos.")
        print("Historial cargado. Escribe 'salir' para terminar.")
        while True:
            userEnvio = input("\nUsuario: ").strip()
            if not userEnvio:
                continue
            elif userEnvio.lower() in ["salir", "adios", "bye", "chao"]:
                self.guardar_estado()
                print("Ashly: ¡Adiós! (Estado guardado)")
                break
            else:
                self.mensajes.append({"role": "user", "content": userEnvio})
                resAshly = self.generate_response()
                print(f"\nAshly: {resAshly}")
                self.mensajes.append({"role": "assistant", "content": resAshly})
                # Guardar en cada interacción para no perder nada si se cierra
                self.guardar_estado()
