import React, { memo } from 'react';
import { Container, Row, Col, Card } from 'react-bootstrap';
import { FaUsers, FaEnvelope, FaBookOpen, FaUser } from 'react-icons/fa';

const DashboardSummary = memo(({ 
    usersCount = 0, 
    vocabCount = 0, 
    feedbackCount = 0, 
    adminsCount = 0,
    recentFeedbacks = [] 
}) => (
    <Container fluid className="p-0">
        <h1 className="main-title">Dashboard</h1>
        <Row className="mb-4">
            {/* Kartu Total Pengguna */}
            <Col md={6} lg={3} className="mb-4">
                <Card className="summary-card text-white bg-success">
                    <Card.Body>
                        <FaUsers size={30} className="card-icon" />
                        <h5 className="mb-0">Total Pengguna</h5>
                        <h2 className="card-text">{usersCount}</h2>
                    </Card.Body>
                </Card>
            </Col>
            {/* Kartu Total Kosakata */}
            <Col md={6} lg={3} className="mb-4">
                <Card className="summary-card text-white bg-warning">
                    <Card.Body>
                        <FaBookOpen size={30} className="card-icon" />
                        <h5 className="mb-0">Total Kosakata</h5>
                        <h2 className="card-text">{vocabCount}</h2>
                    </Card.Body>
                </Card>
            </Col>
            {/* Kartu Total Umpan Balik */}
            <Col md={6} lg={3} className="mb-4">
                <Card className="summary-card text-white bg-danger">
                    <Card.Body>
                        <FaEnvelope size={30} className="card-icon" />
                        <h5 className="mb-0">Umpan Balik</h5>
                        <h2 className="card-text">{feedbackCount}</h2>
                    </Card.Body>
                </Card>
            </Col>
            {/* Kartu Total Admin */}
            <Col md={6} lg={3} className="mb-4">
                <Card className="summary-card text-white bg-primary">
                    <Card.Body>
                        <FaUser size={30} className="card-icon" />
                        <h5 className="mb-0">Total Admin</h5>
                        <h2 className="card-text">{adminsCount}</h2>
                    </Card.Body>
                </Card>
            </Col>
        </Row>
        
        {/* Bagian Aktivitas Terkini (Mengambil data 5 Feedback Terbaru) */}
        <Row>
            <Col md={12} className="mb-4">
                <Card className="stisla-card">
                    <Card.Body>
                        <Card.Title>Aktivitas Terkini (Feedback Terbaru)</Card.Title>
                        {recentFeedbacks.length > 0 ? (
                            <ul className="list-unstyled">
                                {recentFeedbacks.map((item, index) => (
                                    <li key={item.id || index} className="mb-3 border-bottom pb-2">
                                        <div className="d-flex align-items-center">
                                            {/* Avatar sederhana */}
                                            <div className="user-avatar me-3 d-flex align-items-center justify-content-center text-white bg-secondary" style={{ fontSize: '1.2rem' }}>
                                                {item.user && item.user.full_name ? item.user.full_name.charAt(0).toUpperCase() : '?'}
                                            </div>
                                            <div>
                                                <h6 className="mb-0">
                                                    {item.user ? item.user.full_name : 'Pengguna Tidak Dikenal'}
                                                    <span className="text-muted ms-2" style={{fontSize: '0.8rem', fontWeight: 'normal'}}>
                                                        - {item.status || 'Baru'}
                                                    </span>
                                                </h6>
                                                <p className="text-muted mb-0 text-truncate" style={{maxWidth: '600px'}}>
                                                    {item.message}
                                                </p>
                                                <small className="text-muted">
                                                    {item.created_at ? new Date(item.created_at).toLocaleDateString() : ''}
                                                </small>
                                            </div>
                                        </div>
                                    </li>
                                ))}
                            </ul>
                        ) : (
                            <p className="text-muted">Belum ada aktivitas terbaru.</p>
                        )}
                    </Card.Body>
                </Card>
            </Col>
        </Row>
    </Container>
));

DashboardSummary.displayName = 'DashboardSummary';

export default DashboardSummary;