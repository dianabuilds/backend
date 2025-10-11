/* @vitest-environment node */

import request from 'supertest';
import { describe, it, expect } from 'vitest';

import { createSsrServer } from '../../../../server/createServer';

const template = '<!doctype html><html><body><div id="root"><!--app-html--></div><!--initial-data--></body></html>';

describe('createSsrServer', () => {
  it('возвращает собранный SSR-документ', async () => {
    const { app, close } = await createSsrServer({
      mode: 'test',
      template,
      render: async (url) => ({
        html: `<main data-url="${url}">SSR OK</main>`,
        status: 201,
        headers: { 'X-SSR': 'true' },
        initialData: { foo: 'bar' },
      }),
    });

    try {
      const response = await request(app).get('/dev-blog?Page=2');

      expect(response.status).toBe(201);
      expect(response.headers['x-ssr']).toBe('true');
      expect(response.headers['content-type']).toContain('text/html');
      expect(response.text).toContain('SSR OK');
      expect(response.text).toContain('window.__INITIAL_DATA__ = {"foo":"bar"}');
      expect(response.text).toContain('data-url="http://localhost/dev-blog?Page=2"');
    } finally {
      await close();
    }
  });
});
