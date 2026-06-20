import faiss
import numpy as np

class FAISSService:
    def __init__(self, dimension=768):
        # Índice FlatL2 para calcular la distancia euclidiana L2
        self.index = faiss.IndexFlatL2(dimension)
        
        # Base de datos simulada (ej. vectores de personas "riesgosas" conocidas)
        np.random.seed(42)
        # Añadimos 5 vectores aleatorios a nuestro índice
        dummy_data = np.random.rand(5, dimension).astype('float32')
        self.index.add(dummy_data)
        
    def verificar_riesgo(self, embedding_vector: np.ndarray):
        # Aseguramos que la forma sea (1, 768)
        vector_2d = np.expand_dims(embedding_vector, axis=0).astype('float32')
        
        # Buscamos la coincidencia más cercana (k=1)
        distances, indices = self.index.search(vector_2d, 1)
        
        min_distance = distances[0][0]
        
        # Lógica heurística simulada para la probabilidad de riesgo
        # Mientras menor es la distancia, mayor probabilidad de coincidencia
        if min_distance < 10.0:
            probabilidad_riesgo = 0.95
            nivel = "Rojo"
        elif min_distance < 20.0:
            probabilidad_riesgo = 0.50
            nivel = "Amarillo"
        else:
            probabilidad_riesgo = 0.10
            nivel = "Verde"
            
        return {
            "distancia_minima": float(min_distance),
            "probabilidad_riesgo": float(probabilidad_riesgo),
            "nivel_alerta": nivel
        }
