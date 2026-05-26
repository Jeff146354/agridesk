/**
 * Returns the backend base URL.
 *
 * In production (Docker / Nginx), the frontend and backend run on the same
 * origin — Nginx proxies /api/* to the backend container.  So we use a
 * relative empty-string base and all axios calls look like "/api/...".
 *
 * In local dev (Vite dev-server), the proxy in vite.config.js handles the
 * same /api/* → http://127.0.0.1:8000 rewriting, so relative URLs still work.
 *
 * VITE_API_BASE_URL is kept for backward compatibility but defaults to ''.
 */
export function getApiBaseUrl() {
  return import.meta.env.VITE_API_BASE_URL || '';
}
