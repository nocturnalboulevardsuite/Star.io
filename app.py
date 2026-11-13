import streamlit as st
import streamlit.components.v1 as components
import base64
import os
import json

st.set_page_config(page_title="Star.io - Batalla Galáctica", layout="wide")

# ==========================================
# CONFIGURACIÓN DE AUDIO RISO
# ==========================================
RUTA_MUSICA = "test.wav" 

def obtener_audio_b64(ruta):
    if os.path.exists(ruta):
        with open(ruta, "rb") as f:
            audio_bytes = f.read()
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            extension = ruta.split('.')[-1]
            return f"data:audio/{extension};base64,{audio_base64}"
    return None

audio_src = obtener_audio_b64(RUTA_MUSICA) or ""

rutas_sfx = {
    "laser": ["sonidos/laser1.wav", "laser1.wav", "laser1.mp3"],
    "death": ["sonidos/muerte.wav", "muerte.wav", "death1.wav"],
    "bh_death": ["sonidos/explosionagujeronegro.wav", "explosionagujeronegro.wav"],
    "dash": ["sonidos/dash1.wav", "dash1.wav"],
    "food": ["sonidos/food1.wav", "food1.wav"],
    "box": ["sonidos/box1.wav", "box1.wav"],
    "orb": ["sonidos/orb1.wav", "orb1.wav"],
    "respawn": ["sonidos/respawn1.wav", "respawn1.wav"],
    "luna_musica": ["sonidos/lunafase2.wav", "lunafase2.wav"]
}

sfx_data = {}
for cat, rutas in rutas_sfx.items():
    sfx_data[cat] = []
    for ruta in rutas:
        b64_str = obtener_audio_b64(ruta)
        if b64_str:
            sfx_data[cat].append(b64_str)

sfx_json = json.dumps(sfx_data)

# ==========================================
# NIVELES (carpeta niveles/ con un .json por nivel)
# ==========================================
def cargar_niveles():
    base = os.path.dirname(os.path.abspath(__file__))
    carpeta = os.path.join(base, "niveles")
    if not os.path.isdir(carpeta):
        carpeta = "niveles"
    niveles = []
    if os.path.isdir(carpeta):
        for nombre in sorted(os.listdir(carpeta)):          # se ordenan por nombre: nivel_01, nivel_02...
            if not nombre.lower().endswith(".json"):
                continue
            try:
                with open(os.path.join(carpeta, nombre), "r", encoding="utf-8") as f:
                    datos = json.load(f)
                datos["archivo"] = nombre
                niveles.append(datos)
            except Exception as e:
                st.warning(f"No se pudo leer el nivel {nombre}: {e}")
    return niveles

# ==========================================
# FASES (carpeta FASES/ con una subcarpeta por fase: fase.js + config.json)
# ==========================================
def cargar_fases():
    base = os.path.dirname(os.path.abspath(__file__))
    carpeta = os.path.join(base, "FASES")
    if not os.path.isdir(carpeta):
        carpeta = "FASES"
    fases, scripts = [], []
    if os.path.isdir(carpeta):
        for nombre in sorted(os.listdir(carpeta)):
            ruta = os.path.join(carpeta, nombre)
            if not os.path.isdir(ruta):
                continue
            info = {"id": nombre, "config": None, "jugable": False}
            ruta_cfg = os.path.join(ruta, "config.json")
            if os.path.exists(ruta_cfg):
                try:
                    with open(ruta_cfg, "r", encoding="utf-8") as f:
                        info["config"] = json.load(f)
                except Exception as e:
                    st.warning(f"No se pudo leer {nombre}/config.json: {e}")
            ruta_js = os.path.join(ruta, "fase.js")
            if os.path.exists(ruta_js):
                with open(ruta_js, "r", encoding="utf-8") as f:
                    # el ID de la fase es el nombre de su carpeta (fase2, fase_2, desierto... da igual)
                    scripts.append(f"// ---- {nombre}/fase.js ----\nwindow.__FASE_ID__ = {json.dumps(nombre)};\n" + f.read())
                info["jugable"] = True
            fases.append(info)
    return fases, "\n".join(scripts)

fases_info, fases_js = cargar_fases()
fases_json = json.dumps(fases_info, ensure_ascii=False).replace("</", "<\\/")

# Si no hay carpeta niveles/, el juego usa el nivel por defecto (igual al original)
niveles_json = json.dumps(cargar_niveles(), ensure_ascii=False).replace("</", "<\\/")

# El juego ocupa toda la pantalla del navegador y la página nunca hace scroll
st.markdown("""
<style>
header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stSidebarCollapsedControl"], footer { display: none !important; }
.block-container, [data-testid="stMainBlockContainer"] { padding: 0 !important; max-width: 100% !important; }
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], section.main { overflow: hidden !important; overscroll-behavior: none !important; background: #050508 !important; }
iframe { position: fixed !important; top: 0 !important; left: 0 !important; width: 100vw !important; height: 100vh !important; border: none !important; z-index: 999 !important; }
</style>
""", unsafe_allow_html=True)

