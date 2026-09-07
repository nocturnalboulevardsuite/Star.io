import streamlit as st
import streamlit.components.v1 as components

# Configuración de la página
st.set_page_config(page_title="Star.io", layout="centered")

st.title("🌟 Star.io - Supervivencia Espacial")
st.write("Come los puntos pequeños para crecer. Cómete a las estrellas más pequeñas. ¡Huye de las grandes!")

# Manejo del estado para el menú
if 'jugando' not in st.session_state:
    st.session_state.jugando = False

# Función para cambiar de estado
def iniciar_juego():
    st.session_state.jugando = True

def volver_menu():
    st.session_state.jugando = False

# Pantalla de Menú
if not st.session_state.jugando:
    st.button("▶️ JUGAR", on_click=iniciar_juego, type="primary", use_container_width=True)
    st.info("💡 **Instrucciones:** Mueve el mouse sobre el recuadro del juego para dirigir a tu estrella. El juego es todos contra todos.")

# Pantalla de Juego
else:
    st.button("⏹️ Volver al Menú", on_click=volver_menu)
    
    # Código HTML/JS del juego incrustado
    codigo_juego = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { margin: 0; overflow: hidden; background-color: #111; display: flex; justify-content: center; }
            canvas { background-color: #222; border: 2px solid #555; border-radius: 10px; cursor: crosshair; }
            #gameover { display: none; position: absolute; color: white; font-family: sans-serif; top: 40%; text-align: center; font-size: 24px; }
        </style>
    </head>
    <body>
        <canvas id="gameCanvas" width="700" height="500"></canvas>
        <div id="gameover">
            <h2>¡Te comieron!</h2>
            <p>Haz clic en la pantalla para volver a jugar.</p>
        </div>

        <script>
            const canvas = document.getElementById("gameCanvas");
            const ctx = canvas.getContext("2d");
            const overScreen = document.getElementById("gameover");

            let mouseX = canvas.width / 2;
            let mouseY = canvas.height / 2;
            let isGameOver = false;

            // Escuchar el mouse
            canvas.addEventListener('mousemove', (e) => {
                const rect = canvas.getBoundingClientRect();
                mouseX = e.clientX - rect.left;
                mouseY = e.clientY - rect.top;
            });
            
            canvas.addEventListener('mousedown', () => {
                if(isGameOver) init();
            });

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
                ctx.closePath();
                ctx.restore();
            }

            function drawCircle(x, y, radius, color) {
                ctx.beginPath();
                ctx.arc(x, y, radius, 0, Math.PI * 2);
                ctx.fillStyle = color;
                ctx.fill();
                ctx.closePath();
            }

            let player, bots, foods;
            const colors = ['#FF3366', '#33CCFF', '#FF9933', '#33FF66', '#CC33FF', '#FFFF33'];

            function init() {
                isGameOver = false;
                overScreen.style.display = 'none';
                
                player = { x: canvas.width/2, y: canvas.height/2, r: 15, color: '#FFFFFF', speed: 3 };
                
                bots = [];
                for(let i=0; i<8; i++) {
                    bots.push({
                        x: Math.random() * canvas.width,
                        y: Math.random() * canvas.height,
                        r: Math.random() * 20 + 10,
                        color: colors[Math.floor(Math.random() * colors.length)],
                        vx: (Math.random() - 0.5) * 4,
                        vy: (Math.random() - 0.5) * 4
                    });
                }

                foods = [];
                for(let i=0; i<50; i++) {
                    foods.push({
                        x: Math.random() * canvas.width,
                        y: Math.random() * canvas.height,
                        r: 3,
                        color: colors[Math.floor(Math.random() * colors.length)]
                    });
                }
                loop();
            }

            function update() {
                if(isGameOver) return;

                // Mover Jugador hacia el mouse
                let dx = mouseX - player.x;
                let dy = mouseY - player.y;
                let dist = Math.sqrt(dx*dx + dy*dy);
                if (dist > 5) {
                    player.x += (dx / dist) * (player.speed * (15/player.r)); // Más grande = más lento
                    player.y += (dy / dist) * (player.speed * (15/player.r));
                }

                // Mover Bots
                bots.forEach(bot => {
                    bot.x += bot.vx * (15/bot.r);
                    bot.y += bot.vy * (15/bot.r);
                    // Rebote en paredes
                    if(bot.x < 0 || bot.x > canvas.width) bot.vx *= -1;
                    if(bot.y < 0 || bot.y > canvas.height) bot.vy *= -1;
                });

                // Colisiones: Entidades vs Comida
                let entities = [player, ...bots];
                for(let i = foods.length - 1; i >= 0; i--) {
                    let f = foods[i];
                    for(let e of entities) {
                        let d = Math.hypot(e.x - f.x, e.y - f.y);
                        if(d < e.r) {
                            e.r += 0.2; // Crecer
                            foods.splice(i, 1);
                            // Reaparecer comida
                            foods.push({
                                x: Math.random() * canvas.width,
                                y: Math.random() * canvas.height,
                                r: 3,
                                color: colors[Math.floor(Math.random() * colors.length)]
                            });
                            break;
                        }
                    }
                }

                // Colisiones: Todos contra Todos
                for(let i = 0; i < entities.length; i++) {
                    for(let j = i + 1; j < entities.length; j++) {
                        let e1 = entities[i];
                        let e2 = entities[j];
                        let d = Math.hypot(e1.x - e2.x, e1.y - e2.y);
                        
                        if(d < Math.abs(e1.r - e2.r) + 5) { // Uno se come al otro
                            if(e1.r > e2.r * 1.1) {
                                e1.r += e2.r * 0.3;
                                e2.dead = true;
                            } else if (e2.r > e1.r * 1.1) {
                                e2.r += e1.r * 0.3;
                                e1.dead = true;
                            }
                        }
                    }
                }

                // Limpiar muertos
                if(player.dead) {
                    isGameOver = true;
                    overScreen.style.display = 'block';
                }
                bots = bots.filter(b => !b.dead);
                
                // Generar bots nuevos si hay pocos
                if(bots.length < 5 && Math.random() < 0.02) {
                    bots.push({
                        x: Math.random() * canvas.width,
                        y: Math.random() * canvas.height,
                        r: Math.random() * 20 + 10,
                        color: colors[Math.floor(Math.random() * colors.length)],
                        vx: (Math.random() - 0.5) * 4,
                        vy: (Math.random() - 0.5) * 4
                    });
                }
            }

            function draw() {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                
                foods.forEach(f => drawCircle(f.x, f.y, f.r, f.color));
                bots.forEach(b => drawStar(b.x, b.y, b.r, b.color));
                
                if(!isGameOver) {
                    drawStar(player.x, player.y, player.r, player.color);
                    // Nombre jugador
                    ctx.fillStyle = "white";
                    ctx.font = "12px Arial";
                    ctx.textAlign = "center";
                    ctx.fillText("TÚ", player.x, player.y + player.r + 15);
                }
            }

            function loop() {
                update();
                draw();
                if(!isGameOver) {
                    requestAnimationFrame(loop);
                }
            }

            init();
        </script>
    </body>
    </html>
    """
    
    # Renderizamos el juego
    components.html(codigo_juego, height=520, scrolling=False)
