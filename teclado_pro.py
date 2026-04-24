import pyautogui
import pyperclip
import time
import random

def escribir_humanamente(texto, velocidad=None):
    """
    Escribe texto de forma que soporta TODOS los caracteres (acentos, @, symbols, emojis)
    usando el portapapeles para mayor fiabilidad, o simulando teclas para texto simple.
    """
    if velocidad is None:
        # Si no hay velocidad, usamos el portapapeles (instantáneo y soporta todo)
        pyperclip.copy(texto)
        pyautogui.hotkey('ctrl', 'v')
    else:
        # Si hay velocidad, escribimos uno por uno (estilo humano)
        # Nota: pyautogui.write() falla con acentos y caracteres especiales en muchos teclados
        for char in texto:
            # Definimos caracteres que sabemos que dan problemas con write()
            es_especial = ord(char) > 127 or char in "¡¿"
            
            if not es_especial:
                try:
                    pyautogui.write(char)
                    time.sleep(random.uniform(0.05, 0.15) * velocidad)
                except:
                    es_especial = True
            
            if es_especial:
                # Usamos portapapeles para caracteres especiales (acentos, emojis, etc.)
                pyperclip.copy(char)
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(random.uniform(0.05, 0.15) * velocidad)

def presionar_combinacion(teclas):
    """Presiona una combinación de teclas (ej: ['ctrl', 'c'] o ['win', 'e'])."""
    pyautogui.hotkey(*teclas)

if __name__ == "__main__":
    print("Prueba de escritura en 3 segundos...")
    time.sleep(3)
    
    # Ejemplo con caracteres especiales, acentos y arroba
    prueba = "Hola! Este es un test @ 2024: Canción, Acción, y símbolos #$%&/()=?"
    escribir_humanamente(prueba, velocidad=1.0)
