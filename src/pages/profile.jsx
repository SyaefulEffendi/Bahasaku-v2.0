import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Form, Button, Modal, Image, InputGroup, Spinner, Alert } from 'react-bootstrap';
import { 
    FaUser, FaEnvelope, FaHome, FaBirthdayCake, FaInfoCircle, 
    FaCamera, FaEdit, FaLock, FaSave, FaTimes, FaArrowLeft,
    FaTachometerAlt
} from 'react-icons/fa'; 
import './css/profile.css'; 
import { useAuth } from '../context';  
import { useNavigate } from 'react-router-dom';

// Fungsi konversi tanggal
const convertToYYYYMMDD = (dateStr) => {
    if (!dateStr || typeof dateStr !== 'string') return '';
    const yyyy_mm_dd_regex = /^\d{4}-\d{2}-\d{2}/;
    if (yyyy_mm_dd_regex.test(dateStr)) return dateStr.split('T')[0];
    const dd_mm_yyyy_regex = /^(\d{2})\/(\d{2})\/(\d{4})/;
    const match = dateStr.match(dd_mm_yyyy_regex);
    if (match) return `${match[3]}-${match[2]}-${match[1]}`;
    return '';
};

// --- FIX 1: Helper untuk memperbaiki URL Gambar (Masalah Docker Port) ---
const getDisplayImage = (url) => {
    if (!url) return 'https://via.placeholder.com/150'; // Gambar default jika kosong
    
    // Jika base64 (preview sebelum upload), kembalikan langsung
    if (url.startsWith('data:')) return url;

    // FIX UTAMA: Jika URL dari backend mengandung localhost:5000, ubah ke 8080
    if (url.includes('localhost:5000')) {
        return url.replace('localhost:5000', 'localhost:8080');
    }

    // Jika backend hanya menyimpan path relatif (misal: /static/foto...), tambahkan host
    if (url.startsWith('/')) {
        return `http://localhost:8080${url}`;
    }

    return url;
};

