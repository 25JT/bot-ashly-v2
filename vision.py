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

import threading
# --- Variables globales ---
camera = None
_ultimo_frame_hash = None
_ultimo_resultado = (None, None)
_hash_del_cache = None 
_monitor_activo = False
_hilo_monitor = None
_lock_vision = threading.Lock()

class VisionMonitor:
    @staticmethod
    def iniciar():
        global _monitor_activo, _hilo_monitor
        if not _monitor_activo:
            _monitor_activo = True
            _hilo_monitor = threading.Thread(target=VisionMonitor._loop, daemon=True)
            _hilo_monitor.start()
            print("[VISION] Vision en tiempo real iniciada.")

    @staticmethod
    def detener():
        global _monitor_activo
        _monitor_activo = False
        print("[VISION] Vision en tiempo real detenida.")

    @staticmethod
    def _loop():
        global _ultimo_resultado, _ultimo_frame_hash
        while _monitor_activo:
            try:
                # Captura rápida para detectar cambios, pero SIN forzar OCR cada vez.
                # Esto reduce drásticamente el uso de CPU.
                frame = capturar_pantalla()
                if frame is not None:
                    frame_hash = _hash_frame(frame)
                    if frame_hash != _ultimo_frame_hash:
                        # Si algo cambió, actualizamos solo el hash. 
                        # El procesamiento pesado (OCR/Base64) se hará bajo demanda.
                        _ultimo_frame_hash = frame_hash
            except Exception as e:
                print(f"Error en monitor de visión: {e}")
            time.sleep(0.15) # Un poco más lento para liberar CPU
        try:
            cv2.destroyAllWindows()
        except:
            pass

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
            #cv2.imwrite(f"frame_{int(time.time())}.jpg", frame)
            
        return frame  # BGR o BGRA
    except Exception as e:
        print(f"Error en captura: {e}")
        return None

def _hash_frame(frame):
    """Hash rápido de un frame para detectar si la pantalla cambió."""
    # Reducimos a 64x36 y hasheamos — muy barato computacionalmente
    small = cv2.resize(frame, (64, 36), interpolation=cv2.INTER_AREA)
    return hash(small.tobytes())

