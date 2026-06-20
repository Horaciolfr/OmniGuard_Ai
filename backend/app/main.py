import os
import shutil
from fastapi import FastAPI, File, UploadFile, Query
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse, Response
from pydantic import BaseModel
import app.services.video_stream as vs

app = FastAPI(title="OmniGuard AI")

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OMNIGUARD Edge AI Engine</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Inter:wght@400;500;600&display=swap');

        :root {
            --bg-deep: #0f171e;
            --bg-panel: #15222b;
            --bg-input: #0a1116;
            --border-cyan: #1a4551;
            --border-highlight: #00e5ff;
            --text-main: #b0c4de;
            --text-cyan: #00e5ff;
            --text-red: #ff3333;
            --text-green: #00e676;
            --text-muted: #5c7585;
            --font-mono: 'Share Tech Mono', monospace;
            --font-sans: 'Inter', sans-serif;
        }

        body {
            margin: 0;
            padding: 0;
            background-color: var(--bg-deep);
            color: var(--text-main);
            font-family: var(--font-sans);
            height: 100vh;
            display: flex;
            overflow: hidden;
        }

        /* Sidebar */
        .sidebar {
            width: 260px;
            background: var(--bg-panel);
            border-right: 1px solid var(--border-cyan);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .logo-container {
            padding: 20px;
            display: flex;
            align-items: center;
            gap: 12px;
            border-bottom: 1px solid var(--border-cyan);
        }

        .logo-icon {
            width: 32px;
            height: 32px;
            background: rgba(0, 229, 255, 0.1);
            border: 1px solid var(--border-highlight);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--text-cyan);
        }

        .logo-text {
            font-family: var(--font-mono);
            font-size: 16px;
            color: white;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .logo-subtext {
            font-size: 10px;
            color: var(--text-cyan);
            letter-spacing: 0.5px;
        }

        .nav-menu {
            padding: 20px 0;
            flex-grow: 1;
        }

        .nav-item {
            padding: 14px 20px;
            display: flex;
            align-items: center;
            gap: 12px;
            color: var(--text-muted);
            font-size: 11px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            text-transform: uppercase;
            letter-spacing: 1px;
            word-wrap: break-word;
        }

        .nav-item.active {
            background: rgba(0, 229, 255, 0.05);
            color: var(--text-cyan);
            border-left: 3px solid var(--border-highlight);
        }

        .sidebar-footer {
            padding: 20px;
            border-top: 1px solid var(--border-cyan);
            font-family: var(--font-mono);
            font-size: 11px;
        }
        
        .issue-badge {
            background: var(--text-red);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            display: inline-block;
            margin-top: 8px;
        }

        /* Main Content */
        .main-content {
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            padding: 24px;
            gap: 24px;
            height: 100%;
            box-sizing: border-box;
            overflow: hidden;
        }

        /* Top Bar */
        .top-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .top-title {
            font-family: var(--font-mono);
            font-size: 14px;
            color: white;
            letter-spacing: 1px;
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .sys-tag {
            border: 1px solid var(--border-cyan);
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 10px;
            color: var(--text-cyan);
            background: rgba(0, 229, 255, 0.05);
        }

        .btn-export {
            background: rgba(0, 229, 255, 0.1);
            color: var(--text-cyan);
            border: 1px solid var(--text-cyan);
            padding: 8px 16px;
            border-radius: 4px;
            font-family: var(--font-mono);
            font-size: 12px;
            cursor: pointer;
            transition: 0.2s;
            text-transform: uppercase;
        }
        .btn-export:hover {
            background: var(--text-cyan);
            color: black;
        }

        /* Middle Grid Layout */
        .content-grid {
            display: grid;
            grid-template-columns: 1fr 380px;
            gap: 24px;
            flex-grow: 1;
            min-height: 0;
        }

        /* Left Column (Video + Status) */
        .left-col {
            display: flex;
            flex-direction: column;
            gap: 24px;
            min-height: 0;
        }

        /* Video Container */
        .video-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 12px;
            flex-grow: 1;
            min-height: 0;
        }

        .video-wrapper {
            background: black;
            border: 1px solid var(--border-cyan);
            border-radius: 8px;
            position: relative;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 0;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .video-wrapper.fullscreen {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            z-index: 9999;
            border-radius: 0;
            border: none;
        }
        
        .video-wrapper.fullscreen img {
            object-fit: contain;
        }
        
        .video-wrapper img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            opacity: 0.8;
            filter: grayscale(40%) contrast(1.1);
        }

        .video-overlay {
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background-image: 
                linear-gradient(rgba(0, 229, 255, 0.1) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0, 229, 255, 0.1) 1px, transparent 1px);
            background-size: 33.33% 33.33%;
            pointer-events: none;
        }

        .live-badge {
            position: absolute;
            top: 12px;
            left: 12px;
            background: rgba(10, 17, 22, 0.85);
            border: 1px solid var(--border-cyan);
            padding: 6px 12px;
            border-radius: 4px;
            display: flex;
            gap: 12px;
            font-family: var(--font-mono);
            font-size: 11px;
            color: white;
            z-index: 10;
        }
        
        .rec-dot { color: var(--text-red); font-weight: bold; }
        .fps-txt { color: var(--text-green); }

        .cam-info-bottom {
            position: absolute;
            bottom: 12px;
            left: 12px;
            background: rgba(10, 17, 22, 0.85);
            border: 1px solid var(--border-cyan);
            padding: 8px 12px;
            border-radius: 6px;
            font-family: var(--font-mono);
            font-size: 10px;
            color: var(--text-cyan);
            max-width: 45%;
            word-wrap: break-word;
            z-index: 10;
        }

        .model-info-bottom {
            position: absolute;
            bottom: 12px;
            right: 12px;
            background: rgba(10, 17, 22, 0.85);
            border: 1px solid rgba(255,255,255,0.1);
            padding: 8px 12px;
            border-radius: 6px;
            text-align: right;
            font-family: var(--font-mono);
            font-size: 10px;
            color: var(--text-muted);
            max-width: 45%;
            word-wrap: break-word;
            z-index: 10;
        }

        /* Bottom Status Area */
        .bottom-status-area {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
            height: 140px;
            flex-shrink: 0;
        }

        .panel-box {
            background: var(--bg-panel);
            border: 1px solid var(--border-cyan);
            border-radius: 8px;
            padding: 20px;
            display: flex;
            flex-direction: column;
        }

        .panel-title {
            font-family: var(--font-mono);
            font-size: 12px;
            color: white;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 16px;
        }

        .defcon-display {
            display: flex;
            align-items: center;
            gap: 20px;
        }

        .shield-icon {
            width: 40px;
            height: 40px;
            border: 1px solid var(--text-green);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--text-green);
            font-size: 20px;
            background: rgba(0, 230, 118, 0.1);
        }

        .defcon-text h2 {
            margin: 0;
            color: var(--text-green);
            font-size: 24px;
            letter-spacing: 1px;
        }
        
        .defcon-text p {
            margin: 4px 0 0 0;
            font-size: 12px;
            color: var(--text-main);
        }

        .health-list {
            list-style: none;
            padding: 0;
            margin: 0;
            font-size: 11px;
            font-family: var(--font-mono);
            color: var(--text-muted);
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .health-list li {
            display: flex;
            justify-content: space-between;
        }
        
        .health-list span { color: white; }

        .disclaimer-box {
            margin-top: auto;
            border: 1px solid rgba(0,229,255,0.3);
            background: rgba(0,229,255,0.05);
            color: var(--text-cyan);
            padding: 8px;
            font-size: 9px;
            font-family: var(--font-mono);
            border-radius: 4px;
            text-transform: uppercase;
        }

        /* Right Column (Timeline & Intel) */
        .right-col {
            display: flex;
            flex-direction: column;
            gap: 24px;
            min-height: 0;
        }

        /* Timeline Box */
        .timeline-box {
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            min-height: 0;
        }
        
        .timeline-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }

        .log-container {
            flex: 1;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 12px;
            padding-right: 8px;
        }
        
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: var(--border-cyan); }

        .log-card {
            border: 1px solid var(--border-cyan);
            background: rgba(0,0,0,0.3);
            border-radius: 6px;
            padding: 12px;
            position: relative;
            flex-shrink: 0;
            transition: 0.2s;
        }
        .log-card.threat { border-color: var(--text-red); }
        .log-card.artifact { border-color: var(--text-green); }

        .log-title {
            font-family: var(--font-mono);
            font-size: 12px;
            color: var(--text-cyan);
            margin-bottom: 4px;
            text-transform: uppercase;
            display: flex;
            justify-content: space-between;
        }
        .log-card.threat .log-title { color: var(--text-red); }
        
        .log-desc {
            font-size: 11px;
            color: var(--text-main);
            margin-bottom: 8px;
            font-style: italic;
        }

        .log-meta {
            display: flex;
            gap: 12px;
            font-size: 10px;
            color: var(--text-muted);
            font-family: var(--font-mono);
            background: var(--bg-input);
            padding: 4px 8px;
            border-radius: 4px;
            margin-bottom: 8px;
        }

        .tag-badge {
            display: inline-block;
            font-size: 9px;
            font-family: var(--font-mono);
            padding: 2px 8px;
            border-radius: 12px;
            text-transform: uppercase;
        }
        .tag-threat { border: 1px solid var(--text-red); color: var(--text-red); background: rgba(255,51,51,0.1); }
        .tag-artifact { border: 1px solid var(--text-green); color: var(--text-green); background: rgba(0,230,118,0.1); }

        .juez-btn {
            background: transparent;
            color: var(--text-cyan);
            border: 1px solid var(--border-cyan);
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 10px;
            font-family: var(--font-mono);
            cursor: pointer;
            width: 100%;
            margin-top: 8px;
            transition: 0.2s;
        }
        .juez-btn:hover { background: rgba(0,229,255,0.1); }

        /* Assistant Box */
        .assistant-box {
            height: 280px;
            flex-shrink: 0;
            display: flex;
            flex-direction: column;
        }

        .assistant-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            font-family: var(--font-mono);
            font-size: 12px;
        }
        .dot-active { color: var(--text-green); }

        .chat-area {
            flex-grow: 1;
            background: var(--bg-input);
            border: 1px solid var(--border-cyan);
            border-radius: 6px;
            padding: 12px;
            overflow-y: auto;
            margin-bottom: 12px;
            font-size: 12px;
            line-height: 1.5;
        }
        
        .chat-bubble {
            background: rgba(0,229,255,0.05);
            border-left: 2px solid var(--text-cyan);
            padding: 8px 12px;
            margin-bottom: 8px;
            color: var(--text-main);
        }
        .user-bubble {
            background: rgba(255,255,255,0.05);
            border-left: 2px solid var(--text-muted);
            padding: 8px 12px;
            margin-bottom: 8px;
            color: var(--text-main);
        }

        .input-area {
            display: flex;
            background: var(--bg-input);
            border: 1px solid var(--border-cyan);
            border-radius: 6px;
            padding: 8px;
        }
        
        .input-area input {
            flex-grow: 1;
            background: transparent;
            border: none;
            color: white;
            font-family: var(--font-sans);
            font-size: 12px;
            outline: none;
        }
        
        .input-area button {
            background: rgba(0,229,255,0.1);
            border: none;
            color: var(--text-cyan);
            cursor: pointer;
            padding: 4px 8px;
            border-radius: 4px;
        }

        .privacy-note {
            font-size: 9px;
            color: var(--text-muted);
            text-align: center;
            margin-top: 8px;
            font-family: var(--font-mono);
        }
    </style>
