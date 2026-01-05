import { motion } from "framer-motion";
import { BookOpen, User } from "lucide-react";
import { cn } from "@/lib/utils";

interface MessageMetadata {
  source?: string;
  intent?: string;
  probability?: number;
  score?: number;
}

interface ChatMessageProps {
  message: string;
  isBot: boolean;
  timestamp?: string;
  metadata?: MessageMetadata;
}

export const ChatMessage = ({ message, isBot, timestamp, metadata }: ChatMessageProps) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn("flex gap-3 mb-4", !isBot && "flex-row-reverse")}
    >
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
          isBot ? "bg-primary text-primary-foreground" : "bg-secondary text-secondary-foreground"
        )}
      >
        {isBot ? <BookOpen className="h-4 w-4" /> : <User className="h-4 w-4" />}
      </div>
      <div className={cn("flex flex-col gap-1 max-w-[80%]", !isBot && "items-end")}>
        <div
          className={cn(
            "rounded-2xl px-4 py-3 shadow-sm",
            isBot
              ? "bg-card text-card-foreground border border-border"
              : "bg-primary text-primary-foreground"
          )}
        >
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message}</p>
        </div>
        {isBot && metadata && (
          <div className="flex flex-wrap gap-2 px-2 mt-1">
            {metadata.source && (
              <span className="inline-flex items-center gap-1 text-xs text-muted-foreground bg-muted/50 px-2 py-0.5 rounded-full">
                <span className="font-medium text-foreground/70">Source:</span> {metadata.source}
              </span>
            )}
            {metadata.intent && (
              <span className="inline-flex items-center gap-1 text-xs text-muted-foreground bg-muted/50 px-2 py-0.5 rounded-full">
                <span className="font-medium text-foreground/70">Intent:</span> {metadata.intent}
              </span>
            )}
            {metadata.probability !== undefined && (
              <span className="inline-flex items-center gap-1 text-xs text-muted-foreground bg-muted/50 px-2 py-0.5 rounded-full">
                <span className="font-medium text-foreground/70">Probability:</span> {(metadata.probability).toFixed(1)}%
              </span>
            )}
            {metadata.score !== undefined && (
              <span className="inline-flex items-center gap-1 text-xs text-muted-foreground bg-muted/50 px-2 py-0.5 rounded-full">
                <span className="font-medium text-foreground/70">Score:</span> {(metadata.score).toFixed(1)}
              </span>
            )}
          </div>
        )}
        {timestamp && (
          <span className="text-xs text-muted-foreground px-2">{timestamp}</span>
        )}
      </div>
    </motion.div>
  );
};
