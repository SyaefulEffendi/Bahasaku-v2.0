import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';
import Dashboard from './pages/dashboard';
import Login from './pages/login';
import Register from './pages/register';
import Aplikasi from './pages/aplikasi';
import TentangKami from './pages/tentang-kami';
import Kontak from './pages/kontak';
import TextToVideo from './pages/text-to-video';
import VideoToText from './pages/video-to-text';
import DashboardAdmin from './pages/dashboardAdmin';
import Profile from './pages/profile';


function App() {
  return (
    <Router>
      <div>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/aplikasi" element={<Aplikasi />} />
          <Route path="/tentang-kami" element={<TentangKami />} />
          <Route path="/kontak" element={<Kontak />} />
          <Route path="/text-to-video" element={<TextToVideo />} />
          <Route path="/video-to-text" element={<VideoToText />} />
          <Route path="/dashboard-admin" element={<DashboardAdmin />} />
          <Route path="/profile" element={<Profile />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;