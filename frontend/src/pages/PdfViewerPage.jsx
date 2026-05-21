import { useMemo } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, Download, ExternalLink } from 'lucide-react';

export default function PdfViewerPage() {
  const { id } = useParams();

  const token = localStorage.getItem('token') || '';
  const backendBase = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
  const pdfUrl = useMemo(
    () => `${backendBase}/api/surat/${id}/pdf?token=${encodeURIComponent(token)}`,
    [id, token]
  );

  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = pdfUrl;
    link.download = `surat-${id}.pdf`;
    link.target = '_blank';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="flex flex-col" style={{ height: 'calc(100vh - 80px)' }}>
      {/* Toolbar */}
      <div className="px-6 py-3 bg-ivory border-b border-sepia-200 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-4">
          <Link
            to={`/surat/${id}`}
            className="p-2 border border-sepia-200 text-primary hover:border-primary transition-colors rounded-sm bg-white"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h2 className="text-base font-serif text-primary">Dokumen #{id}</h2>
            <p className="text-[10px] tracking-widest uppercase text-primary/50">Pratinjau Resmi</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleDownload}
            className="flex items-center gap-2 px-4 py-2 text-sm border border-sepia-200 text-primary hover:border-primary hover:bg-white transition-colors rounded-sm"
          >
            <Download className="w-4 h-4" />
            <span className="hidden sm:inline">Unduh</span>
          </button>
          <a
            href={pdfUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2 text-sm border border-sepia-200 text-primary hover:border-primary hover:bg-white transition-colors rounded-sm"
          >
            <ExternalLink className="w-4 h-4" />
            <span className="hidden sm:inline">Tab Baru</span>
          </a>
        </div>
      </div>

      {/* PDF Iframe — fills all remaining space */}
      <iframe
        src={pdfUrl}
        title={`Dokumen Surat #${id}`}
        className="flex-1 w-full border-0 bg-white"
        style={{ minHeight: 0 }}
        allow="fullscreen"
      />
    </div>
  );
}

