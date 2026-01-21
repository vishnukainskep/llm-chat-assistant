import React, { useEffect, useRef, useState } from "react";
import { Send, RotateCcw, MessageSquare, Plus, Trash2, Menu } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface Session {
  id: string;
  user_id: string;
  title: string;
  last_updated?: string;
}

const ChatLoader = () => (
  <div className="flex gap-1">
    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
  </div>
);

const Chatbot: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [sessionId, setSessionId] = useState<string>("");
  const [userId, setUserId] = useState<string>("vishnu"); // Default user as per screenshot
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const storedSessionId = localStorage.getItem("chat_session_id");
    const storedUserId = localStorage.getItem("chat_user_id") || "vishnu";
    setUserId(storedUserId);
    
    if (storedSessionId) {
      setSessionId(storedSessionId);
      fetchHistory(storedSessionId);
    } else {
      const newId = crypto.randomUUID();
      setSessionId(newId);
      localStorage.setItem("chat_session_id", newId);
    }
    fetchSessions();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const fetchSessions = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/sessions");
      const data = await res.json();
      setSessions(data.sessions || []);
    } catch (error) {
      console.error("Failed to fetch sessions", error);
    }
  };

  const fetchHistory = async (sid: string) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/history/${sid}`);
      const data = await res.json();
      if (data.history) {
        setMessages(data.history.map((m: any) => ({
          role: m.type === "human" ? "user" : "assistant",
          content: m.content
        })));
      }
    } catch (error) {
      console.error("Failed to fetch history", error);
    }
  };

  const handleNewChat = () => {
    const newId = crypto.randomUUID();
    setSessionId(newId);
    localStorage.setItem("chat_session_id", newId);
    setMessages([]);
    fetchSessions();
  };

  const handleSwitchSession = (sid: string) => {
    setSessionId(sid);
    localStorage.setItem("chat_session_id", sid);
    fetchHistory(sid);
  };

  const handleDeleteSession = async (e: React.MouseEvent, sid: string) => {
    e.stopPropagation();
    try {
      await fetch(`http://127.0.0.1:8000/sessions/${sid}`, { method: "DELETE" });
      if (sid === sessionId) {
        handleNewChat();
      } else {
        fetchSessions();
      }
    } catch (error) {
      console.error("Failed to delete session", error);
    }
  };

  const streamResponse = async (userMessage: string, targetIndex: number, currentSessionId: string) => {
    setIsLoading(true);
    let fullText = "";

    try {
      const response = await fetch(import.meta.env.VITE_BASE_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          user_input: userMessage,
          session_id: currentSessionId,
          user_id: userId
        }),
      });

      // Check for session switch header
      const newSessionId = response.headers.get("X-Session-Id");
      if (newSessionId && newSessionId !== currentSessionId) {
        setSessionId(newSessionId);
        localStorage.setItem("chat_session_id", newSessionId);
        // Refresh history to show the conversation we just switched into
        fetchHistory(newSessionId);
      }

      if (!response.body) throw new Error("Streaming not supported");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        fullText += decoder.decode(value, { stream: true });
        
        setMessages(prev => {
          const updated = [...prev];
          updated[targetIndex] = { role: "assistant", content: fullText };
          return updated;
        });
      }
      
      fetchSessions();
      
    } catch (error) {
      setMessages(prev => {
        const updated = [...prev];
        updated[targetIndex] = { role: "assistant", content: "Error: Could not generate response" };
        return updated;
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMsg = input.trim();
    setInput("");

    const newMessages: Message[] = [
      ...messages,
      { role: "user", content: userMsg },
      { role: "assistant", content: "" }
    ];
    setMessages(newMessages);

    await streamResponse(userMsg, newMessages.length - 1, sessionId);
  };

  const handleRegenerate = async (index: number) => {
    if (isLoading) return;

    const userMsg = messages.slice(0, index).reverse().find(m => m.role === "user")?.content;
    if (!userMsg) return;

    setMessages(prev => {
      const updated = [...prev];
      updated[index] = { role: "assistant", content: "" };
      return updated;
    });

    await streamResponse(userMsg, index, sessionId);
  };

  return (
    <div className="flex h-screen bg-gray-50 text-gray-900 overflow-hidden font-sans">
      {/* Sidebar */}
      <div 
        className={`${
          isSidebarOpen ? "w-72" : "w-0"
        } transition-all duration-300 bg-gray-900 border-r border-gray-800 flex flex-col relative overflow-hidden`}
      >
        <div className="p-4 border-b border-gray-800 flex items-center justify-between">
          <h2 className="text-white font-semibold flex items-center gap-2">
            <MessageSquare size={20} className="text-blue-400" />
            Chat History
          </h2>
        </div>

        <button
          onClick={handleNewChat}
          className="m-4 flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm font-medium shadow-lg shadow-blue-500/20"
        >
          <Plus size={18} />
          New Chat
        </button>

        <div className="flex-1 overflow-y-auto px-2 space-y-1">
          {sessions.map(s => (
            <div
              key={s.id}
              onClick={() => handleSwitchSession(s.id)}
              className={`w-full flex flex-col gap-1 px-3 py-3 rounded-lg text-sm transition-colors text-left group cursor-pointer ${
                sessionId === s.id 
                  ? "bg-gray-800 text-white" 
                  : "text-gray-400 hover:bg-gray-800 hover:text-white"
              }`}
            >
              <div className="flex items-center gap-2">
                <MessageSquare size={14} className="shrink-0 opacity-70" />
                <span className="truncate flex-1 font-medium">{s.title}</span>
                <button
                  onClick={(e) => handleDeleteSession(e, s.id)}
                  className="opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-700 rounded transition-all"
                >
                  <Trash2 size={14} className="text-gray-500 hover:text-red-400" />
                </button>
              </div>
              <div className="flex justify-between items-center pl-6 text-[10px] opacity-50">
                <span>{s.user_id}</span>
                {s.last_updated && (
                  <span>{new Date(s.last_updated).toLocaleDateString()}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0 bg-white">
        {/* Header */}
        <div className="h-16 border-b flex items-center justify-between px-4 bg-white/80 backdrop-blur-md sticky top-0 z-10">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-600"
            >
              <Menu size={20} />
            </button>
            <h1 className="text-lg font-bold text-gray-800 truncate max-w-md">
              {sessions.find(s => s.id === sessionId)?.title || "New Chat"}
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500 font-medium bg-gray-100 px-2 py-1 rounded">
              User: {userId}
            </span>
            <button 
              onClick={() => {
                const newUserId = prompt("Enter User ID:", userId);
                if (newUserId) {
                  setUserId(newUserId);
                  localStorage.setItem("chat_user_id", newUserId);
                }
              }}
              className="p-2 hover:bg-gray-100 rounded-lg text-gray-400 hover:text-gray-600 transition-all"
              title="Change User ID"
            >
              <RotateCcw size={18} />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 md:p-8">
          <div className="max-w-3xl mx-auto space-y-8">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full text-center py-20">
                <div className="w-16 h-16 bg-blue-50 rounded-2xl flex items-center justify-center mb-4">
                  <MessageSquare size={32} className="text-blue-500" />
                </div>
                <h2 className="text-2xl font-bold text-gray-800 mb-2">How can I help you?</h2>
                <p className="text-gray-500 max-w-sm">
                  Start a conversation with your AI agent.
                </p>
              </div>
            )}
            
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} group`}>
                <div className={`max-w-[85%] md:max-w-2xl flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}>
                  <div
                    className={`px-5 py-3 rounded-2xl leading-relaxed shadow-sm ${
                      msg.role === "user"
                        ? "bg-blue-600 text-white rounded-tr-none"
                        : "bg-gray-50 text-gray-800 border border-gray-100 rounded-tl-none"
                    }`}
                  >
                    {msg.content === "" ? <ChatLoader /> : <p className="whitespace-pre-wrap text-[15px]">{msg.content}</p>}
                  </div>
                  
                  {msg.role === "assistant" && msg.content && !isLoading && (
                    <button
                      onClick={() => handleRegenerate(i)}
                      className="flex items-center gap-1.5 mt-2 text-[11px] font-bold text-gray-400 hover:text-blue-600 opacity-0 group-hover:opacity-100 transition-all uppercase tracking-wider"
                    >
                      <RotateCcw size={12} />
                      Regenerate
                    </button>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} className="h-4" />
          </div>
        </div>

        {/* Input */}
        <div className="p-4 md:p-6 bg-white border-t">
          <div className="max-w-3xl mx-auto relative group">
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Message your agent..."
              disabled={isLoading}
              rows={1}
              className="w-full pl-4 pr-14 py-4 bg-gray-50 border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 disabled:bg-gray-50 resize-none transition-all text-[15px] shadow-inner"
              style={{ minHeight: '56px', maxHeight: '200px' }}
              onInput={(e) => {
                const target = e.target as HTMLTextAreaElement;
                target.style.height = 'auto';
                target.style.height = `${target.scrollHeight}px`;
              }}
            />
            <button
              onClick={handleSend}
              disabled={isLoading || !input.trim()}
              className="absolute right-3 bottom-3 p-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:bg-gray-200 disabled:text-gray-400 transition-all flex items-center justify-center shadow-lg shadow-blue-500/20"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chatbot;
