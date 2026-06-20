import os
import shutil
import yaml
from roboflow import Roboflow

API_KEY = "eW2FCKVBcWu130lj6GKr"
DATASETS = [
    {"workspace": "work1-7vtdf", "project": "face-mask-detection-4lelp", "version": 2},
    {"workspace": "lostfound-jy7qx", "project": "sunglasses-vw1em", "version": 1},
    {"workspace": "gruppefuenf", "project": "smartphone-detection-c7e6g", "version": 1},
    {"workspace": "fgde", "project": "cell-phone-jasde", "version": 1},
    {"workspace": "face-mask-detection-v7lf1", "project": "thief-detection-6hqgl", "version": 2},
    {"workspace": "ai-izzuf", "project": "object-detection-mo4fq", "version": 1},
    {"workspace": "atmsecurity-uhtjj", "project": "atm-security-system-new", "version": 7}
]

TRANSLATION_DICT = {
    "mask": "barbijo", "no-mask": "sin_barbijo", "without_mask": "sin_barbijo", "with_mask": "barbijo",
    "sunglasses": "lentes_oscuros", "glasses": "lentes",
    "smartphone": "telefono", "cell phone": "telefono", "cell-phone": "telefono", "phone": "telefono",
    "gun_holder": "persona_armada", "gun": "arma", "pistol": "arma", "weapon": "arma", "firearm": "arma",
    "helmet_wearer": "persona_con_casco", "helmet": "casco",
    "jacket_wearer": "persona_con_chaqueta", "jacket": "chaqueta", "hoodie": "capucha",
    "person": "persona", "thief": "ladron", "robber": "ladron",
    "backpack": "mochila", "bag": "bolso", "knife": "cuchillo",
    "face": "rostro", "head": "cabeza", "body": "cuerpo"
}

def translate_class(cls_name):
    cls_lower = cls_name.lower().strip()
    return TRANSLATION_DICT.get(cls_lower, cls_lower)

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    downloads_dir = os.path.join(base_dir, "downloads")
    merged_dir = os.path.join(base_dir, "dataset_unificado")
    
    os.makedirs(downloads_dir, exist_ok=True)
    os.makedirs(merged_dir, exist_ok=True)
    
    for split in ["train", "valid", "test"]:
        os.makedirs(os.path.join(merged_dir, split, "images"), exist_ok=True)
        os.makedirs(os.path.join(merged_dir, split, "labels"), exist_ok=True)

    print("Conectando con Roboflow...")
    rf = Roboflow(api_key=API_KEY)
    
    unified_classes = []
    
    for ds_info in DATASETS:
        proj_name = ds_info["project"]
        print(f"\n--- Procesando {proj_name} ---")
        try:
            project = rf.workspace(ds_info["workspace"]).project(proj_name)
            version = project.version(ds_info["version"])
            dataset = version.download("yolov8", location=os.path.join(downloads_dir, proj_name))
            
            yaml_path = os.path.join(dataset.location, "data.yaml")
            if not os.path.exists(yaml_path):
                print(f"Error: data.yaml no encontrado en {dataset.location}")
                continue
                
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                
            original_classes = data.get("names", [])
            if isinstance(original_classes, dict):
                original_classes = [original_classes[k] for k in sorted(original_classes.keys())]
                
            class_map = {}
            for i, cls_name in enumerate(original_classes):
                es_name = translate_class(cls_name)
                if es_name not in unified_classes:
                    unified_classes.append(es_name)
                class_map[i] = unified_classes.index(es_name)
                
            print(f"Mapeo de clases ({proj_name}):")
            for i, cls_name in enumerate(original_classes):
                print(f"  {cls_name} -> {unified_classes[class_map[i]]}")
                
            # Mover y remapear labels
            for split in ["train", "valid", "test"]:
                split_img_dir = os.path.join(dataset.location, split, "images")
                split_lbl_dir = os.path.join(dataset.location, split, "labels")
                
                if not os.path.exists(split_img_dir):
                    continue
                    
                for img_file in os.listdir(split_img_dir):
                    if not img_file.endswith(('.jpg', '.jpeg', '.png')): continue
                    
                    base_name = os.path.splitext(img_file)[0]
                    lbl_file = base_name + ".txt"
                    
                    new_img_name = f"{proj_name}_{img_file}"
                    new_lbl_name = f"{proj_name}_{lbl_file}"
                    
                    # Copiar imagen
                    shutil.copy(
                        os.path.join(split_img_dir, img_file),
                        os.path.join(merged_dir, split, "images", new_img_name)
                    )
                    
                    # Procesar label
                    orig_lbl_path = os.path.join(split_lbl_dir, lbl_file)
                    new_lbl_path = os.path.join(merged_dir, split, "labels", new_lbl_name)
                    
                    if os.path.exists(orig_lbl_path):
                        with open(orig_lbl_path, 'r', encoding='utf-8') as f_in, open(new_lbl_path, 'w', encoding='utf-8') as f_out:
                            for line in f_in:
                                parts = line.strip().split()
                                if len(parts) >= 5:
                                    old_id = int(parts[0])
                                    if old_id in class_map:
                                        new_id = class_map[old_id]
                                        new_line = f"{new_id} " + " ".join(parts[1:]) + "\n"
                                        f_out.write(new_line)
                                        
        except Exception as e:
            print(f"Ocurrió un error con {proj_name}: {str(e)}")

    # Crear data.yaml unificado
    yaml_content = {
        "train": "train/images",
        "val": "valid/images",
        "test": "test/images",
        "nc": len(unified_classes),
        "names": unified_classes
    }
    
    with open(os.path.join(merged_dir, "data.yaml"), 'w', encoding='utf-8') as f:
        yaml.dump(yaml_content, f, default_flow_style=False)
        
    print("\n==============================================")
    print("¡FUSIÓN COMPLETADA EXITOSAMENTE!")
    print(f"Dataset maestro guardado en: {merged_dir}")
    print(f"Clases traducidas y unificadas ({len(unified_classes)}): {unified_classes}")
    print("==============================================")

if __name__ == "__main__":
    main()
