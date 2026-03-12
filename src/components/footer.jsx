import React from 'react';
import logo from '../pages/Image/Logo 2 2.png';
import linkedin from '../pages/Image/linkedin.png';
import facebook from '../pages/Image/facebook.png';
import instagram from '../pages/Image/instagram.png';
import whatsapp from '../pages/Image/whatsapp.png';
import playStoreBtn from '../pages/Image/PlayStore.png';
import appStoreBtn from '../pages/Image/AppStore.png';
import "./footer.css";

function Footer() {
    return (
        <footer className="footer">
            <div className="footer-top">
                <div className="footer-column">
                    <div className="footer-logo">
                        <img src={logo} alt="Bahasaku Logo" />
                    </div>
                    <p className="footer-title">Universitas Sebelas Maret PSDKU Madiun</p>
                    <p className="footer-address">
                        Jl. Imam Bonjol, Sumbersoko, Pandean,<br />
                        Kec. Mejayan, Kabupaten Madiun,<br />
                        Jawa Timur 63153
                    </p>
                    <h4>Informasi Kontak</h4>
                    <p className="contact-info">
                        <a href="mailto:mohsyaefuleffendi@student.uns.ac.id">
                            mohsyaefuleffendi@student.uns.ac.id
                        </a>
                    </p>
                    <p className="contact-info">
                        <a href="https://bahasaku.co.id">
                            https://bahasaku.co.id
                        </a>
                    </p>
                    <p className="contact-info">(+62) 851-7520-0586</p>
                </div>

                <div className="footer-column">
                    <h4>Bahasaku</h4>
                    <ul className="footer-links">
                        <li><a href="/">Beranda</a></li>
                        <li><a href="/tentang-kami">Tentang Kami</a></li>
                        <li><a href="/aplikasi">Aplikasi</a></li>
                        <li><a href="#">Pendeteksi Isyarat</a></li>
                    </ul>
                </div>

                <div className="footer-column">
                    <h4>Bantuan</h4>
                    <ul className="footer-links">
                        <li><a href="/kontak">Kontak</a></li>
                    </ul>
                </div>

                <div className="footer-column social-media-column">
                    <h4>Social Media</h4>
                    <div className="social-icons">
                        <a href="https://www.linkedin.com/in/moh-syaeful-effendi-b664a3315" target="_blank" rel="noopener noreferrer">
                            <img src={linkedin} alt="LinkedIn" />
                        </a>
                        <a href="https://www.facebook.com/syaeful.effendi.9/" target="_blank" rel="noopener noreferrer">
                            <img src={facebook} alt="Facebook" />
                        </a>
                        <a href="https://www.instagram.com/syaefuleffendi/" target="_blank" rel="noopener noreferrer">
                            <img src={instagram} alt="Instagram" />
                        </a>
                        <a href="https://wa.me/+6285175200686" target="_blank" rel="noopener noreferrer">
                            <img src={whatsapp} alt="WhatsApp" />
                        </a>
                    </div>
                    <h4>Download Sekarang</h4>
                    <div className="download-buttons">
                        <a href="https://apps.apple.com" target="_blank" rel="noopener noreferrer">
                            <img src={appStoreBtn} alt="App Store" className="download-btn-img" />
                        </a>
                        <a href="https://play.google.com" target="_blank" rel="noopener noreferrer">
                            <img src={playStoreBtn} alt="Google Play" className="download-btn-img" />
                        </a>
                    </div>
                </div>
            </div>

            <div className="footer-bottom">
                <p>Copyright © 2025, All Right Reserved Bahasaku - Universitas Sebelas Maret PSDKU Madiun</p>
            </div>
        </footer>
    );
}

export default Footer;