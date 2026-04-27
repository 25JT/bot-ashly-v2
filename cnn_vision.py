import torch
import torchvision.models as models
import torchvision.transforms as transforms
import cv2
import numpy as np
import os

class VisionEncoder:
    def __init__(self):
        print("[*] Cargando modelo CNN (MobileNetV3 Small) optimizado para CPU...")
        # Cargar MobileNetV3 pre-entrenada
        self.model = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)
        # Al reemplazar el classifier con Identity, nos devuelve el vector de características de 576 dimensiones
        self.model.classifier = torch.nn.Identity()
        self.model.eval() # Modo evaluación (no entrenamos esta red, solo la usamos para extraer características)
        
        # Transformaciones requeridas por el modelo preentrenado de PyTorch
        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),  # MobileNetV3 espera 224x224
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
    def procesar_imagen_cv2(self, image_bgr):
        """Convierte un frame de cv2 (numpy array BGR) a un vector de características matemáticas (embedding)."""
        # Convertir de BGR (OpenCV) a RGB
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        
        # Aplicar transformaciones visuales
        input_tensor = self.transform(image_rgb)
        input_batch = input_tensor.unsqueeze(0) # Crear un batch de 1 (PyTorch espera batches)
        
        # Inferencia sin tracking de gradientes (más rápido)
        with torch.no_grad():
            embedding = self.model(input_batch)
            
        # Retorna un vector Numpy de 1 dimensión
        return embedding.squeeze(0).numpy()

    def procesar_desde_archivo(self, filepath):
        """Carga una imagen del disco y extrae sus características."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"No se encontró la imagen: {filepath}")
            
        img = cv2.imread(filepath)
        if img is None:
            raise ValueError(f"No se pudo leer la imagen: {filepath}")
            
        return self.procesar_imagen_cv2(img)

if __name__ == "__main__":
    # Prueba rápida del encoder visual
    print("Iniciando prueba de VisionEncoder...")
    encoder = VisionEncoder()
    
    # Crear una imagen negra (dummy) de prueba con la resolución usada en user_tracker.py
    test_img = np.zeros((360, 640, 3), dtype=np.uint8)
    
    vector = encoder.procesar_imagen_cv2(test_img)
    print(f"✅ Extracción exitosa. Forma del vector visual: {vector.shape}")
    print(f"Ejemplo de los primeros 5 valores del vector: {vector[:5]}")
