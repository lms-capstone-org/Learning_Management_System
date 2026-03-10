import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { jsPDF } from 'jspdf';
import api from '../api';

function StudentDashboard() {
  const [view, setView] = useState('catalog');
  const [courses, setCourses] = useState([]);
  const [userProfile, setUserProfile] = useState(null);

  // 🆕 Search & Category State
  const [searchQuery, setSearchQuery] = useState("");
  const [activeCategory, setActiveCategory] = useState("All");

  const[selectedCourse, setSelectedCourse] = useState(null);
  const [modules, setModules] = useState([]);
  const[activeModule, setActiveModule] = useState(null);
  const [aiData, setAiData] = useState(null);
  const [moduleMode, setModuleMode] = useState('learn');

  const [quizAnswers, setQuizAnswers] = useState({});
  const [quizSubmitted, setQuizSubmitted] = useState(false);

  const [chatMessages, setChatMessages] = useState([]);
  const[chatInput, setChatInput] = useState("");
  const [isChatting, setIsChatting] = useState(false);
  const [ttsLang, setTtsLang] = useState('en');
  const[isEmailing, setIsEmailing] = useState(false);

  useEffect(() => { fetchInitialData(); },[]);

  const fetchInitialData = async () => {
    try {
      const profileRes = await api.get('/courses/my-profile'); setUserProfile(profileRes.data);
      const catalogRes = await api.get('/courses/catalog'); setCourses(catalogRes.data);
    } catch (error) { console.error(error); }
  };

  const handleEnroll = async (courseId) => {
    try { await api.post(`/courses/${courseId}/enroll`); alert("Enrolled Successfully!"); fetchInitialData(); }
    catch (e) { alert("Error enrolling."); }
  };

  const openCourse = async (course) => {
    setSelectedCourse(course); setView('course');
    try {
      const modRes = await api.get(`/courses/${course.id}/modules`); setModules(modRes.data);
      if (modRes.data.length > 0) selectModule(modRes.data[0]);
    } catch (e) { console.error(e); }
  };

  const selectModule = async (module) => {
    setActiveModule(module); setAiData(null); setQuizAnswers({}); setQuizSubmitted(false); setModuleMode('learn'); setChatMessages([]); setTtsLang('en');
    try { const aiRes = await api.get(`/ai/module/${module.id}`); setAiData(aiRes.data); }
    catch (e) { console.error(e); }
  };

  const handleQuizChange = (questionId, optionKey) => {
    if (quizSubmitted) return; setQuizAnswers(prev => ({ ...prev, [questionId]: optionKey }));
  };

  const submitQuiz = async () => {
    let correct = 0;
    aiData.questions.forEach((q) => {
      if (quizAnswers[q.question_id] === q.correct_answer) correct += 1;
    });

    setQuizSubmitted(true);
    const passScore = Math.ceil(aiData.questions.length * 0.7); // Keeping your 70% rule
    const passed = correct >= passScore;

    try {
      // 1. Send the attempt to the backend regardless of pass/fail
      await api.post(`/courses/${selectedCourse.id}/modules/${activeModule.id}/quiz-attempt`, {
        score: correct,
        total_questions: aiData.questions.length,
        passed: passed
      });

      // 2. Refresh the user profile data to update the progress bar if they passed
      fetchInitialData();

      // 3. Show the appropriate alert to the user
      if (passed) {
        alert(`🎉 Passed! Score: ${correct}/${aiData.questions.length}. Next module unlocked!`);
      } else {
        alert(`You scored ${correct}/${aiData.questions.length}. Study the feedback and try again!`);
      }
    } catch (e) {
      console.error("Error saving quiz attempt:", e);
      alert("Failed to save quiz results. Please check your connection.");
    }
  };

  const handleSendMessage = async () => {
    if (!chatInput.trim()) return;
    const userMsg = { role: 'user', content: chatInput }; setChatMessages(prev =>[...prev, userMsg]); setChatInput(""); setIsChatting(true);
    try {
      const res = await api.post('/ai/chat', { course_id: selectedCourse.id, question: userMsg.content });
      setChatMessages(prev =>[...prev, { role: 'ai', content: res.data.answer }]);
    } catch (e) { setChatMessages(prev =>[...prev, { role: 'ai', content: 'Connection error.' }]); }
    finally { setIsChatting(false); }
  };

  const isModuleUnlocked = (index) => {
    if (index === 0) return true;
    const enrollment = userProfile?.enrollments?.[selectedCourse.id]; if (!enrollment) return false;
    return enrollment.completed_modules.includes(modules[index - 1].id);
  };

  const calculateProgress = () => {
    if (!modules || modules.length === 0) return 0;
    const completedCount = userProfile?.enrollments?.[selectedCourse?.id]?.completed_modules?.length || 0;
    return Math.min(Math.round((completedCount / modules.length) * 100), 100);
  };

  const handleGraduate = async () => {
    setIsEmailing(true);
    try {
      await api.post(`/courses/${selectedCourse.id}/graduate`);
      alert("🎉 Congratulations! Your certificate is being generated and sent to your email.");
    } catch (e) {
      console.error(e);
      alert("Failed to send certificate. Please try again.");
    } finally {
      setIsEmailing(false);
    }
  };

  // 🆕 FILTER LOGIC FOR SEARCH & CATEGORY
  const filteredCourses = courses.filter(course => {
    const courseCat = course.category || "GenAi"; // Fallback for old courses
    const matchesSearch = course.title.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = activeCategory === "All" || courseCat === activeCategory;
    return matchesSearch && matchesCategory;
  });

  if (view === 'catalog') {
    return (
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2>📚 Course Catalog</h2>

          {/* 🆕 SEARCH BAR */}
          <input
            type="text"
            placeholder="🔍 Search for a course..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            style={{ padding: '10px 15px', borderRadius: '25px', border: '1px solid #cbd5e1', width: '300px', outline: 'none' }}
          />
        </div>

        {/* 🆕 CATEGORY FILTER PILLS */}
        <div style={{ display: 'flex', gap: '10px', marginTop: '15px', marginBottom: '25px' }}>
          {['All', 'GenAi', 'Process Mining (PI)', 'Business Analyst (BA)'].map(cat => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              style={{
                padding: '8px 16px', borderRadius: '20px', border: 'none', cursor: 'pointer', fontWeight: 'bold', transition: 'all 0.2s',
                background: activeCategory === cat ? '#4f46e5' : '#e2e8f0',
                color: activeCategory === cat ? 'white' : '#475569'
              }}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* GRID RENDER (Mapped over filteredCourses instead of courses) */}
        {filteredCourses.length === 0 ? (
          <p style={{ textAlign: 'center', color: '#64748b', marginTop: '50px' }}>No courses match your search.</p>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '20px' }}>
            {filteredCourses.map(course => {
              const isEnrolled = userProfile?.enrollments?.[course.id];
              return (
                <div key={course.id} style={{ background: 'white', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                  <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#4f46e5', textTransform: 'uppercase', marginBottom: '5px' }}>{course.category || "GenAi"}</div>
                  <h3 style={{ margin: '0 0 10px 0' }}>{course.title}</h3>
                  {/* 🆕 Add Description with line clamping to keep cards uniform */}
                  <p style={{ fontSize: '14px', color: '#64748b', marginBottom: '15px', display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                    {course.description || "No description provided for this course."}
                  </p>

                  {isEnrolled ? (
                    <button onClick={() => openCourse(course)} style={{ background: '#4f46e5', color: 'white', padding: '10px 15px', border: 'none', borderRadius: '5px', cursor: 'pointer', width: '100%' }}>Continue Learning</button>
                  ) : (
                    <button onClick={() => handleEnroll(course.id)} style={{ background: '#10b981', color: 'white', padding: '10px 15px', border: 'none', borderRadius: '5px', cursor: 'pointer', width: '100%' }}>Enroll Now</button>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    );
  }

  // --- THE REST OF THE RENDER CODE REMAINS UNCHANGED FOR COURSE VIEW ---
  const progress = calculateProgress();
  return (
    <div style={{ display: 'flex', gap: '20px' }}>
      {/* SIDEBAR */}
      <div style={{ width: '300px', background: 'white', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', height: 'fit-content' }}>
        <button onClick={() => setView('catalog')} style={{ marginBottom: '20px', background: '#e2e8f0', border: 'none', padding: '8px 12px', borderRadius: '5px', cursor: 'pointer', width: '100%' }}>← Back to Catalog</button>

        <h3>{selectedCourse?.title}</h3>
        {/* 🆕 Show description in sidebar */}
        <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '20px', lineHeight: '1.5' }}>
          {selectedCourse?.description || "No description provided."}
        </p>
        {/* PROGRESS BAR */}
        <div style={{ marginBottom: '20px', background: '#f8fafc', padding: '15px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', color: '#64748b', marginBottom: '8px', fontWeight: 'bold' }}>
            <span>Progress</span><span style={{ color: progress === 100 ? '#10b981' : '#4f46e5' }}>{progress}%</span>
          </div>
          <div style={{ width: '100%', background: '#cbd5e1', borderRadius: '10px', height: '8px', overflow: 'hidden' }}>
            <div style={{ width: `${progress}%`, background: progress === 100 ? '#10b981' : '#4f46e5', height: '100%', transition: 'width 0.5s' }}></div>
          </div>
          {progress === 100 && (
            <div style={{ textAlign: 'center', marginTop: '15px' }}>
               <div style={{ fontSize: '13px', color: '#10b981', fontWeight: 'bold', marginBottom: '10px' }}>🎉 Course Completed!</div>
               {/* 🆕 Updated Button */}
               <button
                  onClick={handleGraduate}
                  disabled={isEmailing}
                  style={{ background: isEmailing ? '#94a3b8' : '#4f46e5', color: 'white', border: 'none', padding: '10px 15px', borderRadius: '5px', cursor: isEmailing ? 'not-allowed' : 'pointer', fontSize: '13px', fontWeight: 'bold' }}
                >
                  {isEmailing ? "⏳ Sending Email..." : "📧 Email My Certificate"}
                </button>
            </div>
          )}
        </div>
        <hr style={{ margin: '15px 0' }} />
        {modules.map((mod, index) => {
          const unlocked = isModuleUnlocked(index); const isCompleted = userProfile?.enrollments?.[selectedCourse.id]?.completed_modules?.includes(mod.id);
          return (
            <div key={mod.id} onClick={() => unlocked && selectModule(mod)} style={{ padding: '12px', marginBottom: '10px', borderRadius: '5px', cursor: unlocked ? 'pointer' : 'not-allowed', background: activeModule?.id === mod.id ? '#e0e7ff' : '#f9fafb', opacity: unlocked ? 1 : 0.6 }}>
              <div style={{ fontWeight: 'bold' }}>{index + 1}. {mod.title}</div>
              <div style={{ fontSize: '12px', marginTop: '5px' }}>{isCompleted ? '✅ Completed' : unlocked ? '🔓 Unlocked' : '🔒 Locked'}</div>
            </div>
          );
        })}
      </div>

      {/* MAIN CONTENT */}
      <div style={{ flex: 1, background: 'white', padding: '30px', borderRadius: '10px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
        {activeModule && moduleMode === 'learn' && (
          <div className="fade-in">
            <h2>{activeModule.title}</h2>
            <video controls src={activeModule.video_blob_url} style={{ width: '100%', maxHeight: '400px', borderRadius: '10px', backgroundColor: 'black' }} />
            <div style={{ display: 'flex', gap: '20px', marginTop: '20px' }}>
              <div style={{ flex: 1 }}>
                {aiData?.status === 'completed' ? (
                  <div style={{ padding: '20px', background: '#f8fafc', borderLeft: '4px solid #0ea5e9', borderRadius: '0 10px 10px 0' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                      <h3 style={{ margin: 0, color: '#0284c7' }}>✨ AI Summary</h3>
                      <select value={ttsLang} onChange={(e) => setTtsLang(e.target.value)} style={{ padding: '5px', borderRadius: '5px', border: '1px solid #cbd5e1' }}>
                        <option value="en">English</option><option value="es">Spanish</option><option value="fr">French</option><option value="de">German</option><option value="hi">Hindi</option><option value="ja">Japanese</option><option value="zh-Hans">Chinese</option>
                      </select>
                    </div>
                    <audio controls style={{ width: '100%', height: '35px', marginBottom: '15px' }} src={`http://localhost:8000/ai/tts/stream?module_id=${activeModule.id}&lang=${ttsLang}`} />
                    <div style={{ fontSize: '14px', lineHeight: '1.6', color: '#334155' }}><ReactMarkdown>{aiData.summary_markdown}</ReactMarkdown></div>
                  </div>
                ) : <div style={{ padding: '20px', background: '#fffbeb', color: '#b45309', borderRadius: '10px' }}>⏳ AI is analyzing this video...</div>}
              </div>
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', border: '1px solid #e2e8f0', borderRadius: '10px' }}>
                <div style={{ background: '#1e293b', color: 'white', padding: '10px 15px', fontWeight: 'bold' }}>💬 Course AI Tutor</div>
                <div style={{ flex: 1, minHeight: '250px', maxHeight: '250px', overflowY: 'auto', padding: '15px', background: '#f1f5f9' }}>
                  {chatMessages.map((msg, i) => (
                    <div key={i} style={{ marginBottom: '10px', textAlign: msg.role === 'user' ? 'right' : 'left' }}>
                      <div style={{ display: 'inline-block', padding: '10px 14px', borderRadius: '12px', maxWidth: '85%', background: msg.role === 'user' ? '#4f46e5' : 'white', color: msg.role === 'user' ? 'white' : '#334155', textAlign: 'left', border: msg.role === 'user' ? 'none' : '1px solid #e2e8f0', fontSize: '14px' }}>
                         {msg.role === 'user' ? msg.content : <ReactMarkdown>{msg.content}</ReactMarkdown>}
                      </div>
                    </div>
                  ))}
                  {isChatting && <div style={{ color: '#64748b', fontSize: '12px' }}>AI is typing...</div>}
                </div>
                <div style={{ display: 'flex', padding: '10px', background: 'white', borderTop: '1px solid #e2e8f0' }}>
                  <input type="text" value={chatInput} onChange={e => setChatInput(e.target.value)} onKeyPress={e => e.key === 'Enter' && handleSendMessage()} placeholder="Ask a question..." style={{ flex: 1, padding: '10px', border: '1px solid #cbd5e1', borderRadius: '5px' }} />
                  <button onClick={handleSendMessage} disabled={isChatting} style={{ marginLeft: '10px', background: '#4f46e5', color: 'white', border: 'none', padding: '0 15px', borderRadius: '5px', cursor: 'pointer' }}>Send</button>
                </div>
              </div>
            </div>
            <div style={{ marginTop: '30px', textAlign: 'center', padding: '20px', borderTop: '1px dashed #cbd5e1' }}>
              <button onClick={() => setModuleMode('quiz')} style={{ background: '#10b981', color: 'white', padding: '15px 30px', fontSize: '18px', fontWeight: 'bold', border: 'none', borderRadius: '8px', cursor: 'pointer' }}>Proceed to Module Quiz ➡️</button>
            </div>
          </div>
        )}
        {activeModule && moduleMode === 'quiz' && (
          <div className="fade-in" style={{ maxWidth: '800px', margin: '0 auto' }}>
            <button onClick={() => setModuleMode('learn')} style={{ marginBottom: '20px', background: '#e2e8f0', border: 'none', padding: '8px 15px', borderRadius: '5px', cursor: 'pointer' }}>← Return to Video</button>
            <h2 style={{ textAlign: 'center' }}>🧠 Concept Check</h2>
            {aiData.questions.map((q, idx) => {
              const sortedOptions = Object.entries(q.options).sort(([keyA],[keyB]) => keyA.localeCompare(keyB));
              return (
                <div key={q.question_id} style={{ marginBottom: '20px', padding: '25px', border: '1px solid #e2e8f0', borderRadius: '10px', background: '#f8fafc' }}>
                  <p style={{ fontWeight: 'bold', marginBottom: '15px' }}>{idx + 1}. {q.question}</p>
                  {sortedOptions.map(([key, value]) => (
                    <div key={key} style={{ marginBottom: '10px' }}>
                      <label style={{ cursor: 'pointer', display: 'flex', alignItems: 'flex-start' }}>
                        <input type="radio" name={q.question_id} value={key} checked={quizAnswers[q.question_id] === key} onChange={() => handleQuizChange(q.question_id, key)} disabled={quizSubmitted} style={{ marginRight: '10px' }} />
                        <span><strong>{key}.</strong> {value}</span>
                      </label>
                    </div>
                  ))}
                  {quizSubmitted && (
                    <div style={{ marginTop: '15px', padding: '15px', borderRadius: '8px', background: quizAnswers[q.question_id] === q.correct_answer ? '#dcfce7' : '#fee2e2' }}>
                      <strong style={{ color: quizAnswers[q.question_id] === q.correct_answer ? '#166534' : '#991b1b' }}>{quizAnswers[q.question_id] === q.correct_answer ? '✅ Correct!' : `❌ Incorrect (Correct was ${q.correct_answer})`}</strong>
                      <p style={{ margin: 0, fontSize: '14px', marginTop: '5px' }}>{q.explanation}</p>
                    </div>
                  )}
                </div>
              );
            })}
            <div style={{ textAlign: 'center', marginTop: '40px' }}>
              {!quizSubmitted ? (
                <button onClick={submitQuiz} disabled={Object.keys(quizAnswers).length !== aiData.questions.length} style={{ background: Object.keys(quizAnswers).length === aiData.questions.length ? '#4f46e5' : '#94a3b8', color: 'white', padding: '15px 40px', fontSize: '18px', border: 'none', borderRadius: '8px', cursor: Object.keys(quizAnswers).length === aiData.questions.length ? 'pointer' : 'not-allowed' }}>Submit Quiz</button>
              ) : (
                <button onClick={() => { setQuizSubmitted(false); setQuizAnswers({}); }} style={{ background: '#64748b', color: 'white', padding: '12px 25px', fontSize: '16px', border: 'none', borderRadius: '8px', cursor: 'pointer' }}>Try Again</button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default StudentDashboard;