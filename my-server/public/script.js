// ================= 配置区 =================
const introText = "宝宝，今天是我们的一周年纪念日。准备好翻开我们的回忆了吗？";

// 背景音乐 (按顺序播放)
const bgmList = ["bgm1.mp3", "bgm2.mp3", "bgm3.mp3", "bgm4.mp3"];

// 【核心】照片与视频列表 (type区分图片视频，支持横版视频)
// 已包含 images 目录下全部 73 张照片 + 1 个视频
const photos = [
  { type: "image", src: "images/7.jpg", text: "这是我们绑定关系的日子（虽然不是情侣关系)" },
  { type: "image", src: "images/2.jpg", text: "第一次牵手，心跳得好快" },
  { type: "video", src: "videos/memory.mp4", text: "看，这是属于我们的小电影" },
  { type: "image", src: "images/3.jpg", text: "吵过架，但更懂彼此了" },
  { type: "image", src: "images/4.jpg", text: "谢谢你陪我的这一年" },
  { type: "image", src: "images/5.jpg", text: "你眼里有光，我眼里是你" },
  { type: "image", src: "images/6.jpg", text: "和你在一起，连空气都是甜的" },
  { type: "image", src: "images/1.jpg", text: "第一次见你，觉得你闪闪发光" },
  { type: "image", src: "images/8.jpg", text: "心动这件事，我对你反复发生" },
  { type: "image", src: "images/9.jpg", text: "遇见你，是我最大的好运" },
  { type: "image", src: "images/10.jpg", text: "想把你，写进我所有的未来里" },
  { type: "image", src: "images/11.jpg", text: "人间本不该令我这么欣喜，但你来了" },
  { type: "image", src: "images/12.jpg", text: "所有的温柔，都是你" },
  { type: "image", src: "images/13.jpg", text: "有你的日子，风都是甜的" },
  { type: "image", src: "images/14.jpg", text: "想把时间，停在你的眼睛里" },
  { type: "image", src: "images/15.jpg", text: "我们的小世界，刚刚好" },
  { type: "image", src: "images/16.jpg", text: "你一笑，春天就来了" },
  { type: "image", src: "images/17.jpg", text: "平凡日子，因为有你而发光" },
  { type: "image", src: "images/18.jpg", text: "往后余生，请多指教" },
  { type: "image", src: "images/19.jpg", text: "这一眼，就注定了是一辈子" },
  { type: "image", src: "images/20.jpg", text: "和你的每一帧，都值得珍藏" },
  { type: "image", src: "images/21.jpg", text: "月亮很亮，但你更亮" },
  { type: "image", src: "images/22.jpg", text: "谢谢你，成为我的例外" },
  { type: "image", src: "images/23.jpg", text: "所谓浪漫，就是和你慢慢变老" },
  { type: "image", src: "images/24.jpg", text: "你是我的偏爱，也是唯一" },
  { type: "image", src: "images/25.jpg", text: "走过四季，你是我最好的季节" },
  { type: "image", src: "images/26.jpg", text: "世界很大，我只想待在你身边" },
  { type: "image", src: "images/27.jpg", text: "所有的温柔，都是你" },
  { type: "image", src: "images/28.jpg", text: "有你的日子，风都是甜的" },
  { type: "image", src: "images/29.jpg", text: "想把时间，停在你的眼睛里" },
  { type: "image", src: "images/30.jpg", text: "我们的小世界，刚刚好" },
  { type: "image", src: "images/31.jpg", text: "你一笑，春天就来了" },
  { type: "image", src: "images/32.jpg", text: "平凡日子，因为有你而发光" },
  { type: "image", src: "images/33.jpg", text: "往后余生，请多指教" },
  { type: "image", src: "images/34.jpg", text: "这一眼，就注定了是一辈子" },
  { type: "image", src: "images/35.jpg", text: "和你的每一帧，都值得珍藏" },
  { type: "image", src: "images/36.jpg", text: "月亮很亮，但你更亮" },
  { type: "image", src: "images/37.jpg", text: "谢谢你，成为我的例外" },
  { type: "image", src: "images/38.jpg", text: "所谓浪漫，就是和你慢慢变老" },
  { type: "image", src: "images/39.jpg", text: "你是我的偏爱，也是唯一" },
  { type: "image", src: "images/40.jpg", text: "走过四季，你是我最好的季节" },
  { type: "image", src: "images/41.jpg", text: "世界很大，我只想待在你身边" },
  { type: "image", src: "images/42.jpg", text: "所有的温柔，都是你" },
  { type: "image", src: "images/43.jpg", text: "有你的日子，风都是甜的" },
  { type: "image", src: "images/44.jpg", text: "想把时间，停在你的眼睛里" },
  { type: "image", src: "images/45.jpg", text: "我们的小世界，刚刚好" },
  { type: "image", src: "images/46.jpg", text: "你一笑，春天就来了" },
  { type: "image", src: "images/47.jpg", text: "平凡日子，因为有你而发光" },
  { type: "image", src: "images/48.jpg", text: "往后余生，请多指教" },
  { type: "image", src: "images/49.jpg", text: "这一眼，就注定了是一辈子" },
  { type: "image", src: "images/50.jpg", text: "和你的每一帧，都值得珍藏" },
  { type: "image", src: "images/51.jpg", text: "月亮很亮，但你更亮" },
  { type: "image", src: "images/52.jpg", text: "谢谢你，成为我的例外" },
  { type: "image", src: "images/53.jpg", text: "所谓浪漫，就是和你慢慢变老" },
  { type: "image", src: "images/54.jpg", text: "你是我的偏爱，也是唯一" },
  { type: "image", src: "images/55.jpg", text: "走过四季，你是我最好的季节" },
  { type: "image", src: "images/56.jpg", text: "世界很大，我只想待在你身边" },
  { type: "image", src: "images/57.jpg", text: "所有的温柔，都是你" },
  { type: "image", src: "images/58.jpg", text: "有你的日子，风都是甜的" },
  { type: "image", src: "images/59.jpg", text: "想把时间，停在你的眼睛里" },
  { type: "image", src: "images/60.jpg", text: "我们的小世界，刚刚好" },
  { type: "image", src: "images/61.jpg", text: "你一笑，春天就来了" },
  { type: "image", src: "images/62.jpg", text: "平凡日子，因为有你而发光" },
  { type: "image", src: "images/63.jpg", text: "往后余生，请多指教" },
  { type: "image", src: "images/64.jpg", text: "这一眼，就注定了是一辈子" },
  { type: "image", src: "images/65.jpg", text: "和你的每一帧，都值得珍藏" },
  { type: "image", src: "images/66.jpg", text: "月亮很亮，但你更亮" },
  { type: "image", src: "images/67.jpg", text: "谢谢你，成为我的例外" },
  { type: "image", src: "images/68.jpg", text: "所谓浪漫，就是和你慢慢变老" },
  { type: "image", src: "images/69.jpg", text: "你是我的偏爱，也是唯一" },
  { type: "image", src: "images/70.jpg", text: "走过四季，你是我最好的季节" },
  { type: "image", src: "images/71.jpg", text: "世界很大，我只想待在你身边" },
  { type: "image", src: "images/72.jpg", text: "所有的温柔，都是你" },
  { type: "image", src: "images/73.jpg", text: "有你的日子，风都是甜的" }
];

