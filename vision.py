import pyautogui
import dxcam
import cv2
import base64
import numpy as np
import pytesseract
import time

# ═════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE TESSERACT OCR
# ═════════════════════════════════════════════════════════════════════════════
# Apunta al ejecutable de Tesseract (ajusta la ruta si es diferente)
# Tesseract es el motor OCR que permite a la IA "leer" texto de las imágenes.
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# ═════════════════════════════════════════════════════════════════════════════
# CONCIENTIZACIÓN DE DPI DE WINDOWS
# ═════════════════════════════════════════════════════════════════════════════
import ctypes
try:
    # Esto evita que Windows escale (haga zoom) la captura de pantalla si el
    # usuario tiene el "Escalado de pantalla" en 125%, 150%, etc.
    # Si no hacemos esto, dxcam captura solo una porción de la pantalla.
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

import threading

# ═════════════════════════════════════════════════════════════════════════════
# VARIABLES GLOBALES DEL SISTEMA DE VISIÓN
# ═════════════════════════════════════════════════════════════════════════════
camera = None                     # Instancia global de dxcam (capturador)
_ultimo_frame_hash = None         # Hash del último frame capturado para detectar cambios rápidos
_ultimo_resultado = (None, None)  # Tupla (texto_ocr, imagen_base64) cacheada
_hash_del_cache = None            # Hash asociado al frame que se procesó por última vez en OCR
_monitor_activo = False           # Bandera para saber si el hilo de monitoreo está vivo
_hilo_monitor = None              # Referencia al hilo que monitorea la pantalla
_lock_vision = threading.Lock()   # Lock para evitar condiciones de carrera al acceder al caché de OCR

# ═════════════════════════════════════════════════════════════════════════════
# CLASE: VisionMonitor
# ═════════════════════════════════════════════════════════════════════════════
class VisionMonitor:
    """
    Monitor en segundo plano que observa la pantalla continuamente.
    Su objetivo principal es detectar SI la pantalla cambió (usando un hash barato).
    Si cambia, actualiza el hash global para que el sistema sepa que debe
    hacer un nuevo OCR la próxima vez que el agente pregunte.
    NO hace OCR continuo para no derretir la CPU.
    """
    @staticmethod
    def iniciar():
        """Inicia el hilo demonio de monitoreo si no está activo."""
        global _monitor_activo, _hilo_monitor
        if not _monitor_activo:
            _monitor_activo = True
            _hilo_monitor = threading.Thread(target=VisionMonitor._loop, daemon=True)
            _hilo_monitor.start()
            print("[VISION] Vision en tiempo real iniciada.")

    @staticmethod
    def detener():
        """Detiene el hilo de monitoreo de pantalla."""
        global _monitor_activo
        _monitor_activo = False
        print("[VISION] Vision en tiempo real detenida.")

    @staticmethod
    def _loop():
        """Bucle infinito del monitor que calcula el hash de la pantalla."""
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
            
            # Un pequeño sleep (0.15s) equivale a ~6-7 FPS de comprobación de cambios,
            # suficiente para saber si la pantalla está estable o no.
            time.sleep(0.15) 
            
        # Limpieza al salir del bucle
        try:
            cv2.destroyAllWindows()
        except:
            pass

# ═════════════════════════════════════════════════════════════════════════════
# FUNCIONES NÚCLEO DE CAPTURA
# ═════════════════════════════════════════════════════════════════════════════

def get_camera():
    """
    Patrón Singleton para la cámara DXcam. 
    DXcam es extremadamente rápido (captura directo desde la GPU en Windows).
    """
    global camera
    if camera is None:
        camera = dxcam.create(output_color="BGR")
    return camera

