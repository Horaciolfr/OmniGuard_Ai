import os
import yaml
import shutil
from pathlib import Path
from roboflow import Roboflow
from ultralytics import YOLO

def fusion_multidataset(lista_rutas, ruta_salida):
    """
    Fusiona N cantidad de datasets de YOLOv8 en un único mega-dataset sin colisión de IDs.
    """
    ruta_salida = Path(ruta_salida)
    if ruta_salida.exists():
        shutil.rmtree(ruta_salida)
        
    for split in ['train', 'valid', 'test']:
        (ruta_salida / split / 'images').mkdir(parents=True, exist_ok=True)
        (ruta_salida / split / 'labels').mkdir(parents=True, exist_ok=True)

    clases_unificadas = []
    mapas_datasets = []

    # 1. Leer todas las clases y crear el diccionario global unificado
    for ruta in lista_rutas:
        with open(f"{ruta}/data.yaml", 'r') as f:
            datos = yaml.safe_load(f)
            clases_ds = datos['names']
            
            mapa_actual = {}
            for old_id, name in enumerate(clases_ds):
                # Estandarizar a minúsculas para evitar duplicados (Ej: 'Mask' vs 'mask')
                name_std = name.lower().strip()
                if name_std not in clases_unificadas:
                    clases_unificadas.append(name_std)
                mapa_actual[old_id] = clases_unificadas.index(name_std)
            mapas_datasets.append(mapa_actual)

    # 2. Copiar y remapear cada dataset
    for idx, ruta in enumerate(lista_rutas):
        origen = Path(ruta)
        mapa = mapas_datasets[idx]
        prefijo = f"ds_{idx}"
        
        for split in ['train', 'valid', 'test']:
            img_dir = origen / split / 'images'
            lbl_dir = origen / split / 'labels'
            
            if not img_dir.exists(): continue
            
            for img_file in img_dir.glob("*.*"):
                nuevo_nombre = f"{prefijo}_{img_file.name}"
                shutil.copy(img_file, ruta_salida / split / 'images' / nuevo_nombre)
                
                lbl_file = lbl_dir / f"{img_file.stem}.txt"
                if lbl_file.exists():
                    nuevo_lbl_path = ruta_salida / split / 'labels' / f"{prefijo}_{img_file.stem}.txt"
                    with open(lbl_file, 'r') as f_in, open(nuevo_lbl_path, 'w') as f_out:
                        for line in f_in:
                            parts = line.strip().split()
                            if len(parts) > 0:
                                old_cls = int(parts[0])
                                if old_cls in mapa:
                                    parts[0] = str(mapa[old_cls])
                                    f_out.write(" ".join(parts) + "\n")

    # 3. Guardar el mega data.yaml
    nuevo_yaml = {
        'train': '../train/images',
        'val': '../valid/images',
        'test': '../test/images',
        'nc': len(clases_unificadas),
        'names': clases_unificadas
    }
    with open(ruta_salida / 'data.yaml', 'w') as f:
        yaml.dump(nuevo_yaml, f)
        
    return str(ruta_salida.absolute()), clases_unificadas

if __name__ == "__main__":
    print("=== OMNIGUARD AI: CREADOR DE MEGA-DATASET ===")
    rf = Roboflow(api_key="eW2FCKVBcWu130lj6GKr")
    
    # Lista para agregar dinámicamente cualquier proyecto de Roboflow
    # Formato: ("espacio_trabajo", "nombre_proyecto", version)
    proyectos_a_descargar = [
        ("neuros", "bigger-weapons", 2),
        ("sistema-p1bnl", "2026-e8z7a", 1),
        # --> Añade aquí cualquier otro dataset que quieras en el futuro:
        # ("tu_espacio", "tu_nuevo_proyecto", 1)
    ]
    
    rutas_descargadas = []
    
    for i, (workspace, project_name, version) in enumerate(proyectos_a_descargar):
        print(f"\nDescargando Dataset {i+1}: {project_name}...")
        try:
            proj = rf.workspace(workspace).project(project_name)
            ver = proj.version(version)
            dataset = ver.download("yolov8")
            rutas_descargadas.append(dataset.location)
        except Exception as e:
            print(f"Error descargando {project_name}: {e}")

    print("\nFusionando todos los datasets en un Mega-Dataset...")
    ruta_mega, clases = fusion_multidataset(rutas_descargadas, "./mega_dataset_omniguard")
    
    print("\n¡MEGA-DATASET CREADO CON ÉXITO! 🚀")
    print(f"Ruta: {ruta_mega}")
    print(f"Total de Clases Unificadas ({len(clases)}):")
    for id_clase, nombre in enumerate(clases):
        print(f"  - ID {id_clase}: {nombre}")

    print("\n--- 3. Iniciando Entrenamiento MEGA (Medium) ---")
    # Utilizamos yolov8m.pt (Medium) como solicitaste, entrenando por 70 épocas
    model = YOLO("yolov8m.pt") 

    model.train(
        data=os.path.join(ruta_mega, "data.yaml"), 
        epochs=70, 
        imgsz=640,     
        batch=-1,      
        fraction=0.75, 
        workers=8,     
        device=0       
    )
