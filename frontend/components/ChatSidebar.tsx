import { motion, AnimatePresence } from "framer-motion";
import { MessageSquare, Plus, X } from "lucide-react";
import { Button } from "./ui/button";
import { ScrollArea } from "./ui/scroll-area";
import { cn } from "@/lib/utils";

interface Conversation {
  id: string;
  title: string;
  timestamp: string;
}

interface ChatSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  conversations: Conversation[];
  activeConversationId?: string;
  onSelectConversation: (id: string) => void;
  onNewConversation: () => void;
}

export const ChatSidebar = ({
  isOpen,
  onClose,
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
}: ChatSidebarProps) => {
  return (
    <>
      <AnimatePresence>
        {isOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={onClose}
              className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40 md:hidden"
            />
            <motion.aside
              initial={{ x: -300 }}
              animate={{ x: 0 }}
              exit={{ x: -300 }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="fixed left-0 top-0 bottom-0 z-50 w-72 border-r border-border bg-card md:sticky md:block"
            >
              <div className="flex h-16 items-center justify-between border-b border-border px-4">
                <h2 className="font-semibold">Conversations</h2>
                <Button variant="ghost" size="icon" onClick={onClose} className="md:hidden">
                  <X className="h-5 w-5" />
                </Button>
              </div>

              <div className="p-4 border-b border-border">
                <Button
                  onClick={onNewConversation}
                  className="w-full justify-start gap-2"
                  variant="outline"
                >
                  <Plus className="h-4 w-4" />
                  New Conversation
                </Button>
              </div>

              <ScrollArea className="h-[calc(100vh-8rem)]">
                <div className="p-2">
                  {conversations.map((conversation) => (
                    <button
                      key={conversation.id}
                      onClick={() => {
                        onSelectConversation(conversation.id);
                        onClose();
                      }}
                      className={cn(
                        "w-full flex items-start gap-3 rounded-lg p-3 text-left transition-colors hover:bg-accent",
                        activeConversationId === conversation.id && "bg-accent"
                      )}
                    >
                      <MessageSquare className="h-5 w-5 shrink-0 text-muted-foreground mt-0.5" />
                      <div className="flex-1 overflow-hidden">
                        <p className="text-sm font-medium truncate">{conversation.title}</p>
                        <p className="text-xs text-muted-foreground">{conversation.timestamp}</p>
                      </div>
                    </button>
                  ))}
                </div>
              </ScrollArea>
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  );
};
