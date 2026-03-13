import React, { useState, useMemo, memo, useEffect } from 'react';
import { Container, Table, Button, Form, Modal } from 'react-bootstrap';
import { FaPlus } from 'react-icons/fa';
import SearchInput from './SearchInput';

const API_BASE_URL = 'http://localhost:8080/api';

const ManageVocabulary = memo(({ searchTerm, setSearchTerm }) => {
    const [vocabs, setVocabs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showAddModal, setShowAddModal] = useState(false);
    const [showEditModal, setShowEditModal] = useState(false);
    const [editVocab, setEditVocab] = useState(null);

    const [formState, setFormState] = useState({
        text: '',
        category: 'Lainnya',
        video: null
    });

    // Fetch data kosakata dari database
    const fetchVocabs = async () => {
        try {
            setLoading(true);
            setError(null);

            const response = await fetch(`${API_BASE_URL}/kosa-kata/`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                setError('Gagal mengambil data kosakata dari server.');
                setLoading(false);
                return;
            }

            const data = await response.json();
            setVocabs(data);
        } catch (err) {
            console.error('Error fetching vocabs:', err);
            setError(`Terjadi kesalahan: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchVocabs();
    }, []);

    const filteredVocabs = useMemo(() => {
        return vocabs.filter(vocab =>
            vocab.text.toLowerCase().includes(searchTerm.toLowerCase())
        );
    }, [searchTerm, vocabs]);

    const handleDelete = async (vocabId) => {
        if (!window.confirm('Apakah Anda yakin ingin menghapus kosakata ini?')) {
            return;
        }

        try {
            const token = localStorage.getItem('authToken');
            if (!token) {
                setError('Token tidak ditemukan.');
                return;
            }

            const response = await fetch(`${API_BASE_URL}/kosa-kata/${vocabId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                setError('Gagal menghapus kosakata.');
                return;
            }

            await fetchVocabs();
            alert('Kosakata berhasil dihapus.');
        } catch (err) {
            console.error('Error deleting vocab:', err);
            setError(`Gagal menghapus kosakata: ${err.message}`);
        }
    };

    const handleOpenAdd = () => {
        setFormState({ text: '', category: 'Lainnya', video: null });
        setShowAddModal(true);
    };

    const handleOpenEdit = (vocab) => {
        setEditVocab(vocab);
        setFormState({
            text: vocab.text || '',
            category: vocab.category || 'Lainnya',
            video: null
        });
        setShowEditModal(true);
    };

    const handleFormChange = (e) => {
        const { name, value, files } = e.target;
        if (name === 'video') {
            setFormState(prev => ({ ...prev, [name]: files[0] }));
        } else {
            setFormState(prev => ({ ...prev, [name]: value }));
        }
    };

    const handleSubmitAdd = async (e) => {
        e.preventDefault();
        try {
            const token = localStorage.getItem('authToken');
            if (!token) {
                setError('Token tidak ditemukan. Silakan login kembali.');
                return;
            }

            const formData = new FormData();
            formData.append('text', formState.text);
            formData.append('category', formState.category);
            if (formState.video) {
                formData.append('video', formState.video);
            }

            const response = await fetch(`${API_BASE_URL}/kosa-kata/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData
            });

            if (!response.ok) {
                const err = await response.json();
                setError(err.error || 'Gagal menambah kosakata');
                return;
            }

            setShowAddModal(false);
            await fetchVocabs();
            alert('Kosakata berhasil ditambahkan');
        } catch (err) {
            console.error('Error adding vocab:', err);
            setError(err.message || 'Gagal menambah kosakata');
        }
    };

    const handleSubmitEdit = async (e) => {
        e.preventDefault();
        if (!editVocab) return;
        try {
            const token = localStorage.getItem('authToken');
            if (!token) {
                setError('Token tidak ditemukan. Silakan login kembali.');
                return;
            }

            const formData = new FormData();
            formData.append('text', formState.text);
            formData.append('category', formState.category);
            if (formState.video) {
                formData.append('video', formState.video);
            }

            const response = await fetch(`${API_BASE_URL}/kosa-kata/${editVocab.id}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData
            });

            if (!response.ok) {
                const err = await response.json();
                setError(err.error || 'Gagal memperbarui kosakata');
                return;
            }

            setShowEditModal(false);
            setEditVocab(null);
            await fetchVocabs();
            alert('Kosakata berhasil diperbarui');
        } catch (err) {
            console.error('Error updating vocab:', err);
            setError(err.message || 'Gagal memperbarui kosakata');
        }
    };

    return (
        <Container fluid className="p-0">
            <h2 className="main-title">Kelola Data Kosakata</h2>
            <SearchInput searchTerm={searchTerm} setSearchTerm={setSearchTerm} placeholder="Cari kosakata..." />

            {error && (
                <div className="alert alert-danger alert-dismissible fade show" role="alert">
                    {error}
                    <button type="button" className="btn-close" onClick={() => setError(null)}></button>
                </div>
            )}

            <Button variant="primary" className="mb-3" onClick={handleOpenAdd}><FaPlus className="me-2" /> Tambah Kosakata</Button>

            {loading ? (
                <div className="alert alert-info">Memuat data kosakata...</div>
            ) : filteredVocabs.length === 0 ? (
                <div className="alert alert-warning">Tidak ada data kosakata ditemukan.</div>
            ) : (
                <Table key="vocabs-table" striped bordered hover responsive>
                    <thead>
                        <tr><th>#</th><th>Kosakata</th><th>Kategori</th><th>Video</th><th>Aksi</th></tr>
                    </thead>
                    <tbody>
                        {filteredVocabs.map((vocab, index) => (
                            <tr key={vocab.id}>
                                <td>{index + 1}</td>
                                <td>{vocab.text}</td>
                                <td>{vocab.category}</td>
                                <td>
                                    <a href={`http://localhost:8080${vocab.video_file_path}`} target="_blank" rel="noopener noreferrer">
                                        Lihat Video
                                    </a>
                                </td>
                                <td>
                                    <Button variant="warning" size="sm" className="me-2" onClick={() => handleOpenEdit(vocab)}>Edit</Button>
                                    <Button
                                        variant="danger"
                                        size="sm"
                                        onClick={() => handleDelete(vocab.id)}
                                    >
                                        Hapus
                                    </Button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </Table>
            )}

            {/* Add Vocabulary Modal */}
            <Modal show={showAddModal} onHide={() => setShowAddModal(false)}>
                <Form onSubmit={handleSubmitAdd} encType="multipart/form-data">
                    <Modal.Header closeButton><Modal.Title>Tambah Kosakata</Modal.Title></Modal.Header>
                    <Modal.Body>
                        <Form.Group className="mb-2">
                            <Form.Label>Kosakata Teks</Form.Label>
                            <Form.Control name="text" value={formState.text} onChange={handleFormChange} required />
                        </Form.Group>
                        <Form.Group className="mb-2">
                            <Form.Label>Kategori</Form.Label>
                            <Form.Select name="category" value={formState.category} onChange={handleFormChange}>
                                <option value="Huruf">Huruf</option>
                                <option value="Umum">Umum</option>
                                <option value="Salam">Salam</option>
                                <option value="Makanan">Makanan</option>
                                <option value="Emosi">Emosi</option>
                                <option value="Lainnya">Lainnya</option>
                            </Form.Select>
                        </Form.Group>
                        <Form.Group className="mb-2">
                            <Form.Label>Video Kosakata</Form.Label>
                            <Form.Control name="video" type="file" accept="video/*" onChange={handleFormChange} required />
                        </Form.Group>
                    </Modal.Body>
                    <Modal.Footer>
                        <Button variant="secondary" onClick={() => setShowAddModal(false)}>Batal</Button>
                        <Button variant="primary" type="submit">Tambah</Button>
                    </Modal.Footer>
                </Form>
            </Modal>

            {/* Edit Vocabulary Modal */}
            <Modal show={showEditModal} onHide={() => setShowEditModal(false)}>
                <Form onSubmit={handleSubmitEdit} encType="multipart/form-data">
                    <Modal.Header closeButton><Modal.Title>Edit Kosakata</Modal.Title></Modal.Header>
                    <Modal.Body>
                        <Form.Group className="mb-2">
                            <Form.Label>Kosakata Teks</Form.Label>
                            <Form.Control name="text" value={formState.text} onChange={handleFormChange} required />
                        </Form.Group>
                        <Form.Group className="mb-2">
                            <Form.Label>Kategori</Form.Label>
                            <Form.Select name="category" value={formState.category} onChange={handleFormChange}>
                                <option value="Lainnya">Lainnya</option>
                                <option value="Umum">Umum</option>
                                <option value="Salam">Salam</option>
                                <option value="Makanan">Makanan</option>
                                <option value="Emosi">Emosi</option>
                                <option value="Tempat">Tempat</option>
                            </Form.Select>
                        </Form.Group>
                        <Form.Group className="mb-2">
                            <Form.Label>Video Kosakata (kosongkan jika tidak ingin mengganti)</Form.Label>
                            <Form.Control name="video" type="file" accept="video/*" onChange={handleFormChange} />
                        </Form.Group>
                    </Modal.Body>
                    <Modal.Footer>
                        <Button variant="secondary" onClick={() => setShowEditModal(false)}>Batal</Button>
                        <Button variant="primary" type="submit">Simpan Perubahan</Button>
                    </Modal.Footer>
                </Form>
            </Modal>
        </Container>
    );
});

ManageVocabulary.displayName = 'ManageVocabulary';

export default ManageVocabulary;
