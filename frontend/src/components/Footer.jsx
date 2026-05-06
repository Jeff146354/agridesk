import { toast } from 'sonner';

export default function Footer() {
  const showToast = (e, msg) => {
    e.preventDefault();
    toast.info(msg);
  };

  return (
    <footer className="bg-ivory border-t border-sepia-200 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col md:flex-row justify-between items-center gap-4">
        <div className="text-center md:text-left">
          <p className="text-xs text-primary/60">&copy; 2026 Agridesk Ilmu Komputer. All rights reserved.</p>
        </div>
        <div className="flex items-center space-x-6 text-xs text-primary/60">
          <button onClick={(e) => showToast(e, 'Halaman Ketentuan Layanan sedang dalam pengembangan')} className="hover:text-primary transition-colors">Ketentuan Layanan</button>
          <button onClick={(e) => showToast(e, 'Halaman Kebijakan Privasi sedang dalam pengembangan')} className="hover:text-primary transition-colors">Kebijakan Privasi</button>
          <button onClick={(e) => showToast(e, 'Pusat Bantuan sedang dalam pengembangan')} className="hover:text-primary transition-colors">Bantuan</button>
        </div>
      </div>

    </footer>
  );
}
