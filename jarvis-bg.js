/**
 * JARVIS live wallpaper — no download needed.
 * Pinterest pins often block saves; this replaces that animation.
 */
(function () {
    const canvas = document.getElementById('jarvis-bg-canvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let w, h, cx, cy, t = 0, raf;
    const isMobile = () => window.innerWidth < 768;

    const particles = [];
    const nodes = [];
    const columns = [];
    const arcs = [];

    function resize() {
        w = window.innerWidth;
        h = window.innerHeight;
        canvas.width = w;
        canvas.height = h;
        cx = w / 2;
        cy = h * 0.44;
        buildScene();
    }

    function buildScene() {
        particles.length = 0;
        nodes.length = 0;
        columns.length = 0;
        arcs.length = 0;

        const pn = isMobile() ? 50 : 100;
        for (let i = 0; i < pn; i++) {
            particles.push({
                x: Math.random() * w,
                y: Math.random() * h,
                z: Math.random(),
                vx: (Math.random() - 0.5) * 0.6,
                vy: (Math.random() - 0.5) * 0.6
            });
        }

        const nn = isMobile() ? 14 : 24;
        for (let i = 0; i < nn; i++) {
            const ang = (i / nn) * Math.PI * 2;
            const r = Math.min(w, h) * (0.2 + Math.random() * 0.35);
            nodes.push({
                x: cx + Math.cos(ang) * r,
                y: cy + Math.sin(ang) * r * 0.85,
                pulse: Math.random() * Math.PI * 2
            });
        }

        const cn = isMobile() ? 12 : 22;
        for (let i = 0; i < cn; i++) {
            columns.push({
                x: (i / cn) * w + Math.random() * 40,
                speed: 0.4 + Math.random() * 1.2,
                offset: Math.random() * 500,
                chars: '01█░▒▓JARVISNEURALCORE'
            });
        }

        [0.18, 0.28, 0.38, 0.5, 0.62].forEach((ratio, i) => {
            arcs.push({
                r: ratio,
                speed: 0.08 + i * 0.03,
                dir: i % 2 === 0 ? 1 : -1,
                dash: 8 + i * 4
            });
        });
    }

    function drawBase() {
        const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, Math.max(w, h) * 0.7);
        g.addColorStop(0, '#1a0804');
        g.addColorStop(0.35, '#0a0302');
        g.addColorStop(1, '#020101');
        ctx.fillStyle = g;
        ctx.fillRect(0, 0, w, h);
    }

    function drawPerspectiveGrid() {
        const horizon = cy - 20;
        const lines = isMobile() ? 14 : 22;
        ctx.strokeStyle = 'rgba(255, 70, 20, 0.12)';
        ctx.lineWidth = 1;

        for (let i = 0; i < lines; i++) {
            const prog = i / lines;
            const y = horizon + Math.pow(prog, 1.8) * (h - horizon);
            const spread = 0.15 + prog * 0.85;
            ctx.beginPath();
            ctx.moveTo(cx - w * spread, y);
            ctx.lineTo(cx + w * spread, y);
            ctx.stroke();
        }

        const verts = isMobile() ? 12 : 18;
        for (let i = -verts; i <= verts; i++) {
            const x0 = cx + (i / verts) * w * 0.15;
            ctx.beginPath();
            ctx.moveTo(x0, horizon);
            ctx.lineTo(cx + i * 45, h + 50);
            ctx.stroke();
        }
    }

    function drawHexField() {
        const size = 22;
        const rowH = size * 1.72;
        const driftY = (t * 18) % rowH;
        const driftX = Math.sin(t * 0.3) * 8;

        for (let row = -1; row < h / rowH + 2; row++) {
            const y = row * rowH + driftY;
            const off = ((row % 2) * size * 1.5) + driftX;
            for (let col = -1; col < w / (size * 3) + 2; col++) {
                const x = col * size * 3 + off;
                const dist = Math.hypot(x - cx, y - cy);
                const alpha = Math.max(0.03, 0.14 - dist / Math.max(w, h) * 0.5);
                ctx.strokeStyle = `rgba(255, 90, 30, ${alpha})`;
                ctx.beginPath();
                for (let k = 0; k < 6; k++) {
                    const a = (Math.PI / 3) * k - Math.PI / 6;
                    const px = x + size * Math.cos(a);
                    const py = y + size * Math.sin(a);
                    if (k === 0) ctx.moveTo(px, py);
                    else ctx.lineTo(px, py);
                }
                ctx.closePath();
                ctx.stroke();
            }
        }
    }

    function drawArcs() {
        arcs.forEach((a, i) => {
            const radius = Math.min(w, h) * a.r * (1 + Math.sin(t * 1.2 + i) * 0.015);
            ctx.save();
            ctx.translate(cx, cy);
            ctx.rotate(t * a.speed * a.dir);
            ctx.setLineDash([a.dash, a.dash * 0.6]);
            ctx.beginPath();
            ctx.arc(0, 0, radius, 0, Math.PI * 1.35);
            ctx.strokeStyle = `rgba(255, ${100 + i * 20}, 40, ${0.2 + i * 0.05})`;
            ctx.lineWidth = 2;
            ctx.stroke();
            ctx.setLineDash([]);
            ctx.restore();
        });
    }

    function drawCenterOrb() {
        const pulse = 1 + Math.sin(t * 2) * 0.06;
        const r0 = Math.min(w, h) * 0.08 * pulse;
        const r1 = Math.min(w, h) * 0.28;

        const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, r1);
        g.addColorStop(0, 'rgba(255, 200, 120, 0.45)');
        g.addColorStop(0.15, 'rgba(255, 80, 0, 0.35)');
        g.addColorStop(0.45, 'rgba(255, 30, 0, 0.12)');
        g.addColorStop(1, 'transparent');
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(cx, cy, r1, 0, Math.PI * 2);
        ctx.fill();

        ctx.beginPath();
        ctx.arc(cx, cy, r0, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(255, 240, 200, 0.9)';
        ctx.shadowColor = '#ff5500';
        ctx.shadowBlur = 40;
        ctx.fill();
        ctx.shadowBlur = 0;

        for (let i = 0; i < 3; i++) {
            ctx.beginPath();
            ctx.arc(cx, cy, r0 + 15 + i * 12 + Math.sin(t * 3 + i) * 4, 0, Math.PI * 2);
            ctx.strokeStyle = `rgba(255, 120, 50, ${0.35 - i * 0.1})`;
            ctx.lineWidth = 1.5;
            ctx.stroke();
        }
    }

    function drawCircuit() {
        ctx.strokeStyle = 'rgba(255, 80, 30, 0.15)';
        ctx.lineWidth = 1;
        for (let i = 0; i < nodes.length; i++) {
            const a = nodes[i];
            const b = nodes[(i + 3) % nodes.length];
            const flicker = 0.5 + Math.sin(t * 2 + a.pulse) * 0.5;
            if (flicker < 0.7) continue;
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
            ctx.beginPath();
            ctx.arc(a.x, a.y, 2 + Math.sin(t + a.pulse), 0, Math.PI * 2);
            ctx.fillStyle = `rgba(255, 140, 60, ${0.4 + flicker * 0.3})`;
            ctx.fill();
        }
    }

    function drawMatrixColumns() {
        ctx.font = `${isMobile() ? 9 : 11}px monospace`;
        columns.forEach((col) => {
            const head = (col.offset + t * col.speed * 60) % (h + 200);
            for (let j = 0; j < 12; j++) {
                const y = head - j * 16;
                if (y < 0 || y > h) continue;
                const ch = col.chars[Math.floor((t * 4 + j + col.offset) % col.chars.length)];
                ctx.fillStyle = `rgba(255, 60, 20, ${0.35 - j * 0.025})`;
                ctx.fillText(ch, col.x, y);
            }
        });
    }

    function drawParticles() {
        particles.forEach((p) => {
            p.x += p.vx;
            p.y += p.vy;
            if (p.x < 0) p.x = w;
            if (p.x > w) p.x = 0;
            if (p.y < 0) p.y = h;
            if (p.y > h) p.y = 0;

            const dx = cx - p.x;
            const dy = cy - p.y;
            const dist = Math.hypot(dx, dy) || 1;
            if (dist < Math.min(w, h) * 0.35) {
                p.vx += (dx / dist) * 0.015;
                p.vy += (dy / dist) * 0.015;
            }

            const size = 0.5 + p.z * 2;
            ctx.beginPath();
            ctx.arc(p.x, p.y, size, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(255, ${120 + p.z * 80}, 60, ${0.2 + p.z * 0.4})`;
            ctx.fill();
        });
    }

    function drawHudBrackets() {
        const pad = 30;
        const len = 40;
        const corners = [
            [pad, pad], [w - pad, pad], [pad, h - pad], [w - pad, h - pad]
        ];
        ctx.strokeStyle = 'rgba(255, 80, 30, 0.25)';
        ctx.lineWidth = 2;
        corners.forEach(([x, y], i) => {
            const sx = x < cx ? 1 : -1;
            const sy = y < cy ? 1 : -1;
            ctx.beginPath();
            ctx.moveTo(x, y + sy * len);
            ctx.lineTo(x, y);
            ctx.lineTo(x + sx * len, y);
            ctx.stroke();
        });
    }

    function drawScanline() {
        const y = ((t * 50) % (h + 100)) - 50;
        const g = ctx.createLinearGradient(0, y - 40, 0, y + 40);
        g.addColorStop(0, 'transparent');
        g.addColorStop(0.5, 'rgba(255, 100, 50, 0.08)');
        g.addColorStop(1, 'transparent');
        ctx.fillStyle = g;
        ctx.fillRect(0, 0, w, h);
    }

    function frame() {
        t += 0.016;
        drawBase();
        drawPerspectiveGrid();
        drawHexField();
        drawArcs();
        drawMatrixColumns();
        drawCircuit();
        drawParticles();
        drawCenterOrb();
        drawHudBrackets();
        drawScanline();
        raf = requestAnimationFrame(frame);
    }

    window.addEventListener('resize', resize);
    resize();
    frame();

    document.addEventListener('visibilitychange', () => {
        if (document.hidden) cancelAnimationFrame(raf);
        else frame();
    });
})();
