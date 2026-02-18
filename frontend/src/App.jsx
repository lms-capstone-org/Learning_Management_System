import React, { useState, useEffect } from 'react';
import { auth, db } from './firebase';
import { onAuthStateChanged, signOut } from 'firebase/auth';
import { doc, getDoc, setDoc } from 'firebase/firestore';
import './App.css'; // Importing styles

// Components
import Login from './components/Login';
import InstructorDashboard from './components/InstructorDashboard';
import StudentDashboard from './components/StudentDashboard';

function App() {
  const [user, setUser] = useState(null);
  const [role, setRole] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Listen for login/logout changes
    const unsubscribe = onAuthStateChanged(auth, async (currentUser) => {
      if (currentUser) {
        setUser(currentUser);
        // Check Firestore for user role
        const userRef = doc(db, "users", currentUser.uid);
        const userSnap = await getDoc(userRef);
        
        if (userSnap.exists()) {
          setRole(userSnap.data().role);
        } else {
          // Default new users to 'student'
          await setDoc(userRef, { email: currentUser.email, role: "student" });
          setRole("student");
        }
      } else {
        setUser(null);
        setRole(null);
      }
      setLoading(false);
    });
    return () => unsubscribe();
  }, []);

  if (loading) return <div className="loader-center">Loading...</div>;
  if (!user) return <Login />;

  return (
    <div className="app-container">
      {/* Navbar */}
      <nav className="navbar">
        <div className="brand">🎓 LMS Capstone</div>
        <div className="user-info">
          <span>{user.email} ({role})</span>
          <button className="logout-btn" onClick={() => signOut(auth)}>Logout</button>
        </div>
      </nav>
      
      {/* Main Dashboard */}
      <div className="main-content">
        {role === 'instructor' ? (
          <InstructorDashboard user={user} />
        ) : (
          <StudentDashboard />
        )}
      </div>
    </div>
  );
}

export default App;