const Profile = () => {
    const { user, token, login } = useAuth();
    const navigate = useNavigate();

    const [isEditing, setIsEditing] = useState(false);
    const [showPhotoModal, setShowPhotoModal] = useState(false);
    const [showPasswordModal, setShowPasswordModal] = useState(false);
    const [photoPreview, setPhotoPreview] = useState(null);
    
    const [formValues, setFormValues] = useState(null); 
    
    const [passwordForm, setPasswordForm] = useState({
        oldPassword: '',
        newPassword: '',
        confirmPassword: ''
    });

    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    
    const [passError, setPassError] = useState(null);
    const [passSuccess, setPassSuccess] = useState(null);

    // --- FIX 2: Debugging Role Admin ---
    // Cek di console browser apakah 'role' ada di dalam objek user
    useEffect(() => {
        console.log("Current User Data:", user); 
    }, [user]);

    useEffect(() => {
        if (user) {
            setFormValues({
                full_name: user.full_name || '',
                email: user.email || '',
                user_type: user.user_type || '',
                location: user.location || '',
                birth_date: convertToYYYYMMDD(user.birth_date),
                profile_pic_url: user.profile_pic_url // Simpan URL asli, nanti diproses di render
            });
        }
    }, [user]);

    // ... (Fungsi handleChange, handlePasswordInput, handleSave, dll TETAP SAMA) ...
    // ... Copy paste logika handleSave, handleChange, dll dari file lama Anda di sini ...
    
    const handleEditToggle = () => {
        if (isEditing) {
            setFormValues({
                full_name: user.full_name,
                email: user.email,
                user_type: user.user_type,
                location: user.location,
                birth_date: convertToYYYYMMDD(user.birth_date),
                profile_pic_url: user.profile_pic_url
            });
            setError(null); 
            setSuccess(null); 
        }
        setIsEditing(!isEditing);
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormValues({ ...formValues, [name]: value });
    };

    const handlePasswordInput = (e) => {
        const { name, value } = e.target;
        setPasswordForm({ ...passwordForm, [name]: value });
    };

    const handleSave = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);
        setSuccess(null);

        if (!user || !user.id || !token) {
            setError('Sesi habis. Silakan login ulang.');
            setIsLoading(false);
            return;
        }

        const dataToSubmit = {
            full_name: formValues.full_name,
            location: formValues.location,
            birth_date: formValues.birth_date || null
        };

        try {
            const response = await fetch(`http://localhost:8080/api/users/${user.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}` 
                },
                body: JSON.stringify(dataToSubmit)
            });

            const data = await response.json();

            if (!response.ok) throw new Error(data.error || 'Gagal menyimpan.');

            const duration = localStorage.getItem('loginDuration') || (24 * 60 * 60 * 1000);
            const rememberMe = parseInt(duration) > (24 * 60 * 60 * 1000);
            login(data.user, token, rememberMe); 

            setIsEditing(false);
            setSuccess('Profil berhasil diperbarui!');

        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };
    
    const handlePhotoChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            if (!['image/png', 'image/jpeg', 'image/gif'].includes(file.type)) {
                setError('Format file tidak didukung. Gunakan PNG, JPG, atau GIF.');
                return;
            }
            const reader = new FileReader();
            reader.onloadend = () => {
                setPhotoPreview({ file: file, preview: reader.result });
            };
            reader.readAsDataURL(file);
        }
    };

    const handleConfirmPhoto = async () => {
        if (!photoPreview) return;
        await uploadProfilePhoto(photoPreview.file);
        setPhotoPreview(null);
    };

    const handleCancelPhoto = () => {
        setPhotoPreview(null);
        setError(null);
    };

    const uploadProfilePhoto = async (file) => {
        if (!user || !user.id || !token) return;

        setIsLoading(true);
        setError(null);

        const formData = new FormData();
        formData.append('photo', file);

        try {
            const response = await fetch(`http://localhost:8080/api/users/${user.id}/photo`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Gagal mengupload foto.');

            const duration = localStorage.getItem('loginDuration') || (24 * 60 * 60 * 1000);
            const rememberMe = parseInt(duration) > (24 * 60 * 60 * 1000);
            login(data.user, token, rememberMe);

            setFormValues(prev => ({ ...prev, profile_pic_url: data.user.profile_pic_url }));
            setShowPhotoModal(false);
            setSuccess('Foto profil berhasil diupload!');
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };
    
    const handlePasswordChange = async (e) => {
        e.preventDefault();
        setPassError(null);
        setPassSuccess(null);
        setIsLoading(true);

        if (passwordForm.newPassword !== passwordForm.confirmPassword) {
            setPassError("Konfirmasi password baru tidak cocok.");
            setIsLoading(false);
            return;
        }

        try {
            const response = await fetch(`http://localhost:8080/api/users/${user.id}/change-password`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    old_password: passwordForm.oldPassword,
                    new_password: passwordForm.newPassword
                })
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Gagal mengganti password.');

            setPassSuccess("Password berhasil diganti!");
            setPasswordForm({ oldPassword: '', newPassword: '', confirmPassword: '' });
            setTimeout(() => {
                setShowPasswordModal(false);
                setPassSuccess(null);
            }, 2000);

        } catch (err) {
            setPassError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    const closePasswordModal = () => {
        setShowPasswordModal(false);
        setPassError(null);
        setPassSuccess(null);
        setPasswordForm({ oldPassword: '', newPassword: '', confirmPassword: '' });
    };

    if (!user || !formValues) {
        return (
            <div className="profile-background" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
                <Spinner animation="border" variant="primary" />
            </div>
        );
    }

    // --- LOGIKA UTAMA RENDER ---
    
    // Perbaikan logika tombol Admin: Cek case-insensitive
    const isAdmin = (user.role || '').toLowerCase() === 'admin';

    // Perbaikan URL Gambar: Gunakan helper function
    const displayProfilePic = getDisplayImage(formValues.profile_pic_url);

    return (
        <div className="profile-background">
            <Container className="py-5">
                <Row className="justify-content-center">
                    <Col lg={4} xl={3} className="mb-4 mb-lg-0">
                        <Card className="profile-sidebar-card text-center shadow">
                            <Card.Body>
                                <div className="profile-pic-wrapper mx-auto mb-3">
                                    {/* Gunakan variabel displayProfilePic yang sudah diperbaiki */}
                                    <Image 
                                        src={displayProfilePic} 
                                        roundedCircle 
                                        className="profile-pic"
                                        onError={(e) => { e.target.src = 'https://via.placeholder.com/150'; }} 
                                    />
                                    <Button
                                        className="edit-pic-btn shadow-sm"
                                        onClick={() => setShowPhotoModal(true)}
                                    >
                                        <FaCamera />
                                    </Button>
                                </div>
                                <h5>{formValues.full_name}</h5>
                                <p className="text-muted">{formValues.email}</p>

                                {/* Gunakan variabel isAdmin yang lebih aman */}
                                {isAdmin && (
                                    <Button 
                                        variant="primary" 
                                        className="mt-4 w-100" 
                                        onClick={() => navigate('/dashboard-admin')}
                                    >
                                        <FaTachometerAlt className="me-2" /> Dashboard Admin
                                    </Button>
                                )}

                                <Button 
                                    variant="outline-primary" 
                                    className="w-100"
                                    style={{ marginTop: isAdmin ? '0.5rem' : '1.5rem' }}
                                    onClick={() => navigate('/')}
                                >
                                    <FaArrowLeft className="me-2" /> Kembali
                                </Button>
                            </Card.Body>
                        </Card>
                    </Col>

                    {/* --- Kolom Kanan (TIDAK ADA PERUBAHAN SIGNIFIKAN, HANYA RENDER FORM) --- */}
                    <Col lg={8} xl={9}>
                        <Card className="profile-details-card shadow">
                            <Card.Body className="p-4">
                                <div className="d-flex justify-content-between align-items-center mb-4">
                                    <h4 className="mb-0">Profil Pengguna</h4>
                                    {isEditing ? (
                                        <div>
                                            <Button variant="success" onClick={handleSave} className="me-2" disabled={isLoading}>
                                                {isLoading ? <Spinner as="span" animation="border" size="sm" /> : <FaSave className="me-2" />} Simpan
                                            </Button>
                                            <Button variant="secondary" onClick={handleEditToggle} disabled={isLoading}>
                                                <FaTimes className="me-2" /> Batal
                                            </Button>
                                        </div>
                                    ) : (
                                        <Button variant="primary" onClick={handleEditToggle}>
                                            <FaEdit className="me-2" /> Edit Profil
                                        </Button>
                                    )}
                                </div>

                                {error && <Alert variant="danger">{error}</Alert>}
                                {success && <Alert variant="success">{success}</Alert>}

                                <Form onSubmit={handleSave}>
                                    {/* Form fields sama seperti sebelumnya */}
                                    <Row>
                                        <Col md={6}>
                                            <Form.Group className="mb-3">
                                                <Form.Label>Nama Lengkap</Form.Label>
                                                <InputGroup>
                                                    <InputGroup.Text><FaUser /></InputGroup.Text>
                                                    <Form.Control type="text" name="full_name" value={formValues.full_name} onChange={handleChange} disabled={!isEditing} />
                                                </InputGroup>
                                            </Form.Group>
                                        </Col>
                                        <Col md={6}>
                                            <Form.Group className="mb-3">
                                                <Form.Label>Alamat Email</Form.Label>
                                                <InputGroup>
                                                    <InputGroup.Text><FaEnvelope /></InputGroup.Text>
                                                    <Form.Control type="email" name="email" value={formValues.email} disabled />
                                                </InputGroup>
                                            </Form.Group>
                                        </Col>
                                        <Col md={6}>
                                            <Form.Group className="mb-3">
                                                <Form.Label>Tipe Pengguna</Form.Label>
                                                <InputGroup>
                                                    <InputGroup.Text><FaInfoCircle /></InputGroup.Text>
                                                    <Form.Control type="text" name="user_type" value={formValues.user_type} onChange={handleChange} disabled />
                                                </InputGroup>
                                            </Form.Group>
                                        </Col>
                                        <Col md={6}>
                                            <Form.Group className="mb-3">
                                                <Form.Label>Tanggal Lahir</Form.Label>
                                                <InputGroup>
                                                    <InputGroup.Text><FaBirthdayCake /></InputGroup.Text>
                                                    <Form.Control type="date" name="birth_date" value={formValues.birth_date} onChange={handleChange} disabled={!isEditing} />
                                                </InputGroup>
                                            </Form.Group>
                                        </Col>
                                        <Col md={12}>
                                            <Form.Group className="mb-4">
                                                <Form.Label>Lokasi (Tempat Tinggal)</Form.Label>
                                                <InputGroup>
                                                    <InputGroup.Text><FaHome /></InputGroup.Text>
                                                    <Form.Control type="text" name="location" value={formValues.location} onChange={handleChange} disabled={!isEditing} />
                                                </InputGroup>
                                            </Form.Group> 
                                        </Col>
                                    </Row>
                                    <hr />
                                    <Button variant="outline-danger" onClick={() => setShowPasswordModal(true)}>
                                        <FaLock className="me-2" /> Ganti Password
                                    </Button>
                                </Form>
                            </Card.Body>
                        </Card>
                    </Col>
                </Row>
            </Container>

            {/* Modal Ganti Foto (SAMA SEPERTI FILE ASLI) */}
            <Modal centered show={showPhotoModal} onHide={() => setShowPhotoModal(false)} size="sm">
                <Modal.Header closeButton><Modal.Title>Ganti Foto Profil</Modal.Title></Modal.Header>
                <Modal.Body>
                    {!photoPreview ? (
                        <>
                            <p>Pilih foto terbaik Anda. Ukuran file disarankan di bawah 5MB.</p>
                            <Form.Group controlId="formFile" className="mb-3">
                                <Form.Control type="file" accept="image/*" onChange={handlePhotoChange} disabled={isLoading} />
                            </Form.Group>
                        </>
                    ) : (
                        <>
                            <p className="mb-3">Pratinjau foto profil Anda:</p>
                            <div style={{ textAlign: 'center', marginBottom: '1rem' }}>
                                <Image src={photoPreview.preview} roundedCircle style={{ width: '150px', height: '150px', objectFit: 'cover' }} />
                            </div>
                        </>
                    )}
                    {error && <Alert variant="danger" className="mb-0">{error}</Alert>}
                </Modal.Body>
                <Modal.Footer>
                    {!photoPreview ? (
                        <Button variant="secondary" onClick={() => setShowPhotoModal(false)}>Tutup</Button>
                    ) : (
                        <>
                            <Button variant="secondary" onClick={handleCancelPhoto} disabled={isLoading}>Ganti Foto</Button>
                            <Button variant="primary" onClick={handleConfirmPhoto} disabled={isLoading}>Konfirmasi</Button>
                        </>
                    )}
                </Modal.Footer>
            </Modal>
            
            {/* Modal Ganti Password (SAMA SEPERTI FILE ASLI) */}
            <Modal centered show={showPasswordModal} onHide={closePasswordModal}>
                <Modal.Header closeButton><Modal.Title>Ganti Password</Modal.Title></Modal.Header>
                <Modal.Body>
                    {passError && <Alert variant="danger">{passError}</Alert>}
                    {passSuccess && <Alert variant="success">{passSuccess}</Alert>}
                    <Form onSubmit={handlePasswordChange}>
                        <Form.Group className="mb-3"><Form.Label>Password Lama</Form.Label><Form.Control type="password" name="oldPassword" value={passwordForm.oldPassword} onChange={handlePasswordInput} required /></Form.Group>
                        <Form.Group className="mb-3"><Form.Label>Password Baru</Form.Label><Form.Control type="password" name="newPassword" value={passwordForm.newPassword} onChange={handlePasswordInput} required /></Form.Group>
                        <Form.Group className="mb-3"><Form.Label>Konfirmasi Password Baru</Form.Label><Form.Control type="password" name="confirmPassword" value={passwordForm.confirmPassword} onChange={handlePasswordInput} required /></Form.Group>
                        <div className="d-grid"><Button variant="primary" type="submit" disabled={isLoading}>Simpan Password</Button></div>
                    </Form>
                </Modal.Body>
            </Modal>
        </div>
    );
};

export default Profile;