// 纪念日 (年, 月-1, 日)
const startDate = new Date(2026, 3, 6);
// ==========================================

// --- 分组：单张 20 组 + 双张 12 组 + 剩余九宫格 ---
const GROUPS = (function () {
  const g = []; let i = 0;
  const SINGLE = 20, DOUBLE = 12;
  for (let s = 0; s < SINGLE && i < photos.length; s++) g.push({ layout: 'single', items: [photos[i++]] });
  for (let d = 0; d < DOUBLE && i < photos.length; d++) {
    const items = [photos[i++]];
    if (i < photos.length) items.push(photos[i++]);
    g.push({ layout: 'double', items });
  }
  while (i < photos.length) { g.push({ layout: 'grid', items: photos.slice(i, i + 9) }); i += 9; }
  return g;
})();

const bgm = document.getElementById("bgm");
const voice = document.getElementById("voice");
const musicBtn = document.getElementById("music-btn");
const musicPanel = document.getElementById("music-panel");
const typewriterElement = document.getElementById("typewriter");
const startBtn = document.getElementById("start-btn");
const introSection = document.getElementById("intro-section");
const mainSection = document.getElementById("main-section");
const stage = document.getElementById("stage");
const captionElement = document.getElementById("image-caption");
const nextBtn = document.getElementById("next-btn");
const prevBtn = document.getElementById("prev-btn");
const finalWords = document.getElementById("final-words");
const letterTrigger = document.getElementById("letter-trigger");
const openLetterBtn = document.getElementById("open-letter-btn");
const letterContent = document.getElementById("letter-content");

// --- 音乐控制 ---
let currentBgmIndex = 0;
bgm.addEventListener("ended", () => {
  currentBgmIndex++;
  if (currentBgmIndex >= bgmList.length) currentBgmIndex = 0;
  bgm.src = bgmList[currentBgmIndex];
  bgm.play().catch(() => {});
});

// BGM 选择器
musicBtn.addEventListener("click", (e) => { e.stopPropagation(); musicPanel.classList.toggle("hidden"); });
document.querySelectorAll(".music-opt").forEach(btn => {
  btn.addEventListener("click", () => {
    currentBgmIndex = bgmList.indexOf(btn.dataset.src);
    bgm.src = btn.dataset.src;
    bgm.play().catch(() => {});
    document.querySelectorAll(".music-opt").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    musicPanel.classList.add("hidden");
  });
});

