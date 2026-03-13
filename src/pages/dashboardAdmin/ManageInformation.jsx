import React, { useState, useMemo, memo, useEffect } from 'react';
import { Container, Table, Button, Form, Modal, Image } from 'react-bootstrap';
import { FaPlus, FaTrash, FaEdit } from 'react-icons/fa'; // Tambah FaEdit
import SearchInput from './SearchInput';

const API_BASE_URL = 'http://localhost:8080/api';

const ManageInformation = memo(({ searchTerm, setSearchTerm }) => {
    const [infos, setInfos] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    
    // Modal State
    const [showAddModal, setShowAddModal] = useState(false);
    const [showEditModal, setShowEditModal] = useState(false);
    const [editInfo, setEditInfo] = useState(null);
    
    const [formState, setFormState] = useState({
        title: '',
        content: '',
        image: null
    });

    // --- FETCH DATA ---
    const fetchInfos = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${API_BASE_URL}/information/`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });
            if (!response.ok) throw new Error('Gagal mengambil data.');
            const data = await response.json();
            setInfos(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchInfos(); }, []);

    const filteredInfos = useMemo(() => {
        return infos.filter(info =>
            info.title.toLowerCase().includes(searchTerm.toLowerCase())
        );
    }, [searchTerm, infos]);

    // --- HANDLERS FORM ---
    const handleFormChange = (e) => {
        const { name, value, files } = e.target;
        if (name === 'image') {
            setFormState(prev => ({ ...prev, [name]: files[0] }));
        } else {
            setFormState(prev => ({ ...prev, [name]: value }));
        }
    };

    const handleOpenAdd = () => {
        setFormState({ title: '', content: '', image: null });
        setShowAddModal(true);
    };

    const handleOpenEdit = (info) => {
        setEditInfo(info);
        setFormState({
            title: info.title,
            content: info.content,
            image: null // Reset file input
        });
        setShowEditModal(true);
    };

    // --- API ACTIONS ---
    const handleSubmitAdd = async (e) => {
        e.preventDefault();
        await submitData('POST', `${API_BASE_URL}/information/`, formState);
        setShowAddModal(false);
    };

    const handleSubmitEdit = async (e) => {
        e.preventDefault();
        await submitData('PUT', `${API_BASE_URL}/information/${editInfo.id}`, formState);
        setShowEditModal(false);
    };

    const submitData = async (method, url, data) => {
        try {
            const token = localStorage.getItem('authToken');
            const formData = new FormData();
            formData.append('title', data.title);
            formData.append('content', data.content);
            if (data.image) formData.append('image', data.image);

            const response = await fetch(url, {
                method: method,
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData
            });

            if (!response.ok) throw new Error('Gagal menyimpan data');
            
            await fetchInfos();
            alert(`Berhasil ${method === 'POST' ? 'menambahkan' : 'memperbarui'} informasi!`);
        } catch (err) {
            alert(err.message);
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm('Yakin hapus?')) return;
        try {
            const token = localStorage.getItem('authToken');
            await fetch(`${API_BASE_URL}/information/${id}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            await fetchInfos();
        } catch (err) {
            alert('Gagal menghapus');
        }
    };

    return (
        <Container fluid className="p-0">
            <h2 className="main-title">Kelola Informasi</h2>
            <SearchInput searchTerm={searchTerm} setSearchTerm={setSearchTerm} placeholder="Cari judul..." />

            <Button variant="primary" className="mb-3" onClick={handleOpenAdd}>
                <FaPlus className="me-2" /> Tambah Informasi
            </Button>

            {loading ? <div>Loading...</div> : (
                <Table striped bordered hover responsive>
                    <thead>
                        <tr>
                            <th style={{width:'50px'}}>#</th>
                            <th style={{width:'100px'}}>Gambar</th>
                            <th>Judul & Konten</th>
                            <th style={{width:'180px'}}>Info Tanggal</th>
                            <th style={{width:'180px'}}>Aksi</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredInfos.map((info, index) => (
                            <tr key={info.id}>
                                <td>{index + 1}</td>
                                <td>
                                    {info.image_url ? (
                                        <Image src={`http://localhost:8080${info.image_url}`} thumbnail style={{width:'80px', height:'60px', objectFit:'cover'}} />
                                    ) : '-'}
                                </td>
                                <td>
                                    <strong>{info.title}</strong><br/>
                                    <small className="text-muted">
                                        {info.content.length > 60 ? info.content.substring(0, 60) + '...' : info.content}
                                    </small>
                                </td>
                                <td style={{fontSize: '0.85rem'}}>
                                    <div><small>Dibuat: {info.created_at}</small></div>
                                    <div><small>Oleh: <strong>{info.created_by}</strong></small></div>
                                    {info.updated_at !== '-' && (
                                        <div className="mt-2 text-primary">
                                            <small>Diedit: {info.updated_at}</small><br/>
                                            <small>Oleh: <strong>{info.updated_by}</strong></small>
                                        </div>
                                    )}
                                </td>
                                <td>
                                    <Button variant="warning" size="sm" className="me-2" onClick={() => handleOpenEdit(info)}>
                                        <FaEdit /> Edit
                                    </Button>
                                    <Button variant="danger" size="sm" onClick={() => handleDelete(info.id)}>
                                        <FaTrash /> Hapus
                                    </Button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </Table>
            )}

            {/* Modal Form (Dipakai untuk Add & Edit) */}
            <Modal show={showAddModal || showEditModal} onHide={() => {setShowAddModal(false); setShowEditModal(false);}} size="lg">
                <Form onSubmit={showAddModal ? handleSubmitAdd : handleSubmitEdit}>
                    <Modal.Header closeButton>
                        <Modal.Title>{showAddModal ? 'Tambah Informasi' : 'Edit Informasi'}</Modal.Title>
                    </Modal.Header>
                    <Modal.Body>
                        <Form.Group className="mb-3">
                            <Form.Label>Judul</Form.Label>
                            <Form.Control name="title" value={formState.title} onChange={handleFormChange} required />
                        </Form.Group>
                        <Form.Group className="mb-3">
                            <Form.Label>Konten</Form.Label>
                            <Form.Control as="textarea" rows={6} name="content" value={formState.content} onChange={handleFormChange} required />
                        </Form.Group>
                        <Form.Group className="mb-3">
                            <Form.Label>{showAddModal ? 'Gambar' : 'Ganti Gambar (Opsional)'}</Form.Label>
                            <Form.Control name="image" type="file" accept="image/*" onChange={handleFormChange} />
                            {showEditModal && editInfo?.image_url && (
                                <div className="mt-2">
                                    <small>Gambar saat ini:</small><br/>
                                    <Image src={`http://localhost:8080${editInfo.image_url}`} style={{height: '50px'}} />
                                </div>
                            )}
                        </Form.Group>
                    </Modal.Body>
                    <Modal.Footer>
                        <Button variant="secondary" onClick={() => {setShowAddModal(false); setShowEditModal(false);}}>Batal</Button>
                        <Button variant="primary" type="submit">Simpan</Button>
                    </Modal.Footer>
                </Form>
            </Modal>
        </Container>
    );
});

ManageInformation.displayName = 'ManageInformation';
export default ManageInformation;