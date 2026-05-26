import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function HomePage() {
  const { user } = useAuth();

  if (!user) return <Navigate to="/login" replace />;

  switch (user.role) {
    case 'MAHASISWA': return <Navigate to="/dashboard/mahasiswa" replace />;
    case 'DOSEN':     return <Navigate to="/dashboard/dosen" replace />;
    case 'ADMIN':     return <Navigate to="/dashboard/admin" replace />;
    default:          return <Navigate to="/login" replace />;
  }
}
