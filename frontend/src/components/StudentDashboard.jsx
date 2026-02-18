import React, { useState, useEffect } from 'react';
import api from '../api'; // Use secure API
import { db } from '../firebase'; 
import { collection, onSnapshot, orderBy, query } from 'firebase/firestore';

function StudentDashboard() {
  const [videos, setVideos] = useState([]);
  const [selectedVideo, setSelectedVideo] = useState(null);
  const [processing, setProcessing] = useState(false);

  // 1. Fetch Videos (Real-time Listener)
  // We keep using Firestore directly for reading the list because it's faster for updates.
  // However, if you want to use the backend API, you would use api.get('/courses/')
  useEffect(() => {
    // Note: For now, we still read from Firestore directly for real-time updates.
    // In a full production app, you might fetch from API to respect permissions.
    const q = query(collection(db, "videos"), orderBy("created_at", "desc"));

    const unsubscribe = onSnapshot(q, (snapshot) => {
      const videoList = snapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));
      setVideos(videoList);
    });

    return () => unsubscribe();
  }, []);

  // 2. Sync Selected Video
  useEffect(() => {
    if (selectedVideo) {
      const updated = videos.find(v => v.id === selectedVideo.id);
      if (updated) setSelectedVideo(updated);
    }
  }, [videos]); 

  // 3. Trigger AI Generation
  const handleGenerateSummary = async () => {
    if (!selectedVideo) return;
    setProcessing(true);
    try {
      // 👇 NEW ENDPOINT: /ai/process-video
      await api.post(`/ai/process-video/${selectedVideo.id}`);
      
      alert("AI Processing Started! Wait for the update.");
    } catch (error) {
      console.error("Error starting AI:", error);
      alert("Failed to start AI processing. Are you logged in?");
      setProcessing(false);
    }
  };

  return (
    <div className="dashboard-grid">
      <div className="sidebar">
        <h3>Course Content</h3>
        {videos.map(v => (
          <div 
            key={v.id} 
            onClick={() => { setSelectedVideo(v); setProcessing(false); }}
            className={`video-item ${selectedVideo?.id === v.id ? 'active' : ''}`}
          >
            <span className="video-title">{v.title}</span>
            <span className={`status-badge status-${v.status}`}>
              {v.status === 'completed' ? 'Ready' : 
               v.status === 'uploaded' ? 'New' : 'Processing...'}
            </span>
          </div>
        ))}
      </div>

      <div className="main-content">
        {selectedVideo ? (
          <div>
            <h1 style={{ marginBottom: '1rem' }}>{selectedVideo.title}</h1>
            <div className="video-wrapper">
              {/* Note: In production, fetch a fresh SAS URL via API if this link expired */}
              <video controls src={selectedVideo.video_url} width="100%" />
            </div>
            
            <div className="summary-box">
              <div className="summary-header">
                <span className="ai-icon">✨</span>
                <h3 style={{ margin: 0 }}>AI Smart Assistant</h3>
              </div>

              {selectedVideo.status === 'uploaded' && (
                <div style={{ textAlign: 'center', padding: '20px' }}>
                  <p>Click below to generate study notes.</p>
                  <button 
                    onClick={handleGenerateSummary}
                    disabled={processing}
                    style={{
                      background: processing ? '#ccc' : '#4f46e5',
                      color: 'white', padding: '10px 20px', border: 'none', borderRadius: '8px', cursor: 'pointer'
                    }}
                  >
                    {processing ? "Starting AI..." : "⚡ Generate AI Summary"}
                  </button>
                </div>
              )}

              {(selectedVideo.status === 'transcribing' || selectedVideo.status === 'summarizing') && (
                <div style={{ padding: '20px', color: '#b45309', textAlign: 'center' }}>
                  <div className="loader"></div>
                  <p>AI is analyzing... please wait.</p>
                </div>
              )}

              {selectedVideo.status === 'completed' && (
                <div className="fade-in"> 
                  <p style={{ whiteSpace: 'pre-line' }}>{selectedVideo.summary}</p>
                </div>
              )}
            </div>
          </div>
        ) : (
          <p style={{padding: '20px'}}>Select a video to start learning.</p>
        )}
      </div>
    </div>
  );
}

export default StudentDashboard;