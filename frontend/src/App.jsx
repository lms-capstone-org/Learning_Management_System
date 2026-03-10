import React, { useState, useEffect } from 'react';
import { auth, db } from './firebase';
import { onAuthStateChanged, signOut } from 'firebase/auth';
import { doc, getDoc, setDoc } from 'firebase/firestore';
import './App.css';

// Components
import Login from './components/Login';
import RoleSelection from './components/RoleSelection';
import InstructorDashboard from './components/InstructorDashboard';
import StudentDashboard from './components/StudentDashboard';
import CommunityFeed from './components/CommunityFeed';

function App() {
  const [user, setUser] = useState(null);
  const [role, setRole] = useState(null);
  const [loading, setLoading] = useState(true);
  const [username, setUsername] = useState(null);
  const[needsRoleSelection, setNeedsRoleSelection] = useState(false);
  const [currentTab, setCurrentTab] = useState('dashboard');

  // Listen for login/logout state changes
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (currentUser) => {
      if (currentUser) {
        setUser(currentUser);

        // Check if user exists in the Firestore database
        const userRef = doc(db, "users", currentUser.uid);
        const userSnap = await getDoc(userRef);

        if (userSnap.exists()) {
          // User already exists in DB, fetch role and proceed
          setRole(userSnap.data().role);
          setUsername(userSnap.data().username || "User");
          setNeedsRoleSelection(false);
        } else {
          // New User! Show them the role selection screen
          setNeedsRoleSelection(true);
        }
      } else {
        // User is logged out
        setUser(null);
        setRole(null);
        setNeedsRoleSelection(false);
      }

      setLoading(false);
    });

    return () => unsubscribe();
  },[]);

  // Function to save the new user's role to the database
  const handleRoleSelection = async (selectedRole, selectedUsername) => {
    if (!user) return;

    try {
      const userRef = doc(db, "users", user.uid);

      await setDoc(userRef, {
        uid: user.uid,
        email: user.email,
        username: selectedUsername, // 🆕 Save to Firestore
        role: selectedRole,
        created_at: new Date().toISOString(),
        ...(selectedRole === 'student' ? { enrollments: {} } : {})
      });

      // Update local state
      setRole(selectedRole);
      setUsername(selectedUsername); // 🆕 Update local state
      setNeedsRoleSelection(false);
    } catch (error) {
      console.error("Error saving user role:", error);
      alert("Failed to set up your account. Check the console.");
    }
  };

  // 1. Show Loading state while checking auth
  if (loading) {
    return <div style={{ textAlign: 'center', marginTop: '50px' }}>Loading...</div>;
  }

  // 2. Show Login screen if not authenticated
  if (!user) {
    return <Login />;
  }

  // 3. Show Role Selection if they are a brand new user
  if (needsRoleSelection) {
    return (
      <RoleSelection
        onSelectRole={handleRoleSelection}
        userEmail={user.email}
      />
    );
  }

  // 4. Show Main App if authenticated and role is set
  return (
    <div className="app-container">
      {/* Navbar visible on all dashboards */}
      <nav className="navbar" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '15px 20px', background: '#f3f4f6', borderBottom: '1px solid #e5e7eb' }}>

        {/* Logo and Navigation Links */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '30px' }}>
          <div className="brand" style={{ fontWeight: 'bold', fontSize: '18px' }}>🎓 LMS Capstone</div>

          {/* 🆕 Tab Buttons */}
          <div style={{ display: 'flex', gap: '15px' }}>
            <button
              onClick={() => setCurrentTab('dashboard')}
              style={{ background: 'transparent', border: 'none', fontSize: '16px', fontWeight: currentTab === 'dashboard' ? 'bold' : 'normal', color: currentTab === 'dashboard' ? '#4f46e5' : '#64748b', cursor: 'pointer', borderBottom: currentTab === 'dashboard' ? '2px solid #4f46e5' : 'none', paddingBottom: '4px' }}
            >
              Dashboard
            </button>
            <button
              onClick={() => setCurrentTab('community')}
              style={{ background: 'transparent', border: 'none', fontSize: '16px', fontWeight: currentTab === 'community' ? 'bold' : 'normal', color: currentTab === 'community' ? '#4f46e5' : '#64748b', cursor: 'pointer', borderBottom: currentTab === 'community' ? '2px solid #4f46e5' : 'none', paddingBottom: '4px' }}
            >
              Community Feed
            </button>
          </div>
        </div>

        <div className="user-info">
          <span style={{ marginRight: '15px', fontWeight: 'bold' }}>{username} <span style={{fontWeight: 'normal', color: 'gray'}}>({role})</span></span>
          <button
            className="logout-btn"
            onClick={() => signOut(auth)}
            style={{ cursor: 'pointer', padding: '5px 10px', background: '#ef4444', color: 'white', border: 'none', borderRadius: '5px' }}
          >
            Logout
          </button>
        </div>
      </nav>

      {/* Main Content Area */}
      <div className="main-content" style={{ padding: '20px' }}>
        {/* 🆕 Conditional Rendering based on selected tab */}
        {currentTab === 'community' ? (
          <CommunityFeed currentUser={user} />
        ) : (
          <>
            {role === "instructor" && <InstructorDashboard user={user} />}
            {role === "student" && <StudentDashboard user={user} />}
          </>
        )}
      </div>
    </div>
  );
}

export default App;