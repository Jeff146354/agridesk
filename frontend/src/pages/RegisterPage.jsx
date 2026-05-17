import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getErrorMessage } from '../utils/error';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';
import { ChevronDown } from 'lucide-react';

function CustomFormDropdown({ value, onChange, placeholder, options }) {
  const [isOpen, setIsOpen] = useState(false);
  const selectedOption = options.find(opt => opt.value === value) || null;

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-3 bg-ivory border border-sepia-200 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary rounded-sm transition-all text-sm cursor-pointer flex justify-between items-center text-left"
      >
        <span className={selectedOption ? 'text-primary' : 'text-primary/40'}>
          {selectedOption ? selectedOption.label : placeholder}
        </span>
        <ChevronDown size={16} className={`text-primary/60 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      <AnimatePresence>
        {isOpen && (
          <>
            {/* Click outside backdrop */}
            <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
            
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.15 }}
              className="absolute left-0 right-0 mt-1.5 bg-white border border-sepia-200 rounded-sm shadow-lg max-h-60 overflow-y-auto z-20"
            >
              <ul className="py-1">
                {options.map((option) => (
                  <li key={option.value}>
                    <button
                      type="button"
                      onClick={() => {
                        onChange(option.value);
                        setIsOpen(false);
                      }}
                      className={`w-full px-4 py-2.5 text-left text-sm transition-colors flex items-center justify-between
                        ${value === option.value 
                          ? 'bg-primary text-white font-medium' 
                          : 'text-primary/80 hover:bg-ivory hover:text-primary'
                        }`}
                    >
                      <span>{option.label}</span>
                      {value === option.value && (
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
                      )}
                    </button>
                  </li>
                ))}
              </ul>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'MAHASISWA', nim: '', nip: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!form.email.endsWith('@apps.ipb.ac.id')) {
      const errorMsg = 'Pendaftaran hanya diperbolehkan menggunakan email institusi IPB (@apps.ipb.ac.id).';
      setError(errorMsg);
      toast.error('Domain email tidak valid!');
      return;
    }

    setLoading(true);
    try {
      const payload = { ...form };
      if (payload.role === 'MAHASISWA') delete payload.nip;
      else delete payload.nim;
      await register(payload);
      navigate('/login');
    } catch (err) {
      setError(getErrorMessage(err, 'Registrasi gagal. Coba lagi dengan data yang berbeda.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="min-h-screen flex flex-col bg-ivory text-primary font-sans"
    >
      {/* Header Panel */}
      <header className="flex justify-between items-center p-6 lg:px-12 border-b border-sepia-200">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-primary text-white flex items-center justify-center font-serif text-lg font-bold rounded-sm">A</div>
          <div>
            <h1 className="font-serif font-bold text-lg leading-none">Agridesk</h1>
            <p className="text-[10px] tracking-widest text-primary/60 mt-0.5 uppercase">Ilmu Komputer</p>
          </div>
        </div>
        <div className="text-xs sm:text-sm text-primary/70 text-right">
          <span className="hidden sm:inline">Sudah punya akun? </span>
          <Link to="/login" className="font-medium text-primary hover:text-primary-dark underline underline-offset-4 decoration-primary/30">
            Masuk di sini
          </Link>
        </div>
      </header>

      {/* Content Wrapper */}
      <div className="flex-1 flex flex-col lg:flex-row">
        {/* Left Panel - Branding */}
        <div className="w-full lg:w-1/2 flex flex-col justify-center p-8 sm:p-12 lg:p-24 border-b lg:border-b-0 lg:border-r border-sepia-200 order-2 lg:order-1">
          <div className="max-w-md mx-auto lg:mx-0">
            <p className="text-xs tracking-widest text-primary/50 uppercase mb-8 hidden lg:block">Jilid 01 &middot; 2026</p>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-serif leading-tight mb-4 lg:mb-6">
              Mulai kelola surat,<br />
              <span className="italic">lebih</span> terstruktur.
            </h2>
            <p className="text-sm leading-relaxed text-primary/80 mb-8 lg:mb-12">
              Bergabunglah dengan ekosistem administrasi Ilmu Komputer. Buat akun Anda sekarang untuk mempercepat proses persuratan akademik tanpa kendala birokrasi manual.
            </p>

            <div className="mt-12 hidden lg:block">
              <p className="text-xs italic text-primary/60">
                "Kerapian sistem berawal dari data individu yang tertata." <br />
                <span className="not-italic opacity-75">— Administrator</span>
              </p>
            </div>
          </div>
        </div>

        {/* Right Panel - Register Form */}
        <div className="w-full lg:w-1/2 flex flex-col justify-center p-8 sm:p-12 lg:p-24 bg-ivory order-1 lg:order-2">
          <div className="w-full max-w-sm mx-auto">
            <p className="text-[10px] tracking-widest text-primary/50 uppercase mb-4">Daftar &middot; Pengguna Baru</p>
            <h2 className="text-3xl sm:text-4xl font-serif mb-4">Buat akun Anda.</h2>
            <p className="text-sm text-primary/70 mb-8">
              Lengkapi formulir di bawah ini dengan identitas akademik Anda yang sah.
            </p>

            <form onSubmit={handleSubmit} className="space-y-5">
              {error && (
                <div className="bg-red-50/50 border border-red-200 text-red-700 px-4 py-3 text-sm rounded-sm">
                  {error}
                </div>
              )}

              <div>
                <label className="block text-xs tracking-widest text-primary/60 uppercase mb-2">
                  Nama Lengkap
                </label>
                <input
                  required
                  value={form.name}
                  onChange={set('name')}
                  className="w-full px-4 py-3 bg-white/50 border border-sepia-200 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary rounded-sm transition-colors text-sm"
                  placeholder="John Doe"
                />
              </div>

              <div>
                <label className="block text-xs tracking-widest text-primary/60 uppercase mb-2">
                  Email
                </label>
                <input
                  type="email"
                  required
                  value={form.email}
                  onChange={set('email')}
                  className="w-full px-4 py-3 bg-white/50 border border-sepia-200 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary rounded-sm transition-colors text-sm"
                  placeholder="nama@apps.ipb.ac.id"
                />
              </div>

              <div>
                <label className="block text-xs tracking-widest text-primary/60 uppercase mb-2">
                  Kata Sandi
                </label>
                <input
                  type="password"
                  required
                  value={form.password}
                  onChange={set('password')}
                  className="w-full px-4 py-3 bg-white/50 border border-sepia-200 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary rounded-sm transition-colors text-sm"
                  placeholder="••••••••"
                />
              </div>

              <div className="relative">
                <label className="block text-xs tracking-widest text-primary/60 uppercase mb-2">
                  Peran Pengguna
                </label>
                <CustomFormDropdown
                  placeholder="Pilih Peran Pengguna"
                  value={form.role}
                  onChange={(val) => setForm({ ...form, role: val })}
                  options={[
                    { value: 'MAHASISWA', label: 'Mahasiswa' },
                    { value: 'DOSEN', label: 'Dosen' },
                    { value: 'ADMIN', label: 'Admin' }
                  ]}
                />
              </div>

              {form.role === 'MAHASISWA' && (
                <div>
                  <label className="block text-xs tracking-widest text-primary/60 uppercase mb-2">
                    NIM
                  </label>
                  <input
                    required
                    value={form.nim}
                    onChange={set('nim')}
                    className="w-full px-4 py-3 bg-white/50 border border-sepia-200 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary rounded-sm transition-colors text-sm"
                    placeholder="G6xxxxxxxxx"
                  />
                </div>
              )}

              {form.role !== 'MAHASISWA' && (
                <div>
                  <label className="block text-xs tracking-widest text-primary/60 uppercase mb-2">
                    NIP
                  </label>
                  <input
                    required
                    value={form.nip}
                    onChange={set('nip')}
                    className="w-full px-4 py-3 bg-white/50 border border-sepia-200 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary rounded-sm transition-colors text-sm"
                    placeholder="1980xxxxxxxxxxxxxx"
                  />
                </div>
              )}

              <div className="pt-4">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 px-4 bg-primary text-white text-sm font-medium hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary focus:ring-offset-ivory rounded-sm transition-all disabled:opacity-70"
                >
                  {loading ? 'Memproses...' : 'Daftar Sekarang'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
