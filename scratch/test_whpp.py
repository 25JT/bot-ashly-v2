import uiautomation as auto
import time

try:
    print("Probando SendKeys de uiautomation...")
    # Intentamos enviar a la nada o a una ventana cualquiera
    auto.SendKeys("MC{Enter}")
    print("Prueba exitosa (o al menos no dio el error de ord())")
except Exception as e:
    print(f"Error detectado: {e}")
