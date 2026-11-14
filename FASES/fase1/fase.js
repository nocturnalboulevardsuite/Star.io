// ============================================================
// FASE 1 · LA PIRÁMIDE
// Corredor infinito en 3 carriles (estilo Subway Surfers) dentro de los pasillos
// de una pirámide. Salta trampas, agáchate, esquiva flechas... y a los 30 segundos
// despierta una momia que te persigue e intenta atraparte. Llega a la salida.
//
// app.py carga este archivo solo desde FASES/<carpeta>/fase.js.
// Los números para balancear están en config.json (misma carpeta).
// ============================================================
(function () {
    const ID = window.__FASE_ID__ || 'fase1';

    const DEFAULTS = {
        nombre: "La Pirámide",
        duracion_s: 90,            // segundos hasta llegar a la salida
        momia_aparece_s: 30,       // cuándo despierta la momia
        vidas: 3,
        velocidad_inicial: 11, velocidad_max: 22, aceleracion: 0.09,
        separacion_s: 1.05,        // tiempo entre filas de trampas
        momia: { agarre_espera_min_s: 5, agarre_espera_max_s: 8, agarre_aviso_s: 1.1, "acercamiento_golpe": 35, "acercamiento_agarre": 45, "recuperacion_por_s": 4 }
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

    // ---------- Mundo 3D falso ----------
    const LANE_W = 2.2, HALF_W = 3.6, WALL_H = 5.2, CAM_H = 3.6, Z_PLAYER = 6.5, FAR = 90;
    const GRAV = 32, JUMP_V = 11.5, SLIDE_T = 0.7;

    let api = null, C = null, ctx = null, canvas = null, S = null, overlay = null, listenersReady = false;
    const rand = (a, b) => a + Math.random() * (b - a);

    // ======================================================
    // SPRITE PIXEL ART DE ESPALDAS (soldado con cabeza de estrella)
    // ======================================================
    const PAL = { K: '#1A1410', Y: '#FFD54A', y: '#E0A800', R: '#D8312B', r: '#9A1F1B', M: '#A9B3C1', m: '#6B7584', V: '#6B7A35', v: '#4A5524', B: '#6B4423', G: '#E8B934', P: '#B59A62', p: '#8A7448', O: '#3A2A1E' };
    const SPR_HEAD = [
        "........KK........", ".......KYYK.......", "......KYYYYK......", ".KKKKKKYYYYKKKKKK.", ".KYYYYYYYYYYYYYYK.",
        "rrKRRRRRRRRRRRRKrr", "..rKyYYYYYYYYYyKr.", "....KYYYYYYYYYK...", "....KYyYYYYYyYK...", "...KYYYYKKYYYYK...",
        "...KYYYK..KYYYK...", "..KYYK......KYYK..", "..KKK........KKK.."
    ];
    const SPR_BODY = [
        ".....KKKKKKKK.....", "...KKVVVVVVVVKK...", "..KMKvvvvvvvvKMK..", "..KMKvGBBBBGvKMK..",
        "..KMKvvvvvvvvKMK..", "...KKBBBBBBBBKK...", "....KPPPPPPPPK...."
    ];
    const SPR_LEGS = {
        runA: ["....KPPK.KPPK.....", "....KPPK.KPPK.....", "....KOOK.KpPK.....", "....KKKK.KOOOK....", "..........KKKKK...", ".................."],
        runB: [".....KPPK.KPPK....", ".....KPPK.KPPK....", ".....KpPK.KOOK....", "....KOOOK.KKKK....", "...KKKKK..........", ".................."],
        jump: ["....KPPPPPPPPK....", "....KOOK..KOOK....", "....KKKK..KKKK....", "..................", "..................", ".................."]
    };
    function runs(rows, off) {
        const out = [];
        rows.forEach((row, r) => {
            row = (row + "..................").slice(0, 18);
            let c = 0;
            while (c < 18) { const ch = row[c]; if (ch === '.') { c++; continue; } let len = 1; while (c + len < 18 && row[c + len] === ch) len++; out.push({ c, r: r + off, len, col: PAL[ch] }); c += len; }
        });
        return out;
    }
    const RUNS = { head: runs(SPR_HEAD, 0), body: runs(SPR_BODY, 11), runA: runs(SPR_LEGS.runA, 18), runB: runs(SPR_LEGS.runB, 18), jump: runs(SPR_LEGS.jump, 18) };
    function drawRuns(list, ox, oy, px) { for (const q of list) { ctx.fillStyle = q.col; ctx.fillRect(Math.round(ox + q.c * px), Math.round(oy + q.r * px), Math.ceil(q.len * px), Math.ceil(px)); } }

    // ======================================================
    // ESTADO
    // ======================================================
    function newState() {
        const rissos = api.isRissos();
        return {
            t: 0, dist: 0, speed: C.velocidad_inicial, score: 0, gems: 0,
            lane: 0, x: 0, y: 0, vy: 0, slide: 0, inv: 0, hearts: rissos ? 9 : C.vidas, maxHearts: rissos ? 9 : C.vidas, stumble: 0,
            obstacles: [], gemsList: [], nextRow: 30, particles: [], texts: [],
            mummy: { active: false, gap: 100, grabT: 0, grab: null, intro: 0 },
            paused: false, over: false, exit: 0, lastTime: performance.now(), shake: 0, rissos
        };
    }

    // ---------- Entrada ----------
    function setupListeners() {
        if (listenersReady) return; listenersReady = true;
        window.addEventListener('keydown', e => {
            if (!api || !api.active() || !S) return;
            if (['Space', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.code)) e.preventDefault();
            if (e.repeat) return;
            if (e.code === 'Escape') { togglePause(); return; }
            if (S.paused || S.over) return;
            if (e.code === 'KeyA' || e.code === 'ArrowLeft') changeLane(-1);
            if (e.code === 'KeyD' || e.code === 'ArrowRight') changeLane(1);
            if (e.code === 'KeyW' || e.code === 'ArrowUp' || e.code === 'Space') jump();
            if (e.code === 'KeyS' || e.code === 'ArrowDown') slide();
        });
    }
    function changeLane(d) { const n = Math.max(-1, Math.min(1, S.lane + d)); if (n !== S.lane) { S.lane = n; api.playAbilitySfx('whoosh'); } }
    function jump() { if (S.y <= 0.01) { S.vy = JUMP_V; S.slide = 0; api.playAbilitySfx('whoosh'); } }
    function slide() { if (S.y > 0.01) S.vy = -18; S.slide = SLIDE_T; }

    function text(t, color, size, life) { S.texts.push({ t, color, size: size || 28, life: life || 70, max: life || 70 }); }
    function roar() {
        if (!api.interacted() || api.sfxVol() === 0) return;
        try {
            const ac = api.getAudioCtx(), t = ac.currentTime, dur = 1.8, v = Math.min(1, api.sfxVol());
            const out = ac.createGain(); out.gain.setValueAtTime(0.0001, t); out.gain.exponentialRampToValueAtTime(v, t + 0.1); out.gain.exponentialRampToValueAtTime(0.0001, t + dur); out.connect(ac.destination);
            const bp = ac.createBiquadFilter(); bp.type = 'bandpass'; bp.frequency.value = 350; bp.Q.value = 1.5; bp.connect(out);
            [0, 13].forEach(det => { const o = ac.createOscillator(); o.type = 'sawtooth'; o.detune.value = det * 10; o.frequency.setValueAtTime(110, t); o.frequency.exponentialRampToValueAtTime(55, t + dur); o.connect(bp); o.start(t); o.stop(t + dur); });
        } catch (e) {}
    }

    // ======================================================
    // TRAMPAS
    // ======================================================
    // valla: saltar · pozo: saltar · viga: agacharse (todo el ancho) · dardos: agacharse (todo el ancho)
    // muro: cambiar de carril · flecha: viene de frente por un carril (cambiar de carril o agacharse)
    function spawnRow() {
        const d = S.dist + FAR;
        const r = Math.random();
        const lanes = [-1, 0, 1];
        const pickLanes = n => { const ls = lanes.slice().sort(() => Math.random() - 0.5); return ls.slice(0, n); };
        let free = lanes.slice();
        if (r < 0.22) { pickLanes(Math.random() < 0.5 ? 2 : 3).forEach(l => S.obstacles.push({ type: 'valla', lane: l, d })); }
        else if (r < 0.36) { pickLanes(Math.random() < 0.6 ? 1 : 2).forEach(l => S.obstacles.push({ type: 'pozo', lane: l, d, len: 2.4 })); }
        else if (r < 0.50) { S.obstacles.push({ type: 'viga', lane: 9, d }); }
        else if (r < 0.70) { const bl = pickLanes(Math.random() < 0.5 ? 1 : 2); bl.forEach(l => S.obstacles.push({ type: 'muro', lane: l, d })); free = lanes.filter(l => !bl.includes(l)); }
        else if (r < 0.85) { const l = Math.random() < 0.6 ? S.lane : lanes[Math.floor(Math.random() * 3)]; S.obstacles.push({ type: 'flecha', lane: l, d: d + 25, fly: 0 }); free = lanes.filter(x => x !== l); }
        else { S.obstacles.push({ type: 'dardos', lane: 9, d }); }
        // escarabajos dorados para puntos en un carril libre
        if (Math.random() < 0.6) { const l = free[Math.floor(Math.random() * free.length)]; for (let i = 0; i < 4; i++) S.gemsList.push({ lane: l, d: d + 4 + i * 2.2, y: 0.6 }); }
    }

    function hit(reason) {
        if (S.inv > 0 || S.over) return;
        S.hearts--; S.inv = 1.3; S.stumble = 0.4; S.shake = 0.35; S.speed = Math.max(C.velocidad_inicial, S.speed * 0.8);
        api.playAbilitySfx('boom');
        text(reason, '#FF3355', 30, 60);
        if (S.mummy.active) S.mummy.gap -= C.momia['acercamiento_golpe'];
        if (S.hearts <= 0 || (S.mummy.active && S.mummy.gap <= 0)) lose();
    }

    function update() {
        if (!S || S.paused) { if (S) S.lastTime = performance.now(); return; }
        const now = performance.now(); let dt = Math.min(0.05, (now - S.lastTime) / 1000); S.lastTime = now;
        if (S.over) { S.particles.forEach(p => { p.x += p.vx * dt; p.y += p.vy * dt; p.life -= dt; }); return; }
        S.t += dt;
        if (S.exit > 0) { S.exit += dt; S.dist += S.speed * dt; if (S.exit > 2.2) win(); return; }

        S.speed = Math.min(C.velocidad_max, S.speed + C.aceleracion * dt);
        S.dist += S.speed * dt; S.score += S.speed * dt;
        if (S.inv > 0) S.inv -= dt; if (S.stumble > 0) S.stumble -= dt; if (S.shake > 0) S.shake -= dt;
        // jugador
        S.x += (S.lane * LANE_W - S.x) * Math.min(1, dt * 14);
        S.vy -= GRAV * dt; S.y += S.vy * dt; if (S.y < 0) { S.y = 0; S.vy = 0; }
        if (S.slide > 0) S.slide -= dt;
        // filas de trampas
        if (S.dist + FAR >= S.nextRow + 0 && S.t < C.duracion_s - 3) { spawnRow(); S.nextRow = S.dist + FAR + S.speed * C.separacion_s * rand(0.85, 1.25); }
        // trampas
        const pl = S.lane, inAir = S.y > 0.85, sliding = S.slide > 0;
        S.obstacles.forEach(o => {
            if (o.type === 'flecha') { const rel = o.d - S.dist; if (rel < 40) { o.d -= 26 * dt; o.fly = 1; } }
            const rel = o.d - S.dist;
            if (o.done || rel > 0.8 || rel < -(o.len || 0.6)) { if (rel < -(o.len || 0.6) - 2) o.dead = true; return; }
            const sameLane = o.lane === 9 || o.lane === Math.round(S.x / LANE_W);
            if (!sameLane) return;
            if (o.type === 'valla' && !inAir) { o.done = true; hit('¡TROPEZASTE!'); }
            if (o.type === 'pozo' && S.y < 0.3) { o.done = true; hit('¡CAÍSTE EN LAS PÚAS!'); }
            if ((o.type === 'viga' || o.type === 'dardos') && !sliding) { o.done = true; hit(o.type === 'viga' ? '¡TE GOLPEASTE LA CABEZA!' : '¡TE DIERON LOS DARDOS!'); }
            if (o.type === 'muro') { o.done = true; hit('¡CHOCASTE!'); }
            if (o.type === 'flecha' && !sliding) { o.done = true; hit('¡FLECHAZO!'); }
        });
        S.obstacles = S.obstacles.filter(o => !o.dead);
        // escarabajos
        S.gemsList.forEach(g => {
            const rel = g.d - S.dist;
            if (rel < 0.6 && rel > -0.6 && g.lane === Math.round(S.x / LANE_W) && Math.abs(S.y + 0.6 - g.y) < 1.2) { g.taken = true; S.gems++; S.score += 25; api.playAbilitySfx('ping'); }
            if (rel < -2) g.taken = true;
        });
        S.gemsList = S.gemsList.filter(g => !g.taken);

        // la momia
        const M = S.mummy, MC = C.momia;
        if (!M.active && S.t >= C.momia_aparece_s) {
            M.active = true; M.gap = 70; M.intro = 2.5; M.grabT = rand(MC.agarre_espera_min_s, MC.agarre_espera_max_s);
            text('¡LA MOMIA DESPERTÓ! ¡CORRE!', '#E8D9B0', 38, 150); roar(); S.shake = 0.6;
        }
        if (M.active) {
            if (M.intro > 0) M.intro -= dt;
            M.gap = Math.min(100, M.gap + MC['recuperacion_por_s'] * dt);
            if (M.grab) {
                M.grab.t += dt;
                if (!M.grab.hit && M.grab.t >= MC.agarre_aviso_s) {
                    M.grab.hit = true;
                    if (Math.round(S.x / LANE_W) === M.grab.lane && S.inv <= 0) {
                        S.hearts--; S.inv = 1.3; M.gap -= MC['acercamiento_agarre']; S.shake = 0.5;
                        text('¡TE AGARRÓ LA MOMIA!', '#FF3355', 34, 70); roar();
                        if (S.hearts <= 0 || M.gap <= 0) lose();
                    } else text('¡ESQUIVADO!', '#33FF66', 26, 40);
                }
                if (M.grab.t > MC.agarre_aviso_s + 0.5) { M.grab = null; M.grabT = rand(MC.agarre_espera_min_s, MC.agarre_espera_max_s); }
            } else if ((M.grabT -= dt) <= 0) {
                M.grab = { t: 0, lane: S.lane, hit: false };
                text('¡TE VA A AGARRAR!', '#FFB257', 28, 50); api.playAbilitySfx('shield');
            }
            if (M.gap <= 0) lose();
        }
        // salida
        if (S.t >= C.duracion_s && S.exit === 0) { S.exit = 0.01; text('¡LA SALIDA!', '#FFE38A', 44, 140); api.playAbilitySfx('shield'); }
        // efectos
        S.particles.forEach(p => { p.x += p.vx * dt; p.y += p.vy * dt; p.life -= dt; }); S.particles = S.particles.filter(p => p.life > 0);
        S.texts.forEach(q => q.life--); S.texts = S.texts.filter(q => q.life > 0);
    }

    // ======================================================
    // DIBUJO (proyección en perspectiva)
    // ======================================================
    let W = 0, H = 0, HZ = 0, F = 0;
    function P(x, y, z) { const s = F / Math.max(0.3, z); return { x: W / 2 + x * s, y: HZ + (CAM_H - y) * s, s }; }
    function quad(a, b, c, d, fill) { ctx.fillStyle = fill; ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.lineTo(c.x, c.y); ctx.lineTo(d.x, d.y); ctx.closePath(); ctx.fill(); }
    const fog = (z, base) => Math.max(0, Math.min(1, 1 - z / FAR)) * base;

    function drawCorridor() {
        const g = ctx.createLinearGradient(0, 0, 0, H);
        g.addColorStop(0, '#120A04'); g.addColorStop(0.4, '#2A1808'); g.addColorStop(1, '#120A04');
        ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
        // luz al fondo (y la salida al final)
        const exitK = S.exit > 0 ? Math.min(1, S.exit / 2) : Math.max(0, (S.t - (C.duracion_s - 8)) / 8) * 0.4;
        const far = P(0, WALL_H / 2, FAR);
        const lg = ctx.createRadialGradient(far.x, far.y, 2, far.x, far.y, 60 + exitK * W);
        lg.addColorStop(0, `rgba(255, 230, 160, ${0.5 + exitK * 0.5})`); lg.addColorStop(1, 'rgba(255, 200, 120, 0)');
        ctx.fillStyle = lg; ctx.fillRect(0, 0, W, H);
        // segmentos de piso, paredes y techo (de lejos a cerca)
        const seg = 4, off = S.dist % (seg * 2);
        for (let z = FAR - off; z > 0.6; z -= seg) {
            const z1 = z, z0 = Math.max(0.6, z - seg), band = Math.floor((S.dist + z) / seg) % 2 === 0;
            const L = fog(z1, 1);
            const shade = (r, gg, b) => `rgb(${Math.round(r * L)}, ${Math.round(gg * L)}, ${Math.round(b * L)})`;
            // piso
            quad(P(-HALF_W, 0, z1), P(HALF_W, 0, z1), P(HALF_W, 0, z0), P(-HALF_W, 0, z0), band ? shade(170, 120, 60) : shade(150, 104, 50));
            // paredes
            quad(P(-HALF_W, 0, z1), P(-HALF_W, WALL_H, z1), P(-HALF_W, WALL_H, z0), P(-HALF_W, 0, z0), band ? shade(140, 92, 44) : shade(126, 82, 38));
            quad(P(HALF_W, 0, z1), P(HALF_W, WALL_H, z1), P(HALF_W, WALL_H, z0), P(HALF_W, 0, z0), band ? shade(140, 92, 44) : shade(126, 82, 38));
            // techo
            quad(P(-HALF_W, WALL_H, z1), P(HALF_W, WALL_H, z1), P(HALF_W, WALL_H, z0), P(-HALF_W, WALL_H, z0), shade(70, 44, 20));
        }
        // líneas de carriles
        ctx.strokeStyle = 'rgba(60, 35, 10, 0.5)'; ctx.lineWidth = 2;
        [-LANE_W / 2, LANE_W / 2].forEach(x => { const a = P(x, 0, FAR), b = P(x, 0, 0.8); ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke(); });
        // jeroglíficos y antorchas en las paredes
        const spacing = 12, o2 = S.dist % spacing;
        for (let z = FAR - o2; z > 1.2; z -= spacing) {
            const idx = Math.floor((S.dist + z) / spacing), L = fog(z, 1);
            [-1, 1].forEach(side => {
                const x = side * HALF_W * 0.995;
                // jeroglíficos
                ctx.fillStyle = `rgba(60, 30, 10, ${0.7 * L})`;
                for (let k = 0; k < 3; k++) { const p = P(x, 1.4 + k * 1.1, z + 3); ctx.beginPath(); ctx.ellipse(p.x, p.y, 0.12 * p.s, 0.2 * p.s, 0, 0, Math.PI * 2); ctx.fill(); const q = P(x, 1.0 + k * 1.1, z + 3); ctx.fillRect(q.x - 0.04 * q.s, q.y - 0.25 * q.s, 0.08 * q.s, 0.28 * q.s); }
                // antorcha
                if ((idx + (side > 0 ? 1 : 0)) % 2 === 0) {
                    const b = P(x, 2.6, z), top = P(x, 3.1, z), fl = Math.sin(S.t * 18 + idx) * 0.06;
                    ctx.strokeStyle = `rgba(80, 50, 20, ${L})`; ctx.lineWidth = Math.max(1, 0.1 * b.s); ctx.beginPath(); ctx.moveTo(b.x, b.y); ctx.lineTo(top.x, top.y); ctx.stroke();
                    const glow = ctx.createRadialGradient(top.x, top.y, 1, top.x, top.y, 1.6 * top.s);
                    glow.addColorStop(0, `rgba(255, 170, 60, ${0.5 * L})`); glow.addColorStop(1, 'rgba(255, 120, 30, 0)');
                    ctx.fillStyle = glow; ctx.beginPath(); ctx.arc(top.x, top.y, 1.6 * top.s, 0, Math.PI * 2); ctx.fill();
                    ctx.fillStyle = `rgba(255, 200, 80, ${L})`; ctx.beginPath(); ctx.ellipse(top.x, top.y - 0.15 * top.s, 0.1 * top.s, (0.22 + fl) * top.s, 0, 0, Math.PI * 2); ctx.fill();
                }
            });
        }
    }

    function laneX(l) { return l * LANE_W; }
    function drawObstacle(o) {
        const z = o.d - S.dist + Z_PLAYER; if (z < 0.7 || z > FAR) return;
        const L = fog(z, 1), lw = LANE_W * 0.46;
        if (o.type === 'valla') {
            const x = laneX(o.lane), a = P(x - lw, 0.8, z), b = P(x + lw, 0, z);
            ctx.fillStyle = `rgb(${200 * L | 0}, ${150 * L | 0}, ${80 * L | 0})`; ctx.fillRect(a.x, a.y, b.x - a.x, b.y - a.y);
            ctx.strokeStyle = `rgba(80,40,10,${L})`; ctx.lineWidth = 2; ctx.strokeRect(a.x, a.y, b.x - a.x, b.y - a.y);
            ctx.fillStyle = `rgb(${190 * L | 0}, ${190 * L | 0}, ${200 * L | 0})`;   // púas
            for (let i = 0; i < 5; i++) { const sx = a.x + (b.x - a.x) * (i + 0.5) / 5, w = (b.x - a.x) / 10; ctx.beginPath(); ctx.moveTo(sx - w, a.y); ctx.lineTo(sx, a.y - (b.y - a.y) * 0.4); ctx.lineTo(sx + w, a.y); ctx.fill(); }
        } else if (o.type === 'pozo') {
            const x = laneX(o.lane), z2 = z + o.len;
            quad(P(x - lw, 0.01, z2), P(x + lw, 0.01, z2), P(x + lw, 0.01, z), P(x - lw, 0.01, z), `rgb(${20 * L | 0}, ${10 * L | 0}, 0)`);
            ctx.fillStyle = `rgba(200, 200, 210, ${L})`;
            for (let i = 0; i < 4; i++) { const p = P(x - lw + (i + 0.5) * lw / 2, 0.01, z + o.len * 0.4), w = 0.12 * p.s; ctx.beginPath(); ctx.moveTo(p.x - w, p.y); ctx.lineTo(p.x, p.y - 0.4 * p.s); ctx.lineTo(p.x + w, p.y); ctx.fill(); }
        } else if (o.type === 'viga') {
            const a = P(-HALF_W, 1.9, z), b = P(HALF_W, 1.25, z);
            ctx.fillStyle = `rgb(${120 * L | 0}, ${78 * L | 0}, ${36 * L | 0})`; ctx.fillRect(a.x, a.y, b.x - a.x, b.y - a.y);
            ctx.fillStyle = `rgba(240, 200, 120, ${0.5 * L})`; ctx.fillRect(a.x, a.y, b.x - a.x, (b.y - a.y) * 0.18);
            ctx.fillStyle = `rgba(40, 20, 5, ${0.6 * L})`; for (let i = 1; i < 8; i++) ctx.fillRect(a.x + (b.x - a.x) * i / 8, a.y, 3, b.y - a.y);
        } else if (o.type === 'dardos') {
            // agujeros en las paredes y dardos cruzando a la altura de la cabeza
            [-1, 1].forEach(side => { const p = P(side * HALF_W, 1.55, z); ctx.fillStyle = `rgba(0,0,0,${L})`; ctx.beginPath(); ctx.arc(p.x, p.y, 0.12 * p.s, 0, Math.PI * 2); ctx.fill(); });
            if (z < 30) {
                const ph = (S.t * 3) % 1;
                for (let k = 0; k < 3; k++) {
                    const xx = -HALF_W + ((ph + k / 3) % 1) * HALF_W * 2, p = P(xx, 1.55 + (k - 1) * 0.08, z);
                    ctx.strokeStyle = `rgba(230,230,240,${L})`; ctx.lineWidth = Math.max(1, 0.04 * p.s); ctx.beginPath(); ctx.moveTo(p.x - 0.35 * p.s, p.y); ctx.lineTo(p.x + 0.35 * p.s, p.y); ctx.stroke();
                    ctx.fillStyle = `rgba(200,40,40,${L})`; ctx.fillRect(p.x - 0.4 * p.s, p.y - 0.05 * p.s, 0.1 * p.s, 0.1 * p.s);
                }
                const a = P(-HALF_W, 1.75, z), b = P(HALF_W, 1.35, z);
                ctx.fillStyle = `rgba(255, 50, 50, ${0.12 * L})`; ctx.fillRect(a.x, a.y, b.x - a.x, b.y - a.y);
            }
        } else if (o.type === 'muro') {
            const x = laneX(o.lane), a = P(x - lw, 3.2, z), b = P(x + lw, 0, z);
            ctx.fillStyle = `rgb(${165 * L | 0}, ${112 * L | 0}, ${55 * L | 0})`; ctx.fillRect(a.x, a.y, b.x - a.x, b.y - a.y);
            ctx.strokeStyle = `rgba(70,40,15,${L})`; ctx.lineWidth = 3; ctx.strokeRect(a.x, a.y, b.x - a.x, b.y - a.y);
            ctx.fillStyle = `rgba(40, 70, 160, ${0.8 * L})`;   // ojo de Horus
            const c = P(x, 2.0, z); ctx.beginPath(); ctx.ellipse(c.x, c.y, 0.45 * c.s, 0.22 * c.s, 0, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = `rgba(20,10,0,${L})`; ctx.beginPath(); ctx.arc(c.x, c.y, 0.12 * c.s, 0, Math.PI * 2); ctx.fill();
        } else if (o.type === 'flecha') {
            const x = laneX(o.lane);
            // aviso: carril brillando en rojo mientras la flecha se acerca
            if (z < 70) { const k = 0.25 + 0.25 * Math.sin(S.t * 20); quad(P(x - lw, 0.02, Math.min(FAR, z + 6)), P(x + lw, 0.02, Math.min(FAR, z + 6)), P(x + lw, 0.02, Z_PLAYER), P(x - lw, 0.02, Z_PLAYER), `rgba(255, 30, 30, ${k * L})`); }
            const p = P(x, 1.25, z);
            ctx.strokeStyle = `rgba(110,70,30,${L})`; ctx.lineWidth = Math.max(2, 0.06 * p.s); ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(p.x, p.y - 0.02 * p.s); ctx.stroke();
            ctx.fillStyle = `rgba(210,210,220,${L})`; ctx.beginPath(); ctx.moveTo(p.x, p.y - 0.18 * p.s); ctx.lineTo(p.x + 0.12 * p.s, p.y); ctx.lineTo(p.x, p.y + 0.18 * p.s); ctx.lineTo(p.x - 0.12 * p.s, p.y); ctx.fill();
            ctx.fillStyle = `rgba(200,40,40,${L})`; ctx.beginPath(); ctx.arc(p.x, p.y, 0.05 * p.s, 0, Math.PI * 2); ctx.fill();
        }
    }
    function drawGem(g) {
        const z = g.d - S.dist + Z_PLAYER; if (z < 0.8 || z > FAR) return;
        const p = P(laneX(g.lane), g.y + Math.sin(S.t * 5 + g.d) * 0.1, z), r = 0.22 * p.s;
        ctx.fillStyle = '#FFD700'; ctx.beginPath(); ctx.ellipse(p.x, p.y, r * 0.8, r, 0, 0, Math.PI * 2); ctx.fill();
        ctx.strokeStyle = '#8A5A00'; ctx.lineWidth = Math.max(1, r * 0.15); ctx.beginPath(); ctx.moveTo(p.x, p.y - r); ctx.lineTo(p.x, p.y + r); ctx.stroke();
        ctx.fillStyle = '#FFF5B0'; ctx.beginPath(); ctx.arc(p.x - r * 0.3, p.y - r * 0.4, r * 0.2, 0, Math.PI * 2); ctx.fill();
    }

    function drawPlayer() {
        if (S.inv > 0 && Math.floor(S.inv * 12) % 2 === 0) return;
        const feet = P(S.x, S.y, Z_PLAYER), hpx = 1.8 * F / Z_PLAYER, px = hpx / 24;
        // sombra
        const sh = P(S.x, 0, Z_PLAYER); ctx.fillStyle = 'rgba(0,0,0,0.35)'; ctx.beginPath(); ctx.ellipse(sh.x, sh.y, 9 * px, 2.5 * px, 0, 0, Math.PI * 2); ctx.fill();
        ctx.save(); ctx.translate(feet.x, feet.y);
        if (S.slide > 0) { ctx.scale(1.15, 0.55); }
        if (S.stumble > 0) ctx.rotate(Math.sin(S.t * 40) * 0.12);
        const ox = -9 * px, oy = -24 * px;
        const legs = S.y > 0.05 ? RUNS.jump : (Math.floor(S.t * 10) % 2 ? RUNS.runA : RUNS.runB);
        drawRuns(legs, ox, oy, px); drawRuns(RUNS.body, ox, oy, px); drawRuns(RUNS.head, ox, oy, px);
        ctx.restore();
    }

    function drawMummy() {
        const M = S.mummy; if (!M.active) return;
        // mientras más cerca, más grande y más arriba en la pantalla (detrás del jugador)
        const close = 1 - Math.max(0, M.gap) / 100, z = 1.6 + close * 2.6, introK = M.intro > 0 ? 1 - M.intro / 2.5 : 1;
        const bob = Math.sin(S.t * 9) * 0.06, b = P(Math.sin(S.t * 1.3) * 0.8, bob - (1 - introK) * 2.5, z), hh = 2.1 * b.s;
        ctx.save(); ctx.globalAlpha = 0.95;
        ctx.fillStyle = '#E8D9B0';
        ctx.fillRect(b.x - 0.45 * b.s, b.y - hh * 0.8, 0.9 * b.s, hh * 0.8);                                  // cuerpo
        ctx.beginPath(); ctx.arc(b.x, b.y - hh * 0.88, 0.32 * b.s, 0, Math.PI * 2); ctx.fill();            // cabeza
        ctx.strokeStyle = 'rgba(120,95,60,0.8)'; ctx.lineWidth = Math.max(1, 0.03 * b.s);
        for (let i = 0; i < 9; i++) { const y = b.y - hh * 0.8 + i * hh * 0.09; ctx.beginPath(); ctx.moveTo(b.x - 0.45 * b.s, y); ctx.lineTo(b.x + 0.45 * b.s, y + 0.06 * b.s); ctx.stroke(); }
        // brazos estirados hacia ti
        const reach = M.grab ? Math.min(1, M.grab.t / C.momia.agarre_aviso_s) : 0.3 + 0.1 * Math.sin(S.t * 6);
        ctx.fillStyle = '#E8D9B0';
        [-1, 1].forEach(sd => {
            const sx = b.x + sd * 0.4 * b.s, sy = b.y - hh * 0.62, ex = sx + sd * 0.2 * b.s, ey = sy - (0.6 + reach * 0.9) * b.s * 0.6;
            ctx.save(); ctx.lineWidth = 0.22 * b.s; ctx.lineCap = 'round'; ctx.strokeStyle = '#E8D9B0'; ctx.beginPath(); ctx.moveTo(sx, sy); ctx.lineTo(ex, ey); ctx.stroke(); ctx.restore();
        });
        ctx.fillStyle = '#FF2244'; ctx.beginPath(); ctx.arc(b.x - 0.12 * b.s, b.y - hh * 0.9, 0.05 * b.s, 0, Math.PI * 2); ctx.arc(b.x + 0.12 * b.s, b.y - hh * 0.9, 0.05 * b.s, 0, Math.PI * 2); ctx.fill();
        ctx.restore();
        // agarre: vendas que se estiran por el carril
        if (M.grab) {
            const k = Math.min(1, M.grab.t / C.momia.agarre_aviso_s), x = laneX(M.grab.lane), lw = LANE_W * 0.46;
            quad(P(x - lw, 0.02, Z_PLAYER + 1.2), P(x + lw, 0.02, Z_PLAYER + 1.2), P(x + lw, 0.02, 1.2), P(x - lw, 0.02, 1.2), `rgba(255, 40, 40, ${0.15 + 0.25 * (Math.floor(S.t * 10) % 2)})`);
            const tip = P(x, 1.0, 1.4 + k * (Z_PLAYER - 0.6)), base = P(x, 1.0, 1.3);
            ctx.strokeStyle = '#F4ECD8'; ctx.lineWidth = Math.max(4, 0.2 * tip.s); ctx.lineCap = 'round';
            ctx.beginPath(); ctx.moveTo(base.x, base.y); ctx.quadraticCurveTo((base.x + tip.x) / 2, base.y - 40, tip.x, tip.y); ctx.stroke();
            ctx.fillStyle = '#E8D9B0'; ctx.beginPath(); ctx.arc(tip.x, tip.y, 0.25 * tip.s, 0, Math.PI * 2); ctx.fill();
        }
    }

    function drawHUD() {
        ctx.save();
        // vidas
        for (let i = 0; i < S.maxHearts; i++) api.drawIcon(ctx, i < S.hearts ? 'heart' : 'heartEmpty', 24 + i * 28, 30, 24);
        ctx.fillStyle = '#FFF2D0'; ctx.font = 'bold 16px sans-serif'; ctx.textAlign = 'left';
        ctx.fillText(`PUNTOS: ${Math.floor(S.score)}   ·   ESCARABAJOS: ${S.gems}`, 14, 64);
        // camino a la salida
        const bw = Math.min(420, W * 0.5), bx = (W - bw) / 2, pct = Math.min(1, S.t / C.duracion_s);
        ctx.fillStyle = 'rgba(0,0,0,0.6)'; ctx.fillRect(bx, 14, bw, 14);
        ctx.fillStyle = '#FFE38A'; ctx.fillRect(bx + 1, 15, (bw - 2) * pct, 12);
        ctx.strokeStyle = '#E8B934'; ctx.strokeRect(bx, 14, bw, 14);
        ctx.fillStyle = '#FFF2D0'; ctx.font = 'bold 12px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(`SALIDA: ${Math.max(0, Math.ceil(C.duracion_s - S.t))} s`, W / 2, 44);
        // qué tan cerca está la momia
        if (S.mummy.active) {
            const g = Math.max(0, S.mummy.gap) / 100;
            ctx.fillStyle = 'rgba(0,0,0,0.6)'; ctx.fillRect(bx, 52, bw, 10);
            ctx.fillStyle = g < 0.35 ? '#FF3355' : '#E8D9B0'; ctx.fillRect(bx + 1, 53, (bw - 2) * (1 - g), 8);
            ctx.fillStyle = '#FFF2D0'; ctx.fillText('MOMIA', W / 2, 76);
        }
        ctx.textAlign = 'right'; ctx.fillText('[ESC] PAUSA', W - 16, 24); ctx.fillText(`FASE 1 · ${String(C.nombre).toUpperCase()}`, W - 16, 42);
        // mensajes
        ctx.textAlign = 'center';
        S.texts.forEach((q, i) => { ctx.globalAlpha = Math.min(1, q.life / 20); ctx.font = `bold ${q.size}px sans-serif`; ctx.lineWidth = 5; ctx.strokeStyle = 'rgba(0,0,0,0.7)'; ctx.strokeText(q.t, W / 2, H * 0.3 + i * (q.size + 6)); ctx.fillStyle = q.color; ctx.fillText(q.t, W / 2, H * 0.3 + i * (q.size + 6)); });
        ctx.globalAlpha = 1;
        // ayuda
        if (S.t < 6) {
            ctx.globalAlpha = Math.min(1, (6 - S.t)); ctx.fillStyle = 'rgba(20, 10, 0, 0.8)'; ctx.fillRect(W / 2 - 300, H - 110, 600, 70);
            ctx.fillStyle = '#FFF2D0'; ctx.font = 'bold 15px sans-serif';
            ctx.fillText('A / D  o  ← / → : CAMBIAR DE CARRIL', W / 2, H - 82);
            ctx.fillText('W / ↑ / ESPACIO: SALTAR   ·   S / ↓: AGACHARSE', W / 2, H - 58);
        }
        ctx.restore();
    }

    function draw() {
        W = canvas.width; H = canvas.height; HZ = H * 0.2; F = H * 0.85;
        if (!S) { ctx.fillStyle = '#120A04'; ctx.fillRect(0, 0, W, H); return; }
        ctx.save();
        if (S.shake > 0) ctx.translate((Math.random() - 0.5) * 14 * S.shake, (Math.random() - 0.5) * 14 * S.shake);
        drawCorridor();
        // de lejos a cerca: trampas y escarabajos
        const items = S.obstacles.map(o => ({ z: o.d - S.dist, f: () => drawObstacle(o) })).concat(S.gemsList.map(g => ({ z: g.d - S.dist, f: () => drawGem(g) })));
        items.sort((a, b) => b.z - a.z);
        items.filter(i => i.z >= 0).forEach(i => i.f());
        drawPlayer();
        items.filter(i => i.z < 0).forEach(i => i.f());
        drawMummy();
        if (S.exit > 0) { ctx.fillStyle = `rgba(255, 245, 210, ${Math.min(1, S.exit / 2)})`; ctx.fillRect(0, 0, W, H); }
        // viñeta
        const v = ctx.createRadialGradient(W / 2, H / 2, H * 0.3, W / 2, H / 2, H * 0.9); v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(0,0,0,0.55)');
        ctx.fillStyle = v; ctx.fillRect(0, 0, W, H);
        ctx.restore();
        drawHUD();
    }

    // ---------- Fin ----------
    function win() {
        if (S.over) return; S.over = true;
        api.onWin(ID); api.playVictoryMusic();
        showOverlay('¡ESCAPASTE DE LA PIRÁMIDE!', `Puntos: ${Math.floor(S.score)} · Escarabajos: ${S.gems}`, '#FFD700', [
            ['REPETIR FASE', '#FFD700', true, () => { api.stopVictoryMusic(true); restart(); }],
            ['VOLVER A NIVELES', '#00FFFF', false, () => { api.stopVictoryMusic(true); exit(); }]
        ]);
    }
    function lose() {
        if (S.over) return; S.over = true; roar(); api.playEndSfx(true);
        const caught = S.mummy.active && S.mummy.gap <= 0;
        showOverlay(caught ? '¡LA MOMIA TE ATRAPÓ!' : 'NO LOGRASTE ESCAPAR', `Llegaste a ${Math.floor(Math.min(100, S.t / C.duracion_s * 100))}% del camino`, '#FF3355', [
            ['REINTENTAR', '#FF3355', true, restart], ['VOLVER A NIVELES', '#00FFFF', false, exit]
        ]);
    }
    function togglePause() {
        if (!S || S.over) return;
        S.paused = !S.paused;
        if (S.paused) showOverlay('PAUSA', 'FASE 1 · ' + String(C.nombre).toUpperCase(), '#E8C27A', [['CONTINUAR', '#33FF66', true, togglePause], ['REINICIAR', '#FFD700', false, restart], ['VOLVER A NIVELES', '#00FFFF', false, exit]]);
        else { hideOverlay(); S.lastTime = performance.now(); }
    }
    function restart() { hideOverlay(); S = newState(); }
    function exit() { hideOverlay(); S = null; api.onExit(); }
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

    window.FASES_REG = window.FASES_REG || {};
    window.FASES_REG[ID] = {
        start(config, theApi) {
            api = theApi; C = merge(DEFAULTS, config || {});
            canvas = api.canvas; ctx = api.ctx;
            setupListeners(); hideOverlay();
            S = newState();
        },
        update, draw,
        stop() { hideOverlay(); S = null; },
        estado() { return S; }
    };
})();
