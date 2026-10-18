const express = require('express');
const path = require('path');
const os = require('os');
const compression = require('compression');

const app = express();
const port = 3000;

// 1) gzip 压缩：html/css/js 等文本资源传输体积减少约 70%
//    (jpg/mp3/mp4 本身已压缩，compression 会自动跳过，不会浪费 CPU)
app.use(compression());

// 2) 静态资源 + 分级缓存策略
app.use(express.static(path.join(__dirname, 'public'), {
  etag: true,          // 默认开启，配合 304 让重复访问几乎零传输
  lastModified: true,
  setHeaders(res, filePath) {
    const ext = path.extname(filePath).toLowerCase();
    if (['.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg', '.mp4', '.mp3', '.woff', '.woff2'].includes(ext)) {
      // 图片/音视频：内容不变，长期强缓存，二次访问直接从本地读
      res.setHeader('Cache-Control', 'public, max-age=31536000, immutable');
    } else if (['.css', '.js'].includes(ext)) {
      // 样式/脚本：缓存一天，改完文件最晚一天后全量生效
      res.setHeader('Cache-Control', 'public, max-age=86400');
    } else {
      // html：每次重新验证，保证打开就是最新内容
      res.setHeader('Cache-Control', 'no-cache');
    }
  }
}));

// 启动服务器
app.listen(port, () => {
  console.log(`服务器已成功启动！`);
  console.log(`本机访问: http://127.0.0.1:${port}`);
  // 打印局域网地址，方便手机同 Wi-Fi 直接打开
  const nets = os.networkInterfaces();
  for (const name of Object.keys(nets)) {
    for (const net of nets[name] || []) {
      if (net.family === 'IPv4' && !net.internal) {
        console.log(`手机访问: http://${net.address}:${port}`);
      }
    }
  }
});