def dibujar_cuadricula(frame, step=100):
    """Dibuja una cuadrícula con coordenadas para ayudar a la IA a apuntar."""
    h, w = frame.shape[:2]
    color = (0, 255, 0) # Verde brillante para buen contraste
    # Hacemos una copia para no alterar permanentemente si se pasa por referencia
    grid_frame = frame.copy()
    
    for y in range(0, h, step):
        cv2.line(grid_frame, (0, y), (w, y), color, 1)
        cv2.putText(grid_frame, str(y), (5, y + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1, cv2.LINE_AA)
        
    for x in range(0, w, step):
        cv2.line(grid_frame, (x, 0), (x, h), color, 1)
        cv2.putText(grid_frame, str(x), (x + 5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1, cv2.LINE_AA)
        
    return grid_frame

def obtener_coordenadas_texto(palabra_objetivo):
    """Busca una palabra en la pantalla y devuelve sus coordenadas centrales (x, y)."""
    frame = capturar_pantalla()
    if frame is None:
        return None
        
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Intentar con diferentes modos de segmentación (PSM)
    # PSM 3: Totalmente automático (estándar)
    # PSM 11: Texto disperso (mejor para iconos de escritorio)
    modos_psm = ['--oem 3 --psm 3 -l spa+eng', '--oem 3 --psm 11 -l spa+eng']
    
    for config in modos_psm:
        try:
            datos = pytesseract.image_to_data(gray, config=config, output_type=pytesseract.Output.DICT)
            for i, texto in enumerate(datos['text']):
                if texto.strip().lower() == palabra_objetivo.lower():
                    # Calcular el centro del bounding box
                    x = datos['left'][i] + (datos['width'][i] // 2)
                    y = datos['top'][i] + (datos['height'][i] // 2)
                    return (x, y)
        except Exception as e:
            print(f"Error OCR con config {config}: {e}")
            
    return None

def preparar_vision_data(max_width=1280, forzar=False):
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
    if not forzar and frame_hash == _hash_del_cache and _ultimo_resultado[1] is not None:
        # El frame actual es igual al que usamos para el último OCR, devolvemos caché
        with _lock_vision:
            return _ultimo_resultado

    # Si llegamos aquí, es porque forzamos o el frame cambió desde el último OCR
    _hash_del_cache = frame_hash

    # --- OCR con Tesseract (Pesado, solo si es necesario) ---
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
    # Dibujamos la cuadrícula sobre la imagen para la IA, después del OCR
    frame_con_cuadricula = dibujar_cuadricula(frame_bgr)
    
    h, w = frame_con_cuadricula.shape[:2]
    new_w = max_width
    new_h = int(new_w * h / w)
    resized = cv2.resize(frame_con_cuadricula, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # JPEG calidad 75 — buen balance tamaño/legibilidad para el modelo
    _, buffer = cv2.imencode('.jpg', resized, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
    base64_str = base64.b64encode(buffer).decode('utf-8')

    with _lock_vision:
        _ultimo_resultado = (texto_detectado, base64_str)
        return _ultimo_resultado


def buscar_icono_en_pantalla(ruta_icono, umbral=0.8):
    """
    Busca una imagen (icono o botón) en la pantalla en tiempo real usando cv2.matchTemplate.
    Devuelve las coordenadas (x, y) del centro de la mejor coincidencia, o None.
    """
    try:
        frame = capturar_pantalla()
        if frame is None:
            return None
            
        template = cv2.imread(ruta_icono, cv2.IMREAD_UNCHANGED)
        if template is None:
            print(f"Error: No se pudo cargar el icono '{ruta_icono}'")
            return None
            
        # Asegurarnos de que ambos estén en BGR
        if len(template.shape) == 3 and template.shape[2] == 4:
            template = cv2.cvtColor(template, cv2.COLOR_BGRA2BGR)
            
        frame_bgr = frame
        if len(frame.shape) == 3 and frame.shape[2] == 4:
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            
        # Template Matching
        res = cv2.matchTemplate(frame_bgr, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        
        if max_val >= umbral:
            h, w = template.shape[:2]
            centro_x = max_loc[0] + w // 2
            centro_y = max_loc[1] + h // 2
            return (centro_x, centro_y)
            
        return None
    except Exception as e:
        print(f"Error en buscar_icono_en_pantalla: {e}")
        return None

def esperar_cambio_visual(timeout_segundos=10, sensibilidad=25, umbral_pixeles=1000):
    """
    Monitorea la pantalla en tiempo real a alta velocidad y se pausa hasta que
    detecta un cambio significativo (como la carga de una web o un mensaje nuevo).
    Retorna True si hubo cambio, False si se agotó el tiempo.
    """
    inicio = time.time()
    
    frame_base = capturar_pantalla()
    if frame_base is None:
        return False
        
    frame_base_gray = cv2.cvtColor(frame_base, cv2.COLOR_BGR2GRAY)
    frame_base_blur = cv2.GaussianBlur(frame_base_gray, (21, 21), 0)
    
    while time.time() - inicio < timeout_segundos:
        time.sleep(0.05)  # 20 FPS para no bloquear CPU
        frame_actual = capturar_pantalla()
        if frame_actual is None:
            continue
            
        gray = cv2.cvtColor(frame_actual, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (21, 21), 0)
        
        diff = cv2.absdiff(frame_base_blur, blur)
        _, thresh = cv2.threshold(diff, sensibilidad, 255, cv2.THRESH_BINARY)
        
        cambios = cv2.countNonZero(thresh)
        if cambios > umbral_pixeles:
            return True
            
    return False

if __name__ == "__main__":
    print("Probando visión con Tesseract...")
    t0 = time.time()
    texto, img = preparar_vision_data()
    t1 = time.time()
    print(f"\nTiempo: {t1-t0:.2f}s")
    print("\n--- TEXTO DETECTADO ---")
    print(texto[:500])
    print(f"\nImagen Base64 (largo: {len(img) if img else 0})")