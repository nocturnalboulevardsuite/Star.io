# Fase 2 · Desierto del Faraón

Plataformas estilo Jump King + jefes estilo Cuphead, con un soldado pixel art con cabeza de estrella.
Sube por las areniscas, golpea al Faraón en la cara y, cuando huya, vence a la Momia Gigante.

Se desbloquea al ganar el Nivel 1 (en cualquier dificultad). Con el nombre RISSOS está abierta siempre.

## Archivos
- `fase.js`: todo el código de la fase (app.py lo carga solo).
- `config.json`: los números para balancear, sin tocar código.

## Controles
| Tecla | Acción |
|---|---|
| A / D | Caminar |
| Mantener ESPACIO o W | Cargar el salto (suelta para saltar; más carga = más alto) |
| Click izquierdo o J | Golpe hacia el mouse (3 seguidos = combo) |
| Mantener click derecho | Cubrirse (gasta la barra de guardia; si se vacía, guardia rota) |
| R | Katana por 15 s, luego 60 s de recarga |
| ESC | Pausa |

## Cómo va la pelea
1. **Faraón**: láser por los ojos con aviso y objetos lanzados. A la mitad de vida se enfurece.
2. Al morir **grita**, la pantalla tiembla y **sale volando** hacia arriba.
3. Sale de la arena la **Momia Gigante**, que lanza rollos de venda. A la mitad se desenvuelve y lanza 3 a la vez.
4. Momias chicas aparecen de vez en cuando (pocas): 10 golpes o 5 espadazos.
5. **Arena movediza**: si te quedas mucho tiempo en la parte baja, la arena sube. Si te cubre, te hundes y mueres.

## config.json
| Campo | Qué hace |
|---|---|
| `jefe.*` | Faraón: vida, cuándo se enfurece, frecuencia de láseres y objetos |
| `momia_gigante.vida`, `fase2_en` | Vida de la momia gigante y cuándo se desenvuelve |
| `momia_gigante.rollos_espera_min/max` | Frames entre lanzamientos de rollos (60 = 1 s) |
| `momias.vida`, `daño_golpe`, `daño_espada` | Con 20 / 2 / 4: 10 golpes o 5 espadazos |
| `momias.max`, `espera_min/max` | Cuántas momias chicas a la vez y cada cuánto aparecen |
| `momias.prob_ankh` | Probabilidad de soltar un ankh (+1 vida) |
| `jugador.*` | Corazones, fuerza del salto y daño del combo al jefe |
| `espada.*` | Duración, recarga y multiplicador de daño de la katana |
| `guardia.max`, `costo_golpe`, `costo_laser`, `recarga` | Barra de guardia y cuánto gasta cada bloqueo |
| `arena.segundos_para_subir` | Segundos abajo antes de que suba la arena |
| `arena.velocidad_subida`, `altura_max` | Qué tan rápido y hasta dónde sube |
| `arena.segundos_para_hundirse` | Segundos dentro de la arena antes de morir |
