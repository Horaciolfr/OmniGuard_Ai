import torch
import timm
from transformers import ViTImageProcessor, ViTModel
from PIL import Image
import io

class VisionService:
    def __init__(self):
        # Cargamos el modelo CNN para detección de atributos
        self.cnn_model = timm.create_model('efficientnet_b0', pretrained=True)
        self.cnn_model.eval()
        
        # Cargamos Vision Transformer para extraer embeddings faciales
        self.vit_processor = ViTImageProcessor.from_pretrained('google/vit-base-patch16-224')
        self.vit_model = ViTModel.from_pretrained('google/vit-base-patch16-224')
        self.vit_model.eval()
        
    def analizar_imagen(self, image_bytes: bytes):
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        # 1. Detección de atributos con CNN
        # En un caso real, el modelo CNN estaría entrenado para detectar "capucha" o "gafas".
        # Aquí simularemos la detección usando inferencia estándar de forma demostrativa.
        with torch.no_grad():
            # Simulación de extracción de atributos (aquí iría el preprocesado de timm)
            atributos = {
                "capucha": False,
                "gafas": False
            }
            
        # 2. Extracción de embeddings faciales con ViT
        inputs = self.vit_processor(images=image, return_tensors="pt")
        with torch.no_grad():
            outputs = self.vit_model(**inputs)
            # El pooler_output representa el embedding global de la imagen (tamaño 768)
            embedding = outputs.pooler_output.numpy()[0] 
            
        return atributos, embedding
