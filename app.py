import streamlit as st
import streamlit.components.v1 as components

# Ampliamos el layout para que el juego tenga más espacio
st.set_page_config(page_title="Star.io", layout="wide")

st.title("🌟 Star.io - Mundo Masivo")
st.write("¡Mapa extendido! Cómete a los demás, huye de los grandes y llega al Top 1.")

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
        st.info("💡 **Instrucciones:** \n- El mapa es GIGANTE (3000x3000px).\n- Hay 30 estrellas compitiendo.\n- Arriba a la izquierda verás el Top 10.\n- Sigue el ratón para moverte.")

else:
    st.button("⏹️ Volver al Menú / Reiniciar", on_click=volver_menu)
    
    # Código HTML/JS con cámara, mapa grande y leaderboard
    codigo_juego = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { margin: 0; overflow: hidden; background-color: #000; display: flex; justify-content: center; }
            canvas { background-color: #111; cursor: crosshair; border-radius: 5px;}
            #gameover { display: none; position: absolute; color: white; font-family: sans-serif; top: 40%; text-align: center; font-size: 24px; text-shadow: 2px 2px 4px #000; }
        </style>
    </head>
    <body>
        <canvas id="gameCanvas" width="900" height="600"></canvas>
        <div id="gameover">
            <h2>¡Te comieron! 💥</h2>
            <p>Estás en modo espectador (siguiendo al #1).</p>
            <p style="font-size: 16px; color:#aaa;">Usa el botón de Streamlit arriba para reiniciar.</p>
        </div>

        <script>
            const canvas = document.getElementById("gameCanvas");
            const ctx = canvas.getContext("2d");
            const overScreen = document.getElementById("gameover");

            // Configuración del mundo (mucho más grande que el canvas)
            const worldW = 3000;
            const worldH = 3000;
            
            // Variables de la cámara y ratón
            let camX = 0;
            let camY = 0;
            let screenMouseX = canvas.width / 2;
            let screenMouseY = canvas.height / 2;
            let isGameOver = false;

            // Escuchar el mouse en la pantalla
            canvas.addEventListener('mousemove', (e) => {
                const rect = canvas.getBoundingClientRect();
                screenMouseX = e.clientX - rect.left;
                screenMouseY = e.clientY - rect.top;
            });

            // Nombres aleatorios espaciales para los bots
            const nombres = ["Alpha", "Nova", "Sirius", "Vega", "Orion", "Cosmos", "Apollo", "Zeta", "Pulsar", "Quasar", 
                             "Rigel", "Lyra", "Draco", "Cygnus", "Pegasus", "Phoenix", "Astro", "Cometa", "Meteor", "Nebula",
                             "Titan", "Atlas", "Galia", "Krypton", "Zenith", "Vortex", "Horizon", "Eclipse", "Aurora", "Polaris"];
            const colors = ['#FF3366', '#33CCFF', '#FF9933', '#33FF66', '#CC33FF', '#FFFF33', '#FF3333', '#33FFCC'];

            function randomName() {
                return nombres[Math.floor(Math.random() * nombres.length)];
            }

            function randomColor() {
                return colors[Math.floor(Math.random() * colors.length)];
            }

            // Dibuja una estrella
            function drawStar(x, y, radius, color) {
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
                
                // Borde oscuro para dar volumen
                ctx.lineWidth = radius * 0.1;
                ctx.strokeStyle = "rgba(0,0,0,0.3)";
                ctx.stroke();
                ctx.closePath();
                ctx.restore();
            }

            let player, bots, foods;
            const maxBots = 29; // 29 bots + 1 jugador = 30 estrellas
            const maxFoods = 600;

            function init() {
                isGameOver = false;
                overScreen.style.display = 'none';
                
                // Jugador
                player = { 
                    x: Math.random() * worldW, 
                    y: Math.random() * worldH, 
                    r: 15, 
                    color: '#FFFFFF', 
                    name: "TÚ",
                    speed: 3,
                    dead: false
                };
                
                // Bots
                bots = [];
                for(let i=0; i<maxBots; i++) {
                    spawnBot();
                }

                // Comida
                foods = [];
                for(let i=0; i<maxFoods; i++) {
                    spawnFood();
                }
                loop();
            }

            function spawnBot() {
                bots.push({
                    x: Math.random() * worldW,
                    y: Math.random() * worldH,
                    r: Math.random() * 20 + 10, // Tamaño inicial aleatorio
                    color: randomColor(),
                    name: randomName(),
                    vx: (Math.random() - 0.5) * 4,
                    vy: (Math.random() - 0.5) * 4,
                    dead: false
                });
            }

            function spawnFood() {
                foods.push({
                    x: Math.random() * worldW,
                    y: Math.random() * worldH,
                    r: 3,
                    color: randomColor()
                });
            }

            function update() {
                // Posición objetivo del jugador basada en cámara + ratón
                let targetX = screenMouseX + camX;
                let targetY = screenMouseY + camY;

                if(!player.dead) {
                    let dx = targetX - player.x;
                    let dy = targetY - player.y;
                    let dist = Math.sqrt(dx*dx + dy*dy);
                    
                    if (dist > 5) {
                        let speedMultiplier = 15 / player.r;
                        if(speedMultiplier < 0.3) speedMultiplier = 0.3; // Límite de lentitud
                        player.x += (dx / dist) * (player.speed * speedMultiplier);
                        player.y += (dy / dist) * (player.speed * speedMultiplier);
                    }
                    
                    // Límites del mapa para el jugador
                    player.x = Math.max(player.r, Math.min(worldW - player.r, player.x));
                    player.y = Math.max(player.r, Math.min(worldH - player.r, player.y));
                }

                // Actualizar Cámara (Si el jugador muere, la cámara sigue al bot más grande)
                let allStars = [player, ...bots].filter(s => !s.dead);
                allStars.sort((a, b) => b.r - a.r);
                
                let targetCamX = (!player.dead) ? player.x : (allStars[0]?.x || 0);
                let targetCamY = (!player.dead) ? player.y : (allStars[0]?.y || 0);

                // Suavizado de cámara
                camX += (targetCamX - canvas.width / 2 - camX) * 0.1;
                camY += (targetCamY - canvas.height / 2 - camY) * 0.1;

                // Mover Bots
                bots.forEach(bot => {
                    let speedMultiplier = 15 / bot.r;
                    if(speedMultiplier < 0.3) speedMultiplier = 0.3;

                    // De vez en cuando cambian de dirección
                    if(Math.random() < 0.02) {
                        bot.vx = (Math.random() - 0.5) * 4;
                        bot.vy = (Math.random() - 0.5) * 4;
                    }

                    bot.x += bot.vx * speedMultiplier;
                    bot.y += bot.vy * speedMultiplier;

                    // Rebote en los bordes del mapa gigante
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
                            e.r += 0.1; // Crecer un poquito al comer puntos
                            foods.splice(i, 1);
                            spawnFood(); // Reaparecer comida
                            break;
                        }
                    }
                }

                // Colisiones: Todos contra Todos
                for(let i = 0; i < allStars.length; i++) {
                    for(let j = i + 1; j < allStars.length; j++) {
                        let e1 = allStars[i];
                        let e2 = allStars[j];
                        if(e1.dead || e2.dead) continue;

                        let d = Math.hypot(e1.x - e2.x, e1.y - e2.y);
                        
                        // Si la distancia es menor a la estrella más grande, es comida
                        if(d < Math.max(e1.r, e2.r) * 0.8) { 
                            if(e1.r > e2.r * 1.15) { // e1 debe ser un 15% más grande para comer a e2
                                e1.r += e2.r * 0.4;
                                e2.dead = true;
                            } else if (e2.r > e1.r * 1.15) {
                                e2.r += e1.r * 0.4;
                                e1.dead = true;
                            }
                        }
                    }
                }

                // Limpiar muertos
                if(player.dead && !isGameOver) {
                    isGameOver = true;
                    overScreen.style.display = 'block';
                }
                
                bots = bots.filter(b => !b.dead);
                
                // Repoblar bots para que siempre haya 30
                while(bots.length < maxBots) {
                    spawnBot();
                }
            }

            function drawGrid() {
                ctx.strokeStyle = "#222";
                ctx.lineWidth = 2;
                let gridSize = 100;
                
                // Dibujar solo las líneas de la cuadrícula visibles en la cámara
                let startX = Math.floor(camX / gridSize) * gridSize;
                let startY = Math.floor(camY / gridSize) * gridSize;
                
                ctx.beginPath();
                for(let x = startX; x < camX + canvas.width + gridSize; x += gridSize) {
                    if(x >= 0 && x <= worldW) { ctx.moveTo(x, 0); ctx.lineTo(x, worldH); }
                }
                for(let y = startY; y < camY + canvas.height + gridSize; y += gridSize) {
                    if(y >= 0 && y <= worldH) { ctx.moveTo(0, y); ctx.lineTo(worldW, y); }
                }
                ctx.stroke();
            }

            function drawLeaderboard() {
                let allStars = [player, ...bots].filter(s => !s.dead);
                allStars.sort((a, b) => b.r - a.r);
                let top10 = allStars.slice(0, 10);

                // Fondo de la tabla
                ctx.fillStyle = "rgba(0, 0, 0, 0.6)";
                ctx.roundRect = function(x, y, w, h, r) {
                    ctx.beginPath(); ctx.moveTo(x+r, y); ctx.lineTo(x+w-r, y); ctx.quadraticCurveTo(x+w, y, x+w, y+r);
                    ctx.lineTo(x+w, y+h-r); ctx.quadraticCurveTo(x+w, y+h, x+w-r, y+h); ctx.lineTo(x+r, y+h);
                    ctx.quadraticCurveTo(x, y+h, x, y+h-r); ctx.lineTo(x, y+r); ctx.quadraticCurveTo(x, y, x+r, y); ctx.closePath();
                };
                if(ctx.roundRect) ctx.roundRect(10, 10, 200, 35 + (top10.length * 25), 10);
                else ctx.fillRect(10, 10, 200, 35 + (top10.length * 25));
                ctx.fill();

                // Título
                ctx.fillStyle = "white";
                ctx.font = "bold 16px Arial";
                ctx.textAlign = "center";
                ctx.fillText("🏆 TOP 10 ESTRELLAS", 110, 30);

                // Nombres
                ctx.textAlign = "left";
                ctx.font = "14px Arial";
                for(let i=0; i<top10.length; i++) {
                    let s = top10[i];
                    let yPos = 60 + (i * 25);
                    
                    // Puntito de color
                    ctx.fillStyle = s.color;
                    ctx.beginPath();
                    ctx.arc(25, yPos - 4, 6, 0, Math.PI*2);
                    ctx.fill();
                    ctx.strokeStyle = "#fff";
                    ctx.lineWidth = 1;
                    ctx.stroke();

                    // Texto del nombre y tamaño
                    ctx.fillStyle = s.name === "TÚ" ? "#FFD700" : "white"; // Dorado si eres tú
                    let text = `${i+1}. ${s.name} (${Math.floor(s.r)})`;
                    ctx.fillText(text, 40, yPos);
                }
            }

            function draw() {
                // Limpiar pantalla
                ctx.fillStyle = "#111";
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                
                ctx.save();
                // Aplicar movimiento de cámara
                ctx.translate(-camX, -camY);
                
                // Dibujar bordes del mapa rojo para saber dónde termina
                ctx.strokeStyle = "red";
                ctx.lineWidth = 5;
                ctx.strokeRect(0, 0, worldW, worldH);
                
                drawGrid();
                
                // Dibujar Comida
                foods.forEach(f => {
                    // Solo dibujar si está en la pantalla (Optimización)
                    if(f.x > camX && f.x < camX + canvas.width && f.y > camY && f.y < camY + canvas.height) {
                        ctx.beginPath();
                        ctx.arc(f.x, f.y, f.r, 0, Math.PI * 2);
                        ctx.fillStyle = f.color;
                        ctx.fill();
                    }
                });

                // Dibujar Estrellas y Nombres
                let allStars = [player, ...bots].filter(s => !s.dead);
                // Dibujar de menor a mayor tamaño para que los grandes tapen a los chicos
                allStars.sort((a, b) => a.r - b.r); 

                allStars.forEach(s => {
                    // Solo dibujar si están cerca de la pantalla
                    if(s.x + s.r > camX && s.x - s.r < camX + canvas.width && s.y + s.r > camY && s.y - s.r < camY + canvas.height) {
                        drawStar(s.x, s.y, s.r, s.color);
                        
                        // Etiqueta del nombre encima de la estrella
                        ctx.fillStyle = "white";
                        ctx.font = "bold 14px Arial";
                        ctx.textAlign = "center";
                        // Sombra del texto para que se lea mejor
                        ctx.shadowColor = "black";
                        ctx.shadowBlur = 4;
                        ctx.fillText(s.name, s.x, s.y + s.r + 18);
                        ctx.shadowBlur = 0; // quitar sombra
                    }
                });

                ctx.restore(); // Termina lo afectado por la cámara

                // Dibujar la interfaz (Leaderboard) Fija en la pantalla
                drawLeaderboard();
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
    
    # Ajustamos el tamaño del iframe para que coincida con el canvas
    components.html(codigo_juego, height=620, width=920, scrolling=False)
