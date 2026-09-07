import streamlit as st
import streamlit.components.v1 as components
import base64
import os
import json

st.set_page_config(page_title="Star.io - Batalla Galáctica", layout="wide")

st.title("🌟 Star.io - Batalla Galáctica")
st.write("¡Sobrevive, domina el Top y destruye al Agujero Negro para enfrentar a la Luna!")

# ==========================================
# 🎵 CONFIGURACIÓN DE AUDIO (MÚSICA Y EFECTOS)
# ==========================================
def obtener_audio_b64(ruta):
    if os.path.exists(ruta):
        with open(ruta, "rb") as f:
            audio_bytes = f.read()
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            extension = ruta.split('.')[-1]
            return f"data:audio/{extension};base64,{audio_base64}"
    return None

audio_src = obtener_audio_b64("test.wav") or obtener_audio_b64(os.path.join("sonidos", "test.wav")) or ""
if not audio_src:
    st.warning("⚠️ No se encontró la música de fondo (test.wav).")

# SE AÑADIÓ "bhexplosion" A LA LISTA
sfx_categorias = ["dash", "laser", "food", "box", "orb", "death", "respawn", "explosionagujeronegro"]
sfx_data = {cat: [] for cat in sfx_categorias}

for cat in sfx_categorias:
    for i in range(1, 5):
        posibles_rutas = [
            f"{cat}{i}.wav",
            f"{cat}{i}.mp3",
            os.path.join("sonidos", f"{cat}{i}.wav"),
            os.path.join("sonidos", f"{cat}{i}.mp3"),
        ]
        
        b64_str = None
        for ruta in posibles_rutas:
            b64_str = obtener_audio_b64(ruta)
            if b64_str:
                break
                
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
            #audio-controls { position: absolute; top: 15px; left: 15px; background: rgba(10, 10, 20, 0.85); border: 2px solid #00FFFF; border-radius: 8px; padding: 8px 15px; display: flex; align-items: center; gap: 12px; z-index: 15; }
            #mute-btn { background: none; border: none; font-size: 22px; cursor: pointer; padding: 0; margin: 0; color: white; }
            input[type=range] { -webkit-appearance: none; width: 90px; background: transparent; }
            input[type=range]::-webkit-slider-thumb { -webkit-appearance: none; height: 16px; width: 16px; border-radius: 50%; background: #00FFFF; cursor: pointer; margin-top: -6px; }
            input[type=range]::-webkit-slider-runnable-track { width: 100%; height: 4px; background: #444; border-radius: 2px; }
        </style>
    </head>
    <body>
        <div id="main-wrapper">
            <div style="position: relative;">
                <div id="audio-controls">
                    <button id="mute-btn">🔇</button>
                    <input type="range" id="volume-slider" min="0" max="1" step="0.05" value="0.3">
                </div>
                <canvas id="gameCanvas" width="900" height="650"></canvas>
                <div id="gameover">
                    <h2>¡HAS MUERTO! 💥</h2>
                    <p id="gameover-msg" style="font-size: 22px; color: #00FFFF; font-weight: bold;">👉 DALE CLICK AL JUEGO PARA REAPARECER 👈</p>
                </div>
                <div id="orb-modal">
                    <h2 id="orb-title">NUEVA MEJORA</h2>
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
            const audioSrc = "__AUDIO_SRC__";
            const sfxData = __SFX_DATA__;
            let bgMusic = null;
            let isUserInteracted = false;
            
            const muteBtn = document.getElementById("mute-btn");
            const volSlider = document.getElementById("volume-slider");

            if (audioSrc && audioSrc !== "") {
                bgMusic = new Audio(audioSrc);
                bgMusic.loop = true; bgMusic.volume = volSlider.value;
            }

            function playSfx(type) {
                if (!isUserInteracted) return;
                let soundArray = sfxData[type];
                if (soundArray && soundArray.length > 0) {
                    let randomSrc = soundArray[Math.floor(Math.random() * soundArray.length)];
                    let snd = new Audio(randomSrc);
                    snd.volume = volSlider.value;
                    snd.play().catch(e => {});
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
                if(bgMusic.paused) { bgMusic.play(); muteBtn.innerText = "🔊"; if(volSlider.value == 0) { volSlider.value = 0.3; bgMusic.volume = 0.3; } } 
                else { bgMusic.pause(); muteBtn.innerText = "🔇"; }
            });
            volSlider.addEventListener('input', (e) => {
                if(bgMusic) bgMusic.volume = e.target.value;
                if(e.target.value > 0 && bgMusic && bgMusic.paused) { bgMusic.play(); muteBtn.innerText = "🔊"; } 
                else if (e.target.value == 0 && bgMusic) { bgMusic.pause(); muteBtn.innerText = "🔇"; }
            });

            const canvas = document.getElementById("gameCanvas"); const ctx = canvas.getContext("2d");
            const overScreen = document.getElementById("gameover"); const overMsg = document.getElementById("gameover-msg");
            const lbList = document.getElementById("lb-list");
            const orbModal = document.getElementById("orb-modal"); const orbTitle = document.getElementById("orb-title");
            const btn1 = document.getElementById("orb-btn1"); const btn2 = document.getElementById("orb-btn2");

            window.addEventListener('contextmenu', (e) => e.preventDefault());

            const worldW = 3200; const worldH = 3200; const LARGE_THRESHOLD = 50; 
            let camX = 0, camY = 0, zoom = 1; let screenMouseX = canvas.width / 2; let screenMouseY = canvas.height / 2;
            let isGameOver = false; let isPaused = false;
            let lastDashTime = 0; const dashCooldown = 5000; let dashTimer = 0; 

            let floatingTexts = []; let lasers = []; let particles = []; let boxes = []; let hearts = []; let orbs = [];
            let moonProjectiles = []; // ESTRELLAS EN ESPIRAL DE LA LUNA
            let bgStarsLayer1 = []; let bgStarsLayer2 = [];
            
            for(let i=0; i<120; i++) {
                bgStarsLayer1.push({x: Math.random() * canvas.width, y: Math.random() * canvas.height, r: Math.random() * 1.5 + 0.5});
                bgStarsLayer2.push({x: Math.random() * canvas.width, y: Math.random() * canvas.height, r: Math.random() * 2.5 + 1.0});
            }

            let meteor = {}; let blackHole = {};

            canvas.addEventListener('mousemove', (e) => { const rect = canvas.getBoundingClientRect(); screenMouseX = e.clientX - rect.left; screenMouseY = e.clientY - rect.top; });
            canvas.addEventListener('mousedown', (e) => {
                if(isPaused) return;
                if(player.dead) { if (playerLives > 0) respawnPlayer(); return; }
                if(e.button === 0) shootLaser();
                else if(e.button === 2) { e.preventDefault(); triggerDash(); }
            });
            window.addEventListener('keydown', (e) => {
                if(isPaused) return;
                if(e.code === 'Space') { e.preventDefault(); if(player.dead) { if(playerLives > 0) respawnPlayer(); } else { triggerInvulnerability(); } }
            });

            function handlePlayerDeath() {
                playerLives--; isGameOver = true; playSfx("death"); overScreen.style.display = 'block';
                if(playerLives > 0) { overMsg.innerText = `👉 DALE CLICK PARA REAPARECER (${playerLives} VIDAS RESTANTES) 👈`; overMsg.style.color = "#00FFFF"; } 
                else { overMsg.innerText = "💀 SIN VIDAS - JUEGO TERMINADO 💀"; overMsg.style.color = "#FF3333"; }
            }

            function respawnPlayer() {
                player.x = Math.random() * (worldW - 200) + 100; player.y = Math.random() * (worldH - 200) + 100;
                player.r = 18; player.hp = 200; player.maxHp = 200; player.shields = 0; player.dead = false;
                player.invulnTimer = 0; player.fireTimer = 0;
                player.modifiers = { lsSpeed: 1, lsFireRate: 1, moveSpeed: 1, bounce: false, split: false, shieldCap: 0, multishot: 0, vampirism: false };
                isGameOver = false; overScreen.style.display = 'none';
                playSfx("respawn");
            }

            class Bot {
                constructor() {
                    this.name = "Bot" + Math.floor(Math.random() * 1000); this.x = Math.random() * worldW; this.y = Math.random() * worldH;
                    this.r = Math.random() * 10 + 15; this.hp = 100 + (this.r - 15) * 5; this.maxHp = this.hp;
                    this.speed = Math.random() * 0.8 + 1.2; this.color = `hsl(${Math.random() * 360}, 80%, 60%)`;
                    this.vx = 0; this.vy = 0; this.dead = false; this.kills = 0; this.fireTimer = 0;
                }
                update() {
                    if(this.dead) return;
                    let target = player; let dist = Math.hypot(this.x - player.x, this.y - player.y);
                    bots.forEach(b => { if(b !== this && !b.dead) { let d = Math.hypot(this.x - b.x, this.y - b.y); if(d < dist) { dist = d; target = b; } } });
                    if(dist < 500 && !target.dead) {
                        let a = Math.atan2(target.y - this.y, target.x - this.x);
                        this.vx = Math.cos(a) * this.speed; this.vy = Math.sin(a) * this.speed;
                        if(this.fireTimer <= 0 && this.r > LARGE_THRESHOLD) { botsShootLaser(this, a); this.fireTimer = 50; }
                    } else { this.vx *= 0.98; this.vy *= 0.98; }
                    this.x += this.vx; this.y += this.vy; this.fireTimer--;
                    if(this.x < 0 || this.x > worldW) this.vx *= -1; if(this.y < 0 || this.y > worldH) this.vy *= -1;
                    this.x = Math.max(0, Math.min(worldW, this.x)); this.y = Math.max(0, Math.min(worldH, this.y));
                }
            }

            let player = { name: "__NICKNAME__", x: worldW/2, y: worldH/2, r: 18, hp: 200, maxHp: 200, shields: 0, color: '#00FFFF', dead: false, kills: 0, invulnTimer: 0, fireTimer: 0, dashActive: 0, modifiers: { lsSpeed: 1, lsFireRate: 1, moveSpeed: 1, bounce: false, split: false, shieldCap: 0, multishot: 0, vampirism: false } };
            let playerLives = 3; let bots = []; let food = []; let allStars = [];
            
            function init() {
                bots = []; food = []; boxes = []; hearts = []; orbs = []; floatingTexts = []; lasers = []; particles = [];
                moonProjectiles = []; // RESETEAR PROYECTILES DE LA LUNA
                player.name = "__NICKNAME__";
                meteor = { orbitAngle: 0, orbitRadius: 450, x: worldW / 2, y: worldH / 2, r: 100, angle: 0, 
                           craters: [ {x: -35, y: -25, r: 20}, {x: 35, y: -35, r: 16}, {x: 10, y: 30, r: 25}, {x: -40, y: 25, r: 14}, {x: 0, y: 0, r: 18} ], 
                           hp: 15000, maxHp: 15000, isBoss: false, dead: false, shootAngle: 0, lastShootTime: 0 };
                blackHole = { x: worldW * 0.7, y: worldH * 0.3, r: 75, hp: 10000, maxHp: 10000, dead: false, deathTriggered: false };

                for(let i=0; i<15; i++) bots.push(new Bot());
                for(let i=0; i<300; i++) food.push({x: Math.random() * worldW, y: Math.random() * worldH, color: `hsl(${Math.random() * 360}, 100%, 70%)`, r: 4});
                for(let i=0; i<5; i++) boxes.push({x: Math.random() * worldW, y: Math.random() * worldH, size: 25, hp: 40, maxHp: 40});
                allStars = [player, ...bots];
            }

            function triggerInvulnerability() { if(player.invulnTimer <= 0) player.invulnTimer = 60; }
            function triggerDash() {
                let now = performance.now();
                if(now - lastDashTime > dashCooldown) { playSfx("dash"); player.dashActive = 10; lastDashTime = now; dashTimer = dashCooldown; }
            }

            function shootLaser() {
                if(player.fireTimer > 0) return;
                let mouseWorldX = player.x + (screenMouseX - canvas.width/2)/zoom;
                let mouseWorldY = player.y + (screenMouseY - canvas.height/2)/zoom;
                let a = Math.atan2(mouseWorldY - player.y, mouseWorldX - player.x);
                let speed = 12 * player.modifiers.lsSpeed;
                playSfx("laser");
                lasers.push({ x: player.x, y: player.y, vx: Math.cos(a)*speed, vy: Math.sin(a)*speed, owner: player, life: 60, size: player.r > LARGE_THRESHOLD ? 6 : 4, bounceCount: player.modifiers.bounce ? 1 : 0 });
                if(player.modifiers.multishot > 0) {
                    let spread = 0.2;
                    lasers.push({ x: player.x, y: player.y, vx: Math.cos(a - spread)*speed, vy: Math.sin(a - spread)*speed, owner: player, life: 60, size: player.r > LARGE_THRESHOLD ? 6 : 4, bounceCount: player.modifiers.bounce ? 1 : 0 });
                    lasers.push({ x: player.x, y: player.y, vx: Math.cos(a + spread)*speed, vy: Math.sin(a + spread)*speed, owner: player, life: 60, size: player.r > LARGE_THRESHOLD ? 6 : 4, bounceCount: player.modifiers.bounce ? 1 : 0 });
                }
                player.fireTimer = Math.max(5, 20 / player.modifiers.lsFireRate);
            }

            function botsShootLaser(bot, angle) { lasers.push({ x: bot.x, y: bot.y, vx: Math.cos(angle)*8, vy: Math.sin(angle)*8, owner: bot, life: 50, size: 4, bounceCount: 0 }); }

            function spawnParticles(x, y, color) { for(let i=0; i<8; i++) particles.push({ x: x, y: y, vx: (Math.random() - 0.5)*5, vy: (Math.random() - 0.5)*5, color: color, life: 20 }); }
            function addFloatingText(x, y, text, color) { floatingTexts.push({ x: x, y: y, text: text, color: color, life: 30 }); }

            function takeDamage(entity, dmg) {
                if(entity === player && player.invulnTimer > 0) return;
                if(entity.shields > 0) {
                    let absorb = Math.min(entity.shields, dmg);
                    entity.shields -= absorb; dmg -= absorb; addFloatingText(entity.x, entity.y - 15, `-${Math.ceil(absorb)}`, "#00FFFF");
                }
                if(dmg > 0) {
                    entity.hp -= dmg; addFloatingText(entity.x, entity.y, `-${Math.ceil(dmg)}`, "#FF3333");
                    if(entity.hp <= 0) {
                        entity.dead = true;
                        if(entity === player) handlePlayerDeath();
                        else {
                            for(let i=0; i<entity.r; i++) food.push({ x: entity.x + (Math.random()-0.5)*30, y: entity.y + (Math.random()-0.5)*30, color: entity.color, r: 6 });
                        }
                    }
                }
            }

            function dropLoot(x, y) {
                let r = Math.random();
                if(r < 0.2) orbs.push({x: x, y: y});
                else if(r < 0.5) hearts.push({x: x, y: y});
            }

            let lastTime = performance.now();

            function update() {
                if (isPaused) return;
                let now = performance.now(); let dt = now - lastTime; lastTime = now;

                if (!player.dead) {
                    if(dashTimer > 0) dashTimer = Math.max(0, dashTimer - dt);
                    let mouseWorldX = player.x + (screenMouseX - canvas.width/2)/zoom;
                    let mouseWorldY = player.y + (screenMouseY - canvas.height/2)/zoom;
                    let angle = Math.atan2(mouseWorldY - player.y, mouseWorldX - player.x);
                    let dist = Math.hypot(mouseWorldX - player.x, mouseWorldY - player.y);
                    let targetSpeed = dist > 10 ? (player.r > LARGE_THRESHOLD ? 2.5 : 4) * player.modifiers.moveSpeed : 0;
                    if(player.dashActive > 0) { targetSpeed *= 3; player.dashActive--; spawnParticles(player.x, player.y, "#00FFFF"); }
                    player.x += Math.cos(angle) * targetSpeed; player.y += Math.sin(angle) * targetSpeed;
                    player.x = Math.max(0, Math.min(worldW, player.x)); player.y = Math.max(0, Math.min(worldH, player.y));
                    if(player.invulnTimer > 0) player.invulnTimer--;
                    if(player.fireTimer > 0) player.fireTimer--;
                }

                bots.forEach(b => b.update());

                // Mover y Dibujar la Luna
                if (!meteor.isBoss) {
                    meteor.orbitAngle += 0.002;
                    if(!blackHole.dead) { meteor.x = blackHole.x + Math.cos(meteor.orbitAngle) * meteor.orbitRadius; meteor.y = blackHole.y + Math.sin(meteor.orbitAngle) * meteor.orbitRadius; }
                }
                meteor.angle += 0.01;

                // 🌕 ATAQUE DE LA LUNA (JEFA)
                if (meteor.isBoss && !meteor.dead) {
                    if (now - meteor.lastShootTime > 200) { 
                        meteor.shootAngle += 0.4;
                        let vx = Math.cos(meteor.shootAngle) * 4;
                        let vy = Math.sin(meteor.shootAngle) * 4;
                        moonProjectiles.push({ x: meteor.x, y: meteor.y, vx: vx, vy: vy, life: 400, rot: 0 });
                        meteor.lastShootTime = now;
                    }
                }

                // Actualizar proyectiles de la Luna
                for(let i = moonProjectiles.length - 1; i >= 0; i--) {
                    let mp = moonProjectiles[i];
                    mp.x += mp.vx; mp.y += mp.vy; mp.life--; mp.rot += 0.1;
                    let hitPlayer = false;
                    if(!player.dead && Math.hypot(mp.x - player.x, mp.y - player.y) < player.r + 15) {
                        takeDamage(player, 50); hitPlayer = true;
                    }
                    if(hitPlayer || mp.life <= 0) moonProjectiles.splice(i, 1);
                }

                for(let i = lasers.length - 1; i >= 0; i--) {
                    let l = lasers[i]; l.x += l.vx; l.y += l.vy; l.life--; let hit = false;
                    allStars.forEach(s => {
                        if(!s.dead && l.owner !== s && Math.hypot(l.x - s.x, l.y - s.y) < s.r + l.size) {
                            let dmg = l.size * 5; takeDamage(s, dmg);
                            if(l.owner === player && player.modifiers.vampirism) player.hp = Math.min(player.maxHp, player.hp + dmg * 0.2);
                            if(s.dead && l.owner) l.owner.kills++;
                            spawnParticles(l.x, l.y, s.color); hit = true;
                        }
                    });

                    // Colisión Laser vs Luna (Jefa)
                    if(meteor.isBoss && !meteor.dead && !hit) {
                        if(Math.hypot(l.x - meteor.x, l.y - meteor.y) < meteor.r) {
                            meteor.hp -= l.size * 5; hit = true;
                            if(meteor.hp <= 0) meteor.dead = true;
                            for(let k=0; k<4; k++) particles.push({ x: l.x, y: l.y, vx: (Math.random() - 0.5)*4, vy: (Math.random() - 0.5)*4, color: "#FFD700", life: 15 });
                        }
                    }

                    if(!hit) {
                        boxes.forEach(b => {
                            if(Math.hypot(l.x - b.x, l.y - b.y) < b.size + l.size) {
                                b.hp -= l.size * 5; hit = true; spawnParticles(l.x, l.y, "#D2B48C");
                                if(b.hp <= 0) dropLoot(b.x, b.y);
                            }
                        });
                    }

                    if(!hit && !blackHole.dead && Math.hypot(l.x - blackHole.x, l.y - blackHole.y) < blackHole.r) {
                        blackHole.hp -= l.size * 5; blackHole.r = Math.max(25, blackHole.r - 0.25); hit = true;
                        if(blackHole.hp <= 0 && !blackHole.deathTriggered) { 
                            blackHole.dead = true; blackHole.deathTriggered = true;
                            playSfx("bhexplosion"); // SONIDO NUEVO
                            meteor.isBoss = true; meteor.r = 250; meteor.hp = 15000;
                        }
                    }
                    if(hit || l.life <= 0) {
                        if(hit && l.bounceCount > 0) { l.vx *= -1; l.vy *= -1; l.bounceCount--; }
                        else if(hit && l.owner.modifiers && l.owner.modifiers.split && l.life > 0) {
                            l.owner.modifiers.split = false; let a = Math.atan2(l.vy, l.vx); let s = Math.hypot(l.vx, l.vy);
                            lasers.push({x: l.x, y: l.y, vx: Math.cos(a-0.5)*s, vy: Math.sin(a-0.5)*s, owner: l.owner, life: 30, size: l.size, bounceCount: 0});
                            lasers.push({x: l.x, y: l.y, vx: Math.cos(a+0.5)*s, vy: Math.sin(a+0.5)*s, owner: l.owner, life: 30, size: l.size, bounceCount: 0});
                            lasers.splice(i, 1);
                        } else lasers.splice(i, 1);
                    }
                }

                if(!meteor.dead) {
                    allStars.forEach(s => { 
                        let dmg = meteor.isBoss ? 150 : 100;
                        if(Math.hypot(s.x - meteor.x, s.y - meteor.y) < s.r + meteor.r * 0.85) takeDamage(s, dmg); 
                    });
                }
                
                if(!blackHole.dead) {
                    allStars.forEach(s => {
                        if(Math.hypot(s.x - blackHole.x, s.y - blackHole.y) < s.r + blackHole.r * 0.8) {
                            if(s.r > blackHole.r * 1.25) { 
                                if(!blackHole.deathTriggered) {
                                    blackHole.dead = true; blackHole.deathTriggered = true; playSfx("bhexplosion");
                                    meteor.isBoss = true; meteor.r = 250; meteor.hp = 15000;
                                }
                                s.r += 35; 
                            } else { 
                                if(s === player && !player.dead) { player.hp = 0; player.dead = true; handlePlayerDeath(); } 
                                else if(s !== player) { s.dead = true; } 
                            }
                        }
                    });
                }

                allStars.forEach(s => {
                    if(s.dead) return;
                    for(let i = food.length - 1; i >= 0; i--) {
                        if(Math.hypot(s.x - food[i].x, s.y - food[i].y) < s.r) { s.r += 0.5; s.maxHp += 2; s.hp = Math.min(s.maxHp, s.hp + 2); food.splice(i, 1); if(s === player) playSfx("food"); }
                    }
                    for(let i = boxes.length - 1; i >= 0; i--) {
                        if(s.r > LARGE_THRESHOLD && Math.hypot(s.x - boxes[i].x, s.y - boxes[i].y) < s.r + boxes[i].size) { s.r += 2; boxes.splice(i, 1); playSfx("box"); }
                    }
                    for(let i = hearts.length - 1; i >= 0; i--) {
                        if(Math.hypot(s.x - hearts[i].x, s.y - hearts[i].y) < s.r + 15) { s.hp = Math.min(s.maxHp, s.hp + 50); addFloatingText(s.x, s.y, "+50 HP", "#33FF33"); hearts.splice(i, 1); }
                    }
                    if(s === player) {
                        for(let i = orbs.length - 1; i >= 0; i--) {
                            if(Math.hypot(player.x - orbs[i].x, player.y - orbs[i].y) < player.r + 15) { orbs.splice(i, 1); showOrbModal(); playSfx("orb"); }
                        }
                    }
                });
                
                boxes = boxes.filter(b => b.hp > 0);
                if(Math.random() < 0.05 && food.length < 400) food.push({x: Math.random() * worldW, y: Math.random() * worldH, color: `hsl(${Math.random() * 360}, 100%, 70%)`, r: 4});
                if(Math.random() < 0.005 && boxes.length < 15) boxes.push({x: Math.random() * worldW, y: Math.random() * worldH, size: 25, hp: 40, maxHp: 40});
                let aliveBots = bots.filter(b => !b.dead).length;
                if(aliveBots < 15 && Math.random() < 0.01) bots.push(new Bot());
                
                for(let i = particles.length - 1; i >= 0; i--) { let p = particles[i]; p.x += p.vx; p.y += p.vy; p.life--; if(p.life <= 0) particles.splice(i, 1); }
                for(let i = floatingTexts.length - 1; i >= 0; i--) { let ft = floatingTexts[i]; ft.y -= 1; ft.life--; if(ft.life <= 0) floatingTexts.splice(i, 1); }

                updateLeaderboard();
            }

            function updateLeaderboard() {
                let sorted = allStars.slice().sort((a, b) => (b.r * 10 + b.kills * 50) - (a.r * 10 + a.kills * 50));
                lbList.innerHTML = "";
                for(let i = 0; i < Math.min(5, sorted.length); i++) {
                    let s = sorted[i];
                    let div = document.createElement("div"); div.className = "lb-item";
                    if(s === player) div.classList.add("me");
                    let nameSpan = document.createElement("span"); nameSpan.innerText = `${i+1}. ${s.name}`;
                    let scoreSpan = document.createElement("span"); scoreSpan.innerText = Math.floor(s.r * 10 + s.kills * 50);
                    div.appendChild(nameSpan); div.appendChild(scoreSpan); lbList.appendChild(div);
                }
            }

            const powers = [
                { name: "⚡ Velocidad Proyectil", desc: "Tus lásers viajan 30% más rápido", apply: () => player.modifiers.lsSpeed += 0.3 },
                { name: "🔥 Cadencia +", desc: "Disparas 20% más rápido", apply: () => player.modifiers.lsFireRate += 0.2 },
                { name: "🪶 Ligereza", desc: "Te mueves 20% más rápido", apply: () => player.modifiers.moveSpeed += 0.2 },
                { name: "🛡️ Escudo Extra", desc: "+100 Escudo", apply: () => { player.modifiers.shieldCap += 100; player.shields = player.modifiers.shieldCap; } },
                { name: "🩸 Vampirismo", desc: "Te curas un poco al dañar", apply: () => player.modifiers.vampirism = true },
                { name: "🔱 Disparo Triple", desc: "Disparas 3 lásers en abanico", apply: () => player.modifiers.multishot = 1 }
            ];

            function showOrbModal() {
                isPaused = true; orbModal.style.display = 'block';
                let p1 = powers[Math.floor(Math.random() * powers.length)]; let p2 = powers[Math.floor(Math.random() * powers.length)];
                while(p1 === p2) p2 = powers[Math.floor(Math.random() * powers.length)];
                btn1.innerHTML = `${p1.name}<br><br><span style='font-size:12px; font-weight:normal'>${p1.desc}</span>`;
                btn2.innerHTML = `${p2.name}<br><br><span style='font-size:12px; font-weight:normal'>${p2.desc}</span>`;
                btn1.onclick = () => { p1.apply(); isPaused = false; orbModal.style.display = 'none'; };
                btn2.onclick = () => { p2.apply(); isPaused = false; orbModal.style.display = 'none'; };
            }

            function drawBg(offsetX, offsetY, parallax) {
                ctx.fillStyle = "#FFFFFF";
                (parallax === 0.5 ? bgStarsLayer1 : bgStarsLayer2).forEach(s => {
                    let rx = (s.x - offsetX * parallax) % canvas.width; if (rx < 0) rx += canvas.width;
                    let ry = (s.y - offsetY * parallax) % canvas.height; if (ry < 0) ry += canvas.height;
                    ctx.beginPath(); ctx.arc(rx, ry, s.r, 0, Math.PI * 2); ctx.fill();
                });
            }

            function draw() {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                camX = player.x - canvas.width / (2 * zoom); camY = player.y - canvas.height / (2 * zoom);
                drawBg(camX, camY, 0.5); drawBg(camX, camY, 0.8);
                
                ctx.save(); ctx.scale(zoom, zoom); ctx.translate(-camX, -camY);

                food.forEach(f => { ctx.beginPath(); ctx.arc(f.x, f.y, f.r, 0, Math.PI * 2); ctx.fillStyle = f.color; ctx.shadowColor = f.color; ctx.shadowBlur = 10; ctx.fill(); });
                ctx.shadowBlur = 0;

                boxes.forEach(b => { ctx.fillStyle = "#8B4513"; ctx.fillRect(b.x - b.size/2, b.y - b.size/2, b.size, b.size); ctx.strokeStyle = "#D2B48C"; ctx.lineWidth = 2; ctx.strokeRect(b.x - b.size/2, b.y - b.size/2, b.size, b.size); ctx.fillStyle = "#FF0000"; ctx.fillRect(b.x - b.size/2, b.y - b.size/2 - 10, b.size * (b.hp/b.maxHp), 4); });
                hearts.forEach(h => { ctx.fillStyle = "#FF3333"; ctx.beginPath(); ctx.arc(h.x, h.y, 8, 0, Math.PI * 2); ctx.fill(); ctx.fillStyle = "white"; ctx.font = "12px sans-serif"; ctx.fillText("+", h.x-4, h.y+4); });
                orbs.forEach(o => { ctx.fillStyle = "#AA00FF"; ctx.beginPath(); ctx.arc(o.x, o.y, 12, 0, Math.PI * 2); ctx.shadowColor = "#AA00FF"; ctx.shadowBlur = 15; ctx.fill(); ctx.shadowBlur = 0; });

                if(!meteor.dead) {
                    ctx.save(); ctx.translate(meteor.x, meteor.y); 
                    ctx.rotate(meteor.angle); ctx.beginPath(); ctx.arc(0, 0, meteor.r, 0, Math.PI * 2); 
                    ctx.fillStyle = meteor.isBoss ? "#FFD700" : "#A9A9A9"; ctx.fill();
                    if(meteor.isBoss) { ctx.strokeStyle = "#FF8C00"; ctx.lineWidth = 10; ctx.stroke(); ctx.shadowColor = "#FFD700"; ctx.shadowBlur = 30; ctx.fill(); }
                    meteor.craters.forEach(c => { 
                        let scale = meteor.isBoss ? 2 : 1;
                        ctx.beginPath(); ctx.arc(c.x * scale, c.y * scale, c.r * scale, 0, Math.PI * 2); 
                        ctx.fillStyle = meteor.isBoss ? "#DAA520" : "#696969"; ctx.fill(); 
                    }); 
                    ctx.restore();

                    if(meteor.isBoss) {
                        let hpPct = Math.max(0, meteor.hp / meteor.maxHp); 
                        let barW = 200, barH = 14; 
                        ctx.fillStyle = "rgba(0,0,0,0.7)"; ctx.fillRect(meteor.x - barW/2, meteor.y - meteor.r - 40, barW, barH); 
                        ctx.fillStyle = "#FFD700"; ctx.fillRect(meteor.x - barW/2 + 1, meteor.y - meteor.r - 39, (barW - 2) * hpPct, barH - 2); 
                        ctx.strokeStyle = "#FFFFFF"; ctx.lineWidth = 1; ctx.strokeRect(meteor.x - barW/2, meteor.y - meteor.r - 40, barW, barH);
                        ctx.fillStyle = "#FFF"; ctx.font = "bold 16px sans-serif"; ctx.textAlign = "center"; 
                        ctx.fillText(`🌕 LUNA MAYOR: ${Math.ceil(meteor.hp)} / ${meteor.maxHp} HP`, meteor.x, meteor.y - meteor.r - 48);
                    }
                }

                if(!blackHole.dead) {
                    ctx.beginPath(); ctx.arc(blackHole.x, blackHole.y, blackHole.r, 0, Math.PI * 2); ctx.fillStyle = "black"; ctx.shadowColor = "#8A2BE2"; ctx.shadowBlur = 40; ctx.fill(); ctx.shadowBlur = 0;
                    ctx.fillStyle = "#FF0000"; ctx.fillRect(blackHole.x - 40, blackHole.y - blackHole.r - 20, 80 * (blackHole.hp/blackHole.maxHp), 6);
                    ctx.fillStyle = "white"; ctx.font = "12px sans-serif"; ctx.textAlign = "center"; ctx.fillText("AGUJERO NEGRO", blackHole.x, blackHole.y - blackHole.r - 25);
                }

                // Dibujar Estrellas de la Jefa Luna
                moonProjectiles.forEach(mp => {
                    ctx.save(); ctx.translate(mp.x, mp.y); ctx.rotate(mp.rot);
                    ctx.beginPath();
                    for (let i = 0; i < 5; i++) {
                        ctx.lineTo(0, -15); ctx.translate(0, -15); ctx.rotate((Math.PI * 2) / 10);
                        ctx.lineTo(0, 15 / 2); ctx.translate(0, 15 / 2); ctx.rotate((Math.PI * 2) / 10);
                    }
                    ctx.lineTo(0, -15);
                    ctx.fillStyle = "#FFFF00"; ctx.fill(); ctx.strokeStyle = "#FF4500"; ctx.lineWidth = 2; ctx.stroke();
                    ctx.restore();
                });

                allStars.forEach(s => {
                    if(s.dead) return;
                    ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2); ctx.fillStyle = s.color;
                    if(s.invulnTimer > 0) { ctx.globalAlpha = 0.5 + Math.sin(performance.now()/50)*0.5; }
                    ctx.shadowColor = s.color; ctx.shadowBlur = s === player ? 25 : 15; ctx.fill(); ctx.shadowBlur = 0; ctx.globalAlpha = 1.0;
                    
                    if(s.shields > 0) { ctx.beginPath(); ctx.arc(s.x, s.y, s.r + 5, 0, Math.PI * 2); ctx.strokeStyle = "#00FFFF"; ctx.lineWidth = 3; ctx.stroke(); }
                    
                    if(s.r > LARGE_THRESHOLD) {
                        ctx.fillStyle = "#333"; ctx.fillRect(s.x - s.r, s.y - s.r - 15, s.r*2, 6);
                        ctx.fillStyle = "#33FF33"; ctx.fillRect(s.x - s.r, s.y - s.r - 15, (s.r*2) * (s.hp/s.maxHp), 6);
                    }
                    ctx.fillStyle = "white"; ctx.font = "14px sans-serif"; ctx.textAlign = "center";
                    ctx.fillText(s === player ? `${s.name} (${s.kills} Kills)` : s.name, s.x, s.y + s.r + 20);
                });

                lasers.forEach(l => { ctx.beginPath(); ctx.arc(l.x, l.y, l.size, 0, Math.PI * 2); ctx.fillStyle = l.owner.color || "#FFF"; ctx.fill(); });
                particles.forEach(p => { ctx.beginPath(); ctx.arc(p.x, p.y, 3, 0, Math.PI * 2); ctx.fillStyle = p.color; ctx.globalAlpha = p.life / 20; ctx.fill(); ctx.globalAlpha = 1.0; });
                floatingTexts.forEach(ft => { ctx.fillStyle = ft.color; ctx.font = "bold 16px sans-serif"; ctx.globalAlpha = ft.life / 30; ctx.fillText(ft.text, ft.x, ft.y); ctx.globalAlpha = 1.0; });

                ctx.restore();

                // UI Fija
                ctx.fillStyle = "rgba(0, 0, 0, 0.7)"; ctx.fillRect(10, canvas.height - 60, 220, 50);
                ctx.fillStyle = "#00FFFF"; ctx.font = "bold 16px sans-serif"; ctx.textAlign = "left";
                ctx.fillText(`VIDAS: ${playerLives}`, 20, canvas.height - 30);
                
                let cdPct = 1 - (dashTimer / dashCooldown);
                ctx.fillStyle = "#444"; ctx.fillRect(100, canvas.height - 40, 100, 10);
                ctx.fillStyle = cdPct >= 1 ? "#00FFFF" : "#FF8800"; ctx.fillRect(100, canvas.height - 40, 100 * cdPct, 10);
                ctx.fillStyle = "white"; ctx.font = "10px sans-serif"; ctx.fillText("DASH (Click Der)", 100, canvas.height - 45);

                ctx.strokeStyle = "rgba(0, 255, 255, 0.2)"; ctx.lineWidth = 1;
                ctx.beginPath(); ctx.moveTo(screenMouseX - 10, screenMouseY); ctx.lineTo(screenMouseX + 10, screenMouseY); ctx.stroke();
                ctx.beginPath(); ctx.moveTo(screenMouseX, screenMouseY - 10); ctx.lineTo(screenMouseX, screenMouseY + 10); ctx.stroke();
            }

            function loop() { update(); draw(); requestAnimationFrame(loop); }
            init(); loop();
        </script>
    </body>
    </html>
    """

    codigo_juego = codigo_juego_template.replace("__NICKNAME__", st.session_state.nickname)
    codigo_juego = codigo_juego.replace("__AUDIO_SRC__", audio_src)
    codigo_juego = codigo_juego.replace("__SFX_DATA__", sfx_json)

    components.html(codigo_juego, height=700, scrolling=False)
