// import React, { useState, useEffect } from 'react';
// import { auth, db } from './firebase';
// import { onAuthStateChanged, signOut } from 'firebase/auth';
// import { doc, getDoc, setDoc } from 'firebase/firestore';
// import './App.css'; // Importing styles

// // Components
// import Login from './components/Login';
// import InstructorDashboard from './components/InstructorDashboard';
// import StudentDashboard from './components/StudentDashboard';

// function App() {
//   const [user, setUser] = useState(null);
//   const [role, setRole] = useState(null);
//   const [loading, setLoading] = useState(true);

//   useEffect(() => {
//     // Listen for login/logout changes
//     const unsubscribe = onAuthStateChanged(auth, async (currentUser) => {
//       if (currentUser) {
//         setUser(currentUser);
//         // Check Firestore for user role
//         const userRef = doc(db, "users", currentUser.uid);
//         const userSnap = await getDoc(userRef);

//         if (userSnap.exists()) {
//           setRole(userSnap.data().role);
//         } else {
//           // Default new users to 'student'
//           await setDoc(userRef, { email: currentUser.email, role: "student" });
//           setRole("student");
//         }
//       } else {
//         setUser(null);
//         setRole(null);
//       }
//       setLoading(false);
//     });
//     return () => unsubscribe();
//   }, []);

//   if (loading) return <div className="loader-center">Loading...</div>;
//   if (!user) return <Login />;

//   return (
//     <div className="app-container">
//       {/* Navbar */}
//       <nav className="navbar">
//         <div className="brand">🎓 LMS Capstone</div>
//         <div className="user-info">
//           <span>{user.email} ({role})</span>
//           <button className="logout-btn" onClick={() => signOut(auth)}>Logout</button>
//         </div>
//       </nav>

//       {/* Main Dashboard */}
//       <div className="main-content">
//         {role === 'instructor' ? (
//           <InstructorDashboard user={user} />
//         ) : (
//           <StudentDashboard />
//         )}
//       </div>
//     </div>
//   );
// }

// export default App;

import React, { useState, useEffect } from 'react';
import { auth } from './firebase';
import { onAuthStateChanged, signOut } from 'firebase/auth';
import './App.css';
import api from './api';

import Login from './components/Login';
import InstructorDashboard from './components/InstructorDashboard';
import StudentDashboard from './components/StudentDashboard';
import AdminDashboard from './components/AdminDashboard';

function App() {
  const [user, setUser] = useState(null);
  const [role, setRole] = useState(null);
  const [loading, setLoading] = useState(true);

  const refreshRole = async () => {
    try {
      await auth.currentUser?.getIdToken(true);
      const res = await api.get('/users/me');
      setRole(res.data.role);
    } catch (err) {
      console.error('Failed to refresh role:', err);
    }
  };

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (currentUser) => {
      if (currentUser) {
        setUser(currentUser);

        try {
          // Ensure a Firestore profile exists and is up-to-date
          await api.post('/users/sync');
          await currentUser.getIdToken(true);
          const res = await api.get('/users/me');
          setRole(res.data.role);
        } catch (err) {
          console.error('Failed to sync/fetch user:', err);
          // Fallback role so app doesn't break
          setRole('student');
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

  const renderDashboard = () => {
    if (role === 'admin') return <AdminDashboard user={user} onRoleChange={refreshRole} />;
    if (role === 'instructor') return <InstructorDashboard user={user} />;
    return <StudentDashboard />;
  };

  const roleColors = {
    admin: '#dc2626',
    instructor: '#7c3aed',
    student: '#2563eb',
  };

  return (
    <div className="app-container">
      <nav className="navbar">
        <div className="brand">🎓 LMS Capstone</div>
        <div className="user-info" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span>{user.email}</span>
          <span
            style={{
              background: roleColors[role] || '#6b7280',
              color: 'white',
              padding: '2px 10px',
              borderRadius: '999px',
              fontSize: '0.8rem',
              fontWeight: 600,
            }}
          >
            {role}
          </span>
          <button className="logout-btn" onClick={() => signOut(auth)}>
            Logout
          </button>
        </div>
      </nav>
      <div>{renderDashboard()}</div>
    </div>
  );
}

export default App;