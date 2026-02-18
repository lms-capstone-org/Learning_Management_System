import axios from 'axios';
import { auth } from './firebase';

const api = axios.create({
  baseURL: "http://localhost:8000", // Backend URL
});

// Interceptor: Before every request, add the Token
api.interceptors.request.use(async (config) => {
  const user = auth.currentUser;
  
  if (user) {
    // 1. Get the secure token from Firebase
    const token = await user.getIdToken();
    // 2. Add it to the header
    config.headers.Authorization = `Bearer ${token}`;
  }
  
  return config;
}, (error) => {
  return Promise.reject(error);
});

export default api;