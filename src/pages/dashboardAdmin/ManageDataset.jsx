import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Row, Col, Card, Button, Form, Badge, ProgressBar, ButtonGroup, Alert, Spinner } from 'react-bootstrap';
import { FaVideo, FaStop, FaFont, FaHandPaper, FaBrain, FaCamera } from 'react-icons/fa';
import Webcam from 'react-webcam';
import axios from 'axios';
import API_BASE_URL from '../../config/apiConfig';
import { Holistic, HAND_CONNECTIONS, POSE_CONNECTIONS } from '@mediapipe/holistic';
import { drawConnectors, drawLandmarks as mpDrawLandmarks } from '@mediapipe/drawing_utils';
import Swal from 'sweetalert2';
const FRAME_PER_VIDEO = 30;

const ManageDataset = () => {
    const [mode, setMode] = useState('kata'); // 'kata' atau 'huruf'
    const [tab, setTab] = useState('record'); // 'record' atau 'train'
    const [label, setLabel] = useState('');
    
    // --- State Kamera ---
    const [isCameraOpen, setIsCameraOpen] = useState(false);
    const [isCamReady, setIsCamReady] = useState(false);
    const [camError, setCamError] = useState('');
    
    // --- State Recording ---
    const [isCapturing, setIsCapturing] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const [bufferCount, setBufferCount] = useState(0);
    const [stats, setStats] = useState({ kata: {}, huruf: {} });
    const [message, setMessage] = useState(null); // { type: 'success'|'danger', text: '' }

    // --- State Training ---
    const [isTraining, setIsTraining] = useState(false);
    const [trainLog, setTrainLog] = useState('');

    const webcamRef = useRef(null);
    const canvasRef = useRef(null);
    const holisticRef = useRef(null);
    const animFrameRef = useRef(null);
    
    const kataFramesRef = useRef([]); 
    const isSendingBatchRef = useRef(false);
    const handDetectedRef = useRef(false);
    const intervalRef = useRef(null);

    // Ambil Statistik
    const fetchStats = async () => {
        try {
            const { data } = await axios.get(`${API_BASE_URL}/dataset/stats`);
            setStats(data);
        } catch (err) {
            console.error('Error fetching stats:', err);
        }
    };

    useEffect(() => {
        fetchStats();
    }, [tab]);

    // Cleanup camera
    useEffect(() => {
        return () => stopCamera();
    }, []);

    // Setup Holistic
    const onHolisticResults = useCallback((results) => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const w = results.image.width;
        const h = results.image.height;
        canvas.width = w;
        canvas.height = h;
        ctx.clearRect(0, 0, w, h);

        const adaTangan = !!(results.rightHandLandmarks || results.leftHandLandmarks);
        handDetectedRef.current = adaTangan;

        if (results.poseLandmarks) {
            drawConnectors(ctx, results.poseLandmarks, POSE_CONNECTIONS, { color: 'rgba(0, 255, 255, 0.3)', lineWidth: 1 });
        }
        if (results.rightHandLandmarks) {
            drawConnectors(ctx, results.rightHandLandmarks, HAND_CONNECTIONS, { color: '#00DC64', lineWidth: 2 });
            mpDrawLandmarks(ctx, results.rightHandLandmarks, { color: '#FF6600', lineWidth: 1, radius: 3 });
        }
        if (results.leftHandLandmarks) {
            drawConnectors(ctx, results.leftHandLandmarks, HAND_CONNECTIONS, { color: '#0096FF', lineWidth: 2 });
            mpDrawLandmarks(ctx, results.leftHandLandmarks, { color: '#FF6600', lineWidth: 1, radius: 3 });
        }
    }, []);

    useEffect(() => {
        if (!isCameraOpen || !isCamReady) return;

        const holistic = new Holistic({
            locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/holistic/${file}`,
        });
        holistic.setOptions({
            modelComplexity: 1, smoothLandmarks: true, minDetectionConfidence: 0.5, minTrackingConfidence: 0.5,
        });
        holistic.onResults(onHolisticResults);
        holisticRef.current = holistic;

        let running = true;
        const processLoop = async () => {
            if (!running) return;
            const video = webcamRef.current?.video;
            if (video && video.readyState >= 2 && holisticRef.current) {
                try {
                    await holisticRef.current.send({ image: video });
                } catch (e) {}
            }
            if (running) {
                animFrameRef.current = requestAnimationFrame(processLoop);
            }
        };
        processLoop();

        return () => {
            running = false;
            cancelAnimationFrame(animFrameRef.current);
            holistic.close();
            holisticRef.current = null;
        };
    }, [isCameraOpen, isCamReady, onHolisticResults]);

    const startCamera = () => {
        setIsCameraOpen(true);
        setIsCamReady(false);
        setCamError('');
        setMessage(null);
    };

    const stopCamera = () => {
        setIsCameraOpen(false);
        setIsCamReady(false);
        setIsCapturing(false);
        clearInterval(intervalRef.current);
        cancelAnimationFrame(animFrameRef.current);
    };

    // --- REKAM KATA ---
    const captureKataFrame = useCallback(() => {
        if (!webcamRef.current || !isCamReady || isSendingBatchRef.current) return;
        if (kataFramesRef.current.length >= FRAME_PER_VIDEO) return;
        if (!handDetectedRef.current) return; // Hanya ambil kalau ada tangan

        const canvas = webcamRef.current.getCanvas();
        if (!canvas) return;

        canvas.toBlob((blob) => {
            if (!blob) return;
            if (isSendingBatchRef.current) return; // Mencegah request tumpang tindih
            
            kataFramesRef.current.push(blob);
            setBufferCount(kataFramesRef.current.length);

            if (kataFramesRef.current.length === FRAME_PER_VIDEO) {
                sendKataBatch();
            }
        }, 'image/jpeg', 0.8);
    }, [isCamReady]);

    const sendKataBatch = async () => {
        isSendingBatchRef.current = true;
        setIsCapturing(false);
        setIsProcessing(true);

        try {
            const formData = new FormData();
            formData.append('label', label);
            kataFramesRef.current.forEach((blob, i) => {
                formData.append('frames', blob, `frame_${i}.jpg`);
            });

            const { data } = await axios.post(`${API_BASE_URL}/dataset/record/kata`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setMessage({ type: 'success', text: `✅ Berhasil menyimpan 1 video untuk kata '${data.label}'. (Total: ${data.total_video_tersimpan})` });
            fetchStats();
        } catch (err) {
            setMessage({ type: 'danger', text: err.response?.data?.error || 'Gagal menyimpan dataset kata.' });
        } finally {
            setIsProcessing(false);
            kataFramesRef.current = [];
            setBufferCount(0);
            isSendingBatchRef.current = false;
        }
    };

    // --- REKAM HURUF ---
    const captureHuruf = async () => {
        if (!webcamRef.current || !isCamReady || isProcessing) return;
        if (!handDetectedRef.current) {
            setMessage({ type: 'warning', text: '⚠️ Tidak ada tangan terdeteksi!' });
            return;
        }

        const canvas = webcamRef.current.getCanvas();
        if (!canvas) return;

        setIsProcessing(true);
        canvas.toBlob(async (blob) => {
            if (!blob) { setIsProcessing(false); return; }

            try {
                const formData = new FormData();
                formData.append('label', label);
                formData.append('image', blob, 'huruf.jpg');

                const { data } = await axios.post(`${API_BASE_URL}/dataset/record/huruf`, formData, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                });
                setMessage({ type: 'success', text: `✅ Berhasil menyimpan 1 sampel huruf '${data.label}'. (Total: ${data.total_sample_tersimpan})` });
                fetchStats();
            } catch (err) {
                setMessage({ type: 'danger', text: err.response?.data?.error || 'Gagal menyimpan dataset huruf.' });
            } finally {
                setIsProcessing(false);
            }
        }, 'image/jpeg', 0.8);
    };

    // Toggle Capture mode kata
    useEffect(() => {
        clearInterval(intervalRef.current);
        if (mode === 'kata' && isCapturing && isCameraOpen && isCamReady) {
            intervalRef.current = setInterval(captureKataFrame, 33);
        }
        return () => clearInterval(intervalRef.current);
    }, [isCapturing, mode, isCameraOpen, isCamReady, captureKataFrame]);

    const handleStartRecord = () => {
        if (!label.trim()) {
            setMessage({ type: 'danger', text: 'Silakan isi Label sasaran terlebih dahulu!' });
            return;
        }
        if (mode === 'kata') {
            setIsCapturing(true);
            setMessage(null);
        } else {
            captureHuruf();
        }
    };

    // --- TRAIN MODEL ---
    const handleTrain = async (tipe) => {
        const result = await Swal.fire({
            title: 'Konfirmasi',
            text: `Yakin ingin melakukan training ulang untuk model ${tipe.toUpperCase()}? Proses ini bisa memakan waktu beberapa menit.`,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'OK',
            cancelButtonText: 'Cancel'
        });
        if (!result.isConfirmed) return;

        setIsTraining(true);
        setTrainLog('Memulai proses training... Mohon tunggu, proses ini akan berjalan di latar belakang.\n');
        setMessage(null);

        try {
            const { data } = await axios.post(`${API_BASE_URL}/dataset/train/${tipe}`);
            setTrainLog(prev => prev + `\n✅ SELESAI!\n\nOutput Log:\n${data.log}`);
            setMessage({ type: 'success', text: `Training model ${tipe.toUpperCase()} berhasil!` });
        } catch (err) {
            const errLog = err.response?.data?.log || err.message;
            setTrainLog(prev => prev + `\n❌ GAGAL!\n\nOutput Log:\n${errLog}`);
            setMessage({ type: 'danger', text: `Training model ${tipe.toUpperCase()} gagal!` });
        } finally {
            setIsTraining(false);
        }
    };

    return (
        <div>
            <div className="d-flex align-items-center justify-content-between mb-4">
                <h4 className="fw-bold mb-0 text-primary"><FaBrain className="me-2"/> Kelola Dataset & AI</h4>
                <ButtonGroup>
                    <Button variant={tab === 'record' ? 'primary' : 'outline-primary'} onClick={() => setTab('record')}>
                        <FaCamera className="me-1" /> Rekam Dataset
                    </Button>
                    <Button variant={tab === 'train' ? 'primary' : 'outline-primary'} onClick={() => setTab('train')}>
                        <FaBrain className="me-1" /> Training Model
                    </Button>
                </ButtonGroup>
            </div>

            {message && <Alert variant={message.type} onClose={() => setMessage(null)} dismissible>{message.text}</Alert>}

            {tab === 'record' && (
                <Row>
                    <Col lg={7}>
                        <Card className="shadow-sm border-0 mb-4">
                            <Card.Body>
                                <div className="d-flex justify-content-between align-items-center mb-3">
                                    <h5 className="mb-0 fw-bold">Live Kamera</h5>
                                    <ButtonGroup size="sm">
                                        <Button variant={mode === 'kata' ? 'primary' : 'outline-primary'} onClick={() => { setMode('kata'); setIsCapturing(false); }}>
                                            <FaHandPaper className="me-1"/> Kata
                                        </Button>
                                        <Button variant={mode === 'huruf' ? 'primary' : 'outline-primary'} onClick={() => { setMode('huruf'); setIsCapturing(false); }}>
                                            <FaFont className="me-1"/> Huruf
                                        </Button>
                                    </ButtonGroup>
                                </div>

                                <div className="video-wrapper border rounded bg-dark position-relative overflow-hidden d-flex justify-content-center align-items-center" style={{ minHeight: '360px' }}>
                                    {isCameraOpen ? (
                                        <>
                                            <Webcam
                                                audio={false}
                                                ref={webcamRef}
                                                videoConstraints={{ width: 640, height: 480, facingMode: 'user' }}
                                                mirrored={true}
                                                width="100%"
                                                className="rounded"
                                                onUserMedia={() => setIsCamReady(true)}
                                            />
                                            <canvas
                                                ref={canvasRef}
                                                className="position-absolute top-0 start-0 w-100 h-100"
                                                style={{ pointerEvents: 'none', transform: 'scaleX(-1)' }}
                                            />
                                            {isProcessing && (
                                                <div className="position-absolute d-flex flex-column align-items-center justify-content-center w-100 h-100" style={{backgroundColor: 'rgba(0,0,0,0.6)', zIndex: 10}}>
                                                    <Spinner animation="border" variant="light" />
                                                    <span className="text-white mt-2">Menyimpan Dataset...</span>
                                                </div>
                                            )}
                                        </>
                                    ) : (
                                        <div className="text-center text-muted p-4">
                                            <FaVideo size={40} className="mb-2"/>
                                            <p>Kamera Nonaktif</p>
                                        </div>
                                    )}
                                </div>
                                {mode === 'kata' && isCameraOpen && isCamReady && (
                                    <ProgressBar now={(bufferCount/FRAME_PER_VIDEO)*100} className="mt-3" style={{height: '10px'}}/>
                                )}
                            </Card.Body>
                            <Card.Footer className="bg-white border-top-0 d-flex gap-2">
                                <Button variant={isCameraOpen ? 'danger' : 'success'} onClick={isCameraOpen ? stopCamera : startCamera} className="flex-grow-1">
                                    {isCameraOpen ? <><FaStop className="me-2"/> Matikan Kamera</> : <><FaVideo className="me-2"/> Mulai Kamera</>}
                                </Button>
                            </Card.Footer>
                        </Card>
                    </Col>
                    
                    <Col lg={5}>
                        <Card className="shadow-sm border-0 mb-4 bg-primary text-white">
                            <Card.Body>
                                <h5 className="fw-bold mb-3">Target Rekaman ({mode.toUpperCase()})</h5>
                                <Form.Group className="mb-3">
                                    <Form.Label>Label Sasaran</Form.Label>
                                    <Form.Control 
                                        type="text" 
                                        placeholder={mode === 'kata' ? "Contoh: tolong" : "Contoh: A"}
                                        value={label}
                                        onChange={(e) => setLabel(e.target.value)}
                                        size="lg"
                                        className="fw-bold text-center"
                                    />
                                </Form.Group>
                                
                                {isCameraOpen && isCamReady && (
                                    mode === 'kata' ? (
                                        <Button 
                                            variant="light" size="lg" className="w-100 fw-bold text-primary"
                                            onClick={handleStartRecord}
                                            disabled={isCapturing || isProcessing}
                                        >
                                            {isCapturing ? 'Merekam Video...' : 'Mulai Rekam 1 Video (30 Frame)'}
                                        </Button>
                                    ) : (
                                        <Button 
                                            variant="light" size="lg" className="w-100 fw-bold text-primary"
                                            onClick={handleStartRecord}
                                            disabled={isProcessing}
                                        >
                                            Simpan 1 Sampel (Frame Saat Ini)
                                        </Button>
                                    )
                                )}
                            </Card.Body>
                        </Card>
                        
                        <Card className="shadow-sm border-0">
                            <Card.Header className="bg-white fw-bold">Data Tersimpan: {label ? label.toUpperCase() : '-'}</Card.Header>
                            <Card.Body>
                                <h1 className="display-4 text-center text-primary fw-bold">
                                    {label ? (stats[mode][mode === 'kata' ? label.toLowerCase() : label.toUpperCase()] || 0) : 0}
                                </h1>
                                <p className="text-center text-muted">{mode === 'kata' ? 'Video' : 'Sampel/Frame'}</p>
                            </Card.Body>
                        </Card>
                    </Col>
                </Row>
            )}

            {tab === 'train' && (
                <Row>
                    <Col md={12}>
                        <Card className="shadow-sm border-0 mb-4">
                            <Card.Body>
                                <h5 className="fw-bold mb-4">Training Model Machine Learning</h5>
                                <Row>
                                    <Col md={6}>
                                        <div className="p-4 bg-light rounded text-center border h-100">
                                            <FaHandPaper size={40} className="text-primary mb-3"/>
                                            <h6 className="fw-bold">Model Kata (Bi-LSTM)</h6>
                                            <p className="small text-muted mb-4">
                                                Total Kelas: {Object.keys(stats.kata || {}).length} Kata<br/>
                                                Total Video: {Object.values(stats.kata || {}).reduce((a,b) => a+b, 0)}
                                            </p>
                                            <Button variant="primary" disabled={isTraining} onClick={() => handleTrain('kata')} className="w-100 fw-bold">
                                                Mulai Training Kata
                                            </Button>
                                        </div>
                                    </Col>
                                    <Col md={6}>
                                        <div className="p-4 bg-light rounded text-center border h-100">
                                            <FaFont size={40} className="text-success mb-3"/>
                                            <h6 className="fw-bold">Model Huruf (Dense)</h6>
                                            <p className="small text-muted mb-4">
                                                Total Kelas: {Object.keys(stats.huruf || {}).length} Huruf<br/>
                                                Total Sampel: {Object.values(stats.huruf || {}).reduce((a,b) => a+b, 0)}
                                            </p>
                                            <Button variant="success" disabled={isTraining} onClick={() => handleTrain('huruf')} className="w-100 fw-bold">
                                                Mulai Training Huruf
                                            </Button>
                                        </div>
                                    </Col>
                                </Row>

                                {(isTraining || trainLog) && (
                                    <div className="mt-4">
                                        <h6 className="fw-bold">Log Training:</h6>
                                        <pre className="bg-dark text-light p-3 rounded" style={{maxHeight: '400px', overflowY: 'auto', fontSize: '13px'}}>
                                            {trainLog}
                                            {isTraining && <span className="text-warning">  █</span>}
                                        </pre>
                                    </div>
                                )}
                            </Card.Body>
                        </Card>
                    </Col>
                </Row>
            )}

        </div>
    );
};

export default ManageDataset;
