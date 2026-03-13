import React, { useState, useEffect } from 'react';
import { Nav, Button } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom'; 
import { useAuth } from '../context'; 

// --- PERBAIKAN DI SINI (Menambahkan FaNewspaper) ---
import { FaUsers, FaEnvelope, FaBookOpen, FaUserShield, FaSignOutAlt, FaCog, FaBars, FaTimes, FaChevronDown, FaChevronRight, FaNewspaper } from 'react-icons/fa';
import './css/dashboardAdmin.css';
import logoBahasaku from './Image/logo-tittle-copy-0.png';

// Import komponen-komponen terpisah
import DashboardSummary from './dashboardAdmin/DashboardSummary';
import ManageUsers from './dashboardAdmin/ManageUsers';
import ManageVocabulary from './dashboardAdmin/ManageVocabulary';
import ManageAdmins from './dashboardAdmin/ManageAdmins';
import ViewFeedback from './dashboardAdmin/ViewFeedback';

// --- IMPORT KOMPONEN BARU ---
import ManageInformation from './dashboardAdmin/ManageInformation';

const API_BASE_URL = 'http://localhost:8080/api';

const DashboardAdmin = () => {
    const { user } = useAuth();
    const navigate = useNavigate();

    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [activeMenu, setActiveMenu] = useState('summary');
    const [searchTerm, setSearchTerm] = useState('');
    
    const [usersCount, setUsersCount] = useState(0);
    const [adminsCount, setAdminsCount] = useState(0);
    const [vocabCount, setVocabCount] = useState(0);
    const [feedbackCount, setFeedbackCount] = useState(0);
    
    // State baru untuk jumlah informasi
    const [infoCount, setInfoCount] = useState(0);

    const [recentFeedbacks, setRecentFeedbacks] = useState([]);
    const [usersOpen, setUsersOpen] = useState(false);

    // --- 1. Hook Proteksi (Redirect) ---
    useEffect(() => {
        if (!user || user.role !== 'Admin') {
            navigate('/'); 
        }
    }, [user, navigate]);

    // --- 2. Hook Fetch Data (Tetap Dijalankan) ---
    useEffect(() => {
        if (!user || user.role !== 'Admin') return;

        const fetchDashboardData = async () => {
            try {
                const token = localStorage.getItem('authToken');
                if (!token) return;

                const headers = {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                };

                // Fetch Users
                const usersResponse = await fetch(`${API_BASE_URL}/users/`, { method: 'GET', headers });
                if (usersResponse.ok) {
                    const usersData = await usersResponse.json();
                    const onlyUsers = usersData.filter(u => (u.role || '').toLowerCase() === 'user');
                    const onlyAdmins = usersData.filter(u => (u.role || '').toLowerCase() === 'admin');
                    
                    setUsersCount(onlyUsers.length);
                    setAdminsCount(onlyAdmins.length);
                }

                // Fetch Vocab
                const vocabResponse = await fetch(`${API_BASE_URL}/kosa-kata/`, { method: 'GET', headers });
                if (vocabResponse.ok) {
                    const vocabData = await vocabResponse.json();
                    setVocabCount(vocabData.length);
                }

                // Fetch Feedback
                const feedbackResponse = await fetch(`${API_BASE_URL}/feedback/`, { method: 'GET', headers });
                if (feedbackResponse.ok) {
                    const feedbackData = await feedbackResponse.json();
                    setFeedbackCount(feedbackData.length);
                    setRecentFeedbacks(feedbackData.slice(0, 5));
                }

                // --- FETCH INFO COUNT (BARU) ---
                const infoResponse = await fetch(`${API_BASE_URL}/information/`, { method: 'GET', headers });
                if (infoResponse.ok) {
                    const infoData = await infoResponse.json();
                    setInfoCount(infoData.length);
                }

            } catch (err) {
                console.error('Error fetching dashboard data:', err);
            }
        };

        fetchDashboardData();
    }, [user]); 

    // --- 3. Handlers ---
    const handleToggle = () => setSidebarOpen(!sidebarOpen);

    const handleMenuClick = (menu) => {
        setActiveMenu(menu);
        setSearchTerm('');
        setUsersOpen(false);
        if (window.innerWidth < 992) {
            setSidebarOpen(false);
        }
    };

    const renderContent = () => {
        switch (activeMenu) {
            case 'users': return <ManageUsers searchTerm={searchTerm} setSearchTerm={setSearchTerm} />;
            case 'vocabulary': return <ManageVocabulary searchTerm={searchTerm} setSearchTerm={setSearchTerm} />;
            case 'admins': return <ManageAdmins searchTerm={searchTerm} setSearchTerm={setSearchTerm} />;
            case 'feedback': return <ViewFeedback />;
            
            // --- MENU BARU ---
            case 'information': return <ManageInformation searchTerm={searchTerm} setSearchTerm={setSearchTerm} />;
            
            default: return (
                <DashboardSummary 
                    usersCount={usersCount}
                    adminsCount={adminsCount}
                    vocabCount={vocabCount}
                    feedbackCount={feedbackCount}
                    recentFeedbacks={recentFeedbacks}
                    // Anda bisa kirim infoCount ke sini jika ingin ditampilkan di summary
                />
            );
        }
    };

    // --- 4. EARLY RETURN ---
    if (!user || user.role !== 'Admin') {
        return null; 
    }

    // --- 5. Render Utama ---
    return (
        <div className="d-flex stisla-dashboard">
            <title>Dashboard Admin</title>
            <div className={`sidebar text-white ${sidebarOpen ? 'open' : ''}`}>
                <div className="sidebar-header d-flex align-items-center p-4">
                    <img src={logoBahasaku} alt="Bahasaku Logo" className="sidebar-logo" />
                    <h5 className="mb-0 text-white">Bahasaku</h5>
                    <Button variant="danger" className="d-lg-none ms-auto" onClick={handleToggle}><FaTimes size={20} /></Button>
                </div>
                <Nav className="flex-column p-4">
                    <Nav.Link onClick={() => handleMenuClick('summary')} className={`nav-link-stisla ${activeMenu === 'summary' ? 'active' : ''}`}><FaCog className="me-2" /> Dashboard</Nav.Link>

                    <div className={`nav-item user-admin-dropdown ${usersOpen ? 'show' : ''}`}>
                        <div
                            role="button"
                            tabIndex={0}
                            onClick={() => setUsersOpen(!usersOpen)}
                            onKeyPress={(e) => { if (e.key === 'Enter' || e.key === ' ') setUsersOpen(!usersOpen); }}
                            className={`nav-link-stisla d-flex justify-content-between align-items-center ${(activeMenu === 'users' || activeMenu === 'admins') ? 'active' : ''}`}
                        >
                            <span><FaUsers className="me-2" /> Kelola User</span>
                            <span>{usersOpen ? <FaChevronDown /> : <FaChevronRight />}</span>
                        </div>

                        <div className="submenu mt-2">
                            <Nav.Link onClick={() => handleMenuClick('users')} className={`nav-link-stisla ${activeMenu === 'users' ? 'active' : ''}`}>Kelola User</Nav.Link>
                            <Nav.Link onClick={() => handleMenuClick('admins')} className={`nav-link-stisla ${activeMenu === 'admins' ? 'active' : ''}`}>Kelola Admin</Nav.Link>
                        </div>
                    </div>

                    <Nav.Link onClick={() => handleMenuClick('vocabulary')} className={`nav-link-stisla ${activeMenu === 'vocabulary' ? 'active' : ''}`}><FaBookOpen className="me-2" /> Kelola Kosakata</Nav.Link>

                    {/* --- MENU BARU: KELOLA INFORMASI --- */}
                    <Nav.Link onClick={() => handleMenuClick('information')} className={`nav-link-stisla ${activeMenu === 'information' ? 'active' : ''}`}><FaNewspaper className="me-2" /> Kelola Informasi</Nav.Link>

                    <Nav.Link onClick={() => handleMenuClick('feedback')} className={`nav-link-stisla ${activeMenu === 'feedback' ? 'active' : ''}`}><FaEnvelope className="me-2" /> Umpan Balik</Nav.Link>
                </Nav>
                <a href="/">
                    <div className="mt-auto p-4"><Button variant="outline-light" className="w-100"><FaSignOutAlt className="me-2" /> Keluar dari Dashboard Admin</Button></div>
                </a>
            </div>

            <div className={`main-content flex-grow-1 p-0 ${sidebarOpen ? '' : 'shifted'}`}>
                <div className="top-navbar bg-white shadow-sm p-3 d-flex justify-content-between align-items-center">
                    <Button variant="light" className="d-lg-none" onClick={handleToggle}><FaBars size={20} /></Button>
                    <h5 className="mb-0 ms-auto">Hi, Admin!</h5>
                    <div className="user-profile ms-3"><div className="user-avatar"></div></div>
                </div>
                <div className="main-content-inner p-4">{renderContent()}</div>
            </div>
        </div>
    );
};

export default DashboardAdmin;