</head>
<body>

    <!-- Sidebar -->
    <div class="sidebar">
        <div>
            <div class="logo-container">
                <div class="logo-icon"></div>
                <div>
                    <div class="logo-text">OMNIGUARD</div>
                    <div class="logo-subtext">MOTOR IA DE BORDE</div>
                </div>
            </div>
            <div class="nav-menu">
                <div class="nav-item active" onclick="setLiveCamera()">PANEL DE CONTROL (EN VIVO)</div>
                <div class="nav-item" onclick="document.getElementById('fileInput').click()">ARCHIVO (SUBIR MEDIA)</div>
                <div class="nav-item" onclick="limpiarLogs()">REGISTRO DE EVIDENCIA (LIMPIAR)</div>
                <div class="nav-item" id="btnSound" onclick="toggleSound()">AJUSTES DEL SISTEMA (AUDIO: ON)</div>
                <input type="file" id="fileInput" style="display: none;" onchange="uploadAndPlay(event)" accept="image/*,video/*">
            </div>
        </div>
        <div class="sidebar-footer">
            <div style="display:flex; justify-content:space-between; color:var(--text-muted);">
                <span>LATENCIA</span>
                <span style="color:var(--text-green);">0.2MS (LOCAL)</span>
            </div>
            <div class="issue-badge">1 Alerta x</div>
        </div>
    </div>

    <!-- Main Content -->
    <div class="main-content">
        <!-- Top Bar -->
        <div class="top-bar">
            <div class="top-title">
                PANEL DE VIGILANCIA PERIMETRAL
                <span class="sys-tag">ACELERADOR DE HARDWARE: ACTIVADO</span>
                <span class="sys-tag">RED: AISLADA</span>
            </div>
            <button class="btn-export" onclick="exportReport()">DESCARGA TÁCTICA</button>
        </div>

        <div class="content-grid">
            <!-- Left Column -->
            <div class="left-col">
                <!-- Video Section -->
                <div class="video-grid" id="main-video-grid">
                    <div class="video-wrapper" onclick="toggleFullscreen(this)">
                        <img id="feed-0" src="/media_feed?type=camera&path=0" alt="Live Feed">
                        <div class="video-overlay"></div>
                        <div class="live-badge">
                            <span class="rec-dot">EN VIVO</span>
                            <span class="fps-txt">CAM 01</span>
                        </div>
                        <div class="cam-info-bottom">
                            ENTRADA PRINCIPAL SECTOR 01-A<br>
                            <span class="clock" style="color:var(--text-main);">--:--:--</span>
                        </div>
                        <div class="model-info-bottom">
                            <span style="color:white; font-weight:bold;">Motor YOLOv8 Borde</span><br>
                            HARDWARE LOCAL ACTIVO
                        </div>
                    </div>
                </div>

                <!-- Status Panels -->
                <div class="bottom-status-area">
                    <div class="panel-box">
                        <div class="panel-title">ESTADO DEL SISTEMA</div>
                        <div class="defcon-display">
                            <div class="shield-icon" id="shieldIcon"></div>
                            <div class="defcon-text">
                                <h2 id="defconLevel">DEFCON 5</h2>
                                <p>Condición: NORMAL</p>
                            </div>
                        </div>
                        <p style="font-size:11px; color:var(--text-muted); margin-top:20px; border-top:1px solid #1a3644; padding-top:10px;" id="defconMsg">
                            Entorno pacífico. Monitoreo activo.
                        </p>
                    </div>
                    
                    <div class="panel-box">
                        <div class="panel-title" style="display:flex; justify-content:space-between;">
                            SALUD DEL SISTEMA
                        </div>
                        <ul class="health-list">
                            <li>Búfer de Visión (FPS) <span>32.4</span></li>
                            <li>Carga Neuronal (GPU) <span>18%</span></li>
                            <li>Almacenamiento (Local) <span>4.2 GB usados</span></li>
                        </ul>
                        <div class="disclaimer-box">
                            EL SISTEMA FILTRA AUTOMÁTICAMENTE ARTEFACTOS USANDO DISCRIMINACIÓN MATEMÁTICA LLM PARA PREVENIR FALSAS ALARMAS.
                        </div>
                    </div>
                </div>
            </div>

            <!-- Right Column -->
            <div class="right-col">
                <!-- Forensic Timeline -->
                <div class="timeline-box">
                    <div class="timeline-header">
                        <span class="panel-title" style="margin:0;">LÍNEA DE TIEMPO FORENSE</span>
                        <span style="font-family:var(--font-mono); font-size:10px; color:var(--text-muted);">BASE DE DATOS LOCAL</span>
                    </div>
                    <div class="log-container" id="logBox">
                        <!-- Logs injectados aquí -->
                    </div>
                </div>

                <!-- Intel Assistant -->
                <div class="assistant-box">
                    <div class="assistant-header">
                        <span style="color:white;">ASISTENTE DE INTELIGENCIA LOCAL</span>
                        <span class="dot-active">NÚCLEO ACTIVO</span>
                    </div>
                    
                    <div class="chat-area" id="chatResponse">
                        <div class="chat-bubble">Sistemas en línea. Soy tu Asistente de Seguridad de Borde. Puedes preguntarme sobre turnos pasados, armas detectadas o registros de cámaras específicas.</div>
                        <!-- Respuestas y Reportes aquí -->
                    </div>
                    
                    <button class="juez-btn" onclick="generarReporte()" style="margin-bottom:8px;">Generar Reporte DEFCON Automático</button>

                    <div class="input-area">
                        <input type="text" id="chatInput" placeholder="Pregunta sobre el turno de seguridad...">
                        <button onclick="enviarChat()">ENVIAR</button>
                    </div>
                    <div class="privacy-note">
                        Ningún dato sale de este dispositivo. Privacidad local total garantizada.
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let soundEnabled = true;
        const synth = window.speechSynthesis;

        function toggleFullscreen(element) {
            element.classList.toggle('fullscreen');
        }

        function setLiveCamera() {
            document.getElementById('feed-0').src = "/media_feed?type=camera&path=0";
            const camInfos = document.querySelectorAll('.cam-info-bottom');
            if (camInfos.length > 0) camInfos[0].innerHTML = `ENTRADA PRINCIPAL SECTOR 01-A<br><span class="clock" style="color:var(--text-main);">--:--:--</span>`;
        }

        async function uploadAndPlay(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            const camInfos = document.querySelectorAll('.cam-info-bottom');
            if (camInfos.length > 0) camInfos[0].innerHTML = `SISTEMA SUBIENDO...<br><span class="clock" style="color:var(--text-main);">--:--:--</span>`;

            const formData = new FormData();
            formData.append("file", file);

            try {
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                
                document.getElementById('feed-0').src = `/media_feed?type=${data.type}&path=${encodeURIComponent(data.path)}&t=${Date.now()}`;
                if (camInfos.length > 0) camInfos[0].innerHTML = `ARCHIVO: ${file.name}<br><span class="clock" style="color:var(--text-main);">--:--:--</span>`;
            } catch (error) {
                console.error("Upload error:", error);
                if (camInfos.length > 0) camInfos[0].innerHTML = `ERROR AL SUBIR<br><span class="clock" style="color:var(--text-main);">--:--:--</span>`;
            }
        }

        function toggleSound() {
            soundEnabled = !soundEnabled;
            document.getElementById('btnSound').innerText = soundEnabled ? "AJUSTES DEL SISTEMA (AUDIO: ON)" : "AJUSTES DEL SISTEMA (AUDIO: OFF)";
            document.getElementById('btnSound').style.color = soundEnabled ? "var(--text-cyan)" : "var(--text-muted)";
        }

        async function limpiarLogs() {
            document.getElementById('logBox').innerHTML = "";
            try {
                await fetch('/api/logs', { method: 'DELETE' });
            } catch (e) {
                console.error("Error limpiando logs en servidor:", e);
            }
        }

        // Reloj
        setInterval(() => {
            const dateStr = new Date().toLocaleString();
            document.querySelectorAll('.clock').forEach(el => el.innerText = dateStr);
        }, 1000);

        async function fetchLogs() {
            try {
                const response = await fetch('/api/logs');
                const data = await response.json();
                
                const logBox = document.getElementById('logBox');
                logBox.innerHTML = ""; 
                
                data.forEach(evento => {
                    const card = document.createElement('div');
                    card.className = 'log-card ' + ((evento.gravedad === 'CRITICO' || evento.gravedad === 'ALTO') ? 'threat' : 'artifact');
                    
                    let badgeClass = (evento.gravedad === 'CRITICO' || evento.gravedad === 'ALTO') ? 'tag-threat' : 'tag-artifact';
                    let badgeText = (evento.gravedad === 'CRITICO' || evento.gravedad === 'ALTO') ? 'AMENAZA LEGÍTIMA' : 'ARTEFACTO VISUAL';
                    
                    // Limpiar descripcion para quitar la palabra 'Detectado:'
                    let cleanDesc = evento.descripcion.replace('Detectado: ', '');

                    card.innerHTML = `
                        <div class="log-title">
                            <span>${cleanDesc}</span>
                            <span style="color:var(--text-muted); font-size:10px; font-weight:normal;">${evento.hora}</span>
                        </div>
                        <div class="log-desc">Anomalía detectada en búfer de video.</div>
                        <div class="log-meta">
                            <span>LOC: Entrada Principal - Cam 01</span>
                            <span>CONF: 89%</span>
                        </div>
                        <span class="tag-badge ${badgeClass}">${badgeText}</span>
                        ${(evento.gravedad === 'CRITICO' || evento.gravedad === 'ALTO') ? 
                            `<button class="juez-btn" onclick="juzgarAlarma('${evento.hora}', '${evento.descripcion}')">Juez IA: Verificar Amenaza</button>` : ''}
                    `;
                    logBox.appendChild(card);
                    if (soundEnabled && (evento.gravedad === 'CRITICO' || evento.gravedad === 'ALTO') && !evento.alertado) {
                        const utterance = new SpeechSynthesisUtterance("Security alert. " + cleanDesc);
                        utterance.lang = 'en-US';
                        synth.speak(utterance);
                        evento.alertado = true;
                    }
                });
            } catch (error) {
                console.error("Error obteniendo logs:", error);
            }
        }

        async function juzgarAlarma(hora, descripcion) {
            const chatResponse = document.getElementById('chatResponse');
            chatResponse.innerHTML += `<div class="user-bubble">Verifica alarma de las ${hora}</div>`;
            chatResponse.innerHTML += `<div class="chat-bubble"><strong>IA JUEZ ANALIZANDO...</strong></div>`;
            chatResponse.scrollTop = chatResponse.scrollHeight;
            
            try {
                const res = await fetch('/api/juez', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ message: `Hora: ${hora}, Evento: ${descripcion}` })
                });
                const data = await res.json();
                chatResponse.innerHTML += `<div class="chat-bubble"><strong>VEREDICTO:</strong><br>${data.respuesta.replace(/\\n/g, '<br>')}</div>`;
                chatResponse.scrollTop = chatResponse.scrollHeight;
            } catch (e) {
                chatResponse.innerHTML += `<div class="chat-bubble" style="color:var(--text-red);">Error conectando al Juez IA.</div>`;
            }
        }

        async function generarReporte() {
            const chatResponse = document.getElementById('chatResponse');
            chatResponse.innerHTML += `<div class="user-bubble">Genera reporte táctico del turno.</div>`;
            chatResponse.innerHTML += `<div class="chat-bubble">Analizando patrones de seguridad vía LLM local...</div>`;
            chatResponse.scrollTop = chatResponse.scrollHeight;
            
            try {
                const response = await fetch('/api/reporte', { method: 'POST' });
                const data = await response.json();
                
                if (response.ok) {
                    chatResponse.innerHTML += `<div class="chat-bubble" id="latest-report">${data.reporte.replace(/\\n/g, '<br>')}</div>`;
                    
                    // Actualizar DEFCON
                    if(data.reporte.includes("DEFCON 1") || data.reporte.includes("DEFCON 2")) {
                        document.getElementById('defconLevel').innerText = "DEFCON 1";
                        document.getElementById('defconLevel').style.color = "var(--text-red)";
                        document.getElementById('shieldIcon').style.color = "var(--text-red)";
                        document.getElementById('shieldIcon').style.borderColor = "var(--text-red)";
                        document.getElementById('defconMsg').innerText = "AMENAZA CRÍTICA. ACCIÓN REQUERIDA.";
                    } else {
                        document.getElementById('defconLevel').innerText = "DEFCON 5";
                        document.getElementById('defconLevel').style.color = "var(--text-green)";
                        document.getElementById('shieldIcon').style.color = "var(--text-green)";
                        document.getElementById('shieldIcon').style.borderColor = "var(--text-green)";
                        document.getElementById('defconMsg').innerText = "Entorno pacífico. Monitoreo activo.";
                    }

                } else {
                    chatResponse.innerHTML += `<div class="chat-bubble" style="color:var(--text-red);">Error del Sistema: ${data.detail}</div>`;
                }
                chatResponse.scrollTop = chatResponse.scrollHeight;
            } catch (error) {
                chatResponse.innerHTML += `<div class="chat-bubble" style="color:var(--text-red);">Conexión al servidor de inteligencia fallida.</div>`;
            }
        }

        async function enviarChat() {
            const input = document.getElementById('chatInput');
            const chatResponse = document.getElementById('chatResponse');
            const message = input.value;
            if(!message) return;
            
            chatResponse.innerHTML += `<div class="user-bubble">${message}</div>`;
            const loadingId = 'loading-' + Date.now();
            chatResponse.innerHTML += `<div class="chat-bubble" id="${loadingId}">Consultando memoria forense...</div>`;
            input.value = '';
            chatResponse.scrollTop = chatResponse.scrollHeight;
            
            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ message: message })
                });
                const data = await res.json();
                document.getElementById(loadingId).remove();
                chatResponse.innerHTML += `<div class="chat-bubble">${data.respuesta.replace(/\\n/g, '<br>')}</div>`;
                chatResponse.scrollTop = chatResponse.scrollHeight;
            } catch (e) {
                document.getElementById(loadingId).innerText = 'Error conectando al chat forense.';
            }
        }
        
        function exportReport() {
            const reportEl = document.getElementById('latest-report');
            const reportContent = reportEl ? reportEl.innerText : "No report generated yet.";
            
            const logsContent = Array.from(document.querySelectorAll('.log-card'))
                .map(card => card.innerText.replace(/\\n/g, ' ')).join('\\n');
            
            const finalDoc = `=== OMNIGUARD AI - REPORTE FORENSE AUTOMATIZADO ===\\n\\n${reportContent}\\n\\n=== EVIDENCIA (LOGS DE TELEMETRÍA) ===\\n\\n${logsContent}`;
            
            const blob = new Blob([finalDoc], { type: "text/plain" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `OmniGuard_Tactical_Export_${new Date().getTime()}.txt`;
            a.click();
            URL.revokeObjectURL(url);
        }

        setInterval(fetchLogs, 1000);
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return HTML_TEMPLATE

@app.get("/media_feed")
async def media_feed(type: str = Query("camera"), path: str = Query("")):
    if type == "image" and path:
        buffer = vs.analizar_imagen_estatica(path)
        if buffer:
            return Response(content=buffer, media_type="image/jpeg")
        return Response(status_code=404)
    elif type == "video" and path:
        return StreamingResponse(vs.generar_frames(source=path), media_type="multipart/x-mixed-replace; boundary=frame")
    else:
        if path:
            if path.isdigit():
                cam_source = int(path)
            else:
                cam_source = path
        else:
            cam_source = 0
        return StreamingResponse(vs.generar_frames(source=cam_source), media_type="multipart/x-mixed-replace; boundary=frame")

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(TEMP_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    ext = file.filename.split('.')[-1].lower()
    if ext in ['mp4', 'avi', 'mov', 'mkv', 'webm']:
        file_type = "video"
    else:
        file_type = "image"
        
    return JSONResponse(content={"type": file_type, "path": file_path})

@app.get("/api/logs")
async def get_logs():
    return JSONResponse(content=vs.registro_eventos)

@app.delete("/api/logs")
async def clear_logs():
    vs.registro_eventos.clear()
    return JSONResponse(content={"status": "cleared"})

import ollama
from fastapi import HTTPException
import logging

logger = logging.getLogger("uvicorn.error")

@app.post("/api/reporte")
async def generar_reporte_llm():
    logger.info("AUDITORIA (OMNI-012): Acceso a IA - Solicitud de Reporte Forense LLM iniciada por el operador.")
    
    eventos_recientes = vs.registro_eventos[:20]
    if not eventos_recientes:
        return {"reporte": "No hay eventos registrados en la sesión actual para analizar."}
    
    # Preparar el contexto cronológico
    eventos_texto = "\n".join([f"- {e['hora']}: {e['descripcion']} (Nivel: {e['gravedad']})" for e in eventos_recientes])
    
    prompt = f"""Eres el Analista de Seguridad Táctica de OmniGuard. Analiza estos eventos cronológicos:
{eventos_texto}

INSTRUCCIONES ESTRICTAS:
1. Analiza si existe "ESCALADA" (ej. un individuo intentando ocultar su rostro y luego sacando un arma).
2. Asigna un NIVEL DEFCON del 1 (Máxima Alerta Armada) al 5 (Nominal / Sin anomalías).
3. Redacta el reporte usando exactamente esta estructura Markdown:

### 🚨 NIVEL DE AMENAZA: DEFCON [Tu Nivel]

**1. Análisis Cronológico y Escalada:**
[Tu análisis táctico de qué ocurrió primero y qué después. 2 oraciones máximo]

**2. Acción Táctica Recomendada:**
[Recomendación a los guardias: Llamar policía, ignorar, etc. 1 oración]

NO inventes datos que no estén en los logs."""
    
    try:
        response = ollama.chat(model='phi3', messages=[
            {
                'role': 'user',
                'content': prompt,
            },
        ])
        return {"reporte": response['message']['content']}
    except Exception as e:
        logger.error(f"Error conectando con Ollama: {str(e)}")
        raise HTTPException(status_code=503, detail="LLM Server Offline")

class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
async def chat_con_llm(req: ChatRequest):
    # Contexto para el interrogatorio
    eventos_recientes = vs.registro_eventos[-30:] # Tomamos más logs para el chat
    if not eventos_recientes:
        return {"respuesta": "No hay eventos en la memoria actual para analizar."}
        
    eventos_texto = "\n".join([f"- [{e['hora']}] {e['descripcion']}" for e in eventos_recientes])
    
    system_prompt = f"Eres el Copiloto Interactivo de Seguridad Forense. Analiza la siguiente evidencia de video:\n{eventos_texto}\n\nResponde directamente y de forma breve a la duda del operador basándote SOLO en esta evidencia. No inventes eventos."
    
    try:
        response = ollama.chat(model='phi3', messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': req.message}
        ])
        return {"respuesta": response['message']['content']}
    except Exception as e:
        logger.error(f"Error en chat LLM: {str(e)}")
        raise HTTPException(status_code=503, detail="LLM Server Offline")

@app.post("/api/juez")
async def juez_falsa_alarma(req: ChatRequest):
    eventos_recientes = vs.registro_eventos[-15:] # Últimos eventos de contexto
    eventos_texto = "\n".join([f"[{e['hora']}] {e['descripcion']}" for e in eventos_recientes])
    
    system_prompt = f"""Eres el JUEZ TÁCTICO de OmniGuard. Tu trabajo es filtrar errores de detección (Falsas Alarmas) de la cámara.
Historial reciente:
{eventos_texto}

El usuario te preguntará por un evento crítico. Debes evaluar si es una AMENAZA REAL o una FALSA ALARMA basada en el contexto cronológico (Ej: Si un arma aparece por solo 1 fotograma sin que la persona tenga capucha ni actitud sospechosa antes, es probable que sea una falsa alarma por un reflejo).

Responde ESTRICTAMENTE con este formato:
VEREDICTO: [AMENAZA CONFIRMADA o FALSA ALARMA]
JUSTIFICACIÓN: [Una frase corta explicando por qué]"""
    
    try:
        response = ollama.chat(model='phi3', messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': f"Evalúa este evento crítico reciente: {req.message}"}
        ])
        return {"respuesta": response['message']['content']}
    except Exception as e:
        raise HTTPException(status_code=503, detail="LLM Server Offline")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
