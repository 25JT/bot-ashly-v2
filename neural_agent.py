import torch
import torch.nn as nn

class AshlyNeuralNet(nn.Module):
    """
    Red Neuronal de Decisión (Actor).
    Toma el vector visual de 576 dimensiones (MobileNetV3) y decide la próxima acción.
    """
    def __init__(self, input_dim=576, num_actions=3):
        # num_actions: 0=Ninguna, 1=Click, 2=Escribir/Teclado
        super(AshlyNeuralNet, self).__init__()
        
        # Capas ocultas principales (Multilayer Perceptron)
        self.fc1 = nn.Linear(input_dim, 256)
        self.relu1 = nn.ReLU()
        self.dropout = nn.Dropout(0.2)
        self.fc2 = nn.Linear(256, 128)
        self.relu2 = nn.ReLU()
        
        # Cabeza 1: Predicción de Tipo de Acción (Clasificación)
        # Salida: Logits para num_actions
        self.action_head = nn.Linear(128, num_actions)
        
        # Cabeza 2: Predicción de Coordenadas X, Y (Regresión)
        # Salida: 2 valores entre 0.0 y 1.0 (gracias a Sigmoid)
        self.coord_head = nn.Sequential(
            nn.Linear(128, 2),
            nn.Sigmoid()
        )
        
    def forward(self, x):
        # Pasar por las capas comunes
        x = self.fc1(x)
        x = self.relu1(x)
        x = self.dropout(x)
        x = self.fc2(x)
        x = self.relu2(x)
        
        # Bifurcación a las dos cabezas
        action_logits = self.action_head(x)
        coords = self.coord_head(x)
        
        return action_logits, coords

    def predecir_accion(self, visual_vector):
        """Método de inferencia rápida para usar en producción."""
        self.eval() # Modo inferencia
        with torch.no_grad():
            tensor_input = torch.tensor(visual_vector, dtype=torch.float32).unsqueeze(0)
            action_logits, coords = self.forward(tensor_input)
            
            # Obtener el ID de la acción más probable
            action_id = torch.argmax(action_logits, dim=1).item()
            x, y = coords.squeeze(0).tolist()
            
            return action_id, x, y
