import os
import json
import time
import threading
from pynput import mouse, keyboard
import vision
import cv2

DATASET_DIR = "training_data_full"
if not os.path.exists(DATASET_DIR):
    os.makedirs(DATASET_DIR)

current_goal = ""
session_id = int(time.time())
action_log = []
last_frame = None
is_recording = False

def save_experience(action_type, details):
    global last_frame
    if last_frame is None or not is_recording:
        return
    
    timestamp = int(time.time() * 1000)
    image_filename = f"frame_{session_id}_{timestamp}.jpg"
    image_path = os.path.join(DATASET_DIR, image_filename)
    
    # Asegurar que el frame esté en BGR para cv2
    frame_to_save = last_frame
    if len(frame_to_save.shape) == 3 and frame_to_save.shape[2] == 4:
        frame_to_save = cv2.cvtColor(frame_to_save, cv2.COLOR_BGRA2BGR)
        
    # Redimensionar la imagen a algo manejable para la CNN (ej: 640x360) para ahorrar espacio
    h, w = frame_to_save.shape[:2]
    new_w = 1280
    new_h = int(new_w * h / w)
    resized = cv2.resize(frame_to_save, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    cv2.imwrite(image_path, resized, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    
    experience = {
        "timestamp": timestamp,
        "goal": current_goal,
        "image": image_filename,
        "action_type": action_type,
        "details": details
    }
    action_log.append(experience)
    
    with open(os.path.join(DATASET_DIR, f"log_{session_id}.json"), "w") as f:
        json.dump(action_log, f, indent=4)
        
    print(f"[*] Experiencia guardada: {action_type} - {details}")

def on_click(x, y, button, pressed):
    if pressed and is_recording:
        # Obtener resolución real dinámicamente para máxima precisión
        import ctypes
        user32 = ctypes.windll.user32
        sw, sh = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        
        nx = x / float(sw)
        ny = y / float(sh)
        details = {"x": nx, "y": ny, "button": str(button)}
        save_experience("click", details)

def on_press(key):
    global is_recording
    if not is_recording:
        return
        
    if key == keyboard.Key.esc:
        print("\n[!] Deteniendo la grabación (ESC presionado)...")
        is_recording = False
        return False
        
    try:
        details = {"key": key.char}
    except AttributeError:
        details = {"key": str(key)}
    
    save_experience("keypress", details)

def vision_loop():
    global last_frame, is_recording
    while is_recording:
        frame = vision.capturar_pantalla()
        if frame is not None:
            last_frame = frame
        time.sleep(0.1)  # Actualiza el frame a ~10 FPS

def iniciar_rastreador(objetivo="Usar Spotify"):
    global current_goal, is_recording, session_id
    current_goal = objetivo
    is_recording = True
    session_id = int(time.time())
    
    print("="*50)
    print(f"🎥 INICIANDO CLONACIÓN DE COMPORTAMIENTO")
    print(f"Objetivo actual: {objetivo}")
    print("El sistema grabará tus clics y teclas y las relacionará con lo que se ve en pantalla.")
    print("🔴 PRESIONA 'ESC' PARA DETENER LA GRABACIÓN.")
    print("="*50)
    
    threading.Thread(target=vision_loop, daemon=True).start()
    
    # Listeners no-bloqueantes
    mouse_listener = mouse.Listener(on_click=on_click)
    keyboard_listener = keyboard.Listener(on_press=on_press)
    
    mouse_listener.start()
    keyboard_listener.start()
    
    while is_recording:
        time.sleep(1)
        
    mouse_listener.stop()
    print(f"\n✅ Grabación finalizada. Dataset guardado en la carpeta '{DATASET_DIR}'.")

if __name__ == "__main__":
    iniciar_rastreador("cambiar estilo de canciones dj livi o Dj")
