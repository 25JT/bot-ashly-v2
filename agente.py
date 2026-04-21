import os
import json
import requests
import EdiListRead
from dotenv import load_dotenv

SERVER_URL = "http://localhost:1234/v1"

class Agent:
    def __init__(self):
        self.memoria_interna = []
        self.mensajes = [
            {"role": "system", "content": ""}
        ]
        self.actualizar_prompt_sistema()
        self.setup_tools()

    def actualizar_prompt_sistema(self):
        """Actualiza el comportamiento principal de Ashly y le inyecta su memoria actual."""
        base_prompt = "Eres Ashly, una asistente virtual amigable y servicial. Hablas en español.\n"
        base_prompt += "Si es necesario, puedes llamar a múltiples herramientas al mismo tiempo (en paralelo) o usarlas de forma secuencial.\n"
        base_prompt += "Usa la herramienta 'guardar_memoria' frecuentemente para recordar pasos, planes o cosas que ya hiciste y mantener el contexto claro.\n"
        
        if self.memoria_interna:
            base_prompt += "\n--- TU MEMORIA INTERNA (Notas y contexto guardado) ---\n"
            for i, nota in enumerate(self.memoria_interna):
                base_prompt += f"- {nota}\n"
        
        # El mensaje del rol 'system' siempre es el índice 0 del historial
        self.mensajes[0]["content"] = base_prompt

    def setup_tools(self):
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "list_files",
                    "description": "Lista los archivos en un directorio",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "directorio": {
                                "type": "string",
                                "description": "Directorio a listar"
                            }
                        },
                        "required": ["directorio"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "guardar_memoria",
                    "description": "Guarda un recordatorio o apunte importante temporal sobre lo que estás haciendo o descubriendo para no olvidarlo y guiarte en tus próximos pasos.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "dato": {
                                "type": "string",
                                "description": "El apunte detallado de lo que quieres recordar (Ej: 'Ya revisé la carpeta X', 'El plan es listar y luego leer', etc.)"
                            }
                        },
                        "required": ["dato"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "edit_file",
                    "description": "Edita un archivo existente o crea uno nuevo si no existe.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Ruta del archivo a editar o crear"
                            },
                            "content": {
                                "type": "string",
                                "description": "Contenido a escribir en el archivo"
                            },
                            "prev_text": {
                                "type": "string",
                                "description": "Texto previo a reemplazar (opcional)"
                            },
                            "new_text": {
                                "type": "string",
                                "description": "Nuevo texto a insertar (opcional)"
                            }
                        },
                        "required": ["file_path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Lee el contenido de un archivo.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Ruta del archivo a leer"
                            }
                        },
                        "required": ["file_path"]
                    }
                }
            }
        ]

    def get_active_model(self):
        """Obtiene el primer modelo disponible en LM Studio."""
        try:
            response = requests.get(f"{SERVER_URL}/models", timeout=5)
            if response.status_code == 200:
                models_data = response.json().get("data", [])
                if models_data:
                    return models_data[0]["id"]
                else:
                    print("No hay modelos disponibles")
                    return None
            else:
                print("Error al obtener los modelos 1")
                return None
        except Exception as e:
            print("Error al obtener los modelos 2", e)
            return None

    def generate_response(self):
        """Genera una respuesta usando el modelo activo y procesa las herramientas."""
        model = self.get_active_model()
        if not model:
            return "No se pudo obtener el modelo activo."
        
        try:
            response = requests.post(
                f"{SERVER_URL}/chat/completions",
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
                message = data.get("choices", [{}])[0].get("message", {})
                
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
                    return self.generate_response()

                return message.get("content", "")
            else:
                return f"Error en la generación: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error al generar respuesta: {e}"
 
           
       

    def guardar_memoria(self, dato):
        """Guarda un dato en la memoria interna y actualiza el prompt para que la IA sea consciente."""
        self.memoria_interna.append(dato)
        self.actualizar_prompt_sistema()
        return "Notificación: Dato guardado exitosamente en tu memoria interna."

    def run(self):
        print("Iniciando Ashly v2. Escribe 'salir' para terminar.")
        while True:
            userEnvio = input("\nUsuario: ").strip()
            if not userEnvio:
                continue
            elif userEnvio.lower() in ["salir", "adios", "bye", "chao"]:
                print("Ashly: ¡Adiós!")
                break
            else:
                self.mensajes.append({"role": "user", "content": userEnvio})
                resAshly = self.generate_response()
                print(f"\nAshly: {resAshly}")
                self.mensajes.append({"role": "assistant", "content": resAshly})
