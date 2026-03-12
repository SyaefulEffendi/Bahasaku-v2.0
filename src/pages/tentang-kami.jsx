import React, { useEffect, useRef } from 'react';
import Navbar from '../components/navbar';
import Footer from '../components/footer';
import './css/tentang-kami.css';

import bgImage from './Image/background-header.svg fill.png';
import aboutImage from './Image/about-image.jpg';
import bisindoChar from './Image/image 11.png';

function TentangKami() {
    const useScrollAnimation = () => {
        const observer = useRef(null);

        useEffect(() => {
            observer.current = new IntersectionObserver((entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('is-visible');
                        observer.current.unobserve(entry.target);
                    }
                });
            }, {
                threshold: 0.1
            });

            const elementsToAnimate = document.querySelectorAll('.animate-on-scroll');
            elementsToAnimate.forEach((el) => observer.current.observe(el));

            return () => {
                if (observer.current) {
                    observer.current.disconnect();
                }
            };
        }, []);
    };

    useScrollAnimation();

    return (
        <div>
            <title>Tentang Kami</title>
            <Navbar />
            <main>
                {/* HERO BANNER */}
                <div className="we-hero-banner">
                    <img
                        src={bgImage}
                        alt="Dekorasi latar belakang"
                        className="hero-banner-bg-image"
                    />
                    <h1 className="hero-banner-title animate-fade-in-up">Tentang Kami</h1>
                </div>

                {/* --- BAGIAN 1: PENGENALAN TENTANG KAMI --- */}
                <section className="about-intro-section animate-on-scroll">
                    <div className="container about-intro-container">
                        {/* Tambahkan kelas animasi spesifik untuk gambar dan teks */}
                        <div className="about-intro-image animate-slide-in-left">
                            <img src={aboutImage} alt="Video perkenalan Bahasaku" />
                        </div>
                        <div className="about-intro-text animate-slide-in-right">
                            <h2>Tentang Kami</h2>
                            <p>
                                Bahasaku merupakan startup sosial yang menyediakan teknologi penerjemah dan interpretasi Bahasa Isyarat Indonesia sebagai akses informasi dan komunikasi bagi teman Tuli.
                            </p>
                            <p></p>
                        </div>
                    </div>
                </section>

                {/* --- BAGIAN 2: MENGAPA BISINDO PENTING --- */}
                <section className="bisindo-why-section">
                    <div className="container">
                        <h2 className="section-title">Mengapa BISINDO Itu Penting?</h2>
                        
                        <div className="bisindo-card animate-on-scroll animate-scale-up">
                            
                            <div className="bisindo-card-image">
                                <img src={bisindoChar} alt="Karakter 3D melakukan bahasa isyarat" />
                            </div>

                            <div className="bisindo-card-points">
                                <ul>
                                    <li>
                                        <div className="point-icon"></div>
                                        <div className="point-text">
                                            <h3>Bahasa Isyarat Alami</h3>
                                            <p>BISINDO atau singkatan dari Bahasa Isyarat Indonesia merupakan bahasa isyarat alami yang banyak digunakan oleh orang Tuli di Indonesia sebagai alat komunikasi.</p>
                                        </div>
                                    </li>
                                    <li>
                                        <div className="point-icon"></div>
                                        <div className="point-text">
                                            <h3>BISINDO di Setiap Daerah Berbeda</h3>
                                            <p>BISINDO mempunyai variasi isyarat berbeda-beda di tiap daerah yang dipengaruhi oleh bahasa daerah dan budaya daerah.</p>
                                        </div>
                                    </li>
                                    <li>
                                        <div className="point-icon"></div>
                                        <div className="point-text">
                                            <h3>Alat Komunikasi</h3>
                                            <p>BISINDO merupakan salah satu kekayaan bahasa yang tidak hanya digunakan oleh orang Tuli, tetapi oleh semua kalangan agar dapat berinteraksi antar sesama manusia dalam kehidupan sehari-hari.</p>
                                        </div>
                                    </li>
                                </ul>
                            </div>
                            
                        </div>
                    </div>
                </section>

            </main>
            <Footer />
        </div>
    );
}

export default TentangKami;