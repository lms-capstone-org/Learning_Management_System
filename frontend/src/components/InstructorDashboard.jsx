import React, { useState } from 'react';
import api from '../api'; // Import the secure API helper

function InstructorDashboard({ user }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("title", file.name);
      // NOTE: We do NOT need to send instructor_id anymore.
      // The backend extracts it securely from the Token.

      // 👇 Uses new Endpoint + Auto-Token
      await api.post("/courses/upload", formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      alert("Upload Successful! Video saved to 'courses'.");
      setFile(null);
    } catch (error) {
      console.error("Upload Error:", error);
      alert("Upload failed. Check console for details.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-container">
      <div className="upload-card">
        <h2 style={{ marginBottom: '10px' }}>📤 Upload Lecture</h2>
        <p style={{ color: '#6b7280', marginBottom: '30px' }}>
          Upload a video to the Course Catalog.
        </p>
        
        <input 
          className="file-input"
          type="file" 
          accept="video/mp4" 
          onChange={(e) => setFile(e.target.files[0])} 
        />
        
        {file && <p style={{ marginTop: '10px', fontWeight: 600 }}>{file.name}</p>}

        <button 
          className="upload-btn" 
          onClick={handleUpload} 
          disabled={uploading || !file}
        >
          {uploading ? "Uploading..." : "Start Upload"}
        </button>
      </div>
    </div>
  );
}

export default InstructorDashboard;