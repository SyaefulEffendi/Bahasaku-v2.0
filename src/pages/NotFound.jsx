import React from 'react';
import { Link } from 'react-router-dom';

function NotFound() {
  const styles = {
    container: {
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh',
      textAlign: 'center',
      backgroundColor: '#f8f9fa',
      padding: '20px'
    },
    errorCode: {
      fontSize: '8rem',
      fontWeight: 'bold',
      color: '#0d6efd',
      marginBottom: '10px',
      lineHeight: '1'
    },
    title: {
      fontSize: '2rem',
      fontWeight: '600',
      color: '#343a40',
      marginBottom: '15px'
    },
    description: {
      fontSize: '1.2rem',
      color: '#6c757d',
      marginBottom: '30px',
      maxWidth: '500px'
    },
    button: {
      padding: '10px 25px',
      fontSize: '1.1rem',
      borderRadius: '30px',
      textDecoration: 'none'
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.errorCode}>404</div>
      <h1 style={styles.title}>Halaman Tidak Ditemukan</h1>
      <p style={styles.description}>
        Maaf, halaman yang Anda cari mungkin telah dihapus, namanya diubah, atau tidak pernah ada sama sekali.
      </p>
      <Link to="/" className="btn btn-primary" style={styles.button}>
        Kembali ke Beranda
      </Link>
    </div>
  );
}

export default NotFound;
