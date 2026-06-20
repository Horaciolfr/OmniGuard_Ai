import cv2
import time
from datetime import datetime
from ultralytics import YOLO
import os

# 1. Cargar el modelo entrenado personalizado
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "best.pt")
try:
    yolo_model = YOLO(MODEL_PATH)
    print("Modelo personalizado cargado con exito.")
except Exception:
    yolo_model = YOLO("yolov8n.pt")
    
# 1.5 Cargar el modelo base COCO de YOLOv8 para enriquecer el entorno
yolo_coco = YOLO("yolov8n.pt")

# ==========================================
# Variable Global de Logs
# ==========================================
registro_eventos = []
ultimo_tiempo_alerta = {}

def clasificar_gravedad_y_log(detecciones, cam_id=""):
    """
    3. Poblar logs: Evalúa el nivel de riesgo de los objetos y hace insert(0) 
    para que la interfaz consuma los eventos más recientes de /api/logs
    """
    global registro_eventos
    
    if "Arma" in detecciones:
        gravedad, color = "CRITICO", "#ef4444" # Rojo
    elif "Capucha" in detecciones or "Lentes Oscuros" in detecciones or "Barbijo" in detecciones:
        gravedad, color = "AMARILLO", "#eab308" # Naranja/Amarillo
    else:
        gravedad, color = "VERDE", "#22c55e" # Verde
        
    cam_str = f"Cam {cam_id} - " if str(cam_id) != "" else ""
    evento = {
        "hora": datetime.now().strftime("%H:%M:%S"),
        "descripcion": f"{cam_str}Detectado: {', '.join(detecciones)}",
        "gravedad": gravedad,
        "color": color
    }
    
    registro_eventos.insert(0, evento)
    if len(registro_eventos) > 50:
        registro_eventos.pop()

# ==========================================
# Función Generadora de Video (Stream Yield)
# ==========================================
def generar_frames(source=0):
    global ultimo_tiempo_alerta
    
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        return
        
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0: fps = 30
    delay = 1.0 / fps
    
    while True:
        start_time = time.time()
        success, frame = cap.read()
        
        if not success:
            if isinstance(source, str):
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # Repetir en bucle si es video local
                continue
            else:
                break
                
        # 1. Inferencia del modelo personalizado (Sensibilidad equilibrada conf=0.30)
        resultados_custom = yolo_model(frame, conf=0.30, verbose=False)
        # 1.5 Inferencia del modelo COCO (Sensibilidad equilibrada conf=0.30)
        resultados_coco = yolo_coco(frame, conf=0.30, verbose=False)
        
        detecciones_actuales = []
        
        # Helper interno para dibujar cajas
        def procesar_resultados(resultados, modelo, es_coco=False):
            if len(resultados) > 0 and resultados[0].boxes:
                for box in resultados[0].boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cls_id = int(box.cls[0])
                    confianza = float(box.conf[0])
                    
                    nombre_original = modelo.names[cls_id].lower()
                    
                    # Si es COCO y detecta persona, lo ignoramos porque el custom ya lo hace mejor
                    if es_coco and nombre_original in ["person", "human"]:
                        continue
                        
                    traducciones = {
                        "mask": "Barbijo", "face_mask": "Barbijo", "person-with-mask": "Barbijo",
                        "sunglasses": "Lentes Oscuros", "pex5 - v4 2023-12-05 8-35pm": "Lentes Oscuros",
                        "hoodie": "Capucha", "persona_con_chaqueta": "Capucha",
                        "hat": "Gorra", "cap": "Gorra",
                        "person": "Persona", "human": "Persona",
                        "weapon": "Arma", "gun": "Arma", "persona_armada": "Arma",
                        # Agregamos traducciones COCO comunes
                        "cell phone": "Celular", "backpack": "Mochila", "car": "Auto",
                        "motorcycle": "Moto", "laptop": "Laptop", "knife": "Cuchillo",
                        "handbag": "Bolso", "suitcase": "Maleta"
                    }
                    nombre_espanol = traducciones.get(nombre_original, nombre_original.capitalize())
                    detecciones_actuales.append(nombre_espanol)
                    
                    # Color azul para COCO, Verde para Custom (para diferenciarlos)
                    color_caja = (255, 100, 0) if es_coco else (0, 255, 0)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color_caja, 2)
                    texto = f"{nombre_espanol} {confianza:.2f}"
                    cv2.putText(frame, texto, (x1, max(y1 - 10, 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_caja, 2)

        # 2. Procesar y dibujar ambos resultados
        procesar_resultados(resultados_custom, yolo_model, es_coco=False)
        procesar_resultados(resultados_coco, yolo_coco, es_coco=True)

        # Poblar Logs cada 1.5s
        if source not in ultimo_tiempo_alerta:
            ultimo_tiempo_alerta[source] = 0
            
        tiempo_actual = time.time()
        if detecciones_actuales and (tiempo_actual - ultimo_tiempo_alerta[source] > 1.5):
            detecciones_unicas = list(set(detecciones_actuales))
            # Ignoramos logs si la única detección es "Persona" para no inundar el panel de verde inútil
            if any(d != "Persona" for d in detecciones_unicas):
                clasificar_gravedad_y_log(detecciones_unicas, cam_id=source)
                ultimo_tiempo_alerta[source] = tiempo_actual

        # Preparar y codificar frame para FastAPI
        ret, buffer = cv2.imencode('.jpg', frame)
        if ret:
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            
        # Controlar FPS del stream
        if isinstance(source, str):
            elapsed = time.time() - start_time
            if elapsed < delay:
                time.sleep(delay - elapsed)
                
    cap.release()

def analizar_imagen_estatica(file_path):
    """Analiza una sola imagen y devuelve sus bytes en jpeg."""
    frame = cv2.imread(file_path)
    if frame is None:
        return None
        
    resultados_custom = yolo_model(frame, conf=0.30, verbose=False)
    resultados_coco = yolo_coco(frame, conf=0.30, verbose=False)
    
    def procesar_resultados(resultados, modelo, es_coco=False):
        if len(resultados) > 0 and resultados[0].boxes:
            for box in resultados[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cls_id = int(box.cls[0])
                confianza = float(box.conf[0])
                nombre_original = modelo.names[cls_id].lower()
                if es_coco and nombre_original in ["person", "human"]:
                    continue
                color_caja = (255, 100, 0) if es_coco else (0, 255, 0)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color_caja, 2)
                cv2.putText(frame, f"{nombre_original} {confianza:.2f}", (x1, max(y1 - 10, 10)), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_caja, 2)
                            
    procesar_resultados(resultados_custom, yolo_model, es_coco=False)
    procesar_resultados(resultados_coco, yolo_coco, es_coco=True)
    
    ret, buffer = cv2.imencode('.jpg', frame)
    return buffer.tobytes()
