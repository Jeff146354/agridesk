import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Shield, Lock, HelpCircle, FileText, ExternalLink, Mail, Phone, MapPin } from 'lucide-react';
import { toast } from 'sonner';

export default function Footer() {
  const [activeTab, setActiveTab] = useState(null); // 'terms', 'privacy', 'help' or null

  const openModal = (tab) => {
    setActiveTab(tab);
  };

  const closeModal = () => {
    setActiveTab(null);
  };

  const handleEmailClick = (e) => {
    e.preventDefault();
    const email = 'ilkom@apps.ipb.ac.id';
    
    // Copy to clipboard fallback
    navigator.clipboard.writeText(email)
      .then(() => {
        toast.success(`Alamat email ${email} berhasil disalin ke clipboard!`);
      })
      .catch(() => {
        toast.error('Gagal menyalin email secara otomatis.');
      });
      
    // Trigger standard mailto
    window.location.href = `mailto:${email}`;
  };

  return (
    <>
      <footer className="bg-ivory border-t border-sepia-200 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="text-center md:text-left">
            <p className="text-xs text-primary/60">&copy; 2026 Agridesk Ilmu Komputer. All rights reserved.</p>
          </div>
          <div className="flex items-center space-x-6 text-xs text-primary/60">
            <button onClick={() => openModal('terms')} className="hover:text-primary transition-colors font-medium">Ketentuan Layanan</button>
            <button onClick={() => openModal('privacy')} className="hover:text-primary transition-colors font-medium">Kebijakan Privasi</button>
            <button onClick={() => openModal('help')} className="hover:text-primary transition-colors font-medium">Bantuan</button>
          </div>
        </div>
      </footer>

      {/* Interactive Modal System */}
      <AnimatePresence>
        {activeTab && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={closeModal}
              className="fixed inset-0 bg-black/40 backdrop-blur-xs"
            />

            {/* Modal Body */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ type: 'spring', duration: 0.5 }}
              className="relative w-full max-w-3xl bg-white border border-sepia-200 shadow-2xl rounded-sm overflow-hidden flex flex-col max-h-[85vh] z-10"
            >
              {/* Header */}
              <div className="px-6 py-4 bg-ivory border-b border-sepia-200 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 bg-primary text-white flex items-center justify-center font-serif text-sm font-bold rounded-xs">A</div>
                  <h3 className="text-md font-serif font-semibold text-primary">Informasi & Bantuan</h3>
                </div>
                <button
                  onClick={closeModal}
                  className="p-1 text-primary/50 hover:text-primary hover:bg-sepia-100 rounded-sm transition-colors"
                  aria-label="Close modal"
                >
                  <X size={18} />
                </button>
              </div>

              {/* Navigation Tabs */}
              <div className="flex border-b border-sepia-200 bg-white overflow-x-auto shrink-0">
                <button
                  onClick={() => setActiveTab('terms')}
                  className={`flex items-center gap-2 px-6 py-3.5 text-xs font-semibold uppercase tracking-wider border-b-2 transition-all whitespace-nowrap ${
                    activeTab === 'terms'
                      ? 'border-primary text-primary bg-ivory/30'
                      : 'border-transparent text-primary/60 hover:text-primary hover:bg-ivory/10'
                  }`}
                >
                  <FileText size={14} />
                  Ketentuan Layanan
                </button>
                <button
                  onClick={() => setActiveTab('privacy')}
                  className={`flex items-center gap-2 px-6 py-3.5 text-xs font-semibold uppercase tracking-wider border-b-2 transition-all whitespace-nowrap ${
                    activeTab === 'privacy'
                      ? 'border-primary text-primary bg-ivory/30'
                      : 'border-transparent text-primary/60 hover:text-primary hover:bg-ivory/10'
                  }`}
                >
                  <Lock size={14} />
                  Kebijakan Privasi
                </button>
                <button
                  onClick={() => setActiveTab('help')}
                  className={`flex items-center gap-2 px-6 py-3.5 text-xs font-semibold uppercase tracking-wider border-b-2 transition-all whitespace-nowrap ${
                    activeTab === 'help'
                      ? 'border-primary text-primary bg-ivory/30'
                      : 'border-transparent text-primary/60 hover:text-primary hover:bg-ivory/10'
                  }`}
                >
                  <HelpCircle size={14} />
                  Bantuan & Support
                </button>
              </div>

              {/* Scrollable Content */}
              <div className="p-6 overflow-y-auto space-y-6 text-sm text-primary/80 leading-relaxed max-w-full">
                
                {/* 1. KETENTUAN LAYANAN */}
                {activeTab === 'terms' && (
                  <motion.div
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="space-y-6"
                  >
                    <div>
                      <h4 className="text-lg font-serif font-semibold text-primary mb-2">Ketentuan Penggunaan Platform Agridesk</h4>
                      <p className="text-xs text-primary/40">Terakhir diperbarui: 17 Mei 2026</p>
                    </div>

                    <p>
                      Selamat datang di <strong>Agridesk</strong>, sistem administrasi dan tata kelola surat akademik elektronik Departemen Ilmu Komputer IPB University. Dengan mengakses dan menggunakan platform ini, Anda menyetujui ketentuan layanan di bawah ini.
                    </p>

                    <div className="space-y-4">
                      <div className="p-4 bg-ivory border border-sepia-200/60 rounded-xs">
                        <h5 className="font-serif font-semibold text-primary mb-1.5 flex items-center gap-1.5"><Shield size={14} className="text-primary/70" /> 1. Otorisasi & Akun Pengguna</h5>
                        <p className="text-xs">Penggunaan platform dibatasi hanya untuk civitas akademika aktif Departemen Ilmu Komputer IPB (Mahasiswa, Dosen, Kaprodi, dan Staff Tata Usaha). Anda bertanggung jawab penuh untuk menjaga kerahasiaan akun SSO IPB Anda.</p>
                      </div>

                      <div className="p-4 bg-ivory border border-sepia-200/60 rounded-xs">
                        <h5 className="font-serif font-semibold text-primary mb-1.5 flex items-center gap-1.5"><FileText size={14} className="text-primary/70" /> 2. Keabsahan Tanda Tangan Elektronik</h5>
                        <p className="text-xs">Tanda tangan digital yang dibubuhkan melalui Agridesk menggunakan pencocokan hash kriptografis SHA-256 dan bersifat mengikat secara hukum serta sah digunakan untuk keperluan administrasi akademik internal di lingkungan IPB University.</p>
                      </div>

                      <div className="p-4 bg-ivory border border-sepia-200/60 rounded-xs">
                        <h5 className="font-serif font-semibold text-primary mb-1.5 flex items-center gap-1.5"><Lock size={14} className="text-primary/70" /> 3. Integritas Data & Larangan Pemalsuan</h5>
                        <p className="text-xs">Setiap upaya memanipulasi, memalsukan isi dokumen, mengunggah data palsu, atau menggunakan profil tanda tangan milik orang lain secara tidak sah akan dicatat oleh sistem log audit dan akan dikenakan sanksi akademik yang berat.</p>
                      </div>
                    </div>
                  </motion.div>
                )}

                {/* 2. KEBIJAKAN PRIVASI */}
                {activeTab === 'privacy' && (
                  <motion.div
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="space-y-6"
                  >
                    <div>
                      <h4 className="text-lg font-serif font-semibold text-primary mb-2">Kebijakan Privasi Perlindungan Data</h4>
                      <p className="text-xs text-primary/40">Terakhir diperbarui: 17 Mei 2026</p>
                    </div>

                    <p>
                      Kami di Departemen Ilmu Komputer sangat menghargai dan berkomitmen penuh untuk melindungi privasi data pribadi Anda saat menggunakan platform administrasi surat elektronik Agridesk.
                    </p>

                    <div className="space-y-4">
                      <div className="border-l-2 border-primary/40 pl-4 py-1">
                        <h5 className="font-serif font-semibold text-primary mb-1">Data yang Kami Kumpulkan</h5>
                        <p className="text-xs text-primary/70">Nama lengkap, NIM/NIP, email institusi IPB (@apps.ipb.ac.id), gambar stempel tanda tangan digital, alamat IP, dan log transaksi pembuatan dokumen.</p>
                      </div>

                      <div className="border-l-2 border-primary/40 pl-4 py-1">
                        <h5 className="font-serif font-semibold text-primary mb-1">Tujuan Penggunaan Data</h5>
                        <p className="text-xs text-primary/70">Data digunakan secara eksklusif untuk proses penerbitan surat dinas akademik, keperluan tanda tangan persetujuan dosen/kaprodi, pencatatan alur pengajuan, dan fungsi verifikasi keaslian dokumen publik.</p>
                      </div>

                      <div className="border-l-2 border-primary/40 pl-4 py-1">
                        <h5 className="font-serif font-semibold text-primary mb-1">Keamanan & Enkripsi Kriptografis</h5>
                        <p className="text-xs text-primary/70">Seluruh berkas dokumen PDF akhir diproteksi menggunakan integritas hash SHA-256 publik yang menjamin isi surat tidak dapat dirusak atau dimodifikasi tanpa merusak rantai keabsahan tanda tangan.</p>
                      </div>
                    </div>
                  </motion.div>
                )}

                {/* 3. BANTUAN & SUPPORT */}
                {activeTab === 'help' && (
                  <motion.div
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="space-y-6"
                  >
                    <div>
                      <h4 className="text-lg font-serif font-semibold text-primary mb-2">Pusat Bantuan & Panduan Layanan</h4>
                      <p className="text-xs text-primary/40">Menemukan masalah? Silakan baca panduan di bawah ini.</p>
                    </div>

                    <div className="space-y-4">
                      <details className="group border border-sepia-200 p-3 rounded-xs bg-ivory/20 transition-all [&_summary::-webkit-details-marker]:hidden" open>
                        <summary className="flex items-center justify-between cursor-pointer focus:outline-none">
                          <h5 className="font-serif font-semibold text-primary text-sm">Bagaimana cara membubuhkan Tanda Tangan?</h5>
                          <span className="shrink-0 transition duration-300 group-open:-rotate-180">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
                          </span>
                        </summary>
                        <p className="mt-2 text-xs text-primary/70 leading-relaxed">
                          1. Buka halaman <strong>Tanda Tangan</strong> di navbar (setelah login).<br />
                          2. Unggah stempel tanda tangan berformat PNG transparan Anda pada menu profil.<br />
                          3. Saat ada dokumen masuk yang membutuhkan persetujuan Anda, Anda cukup mengklik tombol <strong>Setujui / Tanda Tangan</strong>. Sistem akan otomatis memasang stempel tanda tangan Anda di lembar PDF secara presisi.
                        </p>
                      </details>

                      <details className="group border border-sepia-200 p-3 rounded-xs bg-ivory/20 transition-all [&_summary::-webkit-details-marker]:hidden">
                        <summary className="flex items-center justify-between cursor-pointer focus:outline-none">
                          <h5 className="font-serif font-semibold text-primary text-sm">Bagaimana cara verifikasi dokumen cetak?</h5>
                          <span className="shrink-0 transition duration-300 group-open:-rotate-180">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
                          </span>
                        </summary>
                        <p className="mt-2 text-xs text-primary/70 leading-relaxed">
                          Anda bisa langsung <strong>memindai (scan)</strong> QR Code yang tercetak di sudut bawah surat menggunakan kamera ponsel pintar Anda. Anda akan otomatis diarahkan ke halaman verifikasi resmi Agridesk yang menampilkan kecocokan data surat asli dari database kami.
                        </p>
                      </details>

                      <div className="border border-sepia-200/80 p-4 rounded-xs bg-ivory flex flex-col sm:flex-row gap-4 justify-between items-start sm:items-center">
                        <div>
                          <h5 className="font-serif font-semibold text-primary mb-1">Masih Mengalami Kendala?</h5>
                          <p className="text-xs text-primary/60">Hubungi langsung Unit Layanan Tata Usaha Departemen Ilmu Komputer.</p>
                        </div>
                        <button
                          onClick={handleEmailClick}
                          className="px-4 py-2 bg-primary text-white text-xs font-semibold rounded-xs hover:bg-primary-dark transition-colors inline-flex items-center gap-1.5 shrink-0"
                        >
                          <Mail size={12} />
                          Kirim Email
                        </button>
                      </div>
                    </div>
                  </motion.div>
                )}
              </div>

              {/* Footer inside Modal */}
              <div className="px-6 py-4 bg-ivory border-t border-sepia-200 flex justify-between items-center shrink-0">
                <span className="text-[10px] uppercase tracking-widest text-primary/40 font-mono">Agridesk Sec-Ops &middot; v1.0.2</span>
                <button
                  onClick={closeModal}
                  className="px-4 py-1.5 bg-primary text-white text-xs font-medium rounded-xs hover:bg-primary-dark transition-colors"
                >
                  Selesai
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
}

