// Jika di production (dibuild dan dijalankan oleh Nginx), gunakan path relatif ('')
// Jika di development (npm start), gunakan localhost:5000
export const SERVER_URL = process.env.NODE_ENV === 'production' ? '' : (process.env.REACT_APP_API_URL || 'http://localhost:5000');
export const API_BASE_URL = `${SERVER_URL}/api`;

export default API_BASE_URL;