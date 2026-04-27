import os
import json
import torch
from torch.utils.data import Dataset, DataLoader
import torch.nn as nn
import torch.optim as optim
from cnn_vision import VisionEncoder
from neural_agent import AshlyNeuralNet

class ImitationDataset(Dataset):
    """
    Dataset que carga las experiencias grabadas por user_tracker.py
    y procesa las imágenes al vuelo usando la CNN.
    """
    def __init__(self, dataset_dir="training_data_full"):
        self.data = []
        self.encoder = VisionEncoder()
        
        print(f"[*] Cargando experiencias de {dataset_dir}...")
        if not os.path.exists(dataset_dir):
            return
            
        for file in os.listdir(dataset_dir):
            if file.endswith(".json"):
                with open(os.path.join(dataset_dir, file), "r") as f:
                    log = json.load(f)
                    for exp in log:
                        img_path = os.path.join(dataset_dir, exp["image"])
                        if os.path.exists(img_path):
                            self.data.append((exp, img_path))
                            
    def __len__(self):
        return len(self.data)
        
    def __getitem__(self, idx):
        exp, img_path = self.data[idx]
        
        # 1. Obtener Vector Visual
        vector = self.encoder.procesar_desde_archivo(img_path)
        
        # 2. Convertir Acción a tensores
        action_type = exp["action_type"]
        coords = [0.0, 0.0]
        action_id = 0
        
        if action_type == "click":
            action_id = 1
            coords = [exp["details"]["x"], exp["details"]["y"]]
        elif action_type == "keypress":
            action_id = 2
            
        return torch.tensor(vector, dtype=torch.float32), \
               torch.tensor(action_id, dtype=torch.long), \
               torch.tensor(coords, dtype=torch.float32)

def entrenar_agente(dataset_dir="dataset_memoria", epochs=15):
    """Entrena la red neuronal de Ashly para clonar el comportamiento del usuario."""
    dataset = ImitationDataset(dataset_dir)
    if len(dataset) == 0:
        print("❌ Dataset vacío. Usa 'user_tracker.py' para grabar tus acciones primero.")
        return None
        
    dataloader = DataLoader(dataset, batch_size=8, shuffle=True)
    
    model = AshlyNeuralNet()
    
    # Funciones de pérdida (Loss)
    criterion_class = nn.CrossEntropyLoss() # Para predecir si es Clic o Teclado
    criterion_coord = nn.MSELoss()          # Para predecir las coordenadas X, Y exactas
    
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    print(f"🚀 Iniciando entrenamiento por Imitación ({len(dataset)} experiencias cargadas)...")
    model.train()
    for epoch in range(epochs):
        total_loss = 0
        for vectors, action_ids, coords in dataloader:
            optimizer.zero_grad()
            
            # Forward pass
            pred_actions, pred_coords = model(vectors)
            
            # Calcular pérdidas
            loss_class = criterion_class(pred_actions, action_ids)
            
            # Solo penalizamos el error en coordenadas si la acción real era un clic (id=1)
            # Creamos una máscara para ignorar coordenadas en pulsaciones de teclado
            mask = (action_ids == 1).float().unsqueeze(1)
            loss_coord = criterion_coord(pred_coords * mask, coords * mask)
            
            # Loss total: damos más peso a acertar la coordenada (x5.0)
            loss = loss_class + (loss_coord * 5.0)
            
            # Backpropagation
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
        print(f"Epoch {epoch+1}/{epochs} | Loss Promedio: {total_loss/len(dataloader):.4f}")
        
    # Guardar pesos del modelo entrenado
    torch.save(model.state_dict(), "ashly_neural_brain.pth")
    print("\n✅ Entrenamiento finalizado. Modelo guardado como 'ashly_neural_brain.pth'")
    return model

if __name__ == "__main__":
    entrenar_agente()
