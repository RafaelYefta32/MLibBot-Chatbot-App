"use client";

import { useState } from "react";
import { ChatHeader } from "@/components/ChatHeader";
import { ChatMessage } from "@/components/ChatMessage";
import { ChatInput } from "@/components/ChatInput";
import { ChatSidebar } from "@/components/ChatSidebar";
import { WelcomeScreen } from "@/components/WelcomeScreen";
import { ScrollArea } from "@/components/ui/scroll-area";

interface Message {
  id: string;
  text: string;
  isBot: boolean;
  timestamp: string;
}

export default function Page() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isTyping, setIsTyping] = useState(false);

  // const conversations = [
  //   { id: "1", title: "Mystery Novel Recommendations", timestamp: "2 hours ago" },
  //   { id: "2", title: "Science Fiction Classics", timestamp: "Yesterday" },
  //   { id: "3", title: "Best Fantasy Series", timestamp: "3 days ago" },
  // ];

  const handleSendMessage = (text: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      text,
      isBot: false,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsTyping(true);

    setTimeout(() => {
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: `Thank you for your question: "${text}". I'm a demo interface, so I don't have actual AI capabilities yet, but in a real implementation, I would search our library database and provide you with personalized book recommendations based on your interests!`,
        isBot: true,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, botMessage]);
      setIsTyping(false);
    }, 1500);
  };

  // const handleNewConversation = () => {
  //   setMessages([]);
  //   setIsSidebarOpen(false);
  // };

  return (
    <div className="flex h-screen w-full bg-gradient-to-br from-background via-background to-accent/5">
      {/* <ChatSidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        conversations={conversations}
        onSelectConversation={(id) => console.log("Selected:", id)}
        onNewConversation={handleNewConversation}
      /> */}

      <div className="flex flex-1 flex-col overflow-hidden">
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
