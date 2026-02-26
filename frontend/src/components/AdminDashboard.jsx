import React, { useState, useEffect } from 'react';
import api from '../api';

function AdminDashboard({ user, onRoleChange }) {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [message, setMessage] = useState('');

    useEffect(() => {
        fetchUsers();
    }, []);

    const fetchUsers = async () => {
        try {
            const res = await api.get('/admin/users');
            setUsers(res.data.users);
        } catch (err) {
            setMessage('Failed to load users.');
        } finally {
            setLoading(false);
        }
    };

    const handleRoleChange = async (uid, newRole) => {
        try {
            await api.post('/admin/assign-role', { uid, role: newRole });
            setMessage(`Role updated to "${newRole}" successfully.`);
            fetchUsers();
            if (onRoleChange) onRoleChange();
        } catch (err) {
            setMessage('Failed to update role.');
        }
    };

    return (
        <div style={{ padding: '2rem' }}>
            <h2>🛡️ Admin Dashboard — User Management</h2>

            {message && (
                <p style={{
                    background: '#dcfce7', border: '1px solid #86efac',
                    padding: '0.75rem', borderRadius: '6px', color: '#166534'
                }}>
                    {message}
                </p>
            )}

            {loading ? (
                <p>Loading users...</p>
            ) : (
                <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '1rem' }}>
                    <thead>
                        <tr style={{ background: '#f3f4f6', textAlign: 'left' }}>
                            <th style={{ padding: '0.75rem', borderBottom: '1px solid #e5e7eb' }}>Email</th>
                            <th style={{ padding: '0.75rem', borderBottom: '1px solid #e5e7eb' }}>Current Role</th>
                            <th style={{ padding: '0.75rem', borderBottom: '1px solid #e5e7eb' }}>Change Role</th>
                        </tr>
                    </thead>
                    <tbody>
                        {users.map((u) => (
                            <tr key={u.uid} style={{ borderBottom: '1px solid #f3f4f6' }}>
                                <td style={{ padding: '0.75rem' }}>{u.email}</td>
                                <td style={{ padding: '0.75rem' }}>
                                    <span style={{
                                        background: '#e0e7ff', color: '#3730a3',
                                        padding: '2px 8px', borderRadius: '999px', fontSize: '0.8rem'
                                    }}>
                                        {u.role}
                                    </span>
                                </td>
                                <td style={{ padding: '0.75rem' }}>
                                    {/* Don't let admin change their own role accidentally */}
                                    {u.uid !== user.uid ? (
                                        <select
                                            value={u.role}
                                            onChange={(e) => {
                                                if (e.target.value !== u.role) {
                                                    handleRoleChange(u.uid, e.target.value);
                                                }
                                            }}
                                            style={{ padding: '0.4rem', borderRadius: '4px', border: '1px solid #d1d5db' }}
                                        >
                                            <option value="student">Student</option>
                                            <option value="instructor">Instructor</option>
                                            <option value="admin">Admin</option>
                                        </select>
                                    ) : (
                                        <span style={{ color: '#9ca3af', fontSize: '0.85rem' }}>You (admin)</span>
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </div>
    );
}

export default AdminDashboard;