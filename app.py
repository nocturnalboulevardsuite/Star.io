import streamlit as st
import streamlit.components.v1 as components

# Configuración de página
st.set_page_config(page_title="Star.io - Reglas Avanzadas", layout="wide")

st.title("🌟 Star.io - Reglas Avanzadas & Dash")
st.write("¡Mapa masivo con cámara inteligente, Dash (Click Derecho) y sistema anti-bullying para estrellas gigantes!")

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
        💡 **NUEVAS REGLAS Y CONTROLES:**
        - **⚡ DASH:** Haz **Click Derecho** para hacer un deslizamiento rápido hacia tu ratón (Cooldown: 5s).
        - **👑 ESTRELLA GIGANTE (Radio ≥ 50):** Tu estrella obtiene un borde dorado.
        - **⚠️ REGLA DE ABSORCIÓN:** Al ser gigante, **¡solo puedes comer estrellas del Top 10!**
        - **🚫 PENALIZACIÓN / DESINFLADO:** Si eres gigante y te comes una estrella pequeña fuera del Top 10, **¡TE DESINFLAS Y PIERDES TAMAÑO!**
        - **🔍 CÁMARA INTELIGENTE:** Corrección del bug de tamaño: la pantalla se aleja dinámicamente cuando creces.
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
            <h2>¡Te comieron! 💥</h2>
            <p>Estás en modo espectador (siguiendo al #1).</p>
            <p style="font-size: 16px; color:#aaa;">Usa el botón de arriba para reiniciar.</p>
        </div>

        <script>
            const canvas = document.getElementById("gameCanvas");
            const ctx = canvas.getContext("2d");
            const overScreen = document.getElementById("gameover");

            // Bloquear menú contextual de click derecho
            window.addEventListener('contextmenu', (e) => e.preventDefault());

            // Configuración del mundo
            const worldW = 3200;
            const worldH = 3200;
            const LARGE_THRESHOLD = 50; // A partir de este radio se considera "Muy Grande"
            
            // Cámara y Entrada
            let camX = 0;
            let camY = 0;
            let zoom = 1;
            let screenMouseX = canvas.width / 2;
            let screenMouseY = canvas.height / 2;
            let isGameOver = false;

            // Dash / Impulso
            let lastDashTime = 0;
            const dashCooldown = 5000; // 5 segundos
            let dashTimer = 0; // Frames de dash activo

            // Textos flotantes de penalización / aviso
            let floatingTexts = [];

            // Escuchar ratón
            canvas.addEventListener('mousemove', (e) => {
                const rect = canvas.getBoundingClientRect();
                screenMouseX = e.clientX - rect.left;
                screenMouseY = e.clientY - rect.top;
            });

            canvas.addEventListener('mousedown', (e) => {
                if(e.button === 2) { // Click derecho
                    e.preventDefault();
                    triggerDash();
                }
            });

            function triggerDash() {
                const now = Date.now();
                if(!player.dead && now - lastDashTime >= dashCooldown) {
                    lastDashTime = now;
                    dashTimer = 12; // 12 frames de impulso
                    
                    floatingTexts.push({
                        x: player.x,
                        y: player.y - player.r - 20,
                        text: "⚡ DASH!",
                        color: "#00FFFF",
                        life: 30
                    });
                }
            }

            const nombres = ["Alpha", "Nova", "Sirius", "Vega", "Orion", "Cosmos", "Apollo", "Zeta", "Pulsar", "Quasar", 
                             "Rigel", "Lyra", "Draco", "Cygnus", "Pegasus", "Phoenix", "Astro", "Cometa", "Meteor", "Nebula",
                             "Titan", "Atlas", "Galia", "Krypton", "Zenith", "Vortex", "Horizon", "Eclipse", "Aurora", "Polaris"];
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
                
                // Borde dorado si es estrella gigante
                ctx.lineWidth = Math.max(2, radius * 0.08);
                ctx.strokeStyle = isLarge ? "#FFD700" : "rgba(0,0,0,0.3)";
                ctx.stroke();
                ctx.closePath();
                ctx.restore();
            }

            let player, bots, foods;
            const maxBots = 29;
            const maxFoods = 600;

            function init() {
                isGameOver = false;
                overScreen.style.display = 'none';
                floatingTexts = [];
                
                player = { 
                    x: Math.random() * worldW, 
                    y: Math.random() * worldH, 
                    r: 15, 
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
                // Obtener Top 10 actual para la regla de estrellas grandes
                let allStars = [player, ...bots].filter(s => !s.dead);
                allStars.sort((a, b) => b.r - a.r);
                let top10 = allStars.slice(0, 10);

                // Movimiento del Jugador
                if(!player.dead) {
                    let targetX = (screenMouseX - canvas.width / 2) / zoom + camX + canvas.width / 2;
                    let targetY = (screenMouseY - canvas.height / 2) / zoom + camY + canvas.height / 2;

                    let dx = targetX - player.x;
                    let dy = targetY - player.y;
                    let dist = Math.sqrt(dx*dx + dy*dy);
                    
                    // Velocidad corregida para evitar glitches al crecer
                    let baseSpeed = player.speed * Math.max(0.35, 20 / (player.r + 5));
                    
                    if (dashTimer > 0) {
                        baseSpeed *= 3.8; // Impulso Dash
                        dashTimer--;
                    }

                    if (dist > 5) {
                        player.x += (dx / dist) * baseSpeed;
                        player.y += (dy / dist) * baseSpeed;
                    }
                    
                    player.x = Math.max(player.r, Math.min(worldW - player.r, player.x));
                    player.y = Math.max(player.r, Math.min(worldH - player.r, player.y));
                }

                // Cámara con ZOOM DINÁMICO (Soluciona el bug cuando te haces enorme)
                let focusTarget = (!player.dead) ? player : (allStars[0] || {x: worldW/2, y: worldH/2, r: 15});
                
                let targetZoom = Math.max(0.25, 25 / Math.max(25, focusTarget.r * 0.6));
                zoom += (targetZoom - zoom) * 0.05;

                camX += (focusTarget.x - canvas.width / 2 - camX) * 0.1;
                camY += (focusTarget.y - canvas.height / 2 - camY) * 0.1;

                // Mover Bots
                bots.forEach(bot => {
                    let botSpeed = 3 * Math.max(0.35, 20 / (bot.r + 5));
                    
                    if(Math.random() < 0.002 && bot.r > 25 && bot.dashTimer <= 0) {
                        bot.dashTimer = 10;
                    }

                    if(bot.dashTimer > 0) {
                        botSpeed *= 3;
                        bot.dashTimer--;
                    }

                    if(Math.random() < 0.02) {
                        bot.vx = (Math.random() - 0.5) * 4;
                        bot.vy = (Math.random() - 0.5) * 4;
                    }

                    bot.x += bot.vx * (botSpeed / 2);
                    bot.y += bot.vy * (botSpeed / 2);

                    if(bot.x - bot.r < 0 || bot.x + bot.r > worldW) bot.vx *= -1;
                    if(bot.y - bot.r < 0 || bot.y + bot.r > worldH) bot.vy *= -1;
                    
                    bot.x = Math.max(bot.r, Math.min(worldW - bot.r, bot.x));
                    bot.y = Math.max(bot.r, Math.min(worldH - bot.r, bot.y));
                });

                // Colisiones: Estrellas vs Comida
                for(let i = foods.length - 1; i >= 0; i--) {
                    let f = foods[i];
                    for(let e of allStars) {
                        let d = Math.hypot(e.x - f.x, e.y - f.y);
                        if(d < e.r) {
                            e.r += 0.08; 
                            foods.splice(i, 1);
                            spawnFood();
                            break;
                        }
                    }
                }

                // Colisiones: Estrella vs Estrella (Regla del Top 10 y Penalización)
                for(let i = 0; i < allStars.length; i++) {
                    for(let j = i + 1; j < allStars.length; j++) {
                        let e1 = allStars[i];
                        let e2 = allStars[j];
                        if(e1.dead || e2.dead) continue;

                        let d = Math.hypot(e1.x - e2.x, e1.y - e2.y);
                        let bigger = e1.r > e2.r ? e1 : e2;
                        let smaller = e1.r > e2.r ? e2 : e1;

                        if(d < bigger.r * 0.75) {
                            if(bigger.r > smaller.r * 1.15) {
                                
                                const isBiggerLarge = bigger.r >= LARGE_THRESHOLD;
                                const isSmallerInTop10 = top10.includes(smaller);

                                if (isBiggerLarge) {
                                    if (isSmallerInTop10) {
                                        // ✅ Come Top 10 -> Crece
                                        bigger.r += smaller.r * 0.35;
                                        smaller.dead = true;

                                        floatingTexts.push({
                                            x: bigger.x, y: bigger.y - bigger.r - 10,
                                            text: "👑 +TOP 10 ABSORBIDO!", color: "#00FF66", life: 40
                                        });
                                    } else {
                                        // ❌ PENALIZACIÓN: Intenta comer una estrella pequeña fuera del Top 10 -> ¡DESINFLADO!
                                        let loss = Math.max(6, smaller.r * 0.5);
                                        bigger.r = Math.max(15, bigger.r - loss);
                                        smaller.dead = true;

                                        floatingTexts.push({
                                            x: bigger.x, y: bigger.y - bigger.r - 10,
                                            text: `⚠️ ¡DESINFLADO! -${Math.floor(loss)} TAMAÑO`, color: "#FF3333", life: 45
                                        });
                                    }
                                } else {
                                    // Normal cuando aún no es gigante
                                    bigger.r += smaller.r * 0.35;
                                    smaller.dead = true;
                                }
                            }
                        }
                    }
                }

                // Textos flotantes
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

            function drawLeaderboard() {
                let allStars = [player, ...bots].filter(s => !s.dead);
                allStars.sort((a, b) => b.r - a.r);
                let top10 = allStars.slice(0, 10);

                ctx.save();
                ctx.fillStyle = "rgba(10, 10, 20, 0.8)";
                ctx.strokeStyle = "rgba(255, 255, 255, 0.1)";
                ctx.lineWidth = 1;

                let h = 40 + (top10.length * 24);
                ctx.beginPath();
                if(ctx.roundRect) ctx.roundRect(12, 12, 210, h, 8);
                else ctx.fillRect(12, 12, 210, h);
                ctx.fill();
                ctx.stroke();

                ctx.fillStyle = "#FFD700";
                ctx.font = "bold 14px sans-serif";
                ctx.textAlign = "center";
                ctx.fillText("🏆 TOP 10 ESTRELLAS", 117, 32);

                ctx.textAlign = "left";
                ctx.font = "12px sans-serif";
                for(let i=0; i<top10.length; i++) {
                    let s = top10[i];
                    let yPos = 58 + (i * 24);
                    
                    ctx.fillStyle = s.color;
                    ctx.beginPath();
                    ctx.arc(26, yPos - 4, 5, 0, Math.PI*2);
                    ctx.fill();

                    let isGigante = s.r >= LARGE_THRESHOLD;
                    ctx.fillStyle = s.name === "TÚ" ? "#FFD700" : (isGigante ? "#FFA500" : "white");
                    let text = `${i+1}. ${s.name} (${Math.floor(s.r)})${isGigante ? ' 👑' : ''}`;
                    ctx.fillText(text, 38, yPos);
                }
                ctx.restore();
            }

            function drawDashUI() {
                ctx.save();
                const now = Date.now();
                const elapsed = now - lastDashTime;
                const ready = elapsed >= dashCooldown;
                const progress = Math.min(1, elapsed / dashCooldown);

                let x = canvas.width - 185;
                let y = canvas.height - 45;

                ctx.fillStyle = "rgba(10, 10, 20, 0.8)";
                ctx.fillRect(x, y, 170, 32);

                ctx.fillStyle = ready ? "#00FFCC" : "#444";
                ctx.fillRect(x + 5, y + 22, 160 * progress, 5);

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
                
                // Aplicar Zoom y Cámara
                ctx.translate(canvas.width / 2, canvas.height / 2);
                ctx.scale(zoom, zoom);
                ctx.translate(-camX - canvas.width / 2, -camY - canvas.height / 2);
                
                // Límites del Mundo
                ctx.strokeStyle = "#FF3366";
                ctx.lineWidth = 6;
                ctx.strokeRect(0, 0, worldW, worldH);
                
                drawGrid();
                
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
                    let isLarge = s.r >= LARGE_THRESHOLD;
                    drawStar(s.x, s.y, s.r, s.color, isLarge);
                    
                    ctx.fillStyle = "white";
                    ctx.font = "bold 13px sans-serif";
                    ctx.textAlign = "center";
                    ctx.shadowColor = "black";
                    ctx.shadowBlur = 4;
                    let label = s.name + (isLarge ? " 👑" : "");
                    ctx.fillText(label, s.x, s.y + s.r + 16);
                    ctx.shadowBlur = 0;
                });

                // Textos flotantes (Penalización / Dash)
                floatingTexts.forEach(ft => {
                    ctx.fillStyle = ft.color;
                    ctx.font = "bold 15px sans-serif";
                    ctx.textAlign = "center";
                    ctx.fillText(ft.text, ft.x, ft.y);
                });

                ctx.restore();

                // UI Fija
                drawLeaderboard();
                drawDashUI();
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
