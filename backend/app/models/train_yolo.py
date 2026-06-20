import os
import yaml
import shutil
from pathlib import Path
from roboflow import Roboflow
from ultralytics import YOLO

def unificar_datasets(ruta_ds1, ruta_ds2, ruta_salida):
    """
    Fusiona dos datasets YOLOv8 mapeando correctamente las clases para evitar colisiones 
    (ej: que el ID 0 de armas no sobreescriba el ID 0 de capuchas).
    """
    ruta_salida = Path(ruta_salida)
    if ruta_salida.exists():
        shutil.rmtree(ruta_salida)
        
    for split in ['train', 'valid', 'test']:
        (ruta_salida / split / 'images').mkdir(parents=True, exist_ok=True)
        (ruta_salida / split / 'labels').mkdir(parents=True, exist_ok=True)

    # Cargar los data.yaml originales
    with open(f"{ruta_ds1}/data.yaml", 'r') as f:
        yaml1 = yaml.safe_load(f)
    with open(f"{ruta_ds2}/data.yaml", 'r') as f:
        yaml2 = yaml.safe_load(f)

    # Crear lista de clases unificada
    clases_ds1 = yaml1['names']
    clases_ds2 = yaml2['names']
    clases_unificadas = []
    
    # Mapeos de índices viejos a nuevos
    map1 = {}
    for old_id, name in enumerate(clases_ds1):
        if name not in clases_unificadas:
            clases_unificadas.append(name)
        map1[old_id] = clases_unificadas.index(name)

    map2 = {}
    for old_id, name in enumerate(clases_ds2):
        if name not in clases_unificadas:
            clases_unificadas.append(name)
        map2[old_id] = clases_unificadas.index(name)

    # Función para copiar imágenes y rempear labels
    def procesar_split(ruta_origen, mapa, prefijo=""):
        origen = Path(ruta_origen)
        for split in ['train', 'valid', 'test']:
            img_dir = origen / split / 'images'
            lbl_dir = origen / split / 'labels'
            
            if not img_dir.exists(): continue
            
            for img_file in img_dir.glob("*.*"):
                # Copiar imagen con prefijo para evitar que se pisen nombres iguales
                nuevo_nombre = f"{prefijo}_{img_file.name}"
                shutil.copy(img_file, ruta_salida / split / 'images' / nuevo_nombre)
                
                # Procesar label rempeando IDs
                lbl_file = lbl_dir / f"{img_file.stem}.txt"
                if lbl_file.exists():
                    nuevo_lbl_path = ruta_salida / split / 'labels' / f"{prefijo}_{img_file.stem}.txt"
                    with open(lbl_file, 'r') as f_in, open(nuevo_lbl_path, 'w') as f_out:
                        for line in f_in:
                            parts = line.strip().split()
                            if len(parts) > 0:
                                old_cls = int(parts[0])
                                # Si el ID viejo existe en el mapa, actualizarlo
                                if old_cls in mapa:
                                    new_cls = mapa[old_cls]
                                    parts[0] = str(new_cls)
                                    f_out.write(" ".join(parts) + "\n")

    procesar_split(ruta_ds1, map1, prefijo="ds1")
    procesar_split(ruta_ds2, map2, prefijo="ds2")

    # Guardar nuevo data.yaml maestro
    nuevo_yaml = {
        'train': '../train/images',
        'val': '../valid/images',
        'test': '../test/images',
        'nc': len(clases_unificadas),
        'names': clases_unificadas
    }
    with open(ruta_salida / 'data.yaml', 'w') as f:
        yaml.dump(nuevo_yaml, f)
        
    return str(ruta_salida.absolute())

if __name__ == "__main__":
    print("--- 1. Descargando Datasets desde Roboflow ---")
    rf = Roboflow(api_key="eW2FCKVBcWu130lj6GKr")
    
    # Dataset 1: Armas
    print(">>> Descargando: BIGGER WEAPONS")
    project1 = rf.workspace("neuros").project("bigger-weapons")
    version1 = project1.version(2)
    dataset1 = version1.download("yolov8")
    
    # Dataset 2: Ocultamiento
    print(">>> Descargando: 2026 (Capuchas/Lentes)")
    project2 = rf.workspace("sistema-p1bnl").project("2026-e8z7a")
    version2 = project2.version(1)
    dataset2 = version2.download("yolov8")

    print("\n--- 2. Fusionando y Mapeando Clases Automáticamente ---")
    # Une los dos datasets en uno solo llamado 'dataset_maestro'
    ruta_unificada = unificar_datasets(dataset1.location, dataset2.location, "dataset_maestro")
    print(f"Dataset fusionado listo en: {ruta_unificada}")

    print("\n--- 3. Iniciando Entrenamiento (Fine-Tuning) ---")
    # Ruta de tu cerebro actual
    model_path = os.path.join(os.path.dirname(__file__), "best.pt")
    try:
        model = YOLO(model_path)
    except Exception as e:
        print(f"No se encontro best.pt, iniciando desde cero: {e}")
        model = YOLO("yolov8n.pt") 

    # Entrenamiento a máxima potencia restringiendo la VRAM a 6GB
    model.train(
        data=os.path.join(ruta_unificada, "data.yaml"), 
        epochs=30, 
        imgsz=640,     
        batch=-1,      
        fraction=0.75, # Limita AutoBatch al 75% de los 8GB de VRAM = 6GB exactos
        workers=8,     
        device=0       
    )
