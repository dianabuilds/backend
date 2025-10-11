import process from 'node:process';
import { createSsrServer } from './createServer.js';

const port = Number.parseInt(process.env.PORT ?? '4173', 10);

async function start() {
  const { app, close } = await createSsrServer();
  const server = app.listen(port, () => {
    console.log(`[ssr] server listening on http://localhost:${port}`);
  });

  const shutdown = (signal: NodeJS.Signals) => {
    console.log(`[ssr] received ${signal}, shutting down`);
    server.close(async () => {
      try {
        await close();
      } finally {
        process.exit(0);
      }
    });
  };

  process.on('SIGINT', () => shutdown('SIGINT'));
  process.on('SIGTERM', () => shutdown('SIGTERM'));
}

start().catch((error) => {
  console.error('[ssr] failed to start server', error);
  process.exit(1);
});

