"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { ApiService, Thread, Message } from "../lib/api";

const EXAMPLE_QUESTIONS = [
  "What is the expense ratio of HDFC Large Cap Fund?",
  "What is the lock-in period for ELSS?",
  "How do I download my capital gains statement?",
];

export default function Home() {
  const [threads, setThreads] = useState<Thread[]>([]);
  const [currentThreadId, setCurrentThreadId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadThreads();
  }, []);

  useEffect(() => {
    if (currentThreadId) {
      loadMessages(currentThreadId);
    } else {
      setMessages([]);
    }
  }, [currentThreadId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const loadThreads = async () => {
    try {
      const data = await ApiService.getThreads();
      setThreads(data);
    } catch (e) {
      console.error(e);
    }
  };

  const loadMessages = async (threadId: string) => {
    try {
      const msgs = await ApiService.getThreadMessages(threadId);
      setMessages(msgs);
    } catch (e) {
      console.error(e);
    }
  };

  const handleNewChat = async () => {
    try {
      setIsLoading(true);
      const threadId = await ApiService.createThread();
      setCurrentThreadId(threadId);
      await loadThreads();
    } catch (e) {
      console.error(e);
      alert("Failed to create chat");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteChat = async () => {
    if (!currentThreadId) return;
    try {
      setIsLoading(true);
      await ApiService.deleteThread(currentThreadId);
      setCurrentThreadId(null);
      await loadThreads();
    } catch (e) {
      console.error(e);
      alert("Failed to delete chat");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = async (text: string) => {
    if (!text.trim() || isLoading) return;
    
    const userMsg: Message = { role: "user", text: text.trim() };
    setMessages(prev => [...prev, userMsg]);
    setInputValue("");
    setIsLoading(true);

    try {
      const { thread_id } = await ApiService.sendMessage(text, currentThreadId);
      if (thread_id !== currentThreadId) {
        setCurrentThreadId(thread_id);
        await loadThreads();
      } else {
        await loadMessages(thread_id);
      }
    } catch (e: unknown) {
      console.error(e);
      const errorMessage = e instanceof Error ? e.message : "Failed to send message";
      alert(errorMessage);
      // Remove the optimistically added message if failed
      setMessages((prev) => prev.filter((m) => m !== userMsg));
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend(inputValue);
    }
  };

  return (
    <div className="layout-container animate-fade-in">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ background: 'var(--brand-primary)', color: '#000', padding: '4px', borderRadius: '4px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
            </div>
            <div>
              <h2 className="sidebar-title" style={{ margin: 0, fontSize: '1.25rem', color: 'var(--brand-primary)' }}>MF Assistant</h2>
              <div style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', letterSpacing: '1px' }}>FAQ CONSOLE</div>
            </div>
          </div>
        </div>
        <div className="sidebar-content">
          <h3 style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "8px", textTransform: "uppercase", letterSpacing: "1px" }}>Threads</h3>
          {threads.length === 0 ? (
            <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", textAlign: "center", marginTop: "20px" }}>No previous chats</p>
          ) : (
            threads.map((t) => (
              <div 
                key={t.thread_id} 
                className={`thread-item ${t.thread_id === currentThreadId ? "active" : ""}`}
                onClick={() => setCurrentThreadId(t.thread_id)}
              >
                {t.title || "Untitled Chat"}
              </div>
            ))
          )}
        </div>
        <div className="sidebar-footer" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <button className="btn btn-primary" onClick={handleNewChat} disabled={isLoading} style={{ justifyContent: 'flex-start' }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
            New Inquiry
          </button>
          <button className="btn" onClick={handleDeleteChat} disabled={!currentThreadId || isLoading} style={{ justifyContent: 'flex-start', color: 'var(--text-secondary)', border: 'none', background: 'transparent' }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
            Delete Current
          </button>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="main-area">
        <div className="header-banner" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>⚠️ Facts-only. No investment advice.</span>
          <div style={{ display: 'flex', gap: '16px' }}>
            <Link href="/funds" style={{ textDecoration: 'none', color: 'var(--bg-primary)', backgroundColor: 'var(--brand-primary)', padding: '4px 12px', borderRadius: '4px', fontSize: '0.85rem', fontWeight: 600 }}>
              Scheme Page
            </Link>
            <Link href="/sources" style={{ textDecoration: 'none', color: 'var(--bg-primary)', backgroundColor: 'var(--brand-primary)', padding: '4px 12px', borderRadius: '4px', fontSize: '0.85rem', fontWeight: 600 }}>
              Source Library
            </Link>
          </div>
        </div>
        
        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="empty-state animate-fade-in">
              <h1 style={{ background: 'none', WebkitTextFillColor: 'var(--text-primary)', color: 'var(--text-primary)' }}>Mutual Fund Assistant</h1>
              <p>Inquire about assets, risk, or market data...</p>
              
              <div className="example-questions">
                {EXAMPLE_QUESTIONS.map((q, idx) => (
                  <div key={idx} className="example-card" onClick={() => handleSend(q)}>
                    {q}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="messages-list">
              {messages.map((msg, idx) => (
                <div key={idx} className={`message ${msg.role === "user" ? "message-user" : "message-assistant"}`}>
                  <div className="message-bubble">
                     {/* Split by newline and render */}
                    {msg.text.split("\n").map((line, i) => (
                      <span key={i}>
                        {line}
                        <br />
                      </span>
                    ))}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="message message-assistant">
                  <div className="message-bubble" style={{ opacity: 0.7, fontStyle: "italic" }}>
                    Give me just a moment while I gather the verified facts for you! I'm expanding my knowledge base every single day...
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        <div className="chat-input-container">
          <div className="chat-input-wrapper">
            <input 
              type="text" 
              className="chat-input" 
              placeholder="Inquire about assets, risk, or market data..." 
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
            />
            <button 
              className="chat-submit-btn" 
              onClick={() => handleSend(inputValue)}
              disabled={!inputValue.trim() || isLoading}
            >
              {isLoading ? (
                <span style={{ fontSize: "12px", animation: "fadeIn 1s infinite alternate" }}>...</span>
              ) : (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
              )}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
