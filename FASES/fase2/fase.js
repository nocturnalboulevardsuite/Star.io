// ============================================================
// FASE 2 · DESIERTO DEL FARAÓN
// Plataformas estilo Jump King + jefe estilo Cuphead.
// Eres un robot con cara de estrella. Salta por las areniscas,
// pega combos, saca la espada con R y derrota al Faraón.
//
// Este archivo lo carga app.py automáticamente desde FASES/fase_2/.
// Los valores de dificultad están en config.json (misma carpeta).
// ============================================================
(function () {
    const ID = window.__FASE_ID__ || 'fase2';   // app.py pone aquí el nombre de la carpeta

    // ---------- Configuración (se mezcla con config.json) ----------
    const DEFAULTS = {
        nombre: "Desierto del Faraón",
        jefe: {
            nombre: "FARAÓN", vida: 900, fase2_en: 0.5,
            laser_espera_min: 180, laser_espera_max: 300, laser_aviso: 45, laser_duracion: 30,
            objetos_espera_min: 150, objetos_espera_max: 240
        },
        momias: { vida: 30, velocidad: 1.2, espera_min: 300, espera_max: 420, max: 4, prob_ankh: 0.2 },
        jugador: { vida: 6, salto_min: 7, salto_max: 19, carga_frames: 40, golpes: [8, 10, 18] },
        espada: { duracion_s: 15, cooldown_s: 60, multiplicador: 2.5 }
    };
    function merge(d, c) {
        const out = {};
        Object.keys(d).forEach(k => {
            const v = c ? c[k] : undefined;
            if (d[k] && typeof d[k] === 'object' && !Array.isArray(d[k])) out[k] = merge(d[k], v);
            else out[k] = v !== undefined ? v : d[k];
        });
        return out;
    }

    // ---------- Mundo (coordenadas lógicas) ----------
    const W = 1000, H = 1800, FLOOR = 1760, GRAV = 0.6, MAX_FALL = 16;
    const PLATFORMS = [
        { x: 80, y: 1630, w: 230 }, { x: 430, y: 1550, w: 180 }, { x: 730, y: 1460, w: 220 },
        { x: 390, y: 1350, w: 170 }, { x: 60, y: 1260, w: 210 }, { x: 340, y: 1140, w: 180 },
        { x: 700, y: 1060, w: 230 }, { x: 460, y: 950, w: 150 }, { x: 110, y: 870, w: 210 },
        { x: 380, y: 760, w: 240 }, { x: 770, y: 740, w: 190 }, { x: 30, y: 690, w: 170 }
    ];
    const HEAD = { x: 500, y: 390, rx: 175, ry: 255 };       // zona golpeable del Faraón
    const EYES = [{ x: 438, y: 330 }, { x: 562, y: 330 }];

    let api = null, C = null, ctx = null, canvas = null;
    let S = null;            // estado de la partida
    let keys = new Set(), mouse = { x: 0, y: 0, down: false };
    let overlay = null;
    let listenersReady = false;

    const rand = (a, b) => a + Math.random() * (b - a);

    // El Faraón siempre se ve: cuando estás abajo aparece "a lo lejos" (más chico, arriba de la pantalla)
    // y cuando subes se acerca hasta su tamaño real. Solo se le puede pegar cuando está cerca.
    function pose() {
        const top = topCam(), bottom = Math.max(top + 1, H - S.viewH);
        const k = Math.max(0, Math.min(1, (S.camY - top) / (bottom - top)));
        const screenY = (HEAD.y - S.camY) + (150 - (HEAD.y - S.camY)) * k;
        const sc = 1 - 0.45 * k;
        return { x: HEAD.x, y: S.camY + screenY, s: sc, k, hittable: k < 0.22 };
    }
    // cámara cuando estás en las plataformas más altas
    function topCam() { return Math.max(0, 655 - S.viewH * 0.85); }
    function eyePos(i) { const P = pose(); return { x: P.x + (EYES[i].x - HEAD.x) * P.s, y: P.y + (EYES[i].y - HEAD.y) * P.s }; }

    function newState() {
        const rissos = api.isRissos();
        const P = C.jugador;
        return {
            t: 0, scale: 1, offX: 0, viewH: 700, camY: H - 700,
            paused: false, over: false,
            player: {
                x: 190, y: FLOOR - 35, vx: 0, vy: 0, onGround: true, facing: 1,
                hp: rissos ? 20 : P.vida, maxHp: rissos ? 20 : P.vida, inv: 0,
                charge: 0, charging: false,
                atk: 0, atkDir: 0, combo: 0, comboWindow: 0, hitThisSwing: new Set(),
                hitCombo: 0, hitComboTimer: 0,
                sword: 0, swordCd: 0, kbx: 0
            },
            boss: {
                hp: C.jefe.vida, maxHp: C.jefe.vida, phase2: false, flash: 0, dead: false, deathT: 0,
                laserT: rand(C.jefe.laser_espera_min, C.jefe.laser_espera_max), laser: null,
                throwT: rand(C.jefe.objetos_espera_min, C.jefe.objetos_espera_max)
            },
            mummies: [], mummyT: 120, objects: [], pickups: [], particles: [], texts: [],
            dust: Array.from({ length: 40 }, () => ({ x: rand(0, W), y: rand(0, H), s: rand(0.4, 1.4) })),
            rissos
        };
    }

    // ---------- Entrada ----------
    function setupListeners() {
        if (listenersReady) return; listenersReady = true;
        window.addEventListener('keydown', e => {
            if (!api || !api.active()) return;
            if (['Space', 'KeyW', 'ArrowUp'].includes(e.code)) e.preventDefault();
            keys.add(e.code);
            if (e.repeat) return;
            if (e.code === 'Escape') togglePause();
            if (S && !S.paused && !S.over) {
                if (e.code === 'KeyR') activateSword();
                if (e.code === 'KeyJ' || e.code === 'KeyK') attack();
            }
        });
        window.addEventListener('keyup', e => {
            if (!api || !api.active()) return;
            if (['Space', 'KeyW', 'ArrowUp'].includes(e.code) && S && !S.paused && !S.over) releaseJump();
            keys.delete(e.code);
        });
        window.addEventListener('blur', () => { keys.clear(); mouse.down = false; });
        canvas.addEventListener('mousemove', e => { const r = canvas.getBoundingClientRect(); mouse.x = e.clientX - r.left; mouse.y = e.clientY - r.top; });
        canvas.addEventListener('mousedown', e => {
            if (!api || !api.active() || !S || S.paused || S.over) return;
            if (e.button === 0) { mouse.down = true; attack(); }
        });
        window.addEventListener('mouseup', e => { if (e.button === 0) mouse.down = false; });
    }
    const jumpHeld = () => keys.has('Space') || keys.has('KeyW') || keys.has('ArrowUp');
    const left = () => keys.has('KeyA') || keys.has('ArrowLeft');
    const right = () => keys.has('KeyD') || keys.has('ArrowRight');
    function mouseWorld() { return { x: (mouse.x - S.offX) / S.scale, y: mouse.y / S.scale + S.camY }; }

    // ---------- Acciones del jugador ----------
    function releaseJump() {
        const p = S.player;
        if (!p.charging) return;
        const J = C.jugador;
        const c = Math.min(1, p.charge / J.carga_frames);
        p.vy = -(J.salto_min + (J.salto_max - J.salto_min) * c);
        const dir = (left() ? -1 : 0) + (right() ? 1 : 0);
        p.vx = dir * (2.5 + 5 * c);
        if (dir) p.facing = dir;
        p.onGround = false; p.charging = false; p.charge = 0;
        for (let i = 0; i < 8; i++) puff(p.x + rand(-14, 14), p.y + 35, '#E8C27A');
    }

    function attack() {
        const p = S.player;
        if (p.atk > 0) { p.queued = true; return; }
        const m = mouseWorld();
        p.atkDir = Math.atan2(m.y - p.y, m.x - p.x);
        p.facing = Math.cos(p.atkDir) >= 0 ? 1 : -1;
        p.combo = p.comboWindow > 0 ? (p.combo % 3) + 1 : 1;
        p.atk = 14; p.hitThisSwing = new Set();
        api.playAbilitySfx(p.sword > 0 ? 'whoosh' : 'ping');
    }

    function activateSword() {
        const p = S.player;
        if (p.sword > 0) return;
        if (p.swordCd > 0) { text(p.x, p.y - 60, `ESPADA: ${Math.ceil(p.swordCd / 60)}s`, '#999', 14); return; }
        p.sword = C.espada.duracion_s * 60;
        api.playAbilitySfx('metal');
        text(p.x, p.y - 70, '¡ESPADA!', '#7DF9FF', 26);
    }

    function hurtPlayer(n, fromX) {
        const p = S.player;
        if (p.inv > 0 || S.over) return;
        p.hp -= n; p.inv = 60;
        p.vy = -7; p.kbx = (p.x < fromX ? -1 : 1) * 7; p.onGround = false; p.charging = false; p.charge = 0;
        text(p.x, p.y - 50, `-${n}`, '#FF3355', 22);
        api.playAbilitySfx('boom');
        for (let i = 0; i < 12; i++) puff(p.x, p.y, '#FF3355');
        if (p.hp <= 0) lose();
    }

    // ---------- Efectos ----------
    function puff(x, y, color) { S.particles.push({ x, y, vx: rand(-2.5, 2.5), vy: rand(-3, 0.5), life: rand(18, 30), color }); }
    function text(x, y, t, color, size) { S.texts.push({ x, y, t, color, size: size || 16, life: 50 }); }

    // ---------- Física ----------
    function landOn(e, prevBottom, half) {
        // plataformas de una vía: solo se aterriza cayendo desde arriba
        const bottom = e.y + half;
        if (e.vy >= 0) {
            for (const pl of PLATFORMS) {
                if (e.x + 12 > pl.x && e.x - 12 < pl.x + pl.w && prevBottom <= pl.y + 1 && bottom >= pl.y) {
                    e.y = pl.y - half; e.vy = 0; return pl;
                }
            }
            if (bottom >= FLOOR) { e.y = FLOOR - half; e.vy = 0; return 'floor'; }
        }
        return null;
    }

    function updatePlayer() {
        const p = S.player, J = C.jugador;
        if (p.inv > 0) p.inv--;
        if (p.sword > 0) { p.sword--; if (p.sword === 0) { p.swordCd = (S.rissos ? 5 : C.espada.cooldown_s) * 60; text(p.x, p.y - 60, 'ESPADA AGOTADA', '#999', 16); } }
        else if (p.swordCd > 0) p.swordCd--;
        if (p.comboWindow > 0) p.comboWindow--;
        if (p.hitComboTimer > 0) { p.hitComboTimer--; if (p.hitComboTimer === 0) p.hitCombo = 0; }

        // Ataque en curso
        if (p.atk > 0) {
            p.atk--;
            if (p.atk <= 10 && p.atk >= 4) resolveHits();
            if (p.atk === 0) { p.comboWindow = 22; if (p.queued) { p.queued = false; attack(); } }
        }

        const dir = (left() ? -1 : 0) + (right() ? 1 : 0);
        if (p.onGround) {
            if (jumpHeld()) { p.charging = true; p.charge = Math.min(J.carga_frames, p.charge + 1); p.vx = 0; }
            else { p.vx = dir * 4.2; if (dir) p.facing = dir; }
        } else {
            // muy poco control en el aire (estilo Jump King)
            if (dir) p.vx += dir * 0.12;
            p.vx = Math.max(-8, Math.min(8, p.vx));
        }
        const prevBottom = p.y + 35;
        p.vy = Math.min(MAX_FALL, p.vy + GRAV);
        p.x += p.vx + p.kbx; p.y += p.vy;
        p.kbx *= 0.8; if (Math.abs(p.kbx) < 0.1) p.kbx = 0;

        // Muros: rebote
        if (p.x < 22) { p.x = 22; p.vx = Math.abs(p.vx) * 0.6; }
        if (p.x > W - 22) { p.x = W - 22; p.vx = -Math.abs(p.vx) * 0.6; }
        if (p.y < 40) { p.y = 40; p.vy = Math.max(0, p.vy); }

        const wasAir = !p.onGround;
        const landed = landOn(p, prevBottom, 35);
        p.onGround = !!landed;
        if (landed && wasAir) { p.vx = 0; for (let i = 0; i < 6; i++) puff(p.x + rand(-14, 14), p.y + 35, '#E8C27A'); }
        if (!landed && p.charging) { p.charging = false; p.charge = 0; }
    }

    function attackCircle() {
        const p = S.player, sw = p.sword > 0;
        const reach = sw ? 78 : 50, rad = sw ? 64 : (p.combo === 3 ? 48 : 40);
        return { x: p.x + Math.cos(p.atkDir) * reach, y: p.y + Math.sin(p.atkDir) * reach, r: rad };
    }
    function attackDamage() {
        const p = S.player;
        let d = C.jugador.golpes[p.combo - 1] || C.jugador.golpes[0];
        if (p.sword > 0) d *= C.espada.multiplicador;
        d *= 1 + Math.min(0.5, p.hitCombo * 0.05);           // bonus por combo
        if (S.rissos) d *= 2;
        return Math.round(d);
    }
    function registerHit() {
        const p = S.player;
        p.hitCombo++; p.hitComboTimer = 120;
        if (p.hitCombo >= 3) text(p.x, p.y - 80, `COMBO x${p.hitCombo}`, '#FFD700', 18 + Math.min(14, p.hitCombo));
    }

    function resolveHits() {
        const p = S.player, a = attackCircle(), dmg = attackDamage();
        if (!pose().hittable && !S.boss.dead && p.atk === 10 && !S.hintT) { text(p.x, p.y - 70, '¡SUBE PARA PEGARLE AL FARAÓN!', '#FFF2D0', 16); S.hintT = 180; }
        // Faraón
        const b = S.boss;
        const P = pose();
        if (!b.dead && !p.hitThisSwing.has('boss') && P.hittable) {
            const dx = (a.x - P.x) / (HEAD.rx * P.s + a.r), dy = (a.y - P.y) / (HEAD.ry * P.s + a.r);
            if (dx * dx + dy * dy < 1) {
                p.hitThisSwing.add('boss'); b.hp -= dmg; b.flash = 8; registerHit();
                text(a.x, a.y - 20, `-${dmg}`, p.sword > 0 ? '#7DF9FF' : '#FFFFFF', 22);
                for (let i = 0; i < 8; i++) puff(a.x, a.y, '#FFD700');
                api.playAbilitySfx('ping');
                if (b.hp <= 0) killBoss();
                if (!b.phase2 && b.hp <= b.maxHp * C.jefe.fase2_en) { b.phase2 = true; text(P.x, P.y - 300, '¡EL FARAÓN SE ENFURECE!', '#FF3355', 30); }
            }
        }
        // Momias
        S.mummies.forEach(m => {
            if (m.dead || m.rise > 0 || p.hitThisSwing.has(m)) return;
            if (Math.hypot(m.x - a.x, m.y - a.y) < a.r + 24) {
                p.hitThisSwing.add(m); m.hp -= dmg; m.flash = 6; registerHit();
                m.kb = Math.sign(m.x - p.x || 1) * (p.combo === 3 ? 9 : 5);
                text(m.x, m.y - 40, `-${dmg}`, '#FFFFFF', 18);
                api.playAbilitySfx('ping');
                if (m.hp <= 0) killMummy(m);
            }
        });
        // Objetos lanzados: se pueden destruir de un golpe
        S.objects.forEach(o => {
            if (o.dead || p.hitThisSwing.has(o)) return;
            if (Math.hypot(o.x - a.x, o.y - a.y) < a.r + o.r) { p.hitThisSwing.add(o); breakObject(o); registerHit(); }
        });
    }

    // ---------- Faraón ----------
    function updateBoss() {
        const b = S.boss, p = S.player, J = C.jefe;
        if (b.flash > 0) b.flash--;
        if (b.dead) { b.deathT++; if (b.deathT % 6 === 0) { const P = pose(); for (let i = 0; i < 6; i++) puff(P.x + rand(-160, 160) * P.s, P.y + rand(-200, 200) * P.s, Math.random() < 0.5 ? '#FFD700' : '#C68E4E'); } return; }
        const speed = b.phase2 ? 1.6 : 1;

        // Láser por los ojos
        if (b.laser) {
            b.laser.t++;
            if (b.laser.t === J.laser_aviso) api.playSfx('laser', 1);
            if (b.laser.t > J.laser_aviso) {
                EYES.forEach((_, i) => {
                    const e = eyePos(i);
                    const x2 = e.x + Math.cos(b.laser.angles[i]) * 2400, y2 = e.y + Math.sin(b.laser.angles[i]) * 2400;
                    if (segDist(p.x, p.y, e.x, e.y, x2, y2) < 18 + 22) hurtPlayer(1, e.x);
                    S.mummies.forEach(m => { if (!m.dead && segDist(m.x, m.y, e.x, e.y, x2, y2) < 30) { m.hp -= 2; if (m.hp <= 0) killMummy(m); } });
                });
            }
            if (b.laser.t >= J.laser_aviso + J.laser_duracion) { b.laser = null; b.laserT = rand(J.laser_espera_min, J.laser_espera_max) / speed; }
        } else if ((b.laserT -= 1) <= 0) {
            // apunta donde estás ahora (con un poco de predicción)
            const tx = p.x + p.vx * 10, ty = p.y + p.vy * 4;
            b.laser = { t: 0, angles: EYES.map((_, i) => { const e = eyePos(i); return Math.atan2(ty - e.y, tx - e.x); }) };
            api.playAbilitySfx('shield');
        }

        // Lanza objetos
        if ((b.throwT -= 1) <= 0) {
            const n = b.phase2 ? 2 : 1;
            for (let i = 0; i < n; i++) throwObject(i);
            b.throwT = rand(J.objetos_espera_min, J.objetos_espera_max) / speed;
        }
    }

    function throwObject(i) {
        const p = S.player;
        const side = Math.random() < 0.5 ? -1 : 1;
        const P = pose();
        const sx = P.x + side * 230 * P.s, sy = P.y + 120 * P.s;
        const tx = p.x + rand(-60, 60) + (i ? rand(-180, 180) : 0), ty = p.y;
        const T = 55 + Math.min(40, Math.abs(ty - sy) / 20), g = 0.35;
        const kinds = ['vasija', 'escarabajo', 'bloque'];
        S.objects.push({ x: sx, y: sy, vx: (tx - sx) / T, vy: (ty - sy) / T - 0.5 * g * T, g, r: 18, kind: kinds[Math.floor(Math.random() * 3)], rot: 0, dead: false });
        api.playAbilitySfx('whoosh');
    }
    function breakObject(o) {
        o.dead = true;
        const col = o.kind === 'vasija' ? '#B5651D' : (o.kind === 'escarabajo' ? '#1FB5A8' : '#D9A55B');
        for (let i = 0; i < 14; i++) puff(o.x, o.y, col);
    }
    function updateObjects() {
        const p = S.player;
        S.objects.forEach(o => {
            if (o.dead) return;
            o.vy += o.g; o.x += o.vx; o.y += o.vy; o.rot += 0.15;
            if (Math.hypot(o.x - p.x, o.y - p.y) < o.r + 24) { breakObject(o); hurtPlayer(1, o.x); return; }
            if (o.vy > 0) {
                for (const pl of PLATFORMS) if (o.x > pl.x && o.x < pl.x + pl.w && o.y + o.r >= pl.y && o.y + o.r - o.vy <= pl.y + 2) { breakObject(o); return; }
                if (o.y + o.r >= FLOOR) breakObject(o);
            }
            if (o.x < -50 || o.x > W + 50 || o.y > H + 50) o.dead = true;
        });
        S.objects = S.objects.filter(o => !o.dead);
    }

    function killBoss() {
        const b = S.boss; b.dead = true; b.hp = 0;
        S.mummies.forEach(m => { if (!m.dead) killMummy(m, true); });
        S.objects.forEach(breakObject); b.laser = null;
        text(HEAD.x, pose().y, '¡FARAÓN DERROTADO!', '#FFD700', 44);
        api.playAbilitySfx('boom');
        S.player.inv = 99999;
        const st = S; setTimeout(() => { if (S === st) win(); }, 2600);
    }

    // ---------- Momias ----------
    function spawnMummy() {
        const p = S.player;
        const spots = [{ x: rand(60, W - 60), y: FLOOR, pl: null }].concat(PLATFORMS.map(pl => ({ x: rand(pl.x + 20, pl.x + pl.w - 20), y: pl.y, pl })));
        // aparece cerca de ti (dentro de la pantalla) pero no encima
        const near = spots.filter(s => Math.abs(s.y - p.y) < S.viewH * 0.6 && Math.abs(s.x - p.x) > 90);
        const s = (near.length ? near : spots)[Math.floor(Math.random() * (near.length || spots.length))];
        const M = C.momias;
        S.mummies.push({ x: s.x, y: s.y - 32, vx: 0, vy: 0, hp: M.vida, maxHp: M.vida, rise: 40, dir: Math.random() < 0.5 ? -1 : 1, flash: 0, kb: 0, dead: false, onGround: true, t: rand(0, 100) });
        for (let i = 0; i < 16; i++) puff(s.x + rand(-20, 20), s.y, '#E8C27A');
        text(s.x, s.y - 70, '¡MOMIA!', '#E8D9B0', 16);
    }
    function killMummy(m, silent) {
        m.dead = true;
        for (let i = 0; i < 18; i++) puff(m.x, m.y, i % 2 ? '#E8D9B0' : '#8B7355');
        if (!silent && Math.random() < C.momias.prob_ankh) S.pickups.push({ x: m.x, y: m.y - 10, vy: -4, t: 0 });
        if (!silent) api.playAbilitySfx('boom');
    }
    function updateMummies() {
        const p = S.player, b = S.boss, M = C.momias;
        const max = b.phase2 ? Math.round(M.max * 1.5) : M.max;
        if (!b.dead && (S.mummyT -= 1) <= 0) {
            if (S.mummies.filter(m => !m.dead).length < max) spawnMummy();
            S.mummyT = rand(M.espera_min, M.espera_max) / (b.phase2 ? 1.4 : 1);
        }
        S.mummies.forEach(m => {
            if (m.dead) return;
            m.t++; if (m.flash > 0) m.flash--;
            if (m.rise > 0) { m.rise--; return; }
            const sameLevel = Math.abs(p.y - m.y) < 60;
            if (sameLevel) m.dir = Math.sign(p.x - m.x) || m.dir;
            const sp = M.velocidad * (b.phase2 ? 1.35 : 1);
            m.vx = m.dir * sp + m.kb; m.kb *= 0.85; if (Math.abs(m.kb) < 0.1) m.kb = 0;
            const prevBottom = m.y + 32;
            m.vy = Math.min(MAX_FALL, m.vy + GRAV);
            const nx = m.x + m.vx;
            // se dan vuelta en el borde de su plataforma (si no los empujaste)
            if (m.onGround && !m.kb) {
                const pl = PLATFORMS.find(q => Math.abs(q.y - (m.y + 32)) < 3 && m.x >= q.x - 5 && m.x <= q.x + q.w + 5);
                if (pl && (nx < pl.x + 10 || nx > pl.x + pl.w - 10)) { m.dir *= -1; m.vx = 0; }
            }
            m.x += m.vx; m.y += m.vy;
            if (m.x < 20 || m.x > W - 20) { m.dir *= -1; m.x = Math.max(20, Math.min(W - 20, m.x)); }
            m.onGround = !!landOn(m, prevBottom, 32);
            if (Math.abs(m.x - p.x) < 34 && Math.abs(m.y - p.y) < 55) hurtPlayer(1, m.x);
        });
        S.mummies = S.mummies.filter(m => !m.dead);
    }

    function updatePickups() {
        const p = S.player;
        S.pickups.forEach(k => {
            k.t++; k.vy = Math.min(8, k.vy + 0.3); const prev = k.y + 14; k.y += k.vy;
            const l = landOn(k, prev, 14); if (l) k.vy = 0;
            if (Math.hypot(k.x - p.x, k.y - p.y) < 40) { k.taken = true; p.hp = Math.min(p.maxHp, p.hp + 1); text(p.x, p.y - 50, '+1 VIDA', '#33FF66', 18); api.playAbilitySfx('shield'); }
        });
        S.pickups = S.pickups.filter(k => !k.taken && k.t < 900);
    }

    function segDist(px, py, x1, y1, x2, y2) {
        const vx = x2 - x1, vy = y2 - y1, l2 = vx * vx + vy * vy;
        const t = l2 ? Math.max(0, Math.min(1, ((px - x1) * vx + (py - y1) * vy) / l2)) : 0;
        return Math.hypot(px - (x1 + vx * t), py - (y1 + vy * t));
    }

    // ---------- Fin de la fase ----------
    function win() {
        if (!S || S.over) return;
        S.over = true;
        api.onWin(ID);
        api.playVictoryMusic();
        showOverlay('¡FASE 2 COMPLETADA!', 'Derrotaste al Faraón', '#FFD700', [
            ['REPETIR FASE', '#FFD700', true, () => { api.stopVictoryMusic(true); restart(); }],
            ['VOLVER A NIVELES', '#00FFFF', false, () => { api.stopVictoryMusic(true); exit(); }]
        ]);
    }
    function lose() {
        S.over = true; S.player.hp = 0;
        api.playEndSfx(true);
        showOverlay('EL FARAÓN TE VENCIÓ', 'Las arenas te tragaron...', '#FF3355', [
            ['REINTENTAR', '#FF3355', true, restart],
            ['VOLVER A NIVELES', '#00FFFF', false, exit]
        ]);
    }
    function togglePause() {
        if (!S || S.over) return;
        S.paused = !S.paused; keys.clear();
        if (S.paused) showOverlay('PAUSA', 'FASE 2 · ' + String(C.nombre).toUpperCase(), '#E8C27A', [
            ['CONTINUAR', '#33FF66', true, togglePause],
            ['REINICIAR', '#FFD700', false, restart],
            ['VOLVER A NIVELES', '#00FFFF', false, exit]
        ]);
        else hideOverlay();
    }
    function restart() { hideOverlay(); keys.clear(); S = newState(); text(S.player.x, S.player.y - 90, String(C.nombre).toUpperCase(), '#FFD700', 30); }
    function exit() { hideOverlay(); keys.clear(); S = null; api.onExit(); }

    function showOverlay(title, sub, color, buttons) {
        hideOverlay();
        overlay = document.createElement('div');
        overlay.style.cssText = 'position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);z-index:40;background:rgba(20,12,4,0.95);padding:28px 36px;border-radius:14px;border:3px solid ' + color + ';text-align:center;font-family:Orbitron,Segoe UI,sans-serif;min-width:380px;box-shadow:0 0 40px ' + color + '55;';
        overlay.innerHTML = '<h2 style="margin:0 0 6px;color:' + color + ';letter-spacing:3px;">' + title + '</h2><p style="color:#E8D9B0;margin:0 0 18px;font-size:13px;letter-spacing:1px;">' + sub + '</p>';
        const box = document.createElement('div'); box.style.cssText = 'display:flex;flex-direction:column;gap:10px;';
        buttons.forEach(([t, c, filled, fn]) => {
            const b = document.createElement('button'); b.textContent = t;
            b.style.cssText = 'padding:13px 18px;font-family:inherit;font-size:15px;font-weight:700;letter-spacing:2px;border-radius:10px;cursor:pointer;border:2px solid ' + (filled ? '#FFFFFF' : c) + ';background:' + (filled ? c : '#1a1208') + ';color:' + (filled ? '#120a02' : c) + ';';
            b.addEventListener('click', fn); box.appendChild(b);
        });
        overlay.appendChild(box);
        (canvas.parentElement || document.body).appendChild(overlay);
    }
    function hideOverlay() { if (overlay) { overlay.remove(); overlay = null; } }

    // ---------- Bucle ----------
    function update() {
        if (!S || S.paused) return;
        S.t++;
        // escala: el ancho de la arena (1000) entra completo; alto mínimo visible 700
        S.scale = Math.min(canvas.width / W, canvas.height / 700);
        S.offX = (canvas.width - W * S.scale) / 2;
        S.viewH = canvas.height / S.scale;
        if (S.hintT > 0) S.hintT--;
        if (!S.over) { updatePlayer(); updateBoss(); updateObjects(); updateMummies(); updatePickups(); }
        else if (S.boss.dead) updateBoss();
        // arriba la cámara baja al jugador en la pantalla para mostrar la cara completa del Faraón
        const close = Math.max(0, Math.min(1, (1150 - S.player.y) / 400));
        const ratio = 0.58 + 0.27 * close;
        const target = Math.max(0, Math.min(H - S.viewH, S.player.y - S.viewH * ratio));
        S.camY += (target - S.camY) * 0.1;
        S.particles.forEach(q => { q.x += q.vx; q.y += q.vy; q.vy += 0.12; q.life--; });
        S.particles = S.particles.filter(q => q.life > 0);
        S.texts.forEach(q => { q.y -= 0.7; q.life--; });
        S.texts = S.texts.filter(q => q.life > 0);
        S.dust.forEach(d => { d.x += d.s * 1.2; d.y += Math.sin((S.t + d.x) / 40) * 0.3; if (d.x > W + 20) d.x = -20; });
    }

    // ---------- Dibujo ----------
    function draw() {
        if (!S) { ctx.fillStyle = '#1a0f05'; ctx.fillRect(0, 0, canvas.width, canvas.height); return; }
        const sc = S.scale;
        // Cielo del desierto (pantalla completa)
        const g = ctx.createLinearGradient(0, 0, 0, canvas.height);
        const k = S.camY / (H - S.viewH || 1);
        g.addColorStop(0, k < 0.5 ? '#3B1C5A' : '#FF8A3D'); g.addColorStop(0.55, '#FFB257'); g.addColorStop(1, '#FFE0A3');
        ctx.fillStyle = g; ctx.fillRect(0, 0, canvas.width, canvas.height);
        // Sol
        ctx.save(); ctx.fillStyle = 'rgba(255, 240, 180, 0.85)'; ctx.shadowColor = '#FFE38A'; ctx.shadowBlur = 60;
        ctx.beginPath(); ctx.arc(canvas.width * 0.82, canvas.height * 0.22 - S.camY * 0.03, 70 * sc, 0, Math.PI * 2); ctx.fill(); ctx.restore();
        // Pirámides y dunas lejanas (parallax)
        ctx.save(); ctx.translate(0, -S.camY * 0.08 * sc);
        ctx.fillStyle = 'rgba(190, 110, 50, 0.55)';
        [[0.12, 0.7, 260], [0.3, 0.75, 180], [0.9, 0.72, 300]].forEach(([px, py, s]) => { const x = canvas.width * px, y = canvas.height * py + 300 * sc; ctx.beginPath(); ctx.moveTo(x - s * sc, y); ctx.lineTo(x, y - s * 0.75 * sc); ctx.lineTo(x + s * sc, y); ctx.fill(); });
        ctx.restore();

        ctx.save(); ctx.translate(S.offX, 0); ctx.scale(sc, sc); ctx.translate(0, -S.camY);
        // Columnas laterales con jeroglíficos
        drawWalls();
        drawPharaoh();
        // Plataformas de arenisca
        PLATFORMS.forEach(drawPlatform);
        // Suelo
        ctx.fillStyle = '#E2B062'; ctx.fillRect(-400, FLOOR, W + 800, 200);
        ctx.fillStyle = '#F2CB82'; ctx.fillRect(-400, FLOOR, W + 800, 8);
        // Láseres de los ojos
        drawLaser();
        // Objetos, momias, pickups, jugador
        S.objects.forEach(drawObject);
        S.pickups.forEach(drawAnkh);
        S.mummies.forEach(drawMummy);
        drawRobot();
        // Partículas y polvo
        S.particles.forEach(q => { ctx.globalAlpha = Math.min(1, q.life / 15); ctx.fillStyle = q.color; ctx.fillRect(q.x - 3, q.y - 3, 6, 6); });
        ctx.globalAlpha = 0.35; ctx.fillStyle = '#FFF2D0'; S.dust.forEach(d => ctx.fillRect(d.x, d.y, 2.5 * d.s, 2.5 * d.s)); ctx.globalAlpha = 1;
        S.texts.forEach(q => { ctx.globalAlpha = Math.min(1, q.life / 15); ctx.fillStyle = q.color; ctx.font = 'bold ' + q.size + 'px sans-serif'; ctx.textAlign = 'center'; ctx.strokeStyle = 'rgba(0,0,0,0.6)'; ctx.lineWidth = 4; ctx.strokeText(q.t, q.x, q.y); ctx.fillText(q.t, q.x, q.y); });
        ctx.globalAlpha = 1;
        ctx.restore();
        drawHUD();
    }

    function drawWalls() {
        [[-400, 0], [W, 0]].forEach(([x]) => {
            ctx.fillStyle = '#B97F3E'; ctx.fillRect(x, 0, 400, H + 200);
            ctx.strokeStyle = 'rgba(90, 50, 20, 0.5)'; ctx.lineWidth = 2;
            for (let y = 0; y < H; y += 60) { ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + 400, y); ctx.stroke(); }
            ctx.fillStyle = 'rgba(70, 35, 10, 0.55)';
            for (let y = 30; y < H; y += 120) {
                const cx = x === W ? W + 40 : -40;
                ctx.beginPath(); ctx.ellipse(cx, y, 9, 14, 0, 0, Math.PI * 2); ctx.fill();          // ojo/óvalo
                ctx.fillRect(cx - 3, y + 24, 6, 26); ctx.fillRect(cx - 12, y + 60, 24, 5);             // símbolos
            }
        });
        ctx.fillStyle = '#8A5A28'; ctx.fillRect(-8, 0, 8, H + 200); ctx.fillRect(W, 0, 8, H + 200);
    }

    function drawPlatform(pl) {
        ctx.fillStyle = '#C98F4A'; ctx.fillRect(pl.x, pl.y, pl.w, 26);
        ctx.fillStyle = '#F0C27A'; ctx.fillRect(pl.x, pl.y, pl.w, 6);
        ctx.strokeStyle = 'rgba(110, 65, 25, 0.55)'; ctx.lineWidth = 2;
        for (let x = pl.x + 40; x < pl.x + pl.w; x += 48) { ctx.beginPath(); ctx.moveTo(x, pl.y + 6); ctx.lineTo(x, pl.y + 26); ctx.stroke(); }
        ctx.fillStyle = 'rgba(0,0,0,0.18)'; ctx.fillRect(pl.x + 4, pl.y + 26, pl.w - 8, 6);
    }

    function drawPharaoh() {
        const b = S.boss, cx = HEAD.x, cy = HEAD.y, P = pose();
        // posición del jugador en el sistema de dibujo del faraón (para que los ojos lo sigan bien)
        const p = { x: HEAD.x + (S.player.x - P.x) / P.s, y: HEAD.y + (S.player.y - P.y) / P.s };
        ctx.save();
        ctx.translate(P.x, P.y); ctx.scale(P.s, P.s); ctx.translate(-HEAD.x, -HEAD.y);
        ctx.globalAlpha = 1 - 0.3 * P.k;     // a lo lejos se ve un poco brumoso
        if (b.dead) { ctx.globalAlpha = Math.max(0, 1 - b.deathT / 150); ctx.translate(rand(-4, 4), b.deathT * 1.5); }
        // Tocado (nemes) con rayas
        ctx.beginPath();
        ctx.moveTo(cx - 150, cy - 230); ctx.quadraticCurveTo(cx, cy - 330, cx + 150, cy - 230);
        ctx.lineTo(cx + 270, cy + 40); ctx.lineTo(cx + 230, cy + 260); ctx.lineTo(cx + 150, cy + 260);
        ctx.lineTo(cx + 140, cy - 60); ctx.lineTo(cx - 140, cy - 60);
        ctx.lineTo(cx - 150, cy + 260); ctx.lineTo(cx - 230, cy + 260); ctx.lineTo(cx - 270, cy + 40); ctx.closePath();
        ctx.fillStyle = '#E8B934'; ctx.fill();
        ctx.save(); ctx.clip();
        ctx.fillStyle = '#1F4FA8';
        for (let i = -12; i < 14; i++) { ctx.beginPath(); ctx.moveTo(cx + i * 40, cy - 340); ctx.lineTo(cx + i * 40 + 18, cy - 340); ctx.lineTo(cx + i * 40 + 18 + (i * 6), cy + 300); ctx.lineTo(cx + i * 40 + (i * 6), cy + 300); ctx.fill(); }
        ctx.restore();
        ctx.strokeStyle = '#7A5A10'; ctx.lineWidth = 4; ctx.stroke();
        // Cara
        ctx.fillStyle = b.flash > 0 ? '#FFFFFF' : (b.phase2 ? '#B9774A' : '#C68E4E');
        ctx.beginPath(); ctx.ellipse(cx, cy + 10, 140, 190, 0, 0, Math.PI * 2); ctx.fill();
        ctx.strokeStyle = '#7A4A20'; ctx.lineWidth = 3; ctx.stroke();
        // Banda dorada y cobra (uraeus)
        ctx.fillStyle = '#F5C542'; ctx.fillRect(cx - 145, cy - 175, 290, 26);
        ctx.fillStyle = '#1F4FA8'; for (let i = 0; i < 7; i++) ctx.fillRect(cx - 135 + i * 42, cy - 171, 18, 18);
        ctx.fillStyle = '#F5C542'; ctx.beginPath(); ctx.ellipse(cx, cy - 200, 20, 34, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#D93030'; ctx.beginPath(); ctx.arc(cx, cy - 210, 7, 0, Math.PI * 2); ctx.fill();
        // Ojos que te siguen
        const glowing = b.laser && b.laser.t <= C.jefe.laser_aviso;
        EYES.forEach((e, i) => {
            ctx.save();
            ctx.fillStyle = b.phase2 || glowing ? '#FFD0D0' : '#FFFFFF';
            if (glowing) { ctx.shadowColor = '#FF2244'; ctx.shadowBlur = 20 + (b.laser.t % 10) * 2; }
            ctx.beginPath(); ctx.ellipse(e.x, e.y, 44, 22, 0, 0, Math.PI * 2); ctx.fill(); ctx.shadowBlur = 0;
            // delineado egipcio
            ctx.strokeStyle = '#111'; ctx.lineWidth = 6; ctx.stroke();
            ctx.beginPath(); ctx.moveTo(e.x + (i ? 40 : -40), e.y); ctx.lineTo(e.x + (i ? 78 : -78), e.y + 10); ctx.stroke();
            const a = Math.atan2(p.y - e.y, p.x - e.x), d = Math.min(18, Math.hypot(p.x - e.x, p.y - e.y) / 30);
            ctx.fillStyle = glowing || b.phase2 ? '#FF1133' : '#2A1A0A';
            ctx.beginPath(); ctx.arc(e.x + Math.cos(a) * d, e.y + Math.sin(a) * d * 0.6, 13, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#000'; ctx.beginPath(); ctx.arc(e.x + Math.cos(a) * d, e.y + Math.sin(a) * d * 0.6, 6, 0, Math.PI * 2); ctx.fill();
            ctx.restore();
            // ceja
            ctx.strokeStyle = '#111'; ctx.lineWidth = 7; ctx.beginPath();
            ctx.moveTo(e.x - 46, e.y - 38 + (b.phase2 ? (i ? -8 : 8) : 0)); ctx.lineTo(e.x + 46, e.y - 38 + (b.phase2 ? (i ? 8 : -8) : 0)); ctx.stroke();
        });
        // Nariz y boca
        ctx.strokeStyle = '#7A4A20'; ctx.lineWidth = 4;
        ctx.beginPath(); ctx.moveTo(cx, cy - 10); ctx.lineTo(cx - 14, cy + 60); ctx.lineTo(cx + 12, cy + 64); ctx.stroke();
        ctx.lineWidth = 6; ctx.beginPath();
        if (b.phase2) { ctx.moveTo(cx - 50, cy + 120); ctx.quadraticCurveTo(cx, cy + 95, cx + 50, cy + 120); }
        else { ctx.moveTo(cx - 45, cy + 110); ctx.lineTo(cx + 45, cy + 110); }
        ctx.stroke();
        // Barba postiza
        ctx.fillStyle = '#E8B934'; ctx.fillRect(cx - 26, cy + 190, 52, 70);
        ctx.fillStyle = '#1F4FA8'; for (let y = cy + 200; y < cy + 260; y += 16) ctx.fillRect(cx - 26, y, 52, 7);
        ctx.restore();
    }

    function drawLaser() {
        const b = S.boss; if (!b.laser || b.dead) return;
        const J = C.jefe;
        EYES.forEach((_, i) => {
            const e = eyePos(i), a = b.laser.angles[i], x2 = e.x + Math.cos(a) * 2400, y2 = e.y + Math.sin(a) * 2400;
            ctx.save(); ctx.lineCap = 'round';
            if (b.laser.t <= J.laser_aviso) {
                ctx.globalAlpha = 0.3 + 0.5 * (Math.floor(b.laser.t / 5) % 2);
                ctx.strokeStyle = '#FF2244'; ctx.lineWidth = 3; ctx.setLineDash([14, 10]);
                ctx.beginPath(); ctx.moveTo(e.x, e.y); ctx.lineTo(x2, y2); ctx.stroke();
            } else {
                ctx.shadowColor = '#FF2244'; ctx.shadowBlur = 30;
                ctx.strokeStyle = 'rgba(255, 34, 68, 0.5)'; ctx.lineWidth = 42; ctx.beginPath(); ctx.moveTo(e.x, e.y); ctx.lineTo(x2, y2); ctx.stroke();
                ctx.strokeStyle = '#FF2244'; ctx.lineWidth = 20; ctx.beginPath(); ctx.moveTo(e.x, e.y); ctx.lineTo(x2, y2); ctx.stroke();
                ctx.shadowBlur = 0; ctx.strokeStyle = '#FFF2A8'; ctx.lineWidth = 7; ctx.beginPath(); ctx.moveTo(e.x, e.y); ctx.lineTo(x2, y2); ctx.stroke();
            }
            ctx.restore();
        });
    }

    function drawObject(o) {
        ctx.save(); ctx.translate(o.x, o.y); ctx.rotate(o.rot);
        if (o.kind === 'vasija') {
            ctx.fillStyle = '#B5651D'; ctx.beginPath(); ctx.ellipse(0, 4, 15, 18, 0, 0, Math.PI * 2); ctx.fill();
            ctx.fillRect(-7, -20, 14, 10); ctx.fillStyle = '#1F4FA8'; ctx.fillRect(-15, 0, 30, 5);
        } else if (o.kind === 'escarabajo') {
            ctx.fillStyle = '#1FB5A8'; ctx.beginPath(); ctx.ellipse(0, 0, 16, 20, 0, 0, Math.PI * 2); ctx.fill();
            ctx.strokeStyle = '#0A5A55'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(0, -18); ctx.lineTo(0, 18); ctx.stroke();
            ctx.fillStyle = '#0A5A55'; ctx.beginPath(); ctx.arc(0, -20, 7, 0, Math.PI * 2); ctx.fill();
        } else {
            ctx.fillStyle = '#D9A55B'; ctx.fillRect(-17, -17, 34, 34);
            ctx.strokeStyle = '#8A5A28'; ctx.lineWidth = 3; ctx.strokeRect(-17, -17, 34, 34);
            ctx.beginPath(); ctx.moveTo(-17, 0); ctx.lineTo(17, 0); ctx.stroke();
        }
        ctx.restore();
    }

    function drawAnkh(k) {
        ctx.save(); ctx.translate(k.x, k.y + Math.sin(k.t / 10) * 3);
        ctx.strokeStyle = '#33FF66'; ctx.lineWidth = 5; ctx.shadowColor = '#33FF66'; ctx.shadowBlur = 12;
        ctx.beginPath(); ctx.ellipse(0, -10, 7, 9, 0, 0, Math.PI * 2); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(0, -1); ctx.lineTo(0, 16); ctx.moveTo(-10, 3); ctx.lineTo(10, 3); ctx.stroke();
        ctx.restore();
    }

    function drawMummy(m) {
        ctx.save(); ctx.translate(m.x, m.y);
        if (m.rise > 0) { const p = 1 - m.rise / 40; ctx.beginPath(); ctx.rect(-40, -60, 80, 92); ctx.clip(); ctx.translate(0, (1 - p) * 64); }
        const walk = Math.sin(m.t / 6) * 6;
        ctx.fillStyle = m.flash > 0 ? '#FFFFFF' : '#E8D9B0';
        ctx.fillRect(-10 + walk * 0.3, 10, 8, 22); ctx.fillRect(2 - walk * 0.3, 10, 8, 22);       // piernas
        ctx.fillRect(-14, -18, 28, 32);                                                           // cuerpo
        ctx.fillRect(m.dir > 0 ? 6 : -30, -12, 24, 8);                                           // brazos estirados
        ctx.fillRect(m.dir > 0 ? 6 : -30, -2, 24, 8);
        ctx.beginPath(); ctx.arc(0, -28, 13, 0, Math.PI * 2); ctx.fill();                         // cabeza
        ctx.strokeStyle = 'rgba(120, 95, 60, 0.7)'; ctx.lineWidth = 2;                              // vendas
        for (let y = -36; y < 30; y += 7) { ctx.beginPath(); ctx.moveTo(-14, y); ctx.lineTo(14, y + 3); ctx.stroke(); }
        ctx.fillStyle = '#FF3355'; ctx.beginPath(); ctx.arc(m.dir * 4 - 4, -30, 2.5, 0, Math.PI * 2); ctx.arc(m.dir * 4 + 4, -30, 2.5, 0, Math.PI * 2); ctx.fill();
        ctx.restore();
        if (m.rise <= 0 && m.hp < m.maxHp) { ctx.fillStyle = 'rgba(0,0,0,0.5)'; ctx.fillRect(m.x - 18, m.y - 52, 36, 4); ctx.fillStyle = '#FF3355'; ctx.fillRect(m.x - 18, m.y - 52, 36 * m.hp / m.maxHp, 4); }
    }

    function starPath(cx, cy, rO, rI) {
        ctx.beginPath();
        for (let i = 0; i < 10; i++) { const r = i % 2 ? rI : rO, a = -Math.PI / 2 + i * Math.PI / 5; ctx.lineTo(cx + Math.cos(a) * r, cy + Math.sin(a) * r); }
        ctx.closePath();
    }

    function drawRobot() {
        const p = S.player;
        if (p.inv > 0 && Math.floor(p.inv / 4) % 2 === 0) return;
        ctx.save(); ctx.translate(p.x, p.y);
        const squash = p.charging ? 1 - 0.25 * (p.charge / C.jugador.carga_frames) : 1;
        ctx.translate(0, 35); ctx.scale(1, squash); ctx.translate(0, -35);
        const f = p.facing;
        // piernas
        const walk = p.onGround && Math.abs(p.vx) > 0.5 ? Math.sin(S.t / 4) * 5 : 0;
        ctx.fillStyle = '#5E6773'; ctx.fillRect(-12 + walk, 14, 9, 21); ctx.fillRect(3 - walk, 14, 9, 21);
        ctx.fillStyle = '#3A4048'; ctx.fillRect(-14 + walk, 31, 13, 5); ctx.fillRect(1 - walk, 31, 13, 5);
        // cuerpo metálico
        ctx.fillStyle = '#A9B3C1'; ctx.fillRect(-17, -14, 34, 30);
        ctx.strokeStyle = '#6B7584'; ctx.lineWidth = 2; ctx.strokeRect(-17, -14, 34, 30);
        ctx.fillStyle = p.sword > 0 ? '#7DF9FF' : '#33FF66'; ctx.beginPath(); ctx.arc(0, 0, 5, 0, Math.PI * 2); ctx.fill();   // luz del pecho
        ctx.fillStyle = '#6B7584'; [[-13, -10], [13, -10], [-13, 12], [13, 12]].forEach(([x, y]) => { ctx.beginPath(); ctx.arc(x, y, 1.8, 0, Math.PI * 2); ctx.fill(); });
        // brazo (se estira al pegar)
        let ax = f * 10, ay = 0;
        if (p.atk > 0) { const ext = p.atk > 7 ? (14 - p.atk) / 7 : p.atk / 7; ax = Math.cos(p.atkDir) * (14 + 26 * ext); ay = Math.sin(p.atkDir) * (14 + 26 * ext); }
        ctx.strokeStyle = '#8994A3'; ctx.lineWidth = 7; ctx.lineCap = 'round';
        ctx.beginPath(); ctx.moveTo(f * 14, -6); ctx.lineTo(f * 14 + ax * 0.6, -6 + ay * 0.6); ctx.stroke();
        ctx.fillStyle = '#5E6773'; ctx.beginPath(); ctx.arc(f * 14 + ax * 0.6, -6 + ay * 0.6, 7, 0, Math.PI * 2); ctx.fill();
        // espada
        if (p.sword > 0) {
            const a = p.atk > 0 ? p.atkDir : (f > 0 ? -0.9 : Math.PI + 0.9);
            const hx = f * 14 + ax * 0.6, hy = -6 + ay * 0.6;
            ctx.save(); ctx.translate(hx, hy); ctx.rotate(a);
            ctx.shadowColor = '#7DF9FF'; ctx.shadowBlur = 18; ctx.fillStyle = '#E6FDFF';
            ctx.beginPath(); ctx.moveTo(6, -4); ctx.lineTo(62, -2); ctx.lineTo(70, 0); ctx.lineTo(62, 2); ctx.lineTo(6, 4); ctx.closePath(); ctx.fill();
            ctx.shadowBlur = 0; ctx.fillStyle = '#FFD700'; ctx.fillRect(2, -9, 5, 18); ctx.fillStyle = '#8A5A28'; ctx.fillRect(-10, -3, 12, 6);
            ctx.restore();
        }
        // cabeza de estrella con cara
        ctx.save(); ctx.translate(0, -36); ctx.rotate(Math.sin(S.t / 30) * 0.06);
        starPath(0, 0, 25, 12); ctx.fillStyle = '#FFD54A'; ctx.shadowColor = '#FFD54A'; ctx.shadowBlur = 10; ctx.fill();
        ctx.shadowBlur = 0; ctx.strokeStyle = '#C98F00'; ctx.lineWidth = 2; ctx.stroke();
        ctx.fillStyle = '#2A1A0A';
        ctx.beginPath(); ctx.ellipse(f * 3 - 6, -1, 2.6, 4, 0, 0, Math.PI * 2); ctx.ellipse(f * 3 + 6, -1, 2.6, 4, 0, 0, Math.PI * 2); ctx.fill();
        ctx.strokeStyle = '#2A1A0A'; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(f * 3, 4, 4, 0.2, Math.PI - 0.2); ctx.stroke();
        // antena
        ctx.strokeStyle = '#8994A3'; ctx.beginPath(); ctx.moveTo(0, -25); ctx.lineTo(0, -34); ctx.stroke();
        ctx.fillStyle = '#FF3355'; ctx.beginPath(); ctx.arc(0, -36, 3, 0, Math.PI * 2); ctx.fill();
        ctx.restore();
        ctx.restore();

        // Estela del golpe
        if (p.atk > 3 && p.atk <= 11) {
            const a = attackCircle();
            ctx.save(); ctx.globalAlpha = 0.5; ctx.strokeStyle = p.sword > 0 ? '#7DF9FF' : (p.combo === 3 ? '#FFD700' : '#FFFFFF'); ctx.lineWidth = p.sword > 0 ? 8 : 5;
            ctx.beginPath(); ctx.arc(p.x, p.y, Math.hypot(a.x - p.x, a.y - p.y) + 10, p.atkDir - 0.7, p.atkDir + 0.7); ctx.stroke(); ctx.restore();
        }
        // Barra de carga del salto
        if (p.charging) {
            const c = p.charge / C.jugador.carga_frames;
            ctx.fillStyle = 'rgba(0,0,0,0.5)'; ctx.fillRect(p.x - 25, p.y + 44, 50, 6);
            ctx.fillStyle = c >= 1 ? '#FF3355' : '#FFD700'; ctx.fillRect(p.x - 25, p.y + 44, 50 * c, 6);
        }
    }

    function drawHUD() {
        const p = S.player, b = S.boss, cw = canvas.width;
        ctx.save();
        // Barra del Faraón
        const bw = Math.min(520, cw * 0.6), bx = (cw - bw) / 2;
        ctx.fillStyle = 'rgba(30, 15, 5, 0.85)'; ctx.fillRect(bx, 14, bw, 18);
        ctx.fillStyle = b.phase2 ? '#FF3355' : '#F5C542'; ctx.fillRect(bx + 2, 16, (bw - 4) * Math.max(0, b.hp / b.maxHp), 14);
        ctx.strokeStyle = '#F5C542'; ctx.lineWidth = 2; ctx.strokeRect(bx, 14, bw, 18);
        ctx.fillStyle = '#FFF2D0'; ctx.font = 'bold 12px sans-serif'; ctx.textAlign = 'center';
        ctx.fillText(`${C.jefe.nombre}${b.phase2 ? ' (FURIOSO)' : ''}: ${Math.max(0, Math.ceil(b.hp))} / ${b.maxHp}`, cw / 2, 27);
        // Vida del jugador
        const hs = 22;
        for (let i = 0; i < p.maxHp; i++) api.drawIcon(ctx, i < p.hp ? 'heart' : 'heartEmpty', 24 + i * (hs + 4), canvas.height - 30, hs);
        // Espada
        ctx.textAlign = 'left'; ctx.font = 'bold 14px sans-serif';
        const swTxt = p.sword > 0 ? `ESPADA: ${(p.sword / 60).toFixed(1)}s` : (p.swordCd > 0 ? `ESPADA: ${Math.ceil(p.swordCd / 60)}s` : '[R] ESPADA LISTA');
        ctx.fillStyle = p.sword > 0 ? '#7DF9FF' : (p.swordCd > 0 ? '#999' : '#FFD700');
        ctx.fillText(swTxt, 24, canvas.height - 52);
        if (p.hitCombo >= 2) { ctx.fillStyle = '#FFD700'; ctx.font = 'bold 20px sans-serif'; ctx.fillText(`COMBO x${p.hitCombo}`, 24, canvas.height - 76); }
        // Fase
        ctx.textAlign = 'right'; ctx.font = 'bold 13px sans-serif'; ctx.fillStyle = '#FFF2D0';
        ctx.fillText(`FASE 2 · ${String(C.nombre).toUpperCase()}`, cw - 20, 27);
        ctx.fillText('[ESC] PAUSA', cw - 20, 45);
        // Ayuda los primeros segundos
        if (S.t < 420) {
            ctx.globalAlpha = Math.min(1, (420 - S.t) / 60);
            ctx.fillStyle = 'rgba(30, 15, 5, 0.8)'; ctx.fillRect(cw / 2 - 270, canvas.height - 120, 540, 76);
            ctx.fillStyle = '#FFF2D0'; ctx.textAlign = 'center'; ctx.font = 'bold 13px sans-serif';
            ctx.fillText('A/D: CAMINAR  ·  MANTÉN ESPACIO/W: CARGAR SALTO (suelta para saltar)', cw / 2, canvas.height - 96);
            ctx.fillText('CLICK o J: GOLPE (3 seguidos = COMBO)  ·  R: ESPADA 15 s', cw / 2, canvas.height - 76);
            ctx.fillText('Sube por las areniscas y golpea al Faraón en la cara', cw / 2, canvas.height - 56);
        }
        ctx.restore();
    }

    // ---------- Registro ----------
    window.FASES_REG = window.FASES_REG || {};
    window.FASES_REG[ID] = {
        start(config, theApi) {
            api = theApi; C = merge(DEFAULTS, config || {});
            canvas = api.canvas; ctx = api.ctx;
            setupListeners();
            keys.clear(); hideOverlay();
            S = newState();
            text(S.player.x, S.player.y - 90, String(C.nombre).toUpperCase(), '#FFD700', 30);
        },
        update, draw,
        stop() { hideOverlay(); S = null; keys.clear(); },
        estado() { return S; }          // para pruebas / depuración
    };
})();
