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

// Import konfigurasi API
import API_BASE_URL, { SERVER_URL } from '../config/apiConfig';

const convertToYYYYMMDD = (dateStr) => {
    if (!dateStr || typeof dateStr !== 'string') return '';
    const yyyy_mm_dd_regex = /^\d{4}-\d{2}-\d{2}/;
    if (yyyy_mm_dd_regex.test(dateStr)) return dateStr.split('T')[0];
    const dd_mm_yyyy_regex = /^(\d{2})\/(\d{2})\/(\d{4})/;
    const match = dateStr.match(dd_mm_yyyy_regex);
    if (match) return `${match[3]}-${match[2]}-${match[1]}`;
    return '';
};

const Profile = () => {
    const { user, token, login } = useAuth();
    const navigate = useNavigate();

    const [isEditing, setIsEditing] = useState(false);
    const [showPhotoModal, setShowPhotoModal] = useState(false);
    const [showPasswordModal, setShowPasswordModal] = useState(false);
    const [photoPreview, setPhotoPreview] = useState(null);
    const [formValues, setFormValues] = useState(null); 
    const [passwordForm, setPasswordForm] = useState({ oldPassword: '', newPassword: '', confirmPassword: '' });

    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    const [passError, setPassError] = useState(null);
    const [passSuccess, setPassSuccess] = useState(null);

    useEffect(() => {
        if (user) {
            setFormValues({
                full_name: user.full_name || '',
                email: user.email || '',
                user_type: user.user_type || '',
                location: user.location || '',
                birth_date: convertToYYYYMMDD(user.birth_date),
                profile_pic_url: user.profile_pic_url
            });
        }
    }, [user]);

    // Helper untuk menangani URL gambar secara dinamis
    const getDisplayImage = (url) => {
        if (!url) return 'https://via.placeholder.com/150';
        if (url.startsWith('data:')) return url;
        
        // Menangani path relatif dari backend menggunakan SERVER_URL atau API_BASE_URL
        if (url.startsWith('/')) {
            return `${SERVER_URL || API_BASE_URL}${url}`;
        }
        
        // Jika URL masih mengandung localhost:5000 (hardcoded lama), bersihkan ke SERVER_URL
        if (url.includes('localhost:5000')) {
            return url.replace('http://localhost:5000', SERVER_URL || API_BASE_URL);
        }

        return url;
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormValues(prev => ({ ...prev, [name]: value }));
    };

    const handleEditToggle = () => {
        if (isEditing) {
            setFormValues({
                ...user,
                birth_date: convertToYYYYMMDD(user.birth_date)
            });
            setError(null); 
            setSuccess(null); 
        }
        setIsEditing(!isEditing);
    };

    const handleSave = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch(`${API_BASE_URL}/users/${user.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}` 
                },
                body: JSON.stringify({
                    full_name: formValues.full_name,
                    location: formValues.location,
                    birth_date: formValues.birth_date || null
                })
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Gagal menyimpan.');

            // Update session
            login(data.user, token, true); 
            setIsEditing(false);
            setSuccess('Profil berhasil diperbarui!');
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    const uploadProfilePhoto = async (file) => {
        setIsLoading(true);
        const formData = new FormData();
        formData.append('photo', file);

        try {
            const response = await fetch(`${API_BASE_URL}/users/${user.id}/photo`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Gagal mengupload foto.');

            login(data.user, token, true);
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
        if (passwordForm.newPassword !== passwordForm.confirmPassword) {
            setPassError("Konfirmasi password tidak cocok.");
            return;
        }

        setIsLoading(true);
        try {
            const response = await fetch(`${API_BASE_URL}/users/${user.id}/change-password`, {
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
            setTimeout(() => {
                setShowPasswordModal(false);
                setPassSuccess(null);
                setPasswordForm({ oldPassword: '', newPassword: '', confirmPassword: '' });
            }, 2000);
        } catch (err) {
            setPassError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    if (!user || !formValues) {
        return (
            <div className="profile-background d-flex justify-content-center align-items-center vh-100">
                <Spinner animation="border" variant="primary" />
            </div>
        );
    }

    const isAdmin = user.role?.toLowerCase() === 'admin';

    return (
        <div className="profile-background">
            <Container className="py-5">
                <Row className="justify-content-center">
                    {/* Sidebar Profil */}
                    <Col lg={4} xl={3} className="mb-4">
                        <Card className="profile-sidebar-card text-center shadow border-0">
                            <Card.Body>
                                <div className="profile-pic-wrapper mx-auto mb-3">
                                    <Image 
                                        src={getDisplayImage(formValues.profile_pic_url)} 
                                        roundedCircle 
                                        className="profile-pic"
                                        onError={(e) => { e.target.src = 'https://via.placeholder.com/150'; }} 
                                    />
                                    <Button className="edit-pic-btn shadow-sm" onClick={() => setShowPhotoModal(true)}>
                                        <FaCamera />
                                    </Button>
                                </div>
                                <h5>{formValues.full_name}</h5>
                                <p className="text-muted small">{formValues.email}</p>

                                {isAdmin && (
                                    <Button variant="primary" className="mt-3 w-100" onClick={() => navigate('/dashboard-admin')}>
                                        <FaTachometerAlt className="me-2" /> Admin Dashboard
                                    </Button>
                                )}
                                <Button variant="outline-secondary" className="mt-2 w-100" onClick={() => navigate('/')}>
                                    <FaArrowLeft className="me-2" /> Kembali
                                </Button>
                            </Card.Body>
                        </Card>
                    </Col>

                    {/* Form Detail Profil */}
                    <Col lg={8} xl={9}>
                        <Card className="profile-details-card shadow border-0">
                            <Card.Body className="p-4">
                                <div className="d-flex justify-content-between align-items-center mb-4">
                                    <h4 className="mb-0">Profil Pengguna</h4>
                                    {isEditing ? (
                                        <div className="d-flex gap-2">
                                            <Button variant="success" onClick={handleSave} disabled={isLoading}>
                                                {isLoading ? <Spinner size="sm" /> : <><FaSave className="me-2" /> Simpan</>}
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

                                {error && <Alert variant="danger" dismissible onClose={() => setError(null)}>{error}</Alert>}
                                {success && <Alert variant="success" dismissible onClose={() => setSuccess(null)}>{success}</Alert>}

                                <Form>
                                    <Row>
                                        <Col md={6}>
                                            <Form.Group className="mb-3">
                                                <Form.Label>Nama Lengkap</Form.Label>
                                                <InputGroup>
                                                    <InputGroup.Text><FaUser /></InputGroup.Text>
                                                    <Form.Control name="full_name" value={formValues.full_name} onChange={handleChange} disabled={!isEditing} />
                                                </InputGroup>
                                            </Form.Group>
                                        </Col>
                                        <Col md={6}>
                                            <Form.Group className="mb-3">
                                                <Form.Label>Email</Form.Label>
                                                <InputGroup>
                                                    <InputGroup.Text><FaEnvelope /></InputGroup.Text>
                                                    <Form.Control value={formValues.email} disabled />
                                                </InputGroup>
                                            </Form.Group>
                                        </Col>
                                        <Col md={6}>
                                            <Form.Group className="mb-3">
                                                <Form.Label>Tipe Pengguna</Form.Label>
                                                <InputGroup>
                                                    <InputGroup.Text><FaInfoCircle /></InputGroup.Text>
                                                    <Form.Control value={formValues.user_type} disabled />
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
                                                <Form.Label>Lokasi</Form.Label>
                                                <InputGroup>
                                                    <InputGroup.Text><FaHome /></InputGroup.Text>
                                                    <Form.Control name="location" value={formValues.location} onChange={handleChange} disabled={!isEditing} />
                                                </InputGroup>
                                            </Form.Group> 
                                        </Col>
                                    </Row>
                                    <hr />
                                    <Button variant="outline-danger" size="sm" onClick={() => setShowPasswordModal(true)}>
                                        <FaLock className="me-2" /> Ganti Password
                                    </Button>
                                </Form>
                            </Card.Body>
                        </Card>
                    </Col>
                </Row>
            </Container>

            {/* Modals tetap fungsional namun dengan pemanggilan API yang sudah bersih */}
            {/* Modal Foto & Password dipertahankan dengan logika API yang sama */}
            <Modal centered show={showPhotoModal} onHide={() => setShowPhotoModal(false)} size="sm">
                <Modal.Header closeButton><Modal.Title>Ganti Foto</Modal.Title></Modal.Header>
                <Modal.Body className="text-center">
                    {!photoPreview ? (
                        <Form.Control type="file" accept="image/*" onChange={(e) => {
                            const file = e.target.files[0];
                            if (file) setPhotoPreview({ file, preview: URL.createObjectURL(file) });
                        }} />
                    ) : (
                        <Image src={photoPreview.preview} roundedCircle className="mb-3" style={{ width: '150px', height: '150px', objectFit: 'cover' }} />
                    )}
                </Modal.Body>
                <Modal.Footer>
                    {photoPreview && <Button variant="primary" onClick={() => uploadProfilePhoto(photoPreview.file)}>Simpan</Button>}
                </Modal.Footer>
            </Modal>

            <Modal centered show={showPasswordModal} onHide={() => setShowPasswordModal(false)}>
                <Modal.Header closeButton><Modal.Title>Ganti Password</Modal.Title></Modal.Header>
                <Modal.Body>
                    {passError && <Alert variant="danger">{passError}</Alert>}
                    {passSuccess && <Alert variant="success">{passSuccess}</Alert>}
                    <Form onSubmit={handlePasswordChange}>
                        <Form.Group className="mb-2"><Form.Label>Password Lama</Form.Label><Form.Control type="password" required onChange={(e) => setPasswordForm({...passwordForm, oldPassword: e.target.value})} /></Form.Group>
                        <Form.Group className="mb-2"><Form.Label>Password Baru</Form.Label><Form.Control type="password" required onChange={(e) => setPasswordForm({...passwordForm, newPassword: e.target.value})} /></Form.Group>
                        <Form.Group className="mb-3"><Form.Label>Konfirmasi</Form.Label><Form.Control type="password" required onChange={(e) => setPasswordForm({...passwordForm, confirmPassword: e.target.value})} /></Form.Group>
                        <Button variant="primary" type="submit" className="w-100" disabled={isLoading}>Simpan</Button>
                    </Form>
                </Modal.Body>
            </Modal>
        </div>
    );
};

export default Profile;