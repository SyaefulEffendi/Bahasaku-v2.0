import React, { useState, useRef, useEffect, useCallback } from 'react';
import Navbar from '../components/navbar';
import Footer from '../components/footer';
import { Container, Row, Col, Card, Button, Badge, ProgressBar, ButtonGroup } from 'react-bootstrap';
import { FaVideo, FaStop, FaFont, FaHandPaper, FaRedo } from 'react-icons/fa';
import Webcam from 'react-webcam';
import axios from 'axios';
import './css/video-to-text.css';
import API_BASE_URL from '../config/apiConfig';
import { Holistic, HAND_CONNECTIONS, POSE_CONNECTIONS } from '@mediapipe/holistic';
import { drawConnectors, drawLandmarks as mpDrawLandmarks } from '@mediapipe/drawing_utils';

// ID unik per tab browser
const SESSION_ID = (() => {
    try { return crypto.randomUUID(); }
    catch (_) { return Math.random().toString(36).slice(2); }
})();

const INTERVAL_HURUF  = 150;   // prediksi server tiap 150ms
const INTERVAL_KATA   = 33;    // ~30fps capture lokal
const FRAME_PER_VIDEO = 30;

function VideoToText() {
    const [isCameraOpen, setIsCameraOpen] = useState(false);
    const [isCamReady, setIsCamReady]     = useState(false);
    const [mode, setMode]                 = useState('huruf');
    const [translation, setTranslation]   = useState('');
    const [kalimat, setKalimat]           = useState([]);
    const [confidence, setConfidence]     = useState(0);
    const [dbResult, setDbResult]         = useState(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [bufferCount, setBufferCount]   = useState(0);
    const [isCapturing, setIsCapturing]   = useState(false);
    const [camError, setCamError]         = useState('');
    const [detectionStatus, setDetectionStatus] = useState({
        right_hand: false,
        left_hand: false,
        overlapping: false,
        pose: false,
    });

    const webcamRef          = useRef(null);
    const canvasRef          = useRef(null);
    const intervalRef        = useRef(null);
    const modeRef            = useRef(mode);
    const isCapturingRef     = useRef(isCapturing);
    const isProcessingRef    = useRef(false);
    const isCamReadyRef      = useRef(false);
    const holisticRef        = useRef(null);
    const animFrameRef       = useRef(null);

    // ── Refs untuk batch kata ─────────────────────────────────────────────────
    const kataFramesRef      = useRef([]);    // buffer lokal: array of Blob
    const isSendingBatchRef  = useRef(false); // cegah double-send
    const handDetectedRef    = useRef(false); // Deteksi ada tangan atau tidak

    useEffect(() => { modeRef.current = mode; }, [mode]);
    useEffect(() => {
        isCapturingRef.current = isCapturing;
    }, [isCapturing]);

    const videoConstraints = { width: 640, height: 480, facingMode: 'user' };

    // ── Client-side MediaPipe: gambar landmark real-time di canvas ──────────
    const onHolisticResults = useCallback((results) => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const w = results.image.width;
        const h = results.image.height;
        canvas.width  = w;
        canvas.height = h;
        ctx.clearRect(0, 0, w, h);

        // Deteksi apakah ada tangan (seperti 'ada_sesuatu' di Python)
        const adaTangan = !!(results.rightHandLandmarks || results.leftHandLandmarks);
        handDetectedRef.current = adaTangan;

        // Pose
        if (results.poseLandmarks) {
            drawConnectors(ctx, results.poseLandmarks, POSE_CONNECTIONS,
                { color: 'rgba(0, 255, 255, 0.3)', lineWidth: 1 });
            mpDrawLandmarks(ctx, results.poseLandmarks,
                { color: 'rgba(0, 255, 255, 0.5)', lineWidth: 1, radius: 2 });
        }

        // Tangan kanan (hijau)
        if (results.rightHandLandmarks) {
            drawConnectors(ctx, results.rightHandLandmarks, HAND_CONNECTIONS,
                { color: '#00DC64', lineWidth: 2 });
            mpDrawLandmarks(ctx, results.rightHandLandmarks,
                { color: '#FF6600', lineWidth: 1, radius: 3 });
        }

        // Tangan kiri (biru)
        if (results.leftHandLandmarks) {
            drawConnectors(ctx, results.leftHandLandmarks, HAND_CONNECTIONS,
                { color: '#0096FF', lineWidth: 2 });
            mpDrawLandmarks(ctx, results.leftHandLandmarks,
                { color: '#FF6600', lineWidth: 1, radius: 3 });
        }
    }, []);

    // ── Initialize MediaPipe Holistic saat kamera siap ─────────────────────
    useEffect(() => {
        if (!isCameraOpen || !isCamReady) return;

        const holistic = new Holistic({
            locateFile: (file) =>
                `https://cdn.jsdelivr.net/npm/@mediapipe/holistic/${file}`,
        });
        holistic.setOptions({
            modelComplexity: 1,
            smoothLandmarks: true,
            minDetectionConfidence: 0.5,
            minTrackingConfidence: 0.5,
        });
        holistic.onResults(onHolisticResults);
        holisticRef.current = holistic;

        // Loop: kirim frame webcam ke MediaPipe client-side
        let running = true;
        const processLoop = async () => {
            if (!running) return;
            const video = webcamRef.current?.video;
            if (video && video.readyState >= 2 && holisticRef.current) {
                try {
                    await holisticRef.current.send({ image: video });
                } catch (e) {
                    // Ignore errors saat cleanup
                }
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

    // ── Prediksi huruf — server-side per frame (Asinkron) ─────────────────────
    const captureHuruf = useCallback(() => {
        if (!webcamRef.current)        return;
        if (!isCamReadyRef.current)    return;
        if (isProcessingRef.current)   return;

        const canvas = webcamRef.current.getCanvas();
        if (!canvas) return;

        isProcessingRef.current = true;
        setIsProcessing(true);

        canvas.toBlob(async (blob) => {
            if (!blob) {
                isProcessingRef.current = false;
                setIsProcessing(false);
                return;
            }

            try {
                const formData = new FormData();
                formData.append('image', blob, 'capture.jpg');
                const { data } = await axios.post(
                    `${API_BASE_URL}/ai/predict/huruf`,
                    formData,
                    {
                        headers: {
                            'Content-Type': 'multipart/form-data',
                            'X-Session-ID': SESSION_ID,
                        },
                    }
                );

                if (data.detection_status) {
                    setDetectionStatus(data.detection_status);
                }

                if (data.text) {
                    setTranslation(data.text);
                    setConfidence(Math.round((data.confidence || 0) * 100));
                    setDbResult(data.found_in_db && data.db_detail ? data.db_detail : null);
                }
            } catch (err) {
                console.error('[captureHuruf]', err);
            } finally {
                isProcessingRef.current = false;
                setIsProcessing(false);
            }
        }, 'image/jpeg', 0.8);
    }, []);

    // ══════════════════════════════════════════════════════════════════════════
    // ── BATCH KATA: kumpulkan frame di browser, kirim sekaligus ──────────────
    // ══════════════════════════════════════════════════════════════════════════

    // Langkah 1: Capture frame ke buffer lokal (setiap ~33ms) HANYA jika ada tangan
    const captureKataFrame = useCallback(() => {
        if (!webcamRef.current)       return;
        if (!isCamReadyRef.current)   return;
        if (isSendingBatchRef.current) return;
        if (kataFramesRef.current.length >= FRAME_PER_VIDEO) return;

        // MIMIC PYTHON: Hanya rekam frame JIKA ada tangan terdeteksi oleh MediaPipe client
        if (!handDetectedRef.current) return;

        // OPTIMASI: Gunakan getCanvas().toBlob agar asinkron dan sangat cepat
        const canvas = webcamRef.current.getCanvas();
        if (!canvas) return;

        canvas.toBlob((blob) => {
            if (!blob) return;
            
            kataFramesRef.current.push(blob);
            setBufferCount(kataFramesRef.current.length);

            // Saat buffer penuh → kirim batch ke server
            if (kataFramesRef.current.length >= FRAME_PER_VIDEO) {
                sendKataBatch();
            }
        }, 'image/jpeg', 0.8);
    }, []);

    // Langkah 2: Kirim semua frame sekaligus ke server
    const sendKataBatch = useCallback(async () => {
        if (isSendingBatchRef.current) return;
        isSendingBatchRef.current  = true;
        isCapturingRef.current     = false;
        setIsCapturing(false);
        setIsProcessing(true);

        try {
            const formData = new FormData();
            kataFramesRef.current.forEach((blob, i) => {
                formData.append('frames', blob, `frame_${i}.jpg`);
            });

            const { data } = await axios.post(
                `${API_BASE_URL}/ai/predict/kata/batch`,
                formData,
                {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                        'X-Session-ID': SESSION_ID,
                    },
                    timeout: 30000, // 30 detik timeout untuk batch processing
                }
            );

            if (data.detection_status) {
                setDetectionStatus(data.detection_status);
            }

            if (data.text) {
                setTranslation(data.text);
                if (data.text !== '?') {
                    setKalimat(prev => {
                        if (prev.length === 0 || prev[prev.length - 1].toLowerCase() !== data.text.toLowerCase()) {
                            return [...prev, data.text];
                        }
                        return prev;
                    });
                }
                setConfidence(Math.round((data.confidence || 0) * 100));
                setDbResult(data.found_in_db && data.db_detail ? data.db_detail : null);
            }
        } catch (err) {
            console.error('[sendKataBatch]', err);
        } finally {
            setIsProcessing(false);
            // Reset buffer lokal
            kataFramesRef.current     = [];
            setBufferCount(0);
            isSendingBatchRef.current = false;

            // Mulai capture lagi setelah jeda singkat (dipercepat jadi 500ms agar responsif)
            setTimeout(() => {
                if (modeRef.current === 'kata' && isCamReadyRef.current) {
                    isCapturingRef.current = true;
                    setIsCapturing(true);
                }
            }, 500); 
        }
    }, []);

    // ── Interval — mulai setelah kamera benar-benar siap ──────────────────────
    useEffect(() => {
        clearInterval(intervalRef.current);
        if (!isCameraOpen || !isCamReady) return;

        if (modeRef.current === 'huruf') {
            intervalRef.current = setInterval(captureHuruf, INTERVAL_HURUF);
        } else {
            // Mode kata: capture frame ke buffer lokal
            intervalRef.current = setInterval(() => {
                if (isCapturingRef.current) captureKataFrame();
            }, INTERVAL_KATA);
        }

        return () => clearInterval(intervalRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isCameraOpen, isCamReady, mode]);

    // ── Nyalakan kamera ───────────────────────────────────────────────────────
    const startCamera = () => {
        setCamError('');
        setTranslation('');
        setKalimat([]);
        setDbResult(null);
        setConfidence(0);
        setBufferCount(0);
        setIsCamReady(false);
        isCamReadyRef.current = false;
        kataFramesRef.current = [];
        isSendingBatchRef.current = false;
        handDetectedRef.current = false;
        setDetectionStatus({ right_hand: false, left_hand: false, overlapping: false, pose: false });
        if (modeRef.current === 'kata') {
            isCapturingRef.current = true;
            setIsCapturing(true);
        }
        setIsCameraOpen(true);
    };

    // ── Matikan kamera ────────────────────────────────────────────────────────
    const stopCamera = () => {
        clearInterval(intervalRef.current);
        cancelAnimationFrame(animFrameRef.current);
        setIsCameraOpen(false);
        setIsCamReady(false);
        isCamReadyRef.current = false;
        setTranslation('');
        setKalimat([]);
        setDbResult(null);
        setConfidence(0);
        setBufferCount(0);
        setIsProcessing(false);
        isProcessingRef.current    = false;
        isCapturingRef.current     = false;
        isSendingBatchRef.current  = false;
        handDetectedRef.current    = false;
        kataFramesRef.current      = [];
        setIsCapturing(false);
        setDetectionStatus({ right_hand: false, left_hand: false, overlapping: false, pose: false });
        // Reset session di server
        axios.post(`${API_BASE_URL}/ai/predict/reset`, null, {
            headers: { 'X-Session-ID': SESSION_ID },
        }).catch(() => {});
    };

    const toggleCamera = () => isCameraOpen ? stopCamera() : startCamera();

    // ── Ganti mode — bisa saat kamera aktif ──────────────────────────────────
    const switchMode = (newMode) => {
        if (newMode === mode) return;

        // Reset state
        setTranslation('');
        setKalimat([]);
        setDbResult(null);
        setConfidence(0);
        setBufferCount(0);
        kataFramesRef.current     = [];
        isSendingBatchRef.current = false;
        handDetectedRef.current   = false;
        setDetectionStatus({ right_hand: false, left_hand: false, overlapping: false, pose: false });

        // Reset session di server (buffer + extractor)
        axios.post(`${API_BASE_URL}/ai/predict/reset`, null, {
            headers: { 'X-Session-ID': SESSION_ID },
        }).catch(() => {});

        // Jika masuk ke mode kata, mulai capturing
        if (newMode === 'kata') {
            isCapturingRef.current = true;
            setIsCapturing(true);
        } else {
            isCapturingRef.current = false;
            setIsCapturing(false);
        }

        modeRef.current = newMode;
        setMode(newMode);
    };

    // ── Reset ────────────────────────────────────────────────────────────────
    const resetAll = () => {
        setTranslation('');
        setKalimat([]);
        setDbResult(null);
        setConfidence(0);
        setBufferCount(0);
        kataFramesRef.current     = [];
        isSendingBatchRef.current = false;
        handDetectedRef.current   = false;
        isCapturingRef.current    = true;
        setIsCapturing(true);
        axios.post(`${API_BASE_URL}/ai/predict/reset`, null, {
            headers: { 'X-Session-ID': SESSION_ID },
        }).catch(() => {});
    };

    const confVariant = confidence >= 80 ? 'success' : confidence >= 65 ? 'warning' : 'danger';
    const bufferPct   = Math.round((bufferCount / FRAME_PER_VIDEO) * 100);

    return (
        <div className="d-flex flex-column min-vh-100">
            <title>Video to Text - Bahasaku</title>
            <Navbar />
            <main className="video-to-text-main flex-grow-1">
                <Container className="my-4">
                    <Card className="shadow-sm">
                        <Card.Header className="bg-primary text-white">
                            <div className="d-flex align-items-center justify-content-between flex-wrap gap-2">
                                <h4 className="my-1">Penerjemah Bahasa Isyarat (AI)</h4>
                                <ButtonGroup size="sm">
                                    <Button
                                        variant={mode === 'huruf' ? 'light' : 'outline-light'}
                                        onClick={() => switchMode('huruf')}
                                    >
                                        <FaFont className="me-1" /> Huruf
                                    </Button>
                                    <Button
                                        variant={mode === 'kata' ? 'light' : 'outline-light'}
                                        onClick={() => switchMode('kata')}
                                    >
                                        <FaHandPaper className="me-1" /> Kata
                                    </Button>
                                </ButtonGroup>
                            </div>
                        </Card.Header>

                        <Card.Body className="p-4">
                            <Row className="g-4">

                                {/* ── KIRI: Kamera & kontrol ── */}
                                <Col lg={7} md={12}>
                                    <div
                                        className="video-wrapper border rounded bg-light d-flex align-items-center justify-content-center position-relative overflow-hidden"
                                        style={{ minHeight: '360px' }}
                                    >
                                        {isCameraOpen ? (
                                            <>
                                                <Webcam
                                                    audio={false}
                                                    ref={webcamRef}
                                                    screenshotFormat="image/jpeg"
                                                    videoConstraints={videoConstraints}
                                                    mirrored={true}
                                                    width="100%"
                                                    className="rounded"
                                                    onUserMedia={() => {
                                                        isCamReadyRef.current = true;
                                                        setIsCamReady(true);
                                                    }}
                                                    onUserMediaError={(err) => {
                                                        console.error('Webcam error:', err);
                                                        let msg = `Kamera error: ${err.message}`;
                                                        if (err.name === 'NotAllowedError')
                                                            msg = 'Izin kamera ditolak. Izinkan akses kamera di browser lalu muat ulang halaman.';
                                                        else if (err.name === 'NotFoundError')
                                                            msg = 'Kamera tidak ditemukan. Pastikan perangkat memiliki kamera.';
                                                        setCamError(msg);
                                                        setIsCameraOpen(false);
                                                    }}
                                                />

                                                {/* Canvas overlay untuk landmark (client-side MediaPipe) */}
                                                <canvas
                                                    ref={canvasRef}
                                                    className="position-absolute top-0 start-0 w-100 h-100"
                                                    style={{
                                                        pointerEvents: 'none',
                                                        transform: 'scaleX(-1)',
                                                        zIndex: 1,
                                                    }}
                                                />

                                                {/* Spinner loading sampai stream siap */}
                                                {!isCamReady && (
                                                    <div className="position-absolute d-flex flex-column align-items-center justify-content-center w-100 h-100 bg-light bg-opacity-75">
                                                        <div className="spinner-border text-primary mb-2" role="status" />
                                                        <span className="small text-muted">Memulai kamera...</span>
                                                    </div>
                                                )}

                                                {/* Header mode badge + status deteksi */}
                                                {isCamReady && (
                                                    <div className="position-absolute top-0 start-0 w-100" style={{ zIndex: 2 }}>
                                                        {/* Baris atas: Mode & status */}
                                                        <div className="d-flex justify-content-between align-items-center px-2 py-1"
                                                             style={{ backgroundColor: 'rgba(25, 25, 25, 0.75)' }}>
                                                            <Badge
                                                                bg={mode === 'huruf' ? 'warning' : 'success'}
                                                                text={mode === 'huruf' ? 'dark' : 'white'}
                                                                className="px-2 py-1"
                                                            >
                                                                MODE: {mode.toUpperCase()}
                                                            </Badge>
                                                            <div className="d-flex gap-1">
                                                                {mode === 'huruf' && isProcessing && (
                                                                    <Badge bg="info">Mendeteksi...</Badge>
                                                                )}
                                                                {mode === 'kata' && (
                                                                    <Badge bg={isProcessing ? 'info' : isCapturing ? 'danger' : 'secondary'}>
                                                                        {isProcessing
                                                                            ? '⏳ Memproses...'
                                                                            : isCapturing
                                                                                ? '● Merekam...'
                                                                                : '■ Menunggu...'}
                                                                    </Badge>
                                                                )}
                                                            </div>
                                                        </div>

                                                        {/* Baris kedua: Status deteksi tangan */}
                                                        <div className="detection-status-bar d-flex gap-2 px-2 py-1"
                                                             style={{ backgroundColor: 'rgba(25, 25, 25, 0.55)' }}>
                                                            <span className={`detection-indicator ${detectionStatus.right_hand ? 'active-green' : 'inactive'}`}>
                                                                Kanan:{detectionStatus.right_hand ? '✓' : '○'}
                                                            </span>
                                                            <span className={`detection-indicator ${detectionStatus.left_hand ? 'active-blue' : 'inactive'}`}>
                                                                Kiri:{detectionStatus.left_hand ? '✓' : '○'}
                                                            </span>
                                                            <span className={`detection-indicator ${detectionStatus.overlapping ? 'active-orange' : 'inactive'}`}>
                                                                Tumpuk:{detectionStatus.overlapping ? 'YA' : '-'}
                                                            </span>
                                                        </div>
                                                    </div>
                                                )}
                                            </>
                                        ) : (
                                            /* Placeholder saat kamera mati */
                                            <div className="text-center text-muted p-5">
                                                <FaVideo size={60} className="mb-3" />
                                                <h5>Kamera Nonaktif</h5>
                                                {camError ? (
                                                    <p className="text-danger small mt-2">{camError}</p>
                                                ) : (
                                                    <>
                                                        <p className="mb-1">
                                                            Mode: <strong>
                                                                {mode === 'huruf' ? 'Huruf (BISINDO)' : 'Kata (BISINDO)'}
                                                            </strong>
                                                        </p>
                                                        <p className="small text-muted">
                                                            {mode === 'huruf'
                                                                ? 'Tunjukkan 1 huruf isyarat di depan kamera.'
                                                                : 'Lakukan gerakan kata — sistem otomatis merekam 30 frame.'}
                                                        </p>
                                                    </>
                                                )}
                                                <p className="mt-2 mb-0">Klik "Mulai Kamera" di bawah.</p>
                                            </div>
                                        )}
                                    </div>


                                    {/* Progress bar buffer kata */}
                                    {isCameraOpen && isCamReady && mode === 'kata' && (
                                        <div className="mt-2">
                                            <div className="d-flex justify-content-between small text-muted mb-1">
                                                <span>{isProcessing ? 'Memproses prediksi...' : 'Buffer frame'}</span>
                                                <span>{isProcessing ? '⏳' : `${bufferCount} / ${FRAME_PER_VIDEO}`}</span>
                                            </div>
                                            <ProgressBar
                                                now={isProcessing ? 100 : bufferPct}
                                                variant={isProcessing ? 'info' : bufferPct >= 100 ? 'success' : 'primary'}
                                                animated={isCapturing || isProcessing}
                                                striped={isProcessing}
                                                style={{ height: '8px' }}
                                            />
                                        </div>
                                    )}

                                    {/* Tombol kontrol */}
                                    <div className="d-flex gap-2 mt-3">
                                        <Button
                                            variant={isCameraOpen ? 'danger' : 'primary'}
                                            onClick={toggleCamera}
                                            size="lg"
                                            className="flex-grow-1"
                                        >
                                            {isCameraOpen
                                                ? <><FaStop className="me-2" />Stop Kamera</>
                                                : <><FaVideo className="me-2" />Mulai Kamera</>}
                                        </Button>
                                        {isCameraOpen && isCamReady && (
                                            <Button variant="outline-secondary" onClick={resetAll} title="Reset (R)">
                                                <FaRedo className="me-1" /> Reset
                                            </Button>
                                        )}
                                    </div>
                                </Col>

                                {/* ── KANAN: Hasil terjemahan ── */}
                                <Col lg={5} md={12}>
                                    <div className="h-100 d-flex flex-column">
                                        <h5 className="text-center text-primary mb-3">Hasil Terjemahan:</h5>

                                        <Card
                                            className="text-center p-3 shadow-sm mb-3 d-flex align-items-center justify-content-center"
                                            style={{
                                                border: '2px dashed #0d6efd',
                                                backgroundColor: '#f0f8ff',
                                                minHeight: '120px',
                                                overflow: 'hidden',
                                            }}
                                        >
                                            <div style={{ width: '100%', overflow: 'hidden' }}>
                                                <h2
                                                    className={`fw-bold mb-0 ${translation === '?' ? 'text-muted' : 'text-dark'}`}
                                                    style={{
                                                        fontSize: 'clamp(1.5rem, 4vw, 3rem)',
                                                        wordBreak: 'break-word',
                                                        overflowWrap: 'break-word',
                                                    }}
                                                >
                                                    {translation || '-'}
                                                </h2>
                                                <p className="text-muted mt-2 mb-0 small">
                                                    {translation
                                                        ? translation === '?'
                                                            ? 'Confidence rendah, coba ulangi gerakan'
                                                            : `${mode === 'huruf' ? 'Huruf' : 'Kata'} terakhir terdeteksi`
                                                        : isProcessing && mode === 'kata'
                                                            ? 'Memproses prediksi kata...'
                                                            : mode === 'kata' && isCameraOpen && isCapturing
                                                                ? 'Sedang merekam gerakan...'
                                                                : 'Menunggu gerakan...'}
                                                </p>
                                            </div>
                                        </Card>

                                        {/* Tampilan Kalimat - HANYA UNTUK MODE KATA */}
                                        {mode === 'kata' && (
                                            <Card className="p-3 shadow-sm flex-grow-1 border-0" style={{ borderLeft: '4px solid #0d6efd', backgroundColor: '#fff' }}>
                                                <div className="d-flex justify-content-between align-items-center mb-2">
                                                    <h6 className="mb-0 fw-bold text-primary">Kalimat yang Terbentuk:</h6>
                                                    <div className="d-flex gap-2">
                                                        <Button variant="outline-warning" size="sm" onClick={() => setKalimat(prev => prev.slice(0, -1))} disabled={kalimat.length === 0} title="Hapus kata terakhir">
                                                            Hapus 1 Kata
                                                        </Button>
                                                        <Button variant="outline-danger" size="sm" onClick={() => setKalimat([])} disabled={kalimat.length === 0} title="Hapus semua kalimat">
                                                            Kosongkan
                                                        </Button>
                                                    </div>
                                                </div>
                                                <p className="fs-5 mb-0 text-dark" style={{ minHeight: '60px', wordBreak: 'break-word' }}>
                                                    {kalimat.length > 0 ? kalimat.join(' ') : <span className="text-muted fst-italic">Belum ada kalimat...</span>}
                                                </p>
                                            </Card>
                                        )}

                                        {/* Confidence bar */}
                                        {translation && translation !== '?' && confidence > 0 && (
                                            <div className="mt-3">
                                                <div className="d-flex justify-content-between small mb-1">
                                                    <span className="text-muted">Tingkat keyakinan</span>
                                                    <span className={`fw-bold text-${confVariant}`}>{confidence}%</span>
                                                </div>
                                                <ProgressBar
                                                    now={confidence}
                                                    variant={confVariant}
                                                    style={{ height: '8px' }}
                                                />
                                            </div>
                                        )}

                                        {/* Info dari database */}
                                        {dbResult && (
                                            <Card className="mt-3 p-3 border-0 bg-light shadow-sm">
                                                <small className="text-muted d-block mb-1">
                                                    Ditemukan di database:
                                                </small>
                                                {dbResult.image_url && (
                                                    <img
                                                        src={dbResult.image_url}
                                                        alt={dbResult.text}
                                                        className="img-fluid rounded mb-2"
                                                        style={{ maxHeight: '120px', objectFit: 'contain' }}
                                                    />
                                                )}
                                                {dbResult.description && (
                                                    <p className="small mb-0">{dbResult.description}</p>
                                                )}
                                            </Card>
                                        )}
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