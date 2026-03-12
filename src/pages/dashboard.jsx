import React from 'react';
import { motion } from 'framer-motion';
import './css/dashboard.css';

import Navbar from '../components/navbar';
import Footer from '../components/footer';

// Impor gambar yang digunakan di dashboard.jsx
import heroImage from './Image/hero-image.png';
import aboutImage from './Image/about-image.jpg';
import mobileAppImage from './Image/mobile-app.png';
import textToVideoImage from './Image/iPad Mini.png';
import signLanguageInfoImage from './Image/iMockup - iPhone 15 Pro Max.png';
import signLanguageDictionaryImage from './Image/Konten Video Bahasa Isyarat.png';
import videoToTextImage from './Image/iMac 24 inch.png';
import kumpulan from './Image/kumpulan.png'
import alatAmpuh from './Image/alatAmpuh.png'
import belajar from './Image/belajar.png'
import MencariTeman from './Image/MencariTeman.png'
import playStoreBtn from './Image/PlayStore.png';
import appStoreBtn from './Image/AppStore.png';


function Dashboard() {
    return (
        <div className="dashboard-container">
            <title>Beranda</title>
            <Navbar />
            <main>
                {/* === Hero Section === */}
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

                {/* === About Us === */}
                <motion.section
                    className="about-us-section"
                    initial={{ y: 50, opacity: 0 }}
                    whileInView={{ y: 0, opacity: 1 }}
                    viewport={{ once: true, amount: 0.2 }}
                    transition={{ duration: 0.8 }}
                >
                    <div className="about-image">
                        <img src={aboutImage} alt="Tentang Kami" />
                    </div>
                    <div className="about-content">
                        <h2>Tentang Kami</h2>
                        <p>Bahasaku merupakan startup sosial yang menyediakan teknologi penerjemah dan interpretasi Bahasa Isyarat Indonesia sebagai akses informasi dan komunikasi bagi teman Tuli.</p>
                        <button className="learn-more-btn">Pelajari Lebih Lanjut</button>
                    </div>
                </motion.section>

                {/* === Services Section === */}
                <motion.section
                    className="services-section"
                    initial={{ y: 50, opacity: 0 }}
                    whileInView={{ y: 0, opacity: 1 }}
                    viewport={{ once: true, amount: 0.2 }}
                    transition={{ duration: 0.8 }}
                >
                    <h2>Layanan Produk Kami</h2>
                    <div className="services-grid">
                        <div className="service-card">
                            <div className="card-image-container">
                                <img src={textToVideoImage} alt="Teks Ke Video" className="card-image-1" />
                            </div>
                            <div className="card-content-container">
                                <h3>Teks Ke Video</h3>
                                <p>Teknologi dua arah dengan dua perangkat di meja customer service memungkinkan komunikasi yang inklusif; teks petugas diubah menjadi animasi 3D dalam bahasa isyarat untuk pelanggan Tuli.</p>
                            </div>
                        </div>
                        <div className="service-card">
                            <div className="card-image-container">
                                <img src={signLanguageInfoImage} alt="Layar Informasi Bahasa Isyarat" className="card-image-2" />
                            </div>
                            <div className="card-content-container">
                                <h3>Layar Informasi Bahasa Isyarat</h3>
                                <p>Menampilkan informasi publik dalam Bahasa Isyarat melalui layar digital yang interaktif dan ramah pengguna.</p>
                            </div>
                        </div>
                        <div className="service-card">
                            <div className="card-image-container">
                                <img src={signLanguageDictionaryImage} alt="Kamus Bahasa Isyarat" className="card-image-3" />
                            </div>
                            <div className="card-content-container">
                                <h3>Kamus Bahasa Isyarat</h3>
                                <p>Penambahan video isyarat (juru Bahasa Isyarat atau animasi 3D) agar lebih ramah bagi komunitas Tuli.</p>
                            </div>
                        </div>
                        <div className="service-card">
                            <div className="card-image-container">
                                <img src={videoToTextImage} alt="Video Ke Teks" className="card-image-4" />
                            </div>
                            <div className="card-content-container">
                                <h3>Video Ke Teks</h3>
                                <p>Teknologi penerjemah otomatis yang mengubah video menjadi teks Bahasa Isyarat.</p>
                            </div>
                        </div>
                    </div>
                </motion.section>

                {/* === Download App Section === */}
                <motion.section
                    className="download-app-section"
                    initial={{ y: 50, opacity: 0 }}
                    whileInView={{ y: 0, opacity: 1 }}
                    viewport={{ once: true, amount: 0.2 }}
                    transition={{ duration: 0.8 }}
                >
                    <div className="download-content">
                        <p>Sementara itu, unduh versi gratis dari aplikasi kami untuk memulai belajar bahasa isyarat hari ini!</p>
                        <button className="download-btn">Unduh Aplikasi Sekarang</button>
                    </div>
                    <div className="download-image">
                        <img src={mobileAppImage} alt="Mobile App" />
                    </div>
                </motion.section>

                {/* === Reasons Section === */}
                <motion.section
                    className="reasons-section"
                    initial={{ y: 50, opacity: 0 }}
                    whileInView={{ y: 0, opacity: 1 }}
                    viewport={{ once: true, amount: 0.2 }}
                    transition={{ duration: 0.8 }}
                >
                    <h2>Beberapa alasan mengapa Anda harus menggunakan Aplikasi Bahasaku hari ini</h2>
                    <div className="reasons-grid">
                        <div className="reason-card">
                            <div className="reason-icon">
                                <img src={kumpulan} alt="Berkomunikasi Cepat dan Efektif" />
                            </div>
                            <h3>Berkomunikasi dengan cepat dan efektif</h3>
                            <p>Miliki penerjemah saku Anda kapan pun Anda membutuhkannya, baik saat online maupun offline.</p>
                        </div>
                        <div className="reason-card">
                            <div className="reason-icon">
                                <img src={MencariTeman} alt="Mencari Teman" />
                            </div>
                            <h3>Mencari teman bersama kami</h3>
                            <p>Tidak hanya berkomunikasi menggunakan Bahasa Isyarat. Bukalah pintu bagi jutaan orang, dimulai dengan BISINDO.</p>
                        </div>
                        <div className="reason-card">
                            <div className="reason-icon">
                                <img src={belajar} alt="Belajar Bahasa Baru" />
                            </div>
                            <h3>Belajar bahasa baru bisa menyenangkan</h3>
                            <p>Gunakan waktu luang Anda untuk belajar Bahasa Isyarat baru dengan cara yang menyenangkan bersama kami.</p>
                        </div>
                        <div className="reason-card">
                            <div className="reason-icon">
                                <img src={alatAmpuh} alt="Alat yang Ampuh" />
                            </div>
                            <h3>Aplikasi Bahasaku adalah alat yang ampuh</h3>
                            <p>Gunakan aplikasi ini sebagai sumber daya di dalam kelas, bersama keluarga dan teman, atau sekadar untuk meningkatkan kosakata Anda.</p>
                        </div>
                    </div>
                </motion.section>
            </main>
            <Footer />
        </div>
    );
}

export default Dashboard;