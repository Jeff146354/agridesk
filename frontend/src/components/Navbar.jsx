import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useEffect, useMemo, useRef, useState } from 'react';
import api from '../api';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [isNotificationOpen, setIsNotificationOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [notificationLoading, setNotificationLoading] = useState(false);
  const notificationPanelRef = useRef(null);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  useEffect(() => {
    const handleOutsideClick = (event) => {
      if (notificationPanelRef.current && !notificationPanelRef.current.contains(event.target)) {
        setIsNotificationOpen(false);
      }
    };

    document.addEventListener('mousedown', handleOutsideClick);
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, []);

  useEffect(() => {
    if (!user) return;
    const fetchNotifications = async () => {
      setNotificationLoading(true);
      try {
        const res = await api.get('/api/notifications', { params: { limit: 8 } });
        setNotifications(res.data || []);
      } catch (err) {
        setNotifications([]);
      } finally {
        setNotificationLoading(false);
      }
    };

    fetchNotifications();
    const interval = setInterval(fetchNotifications, 45000);
    return () => clearInterval(interval);
  }, [user?.id]);

  const unreadCount = useMemo(() => notifications.length, [notifications]);

  const formatTime = (value) => {
    if (!value) return '';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return '';
    return date.toLocaleString('id-ID', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const navLinkClass = ({ isActive }) => 
    `px-4 py-6 text-sm font-medium transition-colors border-b-2 ${
      isActive 
        ? 'border-primary text-primary' 
        : 'border-transparent text-primary/70 hover:text-primary hover:border-primary/30'
    }`;

  if (!user) return null;

  // Initials for avatar (must be after null guard)
  const initials = user.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();

  return (
    <nav className="bg-ivory border-b border-sepia-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          
          {/* Logo */}
          <div className="shrink-0 flex items-center gap-3">
            <div className="w-8 h-8 bg-primary text-white flex items-center justify-center font-serif text-lg font-bold rounded-sm">A</div>
            <div>
              <h1 className="font-serif font-bold text-lg leading-none text-primary">Agridesk</h1>
              <p className="text-[10px] tracking-widest text-primary/60 mt-0.5 uppercase">Ilmu Komputer</p>
            </div>
          </div>

          {/* Center Nav Links */}
          <div className="hidden md:flex items-center h-full space-x-2">
            {user.role === 'MAHASISWA' && (
              <>
                <NavLink to="/" className={navLinkClass}>Surat Saya</NavLink>
                <NavLink to="/surat/new" className={navLinkClass}>Buat Surat</NavLink>
                <NavLink to="/signature/me" className={navLinkClass}>Tanda Tangan</NavLink>
              </>
            )}
            {user.role === 'DOSEN' && (
              <>
                <NavLink to="/" className={navLinkClass}>Surat Masuk</NavLink>
                <NavLink to="/surat/all-dosen" className={navLinkClass}>Riwayat</NavLink>
                <NavLink to="/signature/me" className={navLinkClass}>Tanda Tangan</NavLink>
              </>
            )}
            {user.role === 'ADMIN' && (
              <>
                <NavLink to="/" className={navLinkClass}>Surat Masuk</NavLink>
                <NavLink to="/surat/all" className={navLinkClass}>Riwayat</NavLink>
                <NavLink to="/signature/me" className={navLinkClass}>Tanda Tangan</NavLink>
              </>
            )}
          </div>

          {/* Right Section */}
          <div className="hidden md:flex items-center space-x-6" ref={notificationPanelRef}>
            <button
              type="button"
              onClick={() => setIsNotificationOpen((prev) => !prev)}
              className="relative text-primary/70 hover:text-primary transition-colors"
              aria-label="Notifikasi"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
              </svg>
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 min-w-4 h-4 px-1 rounded-full bg-red-500 text-white text-[10px] leading-4 font-semibold text-center">
                  {unreadCount}
                </span>
              )}
            </button>

            {isNotificationOpen && (
              <div className="absolute top-16 right-32 w-96 bg-white border border-sepia-200 shadow-xl rounded-sm overflow-hidden z-50">
                <div className="px-4 py-3 border-b border-sepia-200 bg-ivory flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-primary">Notifikasi</p>
                    <p className="text-xs text-primary/60">Status surat dan tanda tangan terbaru</p>
                  </div>
                </div>
                <div className="max-h-96 overflow-auto">
                  {notificationLoading ? (
                    <div className="px-4 py-6 text-sm text-primary/50 italic">Memuat notifikasi...</div>
                  ) : notifications.length === 0 ? (
                    <div className="px-4 py-6 text-sm text-primary/50 italic">Belum ada notifikasi baru.</div>
                  ) : (
                    notifications.map((item) => (
                      <button
                        key={item.id}
                        type="button"
                        onClick={() => {
                          setIsNotificationOpen(false);
                          if (item.link) navigate(item.link);
                        }}
                        className="w-full text-left px-4 py-3 border-b border-sepia-200/70 hover:bg-ivory transition-colors last:border-0"
                      >
                        <div className="flex items-start gap-3">
                          <div className="mt-1 w-2.5 h-2.5 rounded-full bg-primary/40 shrink-0" />
                          <div className="min-w-0">
                            <p className="text-sm font-medium text-primary">{item.title}</p>
                            <p className="text-xs text-primary/70 mt-1 leading-relaxed">{item.message}</p>
                            <p className="text-[10px] tracking-wide uppercase text-primary/40 mt-2">
                              {item.source_event}{item.created_at ? ` · ${formatTime(item.created_at)}` : ''}
                            </p>
                          </div>
                        </div>
                      </button>
                    ))
                  )}
                </div>
              </div>
            )}
            
            <div className="flex items-center space-x-3 text-right">
              <div>
                <p className="text-sm font-medium text-primary">{user.name}</p>
                <p className="text-xs text-primary/60">{user.role === 'MAHASISWA' ? 'Mahasiswa' : user.role === 'DOSEN' ? 'Dosen' : 'Admin'}</p>
              </div>
              <div className="w-8 h-8 rounded-full bg-sepia-200 text-primary flex items-center justify-center text-xs font-medium uppercase tracking-wider">
                {initials}
              </div>
            </div>

            <button onClick={handleLogout} className="text-sm text-primary/70 hover:text-primary transition-colors">
              Keluar
            </button>
          </div>

          {/* Mobile menu button */}
          <div className="-mr-2 flex md:hidden">
            <button onClick={() => setIsOpen(!isOpen)} className="inline-flex items-center justify-center p-2 rounded-md text-primary/60 hover:text-primary hover:bg-sepia-200 focus:outline-none">
              <span className="sr-only">Open main menu</span>
              {isOpen ? (
                <svg className="block h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg className="block h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      {isOpen && (
        <div className="md:hidden bg-ivory border-t border-sepia-200">
          <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
             {user.role === 'MAHASISWA' && (
              <>
                <NavLink to="/" onClick={() => setIsOpen(false)} className="block px-3 py-2 text-primary hover:bg-sepia-200 rounded-md">Surat Saya</NavLink>
                <NavLink to="/surat/new" onClick={() => setIsOpen(false)} className="block px-3 py-2 text-primary hover:bg-sepia-200 rounded-md">Buat Surat</NavLink>
                <NavLink to="/signature/me" onClick={() => setIsOpen(false)} className="block px-3 py-2 text-primary hover:bg-sepia-200 rounded-md">Tanda Tangan</NavLink>
              </>
            )}
            {user.role === 'DOSEN' && (
              <>
                <NavLink to="/" onClick={() => setIsOpen(false)} className="block px-3 py-2 text-primary hover:bg-sepia-200 rounded-md">Surat Masuk</NavLink>
                <NavLink to="/surat/all-dosen" onClick={() => setIsOpen(false)} className="block px-3 py-2 text-primary hover:bg-sepia-200 rounded-md">Riwayat</NavLink>
                <NavLink to="/signature/me" onClick={() => setIsOpen(false)} className="block px-3 py-2 text-primary hover:bg-sepia-200 rounded-md">Tanda Tangan</NavLink>
              </>
            )}
            {user.role === 'ADMIN' && (
              <>
                <NavLink to="/" onClick={() => setIsOpen(false)} className="block px-3 py-2 text-primary hover:bg-sepia-200 rounded-md">Surat Masuk</NavLink>
                <NavLink to="/surat/all" onClick={() => setIsOpen(false)} className="block px-3 py-2 text-primary hover:bg-sepia-200 rounded-md">Riwayat</NavLink>
                <NavLink to="/signature/me" onClick={() => setIsOpen(false)} className="block px-3 py-2 text-primary hover:bg-sepia-200 rounded-md">Tanda Tangan</NavLink>
              </>
            )}
            <div className="mt-4 pt-4 border-t border-sepia-200 px-3 flex justify-between items-center">
              <span className="text-sm font-medium text-primary">{user.name}</span>
              <button onClick={handleLogout} className="text-sm text-red-600 hover:text-red-800">Keluar</button>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
}
