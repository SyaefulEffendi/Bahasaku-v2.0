import React, { useState, useMemo, memo, useEffect } from 'react';
import { Container, Table, Button, Form, Modal } from 'react-bootstrap';
import { FaPlus } from 'react-icons/fa';
import SearchInput from './SearchInput';

const API_BASE_URL = 'http://localhost:8080/api';

const ManageUsers = memo(({ searchTerm, setSearchTerm }) => {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showAddModal, setShowAddModal] = useState(false);
    const [showEditModal, setShowEditModal] = useState(false);
    const [editUser, setEditUser] = useState(null);

    const [formState, setFormState] = useState({
        full_name: '',
        email: '',
        password: '',
        user_type: '',
        location: '',
        birth_date: '',
        role: 'User'
    });

    // Fetch data users dari database
    // make fetchUsers callable so we can refresh after add/edit/delete
    const fetchUsers = async () => {
        try {
            setLoading(true);
            setError(null);

            // Ambil token dari localStorage (gunakan key 'authToken' dari context)
            const token = localStorage.getItem('authToken');
            
            if (!token) {
                setError('Token tidak ditemukan. Silakan login kembali.');
                setLoading(false);
                return;
            }

            const response = await fetch(`${API_BASE_URL}/users/`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                if (response.status === 401) {
                    setError('Token tidak valid atau telah kadaluarsa.');
                } else if (response.status === 403) {
                    setError('Anda tidak memiliki akses untuk melihat data user.');
                } else {
                    setError('Gagal mengambil data users dari server.');
                }
                setLoading(false);
                return;
            }

            const data = await response.json();
            // Hanya tampilkan users dengan role 'User'
            const transformedUsers = data
                .filter(user => (user.role || '').toLowerCase() === 'user')
                .map(user => ({
                    id: user.id,
                    name: user.full_name,
                    email: user.email,
                    ...user // Simpan semua field asli juga
                }));
            setUsers(transformedUsers);
        } catch (err) {
            console.error('Error fetching users:', err);
            setError(`Terjadi kesalahan: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchUsers();
    }, []);

    const filteredUsers = useMemo(() => {
        return users.filter(user =>
            user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            user.email.toLowerCase().includes(searchTerm.toLowerCase())
        );
    }, [searchTerm, users]);

    const handleDelete = async (userId) => {
        if (!window.confirm('Apakah Anda yakin ingin menghapus user ini?')) {
            return;
        }

        try {
            const token = localStorage.getItem('authToken');
            if (!token) {
                setError('Token tidak ditemukan.');
                return;
            }

            const response = await fetch(`${API_BASE_URL}/users/${userId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                setError('Gagal menghapus user.');
                return;
            }

            // Refresh data
            // Re-fetch list to be safe
            await fetchUsers();
            alert('User berhasil dihapus.');
        } catch (err) {
            console.error('Error deleting user:', err);
            setError(`Gagal menghapus user: ${err.message}`);
        }
    };

    const handleOpenAdd = () => {
        setFormState({ full_name: '', email: '', password: '', user_type: '', location: '', birth_date: '', role: 'User' });
        setShowAddModal(true);
    };

    const handleOpenEdit = (user) => {
        setEditUser(user);
        setFormState({
            full_name: user.full_name || user.name || '',
            email: user.email || '',
            password: '',
            user_type: user.user_type || '',
            location: user.location || '',
            birth_date: user.birth_date || '',
            role: user.role || 'User'
        });
        setShowEditModal(true);
    };

    const handleFormChange = (e) => {
        const { name, value } = e.target;
        setFormState(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmitAdd = async (e) => {
        e.preventDefault();
        try {
            const token = localStorage.getItem('authToken');

            const payload = {
                full_name: formState.full_name,
                email: formState.email,
                password: formState.password,
                user_type: formState.user_type,
                location: formState.location,
                birth_date: formState.birth_date
            };

            const response = await fetch(`${API_BASE_URL}/users/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': token ? `Bearer ${token}` : undefined
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const err = await response.json();
                setError(err.error || 'Gagal menambah user');
                return;
            }

            const data = await response.json();

            setShowAddModal(false);
            await fetchUsers();
            alert('User berhasil ditambahkan');
        } catch (err) {
            console.error('Error adding user:', err);
            setError(err.message || 'Gagal menambah user');
        }
    };

    const handleSubmitEdit = async (e) => {
        e.preventDefault();
        if (!editUser) return;
        try {
            const token = localStorage.getItem('authToken');
            if (!token) {
                setError('Token tidak ditemukan. Silakan login kembali.');
                return;
            }

            const payload = {
                full_name: formState.full_name,
                email: formState.email,
                user_type: formState.user_type,
                location: formState.location,
                birth_date: formState.birth_date
            };
            // Only include password if provided
            if (formState.password) payload.password = formState.password;
            // Admin may set role
            if (formState.role) payload.role = formState.role;

            const response = await fetch(`${API_BASE_URL}/users/${editUser.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const err = await response.json();
                setError(err.error || 'Gagal memperbarui user');
                return;
            }

            setShowEditModal(false);
            setEditUser(null);
            await fetchUsers();
            alert('User berhasil diperbarui');
        } catch (err) {
            console.error('Error updating user:', err);
            setError(err.message || 'Gagal memperbarui user');
        }
    };

    return (
        <Container fluid className="p-0">
            <h2 className="main-title">Kelola Data User</h2>
            <SearchInput searchTerm={searchTerm} setSearchTerm={setSearchTerm} placeholder="Cari user..." />
            
            {error && (
                <div className="alert alert-danger alert-dismissible fade show" role="alert">
                    {error}
                    <button type="button" className="btn-close" onClick={() => setError(null)}></button>
                </div>
            )}

            {loading ? (
                <div className="alert alert-info">Memuat data users...</div>
            ) : filteredUsers.length === 0 ? (
                <div className="alert alert-warning">Tidak ada data users ditemukan.</div>
            ) : (
                <Table key="users-table" striped bordered hover responsive>
                    <thead>
                        <tr><th>#</th><th>Nama</th><th>Email</th><th>Tipe User</th><th>Aksi</th></tr>
                    </thead>
                    <tbody>
                        {filteredUsers.map((user, index) => (
                            <tr key={user.id}>
                                <td>{index + 1}</td>
                                <td>{user.name}</td>
                                <td>{user.email}</td>
                                <td>{user.user_type || '-'}</td>
                                <td>
                                    <Button variant="warning" size="sm" className="me-2" onClick={() => handleOpenEdit(user)}>Edit</Button>
                                    <Button 
                                        variant="danger" 
                                        size="sm"
                                        onClick={() => handleDelete(user.id)}
                                    >
                                        Hapus
                                    </Button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </Table>
            )}
            <Button variant="primary" className="mt-3" onClick={handleOpenAdd}><FaPlus className="me-2" /> Tambah User</Button>

            {/* Add User Modal */}
            <Modal show={showAddModal} onHide={() => setShowAddModal(false)}>
                <Form onSubmit={handleSubmitAdd}>
                    <Modal.Header closeButton><Modal.Title>Tambah User</Modal.Title></Modal.Header>
                    <Modal.Body>
                        <Form.Group className="mb-2">
                            <Form.Label>Nama Lengkap</Form.Label>
                            <Form.Control name="full_name" value={formState.full_name} onChange={handleFormChange} required />
                        </Form.Group>
                        <Form.Group className="mb-2">
                            <Form.Label>Email</Form.Label>
                            <Form.Control name="email" type="email" value={formState.email} onChange={handleFormChange} required />
                        </Form.Group>
                        <Form.Group className="mb-2">
                            <Form.Label>Password</Form.Label>
                            <Form.Control name="password" type="password" value={formState.password} onChange={handleFormChange} required />
                        </Form.Group>
                        <Form.Group className="mb-2">
                            <Form.Label>Tipe User</Form.Label>
                            <Form.Select name="user_type" value={formState.user_type} onChange={handleFormChange} required>
                                <option value="">Pilih tipe</option>
                                <option value="Tuli">Tuli</option>
                                <option value="Dengar">Dengar</option>
                                <option value="Umum">Umum</option>
                            </Form.Select>
                        </Form.Group>
                        <Form.Group className="mb-2">
                            <Form.Label>Lokasi</Form.Label>
                            <Form.Control name="location" value={formState.location} onChange={handleFormChange} />
                        </Form.Group>
                        <Form.Group className="mb-2">
                            <Form.Label>Tanggal Lahir</Form.Label>
                            <Form.Control name="birth_date" type="date" value={formState.birth_date || ''} onChange={handleFormChange} />
                        </Form.Group>
                        {/* Role dihilangkan saat tambah — akan otomatis 'User' di backend */}
                    </Modal.Body>
                    <Modal.Footer>
                        <Button variant="secondary" onClick={() => setShowAddModal(false)}>Batal</Button>
                        <Button variant="primary" type="submit">Tambah</Button>
                    </Modal.Footer>
                </Form>
            </Modal>

            {/* Edit User Modal */}
            <Modal show={showEditModal} onHide={() => setShowEditModal(false)}>
                <Form onSubmit={handleSubmitEdit}>
                    <Modal.Header closeButton><Modal.Title>Edit User</Modal.Title></Modal.Header>
                    <Modal.Body>
                        <Form.Group className="mb-2">
                            <Form.Label>Nama Lengkap</Form.Label>
                            <Form.Control name="full_name" value={formState.full_name} onChange={handleFormChange} required />
                        </Form.Group>
                        <Form.Group className="mb-2">
                            <Form.Label>Email</Form.Label>
                            <Form.Control name="email" type="email" value={formState.email} onChange={handleFormChange} required />
                        </Form.Group>
                        <Form.Group className="mb-2">
                            <Form.Label>Password (kosongkan jika tidak ingin mengganti)</Form.Label>
                            <Form.Control name="password" type="password" value={formState.password} onChange={handleFormChange} />
                        </Form.Group>
                        <Form.Group className="mb-2">
                            <Form.Label>Tipe User</Form.Label>
                            <Form.Select name="user_type" value={formState.user_type} onChange={handleFormChange}>
                                <option value="">Pilih tipe</option>
                                <option value="Tuli">Tuli</option>
                                <option value="Dengar">Dengar</option>
                                <option value="Umum">Umum</option>
                            </Form.Select>
                        </Form.Group>
                        <Form.Group className="mb-2">
                            <Form.Label>Lokasi</Form.Label>
                            <Form.Control name="location" value={formState.location} onChange={handleFormChange} />
                        </Form.Group>
                        <Form.Group className="mb-2">
                            <Form.Label>Tanggal Lahir</Form.Label>
                            <Form.Control name="birth_date" type="date" value={formState.birth_date || ''} onChange={handleFormChange} />
                        </Form.Group>
                        <Form.Group className="mb-2">
                            <Form.Label>Role</Form.Label>
                            <Form.Select name="role" value={formState.role} onChange={handleFormChange}>
                                <option value="User">User</option>
                                <option value="Admin">Admin</option>
                            </Form.Select>
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

ManageUsers.displayName = 'ManageUsers';

export default ManageUsers;
