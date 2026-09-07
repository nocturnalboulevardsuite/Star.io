import streamlit as st
import streamlit.components.v1 as components

# Configuración de página
st.set_page_config(page_title="Star.io - Boss Agujero Negro", layout="wide")

st.title("🌟 Star.io - ¡Combate contra el Agujero Negro!")
st.write("¡Detén al Agujero Negro antes de que devore todo el mapa! Usa [ESPACIO] para disparar láseres.")

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
        💡 **CONTROLES Y MECÁNICAS:**
        - **🕳️ AGUJERO NEGRO (JEFE):** Crece sin parar. ¡Reduce su vida antes de que devore el mapa!
        - **🔫 DISPARAR LÁSER:** Presiona **[ESPACIO]** para disparar hacia el ratón. *(Consume tu masa/tamaño)*.
        - **⚡ DASH:** Haz **Click Derecho** para impulsarte (Cooldown: 5s).
        - **🌑 METEORO LUNAR:** Meteoro gigante con hoyitos en órbita. ¡Chocarlo causa explosión!
        - **👑 REGLA DE GIGANTES:** Si miden ≥ 50, solo ganan tamaño comiendo Top 10.
        """)

else:
    st.button("⏹️ Volver al Menú / Reiniciar", on_click=volver_menu)
    
    codigo_juego = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { margin: 0; overflow: hidden; background-color: #050508; display: flex; justify-content: center; user-select: none; }
            canvas { background-color: #101018; cursor: crosshair; border-radius: 8px; }
            #gameover { display: none; position: absolute; color: white; font-family: sans-serif; top: 40%; text-align: center; font-size: 24px; text-shadow: 2px 2px 8px #000; }
        </style>
    </head>
    <body>
        <canvas id="gameCanvas" width="900" height="600"></canvas>
        <div id="gameover">
            <h2>¡Has muerto! 💥</h2>
            <p>Estás en modo espectador (siguiendo al líder).</p>
            <p style="font-size: 16px; color:#aaa;">Usa el botón de arriba para reiniciar.</p>
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

            // METEORO LUNAR
            let meteor = {
                orbitAngle: 0,
                orbitRadius: 450,
                x: worldW / 2,
                y: worldH / 2,
                r: 100,
                angle: 0,
                craters: [
                    {x: -35, y: -25, r: 20}, {x: 35, y: -35, r: 16},
                    {x: 10, y: 30, r: 25}, {x: -40, y: 25, r: 14},
                    {x: 45, y: 20, r: 15}, {x: 0, y: 0, r: 18}
                ]
            };

            // AGUJERO NEGRO (JEFE FINAL)
            let blackHole = {
                x: worldW * 0.7,
                y: worldH * 0.3,
                r: 75,
                hp: 1200,
                maxHp: 1200,
                angle: 0,
                dead: false
            };

            canvas.addEventListener('mousemove', (e) => {
                const rect = canvas.getBoundingClientRect();
                screenMouseX = e.clientX - rect.left;
                screenMouseY = e.clientY - rect.top;
            });

            canvas.addEventListener('mousedown', (e) => {
                if(e.button === 2) { 
                    e.preventDefault();
                    triggerDash();
                }
            });

            window.addEventListener('keydown', (e) => {
                if(e.code === 'Space') {
                    e.preventDefault();
                    shootLaser();
                }
            });

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

                let speed = 14;
                lasers.push({
                    x: player.x,
                    y: player.y,
                    vx: (dx / dist) * speed,
                    vy: (dy / dist) * speed,
                    life: 70
                });

                // Cuesta masa al jugador
                player.r = Math.max(10, player.r - 0.7);
            }

            const nombres = ["Alpha", "Nova", "Sirius", "Vega", "Orion", "Cosmos", "Apollo", "Zeta", "Pulsar", "Quasar", 
                             "Rigel", "Lyra", "Draco", "Cygnus", "Pegasus", "Phoenix", "Astro", "Cometa", "Titan", "Atlas"];
            const colors = ['#FF3366', '#33CCFF', '#FF9933', '#33FF66', '#CC33FF', '#FFFF33', '#FF3333', '#33FFCC'];

            function randomName() { return nombres[Math.floor(Math.random() * nombres.length)]; }
            function randomColor() { return colors[Math.floor(Math.random() * colors.length)]; }

            function drawStar(x, y, radius, color, isLarge) {
                ctx.save();
                ctx.beginPath();
                ctx.translate(x, y);
                for (let i = 0; i < 5; i++) {
                    ctx.lineTo(0, -radius);
                    ctx.translate(0, -radius);
                    ctx.rotate((Math.PI * 2) / 10);
                    ctx.lineTo(0, radius / 2);
                    ctx.translate(0, radius / 2);
                    ctx.rotate((Math.PI * 2) / 10);
                }
                ctx.lineTo(0, -radius);
                ctx.fillStyle = color;
                ctx.fill();
                ctx.lineWidth = Math.max(2, radius * 0.08);
                ctx.strokeStyle = isLarge ? "#FFD700" : "rgba(0,0,0,0.3)";
                ctx.stroke();
                ctx.closePath();
                ctx.restore();
            }

            function drawMeteor() {
                ctx.save();
                ctx.translate(meteor.x, meteor.y);
                ctx.rotate(meteor.angle);
                ctx.beginPath();
                ctx.arc(0, 0, meteor.r, 0, Math.PI * 2);
                ctx.fillStyle = "#A9A9A9";
                ctx.fill();
                ctx.lineWidth = 8;
                ctx.strokeStyle = "#555555";
                ctx.stroke();

                meteor.craters.forEach(c => {
                    ctx.beginPath();
                    ctx.arc(c.x, c.y, c.r, 0, Math.PI * 2);
                    ctx.fillStyle = "#696969";
                    ctx.fill();
                    ctx.lineWidth = 3;
                    ctx.strokeStyle = "#404040";
                    ctx.stroke();
                });
                ctx.restore();
            }

            function drawBlackHole() {
                if(blackHole.dead) return;
                ctx.save();
                ctx.translate(blackHole.x, blackHole.y);

                // Disco de acreción (aura externa)
                let grad = ctx.createRadialGradient(0, 0, blackHole.r * 0.4, 0, 0, blackHole.r * 1.5);
                grad.addColorStop(0, "#000000");
                grad.addColorStop(0.5, "#8A2BE2");
                grad.addColorStop(1, "rgba(255, 0, 128, 0)");

                ctx.beginPath();
                ctx.arc(0, 0, blackHole.r * 1.5, 0, Math.PI * 2);
                ctx.fillStyle = grad;
                ctx.fill();

                // Centro del Agujero Negro
                ctx.beginPath();
                ctx.arc(0, 0, blackHole.r, 0, Math.PI * 2);
                ctx.fillStyle = "#05000A";
                ctx.fill();
                ctx.lineWidth = 5;
                ctx.strokeStyle = "#DA70D6";
                ctx.stroke();

                ctx.restore();
            }

            let player, bots, foods;
            const maxBots = 28;
            const maxFoods = 600;

            function init() {
                isGameOver = false;
                overScreen.style.display = 'none';
                floatingTexts = [];
                lasers = [];
                
                player = { 
                    x: Math.random() * worldW, 
                    y: Math.random() * worldH, 
                    r: 16, 
                    color: '#FFFFFF', 
                    name: "TÚ",
                    speed: 3.5,
                    dead: false
                };
                
                bots = [];
                for(let i=0; i<maxBots; i++) spawnBot();

                foods = [];
                for(let i=0; i<maxFoods; i++) spawnFood();
                
                loop();
            }

            function spawnBot() {
                bots.push({
                    x: Math.random() * worldW,
                    y: Math.random() * worldH,
                    r: Math.random() * 20 + 10,
                    color: randomColor(),
                    name: randomName(),
                    vx: (Math.random() - 0.5) * 4,
                    vy: (Math.random() - 0.5) * 4,
                    dashTimer: 0,
                    dead: false
                });
            }

            function spawnFood() {
                foods.push({
                    x: Math.random() * worldW,
                    y: Math.random() * worldH,
                    r: 3.5,
                    color: randomColor()
                });
            }

            function update() {
                // Actualizar Meteoro
                meteor.orbitAngle += 0.0012;
                meteor.angle += 0.003;
                meteor.x = (worldW / 2) + Math.cos(meteor.orbitAngle) * meteor.orbitRadius;
                meteor.y = (worldH / 2) + Math.sin(meteor.orbitAngle) * meteor.orbitRadius;

                // Actualizar Agujero Negro (Crecimiento continuo)
                if(!blackHole.dead) {
                    blackHole.r += 0.012; 
                    blackHole.hp = Math.min(blackHole.maxHp, blackHole.hp + 0.1);
                }

                let allStars = [player, ...bots].filter(s => !s.dead);
                allStars.sort((a, b) => b.r - a.r);
                let top10 = allStars.slice(0, 10);

                // Movimiento Jugador
                if(!player.dead) {
                    let targetX = (screenMouseX - canvas.width / 2) / zoom + camX + canvas.width / 2;
                    let targetY = (screenMouseY - canvas.height / 2) / zoom + camY + canvas.height / 2;

                    let dx = targetX - player.x;
                    let dy = targetY - player.y;
                    let dist = Math.sqrt(dx*dx + dy*dy);
                    let baseSpeed = player.speed * Math.max(0.35, 20 / (player.r + 5));
                    
                    if (dashTimer > 0) {
                        baseSpeed *= 3.8; 
                        dashTimer--;
                    }

                    if (dist > 5) {
                        player.x += (dx / dist) * baseSpeed;
                        player.y += (dy / dist) * baseSpeed;
                    }
                    
                    player.x = Math.max(player.r, Math.min(worldW - player.r, player.x));
                    player.y = Math.max(player.r, Math.min(worldH - player.r, player.y));
                }

                // Cámara
                let focusTarget = (!player.dead) ? player : (allStars[0] || {x: worldW/2, y: worldH/2, r: 15});
                let targetZoom = Math.max(0.25, 25 / Math.max(25, focusTarget.r * 0.6));
                zoom += (targetZoom - zoom) * 0.05;

                camX += (focusTarget.x - canvas.width / 2 - camX) * 0.1;
                camY += (focusTarget.y - canvas.height / 2 - camY) * 0.1;

                // Actualizar Lasers
                for(let i = lasers.length - 1; i >= 0; i--) {
                    let l = lasers[i];
                    l.x += l.vx;
                    l.y += l.vy;
                    l.life--;

                    // Impacto Láser vs Agujero Negro
                    if(!blackHole.dead) {
                        let distBH = Math.hypot(l.x - blackHole.x, l.y - blackHole.y);
                        if(distBH < blackHole.r) {
                            blackHole.hp -= 18;
                            blackHole.r = Math.max(25, blackHole.r - 0.25);
                            lasers.splice(i, 1);

                            floatingTexts.push({
                                x: blackHole.x + (Math.random()-0.5)*30,
                                y: blackHole.y + (Math.random()-0.5)*30,
                                text: "-18 HP", color: "#FF00FF", life: 25
                            });

                            if(blackHole.hp <= 0) {
                                blackHole.dead = true;
                                floatingTexts.push({
                                    x: blackHole.x, y: blackHole.y,
                                    text: "💥 ¡AGUJERO NEGRO DESTRUIDO!", color: "#00FFCC", life: 80
                                });
                            }
                            continue;
                        }
                    }

                    if(l.life <= 0 || l.x < 0 || l.x > worldW || l.y < 0 || l.y > worldH) {
                        lasers.splice(i, 1);
                    }
                }

                // Movimiento Bots
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
                });

                // Colisión con Meteoro
                allStars.forEach(s => {
                    if(Math.hypot(s.x - meteor.x, s.y - meteor.y) < s.r + meteor.r * 0.85) {
                        s.dead = true;
                        floatingTexts.push({
                            x: s.x, y: s.y - s.r - 10,
                            text: "💥 ¡EXPLOSIÓN METEÓRICA!", color: "#FF4500", life: 50
                        });
                    }
                });

                // Colisión con Agujero Negro
                if(!blackHole.dead) {
                    allStars.forEach(s => {
                        let d = Math.hypot(s.x - blackHole.x, s.y - blackHole.y);
                        if(d < s.r + blackHole.r * 0.8) {
                            if(s.r > blackHole.r * 1.25) {
                                blackHole.dead = true;
                                s.r += 35;
                                floatingTexts.push({
                                    x: s.x, y: s.y - s.r - 10,
                                    text: "🌌 ¡DEVORASTE EL AGUJERO NEGRO!", color: "#9900FF", life: 70
                                });
                            } else {
                                s.dead = true;
                                blackHole.r += s.r * 0.15;
                                blackHole.hp = Math.min(blackHole.maxHp, blackHole.hp + 60);
                                floatingTexts.push({
                                    x: blackHole.x, y: blackHole.y - blackHole.r - 10,
                                    text: "🕳️ ¡ESTRELLA DEVORADA!", color: "#8A2BE2", life: 40
                                });
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
                            foods.splice(i, 1);
                            spawnFood();
                            break;
                        }
                    }
                }

                // Estrella vs Estrella
                for(let i = 0; i < allStars.length; i++) {
                    for(let j = i + 1; j < allStars.length; j++) {
                        let e1 = allStars[i];
                        let e2 = allStars[j];
                        if(e1.dead || e2.dead) continue;

                        let d = Math.hypot(e1.x - e2.x, e1.y - e2.y);
                        let bigger = e1.r > e2.r ? e1 : e2;
                        let smaller = e1.r > e2.r ? e2 : e1;

                        if(d < bigger.r * 0.75 && bigger.r > smaller.r * 1.15) {
                            if (bigger.r >= LARGE_THRESHOLD) {
                                if (top10.includes(smaller)) {
                                    bigger.r += smaller.r * 0.35;
                                    smaller.dead = true;
                                } else {
                                    let loss = Math.max(6, smaller.r * 0.5);
                                    bigger.r = Math.max(15, bigger.r - loss);
                                    smaller.dead = true;
                                }
                            } else {
                                bigger.r += smaller.r * 0.35;
                                smaller.dead = true;
                            }
                        }
                    }
                }

                // Textos
                for(let i = floatingTexts.length - 1; i >= 0; i--) {
                    let ft = floatingTexts[i];
                    ft.y -= 0.8;
                    ft.life--;
                    if(ft.life <= 0) floatingTexts.splice(i, 1);
                }

                if(player.dead && !isGameOver) {
                    isGameOver = true;
                    overScreen.style.display = 'block';
                }
                
                bots = bots.filter(b => !b.dead);
                while(bots.length < maxBots) spawnBot();
            }

            function drawGrid() {
                ctx.strokeStyle = "#1a1a28";
                ctx.lineWidth = 1.5;
                let gridSize = 120;
                ctx.beginPath();
                for(let x = 0; x <= worldW; x += gridSize) {
                    ctx.moveTo(x, 0); ctx.lineTo(x, worldH);
                }
                for(let y = 0; y <= worldH; y += gridSize) {
                    ctx.moveTo(0, y); ctx.lineTo(worldW, y);
                }
                ctx.stroke();
            }

            function drawBossBar() {
                if(blackHole.dead) return;
                ctx.save();
                let w = 380;
                let h = 20;
                let x = (canvas.width - w) / 2;
                let y = canvas.height - 35;

                ctx.fillStyle = "rgba(10, 5, 20, 0.85)";
                ctx.strokeStyle = "#9900FF";
                ctx.lineWidth = 2;
                ctx.fillRect(x, y, w, h);
                ctx.strokeRect(x, y, w, h);

                let pct = Math.max(0, blackHole.hp / blackHole.maxHp);
                ctx.fillStyle = "#A020F0";
                ctx.fillRect(x + 2, y + 2, (w - 4) * pct, h - 4);

                ctx.fillStyle = "#FFFFFF";
                ctx.font = "bold 11px sans-serif";
                ctx.textAlign = "center";
                ctx.fillText(`🕳️ JEFE FINAL: AGUJERO NEGRO (${Math.ceil(blackHole.hp)} / ${blackHole.maxHp} HP)`, canvas.width / 2, y + 14);
                ctx.restore();
            }

            function drawLeaderboard() {
                let allStars = [player, ...bots].filter(s => !s.dead);
                allStars.sort((a, b) => b.r - a.r);
                let top10 = allStars.slice(0, 10);

                ctx.save();
                ctx.fillStyle = "rgba(10, 10, 20, 0.8)";
                ctx.strokeStyle = "rgba(255, 255, 255, 0.1)";
                let h = 40 + (top10.length * 22);
                ctx.fillRect(12, 12, 200, h);

                ctx.fillStyle = "#FFD700";
                ctx.font = "bold 13px sans-serif";
                ctx.textAlign = "center";
                ctx.fillText("🏆 TOP 10 ESTRELLAS", 112, 30);

                ctx.textAlign = "left";
                ctx.font = "11px sans-serif";
                for(let i=0; i<top10.length; i++) {
                    let s = top10[i];
                    let yPos = 52 + (i * 22);
                    ctx.fillStyle = s.color;
                    ctx.beginPath();
                    ctx.arc(24, yPos - 4, 4, 0, Math.PI*2);
                    ctx.fill();

                    let isGigante = s.r >= LARGE_THRESHOLD;
                    ctx.fillStyle = s.name === "TÚ" ? "#FFD700" : (isGigante ? "#FFA500" : "white");
                    ctx.fillText(`${i+1}. ${s.name} (${Math.floor(s.r)})${isGigante ? ' 👑' : ''}`, 35, yPos);
                }
                ctx.restore();
            }

            function drawDashUI() {
                ctx.save();
                const elapsed = Date.now() - lastDashTime;
                const ready = elapsed >= dashCooldown;
                let x = canvas.width - 185;
                let y = canvas.height - 45;

                ctx.fillStyle = "rgba(10, 10, 20, 0.8)";
                ctx.fillRect(x, y, 170, 32);

                ctx.fillStyle = ready ? "#00FFCC" : "#444";
                ctx.fillRect(x + 5, y + 22, 160 * Math.min(1, elapsed / dashCooldown), 5);

                ctx.fillStyle = ready ? "#00FFCC" : "#AAA";
                ctx.font = "bold 11px sans-serif";
                ctx.textAlign = "center";
                ctx.fillText(ready ? "⚡ DASH LISTO (R-Click)" : `⚡ DASH: ${(5 - elapsed/1000).toFixed(1)}s`, x + 85, y + 15);
                ctx.restore();
            }

            function draw() {
                ctx.fillStyle = "#0a0a12";
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                
                ctx.save();
                ctx.translate(canvas.width / 2, canvas.height / 2);
                ctx.scale(zoom, zoom);
                ctx.translate(-camX - canvas.width / 2, -camY - canvas.height / 2);
                
                ctx.strokeStyle = "#FF3366";
                ctx.lineWidth = 6;
                ctx.strokeRect(0, 0, worldW, worldH);
                
                drawGrid();
                drawMeteor();
                drawBlackHole();

                // Dibujar Láseres
                lasers.forEach(l => {
                    ctx.save();
                    ctx.beginPath();
                    ctx.arc(l.x, l.y, 5, 0, Math.PI * 2);
                    ctx.fillStyle = "#00FFFF";
                    ctx.shadowColor = "#00FFFF";
                    ctx.shadowBlur = 8;
                    ctx.fill();
                    ctx.restore();
                });

                // Comida
                foods.forEach(f => {
                    ctx.beginPath();
                    ctx.arc(f.x, f.y, f.r, 0, Math.PI * 2);
                    ctx.fillStyle = f.color;
                    ctx.fill();
                });

                // Estrellas
                let allStars = [player, ...bots].filter(s => !s.dead);
                allStars.sort((a, b) => a.r - b.r); 

                allStars.forEach(s => {
                    drawStar(s.x, s.y, s.r, s.color, s.r >= LARGE_THRESHOLD);
                    ctx.fillStyle = "white";
                    ctx.font = "bold 12px sans-serif";
                    ctx.textAlign = "center";
                    ctx.fillText(s.name + (s.r >= LARGE_THRESHOLD ? " 👑" : ""), s.x, s.y + s.r + 15);
                });

                floatingTexts.forEach(ft => {
                    ctx.fillStyle = ft.color;
                    ctx.font = "bold 14px sans-serif";
                    ctx.textAlign = "center";
                    ctx.fillText(ft.text, ft.x, ft.y);
                });

                ctx.restore();

                drawLeaderboard();
                drawDashUI();
                drawBossBar();
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
