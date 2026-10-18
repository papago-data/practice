// ============================================================
// 互动特效引擎 effects.js（自动融入相册浏览过程，无手动入口）
// 依赖 script.js 的全局：GROUPS / photos / groupIndex / bgm 等
// 可个性化内容集中在 CONFIG
// ============================================================
(function () {
  'use strict';
  if (typeof GROUPS === 'undefined') return;

  // ================= 配置区（改成你们自己的） =================
  const CONFIG = {
    // 刮刮乐：灰色/金色蒙版盖住，手指擦开才显示（仅单张组生效）
    scratch: ['images/2.jpg', 'images/11.jpg'],

    // 选择题：滑到这些照片时先答题
    quizzes: {
      'images/9.jpg': {
        q: '那天我们看完电影，我最想对你说的一句话是什么？',
        options: ['A. 电影真好看', 'B. 你真好看', 'C. 我饿了'],
        answer: 1, wrong: '笨蛋，再猜！',
        os: '其实我最想说的是：你真好看，比电影好看一百倍。'
      },
      'images/16.jpg': {
        q: '那天我们去了哪里约会？',
        options: ['A. 海边', 'B. 游乐园', 'C. 火锅店'],
        answer: 2, wrong: '笨蛋，那天我们在吃火锅啦！',
        os: '对啦，那顿火锅是我这辈子吃过最香的一次。'
      }
    },

    // 吹蜡烛 / 默契值（仅单张组）
    cakePhoto: 'images/18.jpg',
    compatPhoto: 'images/13.jpg',
    compatQuestions: [
      { q: 'TA 最喜欢的食物是？', options: ['火锅', '烧烤', '甜点', '日料'], answer: 0 },
      { q: '第一次约会去了哪里？', options: ['电影院', '海边', '游乐园', '火锅店'], answer: 3 },
      { q: 'TA 生气时最想要什么？', options: ['讲道理', '抱抱', '冷静一下', '买礼物'], answer: 1 }
    ],

    // 情话
    loveLineEvery: 6,
    loveLines: [
      '所有的温柔，都是你', '有你的日子，连风都是甜的', '想把时间，停在你看着我的眼睛',
      '你一出现，春天就到了', '往后余生，风雪是你，平淡也是你', '这一眼，就注定了是一辈子',
      '月亮很亮，亮也没用，没用也亮', '谢谢你，成为我全部的例外', '所谓浪漫，就是和你一起慢慢变老',
      '你是我的偏爱，也是唯一的例外', '走过四季，你是我最好的季节', '世界很大，但我只想赖在你身边',
      '人间本不该令我这么欣喜，但你来了', '遇见你之后，满天的星星都落进了我眼里',
      '我喜欢你，不止一年，是岁岁年年', '你是我平淡日子里，最想炫耀的糖',
      '想牵着你的手，从心动走到古稀', '我本来不习惯说爱，直到遇见了你',
      '你一笑，我就想和你过一辈子', '所有的美好，都与你有关'
    ],

    // 触发位置（组下标）：把结尾流程分散到全程，避免中段单调
    countdownGroup: 10,
    interludes: { 6: 'timeline', 20: 'wall', 27: 'wish', 30: 'capsule' },
    dashboardGroup: 24,
    starMemoryGroup: 32,

    // 时间轴
    timeline: [
      { date: '2025-04-06', title: '认识那天', text: '第一眼，就注定是特别的', img: 'images/1.jpg' },
      { date: '2025-05-20', title: '第一次牵手', text: '心跳漏了一拍', img: 'images/2.jpg' },
      { date: '2025-08-08', title: '正式在一起', text: '从此，日子有了意义', img: 'images/3.jpg' },
      { date: '2026-04-06', title: '一周年', text: '这只是开始', img: 'images/4.jpg' }
    ],

    // 许愿瓶
    bottleWishes: ['永远在一起', '一起去更多地方', '每天都有小惊喜'],

    // 背景场景（每 3 组切换一次，共 12 种）
    scenes: ['初见 · 暖粉', '樱花 · 落樱', '花海 · 繁花', '云海 · 晴空', '落日 · 晚霞', '枫叶 · 金秋', '星空 · 流星', '银河 · 星云', '萤火虫 · 夏夜', '极光 · 彩霞', '初雪 · 漫步', '海底 · 深蓝'],

    // 恋爱数据大屏（数字浪漫，改这里即可）
    dashboard: [
      { label: '我们已经相爱', value: 365, unit: '天' },
      { label: '我在心里说了', value: 1314, unit: '次我爱你' },
      { label: '我们一共聊了', value: 517, unit: '天的天' },
      { label: '一起吃过', value: 208, unit: '顿饭' },
      { label: '一起看过', value: 42, unit: '场电影' },
      { label: '手牵手走过', value: 99999, unit: '步' },
      { label: '说了', value: 365, unit: '句晚安' },
      { label: '心动的瞬间', value: 999, unit: '次' }
    ],

    // 记忆星空：每颗星是一段回忆
    memories: [
      { date: '2025-04-06', text: '第一次见面，你笑得像春天' },
      { date: '2025-05-20', text: '第一次牵手，心跳漏了一拍' },
      { date: '2025-08-08', text: '正式在一起，从此有了意义' },
      { date: '2026-04-06', text: '一周年，爱还在继续' },
      { date: '每次看你', text: '依然会心动' },
      { date: '每次吵架', text: '最后都会和好' },
      { date: '每天', text: '想你的次数，数不清' },
      { date: '今天', text: '还是很喜欢你' }
    ]
  };

  // ================= 工具 =================
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));
  function safePlay(el) { try { const p = el.play(); if (p && p.catch) p.catch(() => {}); } catch (e) {} }

  let cctx = null, ccanvas = null, cparts = [], craf = null;
  function confetti(count = 120) {
    if (!ccanvas) {
      ccanvas = document.createElement('canvas');
      ccanvas.style.cssText = 'position:fixed;inset:0;pointer-events:none;z-index:99999;';
      document.body.appendChild(ccanvas);
      cctx = ccanvas.getContext('2d');
    }
    ccanvas.width = innerWidth; ccanvas.height = innerHeight;
    const colors = ['#ff6b81', '#ffb6c1', '#e83e8c', '#ffd166', '#ff9f1c', '#9b5de5', '#4cc9f0', '#f4f1de'];
    for (let i = 0; i < count; i++) cparts.push({
      x: Math.random() * innerWidth, y: -20 - Math.random() * 200,
      w: 6 + Math.random() * 6, h: 8 + Math.random() * 8,
      c: colors[(Math.random() * colors.length) | 0],
      vy: 2 + Math.random() * 3, vx: -1.5 + Math.random() * 3,
      rot: Math.random() * Math.PI, vr: -0.15 + Math.random() * 0.3
    });
    if (!craf) (function tick() {
      cctx.clearRect(0, 0, ccanvas.width, ccanvas.height);
      cparts.forEach(p => { p.x += p.vx; p.y += p.vy; p.rot += p.vr; cctx.save(); cctx.translate(p.x, p.y); cctx.rotate(p.rot); cctx.fillStyle = p.c; cctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h); cctx.restore(); });
      cparts = cparts.filter(p => p.y < innerHeight + 30);
      if (cparts.length) craf = requestAnimationFrame(tick); else { craf = null; cctx.clearRect(0, 0, ccanvas.width, ccanvas.height); }
    })();
  }

  // 真实烟花（canvas 爆炸粒子）
  let fwCtx = null, fwCanvas = null, fwParts = [], fwRAF = null;
  function fireworks(count = 4) {
    if (!fwCanvas) {
      fwCanvas = document.createElement('canvas');
      fwCanvas.style.cssText = 'position:fixed;inset:0;pointer-events:none;z-index:99998;';
      document.body.appendChild(fwCanvas);
      fwCtx = fwCanvas.getContext('2d');
    }
    fwCanvas.width = innerWidth; fwCanvas.height = innerHeight;
    const colors = ['#ff6b81', '#ffd166', '#e83e8c', '#4cc9f0', '#9b5de5', '#ff9f1c', '#80ffdb', '#ffb6c1'];
    let launched = 0;
    function launch() {
      if (launched >= count) return;
      launched++;
      const x = innerWidth * (0.2 + Math.random() * 0.6);
      const y = innerHeight * (0.15 + Math.random() * 0.35);
      const color = colors[(Math.random() * colors.length) | 0];
      const n = 50;
      for (let i = 0; i < n; i++) {
        const a = (i / n) * Math.PI * 2;
        const sp = 2 + Math.random() * 4.5;
        fwParts.push({ x, y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, life: 1, decay: 0.012 + Math.random() * 0.014, color });
      }
      setTimeout(launch, 340);
    }
    launch();
    if (!fwRAF) {
      (function tick() {
        fwCtx.clearRect(0, 0, fwCanvas.width, fwCanvas.height);
        fwParts.forEach(p => {
          p.x += p.vx; p.y += p.vy; p.vy += 0.05; p.vx *= 0.99; p.vy *= 0.99; p.life -= p.decay;
          fwCtx.globalAlpha = Math.max(p.life, 0);
          fwCtx.fillStyle = p.color;
          fwCtx.fillRect(p.x, p.y, 3, 3);
        });
        fwParts = fwParts.filter(p => p.life > 0);
        fwCtx.globalAlpha = 1;
        if (fwParts.length) fwRAF = requestAnimationFrame(tick);
        else { fwRAF = null; fwCtx.clearRect(0, 0, fwCanvas.width, fwCanvas.height); }
      })();
    }
  }

  let actx = null;
  function shutterClick() {
    try {
      actx = actx || new (window.AudioContext || window.webkitAudioContext)();
      if (actx.state === 'suspended') actx.resume();
      const dur = 0.06, buf = actx.createBuffer(1, actx.sampleRate * dur, actx.sampleRate), d = buf.getChannelData(0);
      for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / d.length, 3);
      const src = actx.createBufferSource(); src.buffer = buf;
      const g = actx.createGain(); g.gain.value = 0.5;
      const f = actx.createBiquadFilter(); f.type = 'highpass'; f.frequency.value = 2000;
      src.connect(f); f.connect(g); g.connect(actx.destination); src.start();
    } catch (e) {}
  }

  function showModal(html, opts) {
    opts = opts || {};
    const o = $('#fx-modal'); $('#fx-modal-body').innerHTML = html; o.classList.remove('hidden');
    if (opts.noClose) o.dataset.noclose = '1'; else delete o.dataset.noclose;
  }
  function hideModal() { $('#fx-modal').classList.add('hidden'); }

  // ================= 转场（12 种） =================
  let tfIdx = 0;
  function applyTransition() {
    const c = $('#stage'); if (!c) return;
    const n = tfIdx++ % 12;
    for (let i = 0; i < 12; i++) c.classList.remove('tf-' + i);
    void c.offsetWidth;
    c.classList.add('tf-' + n);
  }

  // ================= 相框（12 种） =================
  function applyFrame(index) {
    const f = $('#polaroid-frame'); if (!f) return;
    for (let i = 0; i < 12; i++) f.classList.remove('frame-' + i);
    f.classList.add('frame-' + (index % 12));
  }

  // ================= 背景场景（12 种，真实元素粒子） =================
  const SCENE_FX = {
    0: { type: 'heart', colors: ['#ff6b81', '#e83e8c', '#ff9fb8'], count: 50 },
    1: { type: 'petal', colors: ['#ffd3e2', '#ffa6c6', '#ff8fb2'], count: 85 },
    2: { type: 'petal', colors: ['#ff9fb8', '#ff7fa2', '#ffb3c9'], count: 85 },
    3: { type: 'cloud', colors: ['#ffffff', '#eef6ff'], count: 12 },
    4: { type: 'petal', colors: ['#ffb877', '#f7a85c', '#ffd7a8'], count: 65 },
    5: { type: 'leaf', colors: ['#f5a623', '#e07000', '#b84000', '#ffcf73'], count: 85 },
    6: { type: 'star', colors: ['#ffffff', '#d3e0ff', '#b8ccf0'], count: 65 },
    7: { type: 'star', colors: ['#e6dfff', '#c8bcf0', '#ffffff'], count: 60 },
    8: { type: 'firefly', colors: ['#ffe066', '#d9e86a', '#fff3b0'], count: 55 },
    9: { type: 'star', colors: ['#ffffff', '#b8f0e8'], count: 30 },
    10: { type: 'flake', colors: ['#ffffff', '#eef4fb', '#dce8f5'], count: 75 },
    11: { type: 'bubble', colors: ['#ffffff', '#d0ecf5', '#a8dce8'], count: 60 }
  };

  function renderSceneFx(scene) {
    const cfg = SCENE_FX[scene] || SCENE_FX[0];
    const fx = $('#scene-fx');
    if (!fx) return;
    fx.innerHTML = '';
    for (let i = 0; i < cfg.count; i++) {
      const el = document.createElement('span');
      el.className = 'fx fx-' + cfg.type;
      const size = (cfg.type === 'cloud' ? 60 + Math.random() * 60 : 12 + Math.random() * 20);
      const color = cfg.colors[(Math.random() * cfg.colors.length) | 0];
      el.style.left = (Math.random() * 100) + '%';
      el.style.animationDuration = (5 + Math.random() * 8) + 's';
      el.style.animationDelay = (Math.random() * 6) + 's';
      if (cfg.type === 'star' || cfg.type === 'firefly' || cfg.type === 'cloud') {
        el.style.top = (Math.random() * 90) + '%';
      }
      if (cfg.type === 'star') {
        el.textContent = '✦';
        el.style.fontSize = size + 'px';
        el.style.color = color;
        el.style.textShadow = '0 0 8px ' + color;
      } else if (cfg.type === 'firefly') {
        el.style.width = size + 'px'; el.style.height = size + 'px';
        el.style.background = color;
        el.style.boxShadow = '0 0 14px 5px ' + color;
      } else if (cfg.type === 'bubble') {
        el.style.width = size + 'px'; el.style.height = size + 'px';
        el.style.background = 'none';
        el.style.border = '1px solid ' + color;
      } else {
        el.style.width = size + 'px'; el.style.height = size + 'px';
        el.style.background = color;
      }
      fx.appendChild(el);
    }
  }

  let currentScene = -1;
  let photoCount = 0;
  function applyScene(sceneNum) {
    if (sceneNum === currentScene) return;
    currentScene = sceneNum;
    for (let i = 0; i < 12; i++) document.body.classList.remove('scene-' + i);
    document.body.classList.add('scene-' + sceneNum);
    renderSceneFx(sceneNum);
  }

  // ================= 情话 toast =================
  let loveIdx = 0;
  function showLoveToast() {
    const line = CONFIG.loveLines[loveIdx++ % CONFIG.loveLines.length];
    const t = document.createElement('div');
    t.className = 'love-toast'; t.textContent = '💌 ' + line;
    document.body.appendChild(t);
    setTimeout(() => t.remove(), 3200);
  }

  // ================= 刮刮乐（金色礼盒质感，擦开有彩带） =================
  let sLayer = null, sCtx = null, scratching = false;
  function ensureScratch() {
    if (sLayer) { if (sLayer.parentNode) return; }
    const c = $('#stage');
    sLayer = document.createElement('canvas');
    sLayer.className = 'scratch-canvas';
    sLayer.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;touch-action:none;z-index:5;cursor:crosshair;';
    c.appendChild(sLayer);
    sCtx = sLayer.getContext('2d');
    sLayer.addEventListener('pointerdown', e => { scratching = true; e.target.setPointerCapture(e.pointerId); scratchErase(e); });
    sLayer.addEventListener('pointermove', e => { if (scratching) scratchErase(e); });
    sLayer.addEventListener('pointerup', () => { scratching = false; checkReveal(); });
  }
  function scratchErase(e) {
    const r = sLayer.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
    sCtx.globalCompositeOperation = 'destination-out';
    sCtx.beginPath(); sCtx.arc(x, y, 30, 0, Math.PI * 2); sCtx.fill();
  }
  function scratchReset() {
    ensureScratch();
    sLayer.style.display = 'block'; sLayer.style.opacity = '1'; sLayer.style.transition = 'none';
    sLayer.width = sLayer.clientWidth; sLayer.height = sLayer.clientHeight;
    const g = sCtx.createLinearGradient(0, 0, sLayer.width, sLayer.height);
    g.addColorStop(0, '#e8b85a'); g.addColorStop(0.5, '#d9a441'); g.addColorStop(1, '#c89030');
    sCtx.globalCompositeOperation = 'source-over';
    sCtx.fillStyle = g; sCtx.fillRect(0, 0, sLayer.width, sLayer.height);
    sCtx.fillStyle = 'rgba(255,255,255,.85)';
    sCtx.font = '600 18px sans-serif'; sCtx.textAlign = 'center';
    sCtx.fillText('🎁 刮开看看', sLayer.width / 2, sLayer.height / 2);
  }
  function scratchHide() { if (sLayer) sLayer.style.display = 'none'; }
  function checkReveal() {
    if (!sCtx) return;
    const d = sCtx.getImageData(0, 0, sLayer.width, sLayer.height).data; let clear = 0, total = d.length / 4;
    for (let i = 3; i < d.length; i += 4) if (d[i] < 80) clear++;
    if (clear / total > 0.35) {
      sLayer.style.transition = 'opacity .5s'; sLayer.style.opacity = '0';
      fireworks(2);
      setTimeout(scratchHide, 500);
    }
  }

  // ================= 选择题 =================
  function askQuiz(item) {
    const q = CONFIG.quizzes[item.src]; if (!q) return;
    const optsHtml = q.options.map((o, i) => `<button class="quiz-opt" data-i="${i}">${o}</button>`).join('');
    showModal(`<div class="quiz"><p class="quiz-q">${q.q}</p><div class="quiz-opts">${optsHtml}</div><p class="quiz-msg"></p></div>`, { noClose: true });
    $$('#fx-modal .quiz-opt').forEach(btn => btn.addEventListener('click', () => {
      const i = +btn.dataset.i, msg = $('#fx-modal .quiz-msg');
      if (i === q.answer) {
        btn.classList.add('right'); msg.textContent = q.os; msg.style.color = '#2a9d8f'; fireworks(3); setTimeout(hideModal, 1600);
      } else {
        btn.classList.add('wrong'); msg.textContent = q.wrong; msg.style.color = '#e63946';
        const b = $('#fx-modal-body'); b.classList.remove('shake'); void b.offsetWidth; b.classList.add('shake');
        setTimeout(() => btn.classList.remove('wrong'), 500);
      }
    }));
  }

  // ================= 默契值 =================
  function askCompat() {
    let qi = 0, score = 0; const qs = CONFIG.compatQuestions;
    (function render() {
      if (qi >= qs.length) {
        const pct = Math.round(score / qs.length * 100);
        const msg = pct >= 80 ? '天生一对，默契满分！' : pct >= 50 ? '不错哦，继续加油～' : '看来还要多约几次会 😏';
        showModal(`<div class="compat"><div class="ring" style="--p:${pct}%"><b>${pct}%</b></div><p class="compat-msg">${msg}</p><button class="fx-close-btn" data-close="compat">收下</button></div>`);
        fireworks(4); return;
      }
      const q = qs[qi];
      showModal(`<div class="compat"><p class="compat-q">${qi + 1}/${qs.length}　${q.q}</p><div class="compat-opts">${q.options.map((o, i) => `<button class="quiz-opt" data-i="${i}">${o}</button>`).join('')}</div></div>`, { noClose: true });
      $$('#fx-modal .quiz-opt').forEach(btn => btn.addEventListener('click', () => {
        if (+btn.dataset.i === q.answer) { score++; btn.classList.add('right'); } else btn.classList.add('wrong');
        qi++; setTimeout(render, 450);
      }));
    })();
  }

  // ================= 吹蜡烛 =================
  let cakeShown = false;
  function askCake() {
    if (cakeShown) return; cakeShown = true;
    showModal(`<div class="cake"><div class="cake-scene"><div class="flame" id="flame"></div><div class="cake-body">🎂</div></div><p class="cake-hint">对着手机麦克风，吹一口气熄灭蜡烛</p><p class="cake-status" id="cake-status"></p><button class="fx-close-btn" data-close="cake" id="cake-skip">跳过</button></div>`, { noClose: true });
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) { $('#cake-status').textContent = '当前浏览器不支持麦克风，点"跳过"继续'; return; }
    navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
      actx = actx || new (window.AudioContext || window.webkitAudioContext)();
      const src = actx.createMediaStreamSource(stream), ana = actx.createAnalyser(); ana.fftSize = 1024; src.connect(ana);
      const data = new Uint8Array(ana.fftSize); let blown = 0;
      (function poll() {
        if (!$('#flame')) { stream.getTracks().forEach(t => t.stop()); return; }
        ana.getByteTimeDomainData(data); let sum = 0;
        for (let i = 0; i < data.length; i++) { const v = (data[i] - 128) / 128; sum += v * v; }
        const rms = Math.sqrt(sum / data.length);
        if (rms > 0.22) { if (++blown > 12) { extinguish(stream); return; } } else blown = Math.max(0, blown - 2);
        requestAnimationFrame(poll);
      })();
    }).catch(() => { $('#cake-status').textContent = '未授权麦克风，点"跳过"继续'; });
  }
  function extinguish(stream) {
    if (stream) stream.getTracks().forEach(t => t.stop());
    const f = $('#flame'); if (f) f.classList.add('out');
    $('#cake-status').textContent = '呼——吹灭啦！'; fireworks(5);
    setTimeout(() => showModal(`<div class="surprise"><div class="cake-emoji">🕯️</div><p class="s-title">愿望实现啦</p><p class="s-sub">吹灭蜡烛的这一刻，许下的愿望都会实现 ❤️</p><button class="fx-close-btn" data-close="cake">收下</button></div>`), 1200);
  }

  // ================= 假倒计时（5 秒，关音乐） =================
  let cdDone = false;
  function runCountdown() {
    if (cdDone) return; cdDone = true;
    if (typeof bgm !== 'undefined' && !bgm.paused) bgm.pause();
    const layer = $('#crash-layer');
    layer.classList.remove('hidden');
    let n = 10;
    const numEl = $('#crash-num'), barEl = $('#crash-bar');
    const t = setInterval(() => {
      n--;
      if (n > 0) { numEl.textContent = n; barEl.style.width = ((10 - n) / 10 * 100) + '%'; }
      else {
        clearInterval(t);
        layer.classList.add('hidden');
        if (typeof bgm !== 'undefined') bgm.play().catch(() => {});
        showModal(`<div class="surprise"><div class="cake-emoji">🎂</div><p class="s-title">骗你的！一周年快乐</p><p class="s-sub">未来的时间还很长，我们慢慢走 ❤️</p><button class="fx-close-btn" data-close="surprise">继续看</button></div>`);
        fireworks(6);
      }
    }, 1000);
  }

  // ================= 心跳 =================
  function injectHeartbeat() {
    const fw = $('#final-words'); if (!fw || $('#heartbeat-box')) return;
    const box = document.createElement('div'); box.id = 'heartbeat-box';
    box.innerHTML = `<p class="hb-hint">按住这颗心，听我的心跳</p><div class="hb-heart" id="hb-heart">❤</div><svg class="hb-ecg" viewBox="0 0 300 60"><polyline points="0,30 60,30 70,30 76,12 84,48 90,30 100,30 106,30 112,6 120,54 126,30 140,30 160,30 166,30 172,14 180,46 186,30 200,30 220,30 226,30 232,10 240,50 246,30 260,30 300,30"/></svg><p class="hb-status" id="hb-status"></p>`;
    fw.appendChild(box);
    let vib = null; const h = $('#hb-heart'), status = $('#hb-status');
    const on = () => { h.classList.add('beating'); status.textContent = '砰砰砰… 这是我的心跳，你听到了吗？'; status.classList.add('on'); if (navigator.vibrate) vib = setInterval(() => navigator.vibrate([180, 90, 180, 90, 180, 500]), 1200); };
    const off = () => { h.classList.remove('beating'); status.classList.remove('on'); if (vib) { clearInterval(vib); vib = null; } if (navigator.vibrate) navigator.vibrate(0); };
    h.addEventListener('pointerdown', on); h.addEventListener('pointerup', off); h.addEventListener('pointerleave', off);
  }

  // ================= 中段插曲 =================
  const WISH_KEY = 'anniversary-wishes', CAP_KEY = 'anniversary-capsule';
  function loadWishes() { try { return JSON.parse(localStorage.getItem(WISH_KEY)) || CONFIG.bottleWishes.slice(); } catch (e) { return CONFIG.bottleWishes.slice(); } }
  function saveWishes(w) { try { localStorage.setItem(WISH_KEY, JSON.stringify(w)); } catch (e) {} }
  function openTimeline() {
    const items = CONFIG.timeline.map(t => `<div class="tl-item"><div class="tl-dot"></div><div class="tl-card"><span class="tl-date">${t.date}</span><b class="tl-title">${t.title}</b><p class="tl-text">${t.text}</p>${t.img ? `<img class="tl-img" src="${t.img}" alt="">` : ''}</div></div>`).join('');
    showModal(`<div class="timeline"><p class="tl-head">我们的时间线</p>${items}<button class="fx-close-btn" data-close="timeline">继续翻相册</button></div>`);
  }
  function openWall() {
    const cells = photos.filter(p => p.type === 'image').slice(0, 12).map(p => `<div class="wall-cell"><img src="${p.src}" loading="lazy" alt=""></div>`).join('');
    showModal(`<div class="wall"><p class="wall-head">一路走来的照片</p><div class="wall-grid">${cells}</div><button class="fx-close-btn" data-close="wall">继续翻相册</button></div>`);
  }
  function openWish() {
    const wishes = loadWishes().map((w, i) => `<span class="wish" style="animation-delay:${i * 0.1}s">${w}</span>`).join('');
    showModal(`<div class="bottle"><p class="bottle-head">🍾 许愿瓶</p><div class="bottle-jar">${wishes}</div><div class="bottle-input"><input id="wish-input" placeholder="写下你们的愿望..." maxlength="20"><button class="fx-close-btn wish-add" id="wish-add">投进去</button></div><button class="fx-close-btn" data-close="bottle">继续翻相册</button></div>`);
    const add = () => { const inp = $('#wish-input'), v = (inp.value || '').trim(); if (!v) return; const w = loadWishes(); w.push(v); saveWishes(w); $('.bottle-jar').insertAdjacentHTML('beforeend', `<span class="wish">${v}</span>`); inp.value = ''; };
    const wb = $('#wish-add'), wi = $('#wish-input'); if (wb) wb.addEventListener('click', add); if (wi) wi.addEventListener('keydown', e => { if (e.key === 'Enter') add(); });
  }
  function openCapsule() {
    let saved = null; try { saved = JSON.parse(localStorage.getItem(CAP_KEY)); } catch (e) {}
    if (saved) { showModal(`<div class="capsule"><p class="cap-emoji">⏳</p><p class="cap-title">已封存，一年后的今天开启</p><button class="fx-close-btn" data-close="capsule">继续翻相册</button></div>`); return; }
    showModal(`<div class="capsule"><p class="cap-emoji">✉️</p><p class="cap-title">写给一年后的我们</p><textarea id="cap-text" maxlength="200" placeholder="想对一年后的 TA 说..."></textarea><button class="fx-close-btn cap-seal" id="cap-seal">封存 💌</button></div>`);
    $('#cap-seal').addEventListener('click', () => {
      const v = ($('#cap-text').value || '').trim();
      if (!v) { $('#cap-text').style.borderColor = '#e63946'; return; }
      try { localStorage.setItem(CAP_KEY, JSON.stringify({ text: v, at: Date.now() })); } catch (e) {}
      fireworks(3);
      showModal(`<div class="capsule"><p class="cap-emoji">⏳</p><p class="cap-title">已封存，一年后的今天开启</p><button class="fx-close-btn" data-close="capsule">继续翻相册</button></div>`);
    });
  }
  const interludeShown = {};
  function maybeInterlude(index) {
    const kind = CONFIG.interludes[index];
    if (kind && !interludeShown[kind]) {
      interludeShown[kind] = true;
      if (kind === 'timeline') openTimeline();
      else if (kind === 'wall') openWall();
      else if (kind === 'wish') openWish();
      else if (kind === 'capsule') openCapsule();
    }
  }

  // ================= 恋爱数据大屏 =================
  function openDashboard() {
    const layer = $('#dashboard');
    const grid = $('#db-grid');
    grid.innerHTML = CONFIG.dashboard.map(d => `<div class="db-card"><b class="db-num" data-v="${d.value}">0</b><span class="db-label">${d.label}</span><em class="db-unit">${d.unit}</em></div>`).join('');
    layer.classList.remove('hidden');
    $$('#db-grid .db-num').forEach((el, i) => {
      const target = CONFIG.dashboard[i].value;
      const dur = 1200 + i * 120;
      const t0 = performance.now();
      (function step(now) {
        const p = Math.min((now - t0) / dur, 1);
        el.textContent = Math.round(target * p).toLocaleString();
        if (p < 1) requestAnimationFrame(step);
      })(t0);
    });
  }

  // ================= 记忆星空 =================
  function openStarMemory() {
    const layer = $('#star-memory');
    const sky = $('#star-sky');
    sky.innerHTML = '';
    CONFIG.memories.forEach((m, i) => {
      const s = document.createElement('button');
      s.className = 'mstar';
      s.style.left = (6 + Math.random() * 88) + '%';
      s.style.top = (12 + Math.random() * 66) + '%';
      s.style.animationDelay = (Math.random() * 2.5) + 's';
      s.textContent = '✦';
      s.addEventListener('click', () => {
        const pop = $('#star-pop');
        pop.innerHTML = `<b>${m.date}</b><p>${m.text}</p>`;
        pop.classList.remove('hidden');
        clearTimeout(s._t);
        s._t = setTimeout(() => pop.classList.add('hidden'), 3000);
      });
      sky.appendChild(s);
    });
    layer.classList.remove('hidden');
  }

  // ================= 孔明灯 + 结尾 =================
  function openLanterns() {
    const layer = $('#lantern-layer'); layer.classList.remove('hidden');
    layer.onclick = e => { if (!e.target.closest('[data-close]')) spawnLantern(e.clientX, e.clientY); };
  }
  function spawnLantern(x, y) {
    const l = document.createElement('div'); l.className = 'lantern';
    l.style.left = (x - 23) + 'px'; l.style.top = (y - 30) + 'px';
    const dur = (6 + Math.random() * 4).toFixed(1); l.style.animationDuration = dur + 's';
    $('#lantern-layer').appendChild(l); setTimeout(() => l.remove(), dur * 1000);
  }
  function injectEnding() {
    const fw = $('#final-words'); if (!fw || $('#ending-box')) return;
    const box = document.createElement('div'); box.id = 'ending-box';
    box.innerHTML = `<button class="ep-lantern" id="ep-lantern">🏮 放一盏孔明灯许愿</button>`;
    fw.appendChild(box);
    $('#ep-lantern').addEventListener('click', openLanterns);
  }

  // ================= 挂到相册流程 =================
  let introShot = false;
  window.__onGroup = function (group, index) {
    const single = group.layout === 'single' ? group.items[0] : null;
    applyTransition();
    applyFrame(index);
    applyScene(Math.floor(photoCount / 3) % 12);
    photoCount += group.items.length;
    if (!introShot) { introShot = true; const fl = $('#flash'); if (fl) { fl.classList.add('on'); setTimeout(() => fl.classList.remove('on'), 180); } shutterClick(); }
    if (single) {
      handleScratch(single);
      askQuiz(single);
      if (single.src === CONFIG.compatPhoto) askCompat();
      if (single.src === CONFIG.cakePhoto) askCake();
    } else {
      scratchHide();
    }
    maybeInterlude(index);
    if (CONFIG.loveLineEvery > 0 && index > 0 && index % CONFIG.loveLineEvery === 0) showLoveToast();
    if (index === CONFIG.countdownGroup) runCountdown();
    if (index === CONFIG.dashboardGroup) openDashboard();
    if (index === CONFIG.starMemoryGroup) openStarMemory();
    if (index === GROUPS.length - 1) { setTimeout(injectHeartbeat, 600); injectEnding(); }
  };
  function handleScratch(item) { if (CONFIG.scratch.indexOf(item.src) >= 0 && item.type === 'image') scratchReset(); else scratchHide(); }

  // 点击双张/九宫格照片放大查看
  document.addEventListener('click', e => {
    const img = e.target.closest('.stage-double img, .stage-grid img');
    if (img && img.src) showModal(`<div class="wall-lightbox"><img src="${img.src}" alt=""><button class="fx-close-btn" data-close="lightbox">关闭</button></div>`);
  });

  // 关闭弹窗
  document.addEventListener('click', e => {
    const c = e.target.closest('[data-close]');
    if (c) {
      const what = c.dataset.close;
      if (what === 'lantern') { $('#lantern-layer').classList.add('hidden'); return; }
      if (what === 'starmemory') { $('#star-memory').classList.add('hidden'); return; }
      if (what === 'dashboard') { $('#dashboard').classList.add('hidden'); return; }
      hideModal(); return;
    }
    if (e.target.id === 'fx-modal' && !$('#fx-modal').dataset.noclose) hideModal();
  });

  // 开场阶段也渲染场景粒子（默认暖粉花瓣），让 30 秒开场有氛围
  renderSceneFx(0);
})();
