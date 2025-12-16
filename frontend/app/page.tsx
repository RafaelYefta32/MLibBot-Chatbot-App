"use client";

import { useState } from "react";
import { ChatHeader } from "@/components/ChatHeader";
import { ChatMessage } from "@/components/ChatMessage";
import { ChatInput } from "@/components/ChatInput";
import { ChatSidebar } from "@/components/ChatSidebar";
import { WelcomeScreen } from "@/components/WelcomeScreen";
import { ScrollArea } from "@/components/ui/scroll-area";

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

export default function Page() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isTyping, setIsTyping] = useState(false);

  const conversations = [
    { id: "1", title: "Mystery Novel Recommendations", timestamp: "2 hours ago" },
    { id: "2", title: "Science Fiction Classics", timestamp: "Yesterday" },
    { id: "3", title: "Best Fantasy Series", timestamp: "3 days ago" },
  ];

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
      const apiUrl = "http://localhost:8000/chat"; 
      
      const response = await fetch(apiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ 
            message: text,
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
          
          source: data.sources[0].source, 
          
          intent: data.intent?.label, 
          probability: data.intent?.confidence_percent,
          score: data.sources[0].score_hybrid,
        },
      };
      setMessages((prev) => [...prev, botMessage]);
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

  const handleNewConversation = () => {
    setMessages([]);
    setIsSidebarOpen(false);
  };

  return (
    <div className="flex h-screen w-full bg-gradient-to-br from-background via-background to-accent/5">
      <ChatSidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        conversations={conversations}
        onSelectConversation={(id) => console.log("Selected:", id)}
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
