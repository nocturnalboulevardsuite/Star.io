import streamlit as st
import streamlit.components.v1 as components
import base64
import os
import json

st.set_page_config(page_title="Star.io - Batalla Galáctica", layout="wide")

st.title("🌟 Star.io - Batalla Galáctica")
st.write("¡Sobrevive, domina el Top, destruye al Agujero Negro y enfréntate a la Luna!")

# ==========================================
# 🎵 CONFIGURACIÓN DE AUDIO (MÚSICA Y EFECTOS)
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

# Cargar música de fondo
audio_src = obtener_audio_b64(RUTA_MUSICA) or ""

# Rutas de efectos de sonido
rutas_sfx = {
    "laser": ["sonidos/laser1.wav", "laser1.wav", "laser1.mp3"],
    "death": ["sonidos/muerte.wav", "muerte.wav", "death1.wav"],
    "bh_death": ["sonidos/explosionagujeronegro.wav", "explosionagujeronegro.wav"],
    "dash": ["sonidos/dash1.wav", "dash1.wav"],
    "food": ["sonidos/food1.wav", "food1.wav"],
    "box": ["sonidos/box1.wav", "box1.wav"],
    "orb": ["sonidos/orb1.wav", "orb1.wav"],
    "respawn": ["sonidos/respawn1.wav", "respawn1.wav"],
    "bossluna": ["sonidos/bossluna.wav", "bossluna.wav"] # Agregado por si decides poner un archivo específico
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
        st.text_input("✨ Ingresa el Nickname de tu Estrella:", value=st.session_state.nickname, key="nickname_input", max_chars=12)
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
            #orb-modal { display: none; position: absolute; top: 50%; left: 40%; transform: translate(-50%, -50%); background: rgba(10, 10, 25, 0.95); padding: 30px; border-radius: 12px; border: 3px solid white; text-align: center; z-index: 10; }
            .orb-btn { width: 140px; height: 140px; background: #151525; color: white; border: 2px solid #555; border-radius: 10px; font-size: 16px; font-weight: bold; cursor: pointer; transition: 0.2s; }
            .orb-btn:hover { background: #2a2a40; transform: scale(1.05); }
            #audio-controls { position: absolute; top: 15px; left: 15px; background: rgba(10, 10, 20, 0.85); border: 2px solid #00FFFF; border-radius: 8px; padding: 8px 15px; display: flex; align-items: center; gap: 12px; z-index: 15; box-shadow: 0 0 10px rgba(0, 255, 255, 0.2); }
            #mute-btn { background: none; border: none; font-size: 22px; cursor: pointer; padding: 0; margin: 0; outline: none; transition: transform 0.2s; color: white; }
            #mute-btn:hover { transform: scale(1.15); }
            input[type=range] { -webkit-appearance: none; width: 90px; background: transparent; }
            input[type=range]::-webkit-slider-thumb { -webkit-appearance: none; height: 16px; width: 16px; border-radius: 50%; background: #00FFFF; cursor: pointer; margin-top: -6px; box-shadow: 0 0 5px #00FFFF; }
            input[type=range]::-webkit-slider-runnable-track { width: 100%; height: 4px; cursor: pointer; background: #444; border-radius: 2px; }
        </style>
    </head>
    <body>
        <div id="main-wrapper">
            <div style="position: relative;">
                <div id="audio-controls">
                    <button id="mute-btn" title="Activar/Silenciar">🔇</button>
                    <input type="range" id="volume-slider" min="0" max="1" step="0.05" value="0.3" title="Volumen">
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
            
            const muteBtn = document.getElementById("mute-btn");
            const volSlider = document.getElementById("volume-slider");

            if (audioSrc && audioSrc !== "") {
                bgMusic = new Audio(audioSrc);
                bgMusic.loop = true;
                bgMusic.volume = volSlider.value;
            }

            muteBtn.addEventListener('mousedown', (e) => e.stopPropagation());
            volSlider.addEventListener('mousedown', (e) => e.stopPropagation());

            // Multiplicador de volumen añadido para personalizar intensidad
            function playSfx(type, volMultiplier = 1.0) {
                if (!isUserInteracted) return;
                let soundArray = sfxData[type];
                if (soundArray && soundArray.length > 0) {
                    let randomSrc = soundArray[Math.floor(Math.random() * soundArray.length)];
                    let snd = new Audio(randomSrc);
                    snd.volume = Math.min(1.0, volSlider.value * volMultiplier);
                    snd.play().catch(e => console.log("SFX play bloqueado", e));
                }
            }

            document.getElementById("gameCanvas").addEventListener('mousedown', () => {
                if (!isUserInteracted) {
                    isUserInteracted = true;
                    if (bgMusic && bgMusic.paused) { bgMusic.play().then(() => { muteBtn.innerText = "🔊"; }).catch(err => {}); }
                }
            });

            muteBtn.addEventListener('click', () => {
                if(!bgMusic) return;
                if(bgMusic.paused) {
                    bgMusic.play(); muteBtn.innerText = "🔊";
                    if(volSlider.value == 0) { volSlider.value = 0.3; bgMusic.volume = 0.3; }
                } else { bgMusic.pause(); muteBtn.innerText = "🔇"; }
            });

            volSlider.addEventListener('input', (e) => {
                if(bgMusic) bgMusic.volume = e.target.value;
                if(e.target.value > 0 && bgMusic && bgMusic.paused) { bgMusic.play(); muteBtn.innerText = "🔊"; } 
                else if (e.target.value == 0 && bgMusic) { bgMusic.pause(); muteBtn.innerText = "🔇"; }
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
            let cinematicTimer = 0; // Timer para el paneo de cámara

            let lastDashTime = 0;
            const dashCooldown = 5000; 
            let dashTimer = 0; 

            let floatingTexts = []; let lasers = []; let particles = []; let boxes = []; let hearts = []; let orbs = [];
            let bgStarsLayer1 = []; let bgStarsLayer2 = [];
            
            for(let i=0; i<120; i++) {
                bgStarsLayer1.push({x: Math.random() * canvas.width, y: Math.random() * canvas.height, r: Math.random() * 1.5 + 0.5});
                bgStarsLayer2.push({x: Math.random() * canvas.width, y: Math.random() * canvas.height, r: Math.random() * 2.5 + 1.0});
            }

            let meteor = { orbitAngle: 0, orbitRadius: 450, x: worldW / 2, y: worldH / 2, r: 100, angle: 0, hp: 15000, maxHp: 15000, isBoss: false, dead: false, shootAngle: 0, craters: [ {x: -35, y: -25, r: 20}, {x: 35, y: -35, r: 16}, {x: 10, y: 30, r: 25}, {x: -40, y: 25, r: 14}, {x: 0, y: 0, r: 18} ] };
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
                playSfx("death", 0.3); // Sonido de muerte SÓLO para el jugador, y más bajo
                overScreen.style.display = 'block';
                if(playerLives > 0) { overTitle.innerText = "¡HAS MUERTO! 💥"; overMsg.innerText = `👉 DALE CLICK PARA REAPARECER (${playerLives} VIDAS RESTANTES) 👈`; overMsg.style.color = "#00FFFF"; } 
                else { overTitle.innerText = "FIN DE LA PARTIDA"; overMsg.innerText = "💀 SIN VIDAS - JUEGO TERMINADO - VUELVE AL MENÚ 💀"; overMsg.style.color = "#FF3333"; }
            }

            function respawnPlayer() {
                player.x = Math.random() * (worldW - 200) + 100; player.y = Math.random() * (worldH - 200) + 100;
                player.r = 18; player.hp = 200; player.maxHp = 200; player.shields = 0; player.dead = false;
                player.invulnTimer = 0; player.fireTimer = 0; player.speedBoostTimer = 0; player.hasInvulnCharge = false;
                player.laserRange = 1.0; player.laserDamage = 1.0; player.shotType = 'normal';
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

            function shootLaser() {
                if(player.dead || player.r <= 12) return;
                let targetX = (screenMouseX - canvas.width / 2) / zoom + camX + canvas.width / 2;
                let targetY = (screenMouseY - canvas.height / 2) / zoom + camY + canvas.height / 2;
                let dx = targetX - player.x; let dy = targetY - player.y; let dist = Math.hypot(dx, dy);
                if(dist === 0) return;

                let angle = Math.atan2(dy, dx); let speed = 15; let baseLife = 75 * player.laserRange;

                function fireAt(ang) {
                    lasers.push({ x: player.x, y: player.y, vx: Math.cos(ang) * speed, vy: Math.sin(ang) * speed, life: baseLife, owner: player, color: "#00FFFF", damageMult: player.laserDamage, isStar: false });
                }

                if(player.shotType === 'normal') { fireAt(angle); } 
                else if(player.shotType === 'triple') { fireAt(angle - 0.20); fireAt(angle); fireAt(angle + 0.20); } 
                else if(player.shotType === 'cross') { fireAt(angle); fireAt(angle + Math.PI/2); fireAt(angle + Math.PI); fireAt(angle - Math.PI/2); }

                playSfx("laser");
                player.r = Math.max(10, player.r - 0.4);
            }

            const nombres = ["Alpha", "Nova", "Sirius", "Vega", "Orion", "Cosmos", "Apollo", "Zeta", "Pulsar"];
            const colors = ['#FF3366', '#33CCFF', '#FF9933', '#33FF66', '#CC33FF', '#FFFF33', '#FF3333'];
            function randomColor() { return colors[Math.floor(Math.random() * colors.length)]; }
            function randomName() { return nombres[Math.floor(Math.random() * nombres.length)]; }

            function spawnBox() { boxes.push({ x: Math.random() * (worldW - 100) + 50, y: Math.random() * (worldH - 100) + 50, r: 16 }); }
            function spawnHeart() { hearts.push({ x: Math.random() * (worldW - 100) + 50, y: Math.random() * (worldH - 100) + 50, r: 10 }); }
            function spawnOrb() { orbs.push({ x: Math.random() * (worldW - 100) + 50, y: Math.random() * (worldH - 100) + 50, r: 14, type: Math.random() < 0.5 ? 'celeste' : 'morado' }); }

            let playerLives = 5; let player, bots, foods;
            const maxBots = 28; const maxFoods = 600;

            function init() {
                isGameOver = false; isPaused = false; playerLives = 5; cinematicTimer = 0; orbModal.style.display = 'none'; overScreen.style.display = 'none';
                floatingTexts = []; lasers = []; particles = []; boxes = []; hearts = []; orbs = [];
                
                player = { 
                    x: Math.random() * worldW, y: Math.random() * worldH, r: 18, color: '#FFFFFF', name: "__PLAYER_NICKNAME__", speed: 3.5, dead: false,
                    hp: 200, maxHp: 200, shields: 0, hasInvulnCharge: false, invulnTimer: 0, fireTimer: 0, speedBoostTimer: 0,
                    laserRange: 1.0, laserDamage: 1.0, shotType: 'normal'
                };
                
                bots = []; for(let i=0; i<maxBots; i++) spawnBot();
                foods = []; for(let i=0; i<maxFoods; i++) spawnFood();
                for(let i=0; i<35; i++) spawnHeart();
                
                spawnBox(); spawnBox(); spawnOrb();
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
                    // Ya no hay sonido de muerte para los bots
                    floatingTexts.push({ x: target.x, y: target.y, text: "💥 ¡DESTRUIDO!", color: "#FF3333", life: 40, size: 22 }); 
                }
            }

            function applyUpgrade(type) {
                if(type === 'range') player.laserRange += 0.4;
                if(type === 'damage') player.laserDamage += 0.5;
                if(type === 'triple') player.shotType = 'triple';
                if(type === 'cross') player.shotType = 'cross';
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
                    btn1.style.borderColor = '#CC33FF'; btn1.innerHTML = "🔱<br>DISPARO TRIPLE"; btn1.onclick = () => applyUpgrade('triple');
                    btn2.style.borderColor = '#CC33FF'; btn2.innerHTML = "➕<br>DISPARO EN CRUZ"; btn2.onclick = () => applyUpgrade('cross');
                }
            }

            function updateLeaderboard() {
                let allStars = [player, ...bots].filter(s => !s.dead); allStars.sort((a, b) => b.r - a.r); let topStars = allStars.slice(0, 10);
                let html = ""; topStars.forEach((s, idx) => { let isMe = (s === player); html += `<div class="lb-item ${isMe ? 'me' : ''}"><span>${idx + 1}. ${s.name}</span><span>${Math.round(s.r)} pt</span></div>`; });
                lbList.innerHTML = html;
            }

            function update() {
                if(Math.random() < 0.003 && boxes.length < 5) spawnBox();
                if(Math.random() < 0.002 && orbs.length < 3) spawnOrb();

                // Lógica de la Luna y su Fase Jefe
                if (!meteor.isBoss) {
                    meteor.orbitAngle += 0.0012; 
                    meteor.x = (worldW / 2) + Math.cos(meteor.orbitAngle) * meteor.orbitRadius; 
                    meteor.y = (worldH / 2) + Math.sin(meteor.orbitAngle) * meteor.orbitRadius;
                } else if (!meteor.dead && cinematicTimer <= 0) {
                    // La Luna persigue al jugador lentamente
                    if (!player.dead) {
                        let dx = player.x - meteor.x; let dy = player.y - meteor.y; let dist = Math.hypot(dx, dy);
                        if (dist > 0) { meteor.x += (dx/dist) * 1.5; meteor.y += (dy/dist) * 1.5; }
                    }
                    // La Luna dispara estrellas en espiral
                    meteor.shootAngle += 0.22;
                    if (Date.now() % 4 === 0) {
                        lasers.push({ x: meteor.x, y: meteor.y, vx: Math.cos(meteor.shootAngle) * 5, vy: Math.sin(meteor.shootAngle) * 5, life: 160, owner: meteor, color: "#FFA500", damageMult: 1.5, r: 9, isStar: true });
                    }
                }
                meteor.angle += 0.003;

                // Agujero Negro
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

                // Movimiento del jugador
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

                // Control de Cámara: Paneo cinemático a la Luna
                if (cinematicTimer > 0) {
                    cinematicTimer--;
                    meteor.r += (150 - meteor.r) * 0.03; // Crece hasta 150
                    let focusTarget = meteor;
                    zoom += (0.6 - zoom) * 0.05;
                    camX += (focusTarget.x - canvas.width / 2 - camX) * 0.06; 
                    camY += (focusTarget.y - canvas.height / 2 - camY) * 0.06;
                } else {
                    let focusTarget = (!player.dead) ? player : (allStars[0] || {x: worldW/2, y: worldH/2, r: 15});
                    let targetZoom = Math.max(0.25, 25 / Math.max(25, focusTarget.r * 0.6));
                    zoom += (targetZoom - zoom) * 0.05;
                    camX += (focusTarget.x - canvas.width / 2 - camX) * 0.1; camY += (focusTarget.y - canvas.height / 2 - camY) * 0.1;
                }

                // Colisiones de Láseres
                for(let i = lasers.length - 1; i >= 0; i--) {
                    let l = lasers[i]; l.x += l.vx; l.y += l.vy; l.life--; let hit = false; let dmg = 22 * (l.damageMult || 1);

                    if(!blackHole.dead && Math.hypot(l.x - blackHole.x, l.y - blackHole.y) < blackHole.r) {
                        blackHole.hp -= dmg; blackHole.r = Math.max(25, blackHole.r - 0.25);
                        if(blackHole.hp <= 0 && !blackHole.dead) { 
                            blackHole.dead = true; 
                            playSfx("bh_death", 2.5); // Explosión 2.5x más fuerte
                            // TRANSICIÓN A JEFE LUNA SANGRIENTA
                            meteor.isBoss = true; cinematicTimer = 180;
                            if(bgMusic) bgMusic.playbackRate = 1.3; // Música de transformación (se acelera y sube tono)
                            playSfx("boss_music", 1.5);
                            floatingTexts.push({ x: meteor.x, y: meteor.y - 120, text: "⚠️ LA LUNA DESPIERTA ⚠️", color: "#FF4500", life: 180, size: 40 });
                        } 
                        hit = true;
                    }

                    if(meteor.isBoss && !meteor.dead && l.owner !== meteor && Math.hypot(l.x - meteor.x, l.y - meteor.y) < meteor.r) {
                        meteor.hp -= dmg; hit = true;
                        if(meteor.hp <= 0 && !meteor.dead) {
                            meteor.dead = true;
                            playSfx("bh_death", 2.5); // Explosión final épica
                            floatingTexts.push({ x: meteor.x, y: meteor.y, text: "🌟 VICTORIA GALÁCTICA 🌟", color: "#FFD700", life: 300, size: 50 });
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
                                meteor.isBoss = true; cinematicTimer = 180; if(bgMusic) bgMusic.playbackRate = 1.3; playSfx("boss_music", 1.5);
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
                if(cinematicTimer > 0) { shakeX = (Math.random() - 0.5) * 6; shakeY = (Math.random() - 0.5) * 6; } // Temblor al transformarse la Luna

                ctx.save(); ctx.translate(canvas.width / 2 + shakeX, canvas.height / 2 + shakeY); ctx.scale(zoom, zoom); ctx.translate(-camX - canvas.width / 2, -camY - canvas.height / 2);
                ctx.strokeStyle = "#FF3366"; ctx.lineWidth = 6; ctx.strokeRect(0, 0, worldW, worldH);

                if(!meteor.dead) {
                    ctx.save(); ctx.translate(meteor.x, meteor.y); ctx.rotate(meteor.angle); ctx.beginPath(); ctx.arc(0, 0, meteor.r, 0, Math.PI * 2); 
                    ctx.fillStyle = meteor.isBoss ? "#FF6600" : "#A9A9A9"; 
                    if(meteor.isBoss) { ctx.shadowColor = "#FF4500"; ctx.shadowBlur = 40; }
                    ctx.fill(); ctx.shadowBlur = 0;
                    meteor.craters.forEach(c => { ctx.beginPath(); ctx.arc(c.x, c.y, c.r, 0, Math.PI * 2); ctx.fillStyle = meteor.isBoss ? "#CC3300" : "#696969"; ctx.fill(); }); 
                    ctx.restore();

                    // Barra de Jefe Final (Luna)
                    if(meteor.isBoss) {
                        ctx.save(); ctx.translate(meteor.x, meteor.y);
                        let bossHpPct = Math.max(0, meteor.hp / meteor.maxHp); let barW = 220, barH = 14; 
                        ctx.fillStyle = "rgba(0,0,0,0.7)"; ctx.fillRect(-barW/2, -meteor.r - 40, barW, barH); 
                        ctx.fillStyle = "#FF4500"; ctx.fillRect(-barW/2 + 1, -meteor.r - 39, (barW - 2) * bossHpPct, barH - 2); 
                        ctx.strokeStyle = "#FFFFFF"; ctx.lineWidth = 2; ctx.strokeRect(-barW/2, -meteor.r - 40, barW, barH);
                        ctx.fillStyle = "#FFD700"; ctx.font = "bold 16px sans-serif"; ctx.textAlign = "center"; 
                        ctx.fillText(`🌕 LUNA SANGRIENTA: ${Math.ceil(meteor.hp)} / ${meteor.maxHp} HP`, 0, -meteor.r - 48); 
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
                orbs.forEach(o => { ctx.save(); ctx.translate(o.x, o.y); ctx.beginPath(); ctx.arc(0, 0, o.r, 0, Math.PI * 2); ctx.fillStyle = o.type === 'celeste' ? '#00FFFF' : '#CC33FF'; ctx.fill(); ctx.strokeStyle = "white"; ctx.lineWidth = 2; ctx.stroke(); ctx.globalAlpha = 0.5; ctx.beginPath(); ctx.arc(0, 0, o.r + Math.sin(Date.now() / 150)*4, 0, Math.PI * 2); ctx.strokeStyle = o.type === 'celeste' ? '#00FFFF' : '#CC33FF'; ctx.lineWidth = 2; ctx.stroke(); ctx.restore(); });
                hearts.forEach(h => { ctx.font = "16px sans-serif"; ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText("❤️", h.x, h.y); });
                particles.forEach(p => { ctx.beginPath(); ctx.arc(p.x, p.y, 3, 0, Math.PI * 2); ctx.fillStyle = p.color; ctx.fill(); });
                
                // Dibujar Láseres y Estrellas en Espiral de la Luna
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
                if(player.hasInvulnCharge || player.invulnTimer > 0) { ctx.fillStyle = player.invulnTimer > 0 ? "#00FFFF" : "#FFD700"; ctx.font = "bold 12px sans-serif"; ctx.textAlign = "left"; ctx.fillText(player.invulnTimer > 0 ? `👻 FANTASMA: ${(player.invulnTimer/60).toFixed(1)}s` : "👻 [ESPACIO]: FANTASMA LISTO", x, y - 55); }
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
