import React, { useState, useEffect } from 'react';
import Navbar from '../components/navbar';
import Footer from '../components/footer';
import { useNavigate } from 'react-router-dom'; // Opsional: jika ingin redirect
import './css/kotak.css';

import bgImage from './Image/background-header.svg fill.png';
import dotsLeft from './Image/kontak-kiri-atas.png';
import shapeRight from './Image/kontak-kanan-atas.png';
import shapeLeft from './Image/kontak-kiri-bawah.png';

const API_BASE_URL = 'http://localhost:8080/api';

function Kontak() {
    const [dataForm, setDataForm] = useState({
        namaLengkap: '',
        alamatEmail: '',
        pesan: ''
    });
    const [popUpKonfirmasi, setPopUp] = useState(false);
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [isLoading, setIsLoading] = useState(false);

    // Fungsi bantuan untuk mengambil payload dari JWT Token (untuk dapat ID user)
    const parseJwt = (token) => {
        try {
            return JSON.parse(atob(token.split('.')[1]));
        } catch (e) {
            return null;
        }
    };

    useEffect(() => {
        const checkLoginAndFetchUser = async () => {
            const token = localStorage.getItem('authToken');
            
            if (token) {
                setIsLoggedIn(true);
                const decoded = parseJwt(token);
                
                // Jika token valid dan ada ID (sub atau identity)
                if (decoded && decoded.sub) {
                    try {
                        const response = await fetch(`${API_BASE_URL}/users/${decoded.sub}`, {
                            method: 'GET',
                            headers: {
                                'Authorization': `Bearer ${token}`,
                                'Content-Type': 'application/json'
                            }
                        });

                        if (response.ok) {
                            const userData = await response.json();
                            // Isi otomatis Nama dan Email
                            setDataForm(prev => ({
                                ...prev,
                                namaLengkap: userData.full_name,
                                alamatEmail: userData.email
                            }));
                        }
                    } catch (error) {
                        console.error("Gagal mengambil data user:", error);
                    }
                }
            } else {
                setIsLoggedIn(false);
            }
        };

        checkLoginAndFetchUser();
    }, []);

    const Perubahan = (e) => {
        const { name, value } = e.target;
        setDataForm(prevState => ({
            ...prevState,
            [name]: value
        }));
    };

    const Submit = (e) => {
        e.preventDefault();
        if (!isLoggedIn) {
            alert("Anda harus login terlebih dahulu untuk mengirim pesan.");
            return;
        }
        if (dataForm.namaLengkap && dataForm.alamatEmail && dataForm.pesan) {
            setPopUp(true);
        } else {
            alert("Harap isi semua kolom yang wajib diisi.");
        }
    };

    const TutupPopUp = () => {
        setPopUp(false);
    };

    // Fungsi untuk mengirim data ke Database (Feedback Table)
    const KirimKeDatabase = async () => {
        setIsLoading(true);
        try {
            const token = localStorage.getItem('authToken');
            
            const response = await fetch(`${API_BASE_URL}/feedback/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    // user_id akan diambil otomatis dari token di backend
                    message: dataForm.pesan,
                    // Status default 'Baru' sudah diatur di model database
                })
            });

            if (response.ok) {
                alert("Pesan Anda berhasil dikirim!");
                // Reset pesan saja, nama dan email tetap biarkan karena user masih login
                setDataForm(prev => ({ ...prev, pesan: '' }));
                setPopUp(false);
            } else {
                const errorData = await response.json();
                alert(`Gagal mengirim pesan: ${errorData.error || 'Terjadi kesalahan'}`);
            }
        } catch (error) {
            console.error("Error submitting feedback:", error);
            alert("Terjadi kesalahan koneksi server.");
        } finally {
            setIsLoading(false);
        }
    };


    return (
        <div>
            <title>Kontak</title>
            <Navbar />
            <main>
                <div className="kontak-hero-banner">
                    <img
                        src={bgImage}
                        alt="Dekorasi latar belakang"
                        className="hero-banner-bg-image"
                    />
                    <h1 className="hero-banner-title">Kontak</h1>
                </div>
                
                <section className="form-section">
                    <img src={dotsLeft} alt="Dekorasi titik" className="dots-left-form" />
                    <img src={shapeRight} alt="Dekorasi bentuk kanan" className="shape-right-form" />
                    <img src={shapeLeft} alt="Dekorasi bentuk kiri" className="shape-left-form" />
                    
                    <div className="form-container">
                        {!isLoggedIn && (
                            <div className="alert alert-warning text-center mb-3" style={{ color: '#856404', backgroundColor: '#fff3cd', padding: '10px', borderRadius: '5px' }}>
                                Silakan <strong>Login</strong> terlebih dahulu untuk mengirim pesan kontak.
                            </div>
                        )}

                        <form onSubmit={Submit}>
                            <div className="form-group">
                                <label htmlFor="namaLengkap">Nama Lengkap *</label>
                                <input
                                    type="text"
                                    id="namaLengkap"
                                    name="namaLengkap"
                                    value={dataForm.namaLengkap}
                                    onChange={Perubahan}
                                    required
                                    // ReadOnly jika sudah login agar tidak bisa diubah
                                    readOnly={isLoggedIn} 
                                    className={isLoggedIn ? 'bg-light' : ''}
                                    placeholder={isLoggedIn ? '' : 'Login untuk mengisi otomatis'}
                                />
                            </div>
                            <div className="form-group">
                                <label htmlFor="alamatEmail">Alamat Email *</label>
                                <input
                                    type="email"
                                    id="alamatEmail"
                                    name="alamatEmail"
                                    value={dataForm.alamatEmail}
                                    onChange={Perubahan}
                                    required
                                    // ReadOnly jika sudah login
                                    readOnly={isLoggedIn}
                                    className={isLoggedIn ? 'bg-light' : ''}
                                    placeholder={isLoggedIn ? '' : 'Login untuk mengisi otomatis'}
                                />
                            </div>
                            <div className="form-group">
                                <label htmlFor="pesan">Pesan *</label>
                                <textarea
                                    id="pesan"
                                    name="pesan"
                                    rows="5"
                                    value={dataForm.pesan}
                                    onChange={Perubahan}
                                    required
                                    disabled={!isLoggedIn} // Disable textarea jika belum login
                                    placeholder={!isLoggedIn ? 'Silakan login untuk menulis pesan...' : 'Tulis pesan Anda di sini...'}
                                ></textarea>
                            </div>
                            
                            <button 
                                type="submit" 
                                className="kirim-btn" 
                                disabled={!isLoggedIn || isLoading}
                                style={{ opacity: !isLoggedIn ? 0.6 : 1, cursor: !isLoggedIn ? 'not-allowed' : 'pointer' }}
                            >
                                {isLoading ? 'Mengirim...' : 'Kirim'}
                            </button>
                        </form>
                    </div>
                </section>

                {/* --- BAGIAN POP-UP KONFIRMASI --- */}
                {popUpKonfirmasi && (
                    <div className="popup-overlay" onClick={TutupPopUp}>
                        <div className="popup-content" onClick={(e) => e.stopPropagation()}>
                            <h2>Konfirmasi Data</h2>
                            <p><strong>Nama Lengkap:</strong> {dataForm.namaLengkap}</p>
                            <p><strong>Alamat Email:</strong> {dataForm.alamatEmail}</p>
                            <p><strong>Pesan:</strong> {dataForm.pesan}</p>
                            
                            <div className="popup-actions">
                                <button onClick={TutupPopUp} className="popup-edit-btn" disabled={isLoading}>
                                    Perbaiki
                                </button>
                                {/* Tombol ini sekarang memanggil KirimKeDatabase */}
                                <button onClick={KirimKeDatabase} className="popup-confirm-btn" disabled={isLoading}>
                                    {isLoading ? 'Menyimpan...' : 'Sudah Betul'}
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </main>
            <Footer />
        </div>
    );
}

export default Kontak;