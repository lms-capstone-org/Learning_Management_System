import React, { useState, useEffect } from 'react';
import api from '../api';

function CommunityFeed({ currentUser }) {
  const [posts, setPosts] = useState([]);
  const [newPostContent, setNewPostContent] = useState("");
  const[commentInputs, setCommentInputs] = useState({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchPosts();
  },[]);

  const fetchPosts = async () => {
    try {
      const res = await api.get('/community/');
      setPosts(res.data);
    } catch (error) {
      console.error("Error fetching posts:", error);
    }
  };

  const handleCreatePost = async () => {
    if (!newPostContent.trim()) return;
    setLoading(true);
    try {
      await api.post('/community/', { content: newPostContent });
      setNewPostContent("");
      fetchPosts(); // Refresh feed
    } catch (error) {
      alert("Failed to create post.");
    } finally {
      setLoading(false);
    }
  };

  const handleAddComment = async (postId) => {
    const comment = commentInputs[postId];
    if (!comment || !comment.trim()) return;

    try {
      await api.post(`/community/${postId}/comments`, { content: comment });
      setCommentInputs({ ...commentInputs, [postId]: "" }); // Clear input
      fetchPosts(); // Refresh feed
    } catch (error) {
      alert("Failed to add comment.");
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <h2>🌍 Community Discussion</h2>

      {/* Create Post Box */}
      <div style={{ background: 'white', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', marginBottom: '30px' }}>
        <textarea
          placeholder="What's on your mind? Ask a question or share an insight..."
          value={newPostContent}
          onChange={(e) => setNewPostContent(e.target.value)}
          style={{ width: '100%', padding: '15px', borderRadius: '8px', border: '1px solid #cbd5e1', minHeight: '80px', resize: 'vertical', marginBottom: '10px', boxSizing: 'border-box' }}
        />
        <div style={{ textAlign: 'right' }}>
          <button
            onClick={handleCreatePost}
            disabled={loading || !newPostContent.trim()}
            style={{ background: '#4f46e5', color: 'white', padding: '10px 20px', border: 'none', borderRadius: '5px', cursor: 'pointer', fontWeight: 'bold' }}
          >
            {loading ? "Posting..." : "Post"}
          </button>
        </div>
      </div>

      {/* Feed List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {posts.length === 0 ? (
          <p style={{ textAlign: 'center', color: '#64748b' }}>No posts yet. Be the first to start a discussion!</p>
        ) : (
          posts.map((post) => (
            <div key={post.id} style={{ background: 'white', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>

              {/* Post Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '15px' }}>
                <strong style={{ color: '#0f172a' }}>@{post.author_username}</strong>
                <span style={{ fontSize: '12px', color: '#94a3b8' }}>
                  {post.created_at ? new Date(post.created_at).toLocaleString() : "Just now"}
                </span>
              </div>

              {/* Post Content */}
              <p style={{ color: '#334155', lineHeight: '1.6', marginBottom: '20px' }}>{post.content}</p>

              <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0', marginBottom: '15px' }} />

              {/* Comments Section */}
              <div style={{ background: '#f8fafc', padding: '15px', borderRadius: '8px' }}>
                <h4 style={{ margin: '0 0 10px 0', fontSize: '14px', color: '#475569' }}>Comments</h4>

                {post.comments?.length > 0 ? (
                  post.comments.map((comment, idx) => (
                    <div key={idx} style={{ marginBottom: '10px', fontSize: '14px' }}>
                      <strong style={{ color: '#4f46e5' }}>@{comment.author_username}: </strong>
                      <span style={{ color: '#334155' }}>{comment.content}</span>
                    </div>
                  ))
                ) : (
                  <p style={{ fontSize: '13px', color: '#94a3b8', margin: '0 0 10px 0' }}>No comments yet.</p>
                )}

                {/* Add Comment Input */}
                <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
                  <input
                    type="text"
                    placeholder="Write a comment..."
                    value={commentInputs[post.id] || ""}
                    onChange={(e) => setCommentInputs({ ...commentInputs, [post.id]: e.target.value })}
                    onKeyPress={(e) => e.key === 'Enter' && handleAddComment(post.id)}
                    style={{ flex: 1, padding: '8px 12px', borderRadius: '20px', border: '1px solid #cbd5e1', outline: 'none' }}
                  />
                  <button
                    onClick={() => handleAddComment(post.id)}
                    style={{ background: '#10b981', color: 'white', border: 'none', padding: '0 15px', borderRadius: '20px', cursor: 'pointer', fontSize: '12px', fontWeight: 'bold' }}
                  >
                    Reply
                  </button>
                </div>
              </div>

            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default CommunityFeed;