codigo_juego_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&display=swap" rel="stylesheet">
        <style>
            html, body { margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; overscroll-behavior: none; background-color: #050508; user-select: none; font-family: sans-serif; }
            #game-root { position: relative; width: 100vw; height: 100vh; overflow: hidden; }
            canvas { display: block; width: 100%; height: 100%; background-color: #080812; cursor: crosshair; touch-action: none; }
            #leaderboard-panel { position: absolute; top: 15px; right: 15px; width: 230px; background: rgba(10, 10, 16, 0.82); border: 2px solid #00FFFF; border-radius: 10px; padding: 14px 14px 6px 14px; box-sizing: border-box; color: white; box-shadow: 0 0 15px rgba(0, 255, 255, 0.3); pointer-events: none; z-index: 12; }
            .lb-title { display: flex; align-items: center; justify-content: center; gap: 8px; font-size: 16px; font-weight: bold; color: #00FFFF; text-align: center; border-bottom: 2px solid rgba(0, 255, 255, 0.3); padding-bottom: 10px; margin-top: 0; margin-bottom: 12px; }
            .lb-item { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 8px; color: #eaeaea; }
            .lb-item.me { color: #00FFFF; font-weight: bold; text-shadow: 0 0 5px rgba(0, 255, 255, 0.5); }
            #gameover { display: none; position: absolute; color: white; top: 40%; left: 50%; transform: translateX(-50%); text-align: center; font-size: 24px; text-shadow: 2px 2px 10px #000; pointer-events: none; z-index: 5; width: 100%; }
            
            /* Modal de orbes */
            #victory-modal { display: none; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 20; background: rgba(8, 8, 22, 0.96); padding: 30px 36px; border-radius: 14px; border: 3px solid #FFD700; text-align: center; font-family: 'Orbitron', 'Segoe UI', sans-serif; box-shadow: 0 0 40px rgba(255, 215, 0, 0.35); min-width: 420px; }
            #victory-modal h2 { color: #FFD700; margin: 0 0 6px; letter-spacing: 3px; }
            #victory-modal p { color: #9adfe6; margin: 0 0 20px; font-size: 13px; letter-spacing: 1px; }
            .vic-btns { display: flex; flex-direction: column; gap: 12px; }
            .vic-btn { padding: 14px 18px; font-family: inherit; font-size: 16px; font-weight: 700; letter-spacing: 2px; border-radius: 10px; cursor: pointer; border: 2px solid; background: #0d1424; transition: transform 0.12s; }
            .vic-btn:hover:not(:disabled) { transform: scale(1.04); }
            .vic-btn:disabled { opacity: 0.4; cursor: not-allowed; }
            #orb-modal { display: none; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: rgba(10, 10, 25, 0.95); padding: 30px; border-radius: 12px; border: 3px solid white; text-align: center; z-index: 10; }
            .orb-btn { width: 160px; height: 160px; background: #151525; color: white; border: 2px solid #555; border-radius: 10px; font-size: 16px; font-weight: bold; cursor: pointer; transition: 0.2s; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; line-height: 1.4; }
            .orb-btn:hover { background: #2a2a40; transform: scale(1.05); }
            
            /* Controles de audio */
            #audio-controls { position: absolute; top: 15px; left: 15px; background: rgba(10, 10, 20, 0.85); border: 2px solid #00FFFF; border-radius: 8px; padding: 8px 15px; display: flex; align-items: center; gap: 12px; z-index: 15; box-shadow: 0 0 10px rgba(0, 255, 255, 0.2); }
            #mute-btn, #settings-btn { background: none; border: none; cursor: pointer; padding: 0; margin: 0; outline: none; transition: transform 0.2s; display: flex; align-items: center; justify-content: center; width: 28px; height: 28px; }
            #mute-btn:hover, #settings-btn:hover { transform: scale(1.15); }

            /* Ajustes de radio vintage tipo Caja Fuerte */
            #settings-modal { display: none; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: #2b1d14; border: 6px solid #1a110b; border-radius: 16px; padding: 25px; z-index: 40; color: #fff; text-align: center; box-shadow: inset 0 0 20px #000, 0 15px 40px rgba(0,0,0,0.95); width: 340px; }
            #close-settings { position: absolute; top: 10px; right: 12px; background: none; border: none; color: #d4af37; cursor: pointer; padding: 2px; display: flex; }
            /* ===== MENÚ PRINCIPAL ===== */
            #main-menu { position: absolute; inset: 0; z-index: 30; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 26px; background: radial-gradient(ellipse at center, rgba(5, 5, 20, 0.15) 0%, rgba(5, 5, 12, 0.75) 75%); font-family: 'Orbitron', 'Segoe UI', sans-serif; }
            .menu-logo { display: flex; align-items: center; gap: 18px; }
            .menu-logo svg { filter: drop-shadow(0 0 18px rgba(255, 200, 0, 0.55)); animation: logoSpin 14s linear infinite; }
            @keyframes logoSpin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
            @media (prefers-reduced-motion: reduce) { .menu-logo svg { animation: none; } }
            .menu-title { margin: 0; font-size: clamp(42px, 7vw, 84px); font-weight: 900; line-height: 1; color: #FFFFFF; letter-spacing: 3px; text-shadow: 0 0 10px #00FFFF, 0 0 30px rgba(0, 255, 255, 0.6), 4px 4px 0 #CC33FF; }
            .menu-sub { margin-top: 8px; font-size: clamp(13px, 1.6vw, 18px); font-weight: 700; color: #FFD700; letter-spacing: 8px; }
            .menu-panel { width: min(360px, 86vw); display: flex; flex-direction: column; gap: 14px; padding: 26px 24px; background: rgba(10, 10, 22, 0.88); border: 2px solid #00FFFF; border-radius: 16px; box-shadow: 0 0 25px rgba(0, 255, 255, 0.3), inset 0 0 25px rgba(0, 255, 255, 0.06); }
            /* Selección de personaje */
            #char-select { display: none; position: absolute; inset: 0; z-index: 35; flex-direction: column; align-items: center; justify-content: center; gap: 18px; background: rgba(4, 4, 14, 0.92); font-family: 'Orbitron', 'Segoe UI', sans-serif; }
            #char-select h2 { color: #00FFFF; letter-spacing: 4px; margin: 0; text-shadow: 0 0 14px rgba(0,255,255,0.6); }
            .char-grid { display: flex; gap: 14px; flex-wrap: wrap; justify-content: center; max-width: 1100px; }
            .char-card { width: 190px; padding: 14px 12px; background: #0d1424; border: 2px solid #333; border-radius: 12px; color: #fff; cursor: pointer; font-family: inherit; text-align: center; transition: transform 0.12s, box-shadow 0.12s; display: flex; flex-direction: column; align-items: center; gap: 8px; }
            .char-card:hover, .char-card:focus-visible { transform: translateY(-6px) scale(1.03); outline: none; }
            .char-name { font-size: 15px; font-weight: 900; letter-spacing: 2px; }
            .char-stats { width: 100%; font-size: 10px; letter-spacing: 1px; color: #9adfe6; display: flex; flex-direction: column; gap: 4px; }
            .char-stat { display: flex; justify-content: space-between; align-items: center; gap: 6px; }
            .pips { display: flex; gap: 3px; }
            .pip { width: 12px; height: 7px; border-radius: 2px; background: #2a3344; }
            .char-perk { font-size: 10px; line-height: 1.45; color: #ddd; min-height: 58px; font-family: 'Segoe UI', sans-serif; }
            /* Selección de nivel */
            #level-select { display: none; position: absolute; inset: 0; z-index: 35; flex-direction: column; align-items: center; justify-content: center; gap: 18px; background: rgba(4, 4, 14, 0.94); font-family: 'Orbitron', 'Segoe UI', sans-serif; overflow-y: auto; padding: 20px 0; }
            #level-select h2 { color: #FFD700; letter-spacing: 4px; margin: 0; text-shadow: 0 0 14px rgba(255,215,0,0.5); }
            .lvl-grid { display: flex; gap: 16px; flex-wrap: wrap; justify-content: center; max-width: 1100px; }
            .lvl-card { width: 250px; padding: 16px; border: 2px solid #333; border-radius: 12px; color: #fff; display: flex; flex-direction: column; gap: 8px; text-align: center; }
            .lvl-num { font-size: 11px; letter-spacing: 3px; color: #9adfe6; }
            .lvl-name { font-size: 17px; font-weight: 900; letter-spacing: 2px; }
            .lvl-boss { font-size: 10px; letter-spacing: 1px; color: #ccc; }
            .lvl-desc { font-size: 11px; color: #aaa; font-family: 'Segoe UI', sans-serif; line-height: 1.4; }
            .lvl-diffs { display: flex; flex-direction: column; gap: 7px; margin-top: 6px; }
            .diff-btn { display: flex; align-items: center; justify-content: center; gap: 8px; padding: 9px; font-family: inherit; font-size: 13px; font-weight: 700; letter-spacing: 2px; background: #0d1424; border: 2px solid; border-radius: 8px; cursor: pointer; transition: transform 0.12s; }
            .diff-btn:hover:not(:disabled) { transform: scale(1.04); }
            .diff-btn:disabled { cursor: not-allowed; }
            #level-back { padding: 10px 26px; font-family: inherit; font-size: 14px; letter-spacing: 3px; color: #00FFFF; background: transparent; border: 2px solid #00b8c4; border-radius: 8px; cursor: pointer; }
            #victory-sub { white-space: pre-line; }
            #char-back { padding: 10px 26px; font-family: inherit; font-size: 14px; letter-spacing: 3px; color: #00FFFF; background: transparent; border: 2px solid #00b8c4; border-radius: 8px; cursor: pointer; }
            .menu-pilot { text-align: center; color: #9adfe6; font-size: 13px; letter-spacing: 2px; margin-bottom: 4px; }
            .menu-pilot b { color: #FFFFFF; font-size: 16px; }
            .menu-btn { display: flex; align-items: center; gap: 14px; width: 100%; padding: 14px 18px; font-family: inherit; font-size: 19px; font-weight: 700; letter-spacing: 3px; color: #00FFFF; background: #0d1424; border: 2px solid #00b8c4; border-radius: 10px; cursor: pointer; transition: transform 0.12s, background 0.12s, box-shadow 0.12s; }
            .menu-btn svg { flex-shrink: 0; }
            .menu-btn:hover, .menu-btn:focus-visible { background: #12233a; transform: translateX(4px); box-shadow: 0 0 14px rgba(0, 255, 255, 0.45); outline: none; }
            .menu-btn.primary { justify-content: center; font-size: 26px; padding: 18px; color: #06060E; background: linear-gradient(180deg, #7DFFFF 0%, #00D5E0 100%); border-color: #FFFFFF; box-shadow: 0 0 22px rgba(0, 255, 255, 0.55); }
            .menu-btn.primary:hover, .menu-btn.primary:focus-visible { transform: scale(1.04); background: linear-gradient(180deg, #A8FFFF 0%, #22E5EE 100%); }
            #name-panel { display: none; gap: 8px; }
            #name-input { flex: 1; min-width: 0; padding: 10px 12px; font-family: inherit; font-size: 16px; font-weight: 700; letter-spacing: 1px; color: #FFFFFF; background: #05050c; border: 2px solid #CC33FF; border-radius: 8px; outline: none; }
            #name-input:focus { box-shadow: 0 0 10px rgba(204, 51, 255, 0.6); }
            #name-ok { padding: 0 14px; font-family: inherit; font-weight: 700; font-size: 14px; color: #FFFFFF; background: #CC33FF; border: none; border-radius: 8px; cursor: pointer; }
            .menu-controls { display: flex; gap: 22px; flex-wrap: wrap; justify-content: center; color: #8a93b0; font-size: 11px; letter-spacing: 1px; }
            .menu-controls span { display: flex; align-items: center; gap: 8px; }
            .key { font-style: normal; display: inline-block; padding: 4px 8px; color: #FFFFFF; background: #1a1d2e; border: 1px solid #3a4060; border-bottom-width: 3px; border-radius: 5px; font-size: 10px; font-weight: 700; }
            #home-btn { background: none; border: none; cursor: pointer; padding: 0; margin: 0; outline: none; transition: transform 0.2s; display: flex; align-items: center; justify-content: center; width: 28px; height: 28px; }
            #home-btn:hover { transform: scale(1.15); }

            #gameover-skull { display: none; margin: 0 auto 4px auto; width: 64px; height: 64px; filter: drop-shadow(0 0 10px rgba(255, 51, 51, 0.7)); }
            #close-settings:hover { color: #fff; }
            .radio-title { display: flex; align-items: center; justify-content: center; gap: 10px; margin: 0 0 20px 0; color: #d4af37; font-family: 'Courier New', Courier, monospace; letter-spacing: 2px; font-size: 22px; text-shadow: 1px 1px 2px #000; border-bottom: 2px solid #1a110b; padding-bottom: 10px; }
            .knob-container { display: flex; gap: 45px; justify-content: center; margin-top: 10px; }
            .knob-wrapper { display: flex; flex-direction: column; align-items: center; }
            .knob-wrapper label { font-family: 'Courier New', Courier, monospace; font-weight: bold; margin-bottom: 20px; color: #d4af37; font-size: 15px; letter-spacing: 2px; }
            
            /* Diseño de Perilla Estilo Dial de Caja Fuerte */
            .knob-bg { 
                width: 100px; 
                height: 100px; 
                border-radius: 50%; 
                background: #111; 
                display: flex; 
                justify-content: center; 
                align-items: center; 
                border: 4px solid #3a2512; 
                box-shadow: inset 0 0 15px rgba(0,0,0,0.9); 
                position: relative; 
            }
            .knob { 
                width: 62px; 
                height: 62px; 
                border-radius: 50%; 
                background: conic-gradient(from 180deg, #666 0%, #d4af37 25%, #666 50%, #d4af37 75%, #666 100%); 
                border: 2px solid #222; 
                box-shadow: 0 6px 12px rgba(0,0,0,0.8), inset 0 0 8px rgba(255,255,255,0.4); 
                position: relative; 
                cursor: grab; 
                z-index: 5;
            }
            .knob:active { cursor: grabbing; }
            /* Centro negro del dial */
            .knob::after {
                content: '';
                position: absolute;
                top: 50%; left: 50%;
                transform: translate(-50%, -50%);
                width: 36px; height: 36px;
                background: radial-gradient(circle, #222, #050505);
                border-radius: 50%;
                box-shadow: inset 0 0 5px rgba(255,255,255,0.1);
            }
            .knob-indicator { 
                width: 0; 
                height: 0; 
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-bottom: 12px solid #FF3333; 
                position: absolute; 
                top: -3px; 
                left: 50%; 
                transform: translateX(-50%); 
                z-index: 6; 
                filter: drop-shadow(0 2px 2px rgba(0,0,0,0.8));
            }
        </style>
    </head>
    <body>
        <div id="game-root">
            <canvas id="gameCanvas"></canvas>

            <div id="audio-controls">
                <button id="home-btn" title="Volver al menú">
                    <svg viewBox="0 0 24 24" width="24" height="24"><path d="M3 11.5 L12 4 L21 11.5" fill="none" stroke="#00FFFF" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/><path d="M6 10 V20 H10 V14.5 H14 V20 H18 V10" fill="none" stroke="#00FFFF" stroke-width="2.2" stroke-linejoin="round"/></svg>
                </button>
                <button id="mute-btn" title="Activar/Silenciar"></button>
                <button id="settings-btn" title="Ajustes de Sonido">
                    <svg viewBox="0 0 24 24" width="24" height="24">
                        <circle cx="12" cy="12" r="8.5" fill="none" stroke="#00FFFF" stroke-width="4" stroke-dasharray="3.34 3.34"/>
                        <circle cx="12" cy="12" r="6.5" fill="none" stroke="#00FFFF" stroke-width="2.5"/>
                        <circle cx="12" cy="12" r="2.2" fill="#00FFFF"/>
                    </svg>
                </button>
            </div>

            <div id="leaderboard-panel">
                <h3 class="lb-title">
                    <svg viewBox="0 0 24 20" width="22" height="18">
                        <path d="M2 16 L2 6 L7 10 L12 2 L17 10 L22 6 L22 16 Z" fill="#FFD700" stroke="#B8860B" stroke-width="1.2" stroke-linejoin="round"/>
                        <rect x="2" y="16" width="20" height="3" rx="1" fill="#DAA520"/>
                        <circle cx="12" cy="2.5" r="1.6" fill="#FFF3A0"/><circle cx="2" cy="6" r="1.4" fill="#FFF3A0"/><circle cx="22" cy="6" r="1.4" fill="#FFF3A0"/>
                        <circle cx="12" cy="12" r="1.8" fill="#FF3366"/>
                    </svg>
                    <span>TOP ESTRELLAS</span>
                </h3>
                <div id="lb-list"></div>
            </div>

            <div id="gameover">
                <svg id="gameover-skull" viewBox="0 0 48 48">
                    <path d="M24 4C13 4 6 11.5 6 21c0 6 3 10.5 7 13v6c0 1.5 1 2.5 2.5 2.5h17c1.5 0 2.5-1 2.5-2.5v-6c4-2.5 7-7 7-13C42 11.5 35 4 24 4z" fill="#EEEEEE" stroke="#FF3333" stroke-width="2"/>
                    <ellipse cx="16.5" cy="22" rx="5" ry="5.5" fill="#111"/>
                    <ellipse cx="31.5" cy="22" rx="5" ry="5.5" fill="#111"/>
                    <path d="M24 28 L21 33 L27 33 Z" fill="#111"/>
                    <path d="M19 37v5 M24 37v5 M29 37v5" stroke="#111" stroke-width="2"/>
                </svg>
                <h2 id="gameover-title">¡Te moriste Stupid!</h2>
                <p id="gameover-msg" style="font-size: 22px; color: #00FFFF; font-weight: bold; margin-top: 10px;">DALE CLICK AL JUEGO PARA REAPARECER</p>
            </div>

            <div id="victory-modal">
                <h2>¡NIVEL COMPLETADO!</h2>
                <p id="victory-sub"></p>
                <div class="vic-btns" id="vic-btns"></div>
            </div>

            <div id="orb-modal">
                <h2 id="orb-title" style="margin-top:0; display:flex; align-items:center; justify-content:center; gap:10px;">NUEVA MEJORA</h2>
                <div style="display:flex; gap:20px; justify-content:center;">
                    <button id="orb-btn1" class="orb-btn"></button>
                    <button id="orb-btn2" class="orb-btn"></button>
                    <button id="orb-btn3" class="orb-btn" style="display:none;"></button>
                    <button id="orb-btn4" class="orb-btn" style="display:none;"></button>
                </div>
            </div>

            <!-- MENÚ PRINCIPAL -->
            <div id="main-menu">
                <div class="menu-logo">
                    <svg viewBox="0 0 48 48" width="96" height="96">
                        <defs><linearGradient id="logo-grad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#FFF6A0"/><stop offset="100%" stop-color="#FFB800"/></linearGradient></defs>
                        <polygon points="24.00,2.00 29.29,16.72 44.92,17.20 32.56,26.78 36.93,41.80 24.00,33.00 11.07,41.80 15.44,26.78 3.08,17.20 18.71,16.72" fill="url(#logo-grad)" stroke="#FF8C00" stroke-width="1.6" stroke-linejoin="round"/>
                        <circle cx="20" cy="22" r="1.8" fill="#5a3a00"/><circle cx="28" cy="22" r="1.8" fill="#5a3a00"/>
                    </svg>
                    <div>
                        <h1 class="menu-title">StarZ.io</h1>
                        <div class="menu-sub">BATALLA GALÁCTICA</div>
                    </div>
                </div>

                <div class="menu-panel">
                    <div class="menu-pilot">PILOTO <b id="menu-name">TÚ</b></div>
                    <button class="menu-btn primary" id="btn-play">
                        <svg viewBox="0 0 24 24" width="26" height="26"><path d="M7 4.5 L19.5 12 L7 19.5 Z" fill="#06060E" stroke="#06060E" stroke-width="2" stroke-linejoin="round"/></svg>
                        JUGAR
                    </button>
                    <button class="menu-btn" id="btn-sound">
                        <svg viewBox="0 0 24 24" width="24" height="24"><path d="M3 9 H7 L12 5 V19 L7 15 H3 Z" fill="#00FFFF"/><path d="M15.5 8.5 A5 5 0 0 1 15.5 15.5" stroke="#00FFFF" stroke-width="2" fill="none" stroke-linecap="round"/><path d="M18.5 5.5 A9 9 0 0 1 18.5 18.5" stroke="#00FFFF" stroke-width="2" fill="none" stroke-linecap="round"/></svg>
                        SONIDO
                    </button>
                    <button class="menu-btn" id="btn-name">
                        <svg viewBox="0 0 24 24" width="24" height="24"><circle cx="12" cy="8" r="4" fill="none" stroke="#00FFFF" stroke-width="2.2"/><path d="M4 21 C4 15.5 8 13.5 12 13.5 C16 13.5 20 15.5 20 21" fill="none" stroke="#00FFFF" stroke-width="2.2" stroke-linecap="round"/></svg>
                        NOMBRE
                    </button>
                    <div id="name-panel">
                        <input id="name-input" type="text" maxlength="12" placeholder="Tu nombre" autocomplete="off">
                        <button id="name-ok">LISTO</button>
                    </div>
                </div>

                <div class="menu-controls">
                    <span><i class="key">MANTÉN CLICK IZQ</i> Disparar</span>
                    <span><i class="key">CLICK DER</i> Dash</span>
                    <span><i class="key">ESPACIO</i> Modo fantasma</span>
                    <span><i class="key">R</i> Láser abismal (al matar el agujero negro)</span>
                    <span><i class="key">X</i> Súper cañón</span>
                    <span><i class="key">F</i> Empuje</span>
                    <span><i class="key">Q</i> Piel de Rhino</span>
                    <span><i class="key">E</i> Escudo reflector</span>
                    <span><i class="key">WASD</i> Moverse</span>
                    <span><i class="key">SHIFT</i> Sprint</span>
                    <span><i class="key">MOUSE</i> Apuntar</span>
                </div>
            </div>

            <!-- SELECCIÓN DE NIVEL -->
            <div id="level-select">
                <h2>ELIGE NIVEL Y DIFICULTAD</h2>
                <div class="lvl-grid" id="level-grid"></div>
                <button id="level-back">VOLVER</button>
            </div>

            <!-- SELECCIÓN DE PERSONAJE -->
            <div id="char-select">
                <h2>ELIGE TU ESTRELLA</h2>
                <div class="char-grid" id="char-grid"></div>
                <button id="char-back">VOLVER</button>
            </div>

            <!-- Modal de Radio Vintage -->
            <div id="settings-modal">
                <button id="close-settings" title="Cerrar">
                    <svg viewBox="0 0 24 24" width="20" height="20"><path d="M6 6 L18 18 M18 6 L6 18" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg>
                </button>
                <h3 class="radio-title">
                    <svg viewBox="0 0 32 24" width="32" height="24">
                        <line x1="8" y1="6" x2="24" y2="1" stroke="#d4af37" stroke-width="1.5" stroke-linecap="round"/>
                        <rect x="2" y="6" width="28" height="17" rx="3" fill="#3a2512" stroke="#d4af37" stroke-width="1.5"/>
                        <circle cx="10" cy="14.5" r="5" fill="#1a110b" stroke="#d4af37" stroke-width="1"/>
                        <circle cx="10" cy="14.5" r="1.5" fill="#d4af37"/>
                        <rect x="18" y="10" width="9" height="3" rx="1" fill="#d4af37"/>
                        <circle cx="20" cy="18" r="1.8" fill="#d4af37"/><circle cx="25" cy="18" r="1.8" fill="#d4af37"/>
                    </svg>
                    <span>FRECUENCIA</span>
                </h3>
                <div class="knob-container">
                    <div class="knob-wrapper">
                        <label>MÚSICA</label>
                        <div class="knob-bg" id="bg-music">
                            <div class="knob" id="knob-music">
                                <div class="knob-indicator"></div>
                            </div>
                        </div>
                    </div>
                    <div class="knob-wrapper">
                        <label>EFECTOS</label>
                        <div class="knob-bg" id="bg-sfx">
                            <div class="knob" id="knob-sfx">
                                <div class="knob-indicator"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            // === SISTEMA DE AUDIO (MÚSICA Y SFX) ===
            const audioSrc = "__AUDIO_SRC__";
            const sfxData = __SFX_DATA__; 
            let bgMusic = null;
            let isUserInteracted = false;
            let usingBossTrack = false;
            let gameState = 'menu';   // 'menu' o 'playing'

            let playerName = "TÚ";
            // Siempre se parte como jugador nuevo (no se recuerda el nombre anterior)
            try { localStorage.removeItem('starz_name'); } catch (e) {}
            
            let musicVolume = 0.3;
            let sfxVolume = 0.5;
            
            const muteBtn = document.getElementById("mute-btn");
            const settingsBtn = document.getElementById("settings-btn");
            const settingsModal = document.getElementById("settings-modal");
            const closeSettings = document.getElementById("close-settings");

            // === ICONOS SVG (HTML) ===
            const SPEAKER_BODY = '<path d="M3 9 H7 L12 5 V19 L7 15 H3 Z" fill="#00FFFF" stroke="#00FFFF" stroke-width="1" stroke-linejoin="round"/>';
            const ICON_SOUND_ON = '<svg viewBox="0 0 24 24" width="24" height="24">' + SPEAKER_BODY +
                '<path d="M15.5 8.5 A5 5 0 0 1 15.5 15.5" stroke="#00FFFF" stroke-width="2" fill="none" stroke-linecap="round"/>' +
                '<path d="M18.5 5.5 A9 9 0 0 1 18.5 18.5" stroke="#00FFFF" stroke-width="2" fill="none" stroke-linecap="round"/></svg>';
            const ICON_SOUND_OFF = '<svg viewBox="0 0 24 24" width="24" height="24">' + SPEAKER_BODY +
                '<path d="M15.5 9 L21 15 M21 9 L15.5 15" stroke="#FF3366" stroke-width="2.4" stroke-linecap="round"/></svg>';
            function setMuteIcon(on) { muteBtn.innerHTML = on ? ICON_SOUND_ON : ICON_SOUND_OFF; }
            setMuteIcon(false);

            function spikyPoints(cx, cy, n, ro, ri) {
                let p = [];
                for (let i = 0; i < n * 2; i++) {
                    let r = (i % 2 === 0) ? ro : ri;
                    let a = -Math.PI / 2 + (Math.PI * i) / n;
                    p.push((cx + Math.cos(a) * r).toFixed(1) + "," + (cy + Math.sin(a) * r).toFixed(1));
                }
                return p.join(" ");
            }
            function svgOrb(color, id) {
                return '<svg viewBox="0 0 24 24" width="28" height="28"><defs><radialGradient id="' + id + '" cx="35%" cy="35%" r="70%">' +
                    '<stop offset="0%" stop-color="#FFFFFF"/><stop offset="40%" stop-color="' + color + '"/><stop offset="100%" stop-color="#000"/></radialGradient></defs>' +
                    '<circle cx="12" cy="12" r="10" fill="url(#' + id + ')" stroke="' + color + '" stroke-width="1.5"/></svg>';
            }
            const ICON_RANGE = '<svg viewBox="0 0 48 48" width="52" height="52">' +
                '<path d="M20 33 Q24 44 24 46 Q24 44 28 33 Z" fill="#FFA500"/>' +
                '<path d="M22 33 Q24 39 24 41 Q24 39 26 33 Z" fill="#FFFF66"/>' +
                '<path d="M15 23 L9 32 L16 31 Z M33 23 L39 32 L32 31 Z" fill="#00BFFF" stroke="#00FFFF" stroke-width="1.5" stroke-linejoin="round"/>' +
                '<path d="M24 3 C31 8 34 16 33 25 L29 33 H19 L15 25 C14 16 17 8 24 3 Z" fill="#E8F8FF" stroke="#00FFFF" stroke-width="2" stroke-linejoin="round"/>' +
                '<circle cx="24" cy="17" r="4" fill="#0a3a5a" stroke="#00FFFF" stroke-width="1.5"/></svg>';
            const ICON_DAMAGE = '<svg viewBox="0 0 48 48" width="52" height="52">' +
                '<polygon points="' + spikyPoints(24, 24, 10, 22, 11) + '" fill="#FF4500" stroke="#FFD700" stroke-width="2" stroke-linejoin="round"/>' +
                '<polygon points="' + spikyPoints(24, 24, 10, 13, 7) + '" fill="#FFE066"/>' +
                '<circle cx="24" cy="24" r="4" fill="#FFFFFF"/></svg>';
            const ICON_MULTI = '<svg viewBox="0 0 48 48" width="52" height="52" fill="none" stroke="#CC33FF" stroke-width="3" stroke-linecap="round">' +
                '<defs><marker id="mk-multi" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="4" markerHeight="4" orient="auto"><path d="M0 0 L10 5 L0 10 Z" fill="#E199FF" stroke="none"/></marker></defs>' +
                '<line x1="24" y1="44" x2="24" y2="9" marker-end="url(#mk-multi)"/>' +
                '<line x1="24" y1="44" x2="10" y2="13" marker-end="url(#mk-multi)"/>' +
                '<line x1="24" y1="44" x2="38" y2="13" marker-end="url(#mk-multi)"/></svg>';
            const ICON_CANNON = '<svg viewBox="0 0 48 48" width="52" height="52">' +
                '<circle cx="31" cy="24" r="12" fill="#FF8C00" stroke="#FFD27A" stroke-width="2"/>' +
                '<circle cx="27" cy="20" r="4" fill="#FFE2B0" opacity="0.8"/>' +
                '<path d="M4 18 L16 21 M4 30 L16 27 M2 24 L16 24" stroke="#FFB347" stroke-width="3" stroke-linecap="round"/></svg>';
            const ICON_PUSH = '<svg viewBox="0 0 48 48" width="52" height="52" fill="rgba(51,255,102,0.25)" stroke="#33FF66" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round">' +
                '<path d="M14 40 L14 22 Q14 19 17 19 Q20 19 20 22 L20 12 Q20 9 23 9 Q26 9 26 12 L26 10 Q26 7 29 7 Q32 7 32 10 L32 13 Q32 10 35 10 Q38 10 38 13 L38 30 Q38 40 28 42 L20 42 Q16 42 14 40 Z"/>' +
                '<path d="M14 26 Q8 22 7 27 Q8 31 14 34" /></svg>';
            const ICON_RHINO = '<svg viewBox="0 0 48 48" width="52" height="52">' +
                '<path d="M24 4 L40 10 L40 24 Q40 36 24 44 Q8 36 8 24 L8 10 Z" fill="#8A8F9C" stroke="#E0E3EA" stroke-width="2.5" stroke-linejoin="round"/>' +
                '<path d="M24 4 L24 44 M8 18 L40 18 M10 30 L38 30" stroke="#5A5F6B" stroke-width="2"/>' +
                '<path d="M20 22 Q24 10 30 8 Q27 16 28 24 Z" fill="#FFD700" stroke="#B8860B" stroke-width="1.5" stroke-linejoin="round"/></svg>';
            const ICON_REFLECT = '<svg viewBox="0 0 48 48" width="52" height="52" fill="none" stroke-linecap="round" stroke-linejoin="round">' +
                '<circle cx="24" cy="24" r="17" stroke="#00FFFF" stroke-width="3" stroke-dasharray="6 4"/>' +
                '<circle cx="24" cy="24" r="10" fill="rgba(0,255,255,0.2)" stroke="#00FFFF" stroke-width="1.5"/>' +
                '<path d="M4 6 L17 17 L6 26" stroke="#FFFFFF" stroke-width="2.5"/>' +
                '<path d="M6 26 L3 21 M6 26 L11 27" stroke="#FFFFFF" stroke-width="2.5"/></svg>';
            const ICON_CROSS = '<svg viewBox="0 0 48 48" width="52" height="52" fill="none" stroke="#CC33FF" stroke-width="3" stroke-linecap="round">' +
                '<defs><marker id="mk-cross" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="4" markerHeight="4" orient="auto"><path d="M0 0 L10 5 L0 10 Z" fill="#E199FF" stroke="none"/></marker></defs>' +
                '<line x1="24" y1="24" x2="24" y2="6" marker-end="url(#mk-cross)"/>' +
                '<line x1="24" y1="24" x2="42" y2="24" marker-end="url(#mk-cross)"/>' +
                '<line x1="24" y1="24" x2="24" y2="42" marker-end="url(#mk-cross)"/>' +
                '<line x1="24" y1="24" x2="6" y2="24" marker-end="url(#mk-cross)"/>' +
                '<circle cx="24" cy="24" r="4.5" fill="#CC33FF" stroke="#FFFFFF" stroke-width="1.5"/></svg>';

            if (audioSrc && audioSrc !== "") {
                bgMusic = new Audio(audioSrc);
                bgMusic.loop = true;
                bgMusic.volume = musicVolume;
            }

            // === SONIDO DE DIAL MECÁNICO (CAJA FUERTE) ===
            let safeClickCtx = null;
            function playSafeClick() {
                if (!isUserInteracted) return;
                try {
                    if (!safeClickCtx) {
                        const AudioContext = window.AudioContext || window.webkitAudioContext;
                        safeClickCtx = new AudioContext();
                    }
                    if (safeClickCtx.state === 'suspended') safeClickCtx.resume();
                    
                    let osc = safeClickCtx.createOscillator();
                    let gainNode = safeClickCtx.createGain();
                    let filter = safeClickCtx.createBiquadFilter();
                    
                    osc.type = 'square';
                    osc.frequency.setValueAtTime(800, safeClickCtx.currentTime);
                    osc.frequency.exponentialRampToValueAtTime(80, safeClickCtx.currentTime + 0.015);
                    
                    filter.type = 'bandpass';
                    filter.frequency.value = 1500;
                    
                    gainNode.gain.setValueAtTime(0.4, safeClickCtx.currentTime);
                    gainNode.gain.exponentialRampToValueAtTime(0.01, safeClickCtx.currentTime + 0.015);
                    
                    osc.connect(filter);
                    filter.connect(gainNode);
                    gainNode.connect(safeClickCtx.destination);
                    
                    osc.start();
                    osc.stop(safeClickCtx.currentTime + 0.015);
                } catch(e) {}
            }

            muteBtn.addEventListener('mousedown', (e) => e.stopPropagation());
            settingsBtn.addEventListener('mousedown', (e) => e.stopPropagation());
            settingsModal.addEventListener('mousedown', (e) => e.stopPropagation());

            settingsBtn.addEventListener('click', () => { 
                settingsModal.style.display = 'block'; 
                isPaused = true; 
            });
            
            closeSettings.addEventListener('click', () => { 
                settingsModal.style.display = 'none'; 
                if (orbModal.style.display === 'none') {
                    isPaused = false; 
                }
            });

            // Lógica de las Perillas tipo Dial
            function setupKnob(knobId, initialVol, callback) {
                const knob = document.getElementById(knobId);
                const knobBg = knob.parentElement;
                let isDragging = false;
                let lastStep = -1;
                
                // Generar rayitas y números tipo caja fuerte programáticamente
                // Rango visual: de -135 a 135 grados
                for(let i=0; i<=10; i++) {
                    let angle = -135 + (i * 27);
                    
                    // Rayitas
                    let tick = document.createElement('div');
                    tick.style.position = 'absolute';
                    tick.style.width = '2px';
                    tick.style.height = '6px';
                    tick.style.background = '#d4af37';
                    tick.style.top = '4px';
                    tick.style.left = '49px'; // centro del contenedor (100/2 - 1)
                    tick.style.transformOrigin = '1px 46px'; // pivote en el centro del fondo
                    tick.style.transform = `rotate(${angle}deg)`;
                    knobBg.appendChild(tick);
                    
                    // Números (0 a 100)
                    let num = document.createElement('div');
                    num.style.position = 'absolute';
                    num.style.color = '#d4af37';
                    num.style.fontSize = '10px';
                    num.style.fontFamily = 'monospace';
                    num.style.fontWeight = 'bold';
                    num.style.width = '16px';
                    num.style.textAlign = 'center';
                    num.style.left = '42px'; // (100/2 - 8)
                    num.style.top = '14px';
                    num.style.transformOrigin = '8px 36px'; // pivote
                    num.style.transform = `rotate(${angle}deg)`;
                    num.innerText = i * 10;
                    knobBg.appendChild(num);
                }
                
                function updateKnobTransform(vol) {
                    let angle = (vol * 270) - 135;
                    knob.style.transform = `rotate(${angle}deg)`;
                    
                    // Calcular "clicks" audibles basándose en el volumen
                    let currentStep = Math.round(vol * 40);
                    if (lastStep !== -1 && currentStep !== lastStep) {
                        playSafeClick();
                    }
                    lastStep = currentStep;
                }
                updateKnobTransform(initialVol);
                
                knob.addEventListener('mousedown', (e) => {
                    isDragging = true;
                    e.preventDefault(); 
                });
                
                window.addEventListener('mouseup', () => { isDragging = false; });
                
                window.addEventListener('mousemove', (e) => {
                    if(!isDragging) return;
                    
                    const rect = knob.getBoundingClientRect();
                    const centerX = rect.left + rect.width / 2;
                    const centerY = rect.top + rect.height / 2;
                    
                    // Cálculo matemático corregido del ángulo para la perilla
                    let angle = Math.atan2(e.clientY - centerY, e.clientX - centerX) * (180 / Math.PI) + 90;
                    
                    // Normalizar rango a [-180, 180]
                    while (angle > 180) angle -= 360;
                    while (angle < -180) angle += 360;
                    
                    // Delimitar topes entre -135 (0%) y 135 (100%) sin saltos bruscos
                    if (angle > 135) angle = 135;
                    if (angle < -135) angle = -135;
                    
                    let volume = (angle + 135) / 270;
                    updateKnobTransform(volume);
                    callback(volume);
                });
            }

            setupKnob('knob-music', musicVolume, (v) => { 
                musicVolume = v;
                if(bgMusic) bgMusic.volume = musicVolume; 
                if(musicVolume > 0 && bgMusic && bgMusic.paused && isUserInteracted) {
                    bgMusic.play().catch(()=>{});
                    setMuteIcon(true);
                } else if (musicVolume === 0 && bgMusic) {
                    bgMusic.pause();
                    setMuteIcon(false);
                }
            });

            setupKnob('knob-sfx', sfxVolume, (v) => { sfxVolume = v; });

            function playSfx(type, volMultiplier = 1.0) {
                if (!isUserInteracted || sfxVolume === 0) return;
                let soundArray = sfxData[type];
                if (soundArray && soundArray.length > 0) {
                    let randomSrc = soundArray[Math.floor(Math.random() * soundArray.length)];
                    let snd = new Audio(randomSrc);
                    snd.volume = Math.min(1.0, sfxVolume * volMultiplier);
                    snd.play().catch(e => console.log("SFX play bloqueado", e));
                }
            }

            // El primer click en cualquier parte (menú o juego) activa la música
            document.addEventListener('pointerdown', () => {
                if (!isUserInteracted) {
                    isUserInteracted = true;
                    if (bgMusic && bgMusic.paused && musicVolume > 0) { 
                        bgMusic.play().then(() => { setMuteIcon(true); }).catch(err => {}); 
                    }
                }
            });

            muteBtn.addEventListener('click', () => {
                if(!bgMusic) return;
                if(bgMusic.paused) {
                    bgMusic.play(); setMuteIcon(true);
                } else { 
                    bgMusic.pause(); setMuteIcon(false); 
                }
            });

            // === SISTEMA DEL JUEGO ===
            const canvas = document.getElementById("gameCanvas");
            const ctx = canvas.getContext("2d");
            const overScreen = document.getElementById("gameover");
            const overTitle = document.getElementById("gameover-title");
            const overMsg = document.getElementById("gameover-msg");
            const overSkull = document.getElementById("gameover-skull");
            const lbList = document.getElementById("lb-list");
            const orbModal = document.getElementById("orb-modal");
            const orbTitle = document.getElementById("orb-title");
            const btn1 = document.getElementById("orb-btn1");
            const btn2 = document.getElementById("orb-btn2");
            const btn3 = document.getElementById("orb-btn3");
            const btn4 = document.getElementById("orb-btn4");

            window.addEventListener('contextmenu', (e) => e.preventDefault());

            // Bloquear el scroll de la página: la rueda del mouse y las teclas se quedan dentro del juego
            window.addEventListener('wheel', (e) => e.preventDefault(), { passive: false });
            window.addEventListener('touchmove', (e) => e.preventDefault(), { passive: false });
            window.addEventListener('keydown', (e) => {
                if (['Space', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'PageUp', 'PageDown', 'Home', 'End'].includes(e.code)) e.preventDefault();
            });

            // ======================================================
            // === NIVELES ===  (se cargan desde la carpeta niveles/ del repo)
            // ======================================================
            const LEVELS_RAW = __LEVELS_DATA__;
            const FASES_DATA = __FASES_DATA__;   // carpetas de FASES/ (fase.js se carga en el script de abajo)
            let currentFase = null;
            const DEFAULT_LEVEL = {
                nombre: "Vía Láctea", descripcion: "",
                mundo: { ancho: 3200, alto: 3200, color_fondo: "#06060E", color_borde: "#FF3366" },
                bots: { cantidad: 28, vida: 200, velocidad: 1.0, espera_disparo_ms: 2500, potencia_disparo: 1.0 },
                comida: 600, orbes_max: 3, musica_victoria: "",
                agujero_negro: { vida: 10000, radio: 75, pos_x: 0.7, pos_y: 0.3, crecimiento: 0.012, fuerza_atraccion: 2.8 },
                jefe: { nombre: "LUNA SANGRIENTA", nombre_fase2: "LUNA CÍCLOPE", vida: 15000, velocidad: 1.2, velocidad_fase2: 0.45,
                        color: "#FF6600", color_fase2: "#FF0033", potencia_balas: 1.5, espera_laser_frames: 1800, potencia_laser: 5,
                        color_crateres: "#990000", color_detalles: "", tamano: 1,
                        rayos: false, rayos_cantidad: 1, rayos_espera_frames: 210,
                        bombas: false, bombas_cantidad: 1, bombas_espera_frames: 240 }
            };
            function mergeLevel(raw) {
                const out = {};
                Object.keys(DEFAULT_LEVEL).forEach(k => {
                    const d = DEFAULT_LEVEL[k], v = raw ? raw[k] : undefined;
                    out[k] = (d && typeof d === 'object') ? Object.assign({}, d, (v && typeof v === 'object') ? v : {}) : (v !== undefined ? v : d);
                });
                if (raw && raw.archivo) out.archivo = raw.archivo;
                if (raw && raw.dificultades) out.dificultades = raw.dificultades;
                if (raw && raw.jefe_dificultad) out.jefe_dificultad = raw.jefe_dificultad;
                return out;
            }
            const LEVELS = (Array.isArray(LEVELS_RAW) && LEVELS_RAW.length > 0 ? LEVELS_RAW : [{}]).map(mergeLevel);
            let levelIndex = 0;
            let LV = LEVELS[0];
            let freeMode = false, victoryTimer = 0;

            let worldW = LV.mundo.ancho;
            let worldH = LV.mundo.alto;
            const LARGE_THRESHOLD = 50; 
            
            let camX = 0, camY = 0, zoom = 1;
            let screenMouseX = canvas.width / 2;
            let screenMouseY = canvas.height / 2;
            let isGameOver = false;
            let isPaused = false;
            let cinematicTimer = 0; 

            let lastDashTime = 0;
            const dashCooldown = 5000; 
            let dashTimer = 0; 

            let floatingTexts = []; let lasers = []; let particles = []; let boxes = []; let redBoxes = []; let hearts = []; let orbs = [];
            let bgStarsLayer1 = []; let bgStarsLayer2 = [];
            
            function genBgStars() {
                bgStarsLayer1 = []; bgStarsLayer2 = [];
                let count = Math.max(120, Math.min(400, Math.round((canvas.width * canvas.height) / 5000)));
                for(let i=0; i<count; i++) {
                    bgStarsLayer1.push({x: Math.random() * canvas.width, y: Math.random() * canvas.height, r: Math.random() * 1.5 + 0.5});
                    bgStarsLayer2.push({x: Math.random() * canvas.width, y: Math.random() * canvas.height, r: Math.random() * 2.5 + 1.0});
                }
            }

            // El canvas ocupa toda la ventana del juego y se adapta si cambia de tamaño
            function resizeCanvas() {
                canvas.width = Math.max(300, window.innerWidth);
                canvas.height = Math.max(300, window.innerHeight);
                genBgStars();
            }
            resizeCanvas();
            screenMouseX = canvas.width / 2; screenMouseY = canvas.height / 2;
            window.addEventListener('resize', resizeCanvas);

            let meteor = { 
                orbitAngle: 0, orbitRadius: 450, x: worldW / 2, y: worldH / 2, r: 100, angle: 0, 
                hp: 15000, maxHp: 15000, isBoss: false, isPhase2: false, phase2MusicStarted: false, 
                dead: false, shootAngle: 0, laserTimer: 0, laserChargeTimer: 0, laserSweepTimer: 0, laserAngle: 0,
                craters: [ {x: -35, y: -25, r: 20}, {x: 35, y: -35, r: 16}, {x: 10, y: 30, r: 25}, {x: -40, y: 25, r: 14}, {x: 0, y: 0, r: 18} ] 
            };
            let blackHole = { x: worldW * 0.7, y: worldH * 0.3, r: 75, hp: 10000, maxHp: 10000, dead: false };

            window.addEventListener('mousemove', (e) => {
                const rect = canvas.getBoundingClientRect();
                screenMouseX = e.clientX - rect.left; screenMouseY = e.clientY - rect.top;
            });

            // Movimiento con WASD (y flechas)
            const keysDown = new Set();
            const MOVE_KEYS = ['KeyW', 'KeyA', 'KeyS', 'KeyD', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ShiftLeft', 'ShiftRight'];
            window.addEventListener('keydown', (e) => { if (MOVE_KEYS.includes(e.code)) keysDown.add(e.code); });
            window.addEventListener('keyup', (e) => { keysDown.delete(e.code); });
            window.addEventListener('blur', () => { keysDown.clear(); isFiring = false; });

            // Disparo automático manteniendo el click izquierdo
            let isFiring = false;
            let fireCooldown = 0;
            const FIRE_RATE = 7; // frames entre disparos (~8 disparos por segundo)

            canvas.addEventListener('mousedown', (e) => {
                if(gameState !== 'playing' || isPaused) return;
                if(player.dead) { if (playerLives > 0) respawnPlayer(); else goToMenu(); return; }
                if(e.button === 0) { isFiring = true; if (fireCooldown <= 0) { shootLaser(); fireCooldown = FIRE_RATE; } }
                else if(e.button === 2) { e.preventDefault(); triggerDash(); }
            });
            window.addEventListener('mouseup', (e) => { if (e.button === 0) isFiring = false; });

            window.addEventListener('keydown', (e) => {
                if(gameState !== 'playing' || isPaused) return;
                if(e.code === 'Space') {
                    e.preventDefault();
                    if(player.dead) { if(playerLives > 0) respawnPlayer(); } 
                    else { triggerInvulnerability(); }
                }
                if(e.code === 'KeyR' && !e.repeat) triggerAbyssLaser();
                if(e.code === 'KeyX' && !e.repeat) useAbility('cannon');
                if(e.code === 'KeyF' && !e.repeat) useAbility('push');
                if(e.code === 'KeyQ' && !e.repeat) useAbility('rhino');
                if(e.code === 'KeyE' && !e.repeat) useAbility('reflect');
            });

            function handlePlayerDeath() {
                playerLives--;
                isGameOver = true;
                playEndSfx(playerLives <= 0);
                overScreen.style.display = 'block';
                if(playerLives > 0) { overSkull.style.display = 'none'; overTitle.innerText = "te moriste stupid"; overMsg.innerText = `DALE CLICK PARA REAPARECER (${playerLives} VIDAS RESTANTES)`; overMsg.style.color = "#00FFFF"; } 
                else { overSkull.style.display = 'block'; overTitle.innerText = "FIN DE LA PARTIDA"; overMsg.innerText = "SIN VIDAS - DALE CLICK PARA VOLVER AL MENÚ"; overMsg.style.color = "#FF3333"; }
            }

            function respawnPlayer() {
                player.x = Math.random() * (worldW - 200) + 100; player.y = Math.random() * (worldH - 200) + 100;
                player.r = 18; player.hp = 200; player.maxHp = 200; player.shields = 0; player.dead = false;
                player.invulnTimer = 0; player.fireTimer = 0; player.speedBoostTimer = 0; player.hasInvulnCharge = false;
                player.laserRange = 1.0; player.laserDamage = 1.0; 
                player.multiLevel = 1; player.crossLevel = 0; player.continuousLaserTimer = 0;
                isGameOver = false; overScreen.style.display = 'none';
                
                resetAbilities();
                applyCharacter(false);
                applyRissosMode();
                playSfx("respawn");
                floatingTexts.push({ x: player.x, y: player.y - 30, text: `¡REAPARECISTE! (${playerLives} vidas)`, icon: "star", color: "#33FF66", life: 50, size: 18 });
            }

            // === LÁSER ABISMAL ===
            // Se desbloquea al destruir el agujero negro. Con R dispara un rayo enorme durante 2 s; recarga de 30 s.
            const ABYSS_DURATION = 120;   // 2 segundos (60 fps)
            const ABYSS_COOLDOWN = 1800;  // 30 segundos
            const ABYSS_LENGTH = 1600;    // largo del rayo
            const ABYSS_TICK = 5;         // cada cuántos frames hace daño
            const ABYSS_DMG_BOTS = 30;    // daño a estrellas por golpe
            const ABYSS_DMG_BOSS = 60;    // daño a la Luna por golpe
            let abyssUnlocked = false, abyssTimer = 0, abyssCooldown = 0, abyssAngle = 0;

            function unlockAbyssLaser() {
                if (abyssUnlocked) return;
                abyssUnlocked = true; abyssCooldown = 0;
                floatingTexts.push({ x: player.x, y: player.y - player.r - 60, text: "¡LÁSER ABISMAL DESBLOQUEADO! [R]", icon: "vortex", iconBoth: true, color: "#B266FF", life: 200, size: 26 });
            }

            function aimAngle() {
                let targetX = (screenMouseX - canvas.width / 2) / zoom + camX + canvas.width / 2;
                let targetY = (screenMouseY - canvas.height / 2) / zoom + camY + canvas.height / 2;
                return Math.atan2(targetY - player.y, targetX - player.x);
            }

            function triggerAbyssLaser() {
                if (gameState !== 'playing' || isPaused || !player || player.dead) return;
                if (!abyssUnlocked || abyssTimer > 0) return;
                if (abyssCooldown > 0) {
                    floatingTexts.push({ x: player.x, y: player.y - player.r - 25, text: `RECARGANDO ${Math.ceil(abyssCooldown / 60)}s`, color: "#888", life: 30, size: 14 });
                    return;
                }
                abyssTimer = ABYSS_DURATION; abyssCooldown = ABYSS_COOLDOWN; abyssAngle = aimAngle();
                if (player.character === 'godzilla' && !player.rissos) {
                    // Te deja a 10 golpes de morir; si ya estabas más abajo, te cuesta 1 golpe (nunca te mata)
                    let tenHits = GODZILLA_HIT * 10;
                    let before = player.hp;
                    player.hp = before > tenHits ? tenHits : Math.max(1, before - GODZILLA_HIT);
                    floatingTexts.push({ x: player.x, y: player.y - player.r - 55, text: `-${Math.ceil(before - player.hp)} HP`, color: "#33FF66", life: 50, size: 20 });
                }
                playGodzillaBeam();
                floatingTexts.push({ x: player.x, y: player.y - player.r - 30, text: "¡LÁSER ABISMAL!", icon: "vortex", iconBoth: true, color: "#B266FF", life: 60, size: 24 });
            }

            // Sonido del rayo estilo Godzilla: carga + rugido de bajos saturados (sintetizado, no necesita archivo)
            let beamAudioCtx = null;
            function makeDistortion(amount) {
                const n = 2048, curve = new Float32Array(n);
                for (let i = 0; i < n; i++) { const x = (i * 2) / n - 1; curve[i] = ((3 + amount) * x * 20 * (Math.PI / 180)) / (Math.PI + amount * Math.abs(x)); }
                return curve;
            }
            function playGodzillaBeam() {
                if (!isUserInteracted || sfxVolume === 0) return;
                try {
                    if (!beamAudioCtx) beamAudioCtx = new (window.AudioContext || window.webkitAudioContext)();
                    const ac = beamAudioCtx;
                    if (ac.state === 'suspended') ac.resume();
                    const t0 = ac.currentTime;
                    const charge = 0.12;                                 // carga breve antes del rugido
                    const end = t0 + charge + ABYSS_DURATION / 60;       // dura lo mismo que el rayo
                    const rel = 0.45;

                    // Salida: compresor para que los bajos saturados no revienten
                    const comp = ac.createDynamicsCompressor();
                    comp.threshold.value = -14; comp.ratio.value = 6;
                    const master = ac.createGain(); master.gain.value = Math.min(1, sfxVolume * 1.1);
                    comp.connect(master); master.connect(ac.destination);

                    // Saturación fuerte compartida
                    const drive = ac.createWaveShaper(); drive.curve = makeDistortion(400); drive.oversample = '4x';
                    const tone = ac.createBiquadFilter(); tone.type = 'lowpass'; tone.frequency.value = 1800;
                    drive.connect(tone); tone.connect(comp);

                    // 1) Carga: barrido ascendente que zumba
                    const chOsc = ac.createOscillator(); chOsc.type = 'sawtooth';
                    chOsc.frequency.setValueAtTime(60, t0); chOsc.frequency.exponentialRampToValueAtTime(420, t0 + charge);
                    const chG = ac.createGain(); chG.gain.setValueAtTime(0.0001, t0); chG.gain.exponentialRampToValueAtTime(0.35, t0 + charge * 0.9); chG.gain.exponentialRampToValueAtTime(0.0001, t0 + charge + 0.08);
                    chOsc.connect(chG); chG.connect(drive); chOsc.start(t0); chOsc.stop(t0 + charge + 0.1);

                    // 2) Sub-bajos: dos sierras graves desafinadas con temblor (rugido)
                    const bassG = ac.createGain();
                    bassG.gain.setValueAtTime(0.0001, t0 + charge - 0.02);
                    bassG.gain.exponentialRampToValueAtTime(0.9, t0 + charge + 0.06);
                    bassG.gain.setValueAtTime(0.9, end - 0.1);
                    bassG.gain.exponentialRampToValueAtTime(0.0001, end + rel);
                    const trem = ac.createOscillator(); trem.frequency.value = 17;
                    const tremDepth = ac.createGain(); tremDepth.gain.value = 0.25;
                    trem.connect(tremDepth); tremDepth.connect(bassG.gain);
                    [41, 43.5, 82].forEach((f, i) => {
                        const o = ac.createOscillator(); o.type = i === 2 ? 'square' : 'sawtooth';
                        o.frequency.setValueAtTime(f * 1.25, t0 + charge); o.frequency.exponentialRampToValueAtTime(f, t0 + charge + 0.4);
                        o.frequency.exponentialRampToValueAtTime(f * 0.8, end + rel);
                        const g = ac.createGain(); g.gain.value = i === 2 ? 0.35 : 0.6;
                        o.connect(g); g.connect(bassG); o.start(t0 + charge - 0.02); o.stop(end + rel + 0.05);
                    });
                    bassG.connect(drive); trem.start(t0); trem.stop(end + rel + 0.05);

                    // 3) Chillido del rayo: tono medio con vibrato, filtrado
                    const scr = ac.createOscillator(); scr.type = 'sawtooth'; scr.frequency.value = 230;
                    const vib = ac.createOscillator(); vib.frequency.value = 7; const vibD = ac.createGain(); vibD.gain.value = 12;
                    vib.connect(vibD); vibD.connect(scr.frequency);
                    const bp = ac.createBiquadFilter(); bp.type = 'bandpass'; bp.frequency.value = 1100; bp.Q.value = 3;
                    const scrG = ac.createGain();
                    scrG.gain.setValueAtTime(0.0001, t0 + charge); scrG.gain.exponentialRampToValueAtTime(0.18, t0 + charge + 0.1);
                    scrG.gain.setValueAtTime(0.18, end - 0.1); scrG.gain.exponentialRampToValueAtTime(0.0001, end + rel * 0.6);
                    scr.connect(bp); bp.connect(scrG); scrG.connect(drive);
                    scr.start(t0 + charge); vib.start(t0 + charge); scr.stop(end + rel); vib.stop(end + rel);

                    // 4) Ruido crepitante grave (energía del rayo)
                    const len = Math.ceil(ac.sampleRate * (end + rel - t0));
                    const buf = ac.createBuffer(1, len, ac.sampleRate); const d = buf.getChannelData(0);
                    for (let i = 0; i < len; i++) d[i] = Math.random() * 2 - 1;
                    const nz = ac.createBufferSource(); nz.buffer = buf;
                    const nf = ac.createBiquadFilter(); nf.type = 'lowpass'; nf.frequency.value = 500;
                    const nG = ac.createGain();
                    nG.gain.setValueAtTime(0.0001, t0 + charge); nG.gain.exponentialRampToValueAtTime(0.5, t0 + charge + 0.05);
                    nG.gain.setValueAtTime(0.5, end - 0.1); nG.gain.exponentialRampToValueAtTime(0.0001, end + rel);
                    nz.connect(nf); nf.connect(nG); nG.connect(drive); nz.start(t0); nz.stop(end + rel);
                } catch (e) { console.log("Audio del rayo no disponible", e); }
            }

            // Distancia de un punto al segmento del rayo
            function distToBeam(px, py, x1, y1, x2, y2) {
                let vx = x2 - x1, vy = y2 - y1, len2 = vx * vx + vy * vy;
                let t = len2 > 0 ? Math.max(0, Math.min(1, ((px - x1) * vx + (py - y1) * vy) / len2)) : 0;
                return Math.hypot(px - (x1 + vx * t), py - (y1 + vy * t));
            }

            function beamWidth() { return 40 + player.r * 0.6; }

            function updateAbyssLaser() {
                if (abyssCooldown > 0 && abyssTimer <= 0) abyssCooldown--;
                if (abyssTimer <= 0) return;
                if (player.dead) { abyssTimer = 0; return; }
                abyssTimer--;
                abyssAngle = aimAngle(); // el rayo sigue al mouse
                let x1 = player.x, y1 = player.y;
                let x2 = x1 + Math.cos(abyssAngle) * ABYSS_LENGTH, y2 = y1 + Math.sin(abyssAngle) * ABYSS_LENGTH;
                let w = beamWidth() / 2;

                // El rayo borra los disparos enemigos que toca
                for (let i = lasers.length - 1; i >= 0; i--) {
                    let l = lasers[i];
                    if (l.owner !== player && distToBeam(l.x, l.y, x1, y1, x2, y2) < w) lasers.splice(i, 1);
                }

                if (abyssTimer % ABYSS_TICK === 0) {
                    let dmg = player.laserDamage;
                    bots.forEach(b => { if (!b.dead && distToBeam(b.x, b.y, x1, y1, x2, y2) < w + b.r) takeDamage(b, ABYSS_DMG_BOTS * dmg); });
                    if (meteor.isBoss && !meteor.dead && distToBeam(meteor.x, meteor.y, x1, y1, x2, y2) < w + meteor.r) {
                        meteor.hp -= ABYSS_DMG_BOSS * dmg;
                        floatingTexts.push({ x: meteor.x + (Math.random() - 0.5) * 80, y: meteor.y - meteor.r - 20, text: `-${Math.ceil(ABYSS_DMG_BOSS * dmg)}`, color: "#B266FF", life: 30, size: 26 });
                        if (meteor.hp <= 0 && !meteor.dead) {
                            meteor.dead = true; playSfx("bh_death", 2.5);
                            floatingTexts.push({ x: meteor.x, y: meteor.y, text: "VICTORIA GALÁCTICA", icon: "star", iconBoth: true, color: "#FFD700", life: 300, size: 50 }); onBossDefeated();
                            if (bgMusic && audioSrc) { bgMusic.pause(); bgMusic.src = audioSrc; usingBossTrack = false; bgMusic.currentTime = 0; bgMusic.play().catch(e => console.log(e)); }
                        }
                    }
                }
                // Chispas al final y a lo largo del rayo
                for (let i = 0; i < 3; i++) {
                    let t = Math.random();
                    particles.push({ x: x1 + (x2 - x1) * t, y: y1 + (y2 - y1) * t, vx: (Math.random() - 0.5) * 4, vy: (Math.random() - 0.5) * 4, color: Math.random() > 0.5 ? "#B266FF" : "#FFFFFF", life: 15 });
                }
            }

            function drawAbyssLaser() {
                if (abyssTimer <= 0 || player.dead) return;
                let x1 = player.x, y1 = player.y;
                let x2 = x1 + Math.cos(abyssAngle) * ABYSS_LENGTH, y2 = y1 + Math.sin(abyssAngle) * ABYSS_LENGTH;
                let w = beamWidth(), pulse = 1 + Math.sin(Date.now() / 40) * 0.15;
                let fade = Math.min(1, abyssTimer / 20);
                ctx.save(); ctx.lineCap = "round"; ctx.globalAlpha = fade;
                ctx.shadowColor = "#8A2BE2"; ctx.shadowBlur = 40;
                ctx.strokeStyle = "rgba(138, 43, 226, 0.35)"; ctx.lineWidth = w * 1.8 * pulse; ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
                ctx.strokeStyle = "#B266FF"; ctx.lineWidth = w * pulse; ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
                ctx.shadowBlur = 0;
                ctx.strokeStyle = "#FFFFFF"; ctx.lineWidth = w * 0.35 * pulse; ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
                ctx.restore();
            }

            // ======================================================
            // === HABILIDADES DE ORBES (niveles 1 a 10) ===
            //  X  Súper cañón   (orbe naranja)
            //  F  Empuje        (orbe naranja)
            //  Q  Piel de Rhino (orbe celeste)
            //  E  Escudo reflector (orbe celeste)
            // ======================================================
            let cannonShots = [];
            let pushHands = [];

            // Estadísticas según nivel (L = 1..10). Todo mejora al subir de nivel.
            const AB = {
                cannon: {
                    key: 'X', name: 'CAÑÓN', color: '#FF8C00',
                    cooldown: L => (10 - 0.5 * (L - 1)) * 60,      // 10 s -> 5,5 s
                    damagePct: L => 0.50 + 0.05 * (L - 1),         // 50% -> 95% de la vida del objetivo
                    massCost: L => 0.50 - 0.02 * (L - 1),          // 50% -> 32% de tu masa
                    radius: L => 28 + 3 * L,
                    life: L => 100 + 10 * L
                },
                push: {
                    key: 'F', name: 'EMPUJE', color: '#33FF66',
                    cooldown: L => (8 - 0.4 * (L - 1)) * 60,       // 8 s -> 4,4 s
                    distance: L => 250 * (1 + 0.1 * (L - 1)),      // "5 metros" = 250 px -> 475 px
                    reach: L => 300 + 20 * L,                      // hasta dónde llega la mano
                    damage: L => 8 * L
                },
                rhino: {
                    key: 'Q', name: 'RHINO', color: '#C0C4CE',
                    cooldown: L => (20 - 0.5 * (L - 1)) * 60,      // 20 s -> 15,5 s
                    duration: L => (5 + 0.3 * (L - 1)) * 60        // 5 s -> 7,7 s
                },
                reflect: {
                    key: 'E', name: 'REFLEJO', color: '#00FFFF',
                    cooldown: L => (15 - 0.5 * (L - 1)) * 60,      // 15 s -> 10,5 s
                    duration: L => (3 + 0.3 * (L - 1)) * 60,       // 3 s -> 5,7 s
                    reflectMult: L => 1 + 0.1 * L                  // las balas devueltas pegan más
                }
            };
            const AB_ORDER = ['cannon', 'push', 'rhino', 'reflect'];

            function resetAbilities() {
                player.cannonLvl = 0; player.pushLvl = 0; player.rhinoLvl = 0; player.reflectLvl = 0;
                player.abCd = { cannon: 0, push: 0, rhino: 0, reflect: 0 };
                player.rhinoTimer = 0; player.reflectTimer = 0; player.reflectFlash = 0;
            }

            function getAudioCtx() {
                if (!beamAudioCtx) beamAudioCtx = new (window.AudioContext || window.webkitAudioContext)();
                if (beamAudioCtx.state === 'suspended') beamAudioCtx.resume();
                return beamAudioCtx;
            }

            // Sonido sintetizado corto: tipo 'boom' (cañón), 'whoosh' (empuje), 'metal' (rhino), 'shield' (reflector), 'ping' (rebote)
            function playAbilitySfx(kind) {
                if (!isUserInteracted || sfxVolume === 0) return;
                try {
                    const ac = getAudioCtx(), t = ac.currentTime;
                    const out = ac.createGain(); out.gain.value = Math.min(1, sfxVolume); out.connect(ac.destination);
                    const env = (g, a, peak, d) => { g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(peak, t + a); g.gain.exponentialRampToValueAtTime(0.0001, t + a + d); };
                    const noise = (dur) => {
                        const len = Math.ceil(ac.sampleRate * dur), b = ac.createBuffer(1, len, ac.sampleRate), d = b.getChannelData(0);
                        for (let i = 0; i < len; i++) d[i] = Math.random() * 2 - 1;
                        const src = ac.createBufferSource(); src.buffer = b; return src;
                    };
                    if (kind === 'boom') {
                        const o = ac.createOscillator(); o.type = 'sine'; o.frequency.setValueAtTime(140, t); o.frequency.exponentialRampToValueAtTime(30, t + 0.6);
                        const g = ac.createGain(); env(g, 0.01, 1.0, 0.7); o.connect(g); g.connect(out); o.start(t); o.stop(t + 0.8);
                        const ws = ac.createWaveShaper(); ws.curve = makeDistortion(200);
                        const n = noise(0.6), f = ac.createBiquadFilter(); f.type = 'lowpass'; f.frequency.value = 700;
                        const gn = ac.createGain(); env(gn, 0.005, 0.6, 0.5); n.connect(f); f.connect(ws); ws.connect(gn); gn.connect(out); n.start(t);
                    } else if (kind === 'whoosh') {
                        const n = noise(0.6), f = ac.createBiquadFilter(); f.type = 'bandpass'; f.Q.value = 1.5;
                        f.frequency.setValueAtTime(300, t); f.frequency.exponentialRampToValueAtTime(2500, t + 0.35);
                        const g = ac.createGain(); env(g, 0.05, 0.8, 0.45); n.connect(f); f.connect(g); g.connect(out); n.start(t);
                        const o = ac.createOscillator(); o.type = 'triangle'; o.frequency.setValueAtTime(220, t); o.frequency.exponentialRampToValueAtTime(660, t + 0.3);
                        const go = ac.createGain(); env(go, 0.03, 0.25, 0.35); o.connect(go); go.connect(out); o.start(t); o.stop(t + 0.45);
                    } else if (kind === 'metal') {
                        [180, 271, 397].forEach(fq => {
                            const o = ac.createOscillator(); o.type = 'square'; o.frequency.value = fq;
                            const g = ac.createGain(); env(g, 0.005, 0.18, 0.6); o.connect(g); g.connect(out); o.start(t); o.stop(t + 0.7);
                        });
                        const o2 = ac.createOscillator(); o2.type = 'sine'; o2.frequency.setValueAtTime(90, t); o2.frequency.exponentialRampToValueAtTime(45, t + 0.4);
                        const g2 = ac.createGain(); env(g2, 0.005, 0.7, 0.4); o2.connect(g2); g2.connect(out); o2.start(t); o2.stop(t + 0.5);
                    } else if (kind === 'shield') {
                        const o = ac.createOscillator(); o.type = 'sine'; o.frequency.setValueAtTime(400, t); o.frequency.exponentialRampToValueAtTime(1200, t + 0.25);
                        const g = ac.createGain(); env(g, 0.02, 0.35, 0.4); o.connect(g); g.connect(out); o.start(t); o.stop(t + 0.5);
                    } else if (kind === 'ping') {
                        const o = ac.createOscillator(); o.type = 'triangle'; o.frequency.setValueAtTime(1400, t); o.frequency.exponentialRampToValueAtTime(900, t + 0.08);
                        const g = ac.createGain(); env(g, 0.003, 0.12, 0.1); o.connect(g); g.connect(out); o.start(t); o.stop(t + 0.15);
                    }
                } catch (e) { console.log("SFX habilidad no disponible", e); }
            }

            // Daño directo (sin reducción por tamaño) para estrellas enemigas
            function hurtStar(t, amount, color) {
                if (!t || t.dead || t === player) return;
                t.hp -= amount;
                floatingTexts.push({ x: t.x, y: t.y - t.r - 10, text: `-${Math.ceil(amount)}`, color: color || "#FF8C00", life: 35, size: 26 });
                if (t.hp <= 0) { t.dead = true; dropMass(t); floatingTexts.push({ x: t.x, y: t.y, text: "¡DESTRUIDO!", icon: "burst", color: "#FF3333", life: 40, size: 22 }); }
            }
            function damageMeteor(amount, color) {
                if (!meteor.isBoss || meteor.dead) return;
                meteor.hp -= amount;
                floatingTexts.push({ x: meteor.x + (Math.random() - 0.5) * 80, y: meteor.y - meteor.r - 20, text: `-${Math.ceil(amount)}`, color: color || "#FF8C00", life: 40, size: 30 });
                if (meteor.hp <= 0 && !meteor.dead) {
                    meteor.dead = true; playSfx("bh_death", 2.5);
                    floatingTexts.push({ x: meteor.x, y: meteor.y, text: "VICTORIA GALÁCTICA", icon: "star", iconBoth: true, color: "#FFD700", life: 300, size: 50 }); onBossDefeated();
                    if (bgMusic && audioSrc) { bgMusic.pause(); bgMusic.src = audioSrc; usingBossTrack = false; bgMusic.currentTime = 0; bgMusic.play().catch(e => console.log(e)); }
                }
            }
            function damageBlackHole(amount, color) {
                if (blackHole.dead) return;
                blackHole.hp -= amount;
                floatingTexts.push({ x: blackHole.x + (Math.random() - 0.5) * 60, y: blackHole.y - blackHole.r - 20, text: `-${Math.ceil(amount)}`, color: color || "#FF8C00", life: 40, size: 30 });
                if (blackHole.hp <= 0 && !blackHole.dead) {
                    blackHole.dead = true; unlockAbyssLaser();
                    playSfx("bh_death", 2.5);
                    meteor.isBoss = true; cinematicTimer = 180;
                    if (bgMusic && sfxData["luna_musica"] && sfxData["luna_musica"].length > 0) {
                        bgMusic.pause(); bgMusic.src = sfxData["luna_musica"][0]; usingBossTrack = true; bgMusic.currentTime = 0; bgMusic.play().catch(e => console.log(e));
                    }
                    floatingTexts.push({ x: meteor.x, y: meteor.y - 120, text: "LA LUNA DESPIERTA", icon: "warning", iconBoth: true, color: "#FF4500", life: 180, size: 40 });
                }
            }

            function useAbility(id) {
                if (gameState !== 'playing' || isPaused || !player || player.dead || cinematicTimer > 0) return;
                let L = player[id + 'Lvl'] || 0;
                if (L <= 0) return;
                if (player.abCd[id] > 0) {
                    floatingTexts.push({ x: player.x, y: player.y - player.r - 25, text: `${AB[id].name}: ${Math.ceil(player.abCd[id] / 60)}s`, color: "#888", life: 30, size: 14 });
                    return;
                }
                let ang = aimAngle();

                if (id === 'cannon') {
                    if (player.r < 20 && !player.rissos) {
                        floatingTexts.push({ x: player.x, y: player.y - player.r - 25, text: "MUY PEQUEÑO PARA EL CAÑÓN", color: "#FF8C00", life: 40, size: 14 });
                        return;
                    }
                    if (!player.rissos) player.r = Math.max(10, player.r * (1 - AB.cannon.massCost(L)));
                    let rad = AB.cannon.radius(L), sp = 11;
                    let offsets = player.doubleCannon ? [-1, 1] : [0];   // Ninja: dos balas paralelas
                    offsets.forEach(o => {
                        let ox = -Math.sin(ang) * o * (rad + 4), oy = Math.cos(ang) * o * (rad + 4);
                        cannonShots.push({ x: player.x + Math.cos(ang) * (player.r + rad) + ox, y: player.y + Math.sin(ang) * (player.r + rad) + oy,
                            vx: Math.cos(ang) * sp, vy: Math.sin(ang) * sp, r: rad, life: AB.cannon.life(L), pct: AB.cannon.damagePct(L), hitSet: new Set() });
                    });
                    // retroceso
                    player.x -= Math.cos(ang) * 25; player.y -= Math.sin(ang) * 25;
                    for (let k = 0; k < 25; k++) particles.push({ x: player.x, y: player.y, vx: Math.cos(ang + (Math.random() - 0.5)) * Math.random() * 8, vy: Math.sin(ang + (Math.random() - 0.5)) * Math.random() * 8, color: Math.random() > 0.5 ? "#FF8C00" : "#FFD27A", life: 25 });
                    playAbilitySfx('boom');
                    floatingTexts.push({ x: player.x, y: player.y - player.r - 30, text: "¡SÚPER CAÑÓN!", color: "#FF8C00", life: 45, size: 22 });
                }
                else if (id === 'push') {
                    let reach = AB.push.reach(L), dist = AB.push.distance(L), cone = 0.65;
                    pushHands.push({ angle: ang, t: 0, dur: 28, reach: reach });
                    const tryPush = (obj, mult, radius) => {
                        let dx = obj.x - player.x, dy = obj.y - player.y, d = Math.hypot(dx, dy);
                        if (d - radius > reach) return false;
                        let diff = Math.atan2(dy, dx) - ang;
                        diff = Math.atan2(Math.sin(diff), Math.cos(diff));
                        if (Math.abs(diff) > cone && d > player.r + radius) return false;
                        let a = d > 0 ? Math.atan2(dy, dx) : ang;
                        let v = (dist * mult) / 10;  // con fricción 0.9, recorre ~ 10 veces la velocidad inicial
                        obj.kbx = Math.cos(a) * v; obj.kby = Math.sin(a) * v;
                        for (let k = 0; k < 10; k++) particles.push({ x: obj.x, y: obj.y, vx: Math.cos(a) * Math.random() * 6, vy: Math.sin(a) * Math.random() * 6, color: "#33FF66", life: 20 });
                        return true;
                    };
                    bots.forEach(b => { if (!b.dead && tryPush(b, 1, b.r)) hurtStar(b, AB.push.damage(L), "#33FF66"); });
                    if (!blackHole.dead && tryPush(blackHole, 1, blackHole.r)) floatingTexts.push({ x: blackHole.x, y: blackHole.y - blackHole.r - 30, text: "¡EMPUJADO!", color: "#33FF66", life: 40, size: 20 });
                    if (meteor.isBoss && !meteor.dead && tryPush(meteor, 0.5, meteor.r)) damageMeteor(AB.push.damage(L) * 3, "#33FF66");
                    // también aparta las balas enemigas
                    lasers.forEach(l => {
                        if (l.owner === player) return;
                        let dx = l.x - player.x, dy = l.y - player.y, d = Math.hypot(dx, dy);
                        let diff = Math.atan2(Math.sin(Math.atan2(dy, dx) - ang), Math.cos(Math.atan2(dy, dx) - ang));
                        if (d < reach && Math.abs(diff) < cone) { let sp = Math.hypot(l.vx, l.vy); l.vx = Math.cos(ang) * sp; l.vy = Math.sin(ang) * sp; l.owner = player; l.color = "#33FF66"; }
                    });
                    playAbilitySfx('whoosh');
                }
                else if (id === 'rhino') {
                    player.rhinoTimer = AB.rhino.duration(L);
                    playAbilitySfx('metal');
                    floatingTexts.push({ x: player.x, y: player.y - player.r - 30, text: "¡PIEL DE RHINO!", icon: "shield", iconBoth: true, color: "#C0C4CE", life: 50, size: 22 });
                }
                else if (id === 'reflect') {
                    player.reflectTimer = AB.reflect.duration(L);
                    playAbilitySfx('shield');
                    floatingTexts.push({ x: player.x, y: player.y - player.r - 30, text: "¡ESCUDO REFLECTOR!", color: "#00FFFF", life: 50, size: 22 });
                }
                player.abCd[id] = AB[id].cooldown(L);
            }

            // Devuelve una bala enemiga hacia donde vino
            function reflectLaser(l) {
                let L = player.reflectLvl || 1;
                let sp = Math.hypot(l.vx, l.vy) * 1.3;
                let a = Math.atan2(l.vy, l.vx) + Math.PI + (Math.random() - 0.5) * 0.3;
                l.vx = Math.cos(a) * sp; l.vy = Math.sin(a) * sp;
                l.owner = player; l.color = "#00FFFF"; l.life = Math.max(l.life, 80);
                l.damageMult = (l.damageMult || 1) * AB.reflect.reflectMult(L);
                l.x += l.vx * 2; l.y += l.vy * 2;
                player.reflectFlash = 8;
                for (let k = 0; k < 6; k++) particles.push({ x: l.x, y: l.y, vx: (Math.random() - 0.5) * 5, vy: (Math.random() - 0.5) * 5, color: "#00FFFF", life: 14 });
                if (Math.random() < 0.5) playAbilitySfx('ping');
            }

            function applyKnockback(o) {
                if (!o || (!o.kbx && !o.kby)) return;
                o.x += o.kbx; o.y += o.kby; o.kbx *= 0.9; o.kby *= 0.9;
                if (Math.abs(o.kbx) < 0.05 && Math.abs(o.kby) < 0.05) { o.kbx = 0; o.kby = 0; }
                o.x = Math.max(o.r, Math.min(worldW - o.r, o.x)); o.y = Math.max(o.r, Math.min(worldH - o.r, o.y));
            }

            function updateAbilities() {
                if (!player.abCd) resetAbilities();
                AB_ORDER.forEach(id => { if (player.abCd[id] > 0) player.abCd[id]--; });
                if (player.rhinoTimer > 0) player.rhinoTimer--;
                if (player.reflectTimer > 0) player.reflectTimer--;
                if (player.reflectFlash > 0) player.reflectFlash--;

                bots.forEach(applyKnockback); applyKnockback(player);
                if (!blackHole.dead) applyKnockback(blackHole);
                if (meteor.isBoss && !meteor.dead) applyKnockback(meteor);

                for (let i = pushHands.length - 1; i >= 0; i--) { pushHands[i].t++; if (pushHands[i].t >= pushHands[i].dur) pushHands.splice(i, 1); }

                for (let i = cannonShots.length - 1; i >= 0; i--) {
                    let c = cannonShots[i]; c.x += c.vx; c.y += c.vy; c.life--; let done = false;
                    if (Math.random() < 0.8) particles.push({ x: c.x - c.vx * 2 + (Math.random() - 0.5) * c.r, y: c.y - c.vy * 2 + (Math.random() - 0.5) * c.r, vx: -c.vx * 0.2, vy: -c.vy * 0.2, color: Math.random() > 0.5 ? "#FF8C00" : "#FFD27A", life: 18 });
                    // borra balas enemigas que toca
                    for (let j = lasers.length - 1; j >= 0; j--) { let l = lasers[j]; if (l.owner !== player && Math.hypot(l.x - c.x, l.y - c.y) < c.r) lasers.splice(j, 1); }
                    // atraviesa estrellas: % de su vida máxima
                    bots.forEach(b => {
                        if (b.dead || c.hitSet.has(b)) return;
                        if (Math.hypot(b.x - c.x, b.y - c.y) < b.r + c.r) { c.hitSet.add(b); hurtStar(b, b.maxHp * c.pct, "#FF8C00"); }
                    });
                    // jefes: se detiene y hace 1/5 del porcentaje
                    if (!blackHole.dead && Math.hypot(blackHole.x - c.x, blackHole.y - c.y) < blackHole.r + c.r) { damageBlackHole(blackHole.maxHp * c.pct * 0.2); done = true; }
                    if (!done && meteor.isBoss && !meteor.dead && Math.hypot(meteor.x - c.x, meteor.y - c.y) < meteor.r + c.r) { damageMeteor(meteor.maxHp * c.pct * 0.2); done = true; }
                    if (c.x < -c.r || c.y < -c.r || c.x > worldW + c.r || c.y > worldH + c.r) c.life = 0;
                    if (done || c.life <= 0) {
                        for (let k = 0; k < 30; k++) particles.push({ x: c.x, y: c.y, vx: (Math.random() - 0.5) * 12, vy: (Math.random() - 0.5) * 12, color: Math.random() > 0.5 ? "#FF8C00" : "#FFFFFF", life: 25 });
                        if (done) playAbilitySfx('boom');
                        cannonShots.splice(i, 1);
                    }
                }
            }

            // Mano verde estilo Linterna Verde (dedos apuntando hacia +x)
            function drawGreenHand(x, y, angle, size, alpha) {
                ctx.save(); ctx.translate(x, y); ctx.rotate(angle); ctx.globalAlpha = alpha;
                ctx.lineCap = "round"; ctx.lineJoin = "round";
                const fingers = [[-0.24, 0.30], [-0.08, 0.40], [0.08, 0.38], [0.23, 0.28]];
                const shape = (w, color) => {
                    ctx.strokeStyle = color; ctx.lineWidth = w;
                    ctx.beginPath(); ctx.rect(-size * 0.5, -size * 0.28, size * 0.5, size * 0.56); ctx.stroke();
                    fingers.forEach(f => { ctx.beginPath(); ctx.moveTo(0, f[0] * size); ctx.lineTo(f[1] * size, f[0] * size); ctx.stroke(); });
                    ctx.beginPath(); ctx.moveTo(-size * 0.3, -size * 0.3); ctx.lineTo(-size * 0.05, -size * 0.5); ctx.stroke();
                };
                ctx.shadowColor = "#33FF66"; ctx.shadowBlur = 30;
                shape(size * 0.17, "#33FF66");
                ctx.shadowBlur = 0;
                shape(size * 0.11, "rgba(170, 255, 190, 0.85)");
                ctx.fillStyle = "rgba(51, 255, 102, 0.35)"; ctx.fillRect(-size * 0.5, -size * 0.28, size * 0.5, size * 0.56);
                // muñeca y anillo
                ctx.strokeStyle = "#33FF66"; ctx.lineWidth = size * 0.06;
                ctx.beginPath(); ctx.moveTo(-size * 0.62, -size * 0.2); ctx.lineTo(-size * 0.62, size * 0.2); ctx.stroke();
                ctx.restore();
            }

            function drawAbilitiesWorld() {
                // Balas del cañón
                cannonShots.forEach(c => {
                    ctx.save();
                    let g = ctx.createRadialGradient(c.x - c.r * 0.3, c.y - c.r * 0.3, c.r * 0.1, c.x, c.y, c.r);
                    g.addColorStop(0, "#FFFFFF"); g.addColorStop(0.35, "#FFD27A"); g.addColorStop(0.8, "#FF8C00"); g.addColorStop(1, "rgba(255,80,0,0.6)");
                    ctx.shadowColor = "#FF8C00"; ctx.shadowBlur = 40; ctx.fillStyle = g;
                    ctx.beginPath(); ctx.arc(c.x, c.y, c.r, 0, Math.PI * 2); ctx.fill();
                    ctx.restore();
                });
                if (player.dead) return;
                // Manos de empuje
                pushHands.forEach(h => {
                    let p = h.t / h.dur, ease = 1 - Math.pow(1 - Math.min(1, p * 1.6), 3);
                    let d = player.r + ease * h.reach * 0.75;
                    let size = 60 + player.r * 1.2 + ease * 40;
                    let alpha = p < 0.7 ? 1 : 1 - (p - 0.7) / 0.3;
                    // estela de energía desde el jugador
                    ctx.save(); ctx.globalAlpha = alpha * 0.5; ctx.strokeStyle = "#33FF66"; ctx.lineWidth = size * 0.25; ctx.lineCap = "round";
                    ctx.beginPath(); ctx.moveTo(player.x, player.y); ctx.lineTo(player.x + Math.cos(h.angle) * (d - size * 0.6), player.y + Math.sin(h.angle) * (d - size * 0.6)); ctx.stroke(); ctx.restore();
                    drawGreenHand(player.x + Math.cos(h.angle) * d, player.y + Math.sin(h.angle) * d, h.angle, size, alpha);
                });
            }

            // Se dibuja encima de la estrella del jugador
            function drawPlayerShields() {
                if (player.dead) return;
                if (player.rhinoTimer > 0) {
                    ctx.save(); ctx.translate(player.x, player.y); ctx.rotate(Date.now() / 900);
                    let R = player.r * 1.35 + 6, blink = player.rhinoTimer < 60 && Math.floor(player.rhinoTimer / 6) % 2 === 0;
                    ctx.globalAlpha = blink ? 0.35 : 1;
                    ctx.beginPath();
                    for (let i = 0; i < 6; i++) { let a = (Math.PI / 3) * i; ctx.lineTo(Math.cos(a) * R, Math.sin(a) * R); }
                    ctx.closePath(); ctx.fillStyle = "rgba(150, 155, 170, 0.35)"; ctx.fill();
                    ctx.strokeStyle = "#E0E3EA"; ctx.lineWidth = Math.max(3, player.r * 0.12); ctx.shadowColor = "#FFD700"; ctx.shadowBlur = 15; ctx.stroke();
                    ctx.shadowBlur = 0; ctx.strokeStyle = "rgba(255, 215, 0, 0.8)"; ctx.lineWidth = 2;
                    for (let i = 0; i < 6; i++) { let a = (Math.PI / 3) * i; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(Math.cos(a) * R, Math.sin(a) * R); ctx.stroke(); }
                    ctx.restore();
                }
                if (player.reflectTimer > 0) {
                    ctx.save(); ctx.translate(player.x, player.y);
                    let R = player.r * 1.7 + 10, blink = player.reflectTimer < 60 && Math.floor(player.reflectTimer / 6) % 2 === 0;
                    ctx.globalAlpha = blink ? 0.3 : 1;
                    ctx.fillStyle = player.reflectFlash > 0 ? "rgba(0, 255, 255, 0.3)" : "rgba(0, 255, 255, 0.08)";
                    ctx.beginPath(); ctx.arc(0, 0, R, 0, Math.PI * 2); ctx.fill();
                    ctx.rotate(-Date.now() / 400); ctx.setLineDash([14, 10]);
                    ctx.strokeStyle = "#00FFFF"; ctx.lineWidth = 3 + (player.reflectFlash > 0 ? 3 : 0); ctx.shadowColor = "#00FFFF"; ctx.shadowBlur = 20;
                    ctx.beginPath(); ctx.arc(0, 0, R, 0, Math.PI * 2); ctx.stroke();
                    ctx.restore();
                }
            }

            // Barra de habilidades abajo al centro
            function drawAbilityBar() {
                if (!player.abCd) return;
                let owned = AB_ORDER.filter(id => (player[id + 'Lvl'] || 0) > 0);
                if (owned.length === 0) return;
                const S = 62, gap = 10, total = owned.length * S + (owned.length - 1) * gap;
                let x0 = (canvas.width - total) / 2, y0 = canvas.height - S - 14;
                ctx.save();
                owned.forEach((id, i) => {
                    let x = x0 + i * (S + gap), a = AB[id], L = player[id + 'Lvl'], cd = player.abCd[id];
                    let active = (id === 'rhino' && player.rhinoTimer > 0) || (id === 'reflect' && player.reflectTimer > 0);
                    ctx.fillStyle = "rgba(10, 10, 20, 0.85)"; ctx.fillRect(x, y0, S, S);
                    if (cd > 0 && !active) {
                        let frac = cd / a.cooldown(L);
                        ctx.fillStyle = "rgba(0, 0, 0, 0.55)"; ctx.fillRect(x, y0 + S * (1 - frac), S, S * frac);
                    }
                    ctx.strokeStyle = active ? "#FFFFFF" : (cd > 0 ? "#444" : a.color); ctx.lineWidth = active ? 3 : 2;
                    if (!active && cd <= 0) { ctx.shadowColor = a.color; ctx.shadowBlur = 10; }
                    ctx.strokeRect(x, y0, S, S); ctx.shadowBlur = 0;
                    ctx.textAlign = "left"; ctx.font = "bold 13px sans-serif"; ctx.fillStyle = "#FFFFFF"; ctx.fillText(a.key, x + 5, y0 + 15);
                    ctx.textAlign = "right"; ctx.font = "bold 10px sans-serif"; ctx.fillStyle = "#FFD700"; ctx.fillText(L >= 10 ? "MÁX" : "Nv" + L, x + S - 4, y0 + 14);
                    ctx.textAlign = "center"; ctx.font = "bold 10px sans-serif"; ctx.fillStyle = a.color; ctx.fillText(a.name, x + S / 2, y0 + S - 7);
                    ctx.font = "bold 16px sans-serif"; ctx.fillStyle = "#FFFFFF";
                    let mid = active ? ((id === 'rhino' ? player.rhinoTimer : player.reflectTimer) / 60).toFixed(1) + "s" : (cd > 0 ? Math.ceil(cd / 60) + "s" : "LISTO");
                    if (mid === "LISTO") { ctx.font = "bold 12px sans-serif"; ctx.fillStyle = a.color; }
                    ctx.fillText(mid, x + S / 2, y0 + S / 2 + 6);
                });
                ctx.restore();
            }

            // ======================================================
            // === PERSONAJES Y SPRINT ===
            // ======================================================
            const STAMINA_MAX = 100;
            const STAMINA_DRAIN = 0.8;    // por frame mientras corres (~2 s de sprint)
            const STAMINA_REGEN = 0.4;    // por frame al descansar (~4 s para llenar)
            const SPRINT_MULT = 1.6;      // cuánto más rápido vas con SHIFT
            const GODZILLA_HIT = 22;      // daño de una bala normal (para "10 golpes")

            const CHARACTERS = {
                normal: {
                    name: 'NORMAL', color: '#FFFFFF', stats: [3, 3, 3],
                    perk: 'La estrella estable. Sin ventajas ni desventajas.'
                },
                juggernaut: {
                    name: 'JUGGERNAUT', color: '#FF7A30', stats: [5, 1, 5],
                    perk: 'Muchísima vida y mucho daño, pero muy lento.'
                },
                ninja: {
                    name: 'NINJA', color: '#B266FF', stats: [1, 5, 3],
                    perk: 'Súper rápido y con muy poca vida. Empieza con el Súper Cañón DOBLE [X].'
                },
                godzilla: {
                    name: 'MINI GODZILLA', color: '#33FF66', stats: [3, 2, 4],
                    perk: 'Láser abismal [R] desbloqueado desde el inicio, pero cada uso te deja a 10 golpes de morir.'
                },
                nightmare: {
                    name: 'NIGHTMARE STAR', color: '#FF0040', stats: [0, 6, 6],
                    perk: 'Velocidad luz. Mata lo que toca. 1 vida y un solo golpe te mata. Agujero negro: 2 toques. Luna roja: 3 toques.'
                }
            };
            let selectedCharacter = 'normal';

            function applyCharacter(isNewGame) {
                const id = selectedCharacter;
                player.character = id;
                player.color = CHARACTERS[id].color;
                player.stamina = STAMINA_MAX; player.exhausted = false; player.staminaDelay = 0;
                player.nightmare = false; player.doubleCannon = false; player.nmCd = 0;
                player.speed = 3.5;

                if (id === 'juggernaut') {
                    player.hp = 650; player.maxHp = 650; player.speed = 1.9; player.laserDamage = 2.5; player.r = 24;
                } else if (id === 'ninja') {
                    player.hp = 60; player.maxHp = 60; player.speed = 6.5;
                    player.cannonLvl = Math.max(1, player.cannonLvl || 0); player.doubleCannon = true;
                } else if (id === 'godzilla') {
                    player.hp = 300; player.maxHp = 300; player.speed = 3.2;
                    abyssUnlocked = true;
                } else if (id === 'nightmare') {
                    player.hp = 1; player.maxHp = 1; player.shields = 0; player.speed = 12;
                    player.nightmare = true;
                    if (isNewGame) playerLives = 1;
                }
            }

            // Nightmare Star: mata al tocar, rebota contra los jefes y los vence a toques
            function updateNightmare() {
                if (!player.nightmare || player.dead) return;
                if (player.nmCd > 0) player.nmCd--;
                player.shields = 0;
                if (Math.random() < 0.9) particles.push({ x: player.x + (Math.random() - 0.5) * player.r, y: player.y + (Math.random() - 0.5) * player.r, vx: 0, vy: 0, color: Math.random() > 0.4 ? "#FF0040" : "#330010", life: 22 });

                bots.forEach(b => {
                    if (b.dead || Math.hypot(b.x - player.x, b.y - player.y) > player.r + b.r) return;
                    b.dead = true; dropMass(b); player.r += 0.8;
                    for (let k = 0; k < 14; k++) particles.push({ x: b.x, y: b.y, vx: (Math.random() - 0.5) * 9, vy: (Math.random() - 0.5) * 9, color: "#FF0040", life: 22 });
                    floatingTexts.push({ x: b.x, y: b.y, text: "¡ANIQUILADO!", icon: "burst", color: "#FF0040", life: 40, size: 20 });
                });

                const bounceFrom = (obj) => {
                    let a = Math.atan2(player.y - obj.y, player.x - obj.x);
                    player.kbx = Math.cos(a) * 16; player.kby = Math.sin(a) * 16;
                    player.x = obj.x + Math.cos(a) * (obj.r * 0.85 + player.r + 2);
                    player.y = obj.y + Math.sin(a) * (obj.r * 0.85 + player.r + 2);
                };
                const touchBoss = (obj, needed, damageFn, label) => {
                    obj.nmHits = (obj.nmHits || 0) + 1;
                    let dmg = obj.nmHits >= needed ? obj.hp + 1 : obj.maxHp / needed;
                    damageFn(dmg, "#FF0040");
                    playAbilitySfx('boom');
                    floatingTexts.push({ x: obj.x, y: obj.y - obj.r - 50, text: `${label} ${Math.min(obj.nmHits, needed)}/${needed}`, color: "#FF0040", life: 60, size: 28 });
                    player.nmCd = 40;
                };

                if (!blackHole.dead && Math.hypot(blackHole.x - player.x, blackHole.y - player.y) < player.r + blackHole.r * 0.85) {
                    if (player.nmCd <= 0) touchBoss(blackHole, 2, damageBlackHole, "TOQUE");
                    if (!blackHole.dead) bounceFrom(blackHole);
                }
                if (!meteor.dead && Math.hypot(meteor.x - player.x, meteor.y - player.y) < player.r + meteor.r * 0.85) {
                    if (meteor.isBoss && player.nmCd <= 0 && cinematicTimer <= 0) touchBoss(meteor, 3, damageMeteor, "TOQUE");
                    if (!meteor.dead) bounceFrom(meteor);
                }
            }

            // Pantalla de selección
            const charSelect = document.getElementById('char-select');
            const charGrid = document.getElementById('char-grid');
            function charStarSvg(color) {
                return '<svg viewBox="0 0 48 48" width="70" height="70"><polygon points="24.00,2.00 29.29,16.72 44.92,17.20 32.56,26.78 36.93,41.80 24.00,33.00 11.07,41.80 15.44,26.78 3.08,17.20 18.71,16.72" fill="' + color + '" stroke="#FFFFFF" stroke-width="1.4" stroke-linejoin="round" style="filter: drop-shadow(0 0 6px ' + color + ');"/></svg>';
            }
            function pipsHtml(n, color) {
                let h = '<span class="pips">';
                for (let i = 1; i <= 5; i++) h += '<span class="pip" style="background:' + (i <= n ? color : '#2a3344') + (n > 5 && i <= 5 ? ';box-shadow:0 0 6px ' + color : '') + '"></span>';
                return h + '</span>';
            }
            function buildCharCards() {
                charGrid.innerHTML = '';
                Object.keys(CHARACTERS).forEach(id => {
                    const c = CHARACTERS[id];
                    const card = document.createElement('button');
                    card.className = 'char-card';
                    card.style.borderColor = c.color;
                    card.style.boxShadow = id === selectedCharacter ? '0 0 18px ' + c.color : 'none';
                    card.innerHTML = charStarSvg(c.color) +
                        '<div class="char-name" style="color:' + c.color + '">' + c.name + '</div>' +
                        '<div class="char-stats">' +
                            '<div class="char-stat"><span>VIDA</span>' + pipsHtml(c.stats[0], c.color) + '</div>' +
                            '<div class="char-stat"><span>VELOCIDAD</span>' + pipsHtml(c.stats[1], c.color) + '</div>' +
                            '<div class="char-stat"><span>DAÑO</span>' + pipsHtml(c.stats[2], c.color) + '</div>' +
                        '</div>' +
                        '<div class="char-perk">' + c.perk + '</div>';
                    card.addEventListener('click', () => {
                        selectedCharacter = id;
                        charSelect.style.display = 'none';
                        startGame();
                    });
                    charGrid.appendChild(card);
                });
            }
            function openCharSelect() {
                buildCharCards();
                charSelect.style.display = 'flex';
            }

            // ======================================================
            // === SONIDO DE MUERTE ("END") Y MÚSICA DE VICTORIA ===
            // Todo se sintetiza en el navegador: composición original, sin copyright.
            // ======================================================
            const midiHz = m => 440 * Math.pow(2, (m - 69) / 12);

            function makeReverb(ac, seconds, decay) {
                const len = Math.ceil(ac.sampleRate * seconds), buf = ac.createBuffer(2, len, ac.sampleRate);
                for (let ch = 0; ch < 2; ch++) { const d = buf.getChannelData(ch); for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / len, decay); }
                const c = ac.createConvolver(); c.buffer = buf; return c;
            }

            // final = true cuando ya no quedan vidas (fin de la partida)
            function playEndSfx(final) {
                if (!isUserInteracted || sfxVolume === 0) return;
                try {
                    const ac = getAudioCtx(), t = ac.currentTime;
                    const out = ac.createGain(); out.gain.value = Math.min(1, sfxVolume * 1.2);
                    const comp = ac.createDynamicsCompressor(); comp.threshold.value = -12; comp.ratio.value = 5;
                    const rev = makeReverb(ac, final ? 3.5 : 2, 2.5), wet = ac.createGain(); wet.gain.value = 0.35;
                    out.connect(comp); comp.connect(ac.destination); out.connect(rev); rev.connect(wet); wet.connect(comp);

                    // Golpe grave de impacto
                    const boom = ac.createOscillator(); boom.type = 'sine';
                    boom.frequency.setValueAtTime(110, t); boom.frequency.exponentialRampToValueAtTime(28, t + 0.9);
                    const bg = ac.createGain(); bg.gain.setValueAtTime(0.9, t); bg.gain.exponentialRampToValueAtTime(0.0001, t + 1.1);
                    boom.connect(bg); bg.connect(out); boom.start(t); boom.stop(t + 1.2);

                    // Notas descendentes tipo "game over" (sierras filtradas, sonido de sintetizador retro)
                    const notes = final ? [69, 65, 62, 57, 50] : [67, 63, 60];
                    const step = final ? 0.32 : 0.22;
                    notes.forEach((m, i) => {
                        const st = t + 0.12 + i * step, last = i === notes.length - 1, dur = last ? (final ? 2.4 : 0.9) : step * 1.1;
                        [0, 7].forEach(det => {
                            const o = ac.createOscillator(); o.type = 'sawtooth'; o.frequency.value = midiHz(m); o.detune.value = det;
                            if (last) o.frequency.exponentialRampToValueAtTime(midiHz(m) * 0.94, st + dur);   // la última nota se "cae"
                            const f = ac.createBiquadFilter(); f.type = 'lowpass'; f.frequency.setValueAtTime(2200, st); f.frequency.exponentialRampToValueAtTime(400, st + dur);
                            const g = ac.createGain(); g.gain.setValueAtTime(0.0001, st); g.gain.exponentialRampToValueAtTime(0.16, st + 0.02); g.gain.setValueAtTime(0.16, st + dur * 0.6); g.gain.exponentialRampToValueAtTime(0.0001, st + dur);
                            o.connect(f); f.connect(g); g.connect(out); o.start(st); o.stop(st + dur + 0.05);
                        });
                        // octava grave para darle peso
                        const sub = ac.createOscillator(); sub.type = 'triangle'; sub.frequency.value = midiHz(m - 24);
                        const sg = ac.createGain(); sg.gain.setValueAtTime(0.0001, st); sg.gain.exponentialRampToValueAtTime(0.25, st + 0.02); sg.gain.exponentialRampToValueAtTime(0.0001, st + dur);
                        sub.connect(sg); sg.connect(out); sub.start(st); sub.stop(st + dur + 0.05);
                    });

                    if (final) {
                        // Acorde menor oscuro que queda sonando al final
                        const ct = t + 0.12 + notes.length * step;
                        [38, 45, 50, 53].forEach(m => {
                            const o = ac.createOscillator(); o.type = 'sawtooth'; o.frequency.value = midiHz(m);
                            const f = ac.createBiquadFilter(); f.type = 'lowpass'; f.frequency.value = 700;
                            const g = ac.createGain(); g.gain.setValueAtTime(0.0001, ct); g.gain.exponentialRampToValueAtTime(0.09, ct + 0.3); g.gain.exponentialRampToValueAtTime(0.0001, ct + 3);
                            o.connect(f); f.connect(g); g.connect(out); o.start(ct); o.stop(ct + 3.1);
                        });
                    }
                } catch (e) { console.log("Sonido de muerte no disponible", e); }
            }

            // --- Música épica de victoria (al vencer al jefe del último nivel) ---
            let victoryMusicNode = null, victoryMusicTimeout = null;

            function stopVictoryMusic(resumeBg) {
                stopSpaceLoop();
                if (victoryMusicTimeout) { clearTimeout(victoryMusicTimeout); victoryMusicTimeout = null; }
                if (victoryMusicNode) {
                    const ac = getAudioCtx(), node = victoryMusicNode; victoryMusicNode = null;
                    node.gain.cancelScheduledValues(ac.currentTime);
                    node.gain.setValueAtTime(node.gain.value, ac.currentTime);
                    node.gain.linearRampToValueAtTime(0, ac.currentTime + 0.6);
                    setTimeout(() => { try { node.disconnect(); } catch (e) {} }, 800);
                }
                if (resumeBg && bgMusic && bgMusic.paused && musicVolume > 0 && isUserInteracted) bgMusic.play().catch(() => {});
            }

            function playVictoryMusic() {
                stopVictoryMusic(false);
                if (!isUserInteracted) return;
                const vol = musicVolume > 0 ? musicVolume : 0;
                if (vol === 0) return;
                try {
                    if (bgMusic) bgMusic.pause();
                    const ac = getAudioCtx(), t0 = ac.currentTime + 0.15;
                    const beat = 60 / 108;                      // 108 BPM
                    const bar = beat * 4;

                    const master = ac.createGain(); master.gain.value = Math.min(1, vol * 1.6);
                    const comp = ac.createDynamicsCompressor(); comp.threshold.value = -16; comp.ratio.value = 4;
                    const rev = makeReverb(ac, 3, 2.2), wet = ac.createGain(); wet.gain.value = 0.3;
                    master.connect(comp); comp.connect(ac.destination); master.connect(rev); rev.connect(wet); wet.connect(comp);
                    victoryMusicNode = master;

                    // Instrumentos
                    const brass = (m, st, dur, vel) => {
                        const g = ac.createGain(), f = ac.createBiquadFilter(); f.type = 'lowpass'; f.Q.value = 1;
                        f.frequency.setValueAtTime(500, st); f.frequency.linearRampToValueAtTime(2600, st + 0.12); f.frequency.linearRampToValueAtTime(1500, st + dur);
                        g.gain.setValueAtTime(0.0001, st); g.gain.exponentialRampToValueAtTime(vel, st + 0.07); g.gain.setValueAtTime(vel * 0.85, st + Math.max(0.08, dur - 0.12)); g.gain.exponentialRampToValueAtTime(0.0001, st + dur + 0.15);
                        f.connect(g); g.connect(master);
                        [-6, 6].forEach(det => { const o = ac.createOscillator(); o.type = 'sawtooth'; o.frequency.value = midiHz(m); o.detune.value = det; o.connect(f); o.start(st); o.stop(st + dur + 0.2); });
                    };
                    const pad = (m, st, dur, vel) => {
                        const g = ac.createGain(), f = ac.createBiquadFilter(); f.type = 'lowpass'; f.frequency.value = 1200;
                        g.gain.setValueAtTime(0.0001, st); g.gain.exponentialRampToValueAtTime(vel, st + 0.35); g.gain.setValueAtTime(vel, st + dur - 0.2); g.gain.exponentialRampToValueAtTime(0.0001, st + dur + 0.3);
                        f.connect(g); g.connect(master);
                        [-10, 0, 10].forEach(det => { const o = ac.createOscillator(); o.type = 'sawtooth'; o.frequency.value = midiHz(m); o.detune.value = det; o.connect(f); o.start(st); o.stop(st + dur + 0.35); });
                    };
                    const pluck = (m, st, vel) => {
                        const o = ac.createOscillator(); o.type = 'sawtooth'; o.frequency.value = midiHz(m);
                        const f = ac.createBiquadFilter(); f.type = 'lowpass'; f.frequency.setValueAtTime(2000, st); f.frequency.exponentialRampToValueAtTime(300, st + beat * 0.45);
                        const g = ac.createGain(); g.gain.setValueAtTime(vel, st); g.gain.exponentialRampToValueAtTime(0.0001, st + beat * 0.45);
                        o.connect(f); f.connect(g); g.connect(master); o.start(st); o.stop(st + beat * 0.5);
                    };
                    const timpani = (m, st, vel) => {
                        const o = ac.createOscillator(); o.type = 'sine';
                        o.frequency.setValueAtTime(midiHz(m) * 1.5, st); o.frequency.exponentialRampToValueAtTime(midiHz(m), st + 0.08);
                        const g = ac.createGain(); g.gain.setValueAtTime(vel, st); g.gain.exponentialRampToValueAtTime(0.0001, st + 1.2);
                        o.connect(g); g.connect(master); o.start(st); o.stop(st + 1.3);
                    };
                    const noiseBuf = (() => { const len = ac.sampleRate * 3, b = ac.createBuffer(1, len, ac.sampleRate), d = b.getChannelData(0); for (let i = 0; i < len; i++) d[i] = Math.random() * 2 - 1; return b; })();
                    const cymbal = (st, vel) => {
                        const n = ac.createBufferSource(); n.buffer = noiseBuf;
                        const f = ac.createBiquadFilter(); f.type = 'highpass'; f.frequency.value = 5000;
                        const g = ac.createGain(); g.gain.setValueAtTime(vel, st); g.gain.exponentialRampToValueAtTime(0.0001, st + 2.8);
                        n.connect(f); f.connect(g); g.connect(master); n.start(st); n.stop(st + 2.9);
                    };

                    // Armonía: Re menor heroico que termina en Re mayor
                    const chords = [
                        [50, 53, 57], [46, 50, 53], [53, 57, 60], [48, 52, 55],   // Dm  Bb  F  C
                        [50, 53, 57], [46, 50, 53], [48, 52, 55], [45, 49, 52],   // Dm  Bb  C  A
                        [50, 54, 57], [46, 50, 53], [48, 52, 55], [50, 54, 57]    // D   Bb  C  D  (final triunfal)
                    ];
                    // Melodía de trompetas: [nota MIDI, duración en tiempos]
                    const melody = [
                        [[69, 2], [74, 1], [72, 1]], [[70, 2], [69, 1], [67, 1]], [[65, 1.5], [67, 0.5], [69, 2]], [[67, 3], [64, 1]],
                        [[69, 1], [74, 1], [77, 1], [76, 1]], [[74, 2], [72, 1], [70, 1]], [[72, 2], [76, 2]], [[73, 4]],
                        [[74, 2], [78, 2]], [[77, 1], [74, 1], [70, 2]], [[72, 1], [76, 1], [79, 2]], [[78, 2], [81, 2]]
                    ];

                    chords.forEach((ch, b) => {
                        const bt = t0 + b * bar, climax = b >= 8;
                        ch.forEach(m => pad(m, bt, bar, climax ? 0.05 : 0.04));
                        ch.forEach(m => brass(m + 12, bt, bar * 0.95, climax ? 0.035 : 0.02));
                        // ostinato de cuerdas en corcheas
                        for (let k = 0; k < 8; k++) pluck(k % 2 === 0 ? ch[0] - 12 : ch[0] - 5, bt + k * beat / 2, climax ? 0.13 : 0.1);
                        // bajo
                        brass(ch[0] - 24, bt, bar * 0.95, 0.07);
                        // timbales
                        timpani(ch[0] - 24, bt, 0.9);
                        timpani(ch[0] - 17, bt + beat * 2, 0.5);
                        if (b === 7) for (let k = 0; k < 8; k++) timpani(45 - 24, bt + beat * 2 + k * beat / 4, 0.25 + k * 0.08);   // redoble antes del clímax
                        // melodía
                        let mt = bt;
                        melody[b].forEach(([m, d]) => { brass(m, mt, d * beat * 0.95, climax ? 0.11 : 0.09); brass(m - 12, mt, d * beat * 0.95, 0.04); mt += d * beat; });
                    });
                    cymbal(t0 + 8 * bar, 0.25);

                    // Acorde final largo en Re mayor
                    const ft = t0 + chords.length * bar;
                    [38, 50, 54, 57, 62, 66, 69, 74].forEach(m => brass(m, ft, beat * 6, m > 60 ? 0.06 : 0.05));
                    timpani(26, ft, 1.0); cymbal(ft, 0.3);
                    for (let k = 0; k < 12; k++) timpani(26, ft + beat * 2 + k * beat / 4, 0.2 + k * 0.03);
                    timpani(26, ft + beat * 5, 1.0);

                    const totalMs = (ft + beat * 7 - ac.currentTime) * 1000;
                    victoryMusicTimeout = setTimeout(() => { victoryMusicTimeout = null; stopVictoryMusic(true); }, totalMs);
                } catch (e) { console.log("Música de victoria no disponible", e); }
            }

            // --- Música espacial de victoria en loop (niveles que no son el último) ---
            let spaceLoop = null;
            const SPACE_BPM = 84;

            function scheduleSpaceSegment(ac, st, t0) {
                const beat = 60 / SPACE_BPM, bar = beat * 4;
                // Dmaj9 · Bm9 · Gmaj7(#11) · Asus4→A, dos vueltas
                const chords = [
                    [50, 54, 57, 61, 64], [47, 50, 54, 57, 61], [43, 47, 50, 54, 61], [45, 50, 52, 57, 61],
                    [50, 54, 57, 61, 64], [47, 50, 54, 57, 61], [43, 47, 50, 54, 61], [45, 49, 52, 57, 64]
                ];
                // Campanitas: [nota MIDI, tiempo dentro del compás, duración en tiempos]
                const bells = [
                    [[78, 0, 1.5], [81, 1.5, 2.5]], [[78, 0, 2], [74, 2, 2]], [[79, 0, 1.5], [83, 1.5, 2.5]], [[81, 0, 2], [76, 2, 2]],
                    [[78, 0, 1.5], [81, 1.5, 2.5]], [[83, 0, 2], [81, 2, 2]], [[79, 0, 1], [83, 1, 1], [85, 2, 2]], [[86, 0, 2], [85, 2, 1], [81, 3, 1]]
                ];
                const arpOrder = [0, 2, 4, 1, 3, 2, 4, 3];

                chords.forEach((ch, b) => {
                    const bt = t0 + b * bar;
                    // Colchón (pad) con filtro que respira
                    const pf = ac.createBiquadFilter(); pf.type = 'lowpass'; pf.Q.value = 2;
                    pf.frequency.setValueAtTime(500, bt); pf.frequency.linearRampToValueAtTime(1700, bt + bar * 0.5); pf.frequency.linearRampToValueAtTime(600, bt + bar);
                    const pg = ac.createGain();
                    pg.gain.setValueAtTime(0.0001, bt); pg.gain.exponentialRampToValueAtTime(0.022, bt + 0.6); pg.gain.setValueAtTime(0.022, bt + bar - 0.3); pg.gain.exponentialRampToValueAtTime(0.0001, bt + bar + 0.4);
                    pf.connect(pg); pg.connect(st.wetBus);
                    ch.forEach(m => [-12, 0, 12].forEach(det => {
                        const o = ac.createOscillator(); o.type = 'sawtooth'; o.frequency.value = midiHz(m); o.detune.value = det;
                        o.connect(pf); o.start(bt); o.stop(bt + bar + 0.5);
                    }));
                    // Bajo suave
                    const bo = ac.createOscillator(); bo.type = 'sine'; bo.frequency.value = midiHz(ch[0] - 12);
                    const bg = ac.createGain(); bg.gain.setValueAtTime(0.0001, bt); bg.gain.exponentialRampToValueAtTime(0.22, bt + 0.15); bg.gain.setValueAtTime(0.22, bt + bar - 0.2); bg.gain.exponentialRampToValueAtTime(0.0001, bt + bar + 0.1);
                    bo.connect(bg); bg.connect(st.dryBus); bo.start(bt); bo.stop(bt + bar + 0.2);
                    // Arpegio en corcheas con eco
                    for (let k = 0; k < 8; k++) {
                        const at = bt + k * beat / 2, m = ch[arpOrder[k]] + 12;
                        const o = ac.createOscillator(); o.type = 'triangle'; o.frequency.value = midiHz(m);
                        const g = ac.createGain(); g.gain.setValueAtTime(0.0001, at); g.gain.exponentialRampToValueAtTime(0.07, at + 0.01); g.gain.exponentialRampToValueAtTime(0.0001, at + beat * 0.9);
                        o.connect(g); g.connect(st.echoBus); o.start(at); o.stop(at + beat);
                    }
                    // Campanitas (melodía)
                    bells[b].forEach(([m, off, dur]) => {
                        const at = bt + off * beat;
                        [1, 2.01].forEach((mult, i) => {
                            const o = ac.createOscillator(); o.type = 'sine'; o.frequency.value = midiHz(m) * mult;
                            const g = ac.createGain(); const v = i === 0 ? 0.09 : 0.025;
                            g.gain.setValueAtTime(0.0001, at); g.gain.exponentialRampToValueAtTime(v, at + 0.02); g.gain.exponentialRampToValueAtTime(0.0001, at + dur * beat + 1.2);
                            o.connect(g); g.connect(st.echoBus); o.start(at); o.stop(at + dur * beat + 1.3);
                        });
                    });
                });
                // Brillo de estrellas (ruido muy agudo) al comienzo de cada vuelta
                const len = Math.ceil(ac.sampleRate * bar), buf = ac.createBuffer(1, len, ac.sampleRate), d = buf.getChannelData(0);
                for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * Math.sin(Math.PI * i / len);
                const n = ac.createBufferSource(); n.buffer = buf;
                const hf = ac.createBiquadFilter(); hf.type = 'highpass'; hf.frequency.value = 7000;
                const ng = ac.createGain(); ng.gain.value = 0.05;
                n.connect(hf); hf.connect(ng); ng.connect(st.wetBus); n.start(t0); n.stop(t0 + bar);
                return chords.length * bar;
            }

            function playSpaceVictoryLoop() {
                stopVictoryMusic(false);
                if (!isUserInteracted || musicVolume === 0) return;
                try {
                    if (bgMusic) bgMusic.pause();
                    const ac = getAudioCtx(), now = ac.currentTime, beat = 60 / SPACE_BPM;
                    const master = ac.createGain();
                    master.gain.setValueAtTime(0.0001, now); master.gain.linearRampToValueAtTime(Math.min(1, musicVolume * 1.8), now + 2.5);
                    const comp = ac.createDynamicsCompressor(); comp.threshold.value = -18; comp.ratio.value = 3;
                    master.connect(comp); comp.connect(ac.destination);
                    // Reverb grande (espacio) + eco
                    const rev = makeReverb(ac, 4.5, 1.8), revG = ac.createGain(); revG.gain.value = 0.55;
                    rev.connect(revG); revG.connect(master);
                    const dryBus = ac.createGain(); dryBus.connect(master);
                    const wetBus = ac.createGain(); wetBus.connect(master); wetBus.connect(rev);
                    const echoBus = ac.createGain(); echoBus.connect(master); echoBus.connect(rev);
                    const delay = ac.createDelay(2); delay.delayTime.value = beat * 0.75;
                    const fb = ac.createGain(); fb.gain.value = 0.4;
                    const fbF = ac.createBiquadFilter(); fbF.type = 'lowpass'; fbF.frequency.value = 2500;
                    echoBus.connect(delay); delay.connect(fbF); fbF.connect(fb); fb.connect(delay); fbF.connect(master); fbF.connect(rev);

                    const st = { master, dryBus, wetBus, echoBus, timer: null, next: now + 0.1 };
                    const schedule = () => {
                        if (spaceLoop !== st) return;
                        const len = scheduleSpaceSegment(ac, st, st.next);
                        st.next += len;
                        st.timer = setTimeout(schedule, Math.max(100, (st.next - ac.currentTime - 2) * 1000));   // agenda la siguiente vuelta 2 s antes
                    };
                    spaceLoop = st;
                    schedule();
                } catch (e) { console.log("Música espacial no disponible", e); }
            }

            function stopSpaceLoop() {
                if (!spaceLoop) return;
                const st = spaceLoop; spaceLoop = null;
                if (st.timer) clearTimeout(st.timer);
                try {
                    const ac = getAudioCtx();
                    st.master.gain.cancelScheduledValues(ac.currentTime);
                    st.master.gain.setValueAtTime(st.master.gain.value, ac.currentTime);
                    st.master.gain.linearRampToValueAtTime(0, ac.currentTime + 1);
                    setTimeout(() => { try { st.master.disconnect(); } catch (e) {} }, 1200);
                } catch (e) {}
            }

            // ======================================================
            // === ATAQUES EXTRA DEL JEFE (según dificultad) ===
            // rayos: láseres dirigidos con aviso previo
            // bombas: bombas que caen donde estás y explotan
            // ======================================================
            let bossBombs = [];
            const RAY_CHARGE = 48;   // frames de aviso (línea punteada)
            const RAY_FIRE = 24;     // frames que dura el rayo
            const RAY_LEN = 2400;
            const BOMB_FLIGHT = 55, BOMB_FUSE = 70, BOMB_RADIUS = 170;

            function makeVeins() {
                // grietas en el espacio del jefe (radio 100 = borde)
                const veins = [];
                for (let v = 0; v < 8; v++) {
                    let a = Math.random() * Math.PI * 2, rr = 20 + Math.random() * 30;
                    const pts = [[Math.cos(a) * rr, Math.sin(a) * rr]];
                    for (let k = 0; k < 4; k++) { a += (Math.random() - 0.5) * 0.9; rr = Math.min(96, rr + 14 + Math.random() * 14); pts.push([Math.cos(a) * rr, Math.sin(a) * rr]); }
                    veins.push(pts);
                }
                return veins;
            }

            function updateBossExtras() {
                // Bombas en el aire / en el suelo (siguen aunque el jefe muera)
                for (let i = bossBombs.length - 1; i >= 0; i--) {
                    const b = bossBombs[i]; b.t++;
                    if (b.t <= BOMB_FLIGHT) { const p = b.t / BOMB_FLIGHT; b.x = b.sx + (b.tx - b.sx) * p; b.y = b.sy + (b.ty - b.sy) * p; }
                    if (b.t >= BOMB_FLIGHT + BOMB_FUSE) {
                        // ¡BOOM!
                        const dmg = 40 * (LV.jefe.potencia_laser / 5);
                        if (!player.dead && Math.hypot(player.x - b.x, player.y - b.y) < BOMB_RADIUS + player.r) {
                            takeDamage(player, dmg);
                            const a = Math.atan2(player.y - b.y, player.x - b.x); player.kbx = Math.cos(a) * 12; player.kby = Math.sin(a) * 12;
                        }
                        bots.forEach(bt => { if (!bt.dead && Math.hypot(bt.x - b.x, bt.y - b.y) < BOMB_RADIUS + bt.r) takeDamage(bt, dmg); });
                        for (let k = 0; k < 45; k++) { const a = Math.random() * Math.PI * 2, sp = Math.random() * 11; particles.push({ x: b.x, y: b.y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, color: ["#FF0033", "#FF8C00", "#FFFFFF", LV.jefe.color][k % 4], life: 30 }); }
                        playAbilitySfx('boom');
                        bossBombs.splice(i, 1);
                    }
                }

                if (!meteor.isBoss || meteor.dead || cinematicTimer > 0) { if (meteor.dead) meteor.rays = []; return; }
                const J = LV.jefe;

                // Rayos láser dirigidos
                if (J.rayos) {
                    meteor.rays = meteor.rays || [];
                    meteor.rayTimer = (meteor.rayTimer || 0) + 1;
                    const wait = meteor.isPhase2 ? J.rayos_espera_frames * 0.7 : J.rayos_espera_frames;
                    if (meteor.rayTimer >= wait && meteor.rays.length === 0 && !player.dead) {
                        meteor.rayTimer = 0;
                        const n = J.rayos_cantidad + (meteor.isPhase2 ? 2 : 0);
                        const base = Math.atan2(player.y - meteor.y, player.x - meteor.x), spread = 0.32;
                        for (let i = 0; i < n; i++) meteor.rays.push({ angle: base + (i - (n - 1) / 2) * spread, t: 0 });
                        playAbilitySfx('shield');
                    }
                    for (let i = meteor.rays.length - 1; i >= 0; i--) {
                        const r = meteor.rays[i]; r.t++;
                        if (r.t === RAY_CHARGE) playSfx("laser", 0.9);
                        if (r.t > RAY_CHARGE) {
                            const x2 = meteor.x + Math.cos(r.angle) * RAY_LEN, y2 = meteor.y + Math.sin(r.angle) * RAY_LEN, w = 26;
                            const dmg = J.potencia_laser * 0.8;
                            if (!player.dead && distToBeam(player.x, player.y, meteor.x, meteor.y, x2, y2) < w + player.r) takeDamage(player, dmg);
                            if (r.t % 6 === 0) bots.forEach(b => { if (!b.dead && distToBeam(b.x, b.y, meteor.x, meteor.y, x2, y2) < w + b.r) takeDamage(b, dmg * 6); });
                        }
                        if (r.t >= RAY_CHARGE + RAY_FIRE) meteor.rays.splice(i, 1);
                    }
                }

                // Bombas explosivas
                if (J.bombas) {
                    meteor.bombTimer = (meteor.bombTimer || 0) + 1;
                    const wait = meteor.isPhase2 ? J.bombas_espera_frames * 0.6 : J.bombas_espera_frames;
                    if (meteor.bombTimer >= wait && !player.dead) {
                        meteor.bombTimer = 0;
                        const n = J.bombas_cantidad + (meteor.isPhase2 ? 1 : 0);
                        for (let i = 0; i < n; i++) {
                            const off = i === 0 ? 0 : 120 + Math.random() * 160, a = Math.random() * Math.PI * 2;
                            const tx = Math.max(40, Math.min(worldW - 40, player.x + Math.cos(a) * off + player.kbx * 5));
                            const ty = Math.max(40, Math.min(worldH - 40, player.y + Math.sin(a) * off + player.kby * 5));
                            bossBombs.push({ sx: meteor.x, sy: meteor.y, tx, ty, x: meteor.x, y: meteor.y, t: 0 });
                        }
                        playAbilitySfx('whoosh');
                    }
                }
            }

            function drawBossExtras() {
                const J = LV.jefe;
                // Rayos
                if (meteor.rays && !meteor.dead) meteor.rays.forEach(r => {
                    const x2 = meteor.x + Math.cos(r.angle) * RAY_LEN, y2 = meteor.y + Math.sin(r.angle) * RAY_LEN;
                    const glow = J.color_detalles || J.color, core = J.color_detalles ? "#FFFFFF" : "#FFFFFF";
                    ctx.save(); ctx.lineCap = "round";
                    if (r.t <= RAY_CHARGE) {
                        ctx.globalAlpha = 0.35 + 0.45 * (Math.floor(r.t / 5) % 2);
                        ctx.strokeStyle = glow; ctx.lineWidth = 3; ctx.setLineDash([16, 12]);
                        ctx.beginPath(); ctx.moveTo(meteor.x, meteor.y); ctx.lineTo(x2, y2); ctx.stroke();
                    } else {
                        const fade = Math.min(1, (RAY_CHARGE + RAY_FIRE - r.t) / 8);
                        ctx.globalAlpha = fade; ctx.shadowColor = glow; ctx.shadowBlur = 30;
                        ctx.strokeStyle = glow; ctx.globalAlpha = fade * 0.45; ctx.lineWidth = 64;
                        ctx.beginPath(); ctx.moveTo(meteor.x, meteor.y); ctx.lineTo(x2, y2); ctx.stroke();
                        ctx.globalAlpha = fade; ctx.lineWidth = 30; ctx.beginPath(); ctx.moveTo(meteor.x, meteor.y); ctx.lineTo(x2, y2); ctx.stroke();
                        ctx.shadowBlur = 0; ctx.strokeStyle = core; ctx.lineWidth = 10;
                        ctx.beginPath(); ctx.moveTo(meteor.x, meteor.y); ctx.lineTo(x2, y2); ctx.stroke();
                    }
                    ctx.restore();
                });
                // Bombas
                bossBombs.forEach(b => {
                    ctx.save();
                    const landed = b.t > BOMB_FLIGHT, fuseP = landed ? (b.t - BOMB_FLIGHT) / BOMB_FUSE : 0;
                    // zona de peligro
                    ctx.globalAlpha = landed ? 0.18 + 0.25 * fuseP : 0.12;
                    ctx.fillStyle = "#FF0033"; ctx.beginPath(); ctx.arc(b.tx, b.ty, BOMB_RADIUS, 0, Math.PI * 2); ctx.fill();
                    ctx.globalAlpha = 0.8; ctx.strokeStyle = "#FF0033"; ctx.lineWidth = 3; ctx.setLineDash([10, 8]);
                    ctx.beginPath(); ctx.arc(b.tx, b.ty, BOMB_RADIUS * (landed ? 1 - fuseP * 0.15 : 1), 0, Math.PI * 2); ctx.stroke();
                    ctx.setLineDash([]); ctx.globalAlpha = 1;
                    // la bomba (en el aire se ve más grande, como si viniera alta)
                    const lift = landed ? 0 : Math.sin(Math.PI * b.t / BOMB_FLIGHT);
                    const R = 22 + lift * 14;
                    const blink = landed && Math.floor(b.t / Math.max(2, 8 - fuseP * 6)) % 2 === 0;
                    ctx.shadowColor = "#FF0033"; ctx.shadowBlur = blink ? 30 : 10;
                    ctx.fillStyle = blink ? "#FF0033" : "#1A1A2A"; ctx.beginPath(); ctx.arc(b.x, b.y - lift * 60, R, 0, Math.PI * 2); ctx.fill();
                    ctx.shadowBlur = 0; ctx.strokeStyle = J.color; ctx.lineWidth = 3; ctx.stroke();
                    ctx.fillStyle = "#FFD27A"; ctx.beginPath(); ctx.arc(b.x + R * 0.5, b.y - lift * 60 - R * 0.8, 5 + Math.random() * 3, 0, Math.PI * 2); ctx.fill();
                    ctx.restore();
                });
            }

            // === PANTALLA DE VICTORIA ===
            const victoryModal = document.getElementById('victory-modal');
            const vicBtns = document.getElementById('vic-btns');
            let lastUnlocks = [];
            function onBossDefeated() {
                if (freeMode) return;
                lastUnlocks = markBeaten(levelIndex, difficulty);
                // "musica_victoria" del nivel: "espacial" (loop), "epica" o "ninguna".
                // Si no se indica: el último nivel usa la épica y los demás la espacial. En NIGHTMARE siempre suena la épica.
                let tipo = difficulty === 'nightmare' ? 'epica' : (LV.musica_victoria || (levelIndex >= LEVELS.length - 1 ? 'epica' : 'espacial'));
                if (tipo === 'epica') setTimeout(playVictoryMusic, 120);
                else if (tipo === 'espacial') setTimeout(playSpaceVictoryLoop, 120);
                victoryTimer = 150;   // 2,5 s para ver la explosión antes del menú
            }
            function startLevel(idx, diff) {
                levelIndex = idx; difficulty = diff;
                victoryModal.style.display = 'none'; stopVictoryMusic(true); init(); gameState = 'playing';
            }
            function addVicBtn(text, color, filled, fn) {
                const b = document.createElement('button'); b.className = 'vic-btn'; b.innerText = text;
                b.style.color = filled ? '#06060E' : color; b.style.borderColor = filled ? '#FFFFFF' : color; if (filled) b.style.background = color;
                b.addEventListener('click', fn); vicBtns.appendChild(b);
            }
            function showVictory() {
                isPaused = true; isFiring = false; keysDown.clear();
                const dLabel = DIFFS[difficulty].label;
                const title = allBeaten() ? '¡COMPLETASTE TODO!' : (difficulty === 'nightmare' ? '¡NIGHTMARE SUPERADO!' : '¡NIVEL COMPLETADO!');
                document.querySelector('#victory-modal h2').innerText = title;
                victoryModal.style.borderColor = DIFFS[difficulty].color;
                let sub = `NIVEL ${levelIndex + 1}: ${String(LEVELS[levelIndex].nombre).toUpperCase()} · ${dLabel}`;
                if (lastUnlocks.length) sub += `\n¡DESBLOQUEASTE: ${lastUnlocks.join(' · ')}!`;
                document.getElementById('victory-sub').innerText = sub;

                vicBtns.innerHTML = '';
                const di = DIFF_ORDER.indexOf(difficulty);
                if (di < DIFF_ORDER.length - 1) {
                    const nd = DIFF_ORDER[di + 1];
                    addVicBtn(`JUGAR EN ${DIFFS[nd].label}`, DIFFS[nd].color, true, () => startLevel(levelIndex, nd));
                }
                if (levelIndex < LEVELS.length - 1) {
                    addVicBtn(`SIGUIENTE: ${String(LEVELS[levelIndex + 1].nombre).toUpperCase()}`, '#FFD700', di === DIFF_ORDER.length - 1, () => startLevel(levelIndex + 1, 'normal'));
                }
                addVicBtn('REPETIR NIVEL', '#00FFFF', false, () => startLevel(levelIndex, difficulty));
                addVicBtn('MODO LIBRE', '#33FF66', false, () => {
                    freeMode = true; victoryModal.style.display = 'none'; isPaused = false;
                    floatingTexts.push({ x: player.x, y: player.y - 60, text: "MODO LIBRE", color: "#33FF66", life: 90, size: 26 });
                });
                addVicBtn('ELEGIR NIVEL', '#CC33FF', false, () => {
                    victoryModal.style.display = 'none'; goToMenu(); openLevelSelect();
                });
                victoryModal.style.display = 'block';
            }

            // ======================================================
            // === DIFICULTADES (estilo Geometry Dash) ===
            // Cada nivel se juega en NORMAL -> DIFÍCIL -> NIGHTMARE.
            // Ganar en una dificultad desbloquea la siguiente de ESE nivel.
            // Ganar cualquier dificultad de un nivel desbloquea el siguiente nivel (en normal).
            // ======================================================
            const DIFF_ORDER = ['normal', 'dificil', 'nightmare'];
            const DIFFS = {
                normal:    { label: 'NORMAL',    color: '#33FF66', mult: {} },
                dificil:   { label: 'DIFÍCIL',   color: '#FFAA00', mult: {
                    bots_cantidad: 1.15, bots_vida: 1.5, bots_velocidad: 1.15, bots_espera: 0.75, bots_potencia: 1.4,
                    agujero_vida: 1.5, agujero_crecimiento: 1.3, agujero_atraccion: 1.15,
                    jefe_vida: 1.6, jefe_velocidad: 1.25, jefe_potencia_balas: 1.4, jefe_espera_laser: 0.75, jefe_potencia_laser: 1.4 } },
                nightmare: { label: 'NIGHTMARE', color: '#FF0040', mult: {
                    bots_cantidad: 1.3, bots_vida: 2.2, bots_velocidad: 1.3, bots_espera: 0.55, bots_potencia: 2.0,
                    agujero_vida: 2.2, agujero_crecimiento: 1.6, agujero_atraccion: 1.3,
                    jefe_vida: 2.5, jefe_velocidad: 1.5, jefe_potencia_balas: 2.0, jefe_espera_laser: 0.5, jefe_potencia_laser: 2.0 } }
            };
            let difficulty = 'normal';

            // Nivel final = datos del .json con los multiplicadores de la dificultad
            function buildLevel(idx, diff) {
                const base = LEVELS[Math.min(idx, LEVELS.length - 1)];
                const L = JSON.parse(JSON.stringify(base));
                const custom = (base.dificultades && base.dificultades[diff]) || {};
                const m = Object.assign({}, DIFFS[diff].mult, custom);
                const k = (name) => (m[name] !== undefined ? m[name] : 1);
                L.bots.cantidad = Math.round(L.bots.cantidad * k('bots_cantidad'));
                L.bots.vida *= k('bots_vida'); L.bots.velocidad *= k('bots_velocidad');
                L.bots.espera_disparo_ms *= k('bots_espera'); L.bots.potencia_disparo *= k('bots_potencia');
                L.agujero_negro.vida *= k('agujero_vida'); L.agujero_negro.crecimiento *= k('agujero_crecimiento'); L.agujero_negro.fuerza_atraccion *= k('agujero_atraccion');
                L.jefe.vida = Math.round(L.jefe.vida * k('jefe_vida'));
                L.jefe.velocidad *= k('jefe_velocidad'); L.jefe.velocidad_fase2 *= k('jefe_velocidad');
                L.jefe.potencia_balas *= k('jefe_potencia_balas'); L.jefe.espera_laser_frames *= k('jefe_espera_laser'); L.jefe.potencia_laser *= k('jefe_potencia_laser');
                if (base.jefe_dificultad && base.jefe_dificultad[diff]) Object.assign(L.jefe, base.jefe_dificultad[diff]);
                if (diff !== 'normal') {
                    L.mundo.color_borde = DIFFS[diff].color;
                    L.jefe.nombre += ' [' + DIFFS[diff].label + ']';
                    L.jefe.nombre_fase2 += ' [' + DIFFS[diff].label + ']';
                }
                return L;
            }

            // --- Progreso guardado en el navegador ---
            const PROGRESS_KEY = 'starz_progreso_v1';
            let progress = {};
            try { progress = JSON.parse(localStorage.getItem(PROGRESS_KEY) || '{}') || {}; } catch (e) { progress = {}; }
            function levelKey(i) { return (LEVELS[i] && LEVELS[i].archivo) || ('nivel_' + i); }
            function isBeaten(i, diff) { return !!(progress[levelKey(i)] && progress[levelKey(i)][diff]); }
            function beatenAny(i) { return DIFF_ORDER.some(d => isBeaten(i, d)); }
            function isUnlocked(i, diff) {
                if (isRissos()) return true;   // cheats: todo desbloqueado
                if (i > 0 && !beatenAny(i - 1)) return false;
                const di = DIFF_ORDER.indexOf(diff);
                return di === 0 || isBeaten(i, DIFF_ORDER[di - 1]);
            }
            function markBeaten(i, diff) {
                const before = DIFF_ORDER.map(d => isUnlocked(i, d)), nextBefore = i + 1 < LEVELS.length ? isUnlocked(i + 1, 'normal') : true;
                const key = levelKey(i); progress[key] = progress[key] || {}; progress[key][diff] = true;
                try { localStorage.setItem(PROGRESS_KEY, JSON.stringify(progress)); } catch (e) {}
                const unlocked = [];
                DIFF_ORDER.forEach((d, j) => { if (!before[j] && isUnlocked(i, d)) unlocked.push(DIFFS[d].label); });
                if (!nextBefore && isUnlocked(i + 1, 'normal')) unlocked.push('NIVEL ' + (i + 2));
                return unlocked;
            }
            function allBeaten() { return LEVELS.every((_, i) => DIFF_ORDER.every(d => isBeaten(i, d))); }

            // --- Pantalla de selección de nivel ---
            const levelSelect = document.getElementById('level-select');
            const levelGrid = document.getElementById('level-grid');
            const LOCK_SVG = '<svg viewBox="0 0 24 24" width="14" height="14"><rect x="5" y="11" width="14" height="10" rx="2" fill="currentColor"/><path d="M8 11 V8 a4 4 0 0 1 8 0 V11" fill="none" stroke="currentColor" stroke-width="2.4"/></svg>';
            const CHECK_SVG = '<svg viewBox="0 0 24 24" width="14" height="14"><path d="M4 12.5 L10 18 L20 6" fill="none" stroke="currentColor" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
            function buildLevelCards() {
                levelGrid.innerHTML = '';
                LEVELS.forEach((lv, i) => {
                    const card = document.createElement('div'); card.className = 'lvl-card';
                    const open = isUnlocked(i, 'normal');
                    card.style.borderColor = open ? lv.mundo.color_borde : '#333';
                    card.style.background = 'linear-gradient(180deg, ' + lv.mundo.color_fondo + ' 0%, #0d1424 100%)';
                    let html = '<div class="lvl-num">NIVEL ' + (i + 1) + '</div>' +
                        '<div class="lvl-name" style="color:' + (open ? lv.mundo.color_borde : '#666') + '">' + String(lv.nombre).toUpperCase() + '</div>' +
                        '<div class="lvl-boss">JEFE: ' + lv.jefe.nombre + '</div>' +
                        (lv.descripcion ? '<div class="lvl-desc">' + lv.descripcion + '</div>' : '') +
                        '<div class="lvl-diffs">';
                    DIFF_ORDER.forEach(d => {
                        const un = isUnlocked(i, d), done = isBeaten(i, d), c = DIFFS[d].color;
                        html += '<button class="diff-btn" data-lvl="' + i + '" data-diff="' + d + '" ' + (un ? '' : 'disabled') +
                            ' style="color:' + (un ? c : '#555') + ';border-color:' + (un ? c : '#333') + (done ? ';background:' + c + '22' : '') + '">' +
                            (un ? (done ? CHECK_SVG : '') : LOCK_SVG) + '<span>' + DIFFS[d].label + '</span></button>';
                    });
                    html += '</div>';
                    card.innerHTML = html;
                    levelGrid.appendChild(card);
                });
                // --- Fases (carpeta FASES/) ---
                FASES_DATA.forEach((fa, k) => {
                    const reg = window.FASES_REG && window.FASES_REG[fa.id];
                    const playable = fa.jugable && reg;
                    const open = playable && isFaseUnlocked(k);
                    const done = isFaseBeaten(fa.id);
                    const name = (fa.config && fa.config.nombre) ? String(fa.config.nombre).toUpperCase() : 'PRÓXIMAMENTE';
                    const num = fa.id.replace(/[^0-9]/g, '') || (k + 2);
                    const card = document.createElement('div'); card.className = 'lvl-card';
                    card.style.borderColor = open ? '#E8B934' : '#333';
                    card.style.background = 'linear-gradient(180deg, #5a3510 0%, #0d1424 100%)';
                    let why = !playable ? 'En construcción' : (open ? '' : (k === 0 ? 'Gana el nivel 1 para desbloquear' : 'Completa la fase anterior'));
                    card.innerHTML = '<div class="lvl-num">FASE ' + num + '</div>' +
                        '<div class="lvl-name" style="color:' + (open ? '#F5C542' : '#666') + '">' + name + '</div>' +
                        (fa.config && fa.config.jefe ? '<div class="lvl-boss">JEFE: ' + fa.config.jefe.nombre + '</div>' : '') +
                        (why ? '<div class="lvl-desc">' + why + '</div>' : '') +
                        '<div class="lvl-diffs"><button class="diff-btn fase-btn" data-fase="' + fa.id + '" ' + (open ? '' : 'disabled') +
                        ' style="color:' + (open ? '#F5C542' : '#555') + ';border-color:' + (open ? '#F5C542' : '#333') + (done ? ';background:#F5C54222' : '') + '">' +
                        (open ? (done ? CHECK_SVG : '') : LOCK_SVG) + '<span>' + (playable ? 'JUGAR' : 'PRÓXIMAMENTE') + '</span></button></div>';
                    levelGrid.appendChild(card);
                });
                levelGrid.querySelectorAll('.fase-btn:not([disabled])').forEach(b => b.addEventListener('click', () => startFase(b.dataset.fase)));

                levelGrid.querySelectorAll('.diff-btn:not([disabled]):not(.fase-btn)').forEach(b => b.addEventListener('click', () => {
                    levelIndex = parseInt(b.dataset.lvl, 10); difficulty = b.dataset.diff;
                    levelSelect.style.display = 'none';
                    openCharSelect();
                }));
            }
            // --- Fases: desbloqueo, inicio y salida ---
            function isFaseBeaten(id) { return !!(progress['FASE:' + id] && progress['FASE:' + id].completada); }
            function isFaseUnlocked(k) {
                if (isRissos()) return true;
                // solo cuentan las fases jugables (las carpetas sin fase.js no bloquean a las demás)
                const jugables = FASES_DATA.filter(f => f.jugable);
                const pos = jugables.indexOf(FASES_DATA[k]);
                if (pos <= 0) return beatenAny(0);                   // la primera fase jugable se abre al ganar el nivel 1
                return isFaseBeaten(jugables[pos - 1].id);           // las demás, al completar la anterior
            }
            function startFase(id) {
                const fa = FASES_DATA.find(f => f.id === id), reg = window.FASES_REG && window.FASES_REG[id];
                if (!fa || !reg) return;
                levelSelect.style.display = 'none'; charSelect.style.display = 'none';
                mainMenu.style.display = 'none'; settingsModal.style.display = 'none'; namePanel.style.display = 'none';
                audioControls.style.display = 'flex'; lbPanel.style.display = 'none';
                victoryModal.style.display = 'none'; overScreen.style.display = 'none'; orbModal.style.display = 'none';
                stopVictoryMusic(true);
                currentFase = reg; gameState = 'fase';
                reg.start(fa.config, {
                    canvas, ctx, drawIcon, playSfx, playAbilitySfx, playEndSfx, playVictoryMusic, stopVictoryMusic, isRissos,
                    getAudioCtx, sfxVol: () => sfxVolume, interacted: () => isUserInteracted,
                    active: () => gameState === 'fase' && currentFase === reg,
                    onWin: (faseId) => {
                        const key = 'FASE:' + faseId; progress[key] = progress[key] || {}; progress[key].completada = true;
                        try { localStorage.setItem(PROGRESS_KEY, JSON.stringify(progress)); } catch (e) {}
                    },
                    onExit: () => { goToMenu(); openLevelSelect(); }
                });
            }
            function openLevelSelect() {
                stopVictoryMusic(false);
                buildLevelCards();
                charSelect.style.display = 'none';
                levelSelect.style.display = 'flex';
            }

            // Nombre secreto: RISSOS empieza con todo al máximo
            function isRissos() { return (playerName || "").trim().toUpperCase() === "RISSOS"; }
            function applyRissosMode() {
                if (!isRissos()) return;
                player.r = 60; player.hp = 1000; player.maxHp = 1000; player.shields = 10;
                player.speed = Math.max(player.speed, 5.5); player.hasInvulnCharge = true;
                player.laserRange = 3.0; player.laserDamage = 5.0;
                player.multiLevel = 10; player.crossLevel = 10;
                player.cannonLvl = 10; player.pushLvl = 10; player.rhinoLvl = 10; player.reflectLvl = 10;
                player.rissos = true;
                floatingTexts.push({ x: player.x, y: player.y - 80, text: "MODO RISSOS: TODO AL MÁXIMO", icon: "star", iconBoth: true, color: "#FFD700", life: 120, size: 26 });
            }

            function triggerInvulnerability() {
                if(!player.dead && player.hasInvulnCharge && player.invulnTimer <= 0) {
                    player.hasInvulnCharge = false; player.invulnTimer = 300; 
                    floatingTexts.push({ x: player.x, y: player.y - player.r - 25, text: "¡MODO FANTASMA!", icon: "ghost", color: "#00FFFF", life: 50, size: 16 });
                }
            }

            function triggerDash() {
                const now = Date.now();
                if(!player.dead && now - lastDashTime >= (player.rissos ? 1500 : dashCooldown)) {
                    lastDashTime = now; dashTimer = 12; 
                    playSfx("dash");
                    floatingTexts.push({ x: player.x, y: player.y - player.r - 20, text: "DASH!", icon: "bolt", color: "#00FFFF", life: 30, size: 18 });
                }
            }

            function fireLaserProjectile(owner, ang, speed, life, color, damageMult) {
                lasers.push({ x: owner.x, y: owner.y, vx: Math.cos(ang) * speed, vy: Math.sin(ang) * speed, life: life, owner: owner, color: color, damageMult: damageMult, isStar: false });
            }

            function shootLaser() {
                if(player.dead || (player.r <= 12 && !player.rissos)) return;
                let targetX = (screenMouseX - canvas.width / 2) / zoom + camX + canvas.width / 2;
                let targetY = (screenMouseY - canvas.height / 2) / zoom + camY + canvas.height / 2;
                let dx = targetX - player.x; let dy = targetY - player.y; let dist = Math.hypot(dx, dy);
                if(dist === 0) return;

                let angle = Math.atan2(dy, dx); let speed = 15; let baseLife = 75 * player.laserRange;
                let costPerShot = 0;

                // Disparo Múltiple (Frontal)
                let multiCount = player.multiLevel; 
                let spread = 0.15;
                let startAngle = angle - (spread * (multiCount - 1)) / 2;
                for(let i=0; i<multiCount; i++) {
                    fireLaserProjectile(player, startAngle + i * spread, speed, baseLife, "#00FFFF", player.laserDamage);
                    costPerShot += 0.2;
                }

                // Disparo Cruzado (Laterales y Atras)
                if(player.crossLevel > 0) {
                    let crossCount = player.crossLevel;
                    for(let i=1; i<=3; i++) {
                        let crossAng = angle + (Math.PI/2) * i;
                        let cSpread = 0.10;
                        let cStartAngle = crossAng - (cSpread * (crossCount - 1)) / 2;
                        for(let c=0; c<crossCount; c++) {
                            fireLaserProjectile(player, cStartAngle + c * cSpread, speed, baseLife, "#CC33FF", player.laserDamage * 0.8);
                            costPerShot += 0.1;
                        }
                    }
                }

                playSfx("laser", player.rissos ? 0.35 : 1);
                if (!player.rissos) player.r = Math.max(10, player.r - Math.min(1.5, costPerShot));
            }

            const nombres = ["Alpha", "Nova", "Sirius", "Vega", "Orion", "Cosmos", "Apollo", "Zeta", "Pulsar"];
            const colors = ['#FF3366', '#33CCFF', '#FF9933', '#33FF66', '#CC33FF', '#FFFF33', '#FF3333'];
            function randomColor() { return colors[Math.floor(Math.random() * colors.length)]; }
            function randomName() { return nombres[Math.floor(Math.random() * nombres.length)]; }

            function spawnBox() { boxes.push({ x: Math.random() * (worldW - 100) + 50, y: Math.random() * (worldH - 100) + 50, r: 16 }); }
            function spawnRedBox() { redBoxes.push({ x: Math.random() * (worldW - 100) + 50, y: Math.random() * (worldH - 100) + 50, r: 18 }); }
            function spawnHeart() { hearts.push({ x: Math.random() * (worldW - 100) + 50, y: Math.random() * (worldH - 100) + 50, r: 10 }); }
            function spawnOrb() { orbs.push({ x: Math.random() * (worldW - 100) + 50, y: Math.random() * (worldH - 100) + 50, r: 14, type: ['celeste', 'morado', 'naranja'][Math.floor(Math.random() * 3)] }); }
            function orbColor(type) { return type === 'celeste' ? '#00FFFF' : (type === 'naranja' ? '#FF8C00' : '#CC33FF'); }

            let playerLives = 5; let player, bots, foods;
            let maxBots = 28; let maxFoods = 600;

            function init() {
                LV = buildLevel(levelIndex, difficulty);
                worldW = LV.mundo.ancho; worldH = LV.mundo.alto;
                maxBots = LV.bots.cantidad; maxFoods = LV.comida;
                freeMode = false; victoryTimer = 0; victoryModal.style.display = 'none';
                isGameOver = false; isPaused = false; playerLives = 5; cinematicTimer = 0; orbModal.style.display = 'none'; overScreen.style.display = 'none';
                dashTimer = 0; lastDashTime = 0;
                abyssUnlocked = false; abyssTimer = 0; abyssCooldown = 0;
                blackHole = { x: worldW * LV.agujero_negro.pos_x, y: worldH * LV.agujero_negro.pos_y, r: LV.agujero_negro.radio, hp: LV.agujero_negro.vida, maxHp: LV.agujero_negro.vida, dead: false };
                if (bgMusic && usingBossTrack && audioSrc) {
                    let wasPlaying = !bgMusic.paused;
                    bgMusic.pause(); bgMusic.src = audioSrc; usingBossTrack = false; bgMusic.currentTime = 0;
                    if (wasPlaying) bgMusic.play().catch(() => {});
                }
                floatingTexts = []; lasers = []; particles = []; boxes = []; redBoxes = []; hearts = []; orbs = [];
                
                meteor = { 
                    orbitAngle: 0, orbitRadius: 450, x: worldW / 2, y: worldH / 2, r: 100, angle: 0, 
                    hp: LV.jefe.vida, maxHp: LV.jefe.vida, isBoss: false, isPhase2: false, phase2MusicStarted: false, 
                    dead: false, shootAngle: 0, laserTimer: 0, laserChargeTimer: 0, laserSweepTimer: 0, laserAngle: 0,
                    craters: [ {x: -35, y: -25, r: 20}, {x: 35, y: -35, r: 16}, {x: 10, y: 30, r: 25}, {x: -40, y: 25, r: 14}, {x: 0, y: 0, r: 18} ] 
                };
                meteor.rays = []; meteor.rayTimer = 0; meteor.bombTimer = 0; meteor.veins = makeVeins(); bossBombs = [];

                player = { 
                    x: Math.random() * worldW, y: Math.random() * worldH, r: 18, color: '#FFFFFF', name: playerName, speed: 3.5, dead: false,
                    hp: 200, maxHp: 200, shields: 0, hasInvulnCharge: false, invulnTimer: 0, fireTimer: 0, speedBoostTimer: 0,
                    laserRange: 1.0, laserDamage: 1.0, multiLevel: 1, crossLevel: 0, continuousLaserTimer: 0
                };
                
                bots = []; for(let i=0; i<maxBots; i++) spawnBot();
                foods = []; for(let i=0; i<maxFoods; i++) spawnFood();
                for(let i=0; i<35; i++) spawnHeart();
                
                spawnBox(); spawnBox(); spawnRedBox(); spawnOrb();
                resetAbilities(); cannonShots = []; pushHands = [];
                applyCharacter(true);
                floatingTexts.push({ x: player.x, y: player.y - 120, text: `NIVEL ${levelIndex + 1}: ${String(LV.nombre).toUpperCase()} · ${DIFFS[difficulty].label}`, icon: "star", iconBoth: true, color: DIFFS[difficulty].color, life: 180, size: 30 });
                applyRissosMode();
            }

            function spawnBot() { bots.push({ x: Math.random() * worldW, y: Math.random() * worldH, r: Math.random() * 20 + 10, color: randomColor(), name: randomName(), vx: (Math.random() - 0.5) * 4, vy: (Math.random() - 0.5) * 4, hp: LV.bots.vida, maxHp: LV.bots.vida, lastShootTime: 0, dead: false, lastBurnTime: 0 }); }
            function spawnFood() { foods.push({ x: Math.random() * worldW, y: Math.random() * worldH, r: 3.5, color: randomColor() }); }

            // Al eliminar un enemigo suelta la mitad de su masa en bolitas que salen disparadas
            function dropMass(victim) {
                let total = victim.r * 0.5;
                let count = Math.max(5, Math.min(24, Math.round(victim.r / 3)));
                let value = total / count;
                for (let i = 0; i < count; i++) {
                    let ang = Math.random() * Math.PI * 2;
                    let spd = 3 + Math.random() * 6;
                    foods.push({
                        x: victim.x + Math.cos(ang) * victim.r * 0.4, y: victim.y + Math.sin(ang) * victim.r * 0.4,
                        vx: Math.cos(ang) * spd, vy: Math.sin(ang) * spd,
                        r: 4 + Math.min(6, value * 2.5), color: victim.color || randomColor(),
                        value: value, dropped: true, life: 1800, delay: 12
                    });
                }
            }

            function takeDamage(target, amount) {
                if(target === player && player.invulnTimer > 0) return;
                if(target === player && player.nightmare && player.rhinoTimer <= 0) {
                    // Nightmare Star: un solo golpe te mata
                    if (!player.dead) { player.hp = 0; player.dead = true; floatingTexts.push({ x: player.x, y: player.y, text: "UN GOLPE BASTÓ", icon: "burst", color: "#FF0040", life: 60, size: 22 }); handlePlayerDeath(); }
                    return;
                }
                if(target === player && player.rhinoTimer > 0) {
                    if (Math.random() < 0.15) floatingTexts.push({ x: player.x, y: player.y - player.r - 20, text: "BLINDADO", icon: "shield", color: "#C0C4CE", life: 30, size: 16 });
                    return;
                }
                if(target === player && player.shields > 0) {
                    player.shields--; floatingTexts.push({ x: player.x, y: player.y - player.r - 20, text: "¡ESCUDO ABSORBIÓ DAÑO!", icon: "shield", color: "#C0C0C0", life: 40, size: 16 });
                    return;
                }
                let dmgMult = Math.max(0.25, 18 / Math.max(18, target.r));
                let realDamage = amount * dmgMult; target.hp -= realDamage;
                floatingTexts.push({ x: target.x, y: target.y - target.r - 10, text: `-${Math.ceil(realDamage)}`, color: "#FF3333", life: 30, size: 24 });

                if(target === player && player.hp <= 0 && !player.dead) { player.hp = 0; player.dead = true; handlePlayerDeath(); } 
                else if(target !== player && target.hp <= 0 && !target.dead) { 
                    target.dead = true; 
                    dropMass(target);
                    floatingTexts.push({ x: target.x, y: target.y, text: "¡DESTRUIDO!", icon: "burst", color: "#FF3333", life: 40, size: 22 }); 
                }
            }

            function applyUpgrade(type) {
                if(type === 'range') player.laserRange += 0.4;
                if(type === 'damage') player.laserDamage += 0.5;
                if(type === 'multi') { 
                    player.multiLevel = Math.min(10, player.multiLevel + 1); 
                    floatingTexts.push({ x: player.x, y: player.y - 40, text: `MÚLTIPLE Nv.${player.multiLevel}`, color: "#CC33FF", life: 60, size: 20 });
                }
                if(type === 'cross') { 
                    player.crossLevel = Math.min(10, player.crossLevel + 1); 
                    floatingTexts.push({ x: player.x, y: player.y - 40, text: `CRUZ Nv.${player.crossLevel}`, color: "#CC33FF", life: 60, size: 20 });
                }
                const ABIL_NAMES = { cannon: ['SÚPER CAÑÓN', '#FF8C00'], push: ['EMPUJE', '#33FF66'], rhino: ['PIEL DE RHINO', '#C0C4CE'], reflect: ['ESCUDO REFLECTOR', '#00FFFF'] };
                if (ABIL_NAMES[type]) {
                    let key = type + 'Lvl';
                    player[key] = Math.min(10, (player[key] || 0) + 1);
                    floatingTexts.push({ x: player.x, y: player.y - 40, text: `${ABIL_NAMES[type][0]} Nv.${player[key]}`, color: ABIL_NAMES[type][1], life: 70, size: 20 });
                }
                orbModal.style.display = 'none'; isPaused = false;
            }

            function lvlTag(lvl) {
                let next = Math.min(10, (lvl || 0) + 1);
                let txt = (lvl || 0) >= 10 ? 'NIVEL MÁX' : 'Nv. ' + next;
                return '<span style="color:#FFD700;font-size:14px;display:block;">' + txt + '</span>';
            }
            function setOrbBtn(btn, color, html, fn) {
                btn.style.display = 'flex'; btn.style.borderColor = color; btn.innerHTML = html; btn.onclick = fn;
            }

            function showOrbMenu(type) {
                isPaused = true; isFiring = false; keysDown.clear();
                orbModal.style.display = 'block'; orbModal.style.borderColor = orbColor(type);
                [btn1, btn2, btn3, btn4].forEach(b => { b.onclick = null; b.style.display = 'none'; });

                if(type === 'celeste') {
                    // Celeste: alcance/daño + habilidades de resistencia
                    orbTitle.style.color = '#00FFFF'; orbTitle.innerHTML = svgOrb('#00FFFF', 'orb-grad-c') + "<span>ORBE CELESTE</span>";
                    setOrbBtn(btn1, '#00FFFF', ICON_RANGE + "<span>MAYOR DISTANCIA</span>", () => applyUpgrade('range'));
                    setOrbBtn(btn2, '#00FFFF', ICON_DAMAGE + "<span>MAYOR DAÑO</span>", () => applyUpgrade('damage'));
                    setOrbBtn(btn3, '#C0C4CE', ICON_RHINO + "<span>PIEL DE RHINO</span><span style='font-size:11px;color:#aaa'>[Q]</span>" + lvlTag(player.rhinoLvl), () => applyUpgrade('rhino'));
                    setOrbBtn(btn4, '#00FFFF', ICON_REFLECT + "<span>ESCUDO REFLECTOR</span><span style='font-size:11px;color:#aaa'>[E]</span>" + lvlTag(player.reflectLvl), () => applyUpgrade('reflect'));
                } else if(type === 'naranja') {
                    orbTitle.style.color = '#FF8C00'; orbTitle.innerHTML = svgOrb('#FF8C00', 'orb-grad-n') + "<span>ORBE NARANJA</span>";
                    setOrbBtn(btn1, '#FF8C00', ICON_CANNON + "<span>SÚPER CAÑÓN</span><span style='font-size:11px;color:#aaa'>[X]</span>" + lvlTag(player.cannonLvl), () => applyUpgrade('cannon'));
                    setOrbBtn(btn2, '#33FF66', ICON_PUSH + "<span>EMPUJE</span><span style='font-size:11px;color:#aaa'>[F]</span>" + lvlTag(player.pushLvl), () => applyUpgrade('push'));
                } else {
                    orbTitle.style.color = '#CC33FF'; orbTitle.innerHTML = svgOrb('#CC33FF', 'orb-grad-m') + "<span>ORBE MORADO</span>";
                    let nextMulti = Math.min(10, player.multiLevel + 1);
                    let nextCross = Math.min(10, player.crossLevel + 1);
                    setOrbBtn(btn1, '#CC33FF', `${ICON_MULTI}<span>DISPARO MÚLTIPLE</span><span style="color:#FFD700;font-size:14px;display:block;">Nv. ${nextMulti}</span>`, () => applyUpgrade('multi'));
                    setOrbBtn(btn2, '#CC33FF', `${ICON_CROSS}<span>DISPARO EN CRUZ</span><span style="color:#FFD700;font-size:14px;display:block;">Nv. ${nextCross}</span>`, () => applyUpgrade('cross'));
                }
            }

            function updateLeaderboard() {
                let allStars = [player, ...bots].filter(s => !s.dead); allStars.sort((a, b) => b.r - a.r); let topStars = allStars.slice(0, 10);
                let html = ""; topStars.forEach((s, idx) => { let isMe = (s === player); html += `<div class="lb-item ${isMe ? 'me' : ''}"><span>${idx + 1}. ${s.name}</span><span>${Math.round(s.r)} pt</span></div>`; });
                lbList.innerHTML = html;
            }

            function update() {
                if (victoryTimer > 0) { victoryTimer--; if (victoryTimer === 0 && !isGameOver) showVictory(); }
                if(Math.random() < 0.003 && boxes.length < 5) spawnBox();
                if(Math.random() < 0.0015 && redBoxes.length < 2) spawnRedBox();
                if(Math.random() < 0.002 && orbs.length < LV.orbes_max) spawnOrb();

                if (!player.dead && player.continuousLaserTimer > 0) {
                    player.continuousLaserTimer--;
                    if (player.continuousLaserTimer % 4 === 0 && player.r > 12) {
                        let targetX = (screenMouseX - canvas.width / 2) / zoom + camX + canvas.width / 2;
                        let targetY = (screenMouseY - canvas.height / 2) / zoom + camY + canvas.height / 2;
                        let dx = targetX - player.x, dy = targetY - player.y;
                        let angle = Math.atan2(dy, dx);
                        
                        fireLaserProjectile(player, angle, 20, 60 * player.laserRange, "#FF0000", player.laserDamage * 0.6);
                        if (player.continuousLaserTimer % 12 === 0) playSfx("laser", 0.3);
                        player.r = Math.max(10, player.r - 0.1); 
                    }
                }

                if (!meteor.isBoss) {
                    meteor.orbitAngle += 0.0012; 
                    meteor.x = (worldW / 2) + Math.cos(meteor.orbitAngle) * meteor.orbitRadius; 
                    meteor.y = (worldH / 2) + Math.sin(meteor.orbitAngle) * meteor.orbitRadius;
                } else if (!meteor.dead && cinematicTimer <= 0) {
                    if (meteor.hp <= meteor.maxHp * 0.5 && !meteor.isPhase2) {
                        meteor.isPhase2 = true;
                        floatingTexts.push({ x: meteor.x, y: meteor.y - 140, text: `FASE 2: ${LV.jefe.nombre_fase2} ACTIVADA`, icon: "eye", iconBoth: true, color: "#FF0000", life: 180, size: 36 });
                    }
                    if (meteor.isPhase2 && !meteor.phase2MusicStarted) { meteor.phase2MusicStarted = true; }

                    let bossSpeed = meteor.isPhase2 ? LV.jefe.velocidad_fase2 : LV.jefe.velocidad;
                    if (!player.dead) {
                        let dx = player.x - meteor.x; let dy = player.y - meteor.y; let dist = Math.hypot(dx, dy);
                        if (dist > 0) { meteor.x += (dx/dist) * bossSpeed; meteor.y += (dy/dist) * bossSpeed; }
                    }

                    meteor.shootAngle += 0.22;
                    if (Date.now() % 4 === 0) {
                        lasers.push({ x: meteor.x, y: meteor.y, vx: Math.cos(meteor.shootAngle) * 5, vy: Math.sin(meteor.shootAngle) * 5, life: 160, owner: meteor, color: "#FFA500", damageMult: LV.jefe.potencia_balas, r: 9, isStar: true });
                    }

                    if (meteor.isPhase2) {
                        meteor.laserTimer++;
                        if (meteor.laserTimer >= LV.jefe.espera_laser_frames && meteor.laserChargeTimer <= 0 && meteor.laserSweepTimer <= 0) {
                            meteor.laserChargeTimer = 60; 
                            let angleToPlayer = Math.atan2(player.y - meteor.y, player.x - meteor.x);
                            meteor.laserAngle = angleToPlayer - 0.7; 
                            floatingTexts.push({ x: meteor.x, y: meteor.y - 100, text: "¡LÁSER CÍCLOPE INMINENTE!", icon: "eye", color: "#FF0055", life: 60, size: 28 });
                        }
                        if (meteor.laserChargeTimer > 0) {
                            meteor.laserChargeTimer--;
                            if (meteor.laserChargeTimer === 0) { meteor.laserSweepTimer = 240; meteor.laserTimer = 0; }
                        }
                        if (meteor.laserSweepTimer > 0) {
                            meteor.laserSweepTimer--;
                            meteor.laserAngle += 0.010; 
                            if (!player.dead) {
                                let ux = Math.cos(meteor.laserAngle), uy = Math.sin(meteor.laserAngle);
                                let vx = player.x - meteor.x, vy = player.y - meteor.y;
                                let proj = vx * ux + vy * uy;
                                if (proj > 0) { 
                                    let distSq = (vx * vx + vy * vy) - (proj * proj);
                                    let beamRadius = 35; 
                                    if (distSq < (beamRadius + player.r) * (beamRadius + player.r)) { takeDamage(player, LV.jefe.potencia_laser); }
                                }
                            }
                        }
                    }
                }
                meteor.angle += 0.003;

                if(!blackHole.dead) { 
                    blackHole.r += LV.agujero_negro.crecimiento; blackHole.hp = Math.min(blackHole.maxHp, blackHole.hp + 0.02);
                    let pullRadius = blackHole.r * 5.5; let dPlayer = Math.hypot(blackHole.x - player.x, blackHole.y - player.y);
                    if(!player.dead && !(player.rhinoTimer > 0) && dPlayer < pullRadius && dPlayer > 0) {
                        let pullForce = (1 - dPlayer / pullRadius) * LV.agujero_negro.fuerza_atraccion;
                        player.x += ((blackHole.x - player.x) / dPlayer) * pullForce; player.y += ((blackHole.y - player.y) / dPlayer) * pullForce;
                        if(Math.random() < 0.25) particles.push({ x: player.x, y: player.y, vx: ((blackHole.x - player.x) / dPlayer) * 3, vy: ((blackHole.y - player.y) / dPlayer) * 3, color: "#8A2BE2", life: 12 });
                    }
                }

                if(player.invulnTimer > 0) player.invulnTimer--; if(player.fireTimer > 0) player.fireTimer--; if(player.speedBoostTimer > 0) player.speedBoostTimer--;
                if(player.fireTimer > 0 && !player.dead) { for(let i=0; i<2; i++) particles.push({ x: player.x + (Math.random() - 0.5) * player.r * 1.5, y: player.y + (Math.random() - 0.5) * player.r * 1.5, vx: (Math.random() - 0.5) * 2, vy: -Math.random() * 3, color: Math.random() > 0.5 ? "#FF4500" : "#FFD700", life: 20 }); }

                let allStars = [player, ...bots].filter(s => !s.dead); const now = Date.now();

                if (fireCooldown > 0) fireCooldown--;
                if (isFiring && !player.dead && fireCooldown <= 0) { shootLaser(); fireCooldown = FIRE_RATE; }

                if(!player.dead && cinematicTimer <= 0) {
                    let dx = 0, dy = 0;
                    if (keysDown.has('KeyW') || keysDown.has('ArrowUp')) dy -= 1;
                    if (keysDown.has('KeyS') || keysDown.has('ArrowDown')) dy += 1;
                    if (keysDown.has('KeyA') || keysDown.has('ArrowLeft')) dx -= 1;
                    if (keysDown.has('KeyD') || keysDown.has('ArrowRight')) dx += 1;
                    let dist = Math.sqrt(dx*dx + dy*dy);
                    let baseSpeed = player.speed * Math.max(0.35, 20 / (player.r + 5));

                    if (player.speedBoostTimer > 0) baseSpeed *= 1.7;

                    // Sprint con SHIFT (estamina 100)
                    let wantSprint = (keysDown.has('ShiftLeft') || keysDown.has('ShiftRight')) && dist > 0;
                    if (wantSprint && !player.exhausted && player.stamina > 0) {
                        baseSpeed *= SPRINT_MULT;
                        player.stamina = Math.max(0, player.stamina - STAMINA_DRAIN);
                        player.staminaDelay = 40;
                        if (player.stamina <= 0) { player.exhausted = true; floatingTexts.push({ x: player.x, y: player.y - player.r - 20, text: "SIN ESTAMINA", color: "#FFCC00", life: 35, size: 14 }); }
                        if (Math.random() < 0.6) particles.push({ x: player.x - (dx / dist) * player.r, y: player.y - (dy / dist) * player.r, vx: -(dx / dist) * 2 + (Math.random() - 0.5), vy: -(dy / dist) * 2 + (Math.random() - 0.5), color: "#FFE066", life: 14 });
                    } else {
                        if (player.staminaDelay > 0) player.staminaDelay--;
                        else player.stamina = Math.min(STAMINA_MAX, player.stamina + STAMINA_REGEN);
                        if (player.exhausted && player.stamina >= 25) player.exhausted = false;
                    }
                    if (dashTimer > 0) { baseSpeed *= 3.8; dashTimer--; }

                    if (dist > 0) { player.x += (dx / dist) * baseSpeed; player.y += (dy / dist) * baseSpeed; }
                    player.x = Math.max(player.r, Math.min(worldW - player.r, player.x)); player.y = Math.max(player.r, Math.min(worldH - player.r, player.y));
                }

                updateAbyssLaser();
                updateAbilities();
                updateNightmare();
                updateBossExtras();

                bots.forEach(bot => {
                    let botSpeed = 3 * LV.bots.velocidad * Math.max(0.35, 20 / (bot.r + 5));
                    if(Math.random() < 0.02) { bot.vx = (Math.random() - 0.5) * 4; bot.vy = (Math.random() - 0.5) * 4; }
                    bot.x += bot.vx * (botSpeed / 2); bot.y += bot.vy * (botSpeed / 2);
                    bot.x = Math.max(bot.r, Math.min(worldW - bot.r, bot.x)); bot.y = Math.max(bot.r, Math.min(worldH - bot.r, bot.y));

                    if (now - (bot.lastShootTime || 0) > LV.bots.espera_disparo_ms && Math.random() < 0.03 && bot.r > 12) {
                        let target = (!blackHole.dead && Math.hypot(blackHole.x - bot.x, blackHole.y - bot.y) < 600) ? blackHole : 
                                     (meteor.isBoss && !meteor.dead && Math.hypot(meteor.x - bot.x, meteor.y - bot.y) < 600) ? meteor :
                                     (!player.dead && Math.hypot(player.x - bot.x, player.y - bot.y) < 550) ? player : 
                                     bots.find(b => b !== bot && !b.dead && Math.hypot(b.x - bot.x, b.y - bot.y) < 400);

                        if(target) {
                            let dx = target.x - bot.x, dy = target.y - bot.y, dist = Math.hypot(dx, dy);
                            if(dist > 0) { lasers.push({ x: bot.x, y: bot.y, vx: (dx / dist) * 13, vy: (dy / dist) * 13, life: 65, owner: bot, color: "#FF6633", damageMult: LV.bots.potencia_disparo, isStar: false }); bot.lastShootTime = now; bot.r = Math.max(8, bot.r - 0.3); }
                        }
                    }
                });

                if (cinematicTimer > 0) {
                    cinematicTimer--;
                    meteor.r += (150 * (LV.jefe.tamano || 1) - meteor.r) * 0.03; 
                    zoom += (0.6 - zoom) * 0.05;
                    camX += (meteor.x - canvas.width / 2 - camX) * 0.06; 
                    camY += (meteor.y - canvas.height / 2 - camY) * 0.06;
                } else {
                    let focusTarget = (!player.dead) ? player : (allStars[0] || {x: worldW/2, y: worldH/2, r: 15});
                    let targetZoom = Math.max(0.25, 25 / Math.max(25, focusTarget.r * 0.6));
                    zoom += (targetZoom - zoom) * 0.05;
                    camX += (focusTarget.x - canvas.width / 2 - camX) * 0.1; camY += (focusTarget.y - canvas.height / 2 - camY) * 0.1;
                }

                for(let i = lasers.length - 1; i >= 0; i--) {
                    let l = lasers[i]; l.x += l.vx; l.y += l.vy; l.life--; let hit = false; let dmg = 22 * (l.damageMult || 1);

                    if(!blackHole.dead && Math.hypot(l.x - blackHole.x, l.y - blackHole.y) < blackHole.r) {
                        blackHole.hp -= dmg; blackHole.r = Math.max(25, blackHole.r - 0.25);
                        if(blackHole.hp <= 0 && !blackHole.dead) { 
                            blackHole.dead = true; unlockAbyssLaser(); 
                            playSfx("bh_death", 2.5); 
                            meteor.isBoss = true; cinematicTimer = 180;
                            if (bgMusic && sfxData["luna_musica"] && sfxData["luna_musica"].length > 0) {
                                bgMusic.pause(); bgMusic.src = sfxData["luna_musica"][0]; usingBossTrack = true; bgMusic.currentTime = 0; bgMusic.play().catch(e => console.log(e));
                            }
                            floatingTexts.push({ x: meteor.x, y: meteor.y - 120, text: "LA LUNA DESPIERTA", icon: "warning", iconBoth: true, color: "#FF4500", life: 180, size: 40 });
                        } 
                        hit = true;
                    }

                    if(meteor.isBoss && !meteor.dead && l.owner !== meteor && Math.hypot(l.x - meteor.x, l.y - meteor.y) < meteor.r) {
                        meteor.hp -= dmg; hit = true;
                        if(meteor.hp <= 0 && !meteor.dead) {
                            meteor.dead = true; playSfx("bh_death", 2.5); 
                            floatingTexts.push({ x: meteor.x, y: meteor.y, text: "VICTORIA GALÁCTICA", icon: "star", iconBoth: true, color: "#FFD700", life: 300, size: 50 }); onBossDefeated();
                            if (bgMusic && audioSrc) { bgMusic.pause(); bgMusic.src = audioSrc; usingBossTrack = false; bgMusic.currentTime = 0; bgMusic.play().catch(e => console.log(e)); }
                        }
                    }

                    if(!hit) {
                        for(let s of allStars) {
                            if(s.dead || s === l.owner) continue;
                            if(Math.hypot(l.x - s.x, l.y - s.y) < (s.r + (l.r||5))) {
                                if (s === player && player.reflectTimer > 0) { reflectLaser(l); break; }
                                hit = true; takeDamage(s, dmg);
                                for(let k=0; k<4; k++) particles.push({ x: l.x, y: l.y, vx: (Math.random() - 0.5)*4, vy: (Math.random() - 0.5)*4, color: l.color, life: 15 });
                                break;
                            }
                        }
                    }
                    if(hit || l.life <= 0) lasers.splice(i, 1);
                }

                for(let i = orbs.length - 1; i >= 0; i--) { let o = orbs[i]; if(!player.dead && Math.hypot(player.x - o.x, player.y - o.y) < player.r + o.r) { playSfx("orb"); showOrbMenu(o.type); orbs.splice(i, 1); } }
                
                for(let i = redBoxes.length - 1; i >= 0; i--) {
                    let rb = redBoxes[i];
                    if(!player.dead && Math.hypot(player.x - rb.x, player.y - rb.y) < player.r + rb.r) {
                        redBoxes.splice(i, 1); playSfx("box");
                        player.continuousLaserTimer = 300; 
                        floatingTexts.push({x: player.x, y: player.y - 40, text: "¡MODO LÁSER CONTINUO!", icon: "dot", color: "#FF0000", life: 60, size: 22});
                    }
                }
                
                for(let i = boxes.length - 1; i >= 0; i--) {
                    let b = boxes[i];
                    if(!player.dead && Math.hypot(player.x - b.x, player.y - b.y) < player.r + b.r) {
                        boxes.splice(i, 1); playSfx("box"); let rand = Math.random();
                        if(rand < 0.50) { player.hp += 50; if(player.hp > player.maxHp) player.maxHp = player.hp; player.r += 2; floatingTexts.push({x: player.x, y: player.y - player.r - 15, text: "+50 HP MAX", icon: "heart", color: "#33FF66", life: 50, size: 22}); } 
                        else if(rand < 0.625) { if(player.shields < 4) { player.shields++; floatingTexts.push({x: player.x, y: player.y - 30, text: "ESCUDO +1", icon: "shield", color: "#C0C0C0", life: 45, size: 18}); } } 
                        else if(rand < 0.750) { player.fireTimer = 360; floatingTexts.push({x: player.x, y: player.y - 30, text: "¡AURA DE FUEGO!", icon: "fire", color: "#FF4500", life: 50, size: 22}); } 
                        else if(rand < 0.875) { player.hasInvulnCharge = true; floatingTexts.push({x: player.x, y: player.y - 30, text: "¡FANTASMA LISTO!", icon: "ghost", color: "#00FFFF", life: 55, size: 18}); } 
                        else { player.speedBoostTimer = 300; floatingTexts.push({x: player.x, y: player.y - 30, text: "¡VELOCIDAD!", icon: "bolt", color: "#FFFF33", life: 45, size: 18}); }
                    }
                }

                for(let i = hearts.length - 1; i >= 0; i--) { let h = hearts[i]; if(!player.dead && Math.hypot(player.x - h.x, player.y - h.y) < player.r + h.r) { hearts.splice(i, 1); spawnHeart(); playSfx("food"); player.hp += 20; if(player.hp > player.maxHp) player.maxHp = player.hp; floatingTexts.push({ x: player.x, y: player.y - player.r - 15, text: "+20 HP", icon: "heart", color: "#FF3366", life: 40, size: 18 }); } }

                if(!meteor.dead) { allStars.forEach(s => { if(s === player && player.nightmare) return; if(Math.hypot(s.x - meteor.x, s.y - meteor.y) < s.r + meteor.r * 0.85) takeDamage(s, 100); }); }
                
                if(!blackHole.dead) {
                    allStars.forEach(s => {
                        if(!(s === player && player.nightmare) && Math.hypot(s.x - blackHole.x, s.y - blackHole.y) < s.r + blackHole.r * 0.8) {
                            if(s.r > blackHole.r * 1.25) { 
                                blackHole.dead = true; unlockAbyssLaser(); s.r += 35; 
                                playSfx("bh_death", 2.5);
                                meteor.isBoss = true; cinematicTimer = 180;
                                if (bgMusic && sfxData["luna_musica"] && sfxData["luna_musica"].length > 0) {
                                    bgMusic.pause(); bgMusic.src = sfxData["luna_musica"][0]; usingBossTrack = true; bgMusic.currentTime = 0; bgMusic.play().catch(e => console.log(e));
                                }
                            } 
                            else { 
                                if(s === player && player.rhinoTimer > 0) { /* blindado: el agujero no te traga */ }
                                else if(s === player && !player.dead) { player.hp = 0; player.dead = true; handlePlayerDeath(); } else if(s !== player) { s.dead = true; } 
                            }
                        }
                    });
                }

                for(let i = foods.length - 1; i >= 0; i--) {
                    let f = foods[i];
                    if (f.dropped) {
                        f.x += f.vx; f.y += f.vy; f.vx *= 0.92; f.vy *= 0.92;
                        f.x = Math.max(f.r, Math.min(worldW - f.r, f.x)); f.y = Math.max(f.r, Math.min(worldH - f.r, f.y));
                        f.life--; if (f.delay > 0) f.delay--;
                        if (f.life <= 0) { foods.splice(i, 1); continue; }
                        if (f.delay > 0) continue;
                    }
                    for(let e of allStars) {
                        if(Math.hypot(e.x - f.x, e.y - f.y) < e.r) {
                            let gain = f.dropped ? f.value : 0.08;
                            e.r += gain;
                            if(e === player) { playSfx("food", f.dropped ? 0.5 : 1.0); player.hp += f.dropped ? gain * 2.5 : 0.2; if(player.hp > player.maxHp) player.maxHp = player.hp; }
                            foods.splice(i, 1); if (!f.dropped) spawnFood(); break;
                        }
                    }
                }

                for(let i = 0; i < allStars.length; i++) {
                    for(let j = i + 1; j < allStars.length; j++) {
                        let e1 = allStars[i], e2 = allStars[j]; if (e1.dead || e2.dead) continue; let d = Math.hypot(e1.x - e2.x, e1.y - e2.y);
                        if(d < e1.r + e2.r) { if(e1 === player && player.fireTimer > 0 && (now - (e2.lastBurnTime || 0) > 500)) { takeDamage(e2, 40); e2.lastBurnTime = now; } else if (e2 === player && player.fireTimer > 0 && (now - (e1.lastBurnTime || 0) > 500)) { takeDamage(e1, 40); e1.lastBurnTime = now; } }
                        let bigger = e1.r > e2.r ? e1 : e2; let smaller = e1.r > e2.r ? e2 : e1;
                        if(d < bigger.r * 0.75 && bigger.r > smaller.r * 1.15) {
                            if(smaller === player && (player.invulnTimer > 0 || player.rhinoTimer > 0 || player.nightmare)) continue;
                            bigger.r += smaller.r * 0.35;
                            if(bigger === player) { player.hp += 35; if(player.hp > player.maxHp) player.maxHp = player.hp; } else { bigger.hp = Math.min(bigger.maxHp, bigger.hp + 35); }
                            if(smaller === player && !player.dead) { smaller.hp = 0; smaller.dead = true; handlePlayerDeath(); } else { smaller.dead = true; }
                        }
                    }
                }

                for(let i = particles.length - 1; i >= 0; i--) { let p = particles[i]; p.x += p.vx; p.y += p.vy; p.life--; if(p.life <= 0) particles.splice(i, 1); }
                for(let i = floatingTexts.length - 1; i >= 0; i--) { let ft = floatingTexts[i]; ft.y -= 0.8; ft.life--; if(ft.life <= 0) floatingTexts.splice(i, 1); }
                bots = bots.filter(b => !b.dead); while(bots.length < maxBots) spawnBot();
                updateLeaderboard();
            }

            // === ICONOS DIBUJADOS EN CANVAS (reemplazan a los emojis) ===
            function heartPath(c, x, y, s) {
                const t = y - s * 0.45;
                c.beginPath();
                c.moveTo(x, t + s * 0.25);
                c.bezierCurveTo(x, t, x - s * 0.5, t, x - s * 0.5, t + s * 0.28);
                c.bezierCurveTo(x - s * 0.5, t + s * 0.55, x - s * 0.1, t + s * 0.7, x, t + s * 0.9);
                c.bezierCurveTo(x + s * 0.1, t + s * 0.7, x + s * 0.5, t + s * 0.55, x + s * 0.5, t + s * 0.28);
                c.bezierCurveTo(x + s * 0.5, t, x, t, x, t + s * 0.25);
                c.closePath();
            }
            function starPath(c, x, y, n, rOut, rIn, rot) {
                c.beginPath();
                for (let i = 0; i < n * 2; i++) {
                    let r = (i % 2 === 0) ? rOut : rIn;
                    let a = rot + (Math.PI * i) / n;
                    c.lineTo(x + Math.cos(a) * r, y + Math.sin(a) * r);
                }
                c.closePath();
            }
            function flamePath(c, x, y, s) {
                c.beginPath();
                c.moveTo(x, y - s * 0.5);
                c.bezierCurveTo(x + s * 0.12, y - s * 0.28, x + s * 0.42, y - s * 0.12, x + s * 0.38, y + s * 0.16);
                c.bezierCurveTo(x + s * 0.35, y + s * 0.4, x + s * 0.16, y + s * 0.5, x, y + s * 0.5);
                c.bezierCurveTo(x - s * 0.16, y + s * 0.5, x - s * 0.35, y + s * 0.4, x - s * 0.38, y + s * 0.16);
                c.bezierCurveTo(x - s * 0.4, y - s * 0.04, x - s * 0.24, y - s * 0.14, x - s * 0.18, y - s * 0.3);
                c.bezierCurveTo(x - s * 0.06, y - s * 0.16, x - s * 0.04, y - s * 0.36, x, y - s * 0.5);
                c.closePath();
            }
            function shieldPath(c, x, y, s) {
                c.beginPath();
                c.moveTo(x, y - s * 0.5);
                c.lineTo(x + s * 0.4, y - s * 0.34);
                c.lineTo(x + s * 0.4, y - s * 0.02);
                c.quadraticCurveTo(x + s * 0.38, y + s * 0.34, x, y + s * 0.5);
                c.quadraticCurveTo(x - s * 0.38, y + s * 0.34, x - s * 0.4, y - s * 0.02);
                c.lineTo(x - s * 0.4, y - s * 0.34);
                c.closePath();
            }

            // Dibuja un icono centrado en (x, y) de tamaño s
            function drawIcon(c, type, x, y, s, color) {
                c.save();
                c.shadowBlur = 0; c.lineJoin = "round"; c.lineCap = "round";
                switch (type) {
                    case 'heart': {
                        heartPath(c, x, y, s);
                        let g = c.createLinearGradient(x, y - s * 0.45, x, y + s * 0.45);
                        g.addColorStop(0, "#FF6B8A"); g.addColorStop(1, "#C8102E");
                        c.fillStyle = g; c.fill();
                        c.lineWidth = Math.max(1, s * 0.07); c.strokeStyle = "#7A0019"; c.stroke();
                        c.beginPath(); c.ellipse(x - s * 0.24, y - s * 0.17, s * 0.09, s * 0.06, -0.6, 0, Math.PI * 2);
                        c.fillStyle = "rgba(255,255,255,0.8)"; c.fill();
                        break;
                    }
                    case 'heartEmpty': {
                        heartPath(c, x, y, s);
                        c.fillStyle = "#1a1a1a"; c.fill();
                        c.lineWidth = Math.max(1, s * 0.07); c.strokeStyle = "#555"; c.stroke();
                        break;
                    }
                    case 'ghost': {
                        const r = s * 0.4, top = y - s * 0.08, bot = y + s * 0.45;
                        c.beginPath();
                        c.moveTo(x - r, bot);
                        c.lineTo(x - r, top);
                        c.arc(x, top, r, Math.PI, 0);
                        c.lineTo(x + r, bot);
                        const n = 3, w = (2 * r) / n;
                        for (let i = 0; i < n; i++) { let x0 = x + r - i * w; c.quadraticCurveTo(x0 - w / 2, bot - s * 0.2, x0 - w, bot); }
                        c.closePath();
                        c.fillStyle = "rgba(235, 252, 255, 0.95)"; c.fill();
                        c.lineWidth = Math.max(1, s * 0.06); c.strokeStyle = color || "#00FFFF"; c.stroke();
                        c.fillStyle = "#102030";
                        c.beginPath(); c.ellipse(x - r * 0.38, top, s * 0.07, s * 0.11, 0, 0, Math.PI * 2); c.fill();
                        c.beginPath(); c.ellipse(x + r * 0.38, top, s * 0.07, s * 0.11, 0, 0, Math.PI * 2); c.fill();
                        c.beginPath(); c.ellipse(x, top + s * 0.2, s * 0.06, s * 0.08, 0, 0, Math.PI * 2); c.fill();
                        break;
                    }
                    case 'bolt': {
                        const p = [[0.12, -0.5], [-0.32, 0.06], [-0.04, 0.06], [-0.14, 0.5], [0.32, -0.08], [0.04, -0.08]];
                        c.beginPath();
                        p.forEach((pt, i) => { let X = x + pt[0] * s, Y = y + pt[1] * s; if (i === 0) c.moveTo(X, Y); else c.lineTo(X, Y); });
                        c.closePath();
                        let g = c.createLinearGradient(x, y - s * 0.5, x, y + s * 0.5);
                        g.addColorStop(0, "#FFF56B"); g.addColorStop(1, "#FFB000");
                        c.fillStyle = g; c.fill();
                        c.lineWidth = Math.max(1, s * 0.06); c.strokeStyle = "#A35F00"; c.stroke();
                        break;
                    }
                    case 'shield': case 'shieldEmpty': {
                        shieldPath(c, x, y, s);
                        if (type === 'shield') {
                            let g = c.createLinearGradient(x - s * 0.4, y - s * 0.5, x + s * 0.4, y + s * 0.5);
                            g.addColorStop(0, "#F5F5F5"); g.addColorStop(1, "#7E7E7E");
                            c.fillStyle = g; c.fill();
                            c.lineWidth = Math.max(1, s * 0.07); c.strokeStyle = "#FFFFFF"; c.stroke();
                            c.beginPath(); c.moveTo(x, y - s * 0.38); c.lineTo(x, y + s * 0.38);
                            c.moveTo(x - s * 0.28, y - s * 0.08); c.lineTo(x + s * 0.28, y - s * 0.08);
                            c.lineWidth = Math.max(1, s * 0.06); c.strokeStyle = "rgba(60,60,60,0.6)"; c.stroke();
                        } else {
                            c.fillStyle = "rgba(80, 80, 80, 0.3)"; c.fill();
                            c.lineWidth = 1; c.strokeStyle = "rgba(255,255,255,0.35)"; c.stroke();
                        }
                        break;
                    }
                    case 'burst': {
                        starPath(c, x, y, 10, s * 0.5, s * 0.26, -Math.PI / 2);
                        c.fillStyle = "#FF4500"; c.fill();
                        c.lineWidth = Math.max(1, s * 0.05); c.strokeStyle = "#FFD700"; c.stroke();
                        starPath(c, x, y, 10, s * 0.3, s * 0.16, -Math.PI / 2);
                        c.fillStyle = "#FFE066"; c.fill();
                        break;
                    }
                    case 'star': {
                        starPath(c, x, y, 5, s * 0.5, s * 0.22, -Math.PI / 2);
                        let g = c.createLinearGradient(x, y - s * 0.5, x, y + s * 0.5);
                        g.addColorStop(0, "#FFF6A0"); g.addColorStop(1, "#FFB800");
                        c.fillStyle = g; c.fill();
                        c.lineWidth = Math.max(1, s * 0.06); c.strokeStyle = "#B8860B"; c.stroke();
                        break;
                    }
                    case 'fire': {
                        flamePath(c, x, y, s);
                        let g = c.createLinearGradient(x, y + s * 0.5, x, y - s * 0.5);
                        g.addColorStop(0, "#FF8C00"); g.addColorStop(1, "#FF2200");
                        c.fillStyle = g; c.fill();
                        c.lineWidth = Math.max(1, s * 0.05); c.strokeStyle = "#7A1000"; c.stroke();
                        flamePath(c, x, y + s * 0.17, s * 0.55);
                        c.fillStyle = "#FFE066"; c.fill();
                        break;
                    }
                    case 'eye': {
                        c.beginPath();
                        c.moveTo(x - s * 0.5, y);
                        c.quadraticCurveTo(x, y - s * 0.48, x + s * 0.5, y);
                        c.quadraticCurveTo(x, y + s * 0.48, x - s * 0.5, y);
                        c.closePath();
                        c.fillStyle = "#FFFFFF"; c.fill();
                        c.lineWidth = Math.max(1, s * 0.07); c.strokeStyle = "#FF0055"; c.stroke();
                        c.beginPath(); c.arc(x, y, s * 0.17, 0, Math.PI * 2); c.fillStyle = "#FF0033"; c.fill();
                        c.beginPath(); c.arc(x, y, s * 0.08, 0, Math.PI * 2); c.fillStyle = "#000"; c.fill();
                        c.beginPath(); c.arc(x - s * 0.05, y - s * 0.06, s * 0.035, 0, Math.PI * 2); c.fillStyle = "#FFF"; c.fill();
                        break;
                    }
                    case 'warning': {
                        c.beginPath();
                        c.moveTo(x, y - s * 0.45); c.lineTo(x + s * 0.5, y + s * 0.4); c.lineTo(x - s * 0.5, y + s * 0.4);
                        c.closePath();
                        c.fillStyle = "#FFC400"; c.fill();
                        c.lineWidth = Math.max(1, s * 0.08); c.strokeStyle = "#3a2a00"; c.stroke();
                        c.fillStyle = "#1a1200";
                        c.fillRect(x - s * 0.05, y - s * 0.18, s * 0.1, s * 0.32);
                        c.beginPath(); c.arc(x, y + s * 0.26, s * 0.06, 0, Math.PI * 2); c.fill();
                        break;
                    }
                    case 'crown': {
                        const pts = [[2, 16], [2, 6], [7, 10], [12, 2], [17, 10], [22, 6], [22, 16]];
                        const X = (px) => x + ((px - 12) / 24) * s, Y = (py) => y + ((py - 10.5) / 24) * s;
                        c.beginPath();
                        pts.forEach((p, i) => { if (i === 0) c.moveTo(X(p[0]), Y(p[1])); else c.lineTo(X(p[0]), Y(p[1])); });
                        c.closePath();
                        c.fillStyle = "#FFD700"; c.fill();
                        c.lineWidth = Math.max(1, s * 0.06); c.strokeStyle = "#8B6508"; c.stroke();
                        c.fillStyle = "#DAA520"; c.fillRect(X(2), Y(16), (20 / 24) * s, (3 / 24) * s);
                        c.fillStyle = "#FF3366"; c.beginPath(); c.arc(X(12), Y(12), s * 0.07, 0, Math.PI * 2); c.fill();
                        c.fillStyle = "#FFF3A0";
                        [[12, 2], [2, 6], [22, 6]].forEach(p => { c.beginPath(); c.arc(X(p[0]), Y(p[1]), s * 0.06, 0, Math.PI * 2); c.fill(); });
                        break;
                    }
                    case 'moon': {
                        let g = c.createRadialGradient(x - s * 0.15, y - s * 0.15, s * 0.05, x, y, s * 0.45);
                        g.addColorStop(0, "#FFC890"); g.addColorStop(1, "#C04000");
                        c.beginPath(); c.arc(x, y, s * 0.45, 0, Math.PI * 2); c.fillStyle = g; c.fill();
                        c.fillStyle = "rgba(120, 20, 0, 0.6)";
                        c.beginPath(); c.arc(x + s * 0.12, y - s * 0.1, s * 0.1, 0, Math.PI * 2); c.fill();
                        c.beginPath(); c.arc(x - s * 0.14, y + s * 0.14, s * 0.08, 0, Math.PI * 2); c.fill();
                        c.beginPath(); c.arc(x + s * 0.15, y + s * 0.2, s * 0.05, 0, Math.PI * 2); c.fill();
                        break;
                    }
                    case 'dot': {
                        let g = c.createRadialGradient(x - s * 0.12, y - s * 0.12, s * 0.03, x, y, s * 0.4);
                        g.addColorStop(0, "#FFFFFF"); g.addColorStop(0.35, "#FF2020"); g.addColorStop(1, "#7A0000");
                        c.beginPath(); c.arc(x, y, s * 0.38, 0, Math.PI * 2); c.fillStyle = g; c.fill();
                        c.lineWidth = 1; c.strokeStyle = "rgba(255,255,255,0.7)"; c.stroke();
                        break;
                    }
                    case 'vortex': {
                        c.beginPath(); c.arc(x, y, s * 0.45, 0, Math.PI * 2); c.fillStyle = "#05000A"; c.fill();
                        c.lineWidth = Math.max(1, s * 0.1); c.strokeStyle = "#CC33FF"; c.stroke();
                        c.beginPath(); c.arc(x, y, s * 0.24, 0.3, Math.PI * 1.7); c.lineWidth = Math.max(1, s * 0.07); c.strokeStyle = "#8A2BE2"; c.stroke();
                        break;
                    }
                }
                c.restore();
            }

            function draw() {
                ctx.fillStyle = LV.mundo.color_fondo; ctx.fillRect(0, 0, canvas.width, canvas.height);
                if (difficulty === 'nightmare') { ctx.fillStyle = "rgba(255, 0, 40, 0.07)"; ctx.fillRect(0, 0, canvas.width, canvas.height); }
                ctx.fillStyle = "rgba(255, 255, 255, 0.4)"; bgStarsLayer1.forEach(s => { let px = (s.x - camX * 0.08) % canvas.width; if (px < 0) px += canvas.width; let py = (s.y - camY * 0.08) % canvas.height; if (py < 0) py += canvas.height; ctx.beginPath(); ctx.arc(px, py, s.r, 0, Math.PI * 2); ctx.fill(); });
                ctx.fillStyle = "rgba(180, 200, 255, 0.7)"; bgStarsLayer2.forEach(s => { let px = (s.x - camX * 0.2) % canvas.width; if (px < 0) px += canvas.width; let py = (s.y - camY * 0.2) % canvas.height; if (py < 0) py += canvas.height; ctx.beginPath(); ctx.arc(px, py, s.r, 0, Math.PI * 2); ctx.fill(); });

                let shakeX = 0, shakeY = 0; 
                if(!player.dead && player.hp <= 40 && player.hp > 0) { shakeX = (Math.random() - 0.5) * 9; shakeY = (Math.random() - 0.5) * 9; }
                if(cinematicTimer > 0) { shakeX = (Math.random() - 0.5) * 6; shakeY = (Math.random() - 0.5) * 6; }

                ctx.save(); ctx.translate(canvas.width / 2 + shakeX, canvas.height / 2 + shakeY); ctx.scale(zoom, zoom); ctx.translate(-camX - canvas.width / 2, -camY - canvas.height / 2);
                ctx.strokeStyle = LV.mundo.color_borde; ctx.lineWidth = 6; ctx.strokeRect(0, 0, worldW, worldH);

                if (meteor.isBoss && !meteor.dead && meteor.isPhase2) {
                    if (meteor.laserChargeTimer > 0) {
                        ctx.save(); ctx.strokeStyle = "rgba(255, 0, 85, 0.6)"; ctx.lineWidth = 4; ctx.setLineDash([12, 12]);
                        ctx.beginPath(); ctx.moveTo(meteor.x, meteor.y); ctx.lineTo(meteor.x + Math.cos(meteor.laserAngle) * 2500, meteor.y + Math.sin(meteor.laserAngle) * 2500); ctx.stroke(); ctx.restore();
                    }
                    if (meteor.laserSweepTimer > 0) {
                        ctx.save(); let endX = meteor.x + Math.cos(meteor.laserAngle) * 2500; let endY = meteor.y + Math.sin(meteor.laserAngle) * 2500;
                        ctx.strokeStyle = "rgba(255, 0, 85, 0.35)"; ctx.lineWidth = 70; ctx.beginPath(); ctx.moveTo(meteor.x, meteor.y); ctx.lineTo(endX, endY); ctx.stroke();
                        ctx.strokeStyle = "#FF0055"; ctx.lineWidth = 35; ctx.beginPath(); ctx.moveTo(meteor.x, meteor.y); ctx.lineTo(endX, endY); ctx.stroke();
                        ctx.strokeStyle = "#FFFFFF"; ctx.lineWidth = 12; ctx.beginPath(); ctx.moveTo(meteor.x, meteor.y); ctx.lineTo(endX, endY); ctx.stroke(); ctx.restore();
                    }
                }

                if(!meteor.dead) {
                    ctx.save(); ctx.translate(meteor.x, meteor.y); ctx.rotate(meteor.angle); ctx.beginPath(); ctx.arc(0, 0, meteor.r, 0, Math.PI * 2); 
                    ctx.fillStyle = meteor.isBoss ? (meteor.isPhase2 ? LV.jefe.color_fase2 : LV.jefe.color) : "#A9A9A9"; 
                    if(meteor.isBoss) { ctx.shadowColor = meteor.isPhase2 ? LV.jefe.color_fase2 : LV.jefe.color; ctx.shadowBlur = 40; }
                    ctx.fill(); ctx.shadowBlur = 0;
                    if (meteor.isBoss) { const sc = meteor.r / 150; ctx.scale(sc * 1.5, sc * 1.5); }
                    meteor.craters.forEach(c => { ctx.beginPath(); ctx.arc(c.x, c.y, c.r, 0, Math.PI * 2); ctx.fillStyle = meteor.isBoss ? LV.jefe.color_crateres : "#696969"; ctx.fill(); }); 
                    if (meteor.isBoss && LV.jefe.color_detalles && meteor.veins) {
                        // grietas brillantes (modo nightmare)
                        ctx.strokeStyle = LV.jefe.color_detalles; ctx.lineWidth = 3; ctx.lineCap = "round"; ctx.lineJoin = "round";
                        ctx.shadowColor = LV.jefe.color_detalles; ctx.shadowBlur = 12 + Math.sin(Date.now() / 150) * 8;
                        meteor.veins.forEach(v => { ctx.beginPath(); v.forEach((pt, k) => k ? ctx.lineTo(pt[0], pt[1]) : ctx.moveTo(pt[0], pt[1])); ctx.stroke(); });
                        ctx.shadowBlur = 0;
                        ctx.fillStyle = LV.jefe.color_detalles; ctx.beginPath(); ctx.arc(0, 0, 10 + Math.sin(Date.now() / 120) * 3, 0, Math.PI * 2); ctx.fill();
                    }
                    ctx.restore();

                    if(meteor.isBoss) {
                        ctx.save(); ctx.translate(meteor.x, meteor.y);
                        let bossHpPct = Math.max(0, meteor.hp / meteor.maxHp); let barW = 220, barH = 14; 
                        ctx.fillStyle = "rgba(0,0,0,0.7)"; ctx.fillRect(-barW/2, -meteor.r - 40, barW, barH); 
                        ctx.fillStyle = meteor.isPhase2 ? "#FF0000" : "#FF4500"; ctx.fillRect(-barW/2 + 1, -meteor.r - 39, (barW - 2) * bossHpPct, barH - 2); 
                        ctx.strokeStyle = "#FFFFFF"; ctx.lineWidth = 2; ctx.strokeRect(-barW/2, -meteor.r - 40, barW, barH);
                        ctx.fillStyle = "#FFD700"; ctx.font = "bold 16px sans-serif"; ctx.textAlign = "center"; 
                        let bossLabel = `${meteor.isPhase2 ? LV.jefe.nombre_fase2 + ' (FASE 2)' : LV.jefe.nombre}: ${Math.ceil(meteor.hp)} / ${meteor.maxHp} HP`;
                        ctx.fillText(bossLabel, 0, -meteor.r - 48);
                        let blw = ctx.measureText(bossLabel).width; drawIcon(ctx, meteor.isPhase2 ? 'eye' : 'moon', -blw / 2 - 14, -meteor.r - 54, 20);
                        
                        ctx.restore();
                    }
                }

                if(!blackHole.dead) {
                    ctx.save(); ctx.translate(blackHole.x, blackHole.y); ctx.strokeStyle = "rgba(138, 43, 226, 0.15)"; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(0, 0, blackHole.r * 5.5, 0, Math.PI * 2); ctx.stroke();
                    let grad = ctx.createRadialGradient(0, 0, blackHole.r * 0.4, 0, 0, blackHole.r * 1.5); grad.addColorStop(0, "#000"); grad.addColorStop(0.5, "#8A2BE2"); grad.addColorStop(1, "rgba(255, 0, 128, 0)");
                    ctx.beginPath(); ctx.arc(0, 0, blackHole.r * 1.5, 0, Math.PI * 2); ctx.fillStyle = grad; ctx.fill(); ctx.beginPath(); ctx.arc(0, 0, blackHole.r, 0, Math.PI * 2); ctx.fillStyle = "#05000A"; ctx.fill();
                    let bhHpPct = Math.max(0, blackHole.hp / blackHole.maxHp); let barW = 160, barH = 12; ctx.fillStyle = "rgba(0,0,0,0.7)"; ctx.fillRect(-barW/2, -blackHole.r * 1.5 - 28, barW, barH); ctx.fillStyle = "#CC33FF"; ctx.fillRect(-barW/2 + 1, -blackHole.r * 1.5 - 27, (barW - 2) * bhHpPct, barH - 2); ctx.strokeStyle = "#FFFFFF"; ctx.lineWidth = 1; ctx.strokeRect(-barW/2, -blackHole.r * 1.5 - 28, barW, barH);
                    ctx.fillStyle = "#FFD700"; ctx.font = "bold 14px sans-serif"; ctx.textAlign = "center"; let bhLabel = `AGUJERO NEGRO: ${Math.ceil(blackHole.hp)} / ${blackHole.maxHp} HP`; ctx.fillText(bhLabel, 0, -blackHole.r * 1.5 - 35);
                    let bhw = ctx.measureText(bhLabel).width; drawIcon(ctx, 'vortex', -bhw / 2 - 13, -blackHole.r * 1.5 - 40, 18); ctx.restore();
                }

                boxes.forEach(b => { ctx.save(); ctx.translate(b.x, b.y); ctx.fillStyle = "#FFD700"; ctx.strokeStyle = "#FF8C00"; ctx.lineWidth = 3; ctx.fillRect(-b.r, -b.r, b.r*2, b.r*2); ctx.strokeRect(-b.r, -b.r, b.r*2, b.r*2); ctx.fillStyle = "#000"; ctx.font = "bold 16px sans-serif"; ctx.textAlign = "center"; ctx.fillText("?", 0, 5); ctx.restore(); });
                redBoxes.forEach(rb => { ctx.save(); ctx.translate(rb.x, rb.y); ctx.fillStyle = "#FF0000"; ctx.strokeStyle = "#8B0000"; ctx.lineWidth = 3; ctx.fillRect(-rb.r, -rb.r, rb.r*2, rb.r*2); ctx.strokeRect(-rb.r, -rb.r, rb.r*2, rb.r*2); drawIcon(ctx, 'fire', 0, 0, rb.r * 1.4); ctx.restore(); });

                orbs.forEach(o => { ctx.save(); ctx.translate(o.x, o.y); ctx.beginPath(); ctx.arc(0, 0, o.r, 0, Math.PI * 2); ctx.fillStyle = orbColor(o.type); ctx.fill(); ctx.strokeStyle = "white"; ctx.lineWidth = 2; ctx.stroke(); ctx.globalAlpha = 0.5; ctx.beginPath(); ctx.arc(0, 0, o.r + Math.sin(Date.now() / 150)*4, 0, Math.PI * 2); ctx.strokeStyle = orbColor(o.type); ctx.lineWidth = 2; ctx.stroke(); ctx.restore(); });
                hearts.forEach(h => { drawIcon(ctx, 'heart', h.x, h.y, 20); });
                ctx.textBaseline = "middle";
                particles.forEach(p => { ctx.beginPath(); ctx.arc(p.x, p.y, 3, 0, Math.PI * 2); ctx.fillStyle = p.color; ctx.fill(); });
                
                lasers.forEach(l => { 
                    if(l.isStar) {
                        ctx.save(); ctx.translate(l.x, l.y); ctx.rotate(Date.now() / 150); ctx.beginPath(); ctx.fillStyle = l.color;
                        for (let i = 0; i < 5; i++) { ctx.lineTo(0, -l.r); ctx.translate(0, -l.r); ctx.rotate((Math.PI * 2) / 10); ctx.lineTo(0, l.r / 2); ctx.translate(0, l.r / 2); ctx.rotate((Math.PI * 2) / 10); }
                        ctx.lineTo(0, -l.r); ctx.fill(); ctx.restore();
                    } else {
                        ctx.beginPath(); ctx.arc(l.x, l.y, 5, 0, Math.PI * 2); ctx.fillStyle = l.color || "#00FFFF"; ctx.fill(); 
                    }
                });

                foods.forEach(f => {
                    if (f.dropped) {
                        if (f.life < 120 && Math.floor(f.life / 8) % 2 === 0) return;
                        ctx.save();
                        ctx.shadowColor = f.color; ctx.shadowBlur = 10;
                        ctx.beginPath(); ctx.arc(f.x, f.y, f.r, 0, Math.PI * 2); ctx.fillStyle = f.color; ctx.fill();
                        ctx.shadowBlur = 0; ctx.lineWidth = 1.5; ctx.strokeStyle = "rgba(255,255,255,0.7)"; ctx.stroke();
                        ctx.beginPath(); ctx.arc(f.x - f.r * 0.3, f.y - f.r * 0.3, f.r * 0.25, 0, Math.PI * 2); ctx.fillStyle = "rgba(255,255,255,0.6)"; ctx.fill();
                        ctx.restore();
                    } else {
                        ctx.beginPath(); ctx.arc(f.x, f.y, f.r, 0, Math.PI * 2); ctx.fillStyle = f.color; ctx.fill();
                    }
                });

                let allStars = [player, ...bots].filter(s => !s.dead); allStars.sort((a, b) => a.r - b.r); 

                drawAbyssLaser();
                drawBossExtras();
                drawAbilitiesWorld();

                allStars.forEach(s => {
                    let isInvuln = (s === player && player.invulnTimer > 0), isFire = (s === player && player.fireTimer > 0);
                    ctx.save(); ctx.beginPath(); ctx.translate(s.x, s.y); if(isInvuln) ctx.globalAlpha = 0.5;
                    let starFill = s.color; if (s.r > 30) { let hue = (Date.now() / 20 + s.r * 6) % 360; starFill = `hsl(${hue}, 90%, 60%)`; }
                    for (let i = 0; i < 5; i++) { ctx.lineTo(0, -s.r); ctx.translate(0, -s.r); ctx.rotate((Math.PI * 2) / 10); ctx.lineTo(0, s.r / 2); ctx.translate(0, s.r / 2); ctx.rotate((Math.PI * 2) / 10); }
                    ctx.lineTo(0, -s.r); ctx.fillStyle = isFire ? "#FF4500" : starFill; ctx.fill(); ctx.lineWidth = Math.max(2, s.r * 0.08);
                    if (s.r > 45) { ctx.strokeStyle = `hsl(${(Date.now() / 10) % 360}, 100%, 75%)`; ctx.shadowColor = starFill; ctx.shadowBlur = 12; } else { ctx.strokeStyle = s.r >= LARGE_THRESHOLD ? "#FFD700" : "rgba(0,0,0,0.3)"; }
                    ctx.stroke(); ctx.closePath(); ctx.restore();

                    if(s !== player) {
                        let hpP = Math.max(0, s.hp / s.maxHp); ctx.fillStyle = "rgba(0,0,0,0.5)"; ctx.fillRect(s.x - 15, s.y - s.r - 12, 30, 4);
                        ctx.fillStyle = s.hp > (s.maxHp*0.5) ? "#33FF66" : (s.hp > (s.maxHp*0.2) ? "#FFFF33" : "#FF3333"); ctx.fillRect(s.x - 15, s.y - s.r - 12, 30 * hpP, 4);
                    }
                    ctx.fillStyle = "white"; ctx.font = "bold 12px sans-serif"; ctx.textAlign = "center"; ctx.fillText(s.name, s.x, s.y + s.r + 15);
                    if (s.r >= LARGE_THRESHOLD) { let nw = ctx.measureText(s.name).width; drawIcon(ctx, 'crown', s.x + nw / 2 + 12, s.y + s.r + 14, 16); }
                });

                drawPlayerShields();

                floatingTexts.forEach(ft => {
                    let fs = ft.size || 14;
                    ctx.save(); ctx.globalAlpha = Math.min(1, ft.life / 15);
                    ctx.fillStyle = ft.color; ctx.font = "bold " + fs + "px sans-serif"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
                    ctx.fillText(ft.text, ft.x, ft.y);
                    if (ft.icon) {
                        let w = ctx.measureText(ft.text).width; let is = fs * 1.15;
                        drawIcon(ctx, ft.icon, ft.x - w / 2 - is * 0.7, ft.y, is, ft.color);
                        if (ft.iconBoth) drawIcon(ctx, ft.icon, ft.x + w / 2 + is * 0.7, ft.y, is, ft.color);
                    }
                    ctx.restore();
                });
                ctx.restore();

                ctx.save(); let x = 12, y = canvas.height - 45; ctx.fillStyle = "#FFF"; ctx.font = "bold 14px sans-serif"; ctx.textAlign = "left";
                ctx.fillText("VIDAS:", x, y - 35); let vw = ctx.measureText("VIDAS: ").width;
                for(let i = 0; i < 5; i++) { drawIcon(ctx, i < playerLives ? 'heart' : 'heartEmpty', x + vw + 10 + i * 22, y - 40, 18); }
                ctx.fillStyle = "rgba(10, 10, 20, 0.85)"; ctx.strokeStyle = "#444"; ctx.lineWidth = 2; ctx.fillRect(x, y, 220, 18); ctx.strokeRect(x, y, 220, 18);
                let hpPct = Math.max(0, player.hp / player.maxHp); ctx.fillStyle = player.hp > (player.maxHp*0.5) ? "#33FF66" : (player.hp > (player.maxHp*0.2) ? "#FFFF33" : "#FF3333"); ctx.fillRect(x + 2, y + 2, 216 * hpPct, 14);
                ctx.fillStyle = "#FFF"; ctx.font = "bold 11px sans-serif"; ctx.textAlign = "center"; ctx.fillText(`SALUD: ${Math.ceil(player.hp)} / ${Math.ceil(player.maxHp)} HP`, x + 110, y + 13);

                for(let i = 0; i < 4; i++) { drawIcon(ctx, i < player.shields ? 'shield' : 'shieldEmpty', x + (i * 22) + 10, y - 14, 18); }

                // Estamina
                let stPct = Math.max(0, (player.stamina || 0) / STAMINA_MAX);
                ctx.fillStyle = "rgba(10, 10, 20, 0.85)"; ctx.fillRect(x, y + 22, 220, 9);
                ctx.fillStyle = player.exhausted ? "#886600" : "#FFD700"; ctx.fillRect(x + 1, y + 23, 218 * stPct, 7);
                ctx.strokeStyle = "#444"; ctx.lineWidth = 1; ctx.strokeRect(x, y + 22, 220, 9);
                ctx.fillStyle = "#FFF"; ctx.font = "bold 8px sans-serif"; ctx.textAlign = "left"; ctx.fillText("SHIFT ESTAMINA", x + 228, y + 30);
                // Personaje
                let ch = CHARACTERS[player.character || 'normal'];
                ctx.fillStyle = ch.color; ctx.font = "bold 12px sans-serif"; ctx.textAlign = "left"; ctx.fillText(ch.name, x + 228, y + 13);
                
                let bx = x; const by = y - 58;
                ctx.font = "bold 12px sans-serif"; ctx.textAlign = "left";
                const buffSeg = (icon, text) => { drawIcon(ctx, icon, bx + 8, by - 4, 16); ctx.fillStyle = "#FFD700"; ctx.fillText(text, bx + 20, by); bx += 20 + ctx.measureText(text).width + 18; };
                if(player.hasInvulnCharge || player.invulnTimer > 0) { buffSeg('ghost', player.invulnTimer > 0 ? `FANTASMA: ${(player.invulnTimer/60).toFixed(1)}s` : "[ESPACIO] FANTASMA LISTO"); }
                if(abyssUnlocked) { buffSeg('vortex', abyssTimer > 0 ? `LÁSER ABISMAL: ${(abyssTimer/60).toFixed(1)}s` : (abyssCooldown > 0 ? `LÁSER ABISMAL: ${Math.ceil(abyssCooldown/60)}s` : "[R] LÁSER ABISMAL LISTO")); }
                if(player.continuousLaserTimer > 0) { buffSeg('dot', `LÁSER CONTINUO: ${(player.continuousLaserTimer/60).toFixed(1)}s`); }
                ctx.restore();
                drawAbilityBar();
                ctx.save(); ctx.textAlign = "center"; ctx.font = "bold 14px sans-serif"; ctx.fillStyle = "#FFD700";
                ctx.fillText(`NIVEL ${levelIndex + 1}/${LEVELS.length}: ${String(LV.nombre).toUpperCase()}`, canvas.width / 2, 22);
                ctx.fillStyle = DIFFS[difficulty].color; ctx.font = "bold 12px sans-serif";
                ctx.fillText(`${DIFFS[difficulty].label}${freeMode ? '  ·  MODO LIBRE' : ''}`, canvas.width / 2, 40);
                ctx.restore();
            }

            // === MENÚ PRINCIPAL ===
            const mainMenu = document.getElementById("main-menu");
            const menuName = document.getElementById("menu-name");
            const namePanel = document.getElementById("name-panel");
            const nameInput = document.getElementById("name-input");
            const audioControls = document.getElementById("audio-controls");
            const lbPanel = document.getElementById("leaderboard-panel");
            // Muestra el nombre en el menú y avisa si los cheats de RISSOS están activos
            function updateMenuName() {
                if (isRissos()) {
                    menuName.innerHTML = playerName + ' <span style="color:#FFD700;font-size:0.8em;">(CHEATS ACTIVADOS)</span>';
                    menuName.style.color = '#FFD700';
                } else {
                    menuName.innerText = playerName;
                    menuName.style.color = '';
                }
            }
            updateMenuName();

            function startGame() {
                settingsModal.style.display = 'none'; namePanel.style.display = 'none';
                mainMenu.style.display = 'none';
                audioControls.style.display = 'flex'; lbPanel.style.display = 'block';
                init();
                gameState = 'playing';
            }
            function goToMenu() {
                if (currentFase && currentFase.stop) currentFase.stop();
                currentFase = null;
                gameState = 'menu'; isPaused = false; isFiring = false; keysDown.clear(); stopVictoryMusic(false);
                overScreen.style.display = 'none'; orbModal.style.display = 'none'; settingsModal.style.display = 'none'; victoryModal.style.display = 'none';
                audioControls.style.display = 'none'; lbPanel.style.display = 'none';
                mainMenu.style.display = 'flex';
            }
            function saveName() {
                let n = nameInput.value.trim().slice(0, 12);
                playerName = n || "TÚ";
                updateMenuName();
                namePanel.style.display = 'none';
            }

            document.getElementById("btn-play").addEventListener('click', () => openLevelSelect());
            document.getElementById("level-back").addEventListener('click', () => { levelSelect.style.display = 'none'; });
            document.getElementById("char-back").addEventListener('click', () => { charSelect.style.display = 'none'; levelSelect.style.display = 'flex'; });
            document.getElementById("btn-sound").addEventListener('click', () => { settingsModal.style.display = 'block'; });
            document.getElementById("btn-name").addEventListener('click', () => {
                let open = namePanel.style.display === 'flex';
                namePanel.style.display = open ? 'none' : 'flex';
                if (!open) { nameInput.value = playerName === "TÚ" ? "" : playerName; nameInput.focus(); }
            });
            document.getElementById("name-ok").addEventListener('click', saveName);
            nameInput.addEventListener('keydown', (e) => { e.stopPropagation(); if (e.key === 'Enter') saveName(); });
            document.getElementById("home-btn").addEventListener('mousedown', (e) => e.stopPropagation());
            document.getElementById("home-btn").addEventListener('click', goToMenu);

            // Fondo animado del menú: estrellas de colores flotando por el espacio
            let menuT = 0;
            let menuStars = [];
            for (let i = 0; i < 14; i++) {
                menuStars.push({ x: Math.random(), y: Math.random(), r: 10 + Math.random() * 34, color: randomColor(),
                    vx: (Math.random() - 0.5) * 0.0006, vy: (Math.random() - 0.5) * 0.0006, rot: Math.random() * 6, vr: (Math.random() - 0.5) * 0.01 });
            }
            function drawMenu() {
                menuT++;
                ctx.fillStyle = "#06060E"; ctx.fillRect(0, 0, canvas.width, canvas.height);
                let ox = menuT * 0.35, oy = menuT * 0.12;
                ctx.fillStyle = "rgba(255, 255, 255, 0.4)";
                bgStarsLayer1.forEach(s => { let px = (s.x - ox * 0.3) % canvas.width; if (px < 0) px += canvas.width; let py = (s.y - oy * 0.3) % canvas.height; if (py < 0) py += canvas.height; ctx.beginPath(); ctx.arc(px, py, s.r, 0, Math.PI * 2); ctx.fill(); });
                ctx.fillStyle = "rgba(180, 200, 255, 0.7)";
                bgStarsLayer2.forEach(s => { let px = (s.x - ox) % canvas.width; if (px < 0) px += canvas.width; let py = (s.y - oy) % canvas.height; if (py < 0) py += canvas.height; ctx.beginPath(); ctx.arc(px, py, s.r, 0, Math.PI * 2); ctx.fill(); });

                // Agujero negro decorativo en una esquina
                let bhx = canvas.width * 0.82, bhy = canvas.height * 0.78, bhr = Math.min(canvas.width, canvas.height) * 0.09;
                let g = ctx.createRadialGradient(bhx, bhy, bhr * 0.4, bhx, bhy, bhr * 1.8);
                g.addColorStop(0, "#000"); g.addColorStop(0.45, "rgba(138, 43, 226, 0.8)"); g.addColorStop(1, "rgba(255, 0, 128, 0)");
                ctx.beginPath(); ctx.arc(bhx, bhy, bhr * 1.8, 0, Math.PI * 2); ctx.fillStyle = g; ctx.fill();
                ctx.beginPath(); ctx.arc(bhx, bhy, bhr, 0, Math.PI * 2); ctx.fillStyle = "#05000A"; ctx.fill();

                menuStars.forEach(s => {
                    s.x += s.vx; s.y += s.vy; s.rot += s.vr;
                    if (s.x < -0.05) s.x = 1.05; if (s.x > 1.05) s.x = -0.05; if (s.y < -0.05) s.y = 1.05; if (s.y > 1.05) s.y = -0.05;
                    let fill = s.r > 30 ? `hsl(${(menuT * 2 + s.r * 6) % 360}, 90%, 60%)` : s.color;
                    starPath(ctx, s.x * canvas.width, s.y * canvas.height, 5, s.r, s.r * 0.5, s.rot);
                    ctx.globalAlpha = 0.85; ctx.fillStyle = fill; ctx.fill();
                    ctx.lineWidth = 2; ctx.strokeStyle = "rgba(0,0,0,0.3)"; ctx.stroke(); ctx.globalAlpha = 1;
                });
            }

            function mainLoop() {
                if (gameState === 'menu') { drawMenu(); }
                else if (gameState === 'fase') { if (currentFase) { currentFase.update(); currentFase.draw(); } }
                else { if(!isPaused) update(); draw(); }
                requestAnimationFrame(mainLoop);
            }
            goToMenu();
            mainLoop();
        </script>
        <script>
__FASES_JS__
        </script>
    </body>
    </html>
    """

codigo_juego_listo = codigo_juego_template.replace("__AUDIO_SRC__", audio_src)
codigo_juego_listo = codigo_juego_listo.replace("__SFX_DATA__", sfx_json)
codigo_juego_listo = codigo_juego_listo.replace("__LEVELS_DATA__", niveles_json)
codigo_juego_listo = codigo_juego_listo.replace("__FASES_DATA__", fases_json)
codigo_juego_listo = codigo_juego_listo.replace("__FASES_JS__", fases_js)   # al final, para no tocar el código de las fases

components.html(codigo_juego_listo, height=850, scrolling=False)
