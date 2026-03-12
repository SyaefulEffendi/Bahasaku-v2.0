import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './css/login.css'; // Path ke CSS Anda
import { useAuth } from '../context'; 

import { MdEmail, MdVisibility, MdVisibilityOff } from 'react-icons/md';
import { FcGoogle } from 'react-icons/fc';

const API_URL = "http://localhost:8080/api/users/login"; 

const Login = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    
    // --- 1. TAMBAHKAN STATE UNTUK "INGAT SAYA" ---
    const [rememberMe, setRememberMe] = useState(false); 
    
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const navigate = useNavigate();
    const auth = useAuth(); 

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                // --- 2. KIRIM STATUS "remember_me" KE BACKEND ---
                body: JSON.stringify({ 
                    email, 
                    password, 
                    remember_me: rememberMe // Kirim status checkbox
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Gagal login.');
            }

            // --- 3. KIRIM STATUS "rememberMe" KE CONTEXT ---
            auth.login(data.user, data.access_token, rememberMe); // Kirim ke context
            
            navigate('/'); 

        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleGoogleLogin = () => {
        setError('Login dengan Google belum diimplementasikan.');
    };

    return (
        <div className="login-container">
            <title>Login</title>
            <div className="login-box">
                <div className="login-form-section">
                    <h2>Masuk</h2>
                    
                    {error && <div className="error-message">{error}</div>}

                    <form onSubmit={handleLogin}>
                        {/* ... (input email dan password tidak berubah) ... */}
                        <div className="input-group">
                            <input
                                type="email"
                                placeholder="Alamat Email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                disabled={loading}
                            />
                            <MdEmail className="input-icon" />
                        </div>
                        <div className="input-group">
                            <input
                                type={showPassword ? "text" : "password"}
                                placeholder="Password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                disabled={loading}
                            />
                            <span onClick={() => setShowPassword(!showPassword)} className="password-toggle-icon">
                                {showPassword ? <MdVisibilityOff /> : <MdVisibility />}
                            </span>
                        </div>
                        
                        <div className="form-options">
                            <label>
                                {/* --- 4. HUBUNGKAN CHECKBOX KE STATE --- */}
                                <input 
                                    type="checkbox" 
                                    disabled={loading}
                                    checked={rememberMe}
                                    onChange={(e) => setRememberMe(e.target.checked)}
                                /> Ingat saya
                            </label>
                            <a href="#">Lupa Password?</a>
                        </div>
                        
                        <button type="submit" className="login-button" disabled={loading}>
                            {loading ? 'Memproses...' : 'Masuk'}
                        </button>
                    </form>
                    
                    {/* ... (sisa kode tidak berubah) ... */}
                    <div className="divider">
                        <span>Atau</span>
                    </div>
                    <button onClick={handleGoogleLogin} className="google-login-button" disabled={loading}>
                        <FcGoogle /> Masuk dengan Google
                    </button>
                    <div className="register-link">
                        <span>Belum punya akun? <a href="/register">Daftar Sekarang</a></span>
                    </div>
                </div>
                <div className="login-image-section">
                </div>
            </div>
        </div>
    );
};

export default Login;