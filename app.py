import streamlit as st
import streamlit.components.v1 as components
import base64
import os
import json

st.set_page_config(page_title="Star.io - Batalla Galáctica", layout="wide")

st.title("🌟 StarZ.io - Batalla Galáctica")
st.write("¡Sobrevive, llega al Top, destruye al Agujero Negro y mira lo que pasará!")

# ==========================================
# 🎵 CONFIGURACIÓN DE AUDIO RISO
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

if 'jugando' not in st.session_state:
    st.session_state.jugando = False
if 'nickname' not in st.session_state:
    st.session_state.nickname = "TÚ"

def iniciar_juego():
    nombre = st.session_state.nickname_input.strip()
    st.session_state.nickname = nombre if nombre else "TÚ"
    st.session_state.jugando = True

def volver_menu():
    st.session_state.jugando = False

if not st.session_state.jugando:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.text_input("Ingresa tu Nickname Estrella:", value=st.session_state.nickname, key="nickname_input", max_chars=12)
        st.write("---")
        st.button("▶️ JUGAR AHORA", on_click=iniciar_juego, type="primary", use_container_width=True)

else:
    st.button("⏹️ Volver al Menú Principal", on_click=volver_menu)
    
    codigo_juego_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { margin: 0; overflow: hidden; background-color: #050508; display: flex; justify-content: center; align-items: center; height: 100vh; user-select: none; font-family: sans-serif; }
            #main-wrapper { display: flex; flex-direction: row; gap: 20px; align-items: stretch; }
            canvas { background-color: #080812; cursor: crosshair; border-radius: 8px; border: 1px solid #222; }
            #leaderboard-panel { width: 240px; background: #0a0a10; border: 2px solid #00FFFF; border-radius: 8px; padding: 20px 15px; box-sizing: border-box; color: white; box-shadow: 0 0 15px rgba(0, 255, 255, 0.3); display: flex; flex-direction: column; }
            .lb-title { font-size: 16px; font-weight: bold; color: #00FFFF; text-align: center; border-bottom: 2px solid rgba(0, 255, 255, 0.3); padding-bottom: 12px; margin-top: 0; margin-bottom: 15px; }
            .lb-item { display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 12px; color: #eaeaea; }
            .lb-item.me { color: #00FFFF; font-weight: bold; text-shadow: 0 0 5px rgba(0, 255, 255, 0.5); }
            #gameover { display: none; position: absolute; color: white; top: 40%; left: 50%; transform: translateX(-50%); text-align: center; font-size: 24px; text-shadow: 2px 2px 10px #000; pointer-events: none; z-index: 5; width: 100%; }
            
            /* Modal de orbes */
            #orb-modal { display: none; position: absolute; top: 50%; left: 40%; transform: translate(-50%, -50%); background: rgba(10, 10, 25, 0.95); padding: 30px; border-radius: 12px; border: 3px solid white; text-align: center; z-index: 10; }
            .orb-btn { width: 160px; height: 160px; background: #151525; color: white; border: 2px solid #555; border-radius: 10px; font-size: 16px; font-weight: bold; cursor: pointer; transition: 0.2s; display: flex; flex-direction: column; align-items: center; justify-content: center; line-height: 1.4; }
            .orb-btn:hover { background: #2a2a40; transform: scale(1.05); }
            
            /* Controles de audio */
            #audio-controls { position: absolute; top: 15px; left: 15px; background: rgba(10, 10, 20, 0.85); border: 2px solid #00FFFF; border-radius: 8px; padding: 8px 15px; display: flex; align-items: center; gap: 12px; z-index: 15; box-shadow: 0 0 10px rgba(0, 255, 255, 0.2); }
            #mute-btn, #settings-btn { background: none; border: none; font-size: 22px; cursor: pointer; padding: 0; margin: 0; outline: none; transition: transform 0.2s; color: white; }
            #mute-btn:hover, #settings-btn:hover { transform: scale(1.15); }

            /* Ajustes de radio vintage tipo Caja Fuerte */
            #settings-modal { display: none; position: absolute; top: 50%; left: 40%; transform: translate(-50%, -50%); background: #2b1d14; border: 6px solid #1a110b; border-radius: 16px; padding: 25px; z-index: 20; color: #fff; text-align: center; box-shadow: inset 0 0 20px #000, 0 15px 40px rgba(0,0,0,0.95); width: 340px; }
            #close-settings { position: absolute; top: 10px; right: 15px; background: none; border: none; color: #d4af37; font-size: 20px; cursor: pointer; font-weight: bold; }
            #close-settings:hover { color: #fff; }
            .radio-title { margin: 0 0 20px 0; color: #d4af37; font-family: 'Courier New', Courier, monospace; letter-spacing: 2px; font-size: 22px; text-shadow: 1px 1px 2px #000; border-bottom: 2px solid #1a110b; padding-bottom: 10px; }
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
        <div id="main-wrapper">
            <div style="position: relative;">
                <div id="audio-controls">
                    <button id="mute-btn" title="Activar/Silenciar">🔇</button>
                    <button id="settings-btn" title="Ajustes de Sonido">⚙️</button>
                </div>
                <canvas id="gameCanvas" width="900" height="650"></canvas>
                
                <div id="gameover">
                    <h2 id="gameover-title">¡HAS MUERTO! 💥</h2>
                    <p id="gameover-msg" style="font-size: 22px; color: #00FFFF; font-weight: bold; margin-top: 10px;">👉 DALE CLICK AL JUEGO PARA REAPARECER 👈</p>
                </div>
                
                <div id="orb-modal">
                    <h2 id="orb-title" style="margin-top:0;">NUEVA MEJORA</h2>
                    <div style="display:flex; gap:20px; justify-content:center;">
                        <button id="orb-btn1" class="orb-btn"></button>
                        <button id="orb-btn2" class="orb-btn"></button>
                    </div>
                </div>

                <!-- Modal de Radio Vintage -->
                <div id="settings-modal">
                    <button id="close-settings">✖</button>
                    <h3 class="radio-title">📻 FRECUENCIA</h3>
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
            <div id="leaderboard-panel">
                <h3 class="lb-title">👑 TOP ESTRELLAS</h3>
                <div id="lb-list"></div>
            </div>
        </div>

        <script>
            // === SISTEMA DE AUDIO (MÚSICA Y SFX) ===
            const audioSrc = "__AUDIO_SRC__";
            const sfxData = __SFX_DATA__; 
            let bgMusic = null;
            let isUserInteracted = false;
            
            let musicVolume = 0.3;
            let sfxVolume = 0.5;
            
            const muteBtn = document.getElementById("mute-btn");
            const settingsBtn = document.getElementById("settings-btn");
            const settingsModal = document.getElementById("settings-modal");
            const closeSettings = document.getElementById("close-settings");

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
                    
                    // Calcular "clicks" audibles basándose en el volumen (ej: 40 ranuras)
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
                    
                    let angle = Math.atan2(e.clientY - centerY, e.clientX - centerX) * (180 / Math.PI);
                    angle += 90;
                    if(angle < -180) angle += 360;
                    
                    if(angle < -135 && angle > -180) angle = -135;
                    if(angle > 135 || (angle < -135 && angle <= -180)) {
                        if (angle < -135 && angle > -270) angle = 135;
                        else if (angle < -90) angle = -135;
                        else angle = 135;
                    }
                    
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
                    muteBtn.innerText = "🔊";
                } else if (musicVolume === 0 && bgMusic) {
                    bgMusic.pause();
                    muteBtn.innerText = "🔇";
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

            document.getElementById("gameCanvas").addEventListener('mousedown', () => {
                if (!isUserInteracted) {
                    isUserInteracted = true;
                    if (bgMusic && bgMusic.paused && musicVolume > 0) { 
                        bgMusic.play().then(() => { muteBtn.innerText = "🔊"; }).catch(err => {}); 
                    }
                }
            });

            muteBtn.addEventListener('click', () => {
                if(!bgMusic) return;
                if(bgMusic.paused) {
                    bgMusic.play(); muteBtn.innerText = "🔊";
                } else { 
                    bgMusic.pause(); muteBtn.innerText = "🔇"; 
                }
            });

            // === SISTEMA DEL JUEGO ===
            const canvas = document.getElementById("gameCanvas");
            const ctx = canvas.getContext("2d");
            const overScreen = document.getElementById("gameover");
            const overTitle = document.getElementById("gameover-title");
            const overMsg = document.getElementById("gameover-msg");
            const lbList = document.getElementById("lb-list");
            const orbModal = document.getElementById("orb-modal");
            const orbTitle = document.getElementById("orb-title");
            const btn1 = document.getElementById("orb-btn1");
            const btn2 = document.getElementById("orb-btn2");

            window.addEventListener('contextmenu', (e) => e.preventDefault());

            const worldW = 3200;
            const worldH = 3200;
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
            
            for(let i=0; i<120; i++) {
                bgStarsLayer1.push({x: Math.random() * canvas.width, y: Math.random() * canvas.height, r: Math.random() * 1.5 + 0.5});
                bgStarsLayer2.push({x: Math.random() * canvas.width, y: Math.random() * canvas.height, r: Math.random() * 2.5 + 1.0});
            }

            let meteor = { 
                orbitAngle: 0, orbitRadius: 450, x: worldW / 2, y: worldH / 2, r: 100, angle: 0, 
                hp: 15000, maxHp: 15000, isBoss: false, isPhase2: false, phase2MusicStarted: false, 
                dead: false, shootAngle: 0, laserTimer: 0, laserChargeTimer: 0, laserSweepTimer: 0, laserAngle: 0,
                craters: [ {x: -35, y: -25, r: 20}, {x: 35, y: -35, r: 16}, {x: 10, y: 30, r: 25}, {x: -40, y: 25, r: 14}, {x: 0, y: 0, r: 18} ] 
            };
            let blackHole = { x: worldW * 0.7, y: worldH * 0.3, r: 75, hp: 10000, maxHp: 10000, dead: false };

            canvas.addEventListener('mousemove', (e) => {
                const rect = canvas.getBoundingClientRect();
                screenMouseX = e.clientX - rect.left; screenMouseY = e.clientY - rect.top;
            });

            canvas.addEventListener('mousedown', (e) => {
                if(isPaused) return;
                if(player.dead) { if (playerLives > 0) respawnPlayer(); return; }
                if(e.button === 0) shootLaser();
                else if(e.button === 2) { e.preventDefault(); triggerDash(); }
            });

            window.addEventListener('keydown', (e) => {
                if(isPaused) return;
                if(e.code === 'Space') {
                    e.preventDefault();
                    if(player.dead) { if(playerLives > 0) respawnPlayer(); } 
                    else { triggerInvulnerability(); }
                }
            });

            function handlePlayerDeath() {
                playerLives--;
                isGameOver = true;
                playSfx("death", 0.3);
                overScreen.style.display = 'block';
                if(playerLives > 0) { overTitle.innerText = "¡HAS MUERTO! 💥"; overMsg.innerText = `👉 DALE CLICK PARA REAPARECER (${playerLives} VIDAS RESTANTES) 👈`; overMsg.style.color = "#00FFFF"; } 
                else { overTitle.innerText = "FIN DE LA PARTIDA"; overMsg.innerText = "💀 SIN VIDAS - JUEGO TERMINADO - VUELVE AL MENÚ 💀"; overMsg.style.color = "#FF3333"; }
            }

            function respawnPlayer() {
                player.x = Math.random() * (worldW - 200) + 100; player.y = Math.random() * (worldH - 200) + 100;
                player.r = 18; player.hp = 200; player.maxHp = 200; player.shields = 0; player.dead = false;
                player.invulnTimer = 0; player.fireTimer = 0; player.speedBoostTimer = 0; player.hasInvulnCharge = false;
                player.laserRange = 1.0; player.laserDamage = 1.0; 
                player.multiLevel = 1; player.crossLevel = 0; player.continuousLaserTimer = 0;
                isGameOver = false; overScreen.style.display = 'none';
                
                playSfx("respawn");
                floatingTexts.push({ x: player.x, y: player.y - 30, text: `✨ ¡REAPARECISTE! (${playerLives} vidas)`, color: "#33FF66", life: 50, size: 18 });
            }

            function triggerInvulnerability() {
                if(!player.dead && player.hasInvulnCharge && player.invulnTimer <= 0) {
                    player.hasInvulnCharge = false; player.invulnTimer = 300; 
                    floatingTexts.push({ x: player.x, y: player.y - player.r - 25, text: "👻 ¡MODO FANTASMA!", color: "#00FFFF", life: 50, size: 16 });
                }
            }

            function triggerDash() {
                const now = Date.now();
                if(!player.dead && now - lastDashTime >= dashCooldown) {
                    lastDashTime = now; dashTimer = 12; 
                    playSfx("dash");
                    floatingTexts.push({ x: player.x, y: player.y - player.r - 20, text: "⚡ DASH!", color: "#00FFFF", life: 30, size: 18 });
                }
            }

            function fireLaserProjectile(owner, ang, speed, life, color, damageMult) {
                lasers.push({ x: owner.x, y: owner.y, vx: Math.cos(ang) * speed, vy: Math.sin(ang) * speed, life: life, owner: owner, color: color, damageMult: damageMult, isStar: false });
            }

            function shootLaser() {
                if(player.dead || player.r <= 12) return;
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

                playSfx("laser");
                player.r = Math.max(10, player.r - Math.min(1.5, costPerShot));
            }

            const nombres = ["Alpha", "Nova", "Sirius", "Vega", "Orion", "Cosmos", "Apollo", "Zeta", "Pulsar"];
            const colors = ['#FF3366', '#33CCFF', '#FF9933', '#33FF66', '#CC33FF', '#FFFF33', '#FF3333'];
            function randomColor() { return colors[Math.floor(Math.random() * colors.length)]; }
            function randomName() { return nombres[Math.floor(Math.random() * nombres.length)]; }

            function spawnBox() { boxes.push({ x: Math.random() * (worldW - 100) + 50, y: Math.random() * (worldH - 100) + 50, r: 16 }); }
            function spawnRedBox() { redBoxes.push({ x: Math.random() * (worldW - 100) + 50, y: Math.random() * (worldH - 100) + 50, r: 18 }); }
            function spawnHeart() { hearts.push({ x: Math.random() * (worldW - 100) + 50, y: Math.random() * (worldH - 100) + 50, r: 10 }); }
            function spawnOrb() { orbs.push({ x: Math.random() * (worldW - 100) + 50, y: Math.random() * (worldH - 100) + 50, r: 14, type: Math.random() < 0.5 ? 'celeste' : 'morado' }); }

            let playerLives = 5; let player, bots, foods;
            const maxBots = 28; const maxFoods = 600;

            function init() {
                isGameOver = false; isPaused = false; playerLives = 5; cinematicTimer = 0; orbModal.style.display = 'none'; overScreen.style.display = 'none';
                floatingTexts = []; lasers = []; particles = []; boxes = []; redBoxes = []; hearts = []; orbs = [];
                
                meteor = { 
                    orbitAngle: 0, orbitRadius: 450, x: worldW / 2, y: worldH / 2, r: 100, angle: 0, 
                    hp: 15000, maxHp: 15000, isBoss: false, isPhase2: false, phase2MusicStarted: false, 
                    dead: false, shootAngle: 0, laserTimer: 0, laserChargeTimer: 0, laserSweepTimer: 0, laserAngle: 0,
                    craters: [ {x: -35, y: -25, r: 20}, {x: 35, y: -35, r: 16}, {x: 10, y: 30, r: 25}, {x: -40, y: 25, r: 14}, {x: 0, y: 0, r: 18} ] 
                };

                player = { 
                    x: Math.random() * worldW, y: Math.random() * worldH, r: 18, color: '#FFFFFF', name: "__PLAYER_NICKNAME__", speed: 3.5, dead: false,
                    hp: 200, maxHp: 200, shields: 0, hasInvulnCharge: false, invulnTimer: 0, fireTimer: 0, speedBoostTimer: 0,
                    laserRange: 1.0, laserDamage: 1.0, multiLevel: 1, crossLevel: 0, continuousLaserTimer: 0
                };
                
                bots = []; for(let i=0; i<maxBots; i++) spawnBot();
                foods = []; for(let i=0; i<maxFoods; i++) spawnFood();
                for(let i=0; i<35; i++) spawnHeart();
                
                spawnBox(); spawnBox(); spawnRedBox(); spawnOrb();
                loop();
            }

            function spawnBot() { bots.push({ x: Math.random() * worldW, y: Math.random() * worldH, r: Math.random() * 20 + 10, color: randomColor(), name: randomName(), vx: (Math.random() - 0.5) * 4, vy: (Math.random() - 0.5) * 4, hp: 200, maxHp: 200, lastShootTime: 0, dead: false, lastBurnTime: 0 }); }
            function spawnFood() { foods.push({ x: Math.random() * worldW, y: Math.random() * worldH, r: 3.5, color: randomColor() }); }

            function takeDamage(target, amount) {
                if(target === player && player.invulnTimer > 0) return;
                if(target === player && player.shields > 0) {
                    player.shields--; floatingTexts.push({ x: player.x, y: player.y - player.r - 20, text: "🛡️ ¡ESCUDO ABSORBIÓ DAÑO!", color: "#C0C0C0", life: 40, size: 16 });
                    return;
                }
                let dmgMult = Math.max(0.25, 18 / Math.max(18, target.r));
                let realDamage = amount * dmgMult; target.hp -= realDamage;
                floatingTexts.push({ x: target.x, y: target.y - target.r - 10, text: `-${Math.ceil(realDamage)}`, color: "#FF3333", life: 30, size: 24 });

                if(target === player && player.hp <= 0 && !player.dead) { player.hp = 0; player.dead = true; handlePlayerDeath(); } 
                else if(target !== player && target.hp <= 0) { 
                    target.dead = true; 
                    floatingTexts.push({ x: target.x, y: target.y, text: "💥 ¡DESTRUIDO!", color: "#FF3333", life: 40, size: 22 }); 
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
                orbModal.style.display = 'none'; isPaused = false;
            }

            function showOrbMenu(type) {
                isPaused = true; orbModal.style.display = 'block'; orbModal.style.borderColor = type === 'celeste' ? '#00FFFF' : '#CC33FF';
                btn1.onclick = null; btn2.onclick = null;

                if(type === 'celeste') {
                    orbTitle.style.color = '#00FFFF'; orbTitle.innerText = "🔵 ORBE CELESTE";
                    btn1.style.borderColor = '#00FFFF'; btn1.innerHTML = "🚀<br>MAYOR DISTANCIA"; btn1.onclick = () => applyUpgrade('range');
                    btn2.style.borderColor = '#00FFFF'; btn2.innerHTML = "💥<br>MAYOR DAÑO"; btn2.onclick = () => applyUpgrade('damage');
                } else {
                    orbTitle.style.color = '#CC33FF'; orbTitle.innerText = "🟣 ORBE MORADO";
                    let nextMulti = Math.min(10, player.multiLevel + 1);
                    let nextCross = Math.min(10, player.crossLevel + 1);
                    
                    btn1.style.borderColor = '#CC33FF'; 
                    btn1.innerHTML = `🔱<br>DISPARO MÚLTIPLE<br><span style="color:#FFD700;font-size:14px;margin-top:6px;display:block;">Nv. ${nextMulti}</span>`; 
                    btn1.onclick = () => applyUpgrade('multi');
                    
                    btn2.style.borderColor = '#CC33FF'; 
                    btn2.innerHTML = `➕<br>DISPARO EN CRUZ<br><span style="color:#FFD700;font-size:14px;margin-top:6px;display:block;">Nv. ${nextCross}</span>`; 
                    btn2.onclick = () => applyUpgrade('cross');
                }
            }

            function updateLeaderboard() {
                let allStars = [player, ...bots].filter(s => !s.dead); allStars.sort((a, b) => b.r - a.r); let topStars = allStars.slice(0, 10);
                let html = ""; topStars.forEach((s, idx) => { let isMe = (s === player); html += `<div class="lb-item ${isMe ? 'me' : ''}"><span>${idx + 1}. ${s.name}</span><span>${Math.round(s.r)} pt</span></div>`; });
                lbList.innerHTML = html;
            }

            function update() {
                if(Math.random() < 0.003 && boxes.length < 5) spawnBox();
                if(Math.random() < 0.0015 && redBoxes.length < 2) spawnRedBox();
                if(Math.random() < 0.002 && orbs.length < 3) spawnOrb();

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
                        floatingTexts.push({ x: meteor.x, y: meteor.y - 140, text: "🔴 FASE 2: LUNA CÍCLOPE ACTIVADA 🔴", color: "#FF0000", life: 180, size: 36 });
                    }
                    if (meteor.isPhase2 && !meteor.phase2MusicStarted) { meteor.phase2MusicStarted = true; }

                    let bossSpeed = meteor.isPhase2 ? 0.45 : 1.2;
                    if (!player.dead) {
                        let dx = player.x - meteor.x; let dy = player.y - meteor.y; let dist = Math.hypot(dx, dy);
                        if (dist > 0) { meteor.x += (dx/dist) * bossSpeed; meteor.y += (dy/dist) * bossSpeed; }
                    }

                    meteor.shootAngle += 0.22;
                    if (Date.now() % 4 === 0) {
                        lasers.push({ x: meteor.x, y: meteor.y, vx: Math.cos(meteor.shootAngle) * 5, vy: Math.sin(meteor.shootAngle) * 5, life: 160, owner: meteor, color: "#FFA500", damageMult: 1.5, r: 9, isStar: true });
                    }

                    if (meteor.isPhase2) {
                        meteor.laserTimer++;
                        if (meteor.laserTimer >= 1800 && meteor.laserChargeTimer <= 0 && meteor.laserSweepTimer <= 0) {
                            meteor.laserChargeTimer = 60; 
                            let angleToPlayer = Math.atan2(player.y - meteor.y, player.x - meteor.x);
                            meteor.laserAngle = angleToPlayer - 0.7; 
                            floatingTexts.push({ x: meteor.x, y: meteor.y - 100, text: "👁️ ¡LÁSER CÍCLOPE INMINENTE!", color: "#FF0055", life: 60, size: 28 });
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
                                    if (distSq < (beamRadius + player.r) * (beamRadius + player.r)) { takeDamage(player, 5); }
                                }
                            }
                        }
                    }
                }
                meteor.angle += 0.003;

                if(!blackHole.dead) { 
                    blackHole.r += 0.012; blackHole.hp = Math.min(blackHole.maxHp, blackHole.hp + 0.02);
                    let pullRadius = blackHole.r * 5.5; let dPlayer = Math.hypot(blackHole.x - player.x, blackHole.y - player.y);
                    if(!player.dead && dPlayer < pullRadius && dPlayer > 0) {
                        let pullForce = (1 - dPlayer / pullRadius) * 2.8;
                        player.x += ((blackHole.x - player.x) / dPlayer) * pullForce; player.y += ((blackHole.y - player.y) / dPlayer) * pullForce;
                        if(Math.random() < 0.25) particles.push({ x: player.x, y: player.y, vx: ((blackHole.x - player.x) / dPlayer) * 3, vy: ((blackHole.y - player.y) / dPlayer) * 3, color: "#8A2BE2", life: 12 });
                    }
                }

                if(player.invulnTimer > 0) player.invulnTimer--; if(player.fireTimer > 0) player.fireTimer--; if(player.speedBoostTimer > 0) player.speedBoostTimer--;
                if(player.fireTimer > 0 && !player.dead) { for(let i=0; i<2; i++) particles.push({ x: player.x + (Math.random() - 0.5) * player.r * 1.5, y: player.y + (Math.random() - 0.5) * player.r * 1.5, vx: (Math.random() - 0.5) * 2, vy: -Math.random() * 3, color: Math.random() > 0.5 ? "#FF4500" : "#FFD700", life: 20 }); }

                let allStars = [player, ...bots].filter(s => !s.dead); const now = Date.now();

                if(!player.dead && cinematicTimer <= 0) {
                    let targetX = (screenMouseX - canvas.width / 2) / zoom + camX + canvas.width / 2;
                    let targetY = (screenMouseY - canvas.height / 2) / zoom + camY + canvas.height / 2;
                    let dx = targetX - player.x, dy = targetY - player.y; let dist = Math.sqrt(dx*dx + dy*dy);
                    let baseSpeed = player.speed * Math.max(0.35, 20 / (player.r + 5));

                    if (player.speedBoostTimer > 0) baseSpeed *= 1.7;
                    if (dashTimer > 0) { baseSpeed *= 3.8; dashTimer--; }

                    if (dist > 5) { player.x += (dx / dist) * baseSpeed; player.y += (dy / dist) * baseSpeed; }
                    player.x = Math.max(player.r, Math.min(worldW - player.r, player.x)); player.y = Math.max(player.r, Math.min(worldH - player.r, player.y));
                }

                bots.forEach(bot => {
                    let botSpeed = 3 * Math.max(0.35, 20 / (bot.r + 5));
                    if(Math.random() < 0.02) { bot.vx = (Math.random() - 0.5) * 4; bot.vy = (Math.random() - 0.5) * 4; }
                    bot.x += bot.vx * (botSpeed / 2); bot.y += bot.vy * (botSpeed / 2);
                    bot.x = Math.max(bot.r, Math.min(worldW - bot.r, bot.x)); bot.y = Math.max(bot.r, Math.min(worldH - bot.r, bot.y));

                    if (now - (bot.lastShootTime || 0) > 2500 && Math.random() < 0.03 && bot.r > 12) {
                        let target = (!blackHole.dead && Math.hypot(blackHole.x - bot.x, blackHole.y - bot.y) < 600) ? blackHole : 
                                     (meteor.isBoss && !meteor.dead && Math.hypot(meteor.x - bot.x, meteor.y - bot.y) < 600) ? meteor :
                                     (!player.dead && Math.hypot(player.x - bot.x, player.y - bot.y) < 550) ? player : 
                                     bots.find(b => b !== bot && !b.dead && Math.hypot(b.x - bot.x, b.y - bot.y) < 400);

                        if(target) {
                            let dx = target.x - bot.x, dy = target.y - bot.y, dist = Math.hypot(dx, dy);
                            if(dist > 0) { lasers.push({ x: bot.x, y: bot.y, vx: (dx / dist) * 13, vy: (dy / dist) * 13, life: 65, owner: bot, color: "#FF6633", damageMult: 1, isStar: false }); bot.lastShootTime = now; bot.r = Math.max(8, bot.r - 0.3); }
                        }
                    }
                });

                if (cinematicTimer > 0) {
                    cinematicTimer--;
                    meteor.r += (150 - meteor.r) * 0.03; 
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
                            blackHole.dead = true; 
                            playSfx("bh_death", 2.5); 
                            meteor.isBoss = true; cinematicTimer = 180;
                            if (bgMusic && sfxData["luna_musica"] && sfxData["luna_musica"].length > 0) {
                                bgMusic.pause(); bgMusic.src = sfxData["luna_musica"][0]; bgMusic.currentTime = 0; bgMusic.play().catch(e => console.log(e));
                            }
                            floatingTexts.push({ x: meteor.x, y: meteor.y - 120, text: "⚠️ LA LUNA DESPIERTA ⚠️", color: "#FF4500", life: 180, size: 40 });
                        } 
                        hit = true;
                    }

                    if(meteor.isBoss && !meteor.dead && l.owner !== meteor && Math.hypot(l.x - meteor.x, l.y - meteor.y) < meteor.r) {
                        meteor.hp -= dmg; hit = true;
                        if(meteor.hp <= 0 && !meteor.dead) {
                            meteor.dead = true; playSfx("bh_death", 2.5); 
                            floatingTexts.push({ x: meteor.x, y: meteor.y, text: "🌟 VICTORIA GALÁCTICA 🌟", color: "#FFD700", life: 300, size: 50 });
                            if (bgMusic && audioSrc) { bgMusic.pause(); bgMusic.src = audioSrc; bgMusic.currentTime = 0; bgMusic.play().catch(e => console.log(e)); }
                        }
                    }

                    if(!hit) {
                        for(let s of allStars) {
                            if(s.dead || s === l.owner) continue;
                            if(Math.hypot(l.x - s.x, l.y - s.y) < (s.r + (l.r||5))) {
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
                        floatingTexts.push({x: player.x, y: player.y - 40, text: "🔴 ¡MODO LÁSER CONTINUO!", color: "#FF0000", life: 60, size: 22});
                    }
                }
                
                for(let i = boxes.length - 1; i >= 0; i--) {
                    let b = boxes[i];
                    if(!player.dead && Math.hypot(player.x - b.x, player.y - b.y) < player.r + b.r) {
                        boxes.splice(i, 1); playSfx("box"); let rand = Math.random();
                        if(rand < 0.50) { player.hp += 50; if(player.hp > player.maxHp) player.maxHp = player.hp; player.r += 2; floatingTexts.push({x: player.x, y: player.y - player.r - 15, text: "❤️ +50 HP MAX", color: "#33FF66", life: 50, size: 22}); } 
                        else if(rand < 0.625) { if(player.shields < 4) { player.shields++; floatingTexts.push({x: player.x, y: player.y - 30, text: "🛡️ ESCUDO +1", color: "#C0C0C0", life: 45, size: 18}); } } 
                        else if(rand < 0.750) { player.fireTimer = 360; floatingTexts.push({x: player.x, y: player.y - 30, text: "🔥 ¡AURA DE FUEGO!", color: "#FF4500", life: 50, size: 22}); } 
                        else if(rand < 0.875) { player.hasInvulnCharge = true; floatingTexts.push({x: player.x, y: player.y - 30, text: "👻 ¡FANTASMA LISTO!", color: "#00FFFF", life: 55, size: 18}); } 
                        else { player.speedBoostTimer = 300; floatingTexts.push({x: player.x, y: player.y - 30, text: "⚡ ¡VELOCIDAD!", color: "#FFFF33", life: 45, size: 18}); }
                    }
                }

                for(let i = hearts.length - 1; i >= 0; i--) { let h = hearts[i]; if(!player.dead && Math.hypot(player.x - h.x, player.y - h.y) < player.r + h.r) { hearts.splice(i, 1); spawnHeart(); playSfx("food"); player.hp += 20; if(player.hp > player.maxHp) player.maxHp = player.hp; floatingTexts.push({ x: player.x, y: player.y - player.r - 15, text: "+20 HP ❤️", color: "#FF3366", life: 40, size: 18 }); } }

                if(!meteor.dead) { allStars.forEach(s => { if(Math.hypot(s.x - meteor.x, s.y - meteor.y) < s.r + meteor.r * 0.85) takeDamage(s, 100); }); }
                
                if(!blackHole.dead) {
                    allStars.forEach(s => {
                        if(Math.hypot(s.x - blackHole.x, s.y - blackHole.y) < s.r + blackHole.r * 0.8) {
                            if(s.r > blackHole.r * 1.25) { 
                                blackHole.dead = true; s.r += 35; 
                                playSfx("bh_death", 2.5);
                                meteor.isBoss = true; cinematicTimer = 180;
                                if (bgMusic && sfxData["luna_musica"] && sfxData["luna_musica"].length > 0) {
                                    bgMusic.pause(); bgMusic.src = sfxData["luna_musica"][0]; bgMusic.currentTime = 0; bgMusic.play().catch(e => console.log(e));
                                }
                            } 
                            else { 
                                if(s === player && !player.dead) { player.hp = 0; player.dead = true; handlePlayerDeath(); } else if(s !== player) { s.dead = true; } 
                            }
                        }
                    });
                }

                for(let i = foods.length - 1; i >= 0; i--) {
                    let f = foods[i];
                    for(let e of allStars) {
                        if(Math.hypot(e.x - f.x, e.y - f.y) < e.r) { e.r += 0.08; if(e === player) { playSfx("food"); player.hp += 0.2; if(player.hp > player.maxHp) player.maxHp = player.hp; } foods.splice(i, 1); spawnFood(); break; }
                    }
                }

                for(let i = 0; i < allStars.length; i++) {
                    for(let j = i + 1; j < allStars.length; j++) {
                        let e1 = allStars[i], e2 = allStars[j]; let d = Math.hypot(e1.x - e2.x, e1.y - e2.y);
                        if(d < e1.r + e2.r) { if(e1 === player && player.fireTimer > 0 && (now - (e2.lastBurnTime || 0) > 500)) { takeDamage(e2, 40); e2.lastBurnTime = now; } else if (e2 === player && player.fireTimer > 0 && (now - (e1.lastBurnTime || 0) > 500)) { takeDamage(e1, 40); e1.lastBurnTime = now; } }
                        let bigger = e1.r > e2.r ? e1 : e2; let smaller = e1.r > e2.r ? e2 : e1;
                        if(d < bigger.r * 0.75 && bigger.r > smaller.r * 1.15) {
                            if(smaller === player && player.invulnTimer > 0) continue;
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

            function draw() {
                ctx.fillStyle = "#06060E"; ctx.fillRect(0, 0, canvas.width, canvas.height);
                ctx.fillStyle = "rgba(255, 255, 255, 0.4)"; bgStarsLayer1.forEach(s => { let px = (s.x - camX * 0.08) % canvas.width; if (px < 0) px += canvas.width; let py = (s.y - camY * 0.08) % canvas.height; if (py < 0) py += canvas.height; ctx.beginPath(); ctx.arc(px, py, s.r, 0, Math.PI * 2); ctx.fill(); });
                ctx.fillStyle = "rgba(180, 200, 255, 0.7)"; bgStarsLayer2.forEach(s => { let px = (s.x - camX * 0.2) % canvas.width; if (px < 0) px += canvas.width; let py = (s.y - camY * 0.2) % canvas.height; if (py < 0) py += canvas.height; ctx.beginPath(); ctx.arc(px, py, s.r, 0, Math.PI * 2); ctx.fill(); });

                let shakeX = 0, shakeY = 0; 
                if(!player.dead && player.hp <= 40 && player.hp > 0) { shakeX = (Math.random() - 0.5) * 9; shakeY = (Math.random() - 0.5) * 9; }
                if(cinematicTimer > 0) { shakeX = (Math.random() - 0.5) * 6; shakeY = (Math.random() - 0.5) * 6; }

                ctx.save(); ctx.translate(canvas.width / 2 + shakeX, canvas.height / 2 + shakeY); ctx.scale(zoom, zoom); ctx.translate(-camX - canvas.width / 2, -camY - canvas.height / 2);
                ctx.strokeStyle = "#FF3366"; ctx.lineWidth = 6; ctx.strokeRect(0, 0, worldW, worldH);

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
                    ctx.fillStyle = meteor.isBoss ? (meteor.isPhase2 ? "#FF0033" : "#FF6600") : "#A9A9A9"; 
                    if(meteor.isBoss) { ctx.shadowColor = meteor.isPhase2 ? "#FF0000" : "#FF4500"; ctx.shadowBlur = 40; }
                    ctx.fill(); ctx.shadowBlur = 0;
                    meteor.craters.forEach(c => { ctx.beginPath(); ctx.arc(c.x, c.y, c.r, 0, Math.PI * 2); ctx.fillStyle = meteor.isBoss ? "#990000" : "#696969"; ctx.fill(); }); 
                    ctx.restore();

                    if(meteor.isBoss) {
                        ctx.save(); ctx.translate(meteor.x, meteor.y);
                        let bossHpPct = Math.max(0, meteor.hp / meteor.maxHp); let barW = 220, barH = 14; 
                        ctx.fillStyle = "rgba(0,0,0,0.7)"; ctx.fillRect(-barW/2, -meteor.r - 40, barW, barH); 
                        ctx.fillStyle = meteor.isPhase2 ? "#FF0000" : "#FF4500"; ctx.fillRect(-barW/2 + 1, -meteor.r - 39, (barW - 2) * bossHpPct, barH - 2); 
                        ctx.strokeStyle = "#FFFFFF"; ctx.lineWidth = 2; ctx.strokeRect(-barW/2, -meteor.r - 40, barW, barH);
                        ctx.fillStyle = "#FFD700"; ctx.font = "bold 16px sans-serif"; ctx.textAlign = "center"; 
                        ctx.fillText(`${meteor.isPhase2 ? '🔴 LUNA CÍCLOPE (FASE 2)' : '🌕 LUNA SANGRIENTA'}: ${Math.ceil(meteor.hp)} / ${meteor.maxHp} HP`, 0, -meteor.r - 48); 
                        ctx.restore();
                    }
                }

                if(!blackHole.dead) {
                    ctx.save(); ctx.translate(blackHole.x, blackHole.y); ctx.strokeStyle = "rgba(138, 43, 226, 0.15)"; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(0, 0, blackHole.r * 5.5, 0, Math.PI * 2); ctx.stroke();
                    let grad = ctx.createRadialGradient(0, 0, blackHole.r * 0.4, 0, 0, blackHole.r * 1.5); grad.addColorStop(0, "#000"); grad.addColorStop(0.5, "#8A2BE2"); grad.addColorStop(1, "rgba(255, 0, 128, 0)");
                    ctx.beginPath(); ctx.arc(0, 0, blackHole.r * 1.5, 0, Math.PI * 2); ctx.fillStyle = grad; ctx.fill(); ctx.beginPath(); ctx.arc(0, 0, blackHole.r, 0, Math.PI * 2); ctx.fillStyle = "#05000A"; ctx.fill();
                    let bhHpPct = Math.max(0, blackHole.hp / blackHole.maxHp); let barW = 160, barH = 12; ctx.fillStyle = "rgba(0,0,0,0.7)"; ctx.fillRect(-barW/2, -blackHole.r * 1.5 - 28, barW, barH); ctx.fillStyle = "#CC33FF"; ctx.fillRect(-barW/2 + 1, -blackHole.r * 1.5 - 27, (barW - 2) * bhHpPct, barH - 2); ctx.strokeStyle = "#FFFFFF"; ctx.lineWidth = 1; ctx.strokeRect(-barW/2, -blackHole.r * 1.5 - 28, barW, barH);
                    ctx.fillStyle = "#FFD700"; ctx.font = "bold 14px sans-serif"; ctx.textAlign = "center"; ctx.fillText(`🕳️ AGUJERO NEGRO: ${Math.ceil(blackHole.hp)} / ${blackHole.maxHp} HP`, 0, -blackHole.r * 1.5 - 35); ctx.restore();
                }

                boxes.forEach(b => { ctx.save(); ctx.translate(b.x, b.y); ctx.fillStyle = "#FFD700"; ctx.strokeStyle = "#FF8C00"; ctx.lineWidth = 3; ctx.fillRect(-b.r, -b.r, b.r*2, b.r*2); ctx.strokeRect(-b.r, -b.r, b.r*2, b.r*2); ctx.fillStyle = "#000"; ctx.font = "bold 16px sans-serif"; ctx.textAlign = "center"; ctx.fillText("?", 0, 5); ctx.restore(); });
                redBoxes.forEach(rb => { ctx.save(); ctx.translate(rb.x, rb.y); ctx.fillStyle = "#FF0000"; ctx.strokeStyle = "#8B0000"; ctx.lineWidth = 3; ctx.fillRect(-rb.r, -rb.r, rb.r*2, rb.r*2); ctx.strokeRect(-rb.r, -rb.r, rb.r*2, rb.r*2); ctx.fillStyle = "#FFF"; ctx.font = "bold 16px sans-serif"; ctx.textAlign = "center"; ctx.fillText("🔥", 0, 6); ctx.restore(); });

                orbs.forEach(o => { ctx.save(); ctx.translate(o.x, o.y); ctx.beginPath(); ctx.arc(0, 0, o.r, 0, Math.PI * 2); ctx.fillStyle = o.type === 'celeste' ? '#00FFFF' : '#CC33FF'; ctx.fill(); ctx.strokeStyle = "white"; ctx.lineWidth = 2; ctx.stroke(); ctx.globalAlpha = 0.5; ctx.beginPath(); ctx.arc(0, 0, o.r + Math.sin(Date.now() / 150)*4, 0, Math.PI * 2); ctx.strokeStyle = o.type === 'celeste' ? '#00FFFF' : '#CC33FF'; ctx.lineWidth = 2; ctx.stroke(); ctx.restore(); });
                hearts.forEach(h => { ctx.font = "16px sans-serif"; ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText("❤️", h.x, h.y); });
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

                foods.forEach(f => { ctx.beginPath(); ctx.arc(f.x, f.y, f.r, 0, Math.PI * 2); ctx.fillStyle = f.color; ctx.fill(); });

                let allStars = [player, ...bots].filter(s => !s.dead); allStars.sort((a, b) => a.r - b.r); 

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
                    ctx.fillStyle = "white"; ctx.font = "bold 12px sans-serif"; ctx.textAlign = "center"; ctx.fillText(s.name + (s.r >= LARGE_THRESHOLD ? " 👑" : ""), s.x, s.y + s.r + 15);
                });

                floatingTexts.forEach(ft => { ctx.fillStyle = ft.color; ctx.font = "bold " + (ft.size || 14) + "px sans-serif"; ctx.textAlign = "center"; ctx.fillText(ft.text, ft.x, ft.y); });
                ctx.restore();

                ctx.save(); let x = 12, y = canvas.height - 45; ctx.fillStyle = "#FFF"; ctx.font = "bold 14px sans-serif"; ctx.textAlign = "left";
                let corazones = "❤️".repeat(Math.max(0, playerLives)) + "🖤".repeat(Math.max(0, 5 - playerLives)); ctx.fillText(`VIDAS: ${corazones}`, x, y - 35);
                ctx.fillStyle = "rgba(10, 10, 20, 0.85)"; ctx.strokeStyle = "#444"; ctx.lineWidth = 2; ctx.fillRect(x, y, 220, 18); ctx.strokeRect(x, y, 220, 18);
                let hpPct = Math.max(0, player.hp / player.maxHp); ctx.fillStyle = player.hp > (player.maxHp*0.5) ? "#33FF66" : (player.hp > (player.maxHp*0.2) ? "#FFFF33" : "#FF3333"); ctx.fillRect(x + 2, y + 2, 216 * hpPct, 14);
                ctx.fillStyle = "#FFF"; ctx.font = "bold 11px sans-serif"; ctx.textAlign = "center"; ctx.fillText(`SALUD: ${Math.ceil(player.hp)} / ${Math.ceil(player.maxHp)} HP`, x + 110, y + 13);

                for(let i = 0; i < 4; i++) { ctx.beginPath(); ctx.arc(x + (i * 22) + 10, y - 14, 7, 0, Math.PI * 2); ctx.fillStyle = i < player.shields ? "#A0A0A0" : "rgba(80, 80, 80, 0.3)"; ctx.fill(); ctx.strokeStyle = "#FFF"; ctx.lineWidth = 1; ctx.stroke(); }
                
                let buffStatus = "";
                if(player.hasInvulnCharge || player.invulnTimer > 0) { buffStatus += (player.invulnTimer > 0 ? `👻 FANTASMA: ${(player.invulnTimer/60).toFixed(1)}s   ` : "👻 [ESPACIO] FANTASMA LISTO   "); }
                if(player.continuousLaserTimer > 0) { buffStatus += `🔴 LÁSER CONTINUO: ${(player.continuousLaserTimer/60).toFixed(1)}s`; }
                if(buffStatus !== "") { ctx.fillStyle = "#FFD700"; ctx.font = "bold 12px sans-serif"; ctx.textAlign = "left"; ctx.fillText(buffStatus, x, y - 55); }
                ctx.restore();
            }

            function loop() { if(!isPaused) update(); draw(); requestAnimationFrame(loop); }
            init();
        </script>
    </body>
    </html>
    """
    
    codigo_juego_listo = codigo_juego_template.replace("__PLAYER_NICKNAME__", st.session_state.nickname)
    codigo_juego_listo = codigo_juego_listo.replace("__AUDIO_SRC__", audio_src)
    codigo_juego_listo = codigo_juego_listo.replace("__SFX_DATA__", sfx_json)
    
    components.html(codigo_juego_listo, height=680, width=1200, scrolling=False)
