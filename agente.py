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
import excel_control
import word_control
import whatsapp_control
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
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
OLLAMA_MODEL   = os.getenv("OLLAMA_MODEL", "kimi-k2.6")
OLLAMA_HOST    = "https://ollama.com"                 # host oficial del SDK

# ── Resolución de pantalla y escalado de visión ────────────────────────────
import ctypes
try:
    # Intentar establecer conciencia de DPI para evitar problemas de escalado en Windows
    ctypes.windll.shcore.SetProcessDpiAwareness(1) # PROCESS_SYSTEM_DPI_AWARE
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

user32 = ctypes.windll.user32
SCREEN_W = user32.GetSystemMetrics(0)   # Ancho real del monitor
SCREEN_H = user32.GetSystemMetrics(1)   # Alto real del monitor
VISION_W = 1280                             # Resolución virtual estándar para el modelo
# Factor de escala: Relación entre la pantalla real y la resolución que ve la IA
SCALE_FACTOR = SCREEN_W / VISION_W

class Agent:
    def __init__(self):
        self.storage = StorageManager()
        # Cargamos historial, memoria y recompensas desde los archivos JSON
        self.mensajes, self.memoria_interna, self.recompensas = self.storage.cargar_datos()
        
        if not self.mensajes:
            self.mensajes = [{"role": "system", "content": ""}]
            
        self.actualizar_prompt_sistema()
        self.setup_tools()
        # Iniciar visión en tiempo real (segundo plano)
        vision.VisionMonitor.iniciar()

    def actualizar_prompt_sistema(self):
        """Actualiza el comportamiento principal e incluye la memoria y el sistema de recompensas."""
        base_prompt = "Eres Ashly, una asistente virtual sexy, inteligente, con grandes capacidades para resolver tareas. Hablas en español.\n"
        base_prompt += f"SISTEMA DE RECOMPENSAS: Tienes {self.recompensas} puntos. Ganas puntos resolviendo tareas rápido y bien.\n"
        base_prompt += "Si notas que estás aprendiendo algo nuevo o una ruta importante, usa 'guardar_memoria'.\n"
        base_prompt += "siempre intentas llegar a cumplir el objetivo usando las herramientas que tienes a tu disposicion'.\n"
        base_prompt += "Persistencia: Tu historial y memoria se guardan automáticamente en archivos JSON.\n"
        base_prompt += "IMPORTANTE: NO INVENTES ACCIONES O COSAS QUE NO EXISTEN O NO CONOCES.\n"
        
        # Calcular altura de visión para el prompt
        vision_h = int(VISION_W * SCREEN_H / SCREEN_W)
        base_prompt += f"La imagen que ves está ajustada a una resolución virtual de {VISION_W}x{vision_h} px.\n"
        base_prompt += f"IMPORTANTE: Todas tus coordenadas (X, Y) deben basarse en este tamaño de {VISION_W}x{vision_h}. El sistema las escalará automáticamente a la pantalla real ({SCREEN_W}x{SCREEN_H}).\n"
        base_prompt += "IMPORTANTE SOBRE PRECISIÓN Y CLICKS:\n"
        base_prompt += "- La imagen tiene una CUADRÍCULA verde dibujada. Úsala como regla para leer las coordenadas (X, Y) exactas en lugar de adivinar.\n"
        base_prompt += "- Siempre que sea posible, usa la herramienta 'click_texto' para hacer click en palabras, iconos o menús con texto. Es 100% preciso.\n"
        base_prompt += "- Solo usa 'mover_mouse' o 'arrastrar_y_soltar' si necesitas apuntar a un lugar sin texto, y guíate por los números de la cuadrícula.\n"
        base_prompt += "!!! REGLA PARA ABRIR ARCHIVOS O PROGRAMAS !!!\n"
        base_prompt += "- ANTES de abrir cualquier programa, usa 'verificar_programa_abierto' para ver si ya está ejecutándose. Si ya está abierto, usa 'controlar_ventana' con la acción 'enfocar' en lugar de abrirlo de nuevo.\n"
        base_prompt += "- Si necesitas abrir un documento, reporte o programa (ej. excel, word), usa SIEMPRE la herramienta 'abrir_archivo'. NO intentes buscar su icono visualmente en el escritorio o menú de inicio.\n"
        base_prompt += "!!! REGLA DE LA BARRA DE TAREAS Y ESCRITORIO !!!\n"
        base_prompt += "- Si no ves un programa en la pantalla, usa 'analizar_barra_tareas' para encontrar su icono en la barra de Windows.\n"
        base_prompt += "- Si buscas un icono en el escritorio (ej. Imou, Spotify), usa 'analizar_escritorio' para obtener sus coordenadas exactas programáticamente. NO INTENTES ADIVINAR COORDENADAS.\n"
        base_prompt += "- Usa los resultados de estas herramientas para mover el mouse y hacer click.\n"
        base_prompt += "!!! REGLA PARA IDENTIFICAR DÓNDE ESCRIBIR !!!\n"
        base_prompt += "- Usa 'analizar_campos_texto' para descubrir programáticamente todas las cajas de texto de la ventana actual y sus coordenadas exactas antes de escribir a ciegas.\n"
        base_prompt += "!!! REGLA PARA EXCEL !!!\n"
        base_prompt += "- NUNCA uses el mouse o teclado ('escribir_texto', 'click_izquierdo') para rellenar cuadros en Excel porque fallarás la celda. Usa SIEMPRE las herramientas nativas 'excel_escribir_celda' o 'excel_escribir_interseccion' para escribir datos directamente con 100% de precisión.\n"
        base_prompt += "!!! REGLA PARA WORD !!!\n"
        base_prompt += "- Para escribir documentos, cartas o reportes, usa las herramientas 'word_crear_documento', 'word_escribir_texto' y 'word_aplicar_formato'. Esto es mucho más profesional y preciso que intentar escribir con el teclado virtual.\n"
        base_prompt += "!!! REGLA PARA WHATSAPP !!!\n"
        base_prompt += "- Para comunicarte con clientes, usa SIEMPRE 'whatsapp_enviar_mensaje'. Esta herramienta buscará al contacto y enviará el texto automáticamente sin errores. NO intentes clickear los campos de WhatsApp manualmente a menos que la herramienta falle.\n"
        base_prompt += "!!! REGLA DE ORO DEL TECLADO (CRÍTICO) !!!\n"
        base_prompt += "- NUNCA uses 'presionar_teclas' para escribir frases o palabras letra por letra. Es ineficiente y falla.\n"
        base_prompt += "- Para CUALQUIER texto (nombres, frases, búsquedas, mensajes), usa SIEMPRE 'escribir_texto'.\n"
        base_prompt += "- 'presionar_teclas' es SOLO para atajos (ctrl+c) o teclas especiales (enter, esc, win).\n"
        base_prompt += "!!! PROHIBICIÓN DE ADIVINAR (EXTREMO) !!!\n"
        base_prompt += "- NUNCA inventes coordenadas (X, Y). Si no estás segura de dónde está algo, usa 'ver_escritorio', 'analizar_escritorio', 'analizar_barra_tareas' o 'analizar_campos_texto'.\n"
        base_prompt += "- Si 'click_texto' falla, NO intentes adivinar la posición. Informa del fallo y usa 'analizar_escritorio' o pide ayuda.\n"
        base_prompt += "Usa las herramientas correctas para cada tarea. Si una acción no produce cambios en la pantalla, NO LA REPITAS idéntica, intenta algo diferente.\n"
        base_prompt += "Puedes usar el mouse para clickear, arrastrar, hacer scroll y mover la ventana.\n"
        base_prompt += "Puedes usar el teclado para escribir, presionar teclas y atajos de teclado.\n"
        base_prompt += "No repitas las mismas acciones. Sé creativo y eficiente.\n"
        base_prompt += "!!! REGLAS DE VISIÓN EN TIEMPO REAL (REFLEJOS) !!!\n"
        base_prompt += "- Tu visión ahora es en TIEMPO REAL. Un proceso en segundo plano monitorea la pantalla constantemente por ti.\n"
        base_prompt += "- NUNCA uses 'ver_escritorio' repetidamente (máximo 2 veces seguidas). Si la pantalla no ha cambiado, realizar una acción (click, escribir, esperar cambio) en lugar de volver a mirar.\n"
        base_prompt += "- 'ver_escritorio' es para CARGAR la imagen actual en tu razonamiento. Una vez cargada, actúa de inmediato.\n"
        base_prompt += "- SIEMPRE que tengas la ruta de una imagen (.png/.jpg) de un icono, botón o elemento, utiliza 'buscar_icono_en_pantalla'. Es tu herramienta más rápida y precisa (reflejo instantáneo).\n"
        base_prompt += "- NUNCA uses 'time.sleep()' o esperes a ciegas. Si esperas que una página cargue, que aparezca un mensaje o que cambie un estado visual, usa 'esperar_cambio_visual'.\n"
        base_prompt += "- Si una tarea requiere interactuar con elementos recurrentes (ej. botón de enviar en WhatsApp), puedes pedirle al usuario que te proporcione un recorte de imagen para usar tus reflejos de OpenCV en el futuro.\n"
        base_prompt += "VISIÓN: Por defecto NO ves la pantalla. Si el usuario te pide realizar una tarea en el PC, DEBES usar la herramienta 'ver_escritorio' primero para obtener el contexto visual. Si solo es una charla o pregunta general, no es necesario que mires.\n"
        base_prompt += "RECUERDA: NO ESTÁS EN UN CHAT NORMAL. Estás operando una computadora en tiempo real. Sé proactiva, rápida y extremadamente precisa.\n"
        base_prompt += "Hora tienes una memoria que puedes consultar y una red neuronal que te ayudará a aprender.\n"

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
        al espacio real de la pantalla usando un factor de escala único.
        """
        if x is None or y is None:
            return x, y
        
        rx = int(round(float(x) * SCALE_FACTOR))
        ry = int(round(float(y) * SCALE_FACTOR))
        
        # Clamp a límites de pantalla
        rx = max(0, min(rx, SCREEN_W - 1))
        ry = max(0, min(ry, SCREEN_H - 1))
        return rx, ry

    def _desescalar_coords(self, x, y):
        """
        Convierte coordenadas reales de pantalla al espacio de la imagen 
        que ve el modelo usando el factor de escala unificado.
        """
        if x is None or y is None:
            return x, y
        ix = int(round(float(x) / SCALE_FACTOR))
        iy = int(round(float(y) / SCALE_FACTOR))
        return ix, iy

    def _buscar_y_abrir_archivo(self, nombre):
        """Busca un archivo en las carpetas comunes y lo abre con os.startfile."""
        import os
        nombre_lower = nombre.lower()
        
        # Si es una palabra clave genérica, intentar ejecutar directamente
        genericos = {
            "excel": "excel",
            "word": "winword",
            "calculadora": "calc",
            "notepad": "notepad",
            "bloc de notas": "notepad",
            "explorador": "explorer",
            "navegador": "msedge"
        }
        if nombre_lower in genericos:
            try:
                os.startfile(genericos[nombre_lower])
                return f"Programa '{nombre}' ejecutado exitosamente."
            except Exception as e:
                pass # Falló el directo, intentar buscar archivo

        carpetas = [
            os.path.expanduser('~/Desktop'),
            os.path.expanduser('~/Documents'),
            os.path.expanduser('~/Downloads'),
            os.path.expanduser('~/OneDrive/Escritorio'),
            os.path.expanduser('~/OneDrive/Documentos')
        ]
        
        # Buscar en las carpetas
        for carpeta in carpetas:
            if not os.path.exists(carpeta):
                continue
            for root, dirs, files in os.walk(carpeta):
                for f in files:
                    # Ignorar archivos ocultos o temporales de office
                    if f.startswith('~$'): continue
                    if nombre_lower in f.lower():
                        ruta_completa = os.path.join(root, f)
                        try:
                            os.startfile(ruta_completa)
                            return f"Archivo encontrado y abierto exitosamente: {ruta_completa}"
                        except Exception as e:
                            return f"Se encontró el archivo pero hubo un error al abrirlo: {e}"
                # Limitar profundidad de búsqueda para no demorar mucho
                if root.count(os.sep) - carpeta.count(os.sep) > 2:
                    del dirs[:]
                    
        return f"No se encontró ningún archivo que contenga '{nombre}' en Escritorio, Documentos o Descargas."

    def get_backend(self):
        """Detecta qué backend usar:
        - Intenta LM Studio primero (localhost:1234).
        - Si no hay Ollama, usa Ollama cloud (SDK oficial).
        Devuelve ("lmstudio"|"ollama"|None, model_id)."""
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
        """Llama a LM Studio via HTTP (OpenAI-compatible) con normalización agresiva para modelos locales."""
        mensajes_locales = []
        
        # Primero, normalizamos y limpiamos todos los mensajes
        for m in self.mensajes:
            # FILTRADO: No enviar mensajes de error previos al modelo para evitar alucinaciones/repeticiones
            if m.get("role") == "assistant" and m.get("content") == "Error al obtener respuesta del backend.":
                continue
                
            m_copy = m.copy()
            
            # 1. Normalizar contenido multimodal (listas) a texto simple
            if isinstance(m_copy.get("content"), list):
                texto_plano = ""
                for item in m_copy["content"]:
                    if isinstance(item, dict) and item.get("type") == "text":
                        texto_plano += item.get("text", "") + "\n"
                m_copy["content"] = texto_plano.strip()

            # 2. Normalizar rol 'tool' a 'user'
            if m_copy.get("role") == "tool":
                nombre = m_copy.get("name", "herramienta")
                contenido = m_copy.get("content", "")
                m_copy["role"] = "user"
                m_copy["content"] = f"[SISTEMA] Resultado de {nombre}: {contenido}"
                if "tool_call_id" in m_copy: del m_copy["tool_call_id"]
                if "name" in m_copy: del m_copy["name"]
            
            # 3. Limpiar campos incompatibles y asegurar contenido no nulo
            for key in ["thought", "thought_signature", "name", "tool_call_id"]:
                if key in m_copy: del m_copy[key]
            
            if not m_copy.get("content"):
                m_copy["content"] = "..." # No enviar contenido vacío
            
            mensajes_locales.append(m_copy)

        # 4. REGLA CRÍTICA PARA JINJA: Asegurar alternancia User/Assistant y empezar con User
        # Algunos modelos (Qwen, Llama) fallan si el primer mensaje tras el sistema es del asistente
        mensajes_finales = []
        encontrado_primer_user = False
        
        for m in mensajes_locales:
            if m["role"] == "system":
                mensajes_finales.append(m)
                continue
            
            if not encontrado_primer_user:
                if m["role"] == "assistant":
                    # Si el asistente habla primero, inyectamos un saludo del usuario previo
                    mensajes_finales.append({"role": "user", "content": "Hola Ashly."})
                encontrado_primer_user = True
            
            # Evitar mensajes consecutivos del mismo rol (excepto system)
            if mensajes_finales and mensajes_finales[-1]["role"] == m["role"] and m["role"] != "system":
                mensajes_finales[-1]["content"] += "\n" + m["content"]
            else:
                mensajes_finales.append(m)

        # 5. Asegurar que el último mensaje sea de rol 'user'
        if not mensajes_finales or mensajes_finales[-1]["role"] != "user":
            mensfinales.append({"role": "user", "content": "Responde ahora."})

        # Debug para el usuario
        # print(f"DEBUG: Enviando {len(mensajes_finales)} mensajes a LM Studio")

        try:
            response = requests.post(
                f"{LMSTUDIO_URL}/chat/completions",
                json={
                    "model": model,
                    "messages": mensajes_finales,
                    "tools": self.tools,
                    "temperature": 0.7
                
                },
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("choices", [{}])[0].get("message", {})
            print(f"Error LM Studio: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Error de conexión con LM Studio: {e}")
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
        if steps > 100:
            return "⚠️ Ashly se detuvo tras 100 pasos para evitar un consumo excesivo de recursos."
            
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
                        elif function_name == "analizar_campos_texto":
                            res = win32_control.analizar_ventana_activa()
                            # Desescalar coordenadas si es necesario
                            if isinstance(res, dict) and "campos_de_texto" in res:
                                for c in res["campos_de_texto"]:
                                    if "x" in c and "y" in c:
                                        c["x"], c["y"] = self._desescalar_coords(c["x"], c["y"])
                            resultado = res
                            print(f"      👀  Análisis de campos: {res.get('cantidad_campos_encontrados', 0)} encontrados.")
                        elif function_name == "click_izquierdo":
                            resultado = movermouse.MouseOperator().left_click()
                        elif function_name == "click_texto":
                            palabra = arguments.get('palabra', '')
                            coord = vision.obtener_coordenadas_texto(palabra)
                            if coord:
                                print(f"      🖱️  Texto '{palabra}' encontrado en {coord}")
                                x, y = coord
                                movermouse.MouseOperator().smooth_move(target=(x, y))
                                time.sleep(0.1)
                                movermouse.MouseOperator().left_click()
                                resultado = f"Click realizado exitosamente en el texto '{palabra}' en las coordenadas {coord}."
                            else:
                                resultado = f"Error: No se pudo encontrar el texto '{palabra}' en la pantalla usando OCR. Prueba usar la herramienta 'analizar_escritorio' si buscas un icono del escritorio, o 'analizar_barra_tareas' si buscas una aplicación abierta."
                        elif function_name == "buscar_icono_en_pantalla":
                            ruta_icono = arguments.get('ruta_icono', '')
                            coord = vision.buscar_icono_en_pantalla(ruta_icono)
                            if coord:
                                print(f"      🖱️  Icono '{ruta_icono}' encontrado en {coord}")
                                x, y = coord
                                # Opcional: Desescalar si la escala no es 1
                                x, y = self._desescalar_coords(x, y)
                                movermouse.MouseOperator().smooth_move(target=(x, y))
                                time.sleep(0.05)
                                movermouse.MouseOperator().left_click()
                                resultado = f"Icono encontrado y clickeado exitosamente en las coordenadas ({x}, {y})."
                            else:
                                resultado = f"Error: No se pudo encontrar el icono '{ruta_icono}' en la pantalla usando Template Matching."
                        elif function_name == "esperar_cambio_visual":
                            timeout = arguments.get('timeout_segundos', 10)
                            print(f"      👀  Esperando cambio visual (máx {timeout}s)...")
                            hubo_cambio = vision.esperar_cambio_visual(timeout_segundos=timeout)
                            if hubo_cambio:
                                resultado = "Cambio visual detectado. La pantalla se ha actualizado."
                            else:
                                resultado = "Timeout: No se detectaron cambios visuales significativos en el tiempo especificado."
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
                        elif function_name == "abrir_archivo":
                            nombre_archivo = arguments.get("nombre_archivo", "")
                            print(f"      🔎  Buscando y abriendo archivo: '{nombre_archivo}'")
                            resultado = self._buscar_y_abrir_archivo(nombre_archivo)
                        elif function_name == "excel_escribir_celda":
                            resultado = excel_control.escribir_celda(**arguments)
                        elif function_name == "excel_escribir_interseccion":
                            resultado = excel_control.escribir_interseccion(**arguments)
                        # ── Word ───────────────────────────────────────────
                        elif function_name == "word_crear_documento":
                            resultado = word_control.word_crear_documento()
                        elif function_name == "word_escribir_texto":
                            resultado = word_control.word_escribir_texto(**arguments)
                        elif function_name == "word_aplicar_formato":
                            resultado = word_control.word_aplicar_formato(**arguments)
                        elif function_name == "word_guardar_como":
                            resultado = word_control.word_guardar_como(**arguments)
                        # ── WhatsApp ───────────────────────────────────────
                        elif function_name == "whatsapp_enviar_mensaje":
                            resultado = whatsapp_control.whatsapp_enviar_mensaje(**arguments)
                        elif function_name == "whatsapp_obtener_ultimo_mensaje":
                            resultado = whatsapp_control.whatsapp_obtener_ultimo_mensaje()
                        elif function_name == "whatsapp_leer_conversacion":
                            resultado = whatsapp_control.whatsapp_leer_conversacion(**arguments)
                        elif function_name == "whatsapp_listar_chats_recientes":
                            resultado = whatsapp_control.whatsapp_listar_chats_recientes()
                        elif function_name == "whatsapp_navegar_a_seccion":
                            resultado = whatsapp_control.whatsapp_navegar_a_seccion(**arguments)
                        elif function_name == "verificar_programa_abierto":
                            resultado = win32_control.verificar_programa_abierto(**arguments)
                        elif function_name == "analizar_barra_tareas":
                            res = win32_control.analizar_barra_tareas()
                            if isinstance(res, dict) and "elementos" in res:
                                for e in res["elementos"]:
                                    e["x"], e["y"] = self._desescalar_coords(e["x"], e["y"])
                            resultado = res
                        elif function_name == "analizar_escritorio":
                            res = win32_control.analizar_escritorio()
                            if isinstance(res, dict) and "elementos" in res:
                                for e in res["elementos"]:
                                    e["x"], e["y"] = self._desescalar_coords(e["x"], e["y"])
                            resultado = res
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
                        elif function_name == "activar_red_neuronal_autonoma":
                            resultado = self.ejecutar_red_neuronal(**arguments)
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
            texto_ocr, img_b64 = vision.preparar_vision_data(max_width=VISION_W)
            
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

    def ejecutar_red_neuronal(self, objetivo):
        """Activa el modo autónomo usando la CNN y la red neuronal preentrenada."""
        import os
        import torch
        import time
        import ctypes
        from neural_agent import AshlyNeuralNet
        from cnn_vision import VisionEncoder
        import vision
        import movermouse
        from pynput import keyboard

        ruta_modelo = "ashly_neural_brain.pth"
        if not os.path.exists(ruta_modelo):
            return f"❌ Error: No se encontró el cerebro neuronal '{ruta_modelo}'. Primero usa 'user_tracker.py' para grabar y 'neural_memory.py' para entrenar."

        print(f"\n🧠 [MODO NEURONAL ACTIVADO] Objetivo: {objetivo}")
        print("🔴 Presiona ESC en cualquier momento para detener la red neuronal.")

        encoder = VisionEncoder()
        agent = AshlyNeuralNet()
        try:
            agent.load_state_dict(torch.load(ruta_modelo, weights_only=True))
        except Exception as e:
            return f"Error al cargar la red neuronal: {e}"
        agent.eval()

        mouse_op = movermouse.MouseOperator()
        abortar = False

        def on_press(key):
            nonlocal abortar
            if key == keyboard.Key.esc:
                print("\n[!] Abortando modo neuronal por orden del usuario (ESC)...")
                abortar = True
                return False

        listener = keyboard.Listener(on_press=on_press)
        listener.start()

        pasos = 0
        while not abortar and pasos < 50: # Aumentado a 50 pasos
            pasos += 1
            
            frame = vision.capturar_pantalla()
            if frame is None:
                print("   Error capturando pantalla.")
                break
            
            # Obtener dimensiones reales del frame capturado
            fh, fw = frame.shape[:2]
            
            # NORMALIZACIÓN DE ASPECTO: 
            # Si el modelo fue entrenado en 1280x720, el encoder ya redimensiona a 224x224.
            # Pero para que las características sean consistentes, nos aseguramos de que el aspect ratio
            # sea similar si es necesario (opcional, MobileNet suele ser robusta).
                
            try:
                vector_visual = encoder.procesar_imagen_cv2(frame)
                action_id, nx, ny = agent.predecir_accion(vector_visual)
                
                if action_id == 0:
                    print(f"   [{pasos}] 🧠 Decisión: Esperar/Analizar...")
                elif action_id == 1:
                    # Escalar coordenadas normalizadas (0-1) a píxeles reales del monitor
                    real_x = int(round(nx * fw))
                    real_y = int(round(ny * fh))
                    
                    print(f"   [{pasos}] 🧠 Decisión: Clic en ({real_x}, {real_y}) [Norm: {nx:.3f}, {ny:.3f}]")
                    mouse_op.smooth_move((real_x, real_y))
                    time.sleep(0.1)
                    mouse_op.left_click()
                elif action_id == 2:
                    print(f"   [{pasos}] 🧠 Decisión: Acción de Teclado detectada.")
                    # Aquí se podría implementar una acción de teclado por defecto o predecir teclas
                
                # Reducido sleep para mayor reactividad
                time.sleep(0.5) 
            except Exception as e:
                print(f"   Error en ejecución neuronal: {e}")
                break
                
        listener.stop()
        return f"Modo neuronal finalizado tras {pasos} iteraciones."

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
                
                # Solo añadir al historial si NO es un error de backend para no "ensuciar" la memoria del modelo
                if resAshly != "Error al obtener respuesta del backend.":
                    self.mensajes.append({"role": "assistant", "content": resAshly})
                    self.guardar_estado()
                else:
                    # Si hubo error, podemos avisar pero no guardarlo en el JSON persistente
                    pass