def capturar_pantalla():
    """
    Captura el escritorio usando dxcam y dibuja explícitamente el cursor del mouse.
    DXcam por defecto no captura el cursor del sistema, así que lo inyectamos 
    artificialmente para que la IA sepa dónde está el ratón en la imagen.
    """
    try:
        cam = get_camera()
        frame = cam.grab()
        
        if frame is not None:
            # Dibujar el cursor del mouse para que Ashly pueda verlo
            try:
                mx, my = pyautogui.position()
                # Asegurarse de que el frame sea escribible (copia superficial)
                frame = frame.copy() 
                h, w = frame.shape[:2]
                
                # Si el ratón está dentro de los límites de la pantalla
                if 0 <= mx < w and 0 <= my < h:
                    # Dibujamos un círculo rojo con borde blanco para alto contraste
                    cv2.circle(frame, (mx, my), 7, (255, 255, 255), -1) # Borde blanco
                    cv2.circle(frame, (mx, my), 5, (0, 0, 255), -1)     # Centro rojo
            except Exception as e_cursor:
                print(f"No se pudo dibujar el cursor: {e_cursor}")

            # (Opcional) Guardar foto para debugging
            #cv2.imwrite(f"frame_{int(time.time())}.jpg", frame)
            
        return frame  # Retorna matriz numpy en formato BGR o BGRA
    except Exception as e:
        print(f"Error en captura: {e}")
        return None

def _hash_frame(frame):
    """
    Hash rápido de un frame para detectar si la pantalla cambió.
    En lugar de comparar millones de píxeles, reducimos la imagen a un tamaño
    minúsculo (64x36) y calculamos su hash en memoria. Esto es O(1) virtualmente.
    """
    small = cv2.resize(frame, (64, 36), interpolation=cv2.INTER_AREA)
    return hash(small.tobytes())

# ═════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE AYUDA PARA LA IA (CUADRÍCULA Y OCR)
# ═════════════════════════════════════════════════════════════════════════════

