// ============================================================
// FASE 2 · DESIERTO DEL FARAÓN
// Plataformas estilo Jump King + jefe estilo Cuphead.
// Eres un soldado-robot pixel art con cabeza de estrella:
// sube por las areniscas, pega combos, cúbrete con click derecho,
// saca la katana con R y derrota al Faraón... y a lo que viene después.
//
// app.py carga este archivo solo desde FASES/<carpeta>/fase.js.
// Los números para balancear están en config.json (misma carpeta).
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
        momia_gigante: { nombre: "MOMIA GIGANTE", vida: 700, fase2_en: 0.5, rollos_espera_min: 100, rollos_espera_max: 160 },
        momias: { vida: 20, "daño_golpe": 2, "daño_espada": 4, velocidad: 1.2, espera_min: 480, espera_max: 720, max: 2, prob_ankh: 0.25 },
        jugador: { vida: 6, salto_min: 7, salto_max: 19, carga_frames: 40, golpes: [8, 10, 18] },
        espada: { duracion_s: 15, cooldown_s: 60, multiplicador: 2.5 },
        guardia: { max: 100, costo_golpe: 34, costo_laser: 1.5, recarga: 0.6 },
        arena: { segundos_para_subir: 8, velocidad_subida: 0.5, altura_max: 1380, segundos_para_hundirse: 3 }
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
    const LOW_LINE = 1500;     // más abajo de esto cuenta como "estar abajo" para la arena movediza
    const PLATFORMS = [
        { x: 80, y: 1630, w: 230 }, { x: 430, y: 1550, w: 180 }, { x: 730, y: 1460, w: 220 },
        { x: 390, y: 1350, w: 170 }, { x: 60, y: 1260, w: 210 }, { x: 340, y: 1140, w: 180 },
        { x: 700, y: 1060, w: 230 }, { x: 460, y: 950, w: 150 }, { x: 110, y: 870, w: 210 },
        { x: 380, y: 760, w: 240 }, { x: 770, y: 740, w: 190 }, { x: 30, y: 690, w: 170 }
    ];
    const HEAD = { x: 500, y: 390, rx: 175, ry: 290 };       // zona golpeable del jefe
    const EYES = [{ x: 438, y: 330 }, { x: 562, y: 330 }];
    const LASER_LEN = 1700;

    let api = null, C = null, ctx = null, canvas = null;
    let S = null;
    let keys = new Set(), mouse = { x: 0, y: 0 };
    let overlay = null, listenersReady = false;
    const rand = (a, b) => a + Math.random() * (b - a);

    // ======================================================
    // SPRITE PIXEL ART DEL JUGADOR (18 x 24 píxeles, mirando a la derecha)
    // ======================================================
    const PX = 4;
    const PAL = {
        K: '#1A1410', Y: '#FFD54A', y: '#E0A800', R: '#D8312B', r: '#9A1F1B',
        M: '#A9B3C1', m: '#6B7584', V: '#6B7A35', v: '#4A5524', C: '#33FF66',
        B: '#6B4423', G: '#E8B934', P: '#B59A62', p: '#8A7448', O: '#3A2A1E', W: '#FFFFFF'
    };
    const SPR_HEAD = [
        "........KK........",
        ".......KYYK.......",
        "......KYYYYK......",
        ".KKKKKKYYYYKKKKKK.",
        ".KYYYYYYYYYYYYYYK.",
        "rrKRRRRRRRRRRRRK..",
        "...KYYYYYKYYKYK...",
        "....KYYYYYYYYYK...",
        "....KYYYYYKKYYK...",
        "...KYYYYKKYYYYK...",
        "...KYYYK..KYYYK...",
        "..KYYK......KYYK..",
        "..KKK........KKK.."
    ];
    const SPR_BODY = [   // filas 11 a 17
        ".....KKKKKKKK.....",
        "...KKVVVVVVVVK....",
        "..KvKVVVVCVVVK....",
        "..KvKVVvVVVVVK....",
        "..KvKVVVVVVVVK....",
        "...KKBBBBGBBBK....",
        "....KPPPPPPPPK...."
    ];
    const SPR_LEGS = {      // filas 18 a 23
        stand: ["....KPPK.KPPK.....", "....KPPK.KPPK.....", "....KpPK.KpPK.....", "...KOOOK.KOOOK....", "...KOOOOKKOOOOK...", "...KKKKKK.KKKKKK.."],
        walkA: ["...KPPK...KPPK....", "..KPPK.....KPPK...", "..KpPK.....KpPK...", ".KOOOK.....KOOOK..", ".KOOOOK....KOOOOK.", ".KKKKKK....KKKKKK."],
        walkB: [".....KPPKPPK......", ".....KPPKPPK......", ".....KpPKpPK......", "....KOOOKOOOK.....", "....KOOOOKOOOOK...", "....KKKKKKKKKKK..."],
        jump:  ["....KPPPPPPPPK....", "...KPPK..KPPPK....", "..KOOOK...KOOOK...", "..KOOOOK..KOOOOK..", "..KKKKKK..KKKKKK..", ".................."]
    };
    // Convierte filas en "tiras" de color para dibujar rápido
    function runs(rows, rowOffset) {
        const out = [];
        rows.forEach((row, r) => {
            row = (row + "..................").slice(0, 18);
            let c = 0;
            while (c < 18) {
                const ch = row[c];
                if (ch === '.') { c++; continue; }
                let len = 1; while (c + len < 18 && row[c + len] === ch) len++;
                out.push({ c, r: r + rowOffset, len, col: PAL[ch] });
                c += len;
            }
        });
        return out;
    }
    const RUNS = {
        head: runs(SPR_HEAD, 0), body: runs(SPR_BODY, 11),
        stand: runs(SPR_LEGS.stand, 18), walkA: runs(SPR_LEGS.walkA, 18), walkB: runs(SPR_LEGS.walkB, 18), jump: runs(SPR_LEGS.jump, 18)
    };
    function drawRuns(list, ox, oy, facing) {
        for (const q of list) {
            const x = facing > 0 ? q.c : 18 - q.c - q.len;
            ctx.fillStyle = q.col; ctx.fillRect(ox + x * PX, oy + q.r * PX, q.len * PX, PX);
        }
    }
    // Línea gruesa "pixelada" (para brazos)
    function pixelLine(x0, y0, x1, y1, col, size) {
        const steps = Math.max(1, Math.ceil(Math.hypot(x1 - x0, y1 - y0) / PX));
        ctx.fillStyle = col;
        for (let i = 0; i <= steps; i++) {
            const x = Math.round((x0 + (x1 - x0) * i / steps) / PX) * PX, y = Math.round((y0 + (y1 - y0) * i / steps) / PX) * PX;
            ctx.fillRect(x - size / 2, y - size / 2, size, size);
        }
    }

    // ======================================================
    // KATANA PIXEL ART (hoja rosada, mango negro con rombos magenta)
    // ======================================================
    const KAT = { out: '#2A1418', back: '#D97A9C', body: '#F2A7BF', edge: '#FFE0EA', tsuba: '#C2185B', grip: '#151015', wrap: '#C2185B', sheath: '#151015' };
    function drawKatana(x, y, angle, len) {
        const u = PX;
        ctx.save(); ctx.translate(x, y); ctx.rotate(angle);
        // mango
        ctx.fillStyle = KAT.out; ctx.fillRect(-9 * u, -2 * u, 9 * u, 4 * u);
        ctx.fillStyle = KAT.grip; ctx.fillRect(-8 * u, -1 * u, 8 * u, 2 * u);
        ctx.fillStyle = KAT.wrap; for (let i = -7; i < 0; i += 2) ctx.fillRect(i * u, -1 * u, u, u), ctx.fillRect((i + 1) * u, 0, u, u);
        ctx.fillStyle = KAT.tsuba; ctx.fillRect(-10 * u, -1 * u, u, 2 * u);
        // tsuba (guarda)
        ctx.fillStyle = KAT.out; ctx.fillRect(-u, -3 * u, 3 * u, 6 * u);
        ctx.fillStyle = KAT.tsuba; ctx.fillRect(0, -2 * u, u, 4 * u);
        // hoja curva
        const L = len || 24;
        for (let i = 0; i < L; i++) {
            const t = i / L, yo = Math.round(-2.2 * t * t) * u, bx = (2 + i) * u;
            const thin = i > L - 3;
            ctx.fillStyle = KAT.out; ctx.fillRect(bx, yo - (thin ? 1 : 2) * u, u, (thin ? 2 : 4) * u);
            if (!thin) { ctx.fillStyle = KAT.back; ctx.fillRect(bx, yo - u, u, u); ctx.fillStyle = KAT.body; ctx.fillRect(bx, yo, u, u); }
            ctx.fillStyle = KAT.edge; ctx.fillRect(bx, yo + (thin ? 0 : u), u, u);
        }
        ctx.restore();
    }
    function drawSheath(x, y, angle, withSword) {
        const u = PX;
        ctx.save(); ctx.translate(x, y); ctx.rotate(angle);
        ctx.fillStyle = KAT.out; ctx.fillRect(-u, -2 * u, 22 * u, 4 * u);
        ctx.fillStyle = KAT.sheath; ctx.fillRect(0, -u, 20 * u, 2 * u);
        ctx.fillStyle = KAT.tsuba; ctx.fillRect(18 * u, -u, 2 * u, 2 * u); ctx.fillRect(2 * u, -u, u, u);
        if (withSword) {   // mango asomando
            ctx.fillStyle = KAT.out; ctx.fillRect(-9 * u, -2 * u, 8 * u, 4 * u);
            ctx.fillStyle = KAT.grip; ctx.fillRect(-8 * u, -u, 7 * u, 2 * u);
            ctx.fillStyle = KAT.wrap; for (let i = -7; i < -1; i += 2) ctx.fillRect(i * u, -u, u, u);
            ctx.fillStyle = KAT.tsuba; ctx.fillRect(-u, -3 * u, u, 6 * u);
        }
        ctx.restore();
    }

    // ======================================================
    // ESTADO
    // ======================================================
    function newState() {
        const rissos = api.isRissos();
        const P = C.jugador;
        return {
            t: 0, scale: 1, offX: 0, viewH: 700, camY: H - 700, shake: 0, hintT: 0,
            paused: false, over: false,
            player: {
                x: 190, y: FLOOR - 35, vx: 0, vy: 0, onGround: true, facing: 1,
                hp: rissos ? 20 : P.vida, maxHp: rissos ? 20 : P.vida, inv: 0,
                charge: 0, charging: false,
                atk: 0, atkDir: 0, combo: 0, comboWindow: 0, hitThisSwing: new Set(), queued: false,
                hitCombo: 0, hitComboTimer: 0,
                sword: 0, swordCd: 0, kbx: 0,
                guarding: false, guard: C.guardia.max, guardDelay: 0, guardBroken: 0, blockFlash: 0,
                sink: 0
            },
            boss: {
                stage: 'faraon', t: 0,
                hp: C.jefe.vida, maxHp: C.jefe.vida, phase2: false, flash: 0,
                laserT: rand(C.jefe.laser_espera_min, C.jefe.laser_espera_max), laser: null,
                throwT: rand(C.jefe.objetos_espera_min, C.jefe.objetos_espera_max),
                flyOff: 0, rise: 0, armAnim: 0
            },
            sandY: FLOOR + 30, lowTime: 0, sandWarned: false,
            mummies: [], mummyT: 240, objects: [], rolls: [], pickups: [], particles: [], texts: [],
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
        window.addEventListener('blur', () => { keys.clear(); if (S) S.player.guarding = false; });
        canvas.addEventListener('mousemove', e => { const r = canvas.getBoundingClientRect(); mouse.x = e.clientX - r.left; mouse.y = e.clientY - r.top; });
        canvas.addEventListener('mousedown', e => {
            if (!api || !api.active() || !S || S.paused || S.over) return;
            if (e.button === 0) attack();
            if (e.button === 2) { e.preventDefault(); S.player.guarding = true; }
        });
        window.addEventListener('mouseup', e => { if (e.button === 2 && S) S.player.guarding = false; });
    }
    const jumpHeld = () => keys.has('Space') || keys.has('KeyW') || keys.has('ArrowUp');
    const left = () => keys.has('KeyA') || keys.has('ArrowLeft');
    const right = () => keys.has('KeyD') || keys.has('ArrowRight');
    function mouseWorld() { return { x: (mouse.x - S.offX) / S.scale, y: mouse.y / S.scale + S.camY }; }
    const isGuarding = () => { const p = S.player; return p.guarding && p.guardBroken <= 0 && p.guard > 0; };
    const inSand = () => S.player.y + 35 > S.sandY + 6;

    // ---------- Sonidos propios (grito, rugido) ----------
    function scream(base, dur) {
        if (!api.interacted() || api.sfxVol() === 0) return;
        try {
            const ac = api.getAudioCtx(), t = ac.currentTime;
            const out = ac.createGain(); out.gain.setValueAtTime(0.0001, t); out.gain.exponentialRampToValueAtTime(Math.min(1, api.sfxVol() * 0.9), t + 0.08);
            out.gain.setValueAtTime(Math.min(1, api.sfxVol() * 0.9), t + dur - 0.3); out.gain.exponentialRampToValueAtTime(0.0001, t + dur);
            out.connect(ac.destination);
            const bp = ac.createBiquadFilter(); bp.type = 'bandpass'; bp.frequency.value = base * 2.5; bp.Q.value = 1.2; bp.connect(out);
            const vib = ac.createOscillator(); vib.frequency.value = 9; const vd = ac.createGain(); vd.gain.value = base * 0.08; vib.connect(vd);
            [0, 9, -7].forEach(det => {
                const o = ac.createOscillator(); o.type = 'sawtooth'; o.detune.value = det * 10;
                o.frequency.setValueAtTime(base * 1.6, t); o.frequency.exponentialRampToValueAtTime(base, t + 0.4); o.frequency.exponentialRampToValueAtTime(base * 0.45, t + dur);
                vd.connect(o.frequency); o.connect(bp); o.start(t); o.stop(t + dur);
            });
            vib.start(t); vib.stop(t + dur);
            const len = Math.ceil(ac.sampleRate * dur), buf = ac.createBuffer(1, len, ac.sampleRate), d = buf.getChannelData(0);
            for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * 0.5;
            const n = ac.createBufferSource(); n.buffer = buf; n.connect(bp); n.start(t);
        } catch (e) {}
    }

    // ---------- Acciones del jugador ----------
    function releaseJump() {
        const p = S.player;
        if (!p.charging) return;
        const J = C.jugador;
        const c = Math.min(1, p.charge / J.carga_frames);
        const sandMult = inSand() ? 0.6 : 1;
        p.vy = -(J.salto_min + (J.salto_max - J.salto_min) * c) * sandMult;
        const dir = (left() ? -1 : 0) + (right() ? 1 : 0);
        p.vx = dir * (2.5 + 5 * c) * sandMult;
        if (dir) p.facing = dir;
        p.onGround = false; p.charging = false; p.charge = 0;
        for (let i = 0; i < 8; i++) puff(p.x + rand(-14, 14), p.y + 35, '#E8C27A');
    }

    function attack() {
        const p = S.player;
        if (isGuarding()) return;
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
        if (p.swordCd > 0) { text(p.x, p.y - 60, `KATANA: ${Math.ceil(p.swordCd / 60)}s`, '#999', 14); return; }
        p.sword = C.espada.duracion_s * 60;
        api.playAbilitySfx('metal');
        text(p.x, p.y - 70, '¡KATANA!', '#FF8FB8', 26);
    }

    // kind: 'golpe' | 'laser'
    function hurtPlayer(n, fromX, kind) {
        const p = S.player;
        if (p.inv > 0 || S.over) return;
        if (isGuarding()) {
            p.guard -= kind === 'laser' ? C.guardia.costo_laser : C.guardia.costo_golpe;
            p.guardDelay = 40; p.blockFlash = 6;
            if (kind !== 'laser' || S.t % 10 === 0) { for (let i = 0; i < 5; i++) puff(p.x + p.facing * 22, p.y - 5, '#BFE9FF'); }
            if (kind !== 'laser') { api.playAbilitySfx('ping'); if (!S.blockTxt) { text(p.x, p.y - 60, '¡BLOQUEADO!', '#BFE9FF', 16); S.blockTxt = 30; } p.kbx = (p.x < fromX ? -1 : 1) * 3; }
            if (p.guard <= 0) { p.guard = 0; p.guardBroken = 90; text(p.x, p.y - 75, '¡GUARDIA ROTA!', '#FF3355', 20); api.playAbilitySfx('metal'); }
            return;
        }
        p.hp -= n; p.inv = 60;
        p.vy = -7; p.kbx = (p.x < fromX ? -1 : 1) * 7; p.onGround = false; p.charging = false; p.charge = 0;
        text(p.x, p.y - 50, `-${n}`, '#FF3355', 22);
        api.playAbilitySfx('boom');
        for (let i = 0; i < 12; i++) puff(p.x, p.y, '#FF3355');
        if (p.hp <= 0) lose('EL DESIERTO TE VENCIÓ', 'Las arenas te tragaron...');
    }

    // ---------- Efectos ----------
    function puff(x, y, color) { if (S.particles.length < 400) S.particles.push({ x, y, vx: rand(-2.5, 2.5), vy: rand(-3, 0.5), life: rand(18, 30), color }); }
    function text(x, y, t, color, size) { S.texts.push({ x, y, t, color, size: size || 16, life: 50 }); }

    // ---------- Física ----------
    function landOn(e, prevBottom, half) {
        const bottom = e.y + half;
        if (e.vy >= 0) {
            for (const pl of PLATFORMS) {
                if (e.x + 12 > pl.x && e.x - 12 < pl.x + pl.w && prevBottom <= pl.y + 1 && bottom >= pl.y) { e.y = pl.y - half; e.vy = 0; return pl; }
            }
            if (bottom >= FLOOR) { e.y = FLOOR - half; e.vy = 0; return 'floor'; }
        }
        return null;
    }

    function updatePlayer() {
        const p = S.player, J = C.jugador, G = C.guardia;
        if (p.inv > 0) p.inv--;
        if (p.blockFlash > 0) p.blockFlash--;
        if (S.blockTxt > 0) S.blockTxt--;
        if (p.sword > 0) { p.sword--; if (p.sword === 0) { p.swordCd = (S.rissos ? 5 : C.espada.cooldown_s) * 60; text(p.x, p.y - 60, 'KATANA ENVAINADA', '#999', 16); } }
        else if (p.swordCd > 0) p.swordCd--;
        if (p.comboWindow > 0) p.comboWindow--;
        if (p.hitComboTimer > 0) { p.hitComboTimer--; if (p.hitComboTimer === 0) p.hitCombo = 0; }
        // guardia
        if (p.guardBroken > 0) p.guardBroken--;
        if (!isGuarding()) { if (p.guardDelay > 0) p.guardDelay--; else p.guard = Math.min(G.max, p.guard + G.recarga); }

        if (p.atk > 0) {
            p.atk--;
            if (p.atk <= 10 && p.atk >= 4) resolveHits();
            if (p.atk === 0) { p.comboWindow = 22; if (p.queued) { p.queued = false; attack(); } }
        }

        const guarding = isGuarding();
        const sand = inSand();
        const dir = (left() ? -1 : 0) + (right() ? 1 : 0);
        if (p.onGround) {
            if (guarding) { p.vx = 0; p.charging = false; p.charge = 0; }
            else if (jumpHeld()) { p.charging = true; p.charge = Math.min(J.carga_frames, p.charge + 1); p.vx = 0; }
            else { p.vx = dir * 4.2 * (sand ? 0.4 : 1); if (dir) p.facing = dir; }
        } else {
            if (dir) p.vx += dir * 0.12;
            p.vx = Math.max(-8, Math.min(8, p.vx));
        }
        if (guarding) { const m = mouseWorld(); p.facing = m.x >= p.x ? 1 : -1; }

        const prevBottom = p.y + 35;
        p.vy = Math.min(MAX_FALL, p.vy + GRAV);
        p.x += p.vx + p.kbx; p.y += p.vy;
        p.kbx *= 0.8; if (Math.abs(p.kbx) < 0.1) p.kbx = 0;

        if (p.x < 22) { p.x = 22; p.vx = Math.abs(p.vx) * 0.6; }
        if (p.x > W - 22) { p.x = W - 22; p.vx = -Math.abs(p.vx) * 0.6; }
        if (p.y < 40) { p.y = 40; p.vy = Math.max(0, p.vy); }

        const wasAir = !p.onGround;
        const landed = landOn(p, prevBottom, 35);
        p.onGround = !!landed;
        if (landed && wasAir) { p.vx = 0; for (let i = 0; i < 6; i++) puff(p.x + rand(-14, 14), p.y + 35, '#E8C27A'); }
        if (!landed && p.charging) { p.charging = false; p.charge = 0; }
    }

    // ---------- Arena movediza ----------
    function updateSand() {
        const p = S.player, A = C.arena;
        if (p.y + 35 > LOW_LINE) S.lowTime++; else S.lowTime = Math.max(0, S.lowTime - 2);
        const limit = A.segundos_para_subir * 60;
        if (S.lowTime > limit * 0.7 && !S.sandWarned) { S.sandWarned = true; text(p.x, p.y - 80, '¡LA ARENA SE MUEVE!', '#FFB257', 20); }
        if (S.lowTime < limit * 0.3) S.sandWarned = false;
        if (S.lowTime > limit) S.sandY = Math.max(A.altura_max, S.sandY - A.velocidad_subida);
        else S.sandY = Math.min(FLOOR + 30, S.sandY + A.velocidad_subida * 0.6);

        if (inSand() && !S.over) {
            p.sink++;
            if (p.onGround) p.y += 0.3;   // te va tragando
            if (S.t % 4 === 0) puff(p.x + rand(-16, 16), S.sandY, '#C99A50');
            if (p.sink >= A.segundos_para_hundirse * 60) lose('LA ARENA MOVEDIZA TE TRAGÓ', 'No te quedes mucho tiempo abajo...');
        } else p.sink = Math.max(0, p.sink - 2);
    }

    // ---------- Golpes ----------
    function attackCircle() {
        const p = S.player, sw = p.sword > 0;
        const reach = sw ? 80 : 50, rad = sw ? 64 : (p.combo === 3 ? 48 : 40);
        return { x: p.x + Math.cos(p.atkDir) * reach, y: p.y + Math.sin(p.atkDir) * reach, r: rad };
    }
    function bossDamage() {
        const p = S.player;
        let d = C.jugador.golpes[p.combo - 1] || C.jugador.golpes[0];
        if (p.sword > 0) d *= C.espada.multiplicador;
        d *= 1 + Math.min(0.5, p.hitCombo * 0.05);
        if (S.rissos) d *= 2;
        return Math.round(d);
    }
    function mummyDamage() {
        const p = S.player;
        let d = p.sword > 0 ? C.momias['daño_espada'] : C.momias['daño_golpe'];
        if (S.rissos) d *= 2;
        return d;
    }
    function registerHit() {
        const p = S.player;
        p.hitCombo++; p.hitComboTimer = 120;
        if (p.hitCombo >= 3) text(p.x, p.y - 80, `COMBO x${p.hitCombo}`, '#FFD700', 18 + Math.min(14, p.hitCombo));
    }

    function bossHittable() { const b = S.boss; return (b.stage === 'faraon' || b.stage === 'momia') && pose().hittable; }

    function resolveHits() {
        const p = S.player, a = attackCircle(), b = S.boss;
        if (!pose().hittable && (b.stage === 'faraon' || b.stage === 'momia') && p.atk === 10 && !S.hintT) { text(p.x, p.y - 70, '¡SUBE PARA PEGARLE!', '#FFF2D0', 16); S.hintT = 180; }
        // Jefe
        if (bossHittable() && !p.hitThisSwing.has('boss')) {
            const P = pose(), cy = P.y + (b.stage === 'momia' ? 30 : 0) * P.s;
            const dx = (a.x - P.x) / (HEAD.rx * P.s + a.r), dy = (a.y - cy) / (HEAD.ry * P.s + a.r);
            if (dx * dx + dy * dy < 1) {
                const dmg = bossDamage();
                p.hitThisSwing.add('boss'); b.hp -= dmg; b.flash = 8; registerHit();
                text(a.x, a.y - 20, `-${dmg}`, p.sword > 0 ? '#FF8FB8' : '#FFFFFF', 22);
                for (let i = 0; i < 8; i++) puff(a.x, a.y, b.stage === 'momia' ? '#E8D9B0' : '#FFD700');
                api.playAbilitySfx('ping');
                const half = b.stage === 'momia' ? C.momia_gigante.fase2_en : C.jefe.fase2_en;
                if (!b.phase2 && b.hp > 0 && b.hp <= b.maxHp * half) {
                    b.phase2 = true;
                    text(P.x, P.y - 300 * P.s, b.stage === 'momia' ? '¡LA MOMIA SE DESENVUELVE!' : '¡EL FARAÓN SE ENFURECE!', '#FF3355', 30);
                }
                if (b.hp <= 0) b.stage === 'faraon' ? pharaohDefeated() : giantMummyDefeated();
            }
        }
        // Momias
        S.mummies.forEach(m => {
            if (m.dead || m.rise > 0 || p.hitThisSwing.has(m)) return;
            if (Math.hypot(m.x - a.x, m.y - a.y) < a.r + 24) {
                const dmg = mummyDamage();
                p.hitThisSwing.add(m); m.hp -= dmg; m.flash = 6; registerHit();
                m.kb = Math.sign(m.x - p.x || 1) * (p.combo === 3 ? 8 : 4);
                text(m.x, m.y - 40, `-${dmg}`, '#FFFFFF', 18);
                api.playAbilitySfx('ping');
                if (m.hp <= 0) killMummy(m);
            }
        });
        // Objetos y rollos: se rompen de un golpe
        S.objects.forEach(o => { if (!o.dead && !p.hitThisSwing.has(o) && Math.hypot(o.x - a.x, o.y - a.y) < a.r + o.r) { p.hitThisSwing.add(o); breakObject(o); registerHit(); } });
        S.rolls.forEach(o => { if (!o.dead && !p.hitThisSwing.has(o) && Math.hypot(o.x - a.x, o.y - a.y) < a.r + 16) { p.hitThisSwing.add(o); breakRoll(o); registerHit(); } });
    }

    // ======================================================
    // JEFES
    // ======================================================
    function topCam() { return Math.max(0, 655 - S.viewH * 0.85); }
    // El jefe siempre se ve: desde abajo aparece a lo lejos (más chico) y al subir se acerca.
    function pose() {
        const top = topCam(), bottom = Math.max(top + 1, H - S.viewH);
        const k = Math.max(0, Math.min(1, (S.camY - top) / (bottom - top)));
        const screenY = (HEAD.y - S.camY) + (150 - (HEAD.y - S.camY)) * k;
        const sc = 1 - 0.45 * k;
        return { x: HEAD.x, y: S.camY + screenY + S.boss.flyOff, s: sc, k, hittable: k < 0.22 };
    }
    function eyePos(i) { const P = pose(); return { x: P.x + (EYES[i].x - HEAD.x) * P.s, y: P.y + (EYES[i].y - HEAD.y) * P.s }; }

    function updateBoss() {
        const b = S.boss, p = S.player;
        if (b.flash > 0) b.flash--;
        b.t++;
        if (b.armAnim > 0) b.armAnim--;

        if (b.stage === 'faraon') { if (!S.over) pharaohAttacks(); return; }
        if (b.stage === 'grito') {
            S.shake = Math.max(S.shake, 6);
            if (b.t % 4 === 0) { const P = pose(); puff(P.x + rand(-120, 120) * P.s, P.y + 110 * P.s, '#FFD700'); }
            if (b.t >= 130) { b.stage = 'vuela'; b.t = 0; text(HEAD.x, pose().y - 200, '¡SE ESCAPA!', '#FFD700', 30); }
            return;
        }
        if (b.stage === 'vuela') {
            b.flyOff -= 2 + b.t * 0.35;
            const P = pose(); for (let i = 0; i < 3; i++) puff(P.x + rand(-150, 150) * P.s, P.y + 260 * P.s, '#E8C27A');
            if (b.t >= 100) { b.stage = 'llegada'; b.t = 0; b.flyOff = 0; b.rise = 0; S.shake = 90; scream(70, 2.2); text(HEAD.x, pose().y - 150, '¡MOMIA GIGANTE!', '#E8D9B0', 38); }
            return;
        }
        if (b.stage === 'llegada') {
            b.rise = Math.min(1, b.t / 150);
            S.shake = Math.max(S.shake, 4);
            if (b.t % 3 === 0) { const P = pose(); puff(P.x + rand(-220, 220) * P.s, P.y + 200 * P.s, '#E8C27A'); }
            if (b.t >= 160) {
                b.stage = 'momia'; b.t = 0; b.hp = C.momia_gigante.vida; b.maxHp = C.momia_gigante.vida; b.phase2 = false;
                b.throwT = 60;
            }
            return;
        }
        if (b.stage === 'momia') { if (!S.over) giantMummyAttacks(); return; }
        if (b.stage === 'fin') {
            if (b.t % 3 === 0) { const P = pose(); for (let i = 0; i < 4; i++) puff(P.x + rand(-200, 200) * P.s, P.y + rand(-250, 250) * P.s, i % 2 ? '#E8D9B0' : '#8B7355'); }
            S.shake = Math.max(S.shake, 3);
        }
    }

    function pharaohAttacks() {
        const b = S.boss, p = S.player, J = C.jefe, speed = b.phase2 ? 1.6 : 1;
        if (b.laser) {
            b.laser.t++;
            if (b.laser.t === J.laser_aviso) api.playSfx('laser', 1);
            if (b.laser.t > J.laser_aviso) {
                for (let i = 0; i < 2; i++) {
                    const e = eyePos(i), a = b.laser.angles[i];
                    const x2 = e.x + Math.cos(a) * LASER_LEN, y2 = e.y + Math.sin(a) * LASER_LEN;
                    if (segDist(p.x, p.y, e.x, e.y, x2, y2) < 40) hurtPlayer(1, e.x, 'laser');
                    if (b.laser.t % 6 === 0) S.mummies.forEach(m => { if (!m.dead && segDist(m.x, m.y, e.x, e.y, x2, y2) < 30) { m.hp -= 2; if (m.hp <= 0) killMummy(m); } });
                }
            }
            if (b.laser.t >= J.laser_aviso + J.laser_duracion) { b.laser = null; b.laserT = rand(J.laser_espera_min, J.laser_espera_max) / speed; }
        } else if ((b.laserT -= 1) <= 0) {
            const tx = p.x + p.vx * 10, ty = p.y + p.vy * 4;
            b.laser = { t: 0, angles: [0, 1].map(i => { const e = eyePos(i); return Math.atan2(ty - e.y, tx - e.x); }) };
            api.playAbilitySfx('shield');
        }
        if ((b.throwT -= 1) <= 0) {
            const n = b.phase2 ? 2 : 1;
            for (let i = 0; i < n; i++) throwObject(i);
            b.throwT = rand(J.objetos_espera_min, J.objetos_espera_max) / speed;
        }
    }

    function giantMummyAttacks() {
        const b = S.boss, M = C.momia_gigante;
        if ((b.throwT -= 1) <= 0) {
            const n = b.phase2 ? 3 : (Math.random() < 0.4 ? 2 : 1);
            for (let i = 0; i < n; i++) throwRoll(i, n);
            b.armAnim = 24;
            b.throwT = rand(M.rollos_espera_min, M.rollos_espera_max) / (b.phase2 ? 1.5 : 1);
        }
    }

    function arcTo(sx, sy, tx, ty, g) {
        const T = 55 + Math.min(40, Math.abs(ty - sy) / 20);
        return { vx: (tx - sx) / T, vy: (ty - sy) / T - 0.5 * g * T };
    }
    function throwObject(i) {
        const p = S.player, P = pose(), side = Math.random() < 0.5 ? -1 : 1;
        const sx = P.x + side * 230 * P.s, sy = P.y + 120 * P.s;
        const tx = p.x + rand(-60, 60) + (i ? rand(-180, 180) : 0), ty = p.y, g = 0.35;
        const v = arcTo(sx, sy, tx, ty, g);
        S.objects.push({ x: sx, y: sy, vx: v.vx, vy: v.vy, g, r: 18, kind: ['vasija', 'escarabajo', 'bloque'][Math.floor(Math.random() * 3)], rot: 0, dead: false });
        api.playAbilitySfx('whoosh');
    }
    function throwRoll(i, n) {
        const p = S.player, P = pose(), side = i % 2 === 0 ? 1 : -1;
        const sx = P.x + side * 190 * P.s, sy = P.y - 80 * P.s;
        const spread = n > 1 ? (i - (n - 1) / 2) * 150 : 0;
        const tx = p.x + spread + p.vx * 12, ty = p.y, g = 0.32;
        const v = arcTo(sx, sy, tx, ty, g);
        S.rolls.push({ x: sx, y: sy, vx: v.vx, vy: v.vy, g, rot: 0, trail: [], dead: false });
        api.playAbilitySfx('whoosh');
    }
    function breakObject(o) {
        o.dead = true;
        const col = o.kind === 'vasija' ? '#B5651D' : (o.kind === 'escarabajo' ? '#1FB5A8' : '#D9A55B');
        for (let i = 0; i < 12; i++) puff(o.x, o.y, col);
    }
    function breakRoll(o) { o.dead = true; for (let i = 0; i < 14; i++) puff(o.x, o.y, i % 2 ? '#F4ECD8' : '#CDBF9A'); }

    function hitsGround(o, r) {
        if (o.vy <= 0) return false;
        for (const pl of PLATFORMS) if (o.x > pl.x && o.x < pl.x + pl.w && o.y + r >= pl.y && o.y + r - o.vy <= pl.y + 2) return true;
        return o.y + r >= FLOOR;
    }
    function updateProjectiles() {
        const p = S.player;
        S.objects.forEach(o => {
            if (o.dead) return;
            o.vy += o.g; o.x += o.vx; o.y += o.vy; o.rot += 0.15;
            if (Math.hypot(o.x - p.x, o.y - p.y) < o.r + 24) { breakObject(o); hurtPlayer(1, o.x, 'golpe'); return; }
            if (hitsGround(o, o.r)) breakObject(o);
            if (o.x < -60 || o.x > W + 60 || o.y > H + 60) o.dead = true;
        });
        S.objects = S.objects.filter(o => !o.dead);
        S.rolls.forEach(o => {
            if (o.dead) return;
            o.vy += o.g; o.x += o.vx; o.y += o.vy; o.rot += 0.25;
            o.trail.push({ x: o.x, y: o.y }); if (o.trail.length > 14) o.trail.shift();
            if (Math.hypot(o.x - p.x, o.y - p.y) < 16 + 24) { breakRoll(o); hurtPlayer(1, o.x, 'golpe'); return; }
            if (hitsGround(o, 14)) breakRoll(o);
            if (o.x < -60 || o.x > W + 60 || o.y > H + 60) o.dead = true;
        });
        S.rolls = S.rolls.filter(o => !o.dead);
    }

    function pharaohDefeated() {
        const b = S.boss;
        b.stage = 'grito'; b.t = 0; b.hp = 0; b.laser = null; b.phase2 = false;
        S.objects.forEach(breakObject);
        S.shake = 130;
        scream(220, 2.4);
        text(HEAD.x, pose().y - 260 * pose().s, '¡NOOOOOOO!', '#FF3355', 46);
    }
    function giantMummyDefeated() {
        const b = S.boss;
        b.stage = 'fin'; b.t = 0; b.hp = 0;
        S.mummies.forEach(m => { if (!m.dead) killMummy(m, true); });
        S.rolls.forEach(breakRoll);
        S.player.inv = 99999;
        scream(60, 2.6);
        text(HEAD.x, pose().y, '¡MOMIA GIGANTE DERROTADA!', '#FFD700', 40);
        const st = S; setTimeout(() => { if (S === st) win(); }, 2800);
    }

    // ---------- Momias pequeñas ----------
    function spawnMummy() {
        const p = S.player;
        const spots = [{ x: rand(60, W - 60), y: FLOOR }].concat(PLATFORMS.map(pl => ({ x: rand(pl.x + 20, pl.x + pl.w - 20), y: pl.y })));
        const near = spots.filter(s => Math.abs(s.y - p.y) < S.viewH * 0.6 && Math.abs(s.x - p.x) > 110 && s.y < S.sandY);
        const pool = near.length ? near : spots;
        const s = pool[Math.floor(Math.random() * pool.length)];
        const M = C.momias;
        S.mummies.push({ x: s.x, y: s.y - 32, vx: 0, vy: 0, hp: M.vida, maxHp: M.vida, rise: 40, dir: Math.random() < 0.5 ? -1 : 1, flash: 0, kb: 0, dead: false, onGround: true, t: rand(0, 100) });
        for (let i = 0; i < 14; i++) puff(s.x + rand(-20, 20), s.y, '#E8C27A');
        text(s.x, s.y - 70, '¡MOMIA!', '#E8D9B0', 16);
    }
    function killMummy(m, silent) {
        m.dead = true;
        for (let i = 0; i < 16; i++) puff(m.x, m.y, i % 2 ? '#E8D9B0' : '#8B7355');
        if (!silent && Math.random() < C.momias.prob_ankh) S.pickups.push({ x: m.x, y: m.y - 10, vy: -4, t: 0 });
        if (!silent) api.playAbilitySfx('boom');
    }
    function updateMummies() {
        const p = S.player, b = S.boss, M = C.momias;
        const fighting = b.stage === 'faraon' || b.stage === 'momia';
        const max = b.phase2 ? M.max + 1 : M.max;
        if (fighting && (S.mummyT -= 1) <= 0) {
            if (S.mummies.filter(m => !m.dead).length < max) spawnMummy();
            S.mummyT = rand(M.espera_min, M.espera_max) / (b.phase2 ? 1.3 : 1);
        }
        S.mummies.forEach(m => {
            if (m.dead) return;
            m.t++; if (m.flash > 0) m.flash--;
            if (m.rise > 0) { m.rise--; return; }
            if (Math.abs(p.y - m.y) < 60) m.dir = Math.sign(p.x - m.x) || m.dir;
            const sp = M.velocidad * (b.phase2 ? 1.3 : 1);
            m.vx = m.dir * sp + m.kb; m.kb *= 0.85; if (Math.abs(m.kb) < 0.1) m.kb = 0;
            const prevBottom = m.y + 32;
            m.vy = Math.min(MAX_FALL, m.vy + GRAV);
            const nx = m.x + m.vx;
            if (m.onGround && !m.kb) {
                const pl = PLATFORMS.find(q => Math.abs(q.y - (m.y + 32)) < 3 && m.x >= q.x - 5 && m.x <= q.x + q.w + 5);
                if (pl && (nx < pl.x + 10 || nx > pl.x + pl.w - 10)) { m.dir *= -1; m.vx = 0; }
            }
            m.x += m.vx; m.y += m.vy;
            if (m.x < 20 || m.x > W - 20) { m.dir *= -1; m.x = Math.max(20, Math.min(W - 20, m.x)); }
            m.onGround = !!landOn(m, prevBottom, 32);
            if (Math.abs(m.x - p.x) < 34 && Math.abs(m.y - p.y) < 55) hurtPlayer(1, m.x, 'golpe');
        });
        S.mummies = S.mummies.filter(m => !m.dead);
    }

    function updatePickups() {
        const p = S.player;
        S.pickups.forEach(k => {
            k.t++; k.vy = Math.min(8, k.vy + 0.3); const prev = k.y + 14; k.y += k.vy;
            if (landOn(k, prev, 14)) k.vy = 0;
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
        showOverlay('¡FASE 2 COMPLETADA!', 'Venciste al Faraón y a la Momia Gigante', '#FFD700', [
            ['REPETIR FASE', '#FFD700', true, () => { api.stopVictoryMusic(true); restart(); }],
            ['VOLVER A NIVELES', '#00FFFF', false, () => { api.stopVictoryMusic(true); exit(); }]
        ]);
    }
    function lose(title, sub) {
        if (S.over) return;
        S.over = true; S.player.hp = Math.max(0, S.player.hp);
        api.playEndSfx(true);
        showOverlay(title, sub, '#FF3355', [['REINTENTAR', '#FF3355', true, restart], ['VOLVER A NIVELES', '#00FFFF', false, exit]]);
    }
    function togglePause() {
        if (!S || S.over) return;
        S.paused = !S.paused; keys.clear(); S.player.guarding = false;
        if (S.paused) showOverlay('PAUSA', 'FASE 2 · ' + String(C.nombre).toUpperCase(), '#E8C27A', [
            ['CONTINUAR', '#33FF66', true, togglePause], ['REINICIAR', '#FFD700', false, restart], ['VOLVER A NIVELES', '#00FFFF', false, exit]
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

    // ======================================================
    // BUCLE
    // ======================================================
    function update() {
        if (!S || S.paused) return;
        S.t++;
        S.scale = Math.min(canvas.width / W, canvas.height / 700);
        S.offX = (canvas.width - W * S.scale) / 2;
        S.viewH = canvas.height / S.scale;
        if (S.hintT > 0) S.hintT--;
        if (S.shake > 0) S.shake--;
        if (!S.over) { updatePlayer(); updateSand(); updateProjectiles(); updateMummies(); updatePickups(); }
        updateBoss();
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

    // ======================================================
    // DIBUJO
    // ======================================================
    function draw() {
        if (!S) { ctx.fillStyle = '#1a0f05'; ctx.fillRect(0, 0, canvas.width, canvas.height); return; }
        const sc = S.scale;
        const g = ctx.createLinearGradient(0, 0, 0, canvas.height);
        const k = S.camY / (H - S.viewH || 1);
        g.addColorStop(0, k < 0.5 ? '#3B1C5A' : '#FF8A3D'); g.addColorStop(0.55, '#FFB257'); g.addColorStop(1, '#FFE0A3');
        ctx.fillStyle = g; ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = 'rgba(255, 240, 180, 0.85)'; ctx.beginPath(); ctx.arc(canvas.width * 0.82, canvas.height * 0.22 - S.camY * 0.03, 70 * sc, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = 'rgba(255, 240, 180, 0.25)'; ctx.beginPath(); ctx.arc(canvas.width * 0.82, canvas.height * 0.22 - S.camY * 0.03, 95 * sc, 0, Math.PI * 2); ctx.fill();
        ctx.save(); ctx.translate(0, -S.camY * 0.08 * sc);
        ctx.fillStyle = 'rgba(190, 110, 50, 0.55)';
        [[0.12, 0.7, 260], [0.3, 0.75, 180], [0.9, 0.72, 300]].forEach(([px, py, s]) => { const x = canvas.width * px, y = canvas.height * py + 300 * sc; ctx.beginPath(); ctx.moveTo(x - s * sc, y); ctx.lineTo(x, y - s * 0.75 * sc); ctx.lineTo(x + s * sc, y); ctx.fill(); });
        ctx.restore();

        const shx = S.shake > 0 ? rand(-1, 1) * Math.min(10, S.shake) : 0, shy = S.shake > 0 ? rand(-1, 1) * Math.min(10, S.shake) : 0;
        ctx.save(); ctx.translate(S.offX + shx, shy); ctx.scale(sc, sc); ctx.translate(0, -S.camY);
        drawWalls();
        const st = S.boss.stage;
        if (st === 'faraon' || st === 'grito' || st === 'vuela') drawPharaoh();
        else drawGiantMummy();
        PLATFORMS.forEach(drawPlatform);
        ctx.fillStyle = '#E2B062'; ctx.fillRect(-400, FLOOR, W + 800, 200);
        ctx.fillStyle = '#F2CB82'; ctx.fillRect(-400, FLOOR, W + 800, 8);
        drawLaser();
        S.objects.forEach(drawObject);
        S.rolls.forEach(drawRoll);
        S.pickups.forEach(drawAnkh);
        S.mummies.forEach(drawMummy);
        drawPlayer();
        drawSand();
        for (const q of S.particles) { ctx.globalAlpha = Math.min(1, q.life / 15); ctx.fillStyle = q.color; ctx.fillRect(q.x - 3, q.y - 3, 6, 6); }
        ctx.globalAlpha = 0.35; ctx.fillStyle = '#FFF2D0'; for (const d of S.dust) ctx.fillRect(d.x, d.y, 2.5 * d.s, 2.5 * d.s); ctx.globalAlpha = 1;
        ctx.textAlign = 'center'; ctx.lineWidth = 4; ctx.strokeStyle = 'rgba(0,0,0,0.6)';
        for (const q of S.texts) { ctx.globalAlpha = Math.min(1, q.life / 15); ctx.fillStyle = q.color; ctx.font = 'bold ' + q.size + 'px sans-serif'; ctx.strokeText(q.t, q.x, q.y); ctx.fillText(q.t, q.x, q.y); }
        ctx.globalAlpha = 1;
        ctx.restore();
        drawHUD();
    }

    function drawWalls() {
        [-400, W].forEach(x => {
            ctx.fillStyle = '#B97F3E'; ctx.fillRect(x, 0, 400, H + 200);
            ctx.strokeStyle = 'rgba(90, 50, 20, 0.5)'; ctx.lineWidth = 2;
            ctx.beginPath(); for (let y = 0; y < H; y += 60) { ctx.moveTo(x, y); ctx.lineTo(x + 400, y); } ctx.stroke();
            ctx.fillStyle = 'rgba(70, 35, 10, 0.55)';
            const cx = x === W ? W + 40 : -40;
            for (let y = 30; y < H; y += 120) { ctx.beginPath(); ctx.ellipse(cx, y, 9, 14, 0, 0, Math.PI * 2); ctx.fill(); ctx.fillRect(cx - 3, y + 24, 6, 26); ctx.fillRect(cx - 12, y + 60, 24, 5); }
        });
        ctx.fillStyle = '#8A5A28'; ctx.fillRect(-8, 0, 8, H + 200); ctx.fillRect(W, 0, 8, H + 200);
    }

    function drawPlatform(pl) {
        ctx.fillStyle = '#C98F4A'; ctx.fillRect(pl.x, pl.y, pl.w, 26);
        ctx.fillStyle = '#F0C27A'; ctx.fillRect(pl.x, pl.y, pl.w, 6);
        ctx.strokeStyle = 'rgba(110, 65, 25, 0.55)'; ctx.lineWidth = 2;
        ctx.beginPath(); for (let x = pl.x + 40; x < pl.x + pl.w; x += 48) { ctx.moveTo(x, pl.y + 6); ctx.lineTo(x, pl.y + 26); } ctx.stroke();
        ctx.fillStyle = 'rgba(0,0,0,0.18)'; ctx.fillRect(pl.x + 4, pl.y + 26, pl.w - 8, 6);
    }

    // Transforma al sistema de dibujo del jefe y devuelve la posición del jugador en ese sistema
    function enterBossSpace() {
        const P = pose();
        ctx.translate(P.x, P.y); ctx.scale(P.s, P.s); ctx.translate(-HEAD.x, -HEAD.y);
        return { P, p: { x: HEAD.x + (S.player.x - P.x) / P.s, y: HEAD.y + (S.player.y - P.y) / P.s } };
    }

    function drawPharaoh() {
        const b = S.boss, cx = HEAD.x, cy = HEAD.y;
        ctx.save();
        const { P, p } = enterBossSpace();
        ctx.globalAlpha = 1 - 0.3 * P.k;
        const screaming = b.stage === 'grito' || b.stage === 'vuela';
        if (screaming) ctx.translate(rand(-5, 5), rand(-5, 5));
        // Tocado (nemes)
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
        ctx.fillStyle = b.flash > 0 ? '#FFFFFF' : (b.phase2 || screaming ? '#B9774A' : '#C68E4E');
        ctx.beginPath(); ctx.ellipse(cx, cy + 10, 140, 190, 0, 0, Math.PI * 2); ctx.fill();
        ctx.strokeStyle = '#7A4A20'; ctx.lineWidth = 3; ctx.stroke();
        ctx.fillStyle = '#F5C542'; ctx.fillRect(cx - 145, cy - 175, 290, 26);
        ctx.fillStyle = '#1F4FA8'; for (let i = 0; i < 7; i++) ctx.fillRect(cx - 135 + i * 42, cy - 171, 18, 18);
        ctx.fillStyle = '#F5C542'; ctx.beginPath(); ctx.ellipse(cx, cy - 200, 20, 34, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#D93030'; ctx.beginPath(); ctx.arc(cx, cy - 210, 7, 0, Math.PI * 2); ctx.fill();
        // Ojos (sin sombras: el brillo se hace con un círculo extra, mucho más liviano)
        const glowing = b.laser && b.laser.t <= C.jefe.laser_aviso;
        const angry = b.phase2 || screaming;
        EYES.forEach((e, i) => {
            if (glowing) { ctx.fillStyle = 'rgba(255, 34, 68, ' + (0.25 + 0.2 * (b.laser.t % 10) / 10) + ')'; ctx.beginPath(); ctx.ellipse(e.x, e.y, 62, 36, 0, 0, Math.PI * 2); ctx.fill(); }
            ctx.fillStyle = angry || glowing ? '#FFD0D0' : '#FFFFFF';
            ctx.beginPath(); ctx.ellipse(e.x, e.y, 44, 22, 0, 0, Math.PI * 2); ctx.fill();
            ctx.strokeStyle = '#111'; ctx.lineWidth = 6; ctx.stroke();
            ctx.beginPath(); ctx.moveTo(e.x + (i ? 40 : -40), e.y); ctx.lineTo(e.x + (i ? 78 : -78), e.y + 10); ctx.stroke();
            const a = Math.atan2(p.y - e.y, p.x - e.x), d = screaming ? rand(0, 6) : Math.min(18, Math.hypot(p.x - e.x, p.y - e.y) / 30);
            ctx.fillStyle = glowing || angry ? '#FF1133' : '#2A1A0A';
            ctx.beginPath(); ctx.arc(e.x + Math.cos(a) * d, e.y + Math.sin(a) * d * 0.6, screaming ? 8 : 13, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#000'; ctx.beginPath(); ctx.arc(e.x + Math.cos(a) * d, e.y + Math.sin(a) * d * 0.6, screaming ? 4 : 6, 0, Math.PI * 2); ctx.fill();
            ctx.strokeStyle = '#111'; ctx.lineWidth = 7; ctx.beginPath();
            const tilt = angry ? (i ? 10 : -10) : 0;
            ctx.moveTo(e.x - 46, e.y - 38 - tilt); ctx.lineTo(e.x + 46, e.y - 38 + tilt); ctx.stroke();
        });
        // Nariz y boca
        ctx.strokeStyle = '#7A4A20'; ctx.lineWidth = 4;
        ctx.beginPath(); ctx.moveTo(cx, cy - 10); ctx.lineTo(cx - 14, cy + 60); ctx.lineTo(cx + 12, cy + 64); ctx.stroke();
        if (screaming) {
            // ¡grito! boca enorme abierta
            const open = 40 + Math.sin(b.t / 3) * 8;
            ctx.fillStyle = '#2A0505'; ctx.beginPath(); ctx.ellipse(cx, cy + 120, 60, open, 0, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#B3122E'; ctx.beginPath(); ctx.ellipse(cx, cy + 120 + open * 0.45, 34, open * 0.35, 0, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#FFF2D0'; ctx.fillRect(cx - 40, cy + 120 - open + 4, 80, 8);
            // líneas de grito
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.8)'; ctx.lineWidth = 6;
            for (let j = 0; j < 5; j++) { const a = -Math.PI / 2 + (j - 2) * 0.5, r1 = 260 + (b.t * 6 % 60), r2 = r1 + 50; ctx.beginPath(); ctx.moveTo(cx + Math.cos(a) * r1, cy + 60 + Math.sin(a) * r1); ctx.lineTo(cx + Math.cos(a) * r2, cy + 60 + Math.sin(a) * r2); ctx.stroke(); }
        } else {
            ctx.lineWidth = 6; ctx.beginPath();
            if (b.phase2) { ctx.moveTo(cx - 50, cy + 120); ctx.quadraticCurveTo(cx, cy + 95, cx + 50, cy + 120); }
            else { ctx.moveTo(cx - 45, cy + 110); ctx.lineTo(cx + 45, cy + 110); }
            ctx.stroke();
        }
        ctx.fillStyle = '#E8B934'; ctx.fillRect(cx - 26, cy + 190, 52, 70);
        ctx.fillStyle = '#1F4FA8'; for (let y = cy + 200; y < cy + 260; y += 16) ctx.fillRect(cx - 26, y, 52, 7);
        ctx.restore();
    }

    function drawGiantMummy() {
        const b = S.boss, cx = HEAD.x, cy = HEAD.y;
        ctx.save();
        const { P, p } = enterBossSpace();
        ctx.globalAlpha = 1 - 0.3 * P.k;
        // aparece desde la arena (recorte bajo el montículo)
        ctx.save();
        ctx.beginPath(); ctx.rect(cx - 500, cy - 600, 1000, 1180); ctx.clip();
        let lift = 0;
        if (b.stage === 'llegada') lift = (1 - b.rise) * 520;
        if (b.stage === 'fin') lift = Math.min(560, b.t * 3.5);
        ctx.translate(lift ? rand(-3, 3) : 0, lift);
        const flash = b.flash > 0;
        const wrap = flash ? '#FFFFFF' : '#E8D9B0', dark = '#B9A67A', line = 'rgba(120, 95, 60, 0.75)';
        // brazos (el de lanzar se levanta)
        const throwA = b.armAnim > 0 ? Math.sin((24 - b.armAnim) / 24 * Math.PI) : 0;
        ctx.lineCap = 'round';
        [[-1, 0], [1, throwA]].forEach(([side, up]) => {
            const sx = cx + side * 165, sy = cy + 30;
            const ex = cx + side * (250 - up * 40), ey = cy + 150 - up * 330 + Math.sin(S.t / 30 + side) * 10;
            ctx.strokeStyle = wrap; ctx.lineWidth = 70; ctx.beginPath(); ctx.moveTo(sx, sy); ctx.lineTo(ex, ey); ctx.stroke();
            ctx.strokeStyle = line; ctx.lineWidth = 3;
            for (let j = 0.15; j < 1; j += 0.15) { const x = sx + (ex - sx) * j, y = sy + (ey - sy) * j; ctx.beginPath(); ctx.moveTo(x - 32, y - 10); ctx.lineTo(x + 32, y + 10); ctx.stroke(); }
            ctx.fillStyle = wrap; ctx.beginPath(); ctx.arc(ex, ey, 40, 0, Math.PI * 2); ctx.fill();
            if (side === 1 && throwA > 0.2) { ctx.fillStyle = '#F4ECD8'; ctx.beginPath(); ctx.ellipse(ex, ey - 30, 22, 30, 0.4, 0, Math.PI * 2); ctx.fill(); }
        });
        // torso
        ctx.fillStyle = wrap;
        ctx.beginPath(); ctx.moveTo(cx - 190, cy + 300); ctx.lineTo(cx - 175, cy + 10); ctx.quadraticCurveTo(cx, cy - 60, cx + 175, cy + 10); ctx.lineTo(cx + 190, cy + 300); ctx.closePath(); ctx.fill();
        ctx.save(); ctx.clip();
        ctx.strokeStyle = line; ctx.lineWidth = 4;
        ctx.beginPath(); for (let y = cy - 60; y < cy + 320; y += 24) { ctx.moveTo(cx - 200, y); ctx.lineTo(cx + 200, y + 40); } ctx.stroke();
        ctx.fillStyle = dark; for (let j = 0; j < 4; j++) ctx.fillRect(cx - 160 + j * 90, cy + 60 + (j % 2) * 50, 40, 14);
        if (b.phase2) { ctx.fillStyle = '#3A2A1E'; ctx.beginPath(); ctx.ellipse(cx + 60, cy + 120, 30, 50, 0.3, 0, Math.PI * 2); ctx.fill(); ctx.beginPath(); ctx.ellipse(cx - 80, cy + 200, 24, 34, -0.4, 0, Math.PI * 2); ctx.fill(); }
        ctx.restore();
        // vendas sueltas que cuelgan
        ctx.strokeStyle = wrap; ctx.lineWidth = 16;
        [[-120, 120], [90, 200], [150, 60]].forEach(([dx, dy], j) => { ctx.beginPath(); ctx.moveTo(cx + dx, cy + dy); ctx.quadraticCurveTo(cx + dx + 30 + Math.sin(S.t / 15 + j) * 20, cy + dy + 60, cx + dx + Math.sin(S.t / 12 + j) * 30, cy + dy + 130); ctx.stroke(); });
        // cabeza
        const hy = cy - 150;
        ctx.fillStyle = wrap; ctx.beginPath(); ctx.ellipse(cx, hy, 120, 135, 0, 0, Math.PI * 2); ctx.fill();
        ctx.save(); ctx.clip(); ctx.strokeStyle = line; ctx.lineWidth = 4;
        ctx.beginPath(); for (let y = hy - 140; y < hy + 140; y += 22) { ctx.moveTo(cx - 130, y + 20); ctx.lineTo(cx + 130, y - 20); } ctx.stroke(); ctx.restore();
        // hueco de los ojos y ojos que te siguen
        const eyeCol = b.phase2 ? '#33FF66' : '#FFD200';
        [[-48, -20], [48, -20]].forEach(([dx, dy]) => {
            const ex = cx + dx, ey = hy + dy;
            ctx.fillStyle = '#2A1A0A'; ctx.beginPath(); ctx.ellipse(ex, ey, 34, 22, 0, 0, Math.PI * 2); ctx.fill();
            const a = Math.atan2(p.y - ey, p.x - ex), d = Math.min(12, Math.hypot(p.x - ex, p.y - ey) / 40);
            ctx.fillStyle = eyeCol + '55'; ctx.beginPath(); ctx.arc(ex + Math.cos(a) * d, ey + Math.sin(a) * d * 0.6, 16, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = eyeCol; ctx.beginPath(); ctx.arc(ex + Math.cos(a) * d, ey + Math.sin(a) * d * 0.6, 8, 0, Math.PI * 2); ctx.fill();
        });
        // boca (rugido al llegar)
        ctx.fillStyle = '#2A1A0A';
        const roar = b.stage === 'llegada' || b.armAnim > 0 ? 26 : 10;
        ctx.beginPath(); ctx.ellipse(cx, hy + 70, 50, roar, 0, 0, Math.PI * 2); ctx.fill();
        ctx.restore();
        // montículo de arena delante
        ctx.fillStyle = '#D9A55B'; ctx.beginPath(); ctx.ellipse(cx, cy + 330, 330, 70, 0, Math.PI, 0); ctx.fill();
        ctx.fillStyle = '#F0C27A'; ctx.beginPath(); ctx.ellipse(cx, cy + 335, 300, 40, 0, Math.PI, 0); ctx.fill();
        ctx.restore();
    }

    function drawLaser() {
        const b = S.boss; if (!b.laser || b.stage !== 'faraon') return;
        const J = C.jefe;
        // Sin shadowBlur: varias pasadas con transparencia (mucho más rápido)
        for (let i = 0; i < 2; i++) {
            const e = eyePos(i), a = b.laser.angles[i], x2 = e.x + Math.cos(a) * LASER_LEN, y2 = e.y + Math.sin(a) * LASER_LEN;
            ctx.lineCap = 'round';
            if (b.laser.t <= J.laser_aviso) {
                ctx.globalAlpha = 0.3 + 0.5 * (Math.floor(b.laser.t / 5) % 2);
                ctx.strokeStyle = '#FF2244'; ctx.lineWidth = 3; ctx.setLineDash([14, 10]);
                ctx.beginPath(); ctx.moveTo(e.x, e.y); ctx.lineTo(x2, y2); ctx.stroke();
                ctx.setLineDash([]);
            } else {
                [[64, 'rgba(255, 34, 68, 0.18)'], [40, 'rgba(255, 34, 68, 0.45)'], [20, '#FF2244'], [7, '#FFF2A8']].forEach(([w, c]) => {
                    ctx.strokeStyle = c; ctx.lineWidth = w; ctx.beginPath(); ctx.moveTo(e.x, e.y); ctx.lineTo(x2, y2); ctx.stroke();
                });
            }
            ctx.globalAlpha = 1;
        }
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

    function drawRoll(o) {
        // venda que se va desenrollando detrás
        if (o.trail.length > 1) {
            ctx.strokeStyle = '#F4ECD8'; ctx.lineWidth = 9; ctx.lineCap = 'round'; ctx.beginPath();
            o.trail.forEach((q, i) => { const wv = Math.sin(i * 0.9 + S.t * 0.3) * 4; i ? ctx.lineTo(q.x + wv, q.y) : ctx.moveTo(q.x, q.y); }); ctx.stroke();
        }
        ctx.save(); ctx.translate(o.x, o.y); ctx.rotate(o.rot);
        ctx.fillStyle = '#F4ECD8'; ctx.fillRect(-16, -12, 32, 24);
        ctx.strokeStyle = '#CDBF9A'; ctx.lineWidth = 2; ctx.strokeRect(-16, -12, 32, 24);
        ctx.beginPath(); ctx.moveTo(-6, -12); ctx.lineTo(-6, 12); ctx.moveTo(6, -12); ctx.lineTo(6, 12); ctx.stroke();
        ctx.fillStyle = '#FFFFFF'; ctx.beginPath(); ctx.ellipse(16, 0, 5, 12, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#8B7355'; ctx.beginPath(); ctx.ellipse(16, 0, 2, 5, 0, 0, Math.PI * 2); ctx.fill();
        ctx.restore();
    }

    function drawAnkh(k) {
        ctx.save(); ctx.translate(k.x, k.y + Math.sin(k.t / 10) * 3);
        ctx.strokeStyle = 'rgba(51, 255, 102, 0.35)'; ctx.lineWidth = 11;
        ctx.beginPath(); ctx.ellipse(0, -10, 7, 9, 0, 0, Math.PI * 2); ctx.moveTo(0, -1); ctx.lineTo(0, 16); ctx.moveTo(-10, 3); ctx.lineTo(10, 3); ctx.stroke();
        ctx.strokeStyle = '#33FF66'; ctx.lineWidth = 5;
        ctx.beginPath(); ctx.ellipse(0, -10, 7, 9, 0, 0, Math.PI * 2); ctx.moveTo(0, -1); ctx.lineTo(0, 16); ctx.moveTo(-10, 3); ctx.lineTo(10, 3); ctx.stroke();
        ctx.restore();
    }

    function drawMummy(m) {
        ctx.save(); ctx.translate(m.x, m.y);
        if (m.rise > 0) { const p = 1 - m.rise / 40; ctx.beginPath(); ctx.rect(-40, -60, 80, 92); ctx.clip(); ctx.translate(0, (1 - p) * 64); }
        const walk = Math.sin(m.t / 6) * 6;
        ctx.fillStyle = m.flash > 0 ? '#FFFFFF' : '#E8D9B0';
        ctx.fillRect(-10 + walk * 0.3, 10, 8, 22); ctx.fillRect(2 - walk * 0.3, 10, 8, 22);
        ctx.fillRect(-14, -18, 28, 32);
        ctx.fillRect(m.dir > 0 ? 6 : -30, -12, 24, 8); ctx.fillRect(m.dir > 0 ? 6 : -30, -2, 24, 8);
        ctx.beginPath(); ctx.arc(0, -28, 13, 0, Math.PI * 2); ctx.fill();
        ctx.strokeStyle = 'rgba(120, 95, 60, 0.7)'; ctx.lineWidth = 2;
        ctx.beginPath(); for (let y = -36; y < 30; y += 7) { ctx.moveTo(-14, y); ctx.lineTo(14, y + 3); } ctx.stroke();
        ctx.fillStyle = '#FF3355'; ctx.beginPath(); ctx.arc(m.dir * 4 - 4, -30, 2.5, 0, Math.PI * 2); ctx.arc(m.dir * 4 + 4, -30, 2.5, 0, Math.PI * 2); ctx.fill();
        ctx.restore();
        if (m.rise <= 0) { ctx.fillStyle = 'rgba(0,0,0,0.5)'; ctx.fillRect(m.x - 18, m.y - 52, 36, 4); ctx.fillStyle = '#FF3355'; ctx.fillRect(m.x - 18, m.y - 52, 36 * Math.max(0, m.hp) / m.maxHp, 4); }
    }

    // ---------- Jugador pixel art ----------
    function drawPlayer() {
        const p = S.player;
        if (p.inv > 0 && p.inv < 9999 && Math.floor(p.inv / 4) % 2 === 0) return;
        const f = p.facing, feet = p.y + 35;
        const ox = Math.round((p.x - 9 * PX) / PX) * PX, oy = Math.round((feet - 24 * PX) / PX) * PX;
        ctx.save();
        if (p.charging) { const sq = 1 - 0.22 * (p.charge / C.jugador.carga_frames); ctx.translate(0, feet); ctx.scale(1, sq); ctx.translate(0, -feet); }
        // vaina en la espalda
        // vaina cruzada en la espalda: el mango asoma sobre el hombro, la punta baja hacia atrás
        const backX = ox + (f > 0 ? 7 : 11) * PX, backY = oy + 12 * PX;
        drawSheath(backX, backY, f > 0 ? Math.PI - 0.9 : 0.9, p.sword <= 0);
        // piernas
        let legs = RUNS.stand;
        if (!p.onGround) legs = RUNS.jump;
        else if (Math.abs(p.vx) > 0.5) legs = Math.floor(S.t / 7) % 2 ? RUNS.walkA : RUNS.walkB;
        drawRuns(legs, ox, oy, f);
        drawRuns(RUNS.body, ox, oy, f);
        drawRuns(RUNS.head, ox, oy, f);
        // brazo
        const shX = ox + (f > 0 ? 12 : 5) * PX + PX / 2, shY = oy + 13 * PX;
        let hx, hy;
        if (isGuarding()) {
            hx = shX + f * 18; hy = shY - 6;
        } else if (p.atk > 0) {
            const ext = p.atk > 7 ? (14 - p.atk) / 7 : p.atk / 7;
            hx = shX + Math.cos(p.atkDir) * (12 + 24 * ext); hy = shY + Math.sin(p.atkDir) * (12 + 24 * ext);
        } else { hx = shX + f * 6; hy = shY + 15; }
        pixelLine(shX, shY, hx, hy, PAL.K, 12);
        pixelLine(shX, shY, hx, hy, PAL.M, 6);
        ctx.fillStyle = PAL.K; ctx.fillRect(Math.round(hx / PX) * PX - 7, Math.round(hy / PX) * PX - 7, 14, 14);
        ctx.fillStyle = PAL.m; ctx.fillRect(Math.round(hx / PX) * PX - 4, Math.round(hy / PX) * PX - 4, 8, 8);
        // katana en la mano
        if (p.sword > 0) {
            const a = p.atk > 0 ? p.atkDir : (isGuarding() ? -Math.PI / 2 : (f > 0 ? -0.6 : Math.PI + 0.6));
            drawKatana(hx, hy, a, 24);
        }
        // escudo / postura de guardia
        if (isGuarding()) {
            const sx = Math.round((p.x + f * 30) / PX) * PX, sy = Math.round((p.y - 8) / PX) * PX;
            ctx.fillStyle = PAL.K; ctx.fillRect(sx - 12, sy - 30, 24, 60);
            ctx.fillStyle = p.blockFlash > 0 ? '#FFFFFF' : PAL.M; ctx.fillRect(sx - 9, sy - 27, 18, 54);
            ctx.fillStyle = PAL.m; ctx.fillRect(sx - 9, sy - 3, 18, 6); ctx.fillRect(sx - 3, sy - 27, 6, 54);
            ctx.fillStyle = '#BFE9FF'; ctx.fillRect(sx - 6, sy - 24, 3, 12);
        }
        ctx.restore();

        // Estela del golpe / corte
        if (p.atk > 3 && p.atk <= 11) {
            const a = attackCircle();
            ctx.globalAlpha = 0.55; ctx.strokeStyle = p.sword > 0 ? '#FF8FB8' : (p.combo === 3 ? '#FFD700' : '#FFFFFF'); ctx.lineWidth = p.sword > 0 ? 10 : 5;
            ctx.beginPath(); ctx.arc(p.x, p.y, Math.hypot(a.x - p.x, a.y - p.y) + 10, p.atkDir - 0.8, p.atkDir + 0.8); ctx.stroke();
            if (p.sword > 0) { ctx.strokeStyle = '#FFE0EA'; ctx.lineWidth = 3; ctx.stroke(); }
            ctx.globalAlpha = 1;
        }
        // Barra de carga del salto
        if (p.charging) {
            const c = p.charge / C.jugador.carga_frames;
            ctx.fillStyle = 'rgba(0,0,0,0.5)'; ctx.fillRect(p.x - 25, p.y + 44, 50, 6);
            ctx.fillStyle = c >= 1 ? '#FF3355' : '#FFD700'; ctx.fillRect(p.x - 25, p.y + 44, 50 * c, 6);
        }
        // Medidor de hundimiento
        if (p.sink > 0 && !S.over) {
            const c = p.sink / (C.arena.segundos_para_hundirse * 60);
            ctx.fillStyle = 'rgba(0,0,0,0.6)'; ctx.fillRect(p.x - 30, p.y - 72, 60, 8);
            ctx.fillStyle = '#C97A2A'; ctx.fillRect(p.x - 30, p.y - 72, 60 * c, 8);
            ctx.fillStyle = '#FFF2D0'; ctx.font = 'bold 11px sans-serif'; ctx.textAlign = 'center'; ctx.fillText('¡TE HUNDES!', p.x, p.y - 78);
        }
    }

    function drawSand() {
        if (S.sandY >= FLOOR) return;
        const y0 = S.sandY;
        ctx.fillStyle = 'rgba(201, 140, 70, 0.92)';
        ctx.beginPath(); ctx.moveTo(-400, FLOOR + 200);
        for (let x = -400; x <= W + 400; x += 40) ctx.lineTo(x, y0 + Math.sin((x + S.t * 2) / 60) * 5);
        ctx.lineTo(W + 400, FLOOR + 200); ctx.closePath(); ctx.fill();
        ctx.fillStyle = '#E8B66A';
        for (let x = -400; x <= W + 400; x += 40) ctx.fillRect(x, y0 + Math.sin((x + S.t * 2) / 60) * 5 - 2, 40, 4);
        // remolinos
        ctx.strokeStyle = 'rgba(120, 75, 30, 0.5)'; ctx.lineWidth = 3;
        for (let i = 0; i < 4; i++) {
            const x = 120 + i * 250, y = y0 + 40 + (i % 2) * 30;
            if (y > FLOOR) continue;
            ctx.beginPath(); ctx.ellipse(x, y, 40, 10, 0, S.t / 20 + i, S.t / 20 + i + 4.5); ctx.stroke();
        }
    }

    function drawHUD() {
        const p = S.player, b = S.boss, cw = canvas.width;
        ctx.save();
        // Barra del jefe
        let name = null;
        if (b.stage === 'faraon') name = `${C.jefe.nombre}${b.phase2 ? ' (FURIOSO)' : ''}`;
        if (b.stage === 'momia') name = `${C.momia_gigante.nombre}${b.phase2 ? ' (DESENVUELTA)' : ''}`;
        if (name) {
            const bw = Math.min(520, cw * 0.6), bx = (cw - bw) / 2;
            ctx.fillStyle = 'rgba(30, 15, 5, 0.85)'; ctx.fillRect(bx, 14, bw, 18);
            ctx.fillStyle = b.stage === 'momia' ? (b.phase2 ? '#33FF66' : '#E8D9B0') : (b.phase2 ? '#FF3355' : '#F5C542');
            ctx.fillRect(bx + 2, 16, (bw - 4) * Math.max(0, b.hp / b.maxHp), 14);
            ctx.strokeStyle = '#F5C542'; ctx.lineWidth = 2; ctx.strokeRect(bx, 14, bw, 18);
            ctx.fillStyle = b.stage === 'momia' ? '#1a1208' : '#FFF2D0'; ctx.font = 'bold 12px sans-serif'; ctx.textAlign = 'center';
            ctx.fillText(`${name}: ${Math.max(0, Math.ceil(b.hp))} / ${b.maxHp}`, cw / 2, 27);
        }
        // Vida
        const hs = 22;
        for (let i = 0; i < p.maxHp; i++) api.drawIcon(ctx, i < p.hp ? 'heart' : 'heartEmpty', 24 + i * (hs + 4), canvas.height - 30, hs);
        // Guardia
        ctx.fillStyle = 'rgba(0,0,0,0.6)'; ctx.fillRect(14, canvas.height - 56, 150, 9);
        ctx.fillStyle = p.guardBroken > 0 ? '#FF3355' : '#BFE9FF'; ctx.fillRect(15, canvas.height - 55, 148 * p.guard / C.guardia.max, 7);
        ctx.fillStyle = '#FFF2D0'; ctx.font = 'bold 10px sans-serif'; ctx.textAlign = 'left'; ctx.fillText(p.guardBroken > 0 ? 'GUARDIA ROTA' : 'GUARDIA (CLICK DER)', 170, canvas.height - 48);
        // Katana
        ctx.font = 'bold 14px sans-serif';
        const swTxt = p.sword > 0 ? `KATANA: ${(p.sword / 60).toFixed(1)}s` : (p.swordCd > 0 ? `KATANA: ${Math.ceil(p.swordCd / 60)}s` : '[R] KATANA LISTA');
        ctx.fillStyle = p.sword > 0 ? '#FF8FB8' : (p.swordCd > 0 ? '#999' : '#FFD700');
        ctx.fillText(swTxt, 14, canvas.height - 66);
        if (p.hitCombo >= 2) { ctx.fillStyle = '#FFD700'; ctx.font = 'bold 20px sans-serif'; ctx.fillText(`COMBO x${p.hitCombo}`, 14, canvas.height - 90); }
        // Aviso de arena
        if (S.lowTime > C.arena.segundos_para_subir * 60 * 0.7 && !S.over) {
            ctx.textAlign = 'center'; ctx.font = 'bold 16px sans-serif';
            ctx.fillStyle = Math.floor(S.t / 15) % 2 ? '#FF3355' : '#FFB257';
            ctx.fillText('¡ARENA MOVEDIZA! SUBE', cw / 2, 58);
        }
        ctx.textAlign = 'right'; ctx.font = 'bold 13px sans-serif'; ctx.fillStyle = '#FFF2D0';
        ctx.fillText(`FASE 2 · ${String(C.nombre).toUpperCase()}`, cw - 20, 27);
        ctx.fillText('[ESC] PAUSA', cw - 20, 45);
        if (S.t < 420) {
            ctx.globalAlpha = Math.min(1, (420 - S.t) / 60);
            ctx.fillStyle = 'rgba(30, 15, 5, 0.85)'; ctx.fillRect(cw / 2 - 290, canvas.height - 130, 580, 96);
            ctx.fillStyle = '#FFF2D0'; ctx.textAlign = 'center'; ctx.font = 'bold 13px sans-serif';
            ctx.fillText('A/D: CAMINAR  ·  MANTÉN ESPACIO/W: CARGAR SALTO (suelta para saltar)', cw / 2, canvas.height - 106);
            ctx.fillText('CLICK IZQ o J: GOLPE (3 seguidos = COMBO)  ·  CLICK DER: CUBRIRSE', cw / 2, canvas.height - 86);
            ctx.fillText('R: KATANA 15 s  ·  ¡No te quedes mucho abajo: la arena se vuelve movediza!', cw / 2, canvas.height - 66);
            ctx.fillText('Sube por las areniscas y golpea al Faraón en la cara', cw / 2, canvas.height - 46);
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
