import React, { useState, useEffect } from 'react';
import api from '../api';

function InstructorDashboard() {
  const [view, setView] = useState('list');
  const[courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(false);

  // 🆕 Added Category State
  const [newCourseTitle, setNewCourseTitle] = useState("");
  const[newCourseCategory, setNewCourseCategory] = useState("GenAi");
  const[newCourseDescription, setNewCourseDescription] = useState("");

  const [activeCourse, setActiveCourse] = useState(null);
  const [modules, setModules] = useState([]);
  const[analyticsData, setAnalyticsData] = useState(null);

  const [moduleFormTitle, setModuleFormTitle] = useState("");
  const [moduleFile, setModuleFile] = useState(null);
  const[editingModuleId, setEditingModuleId] = useState(null);
  const [isUploading, setIsUploading] = useState(false);

  const fetchCourses = async () => {
    try {
      const res = await api.get("/courses/my-courses");
      setCourses(res.data);
    } catch (error) { console.error(error); }
  };

  const fetchModules = async (courseId) => {
    try {
      const res = await api.get(`/courses/${courseId}/modules`);
      setModules(res.data);
    } catch (error) { console.error(error); }
  };

  const fetchAnalytics = async (courseId) => {
    try {
      const res = await api.get(`/courses/${courseId}/analytics`);
      setAnalyticsData(res.data);
    } catch (error) { console.error(error); }
  };

  useEffect(() => { fetchCourses(); },[]);

  const handleCreateCourse = async () => {
    // 🆕 Require description as well
    if (!newCourseTitle || !newCourseDescription) return;
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("title", newCourseTitle);
      formData.append("category", newCourseCategory);
      formData.append("description", newCourseDescription); // 🆕 Send description to backend

      await api.post("/courses/", formData);
      setNewCourseTitle("");
      setNewCourseCategory("GenAi");
      setNewCourseDescription(""); // 🆕 Reset field
      fetchCourses();
    } catch (error) { alert("Failed to create course."); }
    finally { setLoading(false); }
  };

  const handleDeleteCourse = async (courseId) => {
    if (!window.confirm("Are you sure you want to delete this entire course?")) return;
    try { await api.delete(`/courses/${courseId}`); fetchCourses(); }
    catch (error) { alert("Failed to delete course."); }
  };

  const openCourse = (course) => {
    setActiveCourse(course); fetchModules(course.id); setView('courseDetail'); resetModuleForm();
  };

  const openAnalytics = (course) => {
    setActiveCourse(course); setAnalyticsData(null); fetchAnalytics(course.id); setView('analytics');
  };

  const resetModuleForm = () => {
    setModuleFormTitle(""); setModuleFile(null); setEditingModuleId(null);
    const fileInput = document.getElementById('module-file-input');
    if (fileInput) fileInput.value = "";
  };

  const handleSaveModule = async () => {
    if (!moduleFormTitle && !editingModuleId) return;
    setIsUploading(true);
    try {
      const formData = new FormData();
      if (moduleFormTitle) formData.append("title", moduleFormTitle);
      if (moduleFile) formData.append("file", moduleFile);

      if (editingModuleId) {
        await api.put(`/courses/${activeCourse.id}/modules/${editingModuleId}`, formData, { headers: { 'Content-Type': 'multipart/form-data' } });
        alert(moduleFile ? "Module updated! AI is processing." : "Title updated!");
      } else {
        if (!moduleFile) return alert("Please select a video.");
        await api.post(`/courses/${activeCourse.id}/modules`, formData, { headers: { 'Content-Type': 'multipart/form-data' } });
        alert("Module added! AI is generating quiz and summary.");
      }
      resetModuleForm(); fetchModules(activeCourse.id);
    } catch (error) { alert("Failed to save."); }
    finally { setIsUploading(false); }
  };

  const handleDeleteModule = async (moduleId) => {
    if (!window.confirm("Delete this module?")) return;
    try { await api.delete(`/courses/${activeCourse.id}/modules/${moduleId}`); fetchModules(activeCourse.id); }
    catch (error) {}
  };

  const startEditModule = (mod) => {
    setEditingModuleId(mod.id); setModuleFormTitle(mod.title); setModuleFile(null);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  if (view === 'analytics') {
    return (
      <div>
        <button onClick={() => setView('list')} style={{ background: '#ccc', padding: '8px 15px', borderRadius: '5px', border: 'none', cursor: 'pointer', marginBottom: '20px' }}>← Back to Courses</button>
        <h2>📊 Analytics: {activeCourse.title}</h2>
        <div style={{ background: 'white', padding: '30px', borderRadius: '10px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
          <p><strong>Total Modules in Course:</strong> {analyticsData?.total_modules || 0}</p>
          <hr style={{ margin: '20px 0' }} />
          <h3>Enrolled Students</h3>
          {!analyticsData ? <p>Loading analytics...</p> : analyticsData.students.length === 0 ? <p style={{ color: 'gray' }}>No students enrolled yet.</p> : (
            <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '10px' }}>
              <thead>
                <tr style={{ background: '#f8fafc', borderBottom: '2px solid #e2e8f0', textAlign: 'left' }}>
                  <th style={{ padding: '12px' }}>Student Email</th><th style={{ padding: '12px' }}>Modules Completed</th><th style={{ padding: '12px', width: '200px' }}>Progress</th>
                </tr>
              </thead>
              <tbody>
                {analyticsData.students.map((student, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid #e2e8f0' }}>
                    <td style={{ padding: '12px' }}>{student.email}</td><td style={{ padding: '12px' }}>{student.completed_modules} / {analyticsData.total_modules}</td>
                    <td style={{ padding: '12px' }}>
                      <div style={{ width: '100%', background: '#cbd5e1', borderRadius: '10px', height: '10px' }}><div style={{ width: `${student.progress}%`, background: student.progress === 100 ? '#10b981' : '#4f46e5', height: '100%', borderRadius: '10px' }}></div></div>
                      <span style={{ fontSize: '12px', color: '#64748b' }}>{student.progress}%</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    );
  }

  if (view === 'courseDetail') {
    return (
      <div>
        <button onClick={() => setView('list')} style={{ background: '#ccc', padding: '8px 15px', borderRadius: '5px', border: 'none', cursor: 'pointer', marginBottom: '20px' }}>← Back to Courses</button>
        <h2>{activeCourse.title} - Module Management</h2>
        <div style={{ display: 'flex', gap: '30px', marginTop: '20px' }}>
          <div style={{ flex: '1', background: 'white', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', alignSelf: 'start' }}>
            <h3>{editingModuleId ? "✏️ Edit Module" : "➕ Add New Module"}</h3>
            <input type="text" value={moduleFormTitle} onChange={(e) => setModuleFormTitle(e.target.value)} placeholder="Module Title" style={{ width: '100%', padding: '10px', marginBottom: '15px', borderRadius: '5px', border: '1px solid #ccc' }} />
            <input id="module-file-input" type="file" accept="video/mp4" onChange={(e) => setModuleFile(e.target.files[0])} style={{ marginBottom: '15px', width: '100%' }} />
            <div style={{ display: 'flex', gap: '10px' }}>
              <button onClick={handleSaveModule} disabled={isUploading} style={{ flex: 1, background: '#4f46e5', color: 'white', padding: '10px', border: 'none', borderRadius: '5px', cursor: 'pointer' }}>{isUploading ? "Uploading..." : editingModuleId ? "Save Changes" : "Upload Module"}</button>
              {editingModuleId && <button onClick={resetModuleForm} style={{ background: '#ef4444', color: 'white', padding: '10px', border: 'none', borderRadius: '5px' }}>Cancel</button>}
            </div>
          </div>
          <div style={{ flex: '2', background: 'white', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
            <h3>Current Modules</h3>
            {modules.map((mod, index) => (
              <div key={mod.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '15px', borderBottom: '1px solid #eee' }}>
                <div><strong>{index + 1}. {mod.title}</strong><div style={{ fontSize: '13px', color: mod.status === 'completed' ? 'green' : 'orange' }}>Status: {mod.status === 'completed' ? 'Ready' : 'AI Processing...'}</div></div>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <button onClick={() => startEditModule(mod)} style={{ background: '#eab308', color: 'white', border: 'none', padding: '8px 12px', borderRadius: '5px', cursor: 'pointer' }}>Edit</button>
                  <button onClick={() => handleDeleteModule(mod.id)} style={{ background: '#ef4444', color: 'white', border: 'none', padding: '8px 12px', borderRadius: '5px', cursor: 'pointer' }}>Delete</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '30px' }}>
        <h2 style={{ margin: 0 }}>👨‍🏫 My Courses</h2>

        {/* 🆕 UPDATED COURSE CREATION UI */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', width: '400px' }}>
          <div style={{ display: 'flex', gap: '10px' }}>
            <input type="text" placeholder="New Course Title" value={newCourseTitle} onChange={(e) => setNewCourseTitle(e.target.value)} style={{ padding: '10px', borderRadius: '5px', border: '1px solid #ccc', flex: 1 }} />
            <select value={newCourseCategory} onChange={(e) => setNewCourseCategory(e.target.value)} style={{ padding: '10px', borderRadius: '5px', border: '1px solid #ccc' }}>
              <option value="GenAi">GenAi</option>
              <option value="Process Mining (PI)">Process Mining (PI)</option>
              <option value="Business Analyst (BA)">Business Analyst (BA)</option>
            </select>
          </div>
          <textarea
            placeholder="Enter a short course description..."
            value={newCourseDescription}
            onChange={(e) => setNewCourseDescription(e.target.value)}
            style={{ padding: '10px', borderRadius: '5px', border: '1px solid #ccc', resize: 'vertical', minHeight: '60px' }}
          />
          <button onClick={handleCreateCourse} disabled={loading || !newCourseTitle || !newCourseDescription} style={{ background: '#10b981', color: 'white', padding: '10px', border: 'none', borderRadius: '5px', cursor: 'pointer', fontWeight: 'bold' }}>+ Create Course</button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
        {courses.map(course => (
          <div key={course.id} style={{ background: 'white', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#4f46e5', textTransform: 'uppercase', marginBottom: '5px' }}>{course.category || "GenAi"}</div>
              <h3 style={{ margin: '0 0 10px 0' }}>{course.title}</h3>
            </div>
            <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
              <button onClick={() => openCourse(course)} style={{ flex: '2', background: '#4f46e5', color: 'white', padding: '10px', border: 'none', borderRadius: '5px', cursor: 'pointer' }}>Modules</button>
              <button onClick={() => openAnalytics(course)} style={{ flex: '1', background: '#eab308', color: 'white', padding: '10px', border: 'none', borderRadius: '5px', cursor: 'pointer' }}>📊</button>
              <button onClick={() => handleDeleteCourse(course.id)} style={{ background: '#ef4444', color: 'white', padding: '10px', border: 'none', borderRadius: '5px', cursor: 'pointer' }}>🗑️</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default InstructorDashboard;