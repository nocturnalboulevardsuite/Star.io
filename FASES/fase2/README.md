# Fase 2 · Desierto del Faraón

Plataformas estilo Jump King + jefe estilo Cuphead. Eres un robot con cara de estrella:
sube por las areniscas, esquiva los láseres de los ojos del Faraón y lo que te lanza,
mata a las momias y golpea al Faraón en la cara.

Se desbloquea al ganar el Nivel 1 (en cualquier dificultad). Con el nombre RISSOS está abierta siempre.

## Archivos
- `fase.js`: todo el código de la fase (app.py lo carga solo).
- `config.json`: los números para balancear, sin tocar código.

## Controles
| Tecla | Acción |
|---|---|
| A / D | Caminar |
| Mantener ESPACIO o W | Cargar el salto (suelta para saltar; más carga = más alto) |
| A/D al soltar el salto | Saltar hacia ese lado |
| Click izquierdo o J | Golpe hacia el mouse (3 seguidos = combo, el 3º pega más fuerte) |
| R | Espada por 15 s (más daño y alcance), luego 60 s de recarga |
| ESC | Pausa |

## config.json
| Campo | Qué hace |
|---|---|
| `jefe.vida` | Vida del Faraón |
| `jefe.fase2_en` | Con qué % de vida se enfurece (0.5 = a la mitad) |
| `jefe.laser_espera_min/max` | Frames entre láseres de los ojos (60 = 1 s) |
| `jefe.laser_aviso` | Frames de aviso (línea punteada) antes del láser |
| `jefe.laser_duracion` | Frames que dura el láser |
| `jefe.objetos_espera_min/max` | Frames entre objetos lanzados |
| `momias.vida`, `velocidad`, `max` | Vida, velocidad y máximo de momias a la vez |
| `momias.espera_min/max` | Frames entre apariciones |
| `momias.prob_ankh` | Probabilidad de que suelten un ankh (+1 vida) |
| `jugador.vida` | Corazones del robot |
| `jugador.salto_min/max` | Fuerza del salto sin cargar / con carga completa |
| `jugador.carga_frames` | Frames para cargar el salto al máximo |
| `jugador.golpes` | Daño de los 3 golpes del combo |
| `espada.duracion_s`, `cooldown_s`, `multiplicador` | Duración, recarga y daño extra de la espada |
