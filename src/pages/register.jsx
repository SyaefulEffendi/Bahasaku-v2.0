import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './css/register.css'; // Path ke CSS Anda

// 1. Impor ikon yang benar
import { MdEmail, MdVisibility, MdVisibilityOff, MdLocationOn, MdCalendarToday } from 'react-icons/md';

const API_URL = "http://localhost:8080/api/users/register"; 

const Register = () => {
    const [formData, setFormData] = useState({
        full_name: '',
        user_type: 'Dengar', // Nilai default
        email: '',
        location: '',
        birth_date: '',
        password: '',
    });
    const [showPassword, setShowPassword] = useState(false);
    
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(false);

    const navigate = useNavigate();

    // Handler ini sekarang bisa menangani input biasa DAN tombol Tipe Pengguna
    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
    };

    // Handler khusus untuk tombol Tipe Pengguna
    const handleUserTypeChange = (type) => {
        setFormData({
            ...formData,
            user_type: type
        });
    };

    const handleRegister = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setSuccess(false);

        const dataToSubmit = { 
            ...formData,
            location: formData.location || null,
            // Pastikan format tanggal YYYY-MM-DD
            birth_date: formData.birth_date || null
        };

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(dataToSubmit),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Gagal mendaftar.');
            }

            setSuccess(true);
            setTimeout(() => {
                navigate('/login');
            }, 2000);

        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="register-container">
            <title>Register</title>
            <div className="register-box">
                <div className="register-form-section">
                    <h2>Daftar Akun</h2>
                    <form onSubmit={handleRegister}>
                        
                        {error && <div className="error-message">{error}</div>}
                        {success && <div className="success-message">Pendaftaran berhasil! Anda akan diarahkan ke halaman login.</div>}

                        <div className="input-group">
                            <input
                                type="text"
                                placeholder="Nama Lengkap"
                                name="full_name"
                                value={formData.full_name}
                                onChange={handleChange}
                                required
                            />
                        </div>
                        
                        {/* 2. INI BAGIAN BARU YANG SESUAI DESAIN */}
                        <div className="input-group">
                            <label className="input-label">Tipe Pengguna</label>
                            <div className="user-type-options">
                                <button
                                    type="button" // PENTING: agar tidak submit form
                                    className={`user-type-box ${formData.user_type === 'Tuli' ? 'active' : ''}`}
                                    onClick={() => handleUserTypeChange('Tuli')}
                                >
                                    <strong>Tuli</strong>
                                    <span>Saya memiliki keterbatasan pendengaran</span>
                                </button>
                                <button
                                    type="button"
                                    className={`user-type-box ${formData.user_type === 'Dengar' ? 'active' : ''}`}
                                    onClick={() => handleUserTypeChange('Dengar')}
                                >
                                    <strong>Dengar</strong>
                                    <span>Saya dapat mendengar dengan normal</span>
                                </button>
                                <button
                                    type="button"
                                    className={`user-type-box ${formData.user_type === 'Umum' ? 'active' : ''}`}
                                    onClick={() => handleUserTypeChange('Umum')}
                                >
                                    <strong>Umum</strong>
                                    <span>Saya pengguna umum</span>
                                </button>
                            </div>
                        </div>

                        <div className="input-group">
                            <input
                                type="email"
                                placeholder="Alamat Email"
                                name="email"
                                value={formData.email}
                                onChange={handleChange}
                                required
                            />
                            <MdEmail className="input-icon" />
                        </div>

                        <div className="input-row">
                            <div className="input-group">
                                <input
                                    type="text"
                                    placeholder="Tempat Tinggal (Opsional)"
                                    name="location"
                                    value={formData.location}
                                    onChange={handleChange}
                                />
                                <MdLocationOn className="input-icon" />
                            </div>
                            <div className="input-group">
                                <input
                                    type="text" // Ubah ke text agar placeholder terlihat
                                    placeholder="Tanggal Lahir (Opsional)"
                                    name="birth_date"
                                    value={formData.birth_date}
                                    onChange={handleChange}
                                    onFocus={(e) => (e.target.type = 'date')} // Ubah ke date saat di-klik
                                    onBlur={(e) => (e.target.type = 'text')} // Kembalikan ke text jika kosong
                                />
                                <MdCalendarToday className="input-icon" />
                            </div>
                        </div>

                        <div className="input-group">
                            <input
                                type={showPassword ? "text" : "password"}
                                placeholder="Password"
                                name="password"
                                value={formData.password}
                                onChange={handleChange}
                                required
                            />
                            <span onClick={() => setShowPassword(!showPassword)} className="password-toggle-icon">
                                {showPassword ? <MdVisibilityOff /> : <MdVisibility />}
                            </span>
                        </div>
                        
                        <button type="submit" className="register-button" disabled={loading}>
                            {loading ? 'Mendaftar...' : 'Daftar'}
                        </button>
                    </form>

                    <div className="login-link">
                        <span>Sudah punya akun? <a href="/login">Masuk Sekarang</a></span>
                    </div>
                </div>

                <div className="register-image-section">
                    {/* Gambar diatur via CSS */}
                </div>
            </div>
        </div>
    );
};

export default Register;