# ═══════════════════════════════════════════════════════════════════════════
# AGENTE.PY - Cerebro principal de Ashly v2
# ═══════════════════════════════════════════════════════════════════════════
# Este archivo contiene la clase Agent, que es el núcleo de Ashly.
# Aquí se gestiona:
#   1. La comunicación con los modelos de IA (LM Studio local u Ollama local/cloud)
#   2. El despacho y ejecución de herramientas (tools) como mouse, teclado, Excel, etc.
#   3. El sistema de visión (captura de pantalla + OCR)
#   4. La memoria a largo plazo y el sistema de recompensas
#   5. La poda automática del historial para mantener velocidad en local
# ═══════════════════════════════════════════════════════════════════════════

# ── Librerías estándar de Python ──
import os       # Para acceder a variables de entorno y rutas de archivo
import sys      # Para reconfigurar la consola (encoding UTF-8)
import json     # Para serializar/deserializar JSON (historial, herramientas)
import requests # Para hacer peticiones HTTP a LM Studio y Ollama
import time     # Para pausas y mediciones de tiempo

# ── Corrección de encoding para Windows ──
# Sin esto, los emojis (👀, ✅, etc.) generan UnicodeEncodeError en la consola de Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# ── Módulos propios de Ashly (cada uno controla una capacidad) ──
import EdiListRead       # Herramientas para listar, leer y editar archivos del sistema
import teclado_pro       # Escritura "humana" de texto y combinaciones de teclado
import movermouse        # Control fino del mouse: mover, click, arrastrar, scroll
import tools             # Definición de las herramientas disponibles para la IA (JSON Schema)
import analizarentorno   # Análisis de ventanas abiertas y sus posiciones
import vision            # Captura de pantalla (dxcam), OCR (Tesseract), detección de cambios
import win32_control     # Control de ventanas de Windows (enfocar, mover, listar, barra de tareas)
import entorno           # Información del sistema: hora, cursor, procesos, portapapeles
import excel_control     # Control directo de Excel vía COM (escribir celdas sin usar el mouse)
import word_control      # Control directo de Word vía COM (crear/escribir documentos)
import whatsapp_control  # Control de WhatsApp Desktop vía API de accesibilidad (UIAutomation)
from storage_manager import StorageManager  # Persistencia de historial y memoria en JSON
from dotenv import load_dotenv              # Carga de variables de entorno desde .env

# ── Importación segura del SDK de Ollama ──
# Si el usuario no tiene la librería instalada, el agente sigue funcionando con LM Studio
try:
    from ollama import Client as OllamaClient
    _OLLAMA_SDK = True  # Bandera: el SDK está disponible
except ImportError:
    _OLLAMA_SDK = False  # Bandera: el SDK NO está disponible

# ── Cargar configuración del archivo .env ──
# El archivo .env contiene las URLs y API keys de forma segura (no hardcodeadas)
load_dotenv()

# ── Configuración de Backends (se leen del archivo .env) ──────────────────
# LMSTUDIO_URL: URL del servidor local de LM Studio (ej: http://localhost:1234/v1)
# OLLAMA_API_KEY: Clave API para Ollama Cloud (opcional, solo si se usa la nube)
# OLLAMA_MODEL: Nombre del modelo a usar en Ollama (ej: gemma3, llama3)
# OLLAMA_HOST: URL del servidor Ollama (local o cloud)
LMSTUDIO_URL   = os.getenv("LMSTUDIO_URL")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_MODEL   = os.getenv("OLLAMA_MODEL")
OLLAMA_HOST    = os.getenv("OLLAMA_HOST")

# ── Resolución de pantalla y escalado de visión ────────────────────────────
# Necesitamos saber el tamaño real del monitor para convertir las coordenadas
# que la IA predice (en la imagen virtual de 1280px) a píxeles reales.
import ctypes
try:
    # Activar conciencia de DPI en Windows para obtener la resolución REAL
    # (sin esto, Windows puede reportar 1920x1080 aunque el monitor sea 2560x1440)
    ctypes.windll.shcore.SetProcessDpiAwareness(1)  # PROCESS_SYSTEM_DPI_AWARE
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()  # Fallback para Windows más viejos
    except Exception:
        pass

user32 = ctypes.windll.user32
SCREEN_W = user32.GetSystemMetrics(0)   # Ancho real del monitor en píxeles
SCREEN_H = user32.GetSystemMetrics(1)   # Alto real del monitor en píxeles
VISION_W = 1440                         # Resolución virtual estándar que ve la IA
# Factor de escala: si la pantalla es 1920px y la IA trabaja con 1440px,
# el factor será 1.5 (cada píxel de la IA = 1.5 píxeles reales)
SCALE_FACTOR = SCREEN_W / VISION_W

