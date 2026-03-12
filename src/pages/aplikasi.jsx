import React from 'react';
import { motion } from 'framer-motion'; 
import Navbar from '../components/navbar';
import Footer from '../components/footer';
import "./css/aplikasi.css";

// --- GAMBAR UNTUK HERO SECTION ---
import appStoreBtn from "./Image/AppStore.png";
import playStoreBtn from "./Image/PlayStore.png";
import heroImage from "./Image/hero-image.png";

// --- GAMBAR UNTUK FITUR SECTION ---
import dotsPattern from './Image/aplikasi-kiri-atas.png';
import blueCircles from './Image/aplikasi-kanan-atas.png';
import feature1 from './Image/aplikasi-content-1.png';
import feature2 from './Image/aplikasi-content-2.png';
import feature3 from './Image/aplikasi-content-3.png';
import feature4 from './Image/aplikasi-content-4.png';

// --- GAMBAR UNTUK STATISTIK SECTION ---
import iconDengar from './Image/icon-dengar.png';
import iconTuli from './Image/icon-tuli.png';
import iconDownload from './Image/icon-download.png';


function Aplikasi() {
    return (
        <div>
            <title>Aplikasi</title>
            <Navbar />
            <main>
                {/* === HERO SECTION === */}
                <motion.section
                    className="hero-section"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 1 }}
                >
                    <div className="hero-content">
                        <h1>Teknologi Akses Bahasa Isyarat untuk Segala Kebutuhanmu</h1>
                        <p>Download aplikasi Bahasaku sekarang!</p>
                        <div className="download-buttons">
                            <a href="https://apps.apple.com/id/app/bahasaku" target="_blank" rel="noopener noreferrer">
                                <img src={appStoreBtn} alt="Download di App Store" className="download-btn-img" />
                            </a>
                            <a href="https://play.google.com/store/apps/details?id=com.bahasaku" target="_blank" rel="noopener noreferrer">
                                <img src={playStoreBtn} alt="Dapatkan di Google Play" className="download-btn-img" />
                            </a>
                        </div>
                    </div>
                    <div className="hero-image">
                        <img src={heroImage} alt="Hero" />
                    </div>
                </motion.section>

                {/* === FEATURES SECTION === */}
                <motion.section 
                    className="features-section"
                    initial={{ opacity: 0, y: 50 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.8 }}
                >
                    <img src={dotsPattern} alt="Dots Pattern" className="dots-pattern" />
                    <img src={blueCircles} alt="Blue Circles" className="blue-circles" />
                    
                    <h2>Ketahui Fitur dari Bahasaku</h2>
                    
                    <div className="features-grid">
                        <div className="feature-card">
                            <img src={feature1} alt="Translate Me - Text to Video" className="feature-img" />
                            <div className="feature-content">
                                <h3>Translate Me - Text to Video</h3>
                                <p>Penerjemah tulisan menjadi bahasa isyarat dalam bentuk animasi 3D.</p>
                            </div>
                        </div>
                        <div className="feature-card">
                            <img src={feature2} alt="Learn Me" className="feature-img" />
                            <div className="feature-content">
                                <h3>Learn Me</h3>
                                <p>Fitur belajar bahasa isyarat (BISINDO) dengan berbagai kategori yang ditampilkan dalam animasi.</p>
                            </div>
                        </div>
                        <div className="feature-card">
                            <img src={feature3} alt="My Dictionary" className="feature-img" />
                            <div className="feature-content">
                                <h3>My Dictionary</h3>
                                <p>Kamus yang memiliki kumpulan bahasa isyarat beserta video animasinya.</p>
                            </div>
                        </div>
                        <div className="feature-card">
                            <img src={feature4} alt="Translate Me - Video to Text" className="feature-img" />
                            <div className="feature-content">
                                <h3>Translate Me - Video to Text</h3>
                                <p>Mengidentifikasi video dengan gerakan isyarat menjadi tulisan secara real-time.</p>
                            </div>
                        </div>
                    </div>
                </motion.section>

                {/* === STATISTIK SECTION === */}
                <motion.section 
                    className="stats-section"
                    initial={{ opacity: 0 }}
                    whileInView={{ opacity: 1 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.8, delay: 0.2 }}
                >
                    <div className="stats-card">
                        <div className="stat-item">
                            <img src={iconDengar} alt="Pengguna Dengar" />
                            <h3>100.000+</h3>
                            <p>Dengar</p>
                        </div>
                        <div className="stat-item">
                            <img src={iconTuli} alt="Pengguna Tuli" />
                            <h3>28.000+</h3>
                            <p>Tuli</p>
                        </div>
                        <div className="stat-item">
                            <img src={iconDownload} alt="Total Download" />
                            <h3>160.000+</h3>
                            <p>Download</p>
                        </div>
                    </div>
                </motion.section>

            </main>
            <Footer />
        </div>
    );
}

export default Aplikasi;