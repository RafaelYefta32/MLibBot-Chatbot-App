"use client";

import { useState, useEffect, useCallback } from "react";
import { ChatHeader } from "@/components/ChatHeader";
import { ChatMessage } from "@/components/ChatMessage";
import { ChatInput } from "@/components/ChatInput";
import { ChatSidebar } from "@/components/ChatSidebar";
import { WelcomeScreen } from "@/components/WelcomeScreen";
import { ScrollArea } from "@/components/ui/scroll-area";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface MessageMetadata {
  source?: string;
  intent?: string;
  probability?: number;
  score?: number;
}

interface Message {
  id: string;
  text: string;
  isBot: boolean;
  timestamp: string;
  metadata?: MessageMetadata;
}

interface Session {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export default function Page() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const storedToken = localStorage.getItem("token");
    setToken(storedToken);
  }, []);

  const fetchSessions = useCallback(async () => {
    if (!token) return;
    
    try {
      const response = await fetch(`${API_URL}/chat/sessions`, {
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setSessions(data);
      }
    } catch (error) {
      console.error("Error fetching sessions:", error);
    }
  }, [token]);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  const loadSession = async (sessionId: string) => {
    if (!token) return;
    
    try {
      const response = await fetch(`${API_URL}/chat/sessions/${sessionId}`, {
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        const loadedMessages: Message[] = data.messages.map((msg: {role: string; content: string; timestamp: string; metadata?: MessageMetadata}, index: number) => ({
          id: `${sessionId}-${index}`,
          text: msg.content,
          isBot: msg.role === "bot",
          timestamp: new Date(msg.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          metadata: msg.metadata,
        }));
        setMessages(loadedMessages);
        setCurrentSessionId(sessionId);
      }
    } catch (error) {
      console.error("Error loading session:", error);
    }
  };

  const createSession = async (): Promise<string | null> => {
    if (!token) return null;
    
    try {
      const response = await fetch(`${API_URL}/chat/sessions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({}),
      });
      
      if (response.ok) {
        const data = await response.json();
        await fetchSessions();
        return data.id;
      }
    } catch (error) {
      console.error("Error creating session:", error);
    }
    return null;
  };

  const handleSendMessage = async (text: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      text,
      isBot: false,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsTyping(true);

    try {
      let sessionId = currentSessionId;
      if (!sessionId && token) {
        sessionId = await createSession();
        setCurrentSessionId(sessionId);
      }

      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token && { "Authorization": `Bearer ${token}` }),
        },
        body: JSON.stringify({ 
          message: text,
          session_id: sessionId,
          top_k: 4,       
          method: "hybrid"
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to get response from server");
      }

      const data = await response.json();

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: data.answer || "No response received",
        isBot: true,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        metadata: {
          source: data.sources?.[0]?.source, 
          intent: data.intent?.label, 
          probability: data.intent?.confidence_percent,
          score: data.sources?.[0]?.score_hybrid,
        },
      };
      setMessages((prev) => [...prev, botMessage]);
      
      if (token) {
        await fetchSessions();
      }
    } catch (error) {
      console.error("Error fetching chat response:", error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: "Maaf, terjadi kesalahan saat menghubungi server. Silakan coba lagi.",
        isBot: true,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleNewConversation = async () => {
    setMessages([]);
    setCurrentSessionId(null);
    setIsSidebarOpen(false);
  };

  const handleSelectConversation = async (id: string) => {
    await loadSession(id);
    setIsSidebarOpen(false);
  };

  const formatTimestamp = (dateString: string) => {
    const utcDateString = dateString.endsWith('Z') ? dateString : dateString + 'Z';
    const date = new Date(utcDateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffHours < 1) return "Just now";
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    return date.toLocaleDateString();
  };

  const conversations = sessions.map(s => ({
    id: s.id,
    title: s.title,
    timestamp: formatTimestamp(s.updated_at),
  }));

  return (
    <div className="flex h-screen w-full bg-gradient-to-br from-background via-background to-accent/5">
      <ChatSidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        conversations={conversations}
        activeConversationId={currentSessionId || undefined}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
      />

      <div className="flex flex-1 flex-col overflow-hidden transition-all duration-300 ease-in-out">
        <ChatHeader onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)} />

        <ScrollArea className="flex-1">
          <div className="mx-auto max-w-4xl p-4 md:p-6">
            {messages.length === 0 ? (
              <WelcomeScreen onSuggestedQuestion={handleSendMessage} />
            ) : (
              <>
                {messages.map((message) => (
                  <ChatMessage
                    key={message.id}
                    message={message.text}
                    isBot={message.isBot}
                    timestamp={message.timestamp}
                    metadata={message.metadata}
                  />
                ))}

                {isTyping && (
                  <ChatMessage message="Thinking..." isBot={true} />
                )}
              </>
            )}
          </div>
        </ScrollArea>

        <ChatInput onSendMessage={handleSendMessage} disabled={isTyping} />
      </div>
    </div>
  );
}