def dibujar_cuadricula(frame, step=100):
    """
    Dibuja una cuadrícula con coordenadas sobre la imagen.
    Esto es CRÍTICO para que los Modelos de Lenguaje Visuales (VLMs) 
    puedan "apuntar" y decirnos coordenadas (x,y) precisas.
    Sin la cuadrícula, la IA suele fallar estrepitosamente al estimar píxeles.
    """
    h, w = frame.shape[:2]
    color = (0, 255, 0) # Verde brillante para buen contraste
    
    # Hacemos una copia para no alterar permanentemente la imagen original
    grid_frame = frame.copy()
    
    # Dibujar líneas horizontales
    for y in range(0, h, step):
        cv2.line(grid_frame, (0, y), (w, y), color, 1)
        # Etiqueta en Y
        cv2.putText(grid_frame, str(y), (5, y + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1, cv2.LINE_AA)
        
    # Dibujar líneas verticales
    for x in range(0, w, step):
        cv2.line(grid_frame, (x, 0), (x, h), color, 1)
        # Etiqueta en X
        cv2.putText(grid_frame, str(x), (x + 5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1, cv2.LINE_AA)
        
    return grid_frame

def obtener_coordenadas_texto(palabra_objetivo):
    """
    Busca una palabra específica en la pantalla usando Tesseract OCR y 
    devuelve las coordenadas centrales (x, y) de donde se encuentra.
    Útil para la herramienta "click_texto".
    """
    frame = capturar_pantalla()
    if frame is None:
        return None
        
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Intentar con diferentes modos de segmentación (PSM) de Tesseract
    # PSM 3: Totalmente automático (estándar, asume un bloque de texto)
    # PSM 11: Texto disperso (mejor para encontrar iconos sueltos en el escritorio)
    modos_psm = ['--oem 3 --psm 3 -l spa+eng', '--oem 3 --psm 11 -l spa+eng']
    
    for config in modos_psm:
        try:
            # Output.DICT nos devuelve cajas delimitadoras (bounding boxes) y confianza
            datos = pytesseract.image_to_data(gray, config=config, output_type=pytesseract.Output.DICT)
            
            for i, texto in enumerate(datos['text']):
                # Comparamos ignorando mayúsculas y espacios
                if texto.strip().lower() == palabra_objetivo.lower():
                    # Calcular el centro exacto del bounding box de la palabra
                    x = datos['left'][i] + (datos['width'][i] // 2)
                    y = datos['top'][i] + (datos['height'][i] // 2)
                    return (x, y)
        except Exception as e:
            print(f"Error OCR con config {config}: {e}")
            
    # Si no la encuentra después de probar todos los modos, retorna None
    return None

# ═════════════════════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL DE INGESTA DE VISIÓN PARA EL AGENTE
# ═════════════════════════════════════════════════════════════════════════════

def preparar_vision_data(max_width=1440, forzar=False):
    """
    El corazón del sistema de visión.
    Captura, aplica OCR con Tesseract, dibuja la cuadrícula y prepara la imagen
    en formato Base64 para ser enviada al LLM.
    
    OPTIMIZACIÓN: Si la pantalla no cambió desde la última vez (según el hash),
    y no se forza explícitamente (`forzar=False`), devuelve el resultado cacheado
    para ahorrar valiosos segundos de procesamiento OCR.
    
    Retorna:
        tuple: (texto_ocr_extraido, imagen_en_base64)
    """
    global _ultimo_frame_hash, _ultimo_resultado, _hash_del_cache

    frame = capturar_pantalla()
    if frame is None:
        return "No se pudo capturar la pantalla.", None

    # --- Detección de cambio y Cacheo ---
    frame_hash = _hash_frame(frame)
    if not forzar and frame_hash == _hash_del_cache and _ultimo_resultado[1] is not None:
        # El frame actual es idéntico al que usamos para el último OCR.
        # Devolvemos la caché bajo lock para evitar problemas de concurrencia.
        with _lock_vision:
            return _ultimo_resultado

    # Si llegamos aquí, es porque forzamos o el frame cambió desde el último OCR.
    # Actualizamos el hash del caché actual.
    _hash_del_cache = frame_hash

    # --- Procesamiento OCR con Tesseract (Operación Pesada) ---
    try:
        # Convertimos a formato BGR limpio si viene en BGRA (con Alpha)
        if frame.shape[2] == 4:  
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        else:
            frame_bgr = frame

        # OCR sobre la imagen en color para conservar mejor la información visual.
        # Tesseract igual puede trabajar sobre BGR/RGB directamente.
        config = '--oem 3 --psm 3 -l spa+eng'
        texto_detectado = pytesseract.image_to_string(frame_bgr, config=config)
        texto_detectado = texto_detectado.strip()
    except Exception as e:
        texto_detectado = f"Error en OCR: {e}"
        frame_bgr = frame

    # --- Preparar imagen final para la IA ---
    # Dibujamos la cuadrícula DESPUÉS del OCR para no confundir a Tesseract con las líneas verdes.
    frame_con_cuadricula = dibujar_cuadricula(frame_bgr)
    
    # Redimensionado inteligente para ahorrar tokens/ancho de banda
    # Mantenemos el aspect ratio original.
    h, w = frame_con_cuadricula.shape[:2]
    new_w = max_width
    new_h = int(new_w * h / w)
    resized = cv2.resize(frame_con_cuadricula, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # Codificamos a JPEG con una calidad un poco mayor para conservar mejor detalles y color.
    _, buffer = cv2.imencode('.jpg', resized, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    base64_str = base64.b64encode(buffer).decode('utf-8')

    # Guardamos en caché y retornamos (protegido por thread lock)
    with _lock_vision:
        _ultimo_resultado = (texto_detectado, base64_str)
        return _ultimo_resultado


# ═════════════════════════════════════════════════════════════════════════════
# FUNCIONES AVANZADAS DE DETECCIÓN Y ESPERA
# ═════════════════════════════════════════════════════════════════════════════

def buscar_icono_en_pantalla(ruta_icono, umbral=0.8):
    """
    Realiza "Template Matching" (búsqueda de patrones) clásico usando OpenCV.
    Busca una pequeña imagen (plantilla) dentro de la pantalla completa.
    
    Argumentos:
        ruta_icono (str): Ruta al archivo .png o .jpg a buscar.
        umbral (float): Confianza mínima (0.0 a 1.0) para considerarlo un match.
        
    Retorna:
        tuple: Coordenadas (x, y) del centro del icono si se encuentra, o None.
    """
    try:
        frame = capturar_pantalla()
        if frame is None:
            return None
            
        template = cv2.imread(ruta_icono, cv2.IMREAD_UNCHANGED)
        if template is None:
            print(f"Error: No se pudo cargar el icono '{ruta_icono}'")
            return None
            
        # Homogeneizar los canales de color (BGR)
        if len(template.shape) == 3 and template.shape[2] == 4:
            template = cv2.cvtColor(template, cv2.COLOR_BGRA2BGR)
            
        frame_bgr = frame
        if len(frame.shape) == 3 and frame.shape[2] == 4:
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            
        # matchTemplate escanea la imagen grande deslizando la pequeña por encima
        # TM_CCOEFF_NORMED es robusto a cambios ligeros de iluminación
        res = cv2.matchTemplate(frame_bgr, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        
        # Si la confianza supera nuestro umbral
        if max_val >= umbral:
            h, w = template.shape[:2]
            # Calculamos el centro sumando la mitad del ancho y alto a la esquina sup-izq
            centro_x = max_loc[0] + w // 2
            centro_y = max_loc[1] + h // 2
            return (centro_x, centro_y)
            
        return None
    except Exception as e:
        print(f"Error en buscar_icono_en_pantalla: {e}")
        return None

def esperar_cambio_visual(timeout_segundos=10, sensibilidad=25, umbral_pixeles=1000):
    """
    Monitorea la pantalla activamente (alta frecuencia) y bloquea la ejecución
    hasta que detecta un cambio visual masivo. 
    
    Es increíblemente útil para sincronizar a la IA con cargas de páginas web,
    apertura de programas, o animaciones lentas. Evita el uso de "sleeps" ciegos.
    
    Argumentos:
        timeout_segundos (int): Máximo tiempo a esperar antes de rendirse.
        sensibilidad (int): Tolerancia de ruido en la diferencia de píxeles (0-255).
        umbral_pixeles (int): Cantidad de píxeles que deben cambiar para activar la señal.
        
    Retorna:
        bool: True si detectó el cambio, False si llegó al timeout.
    """
    inicio = time.time()
    
    # Tomamos la imagen base de comparación
    frame_base = capturar_pantalla()
    if frame_base is None:
        return False
        
    # Convertimos a grises y difuminamos (Blur) agresivamente.
    # El Blur evita que el ruido del sensor o el parpadeo de sub-píxeles
    # detonen falsos positivos.
    frame_base_gray = cv2.cvtColor(frame_base, cv2.COLOR_BGR2GRAY)
    frame_base_blur = cv2.GaussianBlur(frame_base_gray, (21, 21), 0)
    
    # Bucle de monitoreo activo
    while time.time() - inicio < timeout_segundos:
        time.sleep(0.05)  # Chequea a ~20 FPS. Rápido pero no abusa del hilo.
        
        frame_actual = capturar_pantalla()
        if frame_actual is None:
            continue
            
        gray = cv2.cvtColor(frame_actual, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (21, 21), 0)
        
        # Calculamos la diferencia absoluta entre el frame actual y el frame base
        diff = cv2.absdiff(frame_base_blur, blur)
        
        # Binarizamos: si la diferencia es mayor a la 'sensibilidad', es un píxel blanco (255)
        _, thresh = cv2.threshold(diff, sensibilidad, 255, cv2.THRESH_BINARY)
        
        # Contamos cuántos píxeles cambiaron realmente
        cambios = cv2.countNonZero(thresh)
        
        # Si el bloque de cambios supera nuestro umbral masivo, hubo un cambio de UI real
        if cambios > umbral_pixeles:
            return True
            
    # Timeout alcanzado
    return False

# ═════════════════════════════════════════════════════════════════════════════
# PRUEBAS UNITARIAS LOCALES
# ═════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    # Este bloque solo se ejecuta si se corre este archivo directamente:
    # python vision.py
    print("Probando visión con Tesseract...")
    t0 = time.time()
    texto, img = preparar_vision_data()
    t1 = time.time()
    print(f"\nTiempo: {t1-t0:.2f}s")
    print("\n--- TEXTO DETECTADO ---")
    print(texto[:500])
    print(f"\nImagen Base64 (largo: {len(img) if img else 0})")
