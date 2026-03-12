import React, { createContext, useState, useContext, useEffect } from 'react';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(null);

    const logout = () => {
        localStorage.removeItem('authToken');
        localStorage.removeItem('authUser');
        localStorage.removeItem('loginTimestamp');
        localStorage.removeItem('loginDuration');
        setUser(null);
        setToken(null);
    };

    useEffect(() => {
        const storedToken = localStorage.getItem('authToken');
        const storedUser = localStorage.getItem('authUser');
        const storedTimestamp = localStorage.getItem('loginTimestamp');
        const storedDuration = localStorage.getItem('loginDuration');
        
        // --- UBAH DEFAULT KE 8 JAM (8 * 60 menit * 60 detik * 1000 ms) ---
        const defaultDuration = 8 * 60 * 60 * 1000; 
        const maxDuration = storedDuration ? parseInt(storedDuration) : defaultDuration;

        if (storedToken && storedUser && storedTimestamp) {
            const loginTime = parseInt(storedTimestamp);

            if ((Date.now() - loginTime) > maxDuration) { 
                logout();
            } else {
                setToken(storedToken);
                setUser(JSON.parse(storedUser));
            }
        }
    }, []); 

    const login = (userData, authToken, rememberMe = false) => {
        
        const eightHours = 8 * 60 * 60 * 1000; // 8 Jam
        const thirtyDays = 30 * 24 * 60 * 60 * 1000; // 30 Hari (Jika Remember Me)
        
        const duration = rememberMe ? thirtyDays : eightHours;

        localStorage.setItem('authToken', authToken);
        localStorage.setItem('authUser', JSON.stringify(userData));
        localStorage.setItem('loginTimestamp', Date.now().toString());
        localStorage.setItem('loginDuration', duration.toString());

        setUser(userData);
        setToken(authToken);
    };

    return (
        <AuthContext.Provider value={{ user, token, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    return useContext(AuthContext);
};