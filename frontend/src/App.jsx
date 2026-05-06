import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from 'sonner';
import { AuthProvider } from './context/AuthContext';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import ProtectedRoute from './components/ProtectedRoute';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import HomePage from './pages/HomePage';
import MahasiswaDashboard from './pages/MahasiswaDashboard';
import DosenDashboard from './pages/DosenDashboard';
import DosenAllSuratPage from './pages/DosenAllSuratPage';
import AdminDashboard from './pages/AdminDashboard';
import AllSuratPage from './pages/AllSuratPage';
import CreateSuratPage from './pages/CreateSuratPage';
import SuratDetailPage from './pages/SuratDetailPage';
import VerifyPage from './pages/VerifyPage';
import SignatureProfilePage from './pages/SignatureProfilePage';
import PdfViewerPage from './pages/PdfViewerPage';
import './index.css';

export default function App() {
  return (
    <AuthProvider>
      <Toaster position="top-center" richColors theme="light" />
      <BrowserRouter>
        <div className="min-h-screen bg-ivory flex flex-col">
          <Navbar />
          <main className="flex-1 w-full flex flex-col">
            <Routes>
              <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/verify" element={<VerifyPage />} />

            <Route path="/" element={<HomePage />} />

            <Route path="/dashboard/mahasiswa" element={
              <ProtectedRoute roles={['MAHASISWA']}><MahasiswaDashboard /></ProtectedRoute>
            } />
            <Route path="/dashboard/dosen" element={
              <ProtectedRoute roles={['DOSEN']}><DosenDashboard /></ProtectedRoute>
            } />
            <Route path="/surat/all-dosen" element={
              <ProtectedRoute roles={['DOSEN']}><DosenAllSuratPage /></ProtectedRoute>
            } />
            <Route path="/dashboard/admin" element={
              <ProtectedRoute roles={['ADMIN']}><AdminDashboard /></ProtectedRoute>
            } />

            <Route path="/surat/new" element={
              <ProtectedRoute roles={['MAHASISWA']}><CreateSuratPage /></ProtectedRoute>
            } />
            <Route path="/signature/me" element={
              <ProtectedRoute><SignatureProfilePage /></ProtectedRoute>
            } />
            <Route path="/surat/all" element={
              <ProtectedRoute roles={['ADMIN']}><AllSuratPage /></ProtectedRoute>
            } />
            <Route path="/surat/:id" element={
              <ProtectedRoute><SuratDetailPage /></ProtectedRoute>
            } />
            <Route path="/surat/:id/pdf" element={
              <ProtectedRoute><PdfViewerPage /></ProtectedRoute>
            } />
          </Routes>
          </main>
          <Footer />
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}
