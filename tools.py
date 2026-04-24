def get_tools():
    return [
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
                "description": "Escribe texto en el editor activo.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "texto": {
                            "type": "string",
                            "description": "Texto a escribir"
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
                "description": "Presiona las teclas del teclado para escribir texto comabinaciones de teclas etc todo lo que necesitas de un teclado",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "teclas": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "Escribir texto o presionar teclas"
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
        }
    ]