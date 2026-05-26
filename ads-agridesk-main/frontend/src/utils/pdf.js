import api from '../api';

async function extractPdfErrorMessage(err) {
  const fallback = 'Gagal memuat PDF';
  const response = err?.response;
  if (!response) {
    const baseHint = 'Tidak bisa terhubung ke server PDF. Cek backend aktif dan CORS.';
    return err?.message ? `${baseHint} (${err.message})` : baseHint;
  }

  const payload = response.data;
  if (payload instanceof Blob) {
    try {
      const text = await payload.text();
      if (!text) return fallback;
      try {
        const parsed = JSON.parse(text);
        return parsed?.detail || fallback;
      } catch {
        return text;
      }
    } catch {
      return fallback;
    }
  }

  if (typeof payload === 'string') return payload || fallback;
  if (typeof payload === 'object' && payload?.detail) return payload.detail;
  return fallback;
}

export async function fetchSuratPdfBlob(suratId) {
  let res;
  try {
    res = await api.get(`/api/surat/${suratId}/pdf`, {
      responseType: 'blob',
    });
  } catch (err) {
    const message = await extractPdfErrorMessage(err);
    throw new Error(message);
  }

  const contentType = res.headers['content-type'] || 'application/pdf';
  return new Blob([res.data], { type: contentType });
}

export async function fetchSuratPdfBlobUrl(suratId) {
  const blob = await fetchSuratPdfBlob(suratId);
  return URL.createObjectURL(blob);
}

export async function downloadSuratPdf(suratId, filename = `surat-${suratId}.pdf`) {
  const blob = await fetchSuratPdfBlob(suratId);
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
