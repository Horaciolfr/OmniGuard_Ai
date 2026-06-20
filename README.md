# OmniGuard AI

**Arquitectura Edge Computing para Seguridad Perimetral con Detección Convolucional (YOLOv8) y Auditoría Automática (LLM Local)**

OmniGuard AI es un sistema de seguridad avanzado que se ejecuta 100% de manera local (Edge Computing). Combina visión computacional de alta velocidad con un modelo de lenguaje grande (LLM) para detectar amenazas físicas y generar reportes periciales al instante, sin depender de internet ni de la nube.

## Características Principales

* **Visión Convolucional (YOLOv8):** Identificación de armas, rostros cubiertos y comportamientos sospechosos a ~30 FPS en tiempo real.
* **Auditoría Forense IA:** Integración con LLaMA-3 (vía Ollama) que actúa como un perito, redactando resúmenes de eventos y asignando niveles de contingencia táctica (DEFCON) en menos de 5 segundos.
* **Privacidad Total (Zero-Knowledge):** Al ejecutarse localmente, no se filtran datos biométricos a servidores de terceros, garantizando privacidad absoluta y nula latencia de red.
* **Dashboard Reactivo:** Una interfaz web táctica e interactiva (construida con FastAPI y JS Vanilla) que permite el monitoreo dual de múltiples cámaras simultáneas.

## Requisitos Previos

* Docker y Docker Compose instalados en el sistema.
* Ollama (para la IA de texto) y el modelo LLaMA-3 o Phi-3 pre-descargado localmente.
* Una cámara web física o cámara virtual (OBS/DroidCam) conectada.

## Despliegue Rápido

Este proyecto está completamente dockerizado para garantizar la reproducibilidad en cualquier entorno.

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/Horaciolfr/OmniGuard_Ai.git
   cd OmniGuard_Ai
   ```

2. **Levantar los servicios:**
   ```bash
   docker-compose up --build -d
   ```

3. **Acceder al Panel de Control:**
   Abre un navegador web e ingresa a:
   ```text
   http://localhost:8000
   ```

## Estructura del Código

* `backend/app/main.py`: Punto de entrada del servidor FastAPI y rutas del dashboard.
* `backend/app/services/video_stream.py`: Motor central de inferencia YOLOv8 y gestión de la cola de eventos asíncrona.
* `docker-compose.yml`: Orquestación del contenedor.

## Agradecimientos y Referencias
Desarrollado como proyecto de investigación académica. Utiliza tecnologías Open Source como OpenCV, Ultralytics YOLO y Ollama.
