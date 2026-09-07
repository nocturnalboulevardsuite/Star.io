import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Star.io - Corazones & Reaparición Rápida", layout="wide")

st.title("🌟 Star.io - Corazones, Temblor Crítico y Respawn")
st.write("¡Junta corazones para sanarte, devora estrellas y reaparece al instante haciendo clic!")

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
        💡 **NUEVAS MECÁNICAS DE SALUD:**
        - **❤️ CORAZONES ROJOS:** Tócalos para curar 20 HP de salud.
        - **⭐ COMER ESTRELLAS:** Te cura 35 HP al instante.
        - **🚥 ESTADO DE SALUD:** Verde (>50 HP) ➡️ Amarillo (≤50 HP) ➡️ Rojo (≤20 HP).
        - **📳 MAREO Y TEMBLOR:** Si tu salud cae a 20 HP o menos, la pantalla temblará.
        - **🔄 REAPARICIÓN RÁPIDA:** Haz click en la pantalla al morir para volver a jugar al instante.
        """)

else:
    st.button("⏹️ Volver al Menú Principal", on_click=volver_menu)
    
    codigo_juego = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { margin: 0; overflow: hidden; background-color: #050508; display: flex; justify-content: center; user-select: none; }
            canvas { background-color: #080812; cursor: crosshair; border-radius: 8px; }
            #gameover { 
                display: none; position: absolute; color: white; font-family: sans-serif; 
                top: 40%; text-align: center; font-size: 24px; text-shadow: 2px 2px 10px #000;
                pointer-events: none;
            }
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

        <script>
            const canvas = document.getElementById("gameCanvas");
            const ctx = canvas.getContext("2d");
            const overScreen = document.getElementById("gameover");

            window.addEventListener('contextmenu', (e) => e.preventDefault());

            const worldW = 3200;
            const worldH = 3200;
            const LARGE_THRESHOLD = 50; 
            
            let camX = 0, camY = 0, zoom = 1;
            let screenMouseX = canvas.width / 2;
            let screenMouseY = canvas.height / 2;
            let isGameOver = false;

            let lastDashTime = 0;
            const dashCooldown = 5000; 
            let dashTimer = 0; 

            let floatingTexts = [];
            let lasers = [];
            let particles = [];
            let boxes = [];
            let hearts = [];

            // ESTRELLAS PARALLAX DE FONDO
            let bgStarsLayer1 = [];
            let bgStarsLayer2 = [];
            for(let i=0; i<120; i++) {
                bgStarsLayer1.push({x: Math.random() * canvas.width, y: Math.random() * canvas.height, r: Math.random() * 1.5 + 0.5});
                bgStarsLayer2.push({x: Math.random() * canvas.width, y: Math.random() * canvas.height, r: Math.random() * 2.5 + 1.0});
            }

            // METEORO LUNAR
            let meteor = {
                orbitAngle: 0, orbitRadius: 450, x: worldW / 2, y: worldH / 2, r: 100, angle: 0,
                craters: [
                    {x: -35, y: -25, r: 20}, {x: 35, y: -35, r: 16},
                    {x: 10, y: 30, r: 25}, {x: -40, y: 25, r: 14}, {x: 0, y: 0, r: 18}
                ]
            };

            // AGUJERO NEGRO (JEFE FINAL)
            let blackHole = { x: worldW * 0.7, y: worldH * 0.3, r: 75, hp: 1200, maxHp: 1200, dead: false };

            canvas.addEventListener('mousemove', (e) => {
                const rect = canvas.getBoundingClientRect();
                screenMouseX = e.clientX - rect.left;
                screenMouseY = e.clientY - rect.top;
            });

            // CONTROLES DE MOUSE (CLIC PARA REAPARECER O ACCIÓN)
            canvas.addEventListener('mousedown', (e) => {
                if(player.dead) {
                    respawnPlayer();
                    return;
                }

                if(e.button === 0) {
                    shootLaser();
                } else if(e.button === 2) { 
                    e.preventDefault();
                    triggerDash();
                }
            });

            window.addEventListener('keydown', (e) => {
                if(e.code === 'Space') {
                    e.preventDefault();
                    if(player.dead) {
                        respawnPlayer();
                    } else {
                        triggerInvulnerability();
                    }
                }
            });

            function respawnPlayer() {
                player.x = Math.random() * (worldW - 200) + 100;
                player.y = Math.random() * (worldH - 200) + 100;
                player.r = 18;
                player.hp = 100;
                player.maxHp = 100;
                player.shields = 0;
                player.dead = false;
                player.invulnTimer = 0;
                player.fireTimer = 0;
                player.speedBoostTimer = 0;
                player.hasInvulnCharge = false;
                
                isGameOver = false;
                overScreen.style.display = 'none';

                floatingTexts.push({
                    x: player.x, y: player.y - 30,
                    text: "✨ ¡REAPARECISTE!", color: "#33FF66", life: 50
                });
            }

            function triggerInvulnerability() {
                if(!player.dead && player.hasInvulnCharge && player.invulnTimer <= 0) {
                    player.hasInvulnCharge = false;
                    player.invulnTimer = 300; // 5 segundos
                    floatingTexts.push({
                        x: player.x, y: player.y - player.r - 25,
                        text: "👻 ¡MODO FANTASMA ACTIVADO!", color: "#00FFFF", life: 50
                    });
                }
            }

            function triggerDash() {
                const now = Date.now();
                if(!player.dead && now - lastDashTime >= dashCooldown) {
                    lastDashTime = now;
                    dashTimer = 12; 
                    floatingTexts.push({
                        x: player.x, y: player.y - player.r - 20,
                        text: "⚡ DASH!", color: "#00FFFF", life: 30
                    });
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

                lasers.push({
                    x: player.x, y: player.y,
                    vx: (dx / dist) * 15, vy: (dy / dist) * 15, life: 75,
                    owner: player, color: "#00FFFF"
                });

                player.r = Math.max(10, player.r - 0.4);
            }

            const nombres = ["Alpha", "Nova", "Sirius", "Vega", "Orion", "Cosmos", "Apollo", "Zeta", "Pulsar", "Quasar", "Rigel", "Lyra", "Draco", "Cygnus", "Pegasus"];
            const colors = ['#FF3366', '#33CCFF', '#FF9933', '#33FF66', '#CC33FF', '#FFFF33', '#FF3333', '#33FFCC'];

            function randomName() { return nombres[Math.floor(Math.random() * nombres.length)]; }
            function randomColor() { return colors[Math.floor(Math.random() * colors.length)]; }

            function spawnBox() {
                boxes.push({
                    x: Math.random() * (worldW - 100) + 50,
                    y: Math.random() * (worldH - 100) + 50,
                    r: 16
                });
            }

            function spawnHeart() {
                hearts.push({
                    x: Math.random() * (worldW - 100) + 50,
                    y: Math.random() * (worldH - 100) + 50,
                    r: 10
                });
            }

            let player, bots, foods;
            const maxBots = 28;
            const maxFoods = 600;
            const maxBoxes = 20;
            const maxHearts = 35;

            function init() {
                isGameOver = false;
                overScreen.style.display = 'none';
                floatingTexts = [];
                lasers = [];
                particles = [];
                boxes = [];
                hearts = [];
                
                player = { 
                    x: Math.random() * worldW, y: Math.random() * worldH, 
                    r: 18, color: '#FFFFFF', name: "TÚ", speed: 3.5, dead: false,
                    hp: 100, maxHp: 100,
                    shields: 0,
                    hasInvulnCharge: false,
                    invulnTimer: 0,
                    fireTimer: 0,
                    speedBoostTimer: 0
                };
                
                bots = [];
                for(let i=0; i<maxBots; i++) spawnBot();

                foods = [];
                for(let i=0; i<maxFoods; i++) spawnFood();

                for(let i=0; i<maxBoxes; i++) spawnBox();
                for(let i=0; i<maxHearts; i++) spawnHeart();
                
                loop();
            }

            function spawnBot() {
                let initialR = Math.random() * 20 + 10;
                bots.push({
                    x: Math.random() * worldW, y: Math.random() * worldH,
                    r: initialR, color: randomColor(), name: randomName(),
                    vx: (Math.random() - 0.5) * 4, vy: (Math.random() - 0.5) * 4,
                    hp: 100, maxHp: 100,
                    lastShootTime: 0,
                    dead: false
                });
            }

            function spawnFood() {
                foods.push({
                    x: Math.random() * worldW, y: Math.random() * worldH,
                    r: 3.5, color: randomColor()
                });
            }

            function takeDamage(target, amount) {
                if(target === player && player.invulnTimer > 0) return;

                if(target === player && player.shields > 0) {
                    player.shields--;
                    floatingTexts.push({
                        x: player.x, y: player.y - player.r - 20,
                        text: "🛡️ ¡ESCUDO ABSORBIÓ DAÑO!", color: "#C0C0C0", life: 40
                    });
                    return;
                }

                target.hp -= amount;

                if(target === player) {
                    if(player.hp <= 0) {
                        player.hp = 0;
                        player.dead = true;
                    }
                } else {
                    if(target.hp <= 0) {
                        target.dead = true;
                        floatingTexts.push({
                            x: target.x, y: target.y,
                            text: "💥 ¡DESTRUIDO!", color: "#FF3333", life: 40
                        });
                    }
                }
            }

            function update() {
                // Meteoro y Agujero Negro
                meteor.orbitAngle += 0.0012;
                meteor.angle += 0.003;
                meteor.x = (worldW / 2) + Math.cos(meteor.orbitAngle) * meteor.orbitRadius;
                meteor.y = (worldH / 2) + Math.sin(meteor.orbitAngle) * meteor.orbitRadius;

                if(!blackHole.dead) {
                    blackHole.r += 0.012; 
                    blackHole.hp = Math.min(blackHole.maxHp, blackHole.hp + 0.1);
                }

                // Timers del Jugador
                if(player.invulnTimer > 0) player.invulnTimer--;
                if(player.fireTimer > 0) player.fireTimer--;
                if(player.speedBoostTimer > 0) player.speedBoostTimer--;

                // Partículas de Fuego
                if(player.fireTimer > 0 && !player.dead) {
                    for(let i=0; i<2; i++) {
                        particles.push({
                            x: player.x + (Math.random() - 0.5) * player.r * 1.5,
                            y: player.y + (Math.random() - 0.5) * player.r * 1.5,
                            vx: (Math.random() - 0.5) * 2, vy: -Math.random() * 3,
                            color: Math.random() > 0.5 ? "#FF4500" : "#FFD700",
                            life: 20
                        });
                    }
                }

                let allStars = [player, ...bots].filter(s => !s.dead);

                // Movimiento Jugador
                if(!player.dead) {
                    let targetX = (screenMouseX - canvas.width / 2) / zoom + camX + canvas.width / 2;
                    let targetY = (screenMouseY - canvas.height / 2) / zoom + camY + canvas.height / 2;

                    let dx = targetX - player.x;
                    let dy = targetY - player.y;
                    let dist = Math.sqrt(dx*dx + dy*dy);
                    let baseSpeed = player.speed * Math.max(0.35, 20 / (player.r + 5));

                    if (player.speedBoostTimer > 0) baseSpeed *= 1.7;
                    if (dashTimer > 0) { baseSpeed *= 3.8; dashTimer--; }

                    if (dist > 5) {
                        player.x += (dx / dist) * baseSpeed;
                        player.y += (dy / dist) * baseSpeed;
                    }
                    
                    player.x = Math.max(player.r, Math.min(worldW - player.r, player.x));
                    player.y = Math.max(player.r, Math.min(worldH - player.r, player.y));
                }

                // Mover y Disparar Bots
                const now = Date.now();
                bots.forEach(bot => {
                    let botSpeed = 3 * Math.max(0.35, 20 / (bot.r + 5));
                    if(Math.random() < 0.02) {
                        bot.vx = (Math.random() - 0.5) * 4;
                        bot.vy = (Math.random() - 0.5) * 4;
                    }
                    bot.x += bot.vx * (botSpeed / 2);
                    bot.y += bot.vy * (botSpeed / 2);
                    bot.x = Math.max(bot.r, Math.min(worldW - bot.r, bot.x));
                    bot.y = Math.max(bot.r, Math.min(worldH - bot.r, bot.y));

                    if (now - (bot.lastShootTime || 0) > 2500 && Math.random() < 0.03 && bot.r > 12) {
                        let target = !player.dead && Math.hypot(player.x - bot.x, player.y - bot.y) < 550 ? player : null;
                        
                        if(!target) {
                            target = bots.find(b => b !== bot && !b.dead && Math.hypot(b.x - bot.x, b.y - bot.y) < 400);
                        }

                        if(target) {
                            let dx = target.x - bot.x;
                            let dy = target.y - bot.y;
                            let dist = Math.hypot(dx, dy);
                            if(dist > 0) {
                                lasers.push({
                                    x: bot.x, y: bot.y,
                                    vx: (dx / dist) * 13, vy: (dy / dist) * 13,
                                    life: 65, owner: bot, color: "#FF6633"
                                });
                                bot.lastShootTime = now;
                                bot.r = Math.max(8, bot.r - 0.3);
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

                    if(!blackHole.dead && Math.hypot(l.x - blackHole.x, l.y - blackHole.y) < blackHole.r) {
                        blackHole.hp -= 18;
                        blackHole.r = Math.max(25, blackHole.r - 0.25);
                        if(blackHole.hp <= 0) blackHole.dead = true;
                        hit = true;
                    }

                    if(!hit) {
                        for(let s of allStars) {
                            if(s.dead || s === l.owner) continue;
                            if(Math.hypot(l.x - s.x, l.y - s.y) < s.r) {
                                hit = true;
                                takeDamage(s, 22);

                                floatingTexts.push({
                                    x: s.x, y: s.y - s.r - 10,
                                    text: "-22 HP", color: "#FF5555", life: 25
                                });

                                for(let k=0; k<4; k++) {
                                    particles.push({
                                        x: l.x, y: l.y,
                                        vx: (Math.random() - 0.5) * 4, vy: (Math.random() - 0.5) * 4,
                                        color: l.color, life: 15
                                    });
                                }
                                break;
                            }
                        }
                    }

                    if(hit || l.life <= 0) lasers.splice(i, 1);
                }

                // Recoger Corazones (+20 HP)
                for(let i = hearts.length - 1; i >= 0; i--) {
                    let h = hearts[i];
                    if(!player.dead && Math.hypot(player.x - h.x, player.y - h.y) < player.r + h.r) {
                        hearts.splice(i, 1);
                        spawnHeart();

                        player.hp = Math.min(player.maxHp, player.hp + 20);
                        floatingTexts.push({
                            x: player.x, y: player.y - player.r - 15,
                            text: "+20 HP ❤️", color: "#FF3366", life: 40
                        });
                    }
                }

                // Colisión con Cajitas Misteriosas
                for(let i = boxes.length - 1; i >= 0; i--) {
                    let b = boxes[i];
                    if(!player.dead && Math.hypot(player.x - b.x, player.y - b.y) < player.r + b.r) {
                        boxes.splice(i, 1);
                        spawnBox();

                        let rand = Math.random();
                        if(rand < 0.25) {
                            if(player.shields < 4) {
                                player.shields++;
                                floatingTexts.push({x: player.x, y: player.y - player.r - 15, text: "🛡️ +1 ESCUDO GRIS", color: "#C0C0C0", life: 45});
                            } else {
                                player.hp = player.maxHp;
                                floatingTexts.push({x: player.x, y: player.y - player.r - 15, text: "❤️ SALUD MÁXIMA", color: "#FF3366", life: 45});
                            }
                        } else if(rand < 0.45) {
                            player.fireTimer = 360;
                            floatingTexts.push({x: player.x, y: player.y - player.r - 15, text: "🔥 ¡AURA DE FUEGO ACTIVADA!", color: "#FF4500", life: 50});
                        } else if(rand < 0.65) {
                            player.hasInvulnCharge = true;
                            floatingTexts.push({x: player.x, y: player.y - player.r - 15, text: "👻 ¡INVULNERABILIDAD LISTA! [ESPACIO]", color: "#00FFFF", life: 55});
                        } else if(rand < 0.85) {
                            player.speedBoostTimer = 300;
                            floatingTexts.push({x: player.x, y: player.y - player.r - 15, text: "⚡ ¡SUPER VELOCIDAD!", color: "#FFFF33", life: 45});
                        } else {
                            player.hp = Math.min(player.maxHp, player.hp + 40);
                            player.r += 4;
                            floatingTexts.push({x: player.x, y: player.y - player.r - 15, text: "❤️ +40 SALUD & MASA", color: "#33FF66", life: 45});
                        }
                    }
                }

                // Colisión Meteoro
                allStars.forEach(s => {
                    if(Math.hypot(s.x - meteor.x, s.y - meteor.y) < s.r + meteor.r * 0.85) {
                        takeDamage(s, 100);
                    }
                });

                // Colisión Agujero Negro
                if(!blackHole.dead) {
                    allStars.forEach(s => {
                        let d = Math.hypot(s.x - blackHole.x, s.y - blackHole.y);
                        if(d < s.r + blackHole.r * 0.8) {
                            if(s.r > blackHole.r * 1.25) {
                                blackHole.dead = true;
                                s.r += 35;
                            } else {
                                takeDamage(s, 100);
                            }
                        }
                    });
                }

                // Comer Comida
                for(let i = foods.length - 1; i >= 0; i--) {
                    let f = foods[i];
                    for(let e of allStars) {
                        if(e.dead) continue;
                        if(Math.hypot(e.x - f.x, e.y - f.y) < e.r) {
                            e.r += 0.08; 
                            if(e === player) player.hp = Math.min(player.maxHp, player.hp + 0.1);
                            foods.splice(i, 1);
                            spawnFood();
                            break;
                        }
                    }
                }

                // Estrella vs Estrella (Devorar recupera salud)
                for(let i = 0; i < allStars.length; i++) {
                    for(let j = i + 1; j < allStars.length; j++) {
                        let e1 = allStars[i];
                        let e2 = allStars[j];
                        if(e1.dead || e2.dead) continue;

                        let d = Math.hypot(e1.x - e2.x, e1.y - e2.y);
                        let bigger = e1.r > e2.r ? e1 : e2;
                        let smaller = e1.r > e2.r ? e2 : e1;

                        if(d < bigger.r * 0.75 && bigger.r > smaller.r * 1.15) {
                            if(smaller === player && player.fireTimer > 0) {
                                bigger.r = Math.max(12, bigger.r - 0.6);
                                particles.push({
                                    x: bigger.x + (Math.random()-0.5)*bigger.r,
                                    y: bigger.y + (Math.random()-0.5)*bigger.r,
                                    vx: 0, vy: -2, color: "#FF4500", life: 15
                                });
                                continue;
                            }

                            if(smaller === player && player.invulnTimer > 0) continue;

                            bigger.r += smaller.r * 0.35;
                            
                            // RECUPERAR SALUD AL DEVORAR UNA ESTRELLA
                            if(bigger === player) {
                                player.hp = Math.min(player.maxHp, player.hp + 35);
                                floatingTexts.push({
                                    x: player.x, y: player.y - player.r - 15,
                                    text: "❤️ +35 HP", color: "#FF3366", life: 40
                                });
                            } else {
                                bigger.hp = Math.min(bigger.maxHp, bigger.hp + 35);
                            }

                            smaller.dead = true;
                        }
                    }
                }

                // Limpieza
                for(let i = particles.length - 1; i >= 0; i--) {
                    let p = particles[i];
                    p.x += p.vx; p.y += p.vy; p.life--;
                    if(p.life <= 0) particles.splice(i, 1);
                }

                for(let i = floatingTexts.length - 1; i >= 0; i--) {
                    let ft = floatingTexts[i];
                    ft.y -= 0.8; ft.life--;
                    if(ft.life <= 0) floatingTexts.splice(i, 1);
                }

                if(player.dead && !isGameOver) {
                    isGameOver = true;
                    overScreen.style.display = 'block';
                }
                
                bots = bots.filter(b => !b.dead);
                while(bots.length < maxBots) spawnBot();
            }

            function drawParallaxBG() {
                ctx.fillStyle = "rgba(255, 255, 255, 0.4)";
                bgStarsLayer1.forEach(s => {
                    let px = (s.x - camX * 0.08) % canvas.width;
                    if (px < 0) px += canvas.width;
                    let py = (s.y - camY * 0.08) % canvas.height;
                    if (py < 0) py += canvas.height;
                    ctx.beginPath(); ctx.arc(px, py, s.r, 0, Math.PI * 2); ctx.fill();
                });

                ctx.fillStyle = "rgba(180, 200, 255, 0.7)";
                bgStarsLayer2.forEach(s => {
                    let px = (s.x - camX * 0.2) % canvas.width;
                    if (px < 0) px += canvas.width;
                    let py = (s.y - camY * 0.2) % canvas.height;
                    if (py < 0) py += canvas.height;
                    ctx.beginPath(); ctx.arc(px, py, s.r, 0, Math.PI * 2); ctx.fill();
                });
            }

            function drawLeaderboard() {
                ctx.save();
                let allStars = [player, ...bots].filter(s => !s.dead);
                allStars.sort((a, b) => b.r - a.r);
                let top10 = allStars.slice(0, 10);

                let x = 12;
                let y = 12;
                let w = 180;
                let h = 30 + top10.length * 18;

                ctx.fillStyle = "rgba(10, 10, 25, 0.75)";
                ctx.strokeStyle = "rgba(100, 150, 255, 0.4)";
                ctx.lineWidth = 1.5;
                ctx.fillRect(x, y, w, h);
                ctx.strokeRect(x, y, w, h);

                ctx.fillStyle = "#FFD700";
                ctx.font = "bold 12px sans-serif";
                ctx.textAlign = "left";
                ctx.fillText("🏆 TOP 10 ESTRELLAS", x + 10, y + 18);

                ctx.font = "11px sans-serif";
                top10.forEach((s, idx) => {
                    let sy = y + 38 + (idx * 18);
                    ctx.fillStyle = (s === player) ? "#00FFFF" : "rgba(255,255,255,0.85)";
                    if(s === player) ctx.font = "bold 11px sans-serif";
                    else ctx.font = "11px sans-serif";

                    let displayName = s.name.length > 9 ? s.name.substring(0, 8) + "." : s.name;
                    ctx.fillText(`${idx + 1}. ${displayName}`, x + 10, sy);
                    ctx.textAlign = "right";
                    ctx.fillText(`${Math.floor(s.r * 10)} pts`, x + w - 10, sy);
                    ctx.textAlign = "left";
                });

                ctx.restore();
            }

            function drawPlayerUI() {
                ctx.save();
                let x = 12;
                let y = canvas.height - 45;

                // BARRA DE VIDA DINÁMICA (VERDE, AMARILLA, ROJA)
                ctx.fillStyle = "rgba(10, 10, 20, 0.85)";
                ctx.strokeStyle = "#444";
                ctx.lineWidth = 2;
                ctx.fillRect(x, y, 180, 18);
                ctx.strokeRect(x, y, 180, 18);

                let hpPct = Math.max(0, player.hp / player.maxHp);

                if(player.hp > 50) {
                    ctx.fillStyle = "#33FF66"; // Verde
                } else if(player.hp > 20) {
                    ctx.fillStyle = "#FFFF33"; // Amarillo
                } else {
                    ctx.fillStyle = "#FF3333"; // Rojo
                }

                ctx.fillRect(x + 2, y + 2, 176 * hpPct, 14);

                ctx.fillStyle = "#FFF";
                ctx.font = "bold 10px sans-serif";
                ctx.textAlign = "center";
                ctx.fillText(`SALUD: ${Math.ceil(player.hp)} / ${Math.ceil(player.maxHp)} HP`, x + 90, y + 13);

                // Escudos Grises
                for(let i = 0; i < 4; i++) {
                    let sx = x + (i * 22) + 10;
                    let sy = y - 14;
                    ctx.beginPath();
                    ctx.arc(sx, sy, 7, 0, Math.PI * 2);
                    ctx.fillStyle = i < player.shields ? "#A0A0A0" : "rgba(80, 80, 80, 0.3)";
                    ctx.fill();
                    ctx.strokeStyle = "#FFF";
                    ctx.lineWidth = 1;
                    ctx.stroke();
                }

                // Indicador de Invulnerabilidad
                if(player.hasInvulnCharge || player.invulnTimer > 0) {
                    ctx.fillStyle = player.invulnTimer > 0 ? "#00FFFF" : "#FFD700";
                    ctx.font = "bold 11px sans-serif";
                    ctx.textAlign = "left";
                    let txt = player.invulnTimer > 0 ? `👻 FANTASMA: ${(player.invulnTimer/60).toFixed(1)}s` : "👻 [ESPACIO]: FANTASMA LISTO";
                    ctx.fillText(txt, x, y - 28);
                }

                ctx.restore();
            }

            function drawStar(x, y, radius, color, isLarge, isInvuln, isFire) {
                ctx.save();
                ctx.beginPath();
                ctx.translate(x, y);

                if(isInvuln) ctx.globalAlpha = 0.5;

                let starFill = color;
                if (radius > 30) {
                    let hue = (Date.now() / 20 + radius * 6) % 360;
                    starFill = `hsl(${hue}, 90%, 60%)`;
                }

                for (let i = 0; i < 5; i++) {
                    ctx.lineTo(0, -radius);
                    ctx.translate(0, -radius);
                    ctx.rotate((Math.PI * 2) / 10);
                    ctx.lineTo(0, radius / 2);
                    ctx.translate(0, radius / 2);
                    ctx.rotate((Math.PI * 2) / 10);
                }
                ctx.lineTo(0, -radius);
                
                ctx.fillStyle = isFire ? "#FF4500" : starFill;
                ctx.fill();

                ctx.lineWidth = Math.max(2, radius * 0.08);
                if (radius > 45) {
                    ctx.strokeStyle = `hsl(${(Date.now() / 10) % 360}, 100%, 75%)`;
                    ctx.shadowColor = starFill;
                    ctx.shadowBlur = 12;
                } else {
                    ctx.strokeStyle = isLarge ? "#FFD700" : "rgba(0,0,0,0.3)";
                }
                
                ctx.stroke();
                ctx.closePath();
                ctx.restore();
            }

            function drawBoxes() {
                boxes.forEach(b => {
                    ctx.save();
                    ctx.translate(b.x, b.y);
                    ctx.fillStyle = "#FFD700";
                    ctx.strokeStyle = "#FF8C00";
                    ctx.lineWidth = 3;
                    ctx.fillRect(-b.r, -b.r, b.r*2, b.r*2);
                    ctx.strokeRect(-b.r, -b.r, b.r*2, b.r*2);

                    ctx.fillStyle = "#000";
                    ctx.font = "bold 16px sans-serif";
                    ctx.textAlign = "center";
                    ctx.fillText("?", 0, 5);
                    ctx.restore();
                });
            }

            function drawHearts() {
                hearts.forEach(h => {
                    ctx.save();
                    ctx.font = "14px sans-serif";
                    ctx.textAlign = "center";
                    ctx.textBaseline = "middle";
                    ctx.fillText("❤️", h.x, h.y);
                    ctx.restore();
                });
            }

            function draw() {
                ctx.fillStyle = "#06060E";
                ctx.fillRect(0, 0, canvas.width, canvas.height);

                drawParallaxBG();
                
                // EFECTO DE TEMBLOR / MAREO SI SALUD <= 20 HP
                let shakeX = 0;
                let shakeY = 0;
                if(!player.dead && player.hp <= 20 && player.hp > 0) {
                    shakeX = (Math.random() - 0.5) * 9;
                    shakeY = (Math.random() - 0.5) * 9;
                }

                ctx.save();
                ctx.translate(canvas.width / 2 + shakeX, canvas.height / 2 + shakeY);
                ctx.scale(zoom, zoom);
                ctx.translate(-camX - canvas.width / 2, -camY - canvas.height / 2);
                
                ctx.strokeStyle = "#FF3366";
                ctx.lineWidth = 6;
                ctx.strokeRect(0, 0, worldW, worldH);

                // Meteoro y Agujero Negro
                ctx.save();
                ctx.translate(meteor.x, meteor.y);
                ctx.rotate(meteor.angle);
                ctx.beginPath();
                ctx.arc(0, 0, meteor.r, 0, Math.PI * 2);
                ctx.fillStyle = "#A9A9A9"; ctx.fill();
                meteor.craters.forEach(c => {
                    ctx.beginPath(); ctx.arc(c.x, c.y, c.r, 0, Math.PI * 2);
                    ctx.fillStyle = "#696969"; ctx.fill();
                });
                ctx.restore();

                if(!blackHole.dead) {
                    ctx.save();
                    ctx.translate(blackHole.x, blackHole.y);
                    let grad = ctx.createRadialGradient(0, 0, blackHole.r * 0.4, 0, 0, blackHole.r * 1.5);
                    grad.addColorStop(0, "#000"); grad.addColorStop(0.5, "#8A2BE2"); grad.addColorStop(1, "rgba(255, 0, 128, 0)");
                    ctx.beginPath(); ctx.arc(0, 0, blackHole.r * 1.5, 0, Math.PI * 2);
                    ctx.fillStyle = grad; ctx.fill();
                    ctx.beginPath(); ctx.arc(0, 0, blackHole.r, 0, Math.PI * 2);
                    ctx.fillStyle = "#05000A"; ctx.fill();
                    ctx.restore();
                }

                drawBoxes();
                drawHearts();

                // Partículas
                particles.forEach(p => {
                    ctx.beginPath(); ctx.arc(p.x, p.y, 3, 0, Math.PI * 2);
                    ctx.fillStyle = p.color; ctx.fill();
                });

                // Láseres
                lasers.forEach(l => {
                    ctx.beginPath(); ctx.arc(l.x, l.y, 5, 0, Math.PI * 2);
                    ctx.fillStyle = l.color || "#00FFFF"; ctx.fill();
                });

                // Comida
                foods.forEach(f => {
                    ctx.beginPath(); ctx.arc(f.x, f.y, f.r, 0, Math.PI * 2);
                    ctx.fillStyle = f.color; ctx.fill();
                });

                // Estrellas
                let allStars = [player, ...bots].filter(s => !s.dead);
                allStars.sort((a, b) => a.r - b.r); 

                allStars.forEach(s => {
                    let isInvuln = (s === player && player.invulnTimer > 0);
                    let isFire = (s === player && player.fireTimer > 0);
                    drawStar(s.x, s.y, s.r, s.color, s.r >= LARGE_THRESHOLD, isInvuln, isFire);

                    // Barra de Vida Mini para Bots
                    if(s !== player) {
                        let hpP = Math.max(0, s.hp / s.maxHp);
                        ctx.fillStyle = "rgba(0,0,0,0.5)";
                        ctx.fillRect(s.x - 15, s.y - s.r - 12, 30, 4);
                        ctx.fillStyle = s.hp > 50 ? "#33FF66" : (s.hp > 20 ? "#FFFF33" : "#FF3333");
                        ctx.fillRect(s.x - 15, s.y - s.r - 12, 30 * hpP, 4);
                    }

                    ctx.fillStyle = "white";
                    ctx.font = "bold 12px sans-serif";
                    ctx.textAlign = "center";
                    ctx.fillText(s.name + (s.r >= LARGE_THRESHOLD ? " 👑" : ""), s.x, s.y + s.r + 15);
                });

                floatingTexts.forEach(ft => {
                    ctx.fillStyle = ft.color; ctx.font = "bold 14px sans-serif";
                    ctx.textAlign = "center"; ctx.fillText(ft.text, ft.x, ft.y);
                });

                ctx.restore();

                // Interfaz Fija (UI)
                drawLeaderboard();
                drawPlayerUI();
            }

            function loop() {
                update();
                draw();
                requestAnimationFrame(loop);
            }

            init();
        </script>
    </body>
    </html>
    """
    
    components.html(codigo_juego, height=620, width=920, scrolling=False)
