import json
import os

# ═════════════════════════════════════════════════════════════════════════════
# CLASE: StorageManager
# ═════════════════════════════════════════════════════════════════════════════
class StorageManager:
    """
    Clase centralizada para gestionar la persistencia en disco del estado del agente.
    Se encarga de guardar y recuperar:
    1. El historial continuo de conversación (historial.json).
    2. La memoria a largo plazo y recompensas (memoria_agente.json).
    
    El uso de JSON permite que el sistema de memoria sea legible, 
    fácil de depurar y compatible con estructuras de diccionarios.
    """
    
    def __init__(self, historial_path="historial.json", memoria_path="memoria_agente.json"):
        """
        Inicializa las rutas donde se guardarán los archivos JSON locales.
        Por defecto los guarda en la misma carpeta del script.
        """
        self.historial_path = historial_path
        self.memoria_path = memoria_path

    # ─── MÉTODOS DE GUARDADO ─────────────────────────────────────────────────────

    def guardar_completamente(self, mensajes, memoria_interna, recompensas):
        """
        Guarda todo el estado del agente de forma sincrónica en sus respectivos archivos.
        Sobrescribe los archivos existentes por completo.
        
        Argumentos:
            mensajes (list): Lista de diccionarios con el historial de mensajes OpenAI-style.
            memoria_interna (list): Hechos, reglas o datos aprendidos por el agente a largo plazo.
            recompensas (int): Puntuación acumulada de retroalimentación humana.
        """
        # Guardar Historial de conversación
        # Usamos ensure_ascii=False para que los acentos y emojis en español se guarden bien
        with open(self.historial_path, 'w', encoding='utf-8') as f:
            json.dump(mensajes, f, indent=4, ensure_ascii=False)
            
        # Guardar Memoria a largo plazo y Recompensas empaquetadas en un solo JSON
        datos_memoria = {
            "recompensas": recompensas,
            "conocimientos": memoria_interna
        }
        with open(self.memoria_path, 'w', encoding='utf-8') as f:
            json.dump(datos_memoria, f, indent=4, ensure_ascii=False)

    # ─── MÉTODOS DE CARGA ────────────────────────────────────────────────────────

    def cargar_datos(self):
        """
        Carga el historial y la memoria desde los archivos locales si estos existen.
        Si hay un archivo corrupto o no existe, inicializa las estructuras vacías,
        garantizando que el agente siempre pueda iniciar "desde cero" de forma segura.
        
        Retorna:
            tuple: (mensajes, memoria_interna, recompensas) listos para ser 
                   inyectados en el estado del agente (clase Agent).
        """
        mensajes = []
        memoria_interna = []
        recompensas = 0

        # Cargar Historial
        if os.path.exists(self.historial_path):
            try:
                with open(self.historial_path, 'r', encoding='utf-8') as f:
                    mensajes = json.load(f)
            except:
                # Si el JSON se corrompe por un apagado repentino, empezamos limpios.
                mensajes = []

        # Cargar Memoria y Recompensas
        if os.path.exists(self.memoria_path):
            try:
                with open(self.memoria_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Usamos .get() para evitar KeyErrors si el archivo es antiguo
                    # o le faltan claves.
                    recompensas = data.get("recompensas", 0)
                    memoria_interna = data.get("conocimientos", [])
            except:
                # Silenciamos la excepción para un arranque suave en caso de corrupción
                pass
                
        return mensajes, memoria_interna, recompensas
