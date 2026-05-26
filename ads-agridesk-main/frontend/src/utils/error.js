/**
 * Extract a human-readable error message from an Axios error.
 *
 * Supports both the old format  { detail: "..." }
 * and the new structured format { error: { code: "...", message: "..." } }
 */
export function getErrorMessage(err, fallback = 'Terjadi kesalahan') {
  const data = err?.response?.data;
  if (!data) return err?.message || fallback;

  // New structured format
  if (data.error?.message) return data.error.message;

  // Old format (FastAPI HTTPException default)
  if (typeof data.detail === 'string') return data.detail;

  return fallback;
}
