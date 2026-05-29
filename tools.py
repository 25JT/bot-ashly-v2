def get_tools():
    return [
        {
            "type": "function",
            "function": {
                "name": "excel_escribir_interseccion",
                "description": "Busca un texto en las filas (ej. 'Juana') y un texto en las columnas (ej. '10') de Excel, y escribe un valor exactamente en la celda donde se cruzan. Útil para rellenar tablas rápidamente sin usar el ratón.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fila_texto": {
                            "type": "string",
                            "description": "El texto que identifica la fila (ej. 'Juana', 'Total')."
                        },
                        "columna_texto": {
                            "type": "string",
                            "description": "El texto o número que identifica la columna (ej. '10', 'Enero')."
                        },
                        "valor": {
                            "type": "string",
                            "description": "El valor a escribir en la celda cruzada (ej. 'x', '500')."
                        }
                    },
                    "required": ["fila_texto", "columna_texto", "valor"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "word_crear_documento",
                "description": "Crea un nuevo documento de Microsoft Word en blanco y lo pone en primer plano.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "word_escribir_texto",
                "description": "Escribe texto en el documento activo de Microsoft Word en la posición actual del cursor.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "texto": {
                            "type": "string",
                            "description": "El texto que se desea escribir."
                        },
                        "nueva_linea": {
                            "type": "boolean",
                            "description": "¿Debe saltar a una nueva línea después de escribir? (Por defecto true)."
                        }
                    },
                    "required": ["texto"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "word_aplicar_formato",
                "description": "Aplica formato al texto que se escribirá a continuación o a la selección actual en Word (negrita, tamaño, etc.).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "negrita": { "type": "boolean" },
                        "cursiva": { "type": "boolean" },
                        "subrayado": { "type": "boolean" },
                        "tamaño": { "type": "integer", "description": "Tamaño de fuente (ej. 12, 16, 24)." }
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "word_guardar_como",
                "description": "Guarda el documento de Word actual en una ruta específica del disco.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ruta": {
                            "type": "string",
                            "description": "La ruta absoluta donde guardar (ej. 'C:\\Usuarios\\Reporte.docx')."
                        }
                    },
                    "required": ["ruta"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "whatsapp_enviar_mensaje",
                "description": "Busca un contacto por su nombre o número de teléfono en WhatsApp Desktop y le envía un mensaje automáticamente.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "contacto": {
                            "type": "string",
                            "description": "Nombre del contacto o número de teléfono (ej. '+573146290195')."
                        },
                        "mensaje": {
                            "type": "string",
                            "description": "El contenido del mensaje a enviar."
                        }
                    },
                    "required": ["contacto", "mensaje"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "whatsapp_obtener_ultimo_mensaje",
                "description": "Intenta leer el último mensaje del chat que esté abierto actualmente en WhatsApp.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "whatsapp_leer_conversacion",
                "description": "Lee los últimos mensajes de la conversación activa en WhatsApp para obtener contexto de lo que se ha hablado.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limite": {
                            "type": "integer",
                            "description": "Cantidad de mensajes recientes a leer (por defecto 5)."
                        }
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "whatsapp_listar_chats_recientes",
                "description": "Lista los contactos y chats visibles en el panel izquierdo de WhatsApp, útil para ver quién ha enviado mensajes nuevos o buscar conversaciones activas.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "whatsapp_navegar_a_seccion",
                "description": "Cambia entre las diferentes pestañas de la aplicación WhatsApp Desktop.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "seccion": {
                            "type": "string",
                            "enum": ["chats", "estados", "llamadas", "comunidades"],
                            "description": "La sección a la que se desea navegar."
                        }
                    },
                    "required": ["seccion"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "excel_escribir_celda",
                "description": "Escribe un valor directamente en una celda de Excel usando su código alfanumérico (ej. A1, B5).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "celda": {
                            "type": "string",
                            "description": "La referencia de la celda de Excel (ej. 'C12')."
                        },
                        "valor": {
                            "type": "string",
                            "description": "El valor a escribir en la celda."
                        }
                    },
                    "required": ["celda", "valor"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "analizar_campos_texto",
                "description": "Detecta qué programa está en primer plano y devuelve una lista de las áreas y cajas de texto donde se puede escribir, junto con sus coordenadas exactas (x, y) para usar con mover_mouse o click_izquierdo.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "verificar_programa_abierto",
                "description": "Comprueba si un programa específico ya está abierto buscando su nombre en los títulos de las ventanas activas. Útil para no abrir duplicados.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "nombre": {
                            "type": "string",
                            "description": "Nombre parcial del programa a buscar (ej. 'WhatsApp', 'Excel')."
                        }
                    },
                    "required": ["nombre"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "analizar_barra_tareas",
                "description": "Detecta programáticamente todos los iconos y aplicaciones en la barra de tareas de Windows (incluyendo inicio, aplicaciones abiertas y reloj), devolviendo sus coordenadas exactas.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "analizar_escritorio",
                "description": "Detecta programáticamente todos los iconos y carpetas en el escritorio de Windows, devolviendo sus nombres y coordenadas exactas. Útil cuando no puedes encontrar un programa visualmente.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "abrir_archivo",
                "description": "Busca y abre un archivo o programa por su nombre de forma programática. Usa esto en lugar de buscar iconos visualmente. Ejemplos: 'excel', 'reporte financiero', 'documento word'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "nombre_archivo": {
                            "type": "string",
                            "description": "El nombre del archivo o programa a buscar y abrir (no es necesario que sea exacto)."
                        }
                    },
                    "required": ["nombre_archivo"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "buscar_icono_en_pantalla",
                "description": "Busca una imagen, icono o botón en la pantalla en tiempo real (milisegundos) usando OpenCV Template Matching. Devuelve sus coordenadas (x,y) si lo encuentra.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ruta_icono": {
                            "type": "string",
                            "description": "La ruta absoluta de la imagen (.png o .jpg) del icono a buscar."
                        }
                    },
                    "required": ["ruta_icono"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "esperar_cambio_visual",
                "description": "Monitorea la pantalla en tiempo real a alta velocidad y se pausa hasta que detecta un cambio visual (ej. termina de cargar una página o llega un mensaje nuevo).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "timeout_segundos": {
                            "type": "integer",
                            "description": "Tiempo máximo a esperar por un cambio, en segundos (por defecto 10)."
                        }
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "click_texto",
                "description": "Busca una palabra exacta en la pantalla usando OCR y hace click izquierdo automáticamente en el centro de ella. Útil para botones, menús e iconos con texto.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "palabra": {
                            "type": "string",
                            "description": "La palabra exacta o texto sobre el que hacer click (no sensible a mayúsculas)."
                        }
                    },
                    "required": ["palabra"]
                }
            }
        },
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
        },
        {
            "type": "function",
            "function": {
                "name": "dar_recompensa",
                "description": "Herramienta opcional para cuando el usuario o el sistema quieren recompensar al bot con puntos por buen desempeño.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "puntos": {
                            "type": "integer",
                            "description": "Cantidad de puntos a otorgar (Ej: 10, 20)"
                        },
                        "motivo": {
                            "type": "string",
                            "description": "¿Por qué se le dio la recompensa?"
                        }
                    },
                    "required": ["puntos", "motivo"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "escribir_texto",
                "description": "Escribe texto fluido (frases, nombres, correos, mensajes). Úsala SIEMPRE que necesites escribir algo largo de forma humana.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "texto": {
                            "type": "string",
                            "description": "El texto completo a escribir."
                        }
                    },
                    "required": ["texto"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "presionar_teclas",
                "description": "Presiona combinaciones de teclas (ej: 'ctrl','c') o teclas especiales (ej: 'enter', 'win', 'backspace'). NO LA USES PARA ESCRIBIR FRASES.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "teclas": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "Lista de teclas a presionar simultáneamente o en secuencia rápida. Ej: ['ctrl', 'alt', 'del'] o ['enter']."
                        }
                    },
                    "required": ["teclas"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "mover_mouse",
                "description": "Mueve el mouse por pantalla a la pisicion que desees",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "x": {
                            "type": "integer",
                            "description": "Coordenada X"
                        },
                        "y": {
                            "type": "integer",
                            "description": "Coordenada Y"
                        }
                    },
                    "required": ["x", "y"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "arrastrar_y_soltar",
                "description": "Arrastra el mouse desde un punto a otro. te puede servir para arrastrar archivos de un lado a otro o ventanas.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "x1": {
                            "type": "integer",
                            "description": "Coordenada X inicial"
                        },
                        "y1": {
                            "type": "integer",
                            "description": "Coordenada Y inicial"
                        },
                        "x2": {
                            "type": "integer",
                            "description": "Coordenada X final"
                        },
                        "y2": {
                            "type": "integer",
                            "description": "Coordenada Y final"
                        }
                    },
                    "required": ["x1", "y1", "x2", "y2"]
                }
            }
        },{
            "type": "function",
            "function": {
                "name": "analizar_entorno",
                "description": "Analiza el entorno y retorna un mapa detallado de ventanas con posiciones y estados.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "click_izquierdo",
                "description": "Realiza un click con el botón izquierdo del mouse en la posición actual.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "click_derecho",
                "description": "Realiza un click con el botón derecho del mouse en la posición actual.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "click_central",
                "description": "Realiza un click con el botón central (rueda) del mouse en la posición actual.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "scroll_mouse",
                "description": "Mueve la rueda del mouse hacia arriba o hacia abajo.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cantidad": {
                            "type": "integer",
                            "description": "Cantidad de scroll. Positivo para arriba, negativo para abajo. Ejemplo: 3 para arriba, -3 para abajo."
                        }
                    },
                    "required": ["cantidad"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "ver_escritorio",
                "description": "Fuerza una captura de pantalla y OCR para ver el estado actual del escritorio.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "controlar_ventana",
                "description": "Controla una ventana del sistema por su título. Puede minimizarla, maximizarla, restaurarla, cerrarla o enfocarla (traerla al frente).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "titulo": {
                            "type": "string",
                            "description": "Parte del título de la ventana a controlar. Ej: 'Chrome', 'Bloc de notas', 'Explorador'."
                        },
                        "accion": {
                            "type": "string",
                            "description": "Acción a realizar: 'minimizar', 'maximizar', 'restaurar', 'cerrar', 'enfocar'."
                        }
                    },
                    "required": ["titulo", "accion"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "abrir_programa",
                "description": "Abre un programa, aplicación o archivo del sistema. Usar comandos del sistema como: 'notepad', 'calc', 'explorer', 'chrome', 'code', 'cmd', etc.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "comando": {
                            "type": "string",
                            "description": "El comando del programa a abrir. Ej: 'notepad', 'calc', 'chrome', 'explorer C:\\\\', 'cmd'."
                        }
                    },
                    "required": ["comando"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "listar_ventanas_win32",
                "description": "Lista todas las ventanas abiertas y visibles del sistema con sus títulos y handles.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "mover_ventana",
                "description": "Mueve y redimensiona una ventana a una posición y tamaño exactos en la pantalla.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "titulo": {"type": "string", "description": "Título parcial de la ventana."},
                        "x": {"type": "integer", "description": "Posición X (píxeles desde la izquierda)."},
                        "y": {"type": "integer", "description": "Posición Y (píxeles desde arriba)."},
                        "ancho": {"type": "integer", "description": "Ancho de la ventana en píxeles."},
                        "alto": {"type": "integer", "description": "Alto de la ventana en píxeles."}
                    },
                    "required": ["titulo", "x", "y", "ancho", "alto"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "obtener_contexto_sistema",
                "description": "Obtiene un resumen completo del entorno actual: ventana activa, proceso en uso, posición del cursor, contenido del portapapeles, uso de CPU y RAM, y fecha/hora.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "listar_procesos",
                "description": "Lista los procesos del sistema actualmente en ejecución, ordenados por uso de CPU.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "leer_portapapeles",
                "description": "Lee el texto que está actualmente copiado en el portapapeles del sistema.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "escribir_portapapeles",
                "description": "Escribe un texto en el portapapeles del sistema para que pueda ser pegado en cualquier aplicación.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "texto": {
                            "type": "string",
                            "description": "Texto a copiar en el portapapeles."
                        }
                    },
                    "required": ["texto"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "activar_red_neuronal_autonoma",
                "description": "Delega el control a la Red Neuronal (CNN + Imitation Learning) para que ejecute tareas de forma autónoma basándose en la visión, sin saturar el historial textual. Útil para tareas repetitivas o visuales como usar Spotify.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "objetivo": {
                            "type": "string",
                            "description": "El objetivo que la red neuronal debe cumplir (ej. 'Reproducir musica con dj livi en spotify')."
                        }
                    },
                    "required": ["objetivo"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "whatsapp_detectar_nuevos_mensajes",
                "description": "Escanea los chats activos de WhatsApp Desktop en el panel izquierdo buscando mensajes no leídos. Si los hay, abre el chat, lee la conversación y los devuelve.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
    ]