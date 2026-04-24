import json
import os

class StorageManager:
    """Clase encargada de la persistencia de datos en archivos JSON."""
    
    def __init__(self, historial_path="historial.json", memoria_path="memoria_agente.json"):
        self.historial_path = historial_path
        self.memoria_path = memoria_path

    def guardar_completamente(self, mensajes, memoria_interna, recompensas):
        """Guarda todo el estado del agente en sus respectivos archivos."""
        # Guardar Historial de conversación
        with open(self.historial_path, 'w', encoding='utf-8') as f:
            json.dump(mensajes, f, indent=4, ensure_ascii=False)
            
        # Guardar Memoria a largo plazo y recompensas
        datos_memoria = {
            "recompensas": recompensas,
            "conocimientos": memoria_interna
        }
        with open(self.memoria_path, 'w', encoding='utf-8') as f:
            json.dump(datos_memoria, f, indent=4, ensure_ascii=False)

    def cargar_datos(self):
        """Carga el historial y la memoria desde los archivos si existen."""
        mensajes = []
        memoria_interna = []
        recompensas = 0

        # Cargar Historial
        if os.path.exists(self.historial_path):
            try:
                with open(self.historial_path, 'r', encoding='utf-8') as f:
                    mensajes = json.load(f)
            except:
                mensajes = []

        # Cargar Memoria y Recompensas
        if os.path.exists(self.memoria_path):
            try:
                with open(self.memoria_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    recompensas = data.get("recompensas", 0)
                    memoria_interna = data.get("conocimientos", [])
            except:
                pass
                
        return mensajes, memoria_interna, recompensas