class Agent:
    """
    Clase principal del agente Ashly v2.
    Gestiona la conversación con la IA, el despacho de herramientas,
    la visión por computadora, la memoria a largo plazo y la poda
    automática del historial para mantener velocidad en local.
    """

    def __init__(self):
        """
        Constructor del agente. Inicializa:
        - StorageManager: carga/guarda historial.json y memoria_agente.json
        - self.mensajes: lista de mensajes de la conversación (historial)
        - self.memoria_interna: lista de conocimientos adquiridos
        - self.recompensas: puntos de experiencia acumulados
        - self.tools: definición de herramientas disponibles para la IA
        - VisionMonitor: hilo de monitoreo de cambios en la pantalla
        """
        self.storage = StorageManager()
        # Cargamos el estado previo desde los archivos JSON del disco
        self.mensajes, self.memoria_interna, self.recompensas = self.storage.cargar_datos()
        
        # Si no hay historial previo, creamos uno vacío con el System Prompt
        if not self.mensajes:
            self.mensajes = [{"role": "system", "content": ""}]
            
        # Inyectamos el System Prompt actualizado (con memoria y reglas)
        self.actualizar_prompt_sistema()
        # Cargamos la definición de herramientas desde tools.py
        self.setup_tools()
        # Iniciamos el hilo de monitoreo de pantalla en segundo plano
        # (solo detecta cambios por hash, NO hace OCR continuo)
        vision.VisionMonitor.iniciar()

    def actualizar_prompt_sistema(self):
        vision_h = int(VISION_W * SCREEN_H / SCREEN_W)
        base_prompt = f"""
        Eres Ashlyn, una asistente virtual inteligente, amable y eficiente que opera una computadora en tiempo real usando herramientas automatizadas.

        REGLAS PRINCIPALES:
        - Hablas español.
        - No inventes acciones, datos ni resultados.
        - Usa siempre las herramientas más precisas disponibles.
        - Sé rápida, proactiva y evita repetir acciones inútiles.
        - Si una acción falla, intenta otra estrategia distinta.

        MEMORIA Y RECOMPENSAS:
        - Tienes {self.recompensas} puntos.
        - Ganas puntos resolviendo tareas correctamente.
        - Usa 'guardar_memoria' cuando aprendas algo importante.
        - El historial y memoria se guardan automáticamente.

        VISIÓN:
        - La resolución virtual es {VISION_W}x{vision_h}.
        - Todas las coordenadas deben basarse en esa resolución.
        - Usa la cuadrícula verde para precisión.
        - NO adivines coordenadas.
        - Usa herramientas de análisis antes de hacer clics manuales.

        REGLAS DE INTERACCIÓN:
        - Usa 'click_texto' siempre que sea posible.
        - Usa 'escribir_texto' para cualquier texto.
        - Usa 'presionar_teclas' solo para atajos y teclas especiales.
        - Nunca uses sleeps ciegos; usa 'esperar_cambio_visual'.

        PROGRAMAS Y ARCHIVOS:
        - Antes de abrir un programa usa 'verificar_programa_abierto'.
        - Si ya existe, usa 'controlar_ventana' con 'enfocar'.
        - Usa 'abrir_archivo' para abrir documentos o programas.

        HERRAMIENTAS VISUALES:
        - Usa 'analizar_escritorio', 'analizar_barra_tareas' y 'analizar_campos_texto' para localizar elementos.
        - Usa 'buscar_icono_en_pantalla' cuando tengas imágenes de referencia.

        EXCEL:
        - Usa únicamente herramientas nativas como:
        'excel_escribir_celda'
        'excel_escribir_interseccion'

        WORD:
        - Usa:
        'word_crear_documento'
        'word_escribir_texto'
        'word_aplicar_formato'

        WHATSAPP:
        - Usa siempre 'whatsapp_enviar_mensaje'.
        - Nunca respondas con datos internos ni conversaciones privadas.
        - No uses visión manual para responder WhatsApp salvo fallo de herramienta.

        VISIÓN EN TIEMPO REAL:
        - No uses 'ver_escritorio' repetidamente sin actuar.
        - Primero observa, luego actúa.
        - Si la pantalla no cambia, intenta otra acción.

        DATOS PAPELERIA:
        Precios impresiones:
            Color: $600 c/u
            B/N: $400 c/u
        Precios fotocopias:
            Color: $500 c/u
            B/N: $200 c/u
        Horario
        Nuestro horario comercial es el siguiente:
        Jueves: 8:00 - 20:55
        Viernes: 8:00 - 20:55
        Sábado: 8:00 - 12:00
        Domingo: Cerrado
        Lunes: 8:00 - 20:55
        Martes: 8:00 - 20:55
        Miércoles: 8:00 - 20:55

        IMPORTANTE:
        No estás en un chat normal.
        Estás controlando una computadora real en tiempo real.
        """
        if self.memoria_interna:
            base_prompt += "\n--- CONOCIMIENTOS ADQUIRIDOS ---\n"
            for nota in self.memoria_interna:
                base_prompt += f"- {nota}\n"
        
        self.mensajes[0]["content"] = base_prompt

    def setup_tools(self):
        """
        Carga las definiciones JSON de las herramientas disponibles.
        Estas definiciones le dicen a la IA qué herramientas puede usar,
        sus parámetros y descripciones (JSON Schema compatible con OpenAI).
        """
        self.tools = tools.get_tools()

    def _escalar_coords(self, x, y):
        """
        Convierte coordenadas del espacio virtual de la IA (imagen de 1280px)
        al espacio real de la pantalla del usuario.
        
        Ejemplo: Si la IA dice "click en (640, 360)" y la pantalla real es 1920x1080,
        con SCALE_FACTOR=1.5, las coordenadas reales serán (960, 540).
        
        También hace 'clamp' para que nunca se salgan de los bordes del monitor.
        """
        if x is None or y is None:
            return x, y
        
        # Multiplicamos por el factor de escala para obtener píxeles reales
        rx = int(round(float(x) * SCALE_FACTOR))
        ry = int(round(float(y) * SCALE_FACTOR))
        
        # Clamp: aseguramos que las coordenadas no se salgan de la pantalla
        rx = max(0, min(rx, SCREEN_W - 1))
        ry = max(0, min(ry, SCREEN_H - 1))
        return rx, ry

    def _desescalar_coords(self, x, y):
        """
        Operación inversa de _escalar_coords.
        Convierte coordenadas reales de pantalla al espacio virtual de la IA.
        
        Se usa cuando una herramienta (ej: analizar_barra_tareas) devuelve
        coordenadas reales y queremos que la IA las entienda en su resolución virtual.
        """
        if x is None or y is None:
            return x, y
        # Dividimos por el factor de escala para volver al espacio de la IA
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
        """
        Detecta qué backend de IA usar, en orden de prioridad:
          1. LM Studio local (localhost, gratuito, sin internet)
          2. Ollama local (localhost, gratuito, sin internet)
          3. Ollama cloud (requiere API key y conexión a internet)
        
        Devuelve una tupla ("lmstudio"|"ollama"|None, model_id|None)
        """
        # ── PRIORIDAD 1: LM Studio local ───────────────────────────────────
        # Consultamos si LM Studio está corriendo y tiene un modelo cargado
        if LMSTUDIO_URL:
            try:
                response = requests.get(f"{LMSTUDIO_URL}/models", timeout=5)
                if response.status_code == 200:
                    models_data = response.json().get("data", [])
                    if models_data:
                        # Usamos el primer modelo que LM Studio tenga cargado
                        model_id = models_data[0]["id"]
                        print(f"[LM STUDIO] Activo -> modelo: {model_id}")
                        return "lmstudio", model_id
            except Exception:
                pass  # LM Studio no disponible o no responde, seguimos al fallback

        # ── PRIORIDAD 2/3: Ollama (Local o Cloud) ──────────────────────────
        # Determinamos si es Ollama local (localhost) o Ollama en la nube
        is_local_ollama = OLLAMA_HOST and ("localhost" in OLLAMA_HOST or "127.0.0.1" in OLLAMA_HOST)
        has_api_key = OLLAMA_API_KEY and OLLAMA_API_KEY not in ("", "Ollama_API_KEY")

        if OLLAMA_MODEL and (has_api_key or is_local_ollama):
            if not _OLLAMA_SDK:
                print("❌ Librería 'ollama' no instalada. Ejecuta: pip install ollama")
                return None, None
            tipo = "local" if is_local_ollama else "cloud"
            print(f"[OLLAMA] LM Studio sin modelos. Usando Ollama {tipo} ({OLLAMA_HOST}) -> {OLLAMA_MODEL}")
            return "ollama", OLLAMA_MODEL

        # Si ningún backend está disponible, informamos al usuario
        print(f"[ERROR] Sin backend disponible: LM Studio sin modelos y sin OLLAMA_API_KEY configurada. (Ollama Host: {OLLAMA_HOST})")
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
            mensajes_finales.append({"role": "user", "content": "Responde ahora."})

        # Debug para el usuario
        # print(f"DEBUG: Enviando {len(mensajes_finales)} mensajes a LM Studio")

        try:
            # Enviamos la petición HTTP POST al endpoint de LM Studio (compatible con OpenAI)
            response = requests.post(
                f"{LMSTUDIO_URL}/chat/completions",
                json={
                    "model": model,
                    "messages": mensajes_finales,
                    "tools": self.tools,       # Herramientas disponibles para la IA
                    "temperature": 0.7          # Creatividad moderada (0=determinista, 1=creativo)
                },
            )
            if response.status_code == 200:
                data = response.json()
                msg = data.get("choices", [{}])[0].get("message", {})
                
                # Algunos modelos devuelven el razonamiento en 'thought' pero dejan 'content' vacío
                # En ese caso, usamos el pensamiento como contenido visible
                if not msg.get("content") and msg.get("thought"):
                    msg["content"] = msg["thought"]
                return msg
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
        """
        Llama a Ollama (local o cloud) usando requests nativo (HTTP directo).
        No usamos el SDK de Ollama aquí porque el SDK filtra campos como
        'thought' y 'thought_signature' que son críticos para modelos Gemini Thinking.
        """
        import requests
        # Normalizamos los mensajes al formato que Ollama espera
        mensajes_normalizados = self._normalizar_mensajes_ollama(self.mensajes)
        
        # Construimos el payload de la petición
        payload = {
            "model": model,
            "messages": mensajes_normalizados,
            "tools": self.tools,    # Herramientas disponibles
            "stream": False         # Respuesta completa (no streaming)
        }
        
        # Headers de autenticación (solo si hay API key configurada)
        headers = {"Content-Type": "application/json"}
        if OLLAMA_API_KEY:
            headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"
            
        # Petición HTTP directa al endpoint /api/chat de Ollama
        response = requests.post(f"{OLLAMA_HOST}/api/chat", json=payload, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"API Error {response.status_code}: {response.text}")
            
        resp_json = response.json()
        msg = resp_json.get("message", {})
        
        # Construimos el resultado en formato estándar interno
        result = {"role": msg.get("role", "assistant"), "content": msg.get("content", "")}
        
        # Capturamos el razonamiento interno del modelo (puede venir con diferentes nombres)
        for key in ['thought', 'reasoning_content', 'reasoning', 'thought_signature']:
            if msg.get(key):
                result["thought"] = msg[key]
                break
        
        # Procesamos las llamadas a herramientas si el modelo decidió usar alguna
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
            
        # Fallback: si no hay contenido visible pero sí razonamiento, mostramos el razonamiento
        if not result.get("content") and result.get("thought"):
            result["content"] = result["thought"]
            
        return result



    def generate_response(self, steps=0):
        """
        Método central del agente: genera una respuesta de la IA y ejecuta herramientas.
        
        Flujo:
          1. Detecta el backend activo (LM Studio o Ollama)
          2. Envía el historial completo al modelo
          3. Si el modelo pide usar herramientas → las ejecuta y vuelve a llamarse (recursivo)
          4. Si el modelo responde con texto → lo devuelve como respuesta final
        
        El parámetro 'steps' es un contador de recursión para evitar bucles infinitos
        (máximo 100 pasos encadenados de herramientas).
        """
        # Protección anti-bucle infinito: si se encadenan más de 100 herramientas, paramos
        if steps > 100:
            return "⚠️ Ashly se detuvo tras 100 pasos para evitar un consumo excesivo de recursos."
            
        # Detectar qué backend de IA está disponible
        backend, model = self.get_backend()
        if not model:
            return "❌ No hay backend disponible. Carga un modelo en LM Studio o configura OLLAMA_API_KEY en el archivo .env"
        
        # NOTA: La visión NO se captura automáticamente aquí.
        # Ashly decide por sí misma cuándo mirar usando la herramienta 'ver_escritorio'.
        
        try:
            # Enviar los mensajes al backend seleccionado
            if backend == "lmstudio":
                message = self._request_lmstudio(model)
            else:
                message = self._request_ollama(model)

            if message is None:
                return "Error al obtener respuesta del backend."

            if True:  # Bloque unificado de procesamiento de la respuesta
                
                # ══════════════════════════════════════════════════════════════
                # DESPACHO DE HERRAMIENTAS (Tool Dispatch)
                # ══════════════════════════════════════════════════════════════
                # Si la IA decidió usar una herramienta en lugar de responder con texto,
                # procesamos cada herramienta, ejecutamos la acción, y volvemos a llamar
                # a la IA con los resultados para que formule su respuesta final.
                if message.get("tool_calls"):
                    print("\n[TOOLS] Ashly esta usando una herramienta...")
                    # Guardamos la petición de herramienta de la IA en el historial
                    self.mensajes.append(message)
                    
                    # Iteramos sobre cada herramienta que la IA pidió ejecutar
                    for tool_call in message["tool_calls"]:
                        function_name = tool_call["function"]["name"]
                        
                        # Parseamos los argumentos JSON de la herramienta
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
                            # La IA decide cuándo mirar la pantalla (captura + OCR)
                            resultado = self.automirar() or "Vision actualizada correctamente."
                        # ── Control de Ventanas de Windows (Win32 API) ─────
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
                        elif function_name == "whatsapp_detectar_nuevos_mensajes":
                            resultado = whatsapp_control.whatsapp_detectar_nuevos_mensajes()
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
                            
                        # Registramos el resultado de la herramienta en el historial
                        # para que la IA pueda ver qué pasó y actuar en consecuencia
                        self.mensajes.append({
                            "tool_call_id": tool_call["id"],
                            "role": "tool",
                            "name": function_name,
                            "content": str(resultado)
                        })
                        
                    # ── RECURSIÓN: Volvemos a llamar a la IA con los resultados ──
                    # La IA verá los resultados de las herramientas y decidirá si:
                    #   a) Responder al usuario con texto
                    #   b) Usar otra herramienta (encadenamiento)
                    time.sleep(0.2)  # Pequeña pausa (0.2s) para no saturar el backend
                    return self.generate_response(steps=steps + 1)

                # Si la IA respondió con texto (sin herramientas), devolvemos el contenido
                return message.get("content", "")
            else:
                return f"Error en la generación: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error al generar respuesta: {e}"

    def automirar(self):
        """
        Captura la pantalla física actual del usuario, realiza el OCR con Tesseract,
        y formatea el contexto visual (imagen en base64 y texto OCR) para la IA.
        Para evitar la lentitud en local, limpia el contenido de las visiones viejas del historial.
        """
        try:
            print("👀 Ashly está mirando la pantalla...")
            texto_ocr, img_b64 = vision.preparar_vision_data(max_width=VISION_W)
            
            # ── OPTIMIZACIÓN LOCAL: Poda de OCR e Imágenes del Historial Antiguo ──
            # Buscamos todos los índices del historial que contengan capturas visuales antiguas
            vision_indices = []
            for i, m in enumerate(self.mensajes):
                content = m.get("content")
                # Detectamos mensajes multimodales (con listas de imágenes) o marcadores de OCR
                if isinstance(content, list):
                    vision_indices.append(i)
                elif isinstance(content, str) and ("--- VISIÓN DIGITAL ACTUAL ---" in content or "[Visión Histórica" in content):
                    vision_indices.append(i)
            
            # Reemplazamos las capturas antiguas con textos ligeros en lugar de borrarlas.
            # Esto mantiene la coherencia de la conversación pero borra megabytes de tokens.
            if len(vision_indices) > 0:
                for idx in vision_indices:
                    # Descartamos las imágenes y textos OCR pesados de los turnos antiguos
                    self.mensajes[idx]["content"] = "[Visión Histórica - Descartada para mantener velocidad local]"

            if img_b64:
                # La visión actual se añade como la última interacción visual fresca
                contenido_vision = [
                    {
                        "type": "text", 
                        "text": f"--- VISIÓN DIGITAL ACTUAL ---\nTEXTO DETECTADO (OCR, PUEDE CONTENER RUIDO):\n{texto_ocr}\n----------------------------"
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
                    }
                ]
                # Agregamos la visión fresca al historial
                self.mensajes.append({"role": "user", "content": contenido_vision})
        except Exception as e:
            print(f"Error al intentar mirar: {e}")

    def guardar_memoria(self, dato):
        """Guarda un dato en la memoria interna y actualiza el prompt para que la IA sea consciente."""
        self.memoria_interna.append(dato)
        self.actualizar_prompt_sistema()
        return "Notificación: Dato guardado exitosamente en tu memoria interna."

    def extraer_aprendizaje_local(self):
        """
        Pide al modelo local (LM Studio / Ollama) que extraiga un nuevo conocimiento o regla 
        de la conversación actual antes de que sea borrada.
        Esto elimina la necesidad de extraer y guardar la memoria de forma manual.
        """
        backend, model = self.get_backend()
        if not model:
            return None
            
        # Simplificar el historial para no enviar megabytes al extractor
        historial_texto = []
        for m in self.mensajes[1:]: # Omitir el System Prompt gigante del inicio
            rol = m.get("role")
            content = m.get("content")
            if isinstance(content, list):
                # Extraer solo el texto de mensajes multimodales antiguos
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        historial_texto.append(f"{rol}: {item.get('text')}")
            elif isinstance(content, str):
                # Omitir textos OCR gigantes o visiones descartadas
                if "--- VISIÓN DIGITAL ACTUAL ---" in content or "Visión Histórica" in content:
                    historial_texto.append(f"{rol}: [Captura de pantalla analizada]")
                else:
                    historial_texto.append(f"{rol}: {content}")
        
        # Formular una petición muy concisa e independiente para el modelo local
        prompt_extractor = (
            "Analiza el siguiente historial de interacciones de un agente. "
            "Extrae en UNA SOLA línea corta (menos de 100 caracteres) un aprendizaje, ruta, atajo o regla "
            "útil descubierta (ej: 'WhatsApp requiere Enter', 'Para Excel usar excel_escribir_celda'). "
            "Si no hay lecciones o atajos nuevos relevantes, responde simplemente 'Ninguno'.\n\n"
            "HISTORIAL:\n" + "\n".join(historial_texto) + "\n\n"
            "Responde únicamente con el aprendizaje en español o 'Ninguno':"
        )
        
        # Payload de mensajes para el extractor de conocimientos
        extractor_msg = [
            {"role": "system", "content": "Eres un asistente que resume logs técnicos de forma extremadamente concisa."},
            {"role": "user", "content": prompt_extractor}
        ]
        
        try:
            # Respaldar historial actual
            mensajes_originales = self.mensajes
            self.mensajes = extractor_msg
            
            # Ejecutar la llamada con el backend activo
            if backend == "lmstudio":
                resp = self._request_lmstudio(model)
            else:
                resp = self._request_ollama(model)
                
            # Restaurar el historial original
            self.mensajes = mensajes_originales
            
            resultado = resp.get("content", "").strip() if resp else ""
            # Si el modelo local responde que no hay nada nuevo, omitir
            if resultado.lower() in ["ninguno", "ninguno.", "ninguno", "", "ninguno de los anteriores"]:
                return None
            return resultado.strip('"\'')
        except Exception as e:
            print(f"Advertencia: No se pudo extraer aprendizaje de forma local: {e}")
            self.mensajes = mensajes_originales
            return None

    def intentar_consolidar_y_podar(self):
        """
        Revisa si el historial contiene más de 10 conversaciones (mensajes de usuario).
        Si supera este límite, ejecuta la extracción de memoria local, actualiza la
        memoria de largo plazo y borra el historial de mensajes de la sesión para
        evitar la lentitud en local.
        """
        # Contar interacciones del usuario (mensajes con rol user que no son visiones crudas)
        user_msgs = [m for m in self.mensajes if m.get("role") == "user" and isinstance(m.get("content"), str)]
        
        if len(user_msgs) >= 10:
            print(f"\n🔄 [PODA AUTOMÁTICA] Historial alcanzó {len(user_msgs)} interacciones de usuario.")
            print("🧠 Extrayendo conocimientos útiles de la sesión en segundo plano...")
            
            # Intentar consolidar el conocimiento usando el LLM local
            aprendizaje = self.extraer_aprendizaje_local()
            if aprendizaje:
                print(f"✨ [NUEVO CONOCIMIENTO CONSOLIDADO] -> {aprendizaje}")
                self.guardar_memoria(aprendizaje)
            else:
                print("ℹ️ No se detectaron aprendizajes nuevos en este bloque de chat.")
            
            # Podar el historial: Dejar solo el system prompt inicial actualizado y una nota del sistema
            system_prompt = self.mensajes[0]
            self.mensajes = [
                system_prompt,
                {
                    "role": "system",
                    "content": "[SISTEMA] El historial de chat previo fue podado y consolidado automáticamente en tu memoria a largo plazo para asegurar un rendimiento de respuesta rápido e instantáneo."
                }
            ]
            # Guardar el nuevo estado a disco
            self.guardar_estado()
            print("🧹 [HISTORIAL PODADO] El historial ha sido limpiado. Velocidad de respuesta restaurada al 100%.")

    def dar_recompensa(self, puntos, motivo):
        """
        Sistema de gamificación: la IA se "auto-recompensa" cuando logra algo.
        Los puntos acumulados se muestran en el System Prompt como "experiencia".
        """
        self.recompensas += puntos
        self.actualizar_prompt_sistema()  # Actualizar el prompt para reflejar los nuevos puntos
        return f"¡Recompensa recibida! +{puntos} puntos. Motivo: {motivo}"

    def guardar_estado(self):
        """
        Persiste todo el estado actual del agente a disco:
        - historial.json: conversación completa
        - memoria_agente.json: conocimientos + puntos de experiencia
        """
        self.storage.guardar_completamente(self.mensajes, self.memoria_interna, self.recompensas)

    def ejecutar_red_neuronal(self, objetivo):
        """
        Modo autónomo avanzado: usa una red neuronal (CNN + MLP) preentrenada
        para tomar decisiones visuales sin depender del LLM.
        
        Flujo:
          1. Carga el modelo neuronal entrenado (ashly_neural_brain.pth)
          2. Captura la pantalla en un bucle
          3. Pasa cada frame por la CNN (MobileNet) para extraer un vector visual
          4. La red neuronal predice la acción (esperar/click/teclado) y coordenadas
          5. Ejecuta la acción y repite hasta ESC o 50 pasos
        
        NOTA: Este modo requiere entrenamiento previo con user_tracker.py + neural_memory.py
        """
        import os
        import torch
        import time
        import ctypes
        from neural_agent import AshlyNeuralNet   # Red neuronal de decisión (MLP)
        from cnn_vision import VisionEncoder       # Encoder visual (MobileNet)
        import vision                              # Captura de pantalla
        import movermouse                          # Control del mouse
        from pynput import keyboard                # Detección de tecla ESC para abortar

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
        """
        Punto de entrada principal del agente.
        Presenta un menú interactivo para elegir entre Modo Consola tradicional 
        o el nuevo Modo Autónomo Proactivo.
        """
        print(f"Iniciando Ashly v2. Experiencia actual: {self.recompensas} puntos.")
        print("\nSelecciona el modo de ejecución:")
        print(" [1] Modo Consola Tradicional (Chat interactivo en terminal)")
        print(" [2] Modo Autónomo Proactivo (Monitoreo de WhatsApp y aprendizaje autónomo)")
        
        opcion = ""
        while opcion not in ["1", "2"]:
            opcion = input("\nElige una opción (1 o 2) [Por defecto: 2]: ").strip()
            if not opcion:
                opcion = "2" # Por defecto modo autónomo
                break
                
        if opcion == "1":
            self.run_console()
        else:
            self.run_autonomous()

    def run_console(self):
        """
        Bucle clásico de chat por consola.
        Recibe las solicitudes del usuario por terminal de comandos de forma directa.
        """
        print("\n⚡ MODO CONSOLA TRADICIONAL INICIADO ⚡")
        print("Escribe 'salir' para terminar y guardar el estado.")
        while True:
            # 1. Leer entrada del usuario por consola
            userEnvio = input("\nUsuario: ").strip()
            if not userEnvio:
                continue
            # 2. Control de salida segura del agente
            elif userEnvio.lower() in ["salir", "adios", "bye", "chao"]:
                self.guardar_estado()
                print("Ashly: ¡Adiós! (Estado guardado)")
                break
            else:
                # 3. Registrar el mensaje del usuario en el historial
                self.mensajes.append({"role": "user", "content": userEnvio})
                
                # 4. Generar y procesar la respuesta (incluyendo la ejecución de herramientas)
                resAshly = self.generate_response()
                print(f"\nAshly: {resAshly}")
                
                # Solo añadir al historial si NO es un error de backend para no "ensuciar" la memoria
                if resAshly != "Error al obtener respuesta del backend.":
                    self.mensajes.append({"role": "assistant", "content": resAshly})
                    self.guardar_estado()
                    
                    # ── PODA Y CONSOLIDACIÓN AUTOMÁTICA DEL HISTORIAL ──
                    self.intentar_consolidar_y_podar()

    def _esperar_respuesta_contacto(self, contacto, timeout_segundos=30):
        """Solo pausa tras enviar. La respuesta se detecta en el siguiente ciclo."""
        print(f"⏳ Pausa de {timeout_segundos}s tras enviar mensaje a '{contacto}'...")
        time.sleep(timeout_segundos)
        print(f"⏰ Reanudando escaneo normal.")
        return False  # Siempre False: la próxima iteración del while True detectará nuevos mensajes

    def run_autonomous(self):
        """
        Bucle autónomo proactivo.
        Escanéa WhatsApp Desktop en segundo plano, responde automáticamente a contactos,
        y realiza prácticas o exploraciones autónomas para aprender del entorno de Windows.
        """
        import random
        import whatsapp_control
        
        print("\n🚀 MODO AUTÓNOMO PROACTIVO INICIADO 🚀")
        print("Ashly está vigilando WhatsApp. Presiona Ctrl+C en esta consola para detener.\n")
        
        # Iniciamos el monitor de cambios de visión en segundo plano (para optimizar hash)
        from vision import VisionMonitor
        VisionMonitor.iniciar()
        
        ciclos_inactivos = 0
        ultimo_contacto_procesado = None
        tiempo_ultimo_procesado = 0
        tiempo_cooldown_contacto = 120
        
        try:
            while True:
                print("\n[PROACTIVO] Escaneando chats en WhatsApp Desktop...")
                res_scan = whatsapp_control.whatsapp_detectar_nuevos_mensajes()
                
                if res_scan.get("exito"):
                    contacto = res_scan["contacto"]
                    
                    # Saltar si es el mismo contacto que acabamos de procesar (cooldown)
                    if (ultimo_contacto_procesado == contacto and
                            time.time() - tiempo_ultimo_procesado < tiempo_cooldown_contacto):
                        print(f"⏭️ Saltando '{contacto}' (cooldown), esperando nuevo mensaje.")
                        time.sleep(15)
                        continue
                    
                    # Hemos detectado un mensaje no leído, reiniciamos el contador de inactividad
                    ciclos_inactivos = 0
                    tiempo_ultimo_procesado = time.time()
                    ultimo_contacto_procesado = contacto
                    conversacion = res_scan["conversacion"]
                    
                    print(f"✨ [WHATSAPP] ¡Mensaje nuevo de '{contacto}'!")
                    print(f"--- CONVERSACIÓN RECIBIDA ---\n{conversacion}\n-----------------------------")
                    
                    # 1. Simular mensaje de usuario inyectando el contexto de WhatsApp
                    mensaje_usuario = (
                        f"Mensaje de WhatsApp de '{contacto}':\n"
                        f"--- HISTORIAL DE CHAT RECIENTE ---\n"
                        f"{conversacion}\n"
                        f"-----------------------------------\n"
                        f"Por favor responde a este contacto SOLO con atención al cliente. "
                        f"NO menciones otros clientes, números telefónicos de terceros, datos internos, ni detalles de otras conversaciones. "
                        f"Responde solo lo que este cliente necesita. Si no puedes ayudarle, dile simplemente que no puedes. "
                        f"NO uses 'ver_escritorio', 'analizar_escritorio' ni herramientas de visión. Responde DIRECTAMENTE el texto. "
                        f"Tu texto final de respuesta se escribirá y enviará automáticamente al chat de '{contacto}'."
                    )
                    
                    self.mensajes.append({"role": "user", "content": mensaje_usuario})
                    
                    # 2. Generar respuesta autónoma (procesará herramientas recursivamente)
                    print(f"🧠 Generando respuesta y ejecutando herramientas para {contacto}...")
                    respuesta_final = self.generate_response()
                    
                    # 3. Enviar la respuesta final a WhatsApp
                    if respuesta_final and respuesta_final != "Error al obtener respuesta del backend.":
                        print(f"✉️ Enviando respuesta a WhatsApp: '{respuesta_final[:150]}...'")
                        enviar_res = whatsapp_control.whatsapp_enviar_mensaje(contacto, respuesta_final)
                        print(f"Estado del envío: {enviar_res}")
                        
                        # Añadir al historial y persistir
                        self.mensajes.append({"role": "assistant", "content": respuesta_final})
                        self.guardar_estado()
                        self.intentar_consolidar_y_podar()

                        # 3b. Esperar respuesta del contacto tras enviar
                        if self._esperar_respuesta_contacto(contacto, timeout_segundos=30):
                            pass
                        else:
                            print(f"💤 Chat con '{contacto}' finalizado, esperando nuevos mensajes.")
                    else:
                        print("⚠️ Error en generación o respuesta vacía, no se envió mensaje a WhatsApp.")
                
                else:
                    # No hay mensajes no leídos en WhatsApp
                    ciclos_inactivos += 1
                    print(f"💤 Sin mensajes pendientes. (Ciclos en espera: {ciclos_inactivos})")
                    
                    # Probabilidad de práctica autónoma: 15% cada ciclo si lleva al menos 2 ciclos inactivo,
                    # o de forma garantizada cada 8 ciclos (~2 minutos) de inactividad
                    ejecutar_practica = (ciclos_inactivos >= 2 and random.random() < 0.15) or (ciclos_inactivos >= 8)
                    
                    if ejecutar_practica:
                        ciclos_inactivos = 0
                        print("\n🤖 [PENSAMIENTO AUTÓNOMO] Iniciando sesión autónoma de práctica y exploración...")
                        
                        auto_tareas = [
                            "No tengo mensajes pendientes. Voy a usar 'ver_escritorio' para capturar la pantalla y entender qué ventanas tengo abiertas actualmente.",
                            "No hay mensajes de WhatsApp. Voy a revisar el workspace usando la herramienta 'list_files' y leer el archivo readme si existe.",
                            "Voy a obtener el contexto del sistema con 'obtener_contexto_sistema' para validar que los recursos de CPU/RAM del PC estén estables.",
                            "Voy a verificar el escritorio con 'analizar_escritorio' para identificar iconos importantes y planear mover el cursor a alguno de ellos.",
                            "Voy a escribir una nota en mi memoria a largo plazo con 'guardar_memoria' registrando que el sistema autónomo proactivo de Ashly v2 está en línea y funcionando perfectamente."
                        ]
                        
                        tarea = random.choice(auto_tareas)
                        print(f"Auto-Tarea generada: '{tarea}'")
                        
                        # Inyectar pensamiento autónomo en el historial
                        self.mensajes.append({"role": "user", "content": f"[AUTO-PENSAMIENTO AUTÓNOMO]: {tarea}"})
                        
                        # Generar respuesta autónoma (procesa herramientas)
                        res_practica = self.generate_response()
                        print(f"Pensamiento finalizado. Respuesta de práctica: {res_practica}")
                        
                        self.mensajes.append({"role": "assistant", "content": res_practica})
                        self.guardar_estado()
                        self.intentar_consolidar_y_podar()
                        
                # Esperar 15 segundos entre ciclos de escaneo para no devorar la CPU y ahorrar recursos
                time.sleep(15)
                
        except KeyboardInterrupt:
            print("\n👋 Bucle autónomo proactivo detenido por el usuario.")
            VisionMonitor.detener()
            self.guardar_estado()
