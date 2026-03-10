import React, { useState } from 'react';

function RoleSelection({ onSelectRole, userEmail }) {
  const [saving, setSaving] = useState(false);
  // 🆕 Add state for the username
  const [username, setUsername] = useState("");

  const handleSelection = async (role) => {
    // 🆕 Require the user to enter a username before proceeding
    if (!username.trim()) {
      alert("Please enter a username first.");
      return;
    }

    setSaving(true);
    // 🆕 Pass the username back to App.jsx
    await onSelectRole(role, username.trim());
  };

  return (
    <div className="role-selection-container" style={{ textAlign: "center", marginTop: "100px" }}>
      <h2>Welcome, {userEmail}! 🎉</h2>
      <p style={{ color: '#6b7280', marginBottom: '20px' }}>
        It looks like you are new here. Please choose a username and select your account type:
      </p>

      {/* 🆕 NEW USERNAME INPUT FIELD */}
      <div style={{ marginBottom: '30px' }}>
        <input
          type="text"
          placeholder="Enter a cool username..."
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          disabled={saving}
          style={{
            padding: '12px',
            fontSize: '16px',
            borderRadius: '8px',
            border: '1px solid #ccc',
            width: '250px',
            textAlign: 'center'
          }}
        />
      </div>

      <div style={{ display: 'flex', justifyContent: 'center', gap: '20px' }}>
        <button
          onClick={() => handleSelection('student')}
          disabled={saving}
          style={{
            padding: '30px', fontSize: '18px', cursor: 'pointer',
            borderRadius: '10px', border: '2px solid #4f46e5',
            backgroundColor: 'white', width: '200px'
          }}
        >
          🎓<br/><br/>I am a Student
        </button>

        <button
          onClick={() => handleSelection('instructor')}
          disabled={saving}
          style={{
            padding: '30px', fontSize: '18px', cursor: 'pointer',
            borderRadius: '10px', border: '2px solid #10b981',
            backgroundColor: 'white', width: '200px'
          }}
        >
          👨‍🏫<br/><br/>I am an Instructor
        </button>
      </div>

      {saving && <p style={{ marginTop: '20px', color: '#4f46e5' }}>Setting up your account...</p>}
    </div>
  );
}

export default RoleSelection;