import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Star.io - Mejoras de Vida y Fuego", layout="wide")

st.title("🌟 Star.io - Vida Escalable y Aura de Fuego")
st.write("¡Hazte más grande para resistir daño, quema a tus enemigos y supera tus límites de salud!")

if 'jugando' not in st.session_state:
    st.session_state.jugando = False

def iniciar_juego():
    st.session_state.jugando = True

def volver_menu():
    st.session_state.jugando = False

if not st.session_state.jugando:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.button("▶️ JUGAR AHORA", on_click=iniciar_juego, type="primary", use_container_width=True)
        st.info("""
        💡 **ÚLTIMOS CAMBIOS:**
        - **🛡️ TAMAÑO = DEFENSA:** Mientras más grande seas, menos daño recibirás de los ataques.
        - **❤️ VIDA BASE 200:** Comienzas con 200 HP. ¡Agarrar vida cuando estás al máximo aumenta tu límite!
        - **🔥 AURA QUEMANTE:** El poder de fuego de la caja misteriosa ahora hace 40 de daño por toque a los enemigos.
        - **💥 NÚMEROS GIGANTES:** Los indicadores de daño y curación son mucho más visibles.
        """)

else:
    st.button("⏹️ Volver al Menú Principal", on_click=volver_menu)
    
    codigo_juego = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { margin: 0; overflow: hidden; background-color: #050508; display: flex; justify-content: center; user-select: none; font-family: sans-serif; }
            canvas { background-color: #080812; cursor: crosshair; border-radius: 8px; }
            
            #gameover { 
                display: none; position: absolute; color: white; top: 40%; text-align: center; 
                font-size: 24px; text-shadow: 2px 2px 10px #000; pointer-events: none; z-index: 5;
            }
            
            #orb-modal {
                display: none; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
                background: rgba(10, 10, 25, 0.95); padding: 30px; border-radius: 12px; border: 3px solid white;
                text-align: center; z-index: 10; box-shadow: 0px 0px 30px rgba(0, 255, 255, 0.4);
            }
            .orb-btn {
                width: 140px; height: 140px; background: #151525; color: white; border: 2px solid #555;
                border-radius: 10px; font-size: 16px; font-weight: bold; cursor: pointer; transition: 0.2s;
                display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 10px;
            }
            .orb-btn:hover { background: #2a2a40; transform: scale(1.05); }
        </style>
    </head>
    <body>
        <canvas id="gameCanvas" width="900" height="600"></canvas>
        
        <div id="gameover">
            <h2>¡HAS MUERTO! 💥</h2>
            <p style="font-size: 22px; color: #00FFFF; font-weight: bold; margin-top: 10px;">
                👉 DALE CLICK A LA PANTALLA PARA REAPARECER 👈
            </p>
        </div>

        <div id="orb-modal">
            <h2 id="orb-title" style="margin-top:0;">NUEVA MEJORA</h2>
            <p style="color:#DDD; margin-bottom:20px;">Elige una habilidad para tus láseres:</p>
            <div style="display:flex; gap:20px; justify-content:center;">
                <button id="orb-btn1" class="orb-btn"></button>
                <button id="orb-btn2" class="orb-btn"></button>
            </div>
        </div>

        <script>
            const canvas = document.getElementById("gameCanvas");
            const ctx = canvas.getContext("2d");
            const overScreen = document.getElementById("gameover");
            
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

            let lastDashTime = 0;
            const dashCooldown = 5000; 
            let dashTimer = 0; 

            let floatingTexts = [];
            let lasers = [];
            let particles = [];
            let boxes = [];
            let hearts = [];
            let orbs = [];

            let bgStarsLayer1 = [];
            let bgStarsLayer2 = [];
            for(let i=0; i<120; i++) {
                bgStarsLayer1.push({x: Math.random() * canvas.width, y: Math.random() * canvas.height, r: Math.random() * 1.5 + 0.5});
                bgStarsLayer2.push({x: Math.random() * canvas.width, y: Math.random() * canvas.height, r: Math.random() * 2.5 + 1.0});
            }

            let meteor = {
                orbitAngle: 0, orbitRadius: 450, x: worldW / 2, y: worldH / 2, r: 100, angle: 0,
                craters: [ {x: -35, y: -25, r: 20}, {x: 35, y: -35, r: 16}, {x: 10, y: 30, r: 25}, {x: -40, y: 25, r: 14}, {x: 0, y: 0, r: 18} ]
            };

            let blackHole = { x: worldW * 0.7, y: worldH * 0.3, r: 75, hp: 1200, maxHp: 1200, dead: false };

            canvas.addEventListener('mousemove', (e) => {
                const rect = canvas.getBoundingClientRect();
                screenMouseX = e.clientX - rect.left;
                screenMouseY = e.clientY - rect.top;
            });

            canvas.addEventListener('mousedown', (e) => {
                if(isPaused) return;
                if(player.dead) { respawnPlayer(); return; }
                if(e.button === 0) shootLaser();
                else if(e.button === 2) { e.preventDefault(); triggerDash(); }
            });

            window.addEventListener('keydown', (e) => {
                if(isPaused) return;
                if(e.code === 'Space') {
                    e.preventDefault();
                    if(player.dead) respawnPlayer();
                    else triggerInvulnerability();
                }
            });

            function respawnPlayer() {
                player.x = Math.random() * (worldW - 200) + 100;
                player.y = Math.random() * (worldH - 200) + 100;
                player.r = 18;
                player.hp = 200;
                player.maxHp = 200;
                player.shields = 0;
                player.dead = false;
                player.invulnTimer = 0;
                player.fireTimer = 0;
                player.speedBoostTimer = 0;
                player.hasInvulnCharge = false;
                
                player.laserRange = 1.0;
                player.laserDamage = 1.0;
                player.shotType = 'normal';
                
                isGameOver = false;
                overScreen.style.display = 'none';

                floatingTexts.push({ x: player.x, y: player.y - 30, text: "✨ ¡REAPARECISTE!", color: "#33FF66", life: 50, size: 18 });
            }

            function triggerInvulnerability() {
                if(!player.dead && player.hasInvulnCharge && player.invulnTimer <= 0) {
                    player.hasInvulnCharge = false;
                    player.invulnTimer = 300; 
                    floatingTexts.push({ x: player.x, y: player.y - player.r - 25, text: "👻 ¡MODO FANTASMA ACTIVADO!", color: "#00FFFF", life: 50, size: 16 });
                }
            }

            function triggerDash() {
                const now = Date.now();
                if(!player.dead && now - lastDashTime >= dashCooldown) {
                    lastDashTime = now;
                    dashTimer = 12; 
                    floatingTexts.push({ x: player.x, y: player.y - player.r - 20, text: "⚡ DASH!", color: "#00FFFF", life: 30, size: 18 });
                }
            }

            function shootLaser() {
                if(player.dead || player.r <= 12) return;

                let targetX = (screenMouseX - canvas.width / 2) / zoom + camX + canvas.width / 2;
                let targetY = (screenMouseY - canvas.height / 2) / zoom + camY + canvas.height / 2;
                let dx = targetX - player.x;
                let dy = targetY - player.y;
                let dist = Math.hypot(dx, dy);

                if(dist === 0) return;

                let angle = Math.atan2(dy, dx);
                let speed = 15;
                let baseLife = 75 * player.laserRange;

                function fireAt(ang) {
                    lasers.push({
                        x: player.x, y: player.y,
                        vx: Math.cos(ang) * speed, vy: Math.sin(ang) * speed, 
                        life: baseLife, owner: player, color: "#00FFFF",
                        damageMult: player.laserDamage
                    });
                }

                if(player.shotType === 'normal') { fireAt(angle); } 
                else if(player.shotType === 'triple') { fireAt(angle - 0.20); fireAt(angle); fireAt(angle + 0.20); } 
                else if(player.shotType === 'cross') { fireAt(angle); fireAt(angle + Math.PI/2); fireAt(angle + Math.PI); fireAt(angle - Math.PI/2); }

                player.r = Math.max(10, player.r - 0.4);
            }

            const nombres = ["Alpha", "Nova", "Sirius", "Vega", "Orion", "Cosmos", "Apollo", "Zeta", "Pulsar", "Quasar"];
            const colors = ['#FF3366', '#33CCFF', '#FF9933', '#33FF66', '#CC33FF', '#FFFF33', '#FF3333', '#33FFCC'];

            function randomColor() { return colors[Math.floor(Math.random() * colors.length)]; }
            function randomName() { return nombres[Math.floor(Math.random() * nombres.length)]; }

            function spawnBox() { boxes.push({ x: Math.random() * (worldW - 100) + 50, y: Math.random() * (worldH - 100) + 50, r: 16 }); }
            function spawnHeart() { hearts.push({ x: Math.random() * (worldW - 100) + 50, y: Math.random() * (worldH - 100) + 50, r: 10 }); }
            function spawnOrb() { orbs.push({ x: Math.random() * (worldW - 100) + 50, y: Math.random() * (worldH - 100) + 50, r: 14, type: Math.random() < 0.5 ? 'celeste' : 'morado' }); }

            let player, bots, foods;
            const maxBots = 28;
            const maxFoods = 600;
            const maxBoxes = 5;
            const maxHearts = 35;
            const maxOrbs = 3;

            function init() {
                isGameOver = false; isPaused = false;
                orbModal.style.display = 'none'; overScreen.style.display = 'none';
                floatingTexts = []; lasers = []; particles = []; boxes = []; hearts = []; orbs = [];
                
                player = { 
                    x: Math.random() * worldW, y: Math.random() * worldH, 
                    r: 18, color: '#FFFFFF', name: "TÚ", speed: 3.5, dead: false,
                    hp: 200, maxHp: 200, shields: 0, hasInvulnCharge: false, invulnTimer: 0, fireTimer: 0, speedBoostTimer: 0,
                    laserRange: 1.0, laserDamage: 1.0, shotType: 'normal'
                };
                
                bots = []; for(let i=0; i<maxBots; i++) spawnBot();
                foods = []; for(let i=0; i<maxFoods; i++) spawnFood();
                for(let i=0; i<maxHearts; i++) spawnHeart();
                
                spawnBox(); spawnBox(); spawnOrb();
                loop();
            }

            function spawnBot() {
                bots.push({
                    x: Math.random() * worldW, y: Math.random() * worldH,
                    r: Math.random() * 20 + 10, color: randomColor(), name: randomName(),
                    vx: (Math.random() - 0.5) * 4, vy: (Math.random() - 0.5) * 4,
                    hp: 200, maxHp: 200, lastShootTime: 0, dead: false, lastBurnTime: 0
                });
            }

            function spawnFood() { foods.push({ x: Math.random() * worldW, y: Math.random() * worldH, r: 3.5, color: randomColor() }); }

            function takeDamage(target, amount) {
                if(target === player && player.invulnTimer > 0) return;

                if(target === player && player.shields > 0) {
                    player.shields--;
                    floatingTexts.push({ x: player.x, y: player.y - player.r - 20, text: "🛡️ ¡ESCUDO ABSORBIÓ DAÑO!", color: "#C0C0C0", life: 40, size: 16 });
                    return;
                }

                // Mientras más grande, menos daño recibes (Reducción de daño)
                let dmgMult = Math.max(0.25, 18 / Math.max(18, target.r));
                let realDamage = amount * dmgMult;
                
                target.hp -= realDamage;
                
                // Textos grandes para el daño
                floatingTexts.push({ x: target.x, y: target.y - target.r - 10, text: `-${Math.ceil(realDamage)}`, color: "#FF3333", life: 30, size: 24 });

                if(target === player && player.hp <= 0) {
                    player.hp = 0; player.dead = true;
                } else if(target !== player && target.hp <= 0) {
                    target.dead = true;
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
                isPaused = true; orbModal.style.display = 'block';
                orbModal.style.borderColor = type === 'celeste' ? '#00FFFF' : '#CC33FF';
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

            function update() {
                if(Math.random() < 0.003 && boxes.length < maxBoxes) spawnBox();
                if(Math.random() < 0.002 && orbs.length < maxOrbs) spawnOrb();

                meteor.orbitAngle += 0.0012; meteor.angle += 0.003;
                meteor.x = (worldW / 2) + Math.cos(meteor.orbitAngle) * meteor.orbitRadius;
                meteor.y = (worldH / 2) + Math.sin(meteor.orbitAngle) * meteor.orbitRadius;

                if(!blackHole.dead) { blackHole.r += 0.012; blackHole.hp = Math.min(blackHole.maxHp, blackHole.hp + 0.1); }

                if(player.invulnTimer > 0) player.invulnTimer--;
                if(player.fireTimer > 0) player.fireTimer--;
                if(player.speedBoostTimer > 0) player.speedBoostTimer--;

                if(player.fireTimer > 0 && !player.dead) {
                    for(let i=0; i<2; i++) {
                        particles.push({
                            x: player.x + (Math.random() - 0.5) * player.r * 1.5, y: player.y + (Math.random() - 0.5) * player.r * 1.5,
                            vx: (Math.random() - 0.5) * 2, vy: -Math.random() * 3, color: Math.random() > 0.5 ? "#FF4500" : "#FFD700", life: 20
                        });
                    }
                }

                let allStars = [player, ...bots].filter(s => !s.dead);
                const now = Date.now();

                // Movimiento Jugador
                if(!player.dead) {
                    let targetX = (screenMouseX - canvas.width / 2) / zoom + camX + canvas.width / 2;
                    let targetY = (screenMouseY - canvas.height / 2) / zoom + camY + canvas.height / 2;
                    let dx = targetX - player.x, dy = targetY - player.y;
                    let dist = Math.sqrt(dx*dx + dy*dy);
                    let baseSpeed = player.speed * Math.max(0.35, 20 / (player.r + 5));

                    if (player.speedBoostTimer > 0) baseSpeed *= 1.7;
                    if (dashTimer > 0) { baseSpeed *= 3.8; dashTimer--; }

                    if (dist > 5) { player.x += (dx / dist) * baseSpeed; player.y += (dy / dist) * baseSpeed; }
                    player.x = Math.max(player.r, Math.min(worldW - player.r, player.x));
                    player.y = Math.max(player.r, Math.min(worldH - player.r, player.y));
                }

                // Bots
                bots.forEach(bot => {
                    let botSpeed = 3 * Math.max(0.35, 20 / (bot.r + 5));
                    if(Math.random() < 0.02) { bot.vx = (Math.random() - 0.5) * 4; bot.vy = (Math.random() - 0.5) * 4; }
                    bot.x += bot.vx * (botSpeed / 2); bot.y += bot.vy * (botSpeed / 2);
                    bot.x = Math.max(bot.r, Math.min(worldW - bot.r, bot.x)); bot.y = Math.max(bot.r, Math.min(worldH - bot.r, bot.y));

                    if (now - (bot.lastShootTime || 0) > 2500 && Math.random() < 0.03 && bot.r > 12) {
                        let target = !player.dead && Math.hypot(player.x - bot.x, player.y - bot.y) < 550 ? player : null;
                        if(!target) target = bots.find(b => b !== bot && !b.dead && Math.hypot(b.x - bot.x, b.y - bot.y) < 400);
                        if(target) {
                            let dx = target.x - bot.x, dy = target.y - bot.y, dist = Math.hypot(dx, dy);
                            if(dist > 0) {
                                lasers.push({ x: bot.x, y: bot.y, vx: (dx / dist) * 13, vy: (dy / dist) * 13, life: 65, owner: bot, color: "#FF6633", damageMult: 1 });
                                bot.lastShootTime = now; bot.r = Math.max(8, bot.r - 0.3);
                            }
                        }
                    }
                });

                // Cámara
                let focusTarget = (!player.dead) ? player : (allStars[0] || {x: worldW/2, y: worldH/2, r: 15});
                let targetZoom = Math.max(0.25, 25 / Math.max(25, focusTarget.r * 0.6));
                zoom += (targetZoom - zoom) * 0.05;
                camX += (focusTarget.x - canvas.width / 2 - camX) * 0.1;
                camY += (focusTarget.y - canvas.height / 2 - camY) * 0.1;

                // Colisiones Láseres
                for(let i = lasers.length - 1; i >= 0; i--) {
                    let l = lasers[i];
                    l.x += l.vx; l.y += l.vy; l.life--;
                    let hit = false;
                    let dmg = 22 * (l.damageMult || 1);

                    if(!blackHole.dead && Math.hypot(l.x - blackHole.x, l.y - blackHole.y) < blackHole.r) {
                        blackHole.hp -= dmg; blackHole.r = Math.max(25, blackHole.r - 0.25);
                        if(blackHole.hp <= 0) blackHole.dead = true;
                        hit = true;
                    }

                    if(!hit) {
                        for(let s of allStars) {
                            if(s.dead || s === l.owner) continue;
                            if(Math.hypot(l.x - s.x, l.y - s.y) < s.r) {
                                hit = true; takeDamage(s, dmg);
                                for(let k=0; k<4; k++) particles.push({ x: l.x, y: l.y, vx: (Math.random() - 0.5)*4, vy: (Math.random() - 0.5)*4, color: l.color, life: 15 });
                                break;
                            }
                        }
                    }
                    if(hit || l.life <= 0) lasers.splice(i, 1);
                }

                // Cajas y Orbes
                for(let i = orbs.length - 1; i >= 0; i--) {
                    let o = orbs[i];
                    if(!player.dead && Math.hypot(player.x - o.x, player.y - o.y) < player.r + o.r) {
                        showOrbMenu(o.type); orbs.splice(i, 1);
                    }
                }

                for(let i = boxes.length - 1; i >= 0; i--) {
                    let b = boxes[i];
                    if(!player.dead && Math.hypot(player.x - b.x, player.y - b.y) < player.r + b.r) {
                        boxes.splice(i, 1);
                        let rand = Math.random();
                        if(rand < 0.50) { 
                            player.hp += 50;
                            if(player.hp > player.maxHp) player.maxHp = player.hp; // Aumenta vida base
                            player.r += 2;
                            floatingTexts.push({x: player.x, y: player.y - player.r - 15, text: "❤️ +50 HP MAX", color: "#33FF66", life: 50, size: 22});
                        } else if(rand < 0.625) {
                            if(player.shields < 4) { player.shields++; floatingTexts.push({x: player.x, y: player.y - 30, text: "🛡️ ESCUDO +1", color: "#C0C0C0", life: 45, size: 18}); }
                        } else if(rand < 0.750) {
                            player.fireTimer = 360; floatingTexts.push({x: player.x, y: player.y - 30, text: "🔥 ¡AURA DE FUEGO!", color: "#FF4500", life: 50, size: 22});
                        } else if(rand < 0.875) {
                            player.hasInvulnCharge = true; floatingTexts.push({x: player.x, y: player.y - 30, text: "👻 ¡FANTASMA LISTO!", color: "#00FFFF", life: 55, size: 18});
                        } else {
                            player.speedBoostTimer = 300; floatingTexts.push({x: player.x, y: player.y - 30, text: "⚡ ¡VELOCIDAD!", color: "#FFFF33", life: 45, size: 18});
                        }
                    }
                }

                // Corazones (Aumentan Vida Base si estás lleno)
                for(let i = hearts.length - 1; i >= 0; i--) {
                    let h = hearts[i];
                    if(!player.dead && Math.hypot(player.x - h.x, player.y - h.y) < player.r + h.r) {
                        hearts.splice(i, 1); spawnHeart();
                        player.hp += 20;
                        if(player.hp > player.maxHp) player.maxHp = player.hp;
                        floatingTexts.push({ x: player.x, y: player.y - player.r - 15, text: "+20 HP ❤️", color: "#FF3366", life: 40, size: 18 });
                    }
                }

                allStars.forEach(s => { if(Math.hypot(s.x - meteor.x, s.y - meteor.y) < s.r + meteor.r * 0.85) takeDamage(s, 100); });
                if(!blackHole.dead) {
                    allStars.forEach(s => {
                        if(Math.hypot(s.x - blackHole.x, s.y - blackHole.y) < s.r + blackHole.r * 0.8) {
                            if(s.r > blackHole.r * 1.25) { blackHole.dead = true; s.r += 35; } else takeDamage(s, 100);
                        }
                    });
                }

                // Comer y Choques entre estrellas
                for(let i = foods.length - 1; i >= 0; i--) {
                    let f = foods[i];
                    for(let e of allStars) {
                        if(Math.hypot(e.x - f.x, e.y - f.y) < e.r) {
                            e.r += 0.08; 
                            if(e === player) {
                                player.hp += 0.2;
                                if(player.hp > player.maxHp) player.maxHp = player.hp;
                            }
                            foods.splice(i, 1); spawnFood(); break;
                        }
                    }
                }

                for(let i = 0; i < allStars.length; i++) {
                    for(let j = i + 1; j < allStars.length; j++) {
                        let e1 = allStars[i], e2 = allStars[j];
                        let d = Math.hypot(e1.x - e2.x, e1.y - e2.y);
                        
                        // 🔥 DAÑO POR AURA DE FUEGO 🔥 (40 HP por contacto)
                        if(d < e1.r + e2.r) {
                            if(e1 === player && player.fireTimer > 0 && (now - (e2.lastBurnTime || 0) > 500)) {
                                takeDamage(e2, 40); e2.lastBurnTime = now;
                                floatingTexts.push({ x: e2.x, y: e2.y, text: "🔥 -40", color: "#FF4500", life: 30, size: 24 });
                            } else if (e2 === player && player.fireTimer > 0 && (now - (e1.lastBurnTime || 0) > 500)) {
                                takeDamage(e1, 40); e1.lastBurnTime = now;
                                floatingTexts.push({ x: e1.x, y: e1.y, text: "🔥 -40", color: "#FF4500", life: 30, size: 24 });
                            }
                        }

                        let bigger = e1.r > e2.r ? e1 : e2;
                        let smaller = e1.r > e2.r ? e2 : e1;

                        if(d < bigger.r * 0.75 && bigger.r > smaller.r * 1.15) {
                            if(smaller === player && player.invulnTimer > 0) continue;
                            bigger.r += smaller.r * 0.35;
                            if(bigger === player) {
                                player.hp += 35;
                                if(player.hp > player.maxHp) player.maxHp = player.hp;
                                floatingTexts.push({ x: player.x, y: player.y - player.r - 15, text: "❤️ +35 HP", color: "#FF3366", life: 40, size: 20 });
                            } else { bigger.hp = Math.min(bigger.maxHp, bigger.hp + 35); }
                            smaller.dead = true;
                        }
                    }
                }

                for(let i = particles.length - 1; i >= 0; i--) {
                    let p = particles[i]; p.x += p.vx; p.y += p.vy; p.life--;
                    if(p.life <= 0) particles.splice(i, 1);
                }

                for(let i = floatingTexts.length - 1; i >= 0; i--) {
                    let ft = floatingTexts[i]; ft.y -= 0.8; ft.life--;
                    if(ft.life <= 0) floatingTexts.splice(i, 1);
                }

                if(player.dead && !isGameOver) { isGameOver = true; overScreen.style.display = 'block'; }
                bots = bots.filter(b => !b.dead);
                while(bots.length < maxBots) spawnBot();
            }

            function draw() {
                ctx.fillStyle = "#06060E";
                ctx.fillRect(0, 0, canvas.width, canvas.height);

                ctx.fillStyle = "rgba(255, 255, 255, 0.4)";
                bgStarsLayer1.forEach(s => {
                    let px = (s.x - camX * 0.08) % canvas.width; if (px < 0) px += canvas.width;
                    let py = (s.y - camY * 0.08) % canvas.height; if (py < 0) py += canvas.height;
                    ctx.beginPath(); ctx.arc(px, py, s.r, 0, Math.PI * 2); ctx.fill();
                });
                ctx.fillStyle = "rgba(180, 200, 255, 0.7)";
                bgStarsLayer2.forEach(s => {
                    let px = (s.x - camX * 0.2) % canvas.width; if (px < 0) px += canvas.width;
                    let py = (s.y - camY * 0.2) % canvas.height; if (py < 0) py += canvas.height;
                    ctx.beginPath(); ctx.arc(px, py, s.r, 0, Math.PI * 2); ctx.fill();
                });

                let shakeX = 0, shakeY = 0;
                if(!player.dead && player.hp <= 40 && player.hp > 0) { shakeX = (Math.random() - 0.5) * 9; shakeY = (Math.random() - 0.5) * 9; }

                ctx.save();
                ctx.translate(canvas.width / 2 + shakeX, canvas.height / 2 + shakeY);
                ctx.scale(zoom, zoom); ctx.translate(-camX - canvas.width / 2, -camY - canvas.height / 2);
                
                ctx.strokeStyle = "#FF3366"; ctx.lineWidth = 6; ctx.strokeRect(0, 0, worldW, worldH);

                ctx.save();
                ctx.translate(meteor.x, meteor.y); ctx.rotate(meteor.angle);
                ctx.beginPath(); ctx.arc(0, 0, meteor.r, 0, Math.PI * 2); ctx.fillStyle = "#A9A9A9"; ctx.fill();
                meteor.craters.forEach(c => { ctx.beginPath(); ctx.arc(c.x, c.y, c.r, 0, Math.PI * 2); ctx.fillStyle = "#696969"; ctx.fill(); });
                ctx.restore();

                if(!blackHole.dead) {
                    ctx.save(); ctx.translate(blackHole.x, blackHole.y);
                    let grad = ctx.createRadialGradient(0, 0, blackHole.r * 0.4, 0, 0, blackHole.r * 1.5);
                    grad.addColorStop(0, "#000"); grad.addColorStop(0.5, "#8A2BE2"); grad.addColorStop(1, "rgba(255, 0, 128, 0)");
                    ctx.beginPath(); ctx.arc(0, 0, blackHole.r * 1.5, 0, Math.PI * 2); ctx.fillStyle = grad; ctx.fill();
                    ctx.beginPath(); ctx.arc(0, 0, blackHole.r, 0, Math.PI * 2); ctx.fillStyle = "#05000A"; ctx.fill();
                    ctx.restore();
                }

                boxes.forEach(b => {
                    ctx.save(); ctx.translate(b.x, b.y);
                    ctx.fillStyle = "#FFD700"; ctx.strokeStyle = "#FF8C00"; ctx.lineWidth = 3;
                    ctx.fillRect(-b.r, -b.r, b.r*2, b.r*2); ctx.strokeRect(-b.r, -b.r, b.r*2, b.r*2);
                    ctx.fillStyle = "#000"; ctx.font = "bold 16px sans-serif"; ctx.textAlign = "center"; ctx.fillText("?", 0, 5); ctx.restore();
                });

                orbs.forEach(o => {
                    ctx.save(); ctx.translate(o.x, o.y);
                    ctx.beginPath(); ctx.arc(0, 0, o.r, 0, Math.PI * 2);
                    ctx.fillStyle = o.type === 'celeste' ? '#00FFFF' : '#CC33FF'; ctx.fill();
                    ctx.strokeStyle = "white"; ctx.lineWidth = 2; ctx.stroke();
                    ctx.globalAlpha = 0.5; ctx.beginPath(); ctx.arc(0, 0, o.r + Math.sin(Date.now() / 150)*4, 0, Math.PI * 2);
                    ctx.strokeStyle = o.type === 'celeste' ? '#00FFFF' : '#CC33FF'; ctx.lineWidth = 2; ctx.stroke();
                    ctx.restore();
                });

                hearts.forEach(h => { ctx.font = "16px sans-serif"; ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText("❤️", h.x, h.y); });

                particles.forEach(p => { ctx.beginPath(); ctx.arc(p.x, p.y, 3, 0, Math.PI * 2); ctx.fillStyle = p.color; ctx.fill(); });
                lasers.forEach(l => { ctx.beginPath(); ctx.arc(l.x, l.y, 5, 0, Math.PI * 2); ctx.fillStyle = l.color || "#00FFFF"; ctx.fill(); });
                foods.forEach(f => { ctx.beginPath(); ctx.arc(f.x, f.y, f.r, 0, Math.PI * 2); ctx.fillStyle = f.color; ctx.fill(); });

                let allStars = [player, ...bots].filter(s => !s.dead);
                allStars.sort((a, b) => a.r - b.r); 

                allStars.forEach(s => {
                    let isInvuln = (s === player && player.invulnTimer > 0), isFire = (s === player && player.fireTimer > 0);
                    ctx.save(); ctx.beginPath(); ctx.translate(s.x, s.y);
                    if(isInvuln) ctx.globalAlpha = 0.5;
                    let starFill = s.color;
                    if (s.r > 30) { let hue = (Date.now() / 20 + s.r * 6) % 360; starFill = `hsl(${hue}, 90%, 60%)`; }

                    for (let i = 0; i < 5; i++) {
                        ctx.lineTo(0, -s.r); ctx.translate(0, -s.r); ctx.rotate((Math.PI * 2) / 10);
                        ctx.lineTo(0, s.r / 2); ctx.translate(0, s.r / 2); ctx.rotate((Math.PI * 2) / 10);
                    }
                    ctx.lineTo(0, -s.r);
                    ctx.fillStyle = isFire ? "#FF4500" : starFill; ctx.fill();
                    ctx.lineWidth = Math.max(2, s.r * 0.08);
                    if (s.r > 45) { ctx.strokeStyle = `hsl(${(Date.now() / 10) % 360}, 100%, 75%)`; ctx.shadowColor = starFill; ctx.shadowBlur = 12; }
                    else { ctx.strokeStyle = s.r >= LARGE_THRESHOLD ? "#FFD700" : "rgba(0,0,0,0.3)"; }
                    ctx.stroke(); ctx.closePath(); ctx.restore();

                    if(s !== player) {
                        let hpP = Math.max(0, s.hp / s.maxHp);
                        ctx.fillStyle = "rgba(0,0,0,0.5)"; ctx.fillRect(s.x - 15, s.y - s.r - 12, 30, 4);
                        ctx.fillStyle = s.hp > (s.maxHp*0.5) ? "#33FF66" : (s.hp > (s.maxHp*0.2) ? "#FFFF33" : "#FF3333");
                        ctx.fillRect(s.x - 15, s.y - s.r - 12, 30 * hpP, 4);
                    }
                    ctx.fillStyle = "white"; ctx.font = "bold 12px sans-serif"; ctx.textAlign = "center";
                    ctx.fillText(s.name + (s.r >= LARGE_THRESHOLD ? " 👑" : ""), s.x, s.y + s.r + 15);
                });

                floatingTexts.forEach(ft => { 
                    ctx.fillStyle = ft.color; 
                    ctx.font = "bold " + (ft.size || 14) + "px sans-serif"; 
                    ctx.textAlign = "center"; 
                    ctx.fillText(ft.text, ft.x, ft.y); 
                });
                ctx.restore();

                // UI Principal
                ctx.save();
                let x = 12, y = canvas.height - 45;
                ctx.fillStyle = "rgba(10, 10, 20, 0.85)"; ctx.strokeStyle = "#444"; ctx.lineWidth = 2;
                ctx.fillRect(x, y, 220, 18); ctx.strokeRect(x, y, 220, 18); // Barra más ancha para 200hp

                let hpPct = Math.max(0, player.hp / player.maxHp);
                ctx.fillStyle = player.hp > (player.maxHp*0.5) ? "#33FF66" : (player.hp > (player.maxHp*0.2) ? "#FFFF33" : "#FF3333");
                ctx.fillRect(x + 2, y + 2, 216 * hpPct, 14);

                ctx.fillStyle = "#FFF"; ctx.font = "bold 11px sans-serif"; ctx.textAlign = "center";
                ctx.fillText(`SALUD: ${Math.ceil(player.hp)} / ${Math.ceil(player.maxHp)} HP`, x + 110, y + 13);

                for(let i = 0; i < 4; i++) {
                    ctx.beginPath(); ctx.arc(x + (i * 22) + 10, y - 14, 7, 0, Math.PI * 2);
                    ctx.fillStyle = i < player.shields ? "#A0A0A0" : "rgba(80, 80, 80, 0.3)"; ctx.fill();
                    ctx.strokeStyle = "#FFF"; ctx.lineWidth = 1; ctx.stroke();
                }
                
                if(player.hasInvulnCharge || player.invulnTimer > 0) {
                    ctx.fillStyle = player.invulnTimer > 0 ? "#00FFFF" : "#FFD700"; ctx.font = "bold 12px sans-serif"; ctx.textAlign = "left";
                    ctx.fillText(player.invulnTimer > 0 ? `👻 FANTASMA: ${(player.invulnTimer/60).toFixed(1)}s` : "👻 [ESPACIO]: FANTASMA LISTO", x, y - 28);
                }
                ctx.restore();
            }

            function loop() {
                if(!isPaused) update();
                draw();
                requestAnimationFrame(loop);
            }

            init();
        </script>
    </body>
    </html>
    """
    
    components.html(codigo_juego, height=620, width=920, scrolling=False)
