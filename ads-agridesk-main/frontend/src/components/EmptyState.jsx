import { FileBox } from 'lucide-react';

export default function EmptyState({ message, subMessage }) {
  return (
    <div className="py-16 flex flex-col items-center justify-center text-center px-4">
      <div className="w-16 h-16 bg-sepia-200/50 rounded-full flex items-center justify-center mb-6">
        <FileBox className="w-8 h-8 text-primary/40 stroke-[1.5]" />
      </div>
      <h4 className="text-base font-serif text-primary mb-2">{message || "Tidak ada catatan"}</h4>
      <p className="text-sm text-primary/60 max-w-sm">{subMessage || "Belum ada dokumen yang perlu ditampilkan saat ini."}</p>
    </div>
  );
}
