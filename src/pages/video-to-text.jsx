import React, { useState, useRef, useEffect, useCallback } from 'react';
import Navbar from '../components/navbar';
import Footer from '../components/footer';
import { Container, Row, Col, Card, Button, Badge } from 'react-bootstrap';
import { FaVideo, FaStop } from 'react-icons/fa';
import Webcam from 'react-webcam';
import axios from 'axios';
import './css/video-to-text.css';

function VideoToText() {
    const [isCameraOpen, setIsCameraOpen] = useState(false);
    const [translation, setTranslation] = useState('');
    const [dbResult, setDbResult] = useState(null); 
    const [isProcessing, setIsProcessing] = useState(false);
    
    const webcamRef = useRef(null);

    const videoConstraints = {
        width: 640,
        height: 480,
        facingMode: "user"
    };

    const dataURItoBlob = (dataURI) => {
        const byteString = atob(dataURI.split(',')[1]);
        const mimeString = dataURI.split(',')[0].split(':')[1].split(';')[0];
        const ab = new ArrayBuffer(byteString.length);
        const ia = new Uint8Array(ab);
        for (let i = 0; i < byteString.length; i++) {
            ia[i] = byteString.charCodeAt(i);
        }
        return new Blob([ab], { type: mimeString });
    };

    const captureAndPredict = useCallback(async () => {
        if (!webcamRef.current || isProcessing) return;

        const imageSrc = webcamRef.current.getScreenshot();
        if (!imageSrc) return;

        try {
            setIsProcessing(true);
            const blob = dataURItoBlob(imageSrc);
            const formData = new FormData();
            formData.append('image', blob, 'capture.jpg');

            // Ganti port 8080 sesuai konfigurasi docker-compose Anda
            const response = await axios.post('http://localhost:8080/api/ai/predict', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });

            const { text, found_in_db, db_detail } = response.data;

            if (text) {
                setTranslation(text);
                if (found_in_db && db_detail) {
                    setDbResult(db_detail);
                }
            } 
            
        } catch (error) {
            console.error("Error predicting sign:", error);
        } finally {
            setIsProcessing(false);
        }
    }, [webcamRef, isProcessing]);

    useEffect(() => {
        let intervalId;
        if (isCameraOpen) {
            intervalId = setInterval(() => {
                captureAndPredict();
            }, 500); // Interval prediksi (ms)
        }
        return () => clearInterval(intervalId);
    }, [isCameraOpen, captureAndPredict]);

    const toggleCamera = () => {
        if (isCameraOpen) {
            setIsCameraOpen(false);
            setTranslation('');
            setDbResult(null);
        } else {
            setIsCameraOpen(true);
        }
    };

    return (
        <div className="d-flex flex-column min-vh-100">
            <title>Video to Text - Bahasaku</title>
            <Navbar />
            <main className="video-to-text-main flex-grow-1">
                <Container className="my-4"> {/* Margin top/bottom sedikit dikurangi agar muat */}
                    <Card className="shadow-sm">
                        <Card.Header className="text-center bg-primary text-white">
                            <h4 className="my-1">Penerjemah Bahasa Isyarat (AI)</h4>
                        </Card.Header>
                        <Card.Body className="p-4">
                            
                            {/* LAYOUT SPLIT: Kiri Kamera, Kanan Hasil */}
                            <Row className="g-4"> 
                                {/* KOLOM KIRI: KAMERA & KONTROL */}
                                <Col lg={7} md={12}>
                                    <div className="video-wrapper border rounded bg-light d-flex align-items-center justify-content-center position-relative" style={{ minHeight: '360px' }}>
                                        {isCameraOpen ? (
                                            <>
                                                <Webcam
                                                    audio={false}
                                                    ref={webcamRef}
                                                    screenshotFormat="image/jpeg"
                                                    videoConstraints={videoConstraints}
                                                    width="100%"
                                                    className="rounded"
                                                />
                                                {isProcessing && (
                                                    <Badge bg="warning" text="dark" className="position-absolute top-0 end-0 m-2">
                                                        Mendeteksi...
                                                    </Badge>
                                                )}
                                            </>
                                        ) : (
                                            <div className="text-center text-muted p-5">
                                                <FaVideo size={60} className="mb-3" />
                                                <h5>Kamera Nonaktif</h5>
                                                <p>Klik tombol "Mulai Kamera" di bawah.</p>
                                            </div>
                                        )}
                                    </div>

                                    {/* Tombol Kontrol langsung di bawah video */}
                                    <div className="d-grid gap-2 mt-3">
                                        <Button 
                                            variant={isCameraOpen ? "danger" : "primary"} 
                                            onClick={toggleCamera}
                                            size="lg"
                                        >
                                            {isCameraOpen ? (
                                                <><FaStop className="me-2" /> Stop Kamera</>
                                            ) : (
                                                <><FaVideo className="me-2" /> Mulai Kamera</>
                                            )}
                                        </Button>
                                    </div>
                                </Col>

                                {/* KOLOM KANAN: HASIL TERJEMAHAN */}
                                <Col lg={5} md={12}>
                                    <div className="h-100 d-flex flex-column">
                                        <div className="flex-grow-1 d-flex flex-column justify-content-center">
                                            <h5 className="text-center text-primary mb-3">Hasil Terjemahan:</h5>
                                            
                                            <Card className="text-center p-5 shadow-sm h-100 justify-content-center" style={{ border: '2px dashed #0d6efd', backgroundColor: '#f0f8ff' }}>
                                                <div>
                                                    <h1 className="display-1 fw-bold mb-0 text-dark">
                                                        {translation || "-"}
                                                    </h1>
                                                    <p className="text-muted mt-3 mb-0">
                                                        {translation ? "Gerakan terdeteksi" : "Menunggu gerakan..."}
                                                    </p>
                                                </div>
                                            </Card>
                                        </div>
                                    </div>
                                </Col>
                            </Row>
                        </Card.Body>
                    </Card>
                </Container>
            </main>
            <Footer />
        </div>
    );
}

export default VideoToText;