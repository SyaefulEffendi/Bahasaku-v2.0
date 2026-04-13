import React, { useState, useEffect } from 'react';
// 1. Impor useNavigate dan useAuth
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context'; // <-- Sesuaikan path ini jika perlu
import logo from '../pages/Image/Logo 2 2.png';
import './navbar.css';

function Navbar() {
    const [isOpen, setIsOpen] = useState(false);
    const [isDropdownOpen, setIsDropdownOpen] = useState(false);
    // 2. Tambahkan state untuk dropdown profil
    const [isProfileOpen, setIsProfileOpen] = useState(false);
    
    const location = useLocation();
    // 3. Panggil hook useAuth dan useNavigate
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    const toggleMenu = (e) => {
        e.stopPropagation(); 
        setIsOpen(!isOpen);
    };

    // 4. Buat fungsi untuk handle logout
    const handleLogout = () => {
        logout(); // Panggil fungsi logout dari context
        navigate('/'); // Arahkan ke halaman utama
    };

    // 5. Efek untuk menutup SEMUA menu saat klik di luar
    useEffect(() => {
        const handleOutsideClick = (event) => {
            if (!event.target.closest('.navbar')) {
                setIsOpen(false);
                setIsDropdownOpen(false);
                setIsProfileOpen(false); // <-- Tambahkan ini
            }
        };
        document.addEventListener('click', handleOutsideClick);
        return () => document.removeEventListener('click', handleOutsideClick);
    }, []);

    const getNavLinkClass = (path) => {
        return location.pathname === path ? 'active' : '';
    };

    return (
        <>
            <nav className="navbar">
                <div className="navbar-logo">
                    <NavLink to="/">
                        <img src={logo} alt="Bahasaku Logo" />
                    </NavLink>
                </div>

                <button
                    className={`menu-toggle ${isOpen ? 'open' : ''}`}
                    onClick={toggleMenu}
                    aria-label="Toggle menu"
                >
                    <div className="hamburger-bar"></div>
                    <div className="hamburger-bar"></div>
                    <div className="hamburger-bar"></div>
                </button>

                <ul className={`navbar-menu ${isOpen ? 'open' : ''}`}>
                    <li><NavLink to="/" className={getNavLinkClass('/')}>Beranda</NavLink></li>
                    <li><NavLink to="/tentang-kami" className={getNavLinkClass('/tentang-kami')}>Tentang Kami</NavLink></li>
                    <li><NavLink to="/aplikasi" className={getNavLinkClass('/aplikasi')}>Aplikasi</NavLink></li>
                    <li
                        className="dropdown"
                        onMouseEnter={() => setIsDropdownOpen(true)}
                        onMouseLeave={() => setIsDropdownOpen(false)}
                    >
                        <a href="#" onClick={(e) => e.preventDefault()}>
                            Pendeteksi Isyarat &#9662;
                        </a>
                        {isDropdownOpen && (
                            <ul className="dropdown-menu">
                                <li><NavLink to="/video-to-text" className={getNavLinkClass('/video-to-text')}>Video to Text</NavLink></li>
                                <li><NavLink to="/text-to-video" className={getNavLinkClass('/text-to-video')}>Text to Video</NavLink></li>
                            </ul>
                        )}
                    </li>
                    <li><NavLink to="/kontak" className={getNavLinkClass('/kontak')}>Kontak</NavLink></li>
                    
                    {/* --- 6. INI BAGIAN UTAMANYA --- */}
                    { user ? (
                        // JIKA SUDAH LOGIN: Tampilkan nama dan dropdown profil
                        <li
                            className="dropdown"
                            onMouseEnter={() => setIsProfileOpen(true)}
                            onMouseLeave={() => setIsProfileOpen(false)}
                        >
                            <a href="#" onClick={(e) => e.preventDefault()} className="navbar-username">
                                {user.full_name} &#9662;
                            </a>
                            {isProfileOpen && (
                                <ul className="dropdown-menu">
                                    <li><NavLink to="/profile" className={getNavLinkClass('/profile')}>Profil Saya</NavLink></li>
                                    <li>
                                        <a href="#" onClick={handleLogout} className="logout-link">
                                            Logout
                                        </a>
                                    </li>
                                </ul>
                            )}
                        </li>
                    ) : (
                        // JIKA BELUM LOGIN: Tampilkan tombol Login
                        <li><NavLink to="/login" className={getNavLinkClass('/login')}>Login</NavLink></li>
                    )}
                    {/* --- Akhir Bagian Utama --- */}

                </ul>
            </nav>
            <div className="navbar-spacer"></div>
        </>
    );
}

export default Navbar;