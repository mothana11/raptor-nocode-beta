import React, { useEffect, useState, useRef } from "react";
import axios from "axios";
import AuthModal from "./AuthModal";

// TypeScript declarations for Speech Recognition API
declare global {
  interface Window {
    SpeechRecognition: typeof SpeechRecognition;
    webkitSpeechRecognition: typeof SpeechRecognition;
  }
}

interface SpeechRecognitionEvent extends Event {
  resultIndex: number;
  results: SpeechRecognitionResultList;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start(): void;
  stop(): void;
  onstart: ((this: SpeechRecognition, ev: Event) => any) | null;
  onend: ((this: SpeechRecognition, ev: Event) => any) | null;
  onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => any) | null;
  onerror: ((this: SpeechRecognition, ev: SpeechRecognitionErrorEvent) => any) | null;
}

declare var SpeechRecognition: {
  prototype: SpeechRecognition;
  new(): SpeechRecognition;
};

interface Message {
  from: "user" | "agent";
  text: string;
  timestamp?: Date;
  attachments?: {
    type: 'image' | 'file';
    name: string;
    url: string;
    size?: number;
  }[];
}

interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  nationality?: string;
  is_demo_user: boolean;
}

const Chat: React.FC = () => {
  // Authentication state - SIMPLIFIED
  const [user, setUser] = useState<User | null>(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [attachments, setAttachments] = useState<File[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // SINGLE useEffect for authentication - NO MORE CONFLICTS
  useEffect(() => {
    const initAuth = async () => {
      try {
        const token = localStorage.getItem('auth_token');
        const userData = localStorage.getItem('user_data');
        
        console.log('🔍 Auth check:', { hasToken: !!token, hasUserData: !!userData });
        
        if (token && userData) {
          const parsedUser = JSON.parse(userData);
          
          // Test the token by making a quick API call
          try {
            const response = await axios.get('http://localhost:8000/auth/me', {
              headers: { Authorization: `Bearer ${token}` }
            });
            
            console.log('✅ Token is valid, user authenticated:', response.data.email);
            setUser(parsedUser);
            axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
            setShowAuthModal(false);
            
          } catch (tokenError: any) {
            console.log('❌ Token is invalid/expired, clearing auth:', tokenError.response?.status);
            // Token is invalid, clear everything and force re-login
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user_data');
            delete axios.defaults.headers.common['Authorization'];
            setUser(null);
            setShowAuthModal(true);
          }
        } else {
          setUser(null);
          setShowAuthModal(true);
          console.log('❌ No authentication found');
        }
      } catch (error) {
        console.error('Auth error:', error);
        setUser(null);
        setShowAuthModal(true);
      } finally {
        setAuthChecked(true);
      }
    };
    
    initAuth();
  }, []); // Only run once

  const handleAuthSuccess = (userData: User, token: string) => {
    localStorage.setItem('auth_token', token);
    localStorage.setItem('user_data', JSON.stringify(userData));
    setUser(userData);
    setShowAuthModal(false);
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    
    // Welcome message only for first time
    if (!userData.is_demo_user && messages.length === 0) {
      setMessages([{
        from: "agent",
        text: `Welcome ${userData.first_name}! I'm your personal travel assistant ready to help with your travel needs.`,
        timestamp: new Date()
      }]);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_data');
    setUser(null);
    setShowAuthModal(true);
    delete axios.defaults.headers.common['Authorization'];
    setMessages([]);
    setConversationId(null);
  };

  // Voice recording setup
  const startRecording = async () => {
    try {
      // Try to use Web Speech API first (better for speech-to-text)
      if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';
        
        recognition.onstart = () => {
          setIsRecording(true);
        };
        
        recognition.onresult = (event) => {
          let transcript = '';
          for (let i = event.resultIndex; i < event.results.length; i++) {
            if (event.results[i].isFinal) {
              transcript += event.results[i][0].transcript;
            }
          }
          if (transcript) {
            setInput(prev => prev + transcript + ' ');
          }
        };
        
        recognition.onerror = (event) => {
          console.error('Speech recognition error:', event.error);
          setIsRecording(false);
          alert('Speech recognition error. Please try again.');
        };
        
        recognition.onend = () => {
          setIsRecording(false);
        };
        
        recognition.start();
        return;
      }
      
      // Fallback to MediaRecorder for audio recording
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        await processAudioInput(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Could not access microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    // Stop speech recognition if it's running
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      // The recognition will stop automatically
      setIsRecording(false);
      return;
    }
    
    // Stop MediaRecorder
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const processAudioInput = async (audioBlob: Blob) => {
    // For MediaRecorder fallback - in a real app, you'd send this to a speech-to-text service
    setInput(prev => prev + "[Audio recorded - would be transcribed by speech service] ");
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    setAttachments(prev => [...prev, ...files]);
  };

  const removeAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const sendMessage = async () => {
    const trimmed = input.trim();
    if (!trimmed && attachments.length === 0) return;

    console.log('📤 Sending message - User state check:');
    console.log('- user:', !!user, user?.email);
    console.log('- authToken:', !!localStorage.getItem('auth_token'));
    console.log('- axios header:', axios.defaults.headers.common['Authorization']);
    console.log('- localStorage token:', !!localStorage.getItem('auth_token'));

    setIsLoading(true);
    
    // Process attachments and create URLs for display
    const messageAttachments = await Promise.all(
      attachments.map(async (file) => {
        const url = URL.createObjectURL(file);
        return {
          type: file.type.startsWith('image/') ? 'image' as const : 'file' as const,
          name: file.name,
          url: url,
          size: file.size
        };
      })
    );

    // optimistic update
    const userMessage: Message = { 
      from: "user", 
      text: trimmed || "Sent attachments",
      timestamp: new Date(),
      attachments: messageAttachments
    };
    setMessages((prev: Message[]) => [...prev, userMessage]);
    setInput("");
    setAttachments([]);

    try {
      let response;
      
      if (attachments.length > 0) {
        // Use FormData for file uploads
        const formData = new FormData();
        formData.append('message', trimmed || "I've attached some files for you to review.");
        if (conversationId) {
          formData.append('conversation_id', conversationId);
        }
        
        attachments.forEach((file) => {
          formData.append('files', file);
        });

        response = await axios.post<{ conversation_id: string; response: string }>(
          "http://localhost:8000/chat-with-files",
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          }
        );
      } else {
        // Regular text message
        response = await axios.post<{ conversation_id: string; response: string }>(
          "http://localhost:8000/chat",
          conversationId ? {
          conversation_id: conversationId,
          message: trimmed,
          } : {
          message: trimmed,
        }
      );
      }

      const { conversation_id, response: aiResponse } = response.data;
      setConversationId(conversation_id);
      
      const agentMessage: Message = { 
        from: "agent", 
        text: aiResponse,
        timestamp: new Date()
      };
      setMessages((prev: Message[]) => [...prev, agentMessage]);
    } catch (err) {
      console.error(err);
      const errorMessage: Message = { 
        from: "agent", 
        text: "Sorry, I'm having trouble connecting right now. Please try again.",
        timestamp: new Date()
      };
      setMessages((prev: Message[]) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // auto scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const renderAttachment = (attachment: Message['attachments'][0]) => {
    if (attachment.type === 'image') {
  return (
        <div key={attachment.url} style={{ marginTop: '0.5rem' }}>
          <img 
            src={attachment.url} 
            alt={attachment.name}
            style={{
              maxWidth: '200px', 
              maxHeight: '200px', 
              borderRadius: '0.5rem',
              objectFit: 'cover'
            }}
          />
          <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.25rem' }}>
            {attachment.name} {attachment.size && `(${formatFileSize(attachment.size)})`}
          </div>
        </div>
      );
    } else {
      return (
        <div key={attachment.url} style={{ 
          marginTop: '0.5rem', 
          padding: '0.5rem', 
          backgroundColor: 'rgba(0,0,0,0.1)', 
          borderRadius: '0.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem'
        }}>
          <div style={{ fontSize: '1.2rem' }}>📄</div>
          <div>
            <div style={{ fontSize: '0.875rem', fontWeight: '500' }}>{attachment.name}</div>
            {attachment.size && (
              <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
                {formatFileSize(attachment.size)}
              </div>
            )}
          </div>
        </div>
      );
    }
  };

  return (
    <div style={{ 
      display: "flex", 
      flexDirection: "column", 
      height: "100vh", 
      width: "100vw",
      backgroundColor: "#f9fafb",
      position: "fixed",
      top: 0,
      left: 0,
      zIndex: 1000,
      margin: 0,
      padding: 0
    }}>
        {/* Authentication Header - ALWAYS VISIBLE */}
        <div style={{
          padding: "1rem",
          backgroundColor: "white",
          borderBottom: "1px solid #e5e7eb",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexShrink: 0,
          zIndex: 1001
        }}>
          <div>
            <h1 style={{ margin: 0, fontSize: "1.5rem", fontWeight: "bold", color: "#1f2937" }}>
              🌟 Travel Assistant
            </h1>
            <p style={{ margin: 0, fontSize: "0.875rem", color: "#6b7280" }}>
              AI-powered travel planning with personalized recommendations
            </p>
          </div>
          
          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            {!authChecked ? (
              <div style={{ fontSize: "0.875rem", color: "#6b7280" }}>
                Loading...
              </div>
            ) : user ? (
              <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: "0.875rem", fontWeight: "500", color: "#1f2937" }}>
                    {user.first_name} {user.last_name}
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "#10b981" }}>
                    ✅ Authenticated
                  </div>
                </div>
                <button
                  onClick={() => {
                    // Force fresh authentication for testing
                    localStorage.removeItem('auth_token');
                    localStorage.removeItem('user_data');
                    delete axios.defaults.headers.common['Authorization'];
                    setUser(null);
                    setShowAuthModal(true);
                  }}
            style={{
                    padding: "0.5rem 1rem",
                    backgroundColor: "#f59e0b",
                    border: "1px solid #d97706",
                    borderRadius: "0.375rem",
                    fontSize: "0.875rem",
                    cursor: "pointer",
                    color: "white",
                    marginRight: "0.5rem"
                  }}
                >
                  🔄 Re-auth
                </button>
                <button
                  onClick={handleLogout}
            style={{
                    padding: "0.5rem 1rem",
                    backgroundColor: "#f3f4f6",
                    border: "1px solid #d1d5db",
                    borderRadius: "0.375rem",
                    fontSize: "0.875rem",
                    cursor: "pointer",
                    color: "#374151"
                  }}
                >
                  Logout
                </button>
              </div>
            ) : (
              <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                <div style={{ fontSize: "0.875rem", color: "#ef4444" }}>
                  ⚠️ Authentication Required
                </div>
              </div>
            )}
          </div>
        </div>

      {/* Personalization Notice - ALWAYS VISIBLE when user authenticated */}
      {user && !user.is_demo_user && (
        <div style={{
          padding: "0.75rem 1rem",
          backgroundColor: "#dbeafe",
          borderBottom: "1px solid #e5e7eb",
          fontSize: "0.875rem",
          color: "#1e40af",
          marginTop: "0",
          width: "100%",
          boxSizing: "border-box",
          borderTop: "1px solid #e5e7eb"
        }}>
          💡 I'm learning from our conversations to provide better personalized recommendations
        </div>
      )}

      {/* Messages Area - ALWAYS VISIBLE */}
      <div style={{ 
        flex: 1, 
        overflowY: "auto", 
        padding: "1rem", 
        backgroundColor: "white",
        minHeight: 0
      }}>
        {!authChecked ? (
          <div style={{ 
            textAlign: "center", 
            padding: "4rem 2rem", 
            color: "#6b7280",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            height: "100%"
          }}>
            <div style={{ fontSize: "4rem", marginBottom: "1rem" }}>🔄</div>
            <h2 style={{ fontSize: "1.5rem", fontWeight: "600", marginBottom: "1rem", color: "#1f2937" }}>
              Initializing...
            </h2>
            <p style={{ fontSize: "1rem" }}>
              Setting up your travel assistant
            </p>
          </div>
        ) : !user ? (
          <div style={{ 
            textAlign: "center", 
            padding: "4rem 2rem", 
            color: "#6b7280",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            height: "100%"
          }}>
            <div style={{ fontSize: "4rem", marginBottom: "1rem" }}>🔐</div>
            <h2 style={{ fontSize: "1.5rem", fontWeight: "600", marginBottom: "1rem", color: "#1f2937" }}>
              Authentication Required
            </h2>
            <p style={{ fontSize: "1rem", marginBottom: "0.5rem", maxWidth: "500px" }}>
              Please create an account or sign in to access your personalized AI travel assistant.
            </p>
            <p style={{ fontSize: "0.875rem", color: "#6b7280", maxWidth: "500px" }}>
              Your account enables us to learn your preferences and provide better recommendations over time.
            </p>
          </div>
        ) : messages.length === 0 ? (
          <div style={{ textAlign: "center", padding: "2rem", color: "#64748b" }}>
            <h2 style={{ fontSize: "1.25rem", fontWeight: "600", marginBottom: "0.5rem" }}>
              Welcome to Travel Assistant! 🛫
            </h2>
            <p style={{ fontSize: "0.875rem" }}>
              I can help you with hotel bookings, flight reservations, rescheduling, and refund requests.
            </p>
            <p style={{ fontSize: "0.75rem", marginTop: "0.5rem" }}>
              You can also send images, files, or use voice input! 📎 🎤
            </p>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            {messages.map((message, idx) => (
              <div key={idx} style={{ 
                display: "flex", 
                justifyContent: message.from === "user" ? "flex-end" : "flex-start" 
              }}>
                <div style={{
                  maxWidth: "70%",
                  backgroundColor: message.from === "user" ? "#3b82f6" : "#f1f5f9",
                  color: message.from === "user" ? "white" : "#1e293b",
                  borderRadius: "0.75rem",
                  padding: "0.75rem",
                  position: "relative"
                }}>
                  <div style={{ display: "flex", alignItems: "flex-start", gap: "0.5rem" }}>
                    {message.from === "agent" && (
                      <div style={{
                        width: "2rem",
                        height: "2rem",
                        borderRadius: "50%",
                        backgroundColor: "#3b82f6",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        color: "white",
                        fontSize: "0.75rem",
                        fontWeight: "600"
                      }}>
                        TA
                      </div>
                    )}
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: "0.875rem", fontWeight: "500", marginBottom: "0.25rem" }}>
                        {message.from === "user" ? "You" : "Travel Assistant"}
                      </div>
                      <div style={{ fontSize: "1rem", whiteSpace: "pre-wrap" }}>
                        {message.text}
                      </div>
                      {message.attachments && message.attachments.map(renderAttachment)}
                      {message.timestamp && (
                        <div style={{ 
                          fontSize: "0.75rem", 
                          color: message.from === "user" ? "#bfdbfe" : "#64748b", 
                          marginTop: "0.5rem" 
                        }}>
                          {formatTime(message.timestamp)}
                        </div>
                      )}
                    </div>
                    {message.from === "user" && (
                      <div style={{
                        width: "2rem",
                        height: "2rem",
                        borderRadius: "50%",
                        backgroundColor: "#9ca3af",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        color: "white",
                        fontSize: "0.75rem",
                        fontWeight: "600"
                      }}>
                        U
                      </div>
                    )}
                  </div>
                </div>
      </div>
    ))}
            
            {isLoading && (
              <div style={{ display: "flex", justifyContent: "flex-start" }}>
                <div style={{
                  backgroundColor: "#f1f5f9",
                  borderRadius: "0.75rem",
                  padding: "0.75rem"
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <div style={{
                      width: "2rem",
                      height: "2rem",
                      borderRadius: "50%",
                      backgroundColor: "#3b82f6",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      color: "white",
                      fontSize: "0.75rem",
                      fontWeight: "600"
                    }}>
                      TA
                    </div>
                    <div style={{
                      width: "1rem",
                      height: "1rem",
                      border: "2px solid #3b82f6",
                      borderTop: "2px solid transparent",
                      borderRadius: "50%",
                      animation: "spin 1s linear infinite"
                    }}></div>
                    <span style={{ fontSize: "0.875rem", color: "#475569" }}>
                      Travel Assistant is typing...
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
    <div ref={bottomRef} />
  </div>

      {/* Attachments Preview - ALWAYS VISIBLE when attachments exist */}
      {attachments.length > 0 && (
        <div style={{ 
          padding: "0.75rem 1rem", 
          backgroundColor: "#f8fafc", 
          borderTop: "1px solid #e2e8f0",
          borderBottom: "1px solid #e2e8f0"
        }}>
          <div style={{ fontSize: "0.875rem", fontWeight: "500", marginBottom: "0.5rem", color: "#374151" }}>
            Attachments ({attachments.length}):
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
            {attachments.map((file, index) => (
              <div key={index} style={{
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
                padding: "0.5rem",
                backgroundColor: "white",
                borderRadius: "0.5rem",
                border: "1px solid #d1d5db",
                fontSize: "0.875rem"
              }}>
                <span>{file.type.startsWith('image/') ? '🖼️' : '📄'}</span>
                <span>{file.name}</span>
                <span style={{ color: "#6b7280" }}>({formatFileSize(file.size)})</span>
                <button
                  onClick={() => removeAttachment(index)}
                  style={{
                    background: "none",
                    border: "none",
                    color: "#ef4444",
                    cursor: "pointer",
                    fontSize: "1rem",
                    padding: "0",
                    marginLeft: "0.25rem"
                  }}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
      </div>
      )}

      {/* Input Area - ALWAYS VISIBLE */}
      <div style={{ 
        padding: "1rem", 
        backgroundColor: "#f3f4f6",
        borderTop: "1px solid #d1d5db",
        boxShadow: "0 -1px 3px rgba(0,0,0,0.05)",
        minHeight: "80px",
        flexShrink: 0,
        opacity: !user ? 0.6 : 1
      }}>
      <form
        onSubmit={(e) => {
          e.preventDefault();
            if (user) {
          sendMessage();
            }
          }}
          style={{ 
            display: "flex", 
            gap: "0.75rem", 
            alignItems: "flex-end"
          }}
        >
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept="image/*,.pdf,.doc,.docx,.txt"
              onChange={handleFileSelect}
              style={{ display: "none" }}
            />
            <button
              type="button"
              onClick={() => user && fileInputRef.current?.click()}
              disabled={isLoading || !user}
              style={{
                padding: "0.75rem",
                backgroundColor: "#6b7280",
                color: "white",
                border: "none",
                borderRadius: "0.5rem",
                fontSize: "1rem",
                cursor: "pointer",
                transition: "background-color 0.2s",
                opacity: (isLoading || !user) ? 0.4 : 1
              }}
              title={user ? "Attach files" : "Login required to attach files"}
            >
              📎
            </button>
            <button
              type="button"
              onClick={isRecording ? stopRecording : startRecording}
              disabled={isLoading || !user}
              style={{
                padding: "0.75rem",
                backgroundColor: isRecording ? "#ef4444" : "#10b981",
                color: "white",
                border: "none",
                borderRadius: "0.5rem",
                fontSize: "1rem",
                cursor: "pointer",
                transition: "background-color 0.2s",
                opacity: (isLoading || !user) ? 0.4 : 1
              }}
              title={user ? (isRecording ? "Stop recording" : "Start voice input") : "Login required for voice input"}
            >
              {isRecording ? "⏹️" : "🎤"}
            </button>
          </div>

        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
            placeholder={user ? "Ask about hotels, flights, rescheduling, or refunds..." : "Login to start chatting..."}
            disabled={isLoading || !user}
            style={{
              flex: 1,
              padding: "0.75rem 1rem",
              borderRadius: "9999px",
              border: "1px solid #d1d5db",
              fontSize: "1rem",
              outline: "none",
              transition: "border-color 0.2s, box-shadow 0.2s",
              backgroundColor: !user ? "#f3f4f6" : "white"
            }}
            onFocus={(e) => {
              e.target.style.borderColor = "#3b82f6";
              e.target.style.boxShadow = "0 0 0 1px #3b82f6";
            }}
            onBlur={(e) => {
              e.target.style.borderColor = "#d1d5db";
              e.target.style.boxShadow = "none";
            }}
        />
        <button
          type="submit"
            disabled={isLoading || !user || (!input.trim() && attachments.length === 0)}
            style={{
              padding: "0.75rem 1.5rem",
              backgroundColor: "#3b82f6",
              color: "white",
              border: "none",
              borderRadius: "9999px",
              fontSize: "1rem",
              fontWeight: "500",
              cursor: "pointer",
              transition: "background-color 0.2s",
              opacity: (isLoading || !user || (!input.trim() && attachments.length === 0)) ? 0.4 : 1,
              pointerEvents: (isLoading || !user || (!input.trim() && attachments.length === 0)) ? "none" : "auto"
            }}
            title={user ? "Send" : "Login to send messages"}
            onMouseEnter={(e) => {
              if (!isLoading && user && (input.trim() || attachments.length > 0)) {
                e.currentTarget.style.backgroundColor = "#2563eb";
              }
            }}
            onMouseLeave={(e) => {
              if (!isLoading && user && (input.trim() || attachments.length > 0)) {
                e.currentTarget.style.backgroundColor = "#3b82f6";
              }
            }}
        >
          Send
        </button>
      </form>

  {!user && (
    <div style={{
      marginTop: "0.5rem",
      fontSize: "0.75rem",
      color: "#6b7280",
      textAlign: "center"
    }}>
      Please log in to enable chat input
    </div>
  )}
      </div>

      {/* Authentication Modal - ALWAYS PRESENT */}
      <AuthModal
        isOpen={showAuthModal}
        onClose={() => {
          if (user) {
            setShowAuthModal(false);
          }
        }}
        onAuthSuccess={(userData, token) => {
          handleAuthSuccess(userData, token);
          setShowAuthModal(false);
        }}
        isMandatory={true}
      />
    </div>
  );
};

export default Chat; 