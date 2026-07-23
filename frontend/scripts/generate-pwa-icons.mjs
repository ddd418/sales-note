/**
 * 의존성 없이(zlib만 사용) PWA 아이콘 PNG를 생성한다.
 * 브랜드 컬러(#2563eb) 배경 + 파이프라인(단계별 바) 글리프.
 * maskable 아이콘은 OS가 마스킹하는 안전영역(중앙 80%)에 글리프가 들어가도록 축소한다.
 */
import { deflateSync } from 'node:zlib';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = fileURLToPath(new URL('.', import.meta.url));
const publicDir = join(__dirname, '..', 'public');

const BG = [0x25, 0x63, 0xeb]; // #2563eb
const FG = [0xff, 0xff, 0xff];

const CRC_TABLE = (() => {
  const table = new Uint32Array(256);
  for (let n = 0; n < 256; n += 1) {
    let c = n;
    for (let k = 0; k < 8; k += 1) {
      c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    }
    table[n] = c >>> 0;
  }
  return table;
})();

function crc32(buf) {
  let c = 0xffffffff;
  for (let i = 0; i < buf.length; i += 1) {
    c = CRC_TABLE[(c ^ buf[i]) & 0xff] ^ (c >>> 8);
  }
  return (c ^ 0xffffffff) >>> 0;
}

function chunk(type, data) {
  const typeBuf = Buffer.from(type, 'ascii');
  const lenBuf = Buffer.alloc(4);
  lenBuf.writeUInt32BE(data.length, 0);
  const crcBuf = Buffer.alloc(4);
  crcBuf.writeUInt32BE(crc32(Buffer.concat([typeBuf, data])), 0);
  return Buffer.concat([lenBuf, typeBuf, data, crcBuf]);
}

function encodePNG(width, height, rgb) {
  const signature = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8; // bit depth
  ihdr[9] = 2; // color type: truecolor RGB
  ihdr[10] = 0;
  ihdr[11] = 0;
  ihdr[12] = 0;

  const stride = width * 3;
  const raw = Buffer.alloc((stride + 1) * height);
  for (let y = 0; y < height; y += 1) {
    raw[y * (stride + 1)] = 0; // filter: none
    rgb.copy(raw, y * (stride + 1) + 1, y * stride, y * stride + stride);
  }
  const idat = deflateSync(raw, { level: 9 });
  return Buffer.concat([signature, chunk('IHDR', ihdr), chunk('IDAT', idat), chunk('IEND', Buffer.alloc(0))]);
}

function pointInCapsule(x, y, cx, cy, halfLength, radius) {
  const dx = Math.abs(x - cx);
  if (dx <= halfLength) {
    return Math.abs(y - cy) <= radius;
  }
  const capCx = cx + (x < cx ? -halfLength : halfLength);
  const ddx = x - capCx;
  const ddy = y - cy;
  return ddx * ddx + ddy * ddy <= radius * radius;
}

/** 파이프라인 3단 바 글리프. scale<1 이면 maskable 안전영역에 맞춰 축소. */
function drawIcon(size, { scale = 1, supersample = 4 } = {}) {
  const S = size * supersample;
  const px = new Uint8Array(S * S * 3);
  for (let i = 0; i < S * S; i += 1) {
    px[i * 3] = BG[0];
    px[i * 3 + 1] = BG[1];
    px[i * 3 + 2] = BG[2];
  }

  const cx = S / 2;
  const bars = [
    { widthFrac: 0.62, yFrac: 0.35 },
    { widthFrac: 0.44, yFrac: 0.5 },
    { widthFrac: 0.26, yFrac: 0.65 },
  ];
  const thickness = S * 0.1 * scale;
  const radius = thickness / 2;

  for (const bar of bars) {
    const halfLen = (S * bar.widthFrac * scale) / 2 - radius;
    const cy = S * (0.5 + (bar.yFrac - 0.5) * scale);
    for (let y = Math.max(0, Math.floor(cy - radius - 1)); y <= Math.min(S - 1, Math.ceil(cy + radius + 1)); y += 1) {
      for (let x = Math.max(0, Math.floor(cx - halfLen - radius - 1)); x <= Math.min(S - 1, Math.ceil(cx + halfLen + radius + 1)); x += 1) {
        if (pointInCapsule(x + 0.5, y + 0.5, cx, cy, Math.max(halfLen, 0), radius)) {
          const idx = (y * S + x) * 3;
          px[idx] = FG[0];
          px[idx + 1] = FG[1];
          px[idx + 2] = FG[2];
        }
      }
    }
  }

  // 슈퍼샘플 다운스케일 (박스 평균) → 부드러운 가장자리
  const out = Buffer.alloc(size * size * 3);
  for (let y = 0; y < size; y += 1) {
    for (let x = 0; x < size; x += 1) {
      let r = 0;
      let g = 0;
      let b = 0;
      for (let sy = 0; sy < supersample; sy += 1) {
        for (let sx = 0; sx < supersample; sx += 1) {
          const idx = ((y * supersample + sy) * S + (x * supersample + sx)) * 3;
          r += px[idx];
          g += px[idx + 1];
          b += px[idx + 2];
        }
      }
      const n = supersample * supersample;
      const outIdx = (y * size + x) * 3;
      out[outIdx] = Math.round(r / n);
      out[outIdx + 1] = Math.round(g / n);
      out[outIdx + 2] = Math.round(b / n);
    }
  }
  return out;
}

mkdirSync(join(publicDir, 'icons'), { recursive: true });

const targets = [
  { file: 'icons/icon-192.png', size: 192, scale: 1 },
  { file: 'icons/icon-512.png', size: 512, scale: 1 },
  { file: 'icons/icon-maskable-192.png', size: 192, scale: 0.72 },
  { file: 'icons/icon-maskable-512.png', size: 512, scale: 0.72 },
  { file: 'apple-touch-icon.png', size: 180, scale: 1 },
  { file: 'favicon-48.png', size: 48, scale: 1 },
  { file: 'favicon-32.png', size: 32, scale: 1 },
  { file: 'favicon-16.png', size: 16, scale: 1 },
];

for (const target of targets) {
  const rgb = drawIcon(target.size, { scale: target.scale });
  const png = encodePNG(target.size, target.size, rgb);
  const outPath = join(publicDir, target.file);
  mkdirSync(dirname(outPath), { recursive: true });
  writeFileSync(outPath, png);
  console.log(`wrote ${target.file} (${target.size}x${target.size}, ${png.length} bytes)`);
}
