import pyautogui
import dxcam
import cv2
import base64
import numpy as np
import pytesseract
import time

# Apunta al ejecutable de Tesseract (ajusta la ruta si es diferente)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# --- Variables globales ---
camera = None
_ultimo_frame_hash = None
_ultimo_resultado = (None, None)

def get_camera():
    global camera
    if camera is None:
        camera = dxcam.create(output_color="BGR")
    return camera

def capturar_pantalla():
    """Captura el escritorio usando dxcam y dibuja el cursor del mouse."""
    try:
        cam = get_camera()
        frame = cam.grab()
        
        if frame is not None:
            # Dibujar el cursor del mouse para que Ashly pueda verlo
            try:
                mx, my = pyautogui.position()
                # Asegurarse de que el frame sea escribible
                frame = frame.copy() 
                h, w = frame.shape[:2]
                if 0 <= mx < w and 0 <= my < h:
                    # Dibujamos un círculo rojo con borde blanco para contraste
                    cv2.circle(frame, (mx, my), 7, (255, 255, 255), -1) # Borde
                    cv2.circle(frame, (mx, my), 5, (0, 0, 255), -1)   # Centro rojo
            except Exception as e_cursor:
                print(f"No se pudo dibujar el cursor: {e_cursor}")

            # Guardar foto para debugging (opcional, pero útil para el usuario)
            cv2.imwrite(f"frame_{int(time.time())}.jpg", frame)
            
        return frame  # BGR o BGRA
    except Exception as e:
        print(f"Error en captura: {e}")
        return None

def _hash_frame(frame):
    """Hash rápido de un frame para detectar si la pantalla cambió."""
    # Reducimos a 64x36 y hasheamos — muy barato computacionalmente
    small = cv2.resize(frame, (64, 36), interpolation=cv2.INTER_AREA)
    return hash(small.tobytes())

def preparar_vision_data(max_width=1920, forzar=False):
    """
    Captura, OCR con Tesseract y prepara imagen en Base64.
    Si la pantalla no cambió y no se fuerza, devuelve el resultado cacheado.
    Retorna (texto_ocr, imagen_base64)
    """
    global _ultimo_frame_hash, _ultimo_resultado

    frame = capturar_pantalla()
    if frame is None:
        return "No se pudo capturar la pantalla.", None

    # --- Detección de cambio ---
    frame_hash = _hash_frame(frame)
    if not forzar and frame_hash == _ultimo_frame_hash:
        # Pantalla idéntica a la última captura, devolvemos caché
        return _ultimo_resultado

    _ultimo_frame_hash = frame_hash

    # --- OCR con Tesseract (rápido en CPU) ---
    try:
        # Convertimos a RGB para PIL/Tesseract
        if frame.shape[2] == 4:  # BGRA → BGR
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        else:
            frame_bgr = frame

        # Tesseract funciona mejor con imagen en escala de grises
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        
        # Config: modo página automático, español + inglés
        config = '--oem 3 --psm 3 -l spa+eng'
        texto_detectado = pytesseract.image_to_string(gray, config=config)
        texto_detectado = texto_detectado.strip()
    except Exception as e:
        texto_detectado = f"Error en OCR: {e}"
        frame_bgr = frame

    # --- Preparar imagen para la IA ---
    h, w = frame_bgr.shape[:2]
    new_w = max_width
    new_h = int(new_w * h / w)
    resized = cv2.resize(frame_bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # JPEG calidad 75 — buen balance tamaño/legibilidad para el modelo
    _, buffer = cv2.imencode('.jpg', resized, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
    base64_str = base64.b64encode(buffer).decode('utf-8')

    _ultimo_resultado = (texto_detectado, base64_str)
    return _ultimo_resultado


if __name__ == "__main__":
    print("Probando visión con Tesseract...")
    t0 = time.time()
    texto, img = preparar_vision_data()
    t1 = time.time()
    print(f"\nTiempo: {t1-t0:.2f}s")
    print("\n--- TEXTO DETECTADO ---")
    print(texto[:500])
    print(f"\nImagen Base64 (largo: {len(img) if img else 0})")