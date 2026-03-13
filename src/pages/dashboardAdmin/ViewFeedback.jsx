import React, { useState, useEffect, memo } from 'react';
import { Container, Table, Button, Badge, Modal, Form } from 'react-bootstrap';

const API_BASE_URL = 'http://localhost:8080/api';

const ViewFeedback = memo(() => {
    const [feedbacks, setFeedbacks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // State untuk Modal Update
    const [showModal, setShowModal] = useState(false);
    const [selectedFeedback, setSelectedFeedback] = useState(null);
    const [statusToUpdate, setStatusToUpdate] = useState('');

    // Fetch data feedback dari database
    const fetchFeedbacks = async () => {
        try {
            setLoading(true); // Set loading true saat refresh data
            setError(null);

            const response = await fetch(`${API_BASE_URL}/feedback/`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                setError('Gagal mengambil data feedback dari server.');
                setLoading(false);
                return;
            }

            const data = await response.json();
            setFeedbacks(data);
        } catch (err) {
            console.error('Error fetching feedbacks:', err);
            setError(`Terjadi kesalahan: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchFeedbacks();
    }, []);

    // Fungsi menghapus feedback
    const handleDelete = async (feedbackId) => {
        if (!window.confirm('Apakah Anda yakin ingin menghapus feedback ini?')) {
            return;
        }

        try {
            const token = localStorage.getItem('authToken');
            if (!token) {
                setError('Token tidak ditemukan.');
                return;
            }

            const response = await fetch(`${API_BASE_URL}/feedback/${feedbackId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                setError('Gagal menghapus feedback.');
                return;
            }

            await fetchFeedbacks();
            alert('Feedback berhasil dihapus.');
        } catch (err) {
            console.error('Error deleting feedback:', err);
            setError(`Gagal menghapus feedback: ${err.message}`);
        }
    };

    // Fungsi Menampilkan Modal Update
    const handleShowUpdate = (feedback) => {
        setSelectedFeedback(feedback);
        setStatusToUpdate(feedback.status); // Set status awal sesuai data saat ini
        setShowModal(true);
    };

    const handleCloseModal = () => {
        setShowModal(false);
        setSelectedFeedback(null);
    };

    // Fungsi Menyimpan Perubahan Status ke Database
    const handleSaveStatus = async () => {
        if (!selectedFeedback) return;

        try {
            const token = localStorage.getItem('authToken');
            if (!token) {
                alert('Token tidak ditemukan. Silakan login ulang.');
                return;
            }

            const response = await fetch(`${API_BASE_URL}/feedback/${selectedFeedback.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ status: statusToUpdate })
            });

            if (!response.ok) {
                alert('Gagal mengupdate status.');
                return;
            }

            alert('Status berhasil diperbarui!');
            setShowModal(false);
            fetchFeedbacks(); // Refresh tabel
        } catch (err) {
            console.error('Error updating status:', err);
            alert(`Terjadi kesalahan: ${err.message}`);
        }
    };

    // Helper untuk warna status (Badge)
    const getStatusBadge = (status) => {
        switch (status) {
            case 'Selesai':
                return <Badge bg="success">Selesai</Badge>; // Hijau
            case 'Ditinjau':
                return <Badge bg="warning" text="dark">Ditinjau</Badge>; // Oren/Kuning
            case 'Baru':
            default:
                return <Badge bg="secondary">Baru</Badge>; // Abu-abu
        }
    };

    return (
        <Container fluid className="p-0">
            <h2 className="main-title">Umpan Balik Pengguna</h2>
            {error && (
                <div className="alert alert-danger alert-dismissible fade show" role="alert">
                    {error}
                    <button type="button" className="btn-close" onClick={() => setError(null)}></button>
                </div>
            )}

            {loading ? (
                <div className="alert alert-info">Memuat data feedback...</div>
            ) : feedbacks.length === 0 ? (
                <div className="alert alert-warning">Tidak ada data feedback ditemukan.</div>
            ) : (
                <Table key="feedback-table" striped bordered hover responsive>
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Pengguna</th>
                            <th>Umpan Balik</th>
                            <th>Status</th>
                            <th>Tanggal Dibuat</th>
                            <th style={{ width: '180px' }}>Aksi</th>
                        </tr>
                    </thead>
                    <tbody>
                        {feedbacks.map((feedback, index) => (
                            <tr key={feedback.id}>
                                <td>{index + 1}</td>
                                <td>{feedback.user ? feedback.user.full_name : 'Unknown'}</td>
                                <td>{feedback.message}</td>
                                <td>{getStatusBadge(feedback.status)}</td>
                                <td>{new Date(feedback.created_at).toLocaleString()}</td>
                                <td>
                                    <div className="d-flex gap-2">
                                        <Button
                                            variant="primary"
                                            size="sm"
                                            onClick={() => handleShowUpdate(feedback)}
                                        >
                                            Update
                                        </Button>
                                        <Button
                                            variant="danger"
                                            size="sm"
                                            onClick={() => handleDelete(feedback.id)}
                                        >
                                            Hapus
                                        </Button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </Table>
            )}

            {/* Modal (Pop-up) Update Status */}
            <Modal show={showModal} onHide={handleCloseModal} centered>
                <Modal.Header closeButton>
                    <Modal.Title>Update Status Feedback</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    {selectedFeedback && (
                        <Form>
                            <Form.Group className="mb-3">
                                <Form.Label>Pengguna</Form.Label>
                                <Form.Control type="text" value={selectedFeedback.user ? selectedFeedback.user.full_name : 'Unknown'} disabled />
                            </Form.Group>
                            <Form.Group className="mb-3">
                                <Form.Label>Pesan</Form.Label>
                                <Form.Control as="textarea" rows={3} value={selectedFeedback.message} disabled />
                            </Form.Group>
                            <Form.Group className="mb-3">
                                <Form.Label>Status</Form.Label>
                                <Form.Select 
                                    value={statusToUpdate} 
                                    onChange={(e) => setStatusToUpdate(e.target.value)}
                                >
                                    <option value="Baru">Baru (Abu-abu)</option>
                                    <option value="Ditinjau">Ditinjau (Oren)</option>
                                    <option value="Selesai">Selesai (Hijau)</option>
                                </Form.Select>
                            </Form.Group>
                        </Form>
                    )}
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={handleCloseModal}>
                        Batal
                    </Button>
                    <Button variant="primary" onClick={handleSaveStatus}>
                        Simpan Perubahan
                    </Button>
                </Modal.Footer>
            </Modal>

        </Container>
    );
});

ViewFeedback.displayName = 'ViewFeedback';

export default ViewFeedback;