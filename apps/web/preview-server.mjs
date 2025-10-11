import express from 'express';
import compression from 'compression';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const distDir = path.resolve(__dirname, 'dist', 'client');

const app = express();
app.use(compression());
app.use('/assets', express.static(path.join(distDir, 'assets'), { maxAge: '1h', immutable: true }));
app.use('/vite.svg', express.static(path.resolve(__dirname, 'public', 'vite.svg'), { maxAge: '1h' }));

const homeResponse = {
  slug: 'main',
  version: 20251011,
  updated_at: '2025-10-11T00:00:00Z',
  published_at: '2025-10-10T00:00:00Z',
  blocks: [
    {
      id: 'hero',
      type: 'hero',
      enabled: true,
      slots: {
        headline: 'Caves: быстрые релизы и здоровый перформанс',
        subheadline: 'Пересобрали главную, упростили бандлы и сократили LCP до 2.3 с.',
        cta: { label: 'Читать обновления', href: '/dev-blog' },
      },
      items: [],
      layout: null,
    },
  ],
  fallbacks: [],
  meta: {
    title: { ru: 'Caves World — обновления платформы', en: 'Caves World — Platform updates' },
    description: {
      ru: 'Подборка заметок о перформансе и DX Caves. Рассказываем, как добились целевых метрик Lighthouse.',
      en: 'Notes on Caves performance and DX. Detailing how we hit the Lighthouse goals.',
    },
    alternates: {
      ru: { href: '/' },
      en: { href: '/en/' },
    },
  },
};

const devBlogListResponse = {
  items: [
    {
      id: 'roadmap-october',
      slug: 'roadmap-october',
      title: 'Wave-1: ускоряем главную и dev-blog',
      summary: 'Финализировали цепочку оптимизаций, обновили бандлы, довели LCP до 2.3 с.',
      cover_url: null,
      publish_at: '2025-10-10T08:00:00Z',
      updated_at: '2025-10-10T08:00:00Z',
      author: { id: 'irina.m', name: 'Ирина М' },
      tags: ['release', 'performance'],
    },
    {
      id: 'bundle-splitting',
      slug: 'bundle-splitting-notes',
      title: 'Split по Quill и hero-блокам',
      summary: 'Сократили entry bundle, вывели тяжёлые чанки из critical path.',
      cover_url: null,
      publish_at: '2025-10-05T09:00:00Z',
      updated_at: '2025-10-05T09:00:00Z',
      author: { id: 'alex.s', name: 'Алекс С' },
      tags: ['frontend', 'performance'],
    },
  ],
  total: 2,
  has_next: false,
  available_tags: ['release', 'performance', 'frontend'],
  applied_tags: [],
  date_range: { start: '2025-10-01', end: '2025-10-31' },
};

const devBlogDetailResponse = {
  post: {
    id: 'roadmap-october',
    slug: 'roadmap-october',
    title: 'Wave-1: ускоряем главную и dev-blog',
    summary: 'Финализировали цепочку оптимизаций, обновили бандлы, довели LCP до 2.3 с.',
    cover_url: null,
    publish_at: '2025-10-10T08:00:00Z',
    updated_at: '2025-10-10T08:00:00Z',
    author: { id: 'irina.m', name: 'Ирина М' },
    tags: ['release', 'performance'],
    content: '<p>Команда закончила волну оптимизаций: вынесли тяжёлые блоки из critical path, пересобрали prefetch и проверили кеш заголовков. По итогам получили LCP 2.3 с на главной и 2.2 с на dev-blog.</p><p>Также пересняли Lighthouse, обновили документацию и подготовили отчёт в #web-platform.</p>',
    status: 'published',
    is_public: true,
  },
  prev: null,
  next: null,
};

app.get('/v1/public/home', (req, res) => {
  res.json(homeResponse);
});

app.get('/v1/nodes/dev-blog', (req, res) => {
  res.json(devBlogListResponse);
});

app.get('/v1/nodes/dev-blog/:slug', (req, res) => {
  res.json(devBlogDetailResponse);
});

app.use((req, res) => { res.sendFile(path.join(distDir, 'index.html')); });

const port = Number.parseInt(process.env.PORT ?? '4173', 10);
app.listen(port, '127.0.0.1', () => {
  console.log(`[preview] listening on http://127.0.0.1:${port}`);
});

