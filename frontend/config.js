// Configuration
const CONFIG = {
    // Change this to your deployed backend URL
    API_BASE_URL: window.location.hostname === 'localhost'
        ? 'http://localhost:5000/api'
        : 'https://finvizpro-api.onrender.com/api', // Replace with your actual backend URL
};

const API_BASE_URL = CONFIG.API_BASE_URL;