// --- 打字机 ---
let charIndex = 0;
function typeEffect() {
  if (charIndex < introText.length) {
    typewriterElement.innerHTML += introText.charAt(charIndex);
    charIndex++;
    setTimeout(typeEffect, 100);
  } else {
    startBtn.classList.remove("hidden");
  }
}

// --- 性能：渐进式预加载 ---
const preloadedSrcs = new Set();
function preloadGroup(index) {
  const end = Math.min(index + 2, GROUPS.length - 1);
  for (let i = index; i <= end; i++) {
    GROUPS[i].items.forEach(item => {
      if (item.type === 'image' && !preloadedSrcs.has(item.src)) {
        preloadedSrcs.add(item.src);
        const img = new Image();
        img.decoding = 'async';
        img.src = item.src;
      }
    });
  }
}
preloadGroup(0);

window.addEventListener('load', () => {
  setTimeout(typeEffect, 5000);
});

// --- 相册切换逻辑 ---
let groupIndex = 0;
startBtn.addEventListener("click", () => {
  if (bgmList.length > 0) { bgm.src = bgmList[currentBgmIndex]; bgm.play().catch(() => {}); }
  introSection.classList.add("hidden");
  mainSection.classList.remove("hidden");
  renderGroup();
});

function renderGroup() {
  const g = GROUPS[groupIndex];
  stage.innerHTML = '';
  captionElement.innerText = '';

  if (g.layout === 'single') {
    const item = g.items[0];
    if (item.type === 'video') {
      stage.innerHTML = `<video class="stage-video" src="${item.src}" controls playsinline preload="metadata"></video>`;
      const v = stage.querySelector('video');
      v.addEventListener('play', () => bgm.pause());
      v.addEventListener('ended', () => bgm.play().catch(() => {}));
      v.addEventListener('pause', () => { if (!v.ended) bgm.play().catch(() => {}); });
    } else {
      stage.innerHTML = `<img class="stage-img" src="${item.src}" alt="" decoding="async">`;
    }
    captionElement.innerText = item.text || '';
  } else if (g.layout === 'double') {
    stage.innerHTML = `<div class="stage-double">${g.items.map(it => `<img class="stage-img" src="${it.src}" alt="" loading="lazy" decoding="async">`).join('')}</div>`;
  } else {
    stage.innerHTML = `<div class="stage-grid">${g.items.map(it => `<img class="stage-img" src="${it.src}" alt="" loading="lazy" decoding="async">`).join('')}</div>`;
  }

  const frame = document.getElementById('polaroid-frame');
  frame.classList.remove('layout-single', 'layout-double', 'layout-grid');
  frame.classList.add('layout-' + g.layout);
  const randomRotate = (Math.random() * 6 - 3).toFixed(1);
  frame.style.transform = `rotate(${randomRotate}deg)`;

  prevBtn.style.visibility = groupIndex === 0 ? 'hidden' : 'visible';
  if (groupIndex === GROUPS.length - 1) {
    nextBtn.innerText = '还要再重新看一次吗？';
    nextBtn.classList.add('final');
  } else {
    nextBtn.innerText = '下一张';
    nextBtn.classList.remove('final');
  }

  preloadGroup(groupIndex);

  // 供 effects.js 挂接
  if (window.__onGroup) window.__onGroup(g, groupIndex);
}

// --- 按钮翻页 ---
nextBtn.addEventListener('click', () => {
  if (groupIndex < GROUPS.length - 1) {
    groupIndex++;
    renderGroup();
  } else {
    playFinalVoice();
  }
});
prevBtn.addEventListener('click', () => {
  if (groupIndex > 0) { groupIndex--; renderGroup(); }
});

// --- 结尾彩蛋 ---
function playFinalVoice() {
  if (!voice.src) voice.src = 'voice.mp3';
  const p = voice.play();
  if (p && p.catch) p.catch(() => setTimeout(showLetterTrigger, 3000));

  const now = new Date();
  const diffDays = Math.ceil(Math.abs(now - startDate) / (1000 * 60 * 60 * 24));
  document.getElementById('days-counter').innerText = `我们已经相爱了 ${diffDays} 天，往后的每一天都想和你继续 ❤️`;

  document.querySelector('.nav-controls').classList.add('hidden');
  document.querySelector('.image-box').classList.add('hidden');
  finalWords.classList.remove('hidden');
}

function showLetterTrigger() {
  letterTrigger.classList.remove('hidden');
}

voice.addEventListener('play', () => bgm.pause());
voice.addEventListener('ended', () => { showLetterTrigger(); bgm.play().catch(() => {}); });
voice.addEventListener('error', () => { setTimeout(showLetterTrigger, 3000); bgm.play().catch(() => {}); });

openLetterBtn.addEventListener('click', () => {
  letterTrigger.classList.add('hidden');
  letterContent.classList.remove('hidden');
});
