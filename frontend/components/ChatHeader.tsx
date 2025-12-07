import { BookOpen, Menu } from "lucide-react";
import { Button } from "./ui/button";

interface ChatHeaderProps {
  onToggleSidebar: () => void;
}

export const ChatHeader = ({ onToggleSidebar }: ChatHeaderProps) => {
  return (
    <header className="sticky top-0 z-10 pl-7 border-b border-border bg-card/80 backdrop-blur-sm">
      <div className="flex h-16 items-center justify-between px-4 md:px-6">
        <div className="flex items-center gap-3">
          {/* <Button variant="ghost" size="icon" onClick={onToggleSidebar}>
            <Menu className="h-5 w-5" />
          </Button> */}
          <div className="flex items-center gap-2">
            <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-primary via-secondary to-primary shadow-lg shadow-primary/20">
              <div className="absolute inset-0 rounded-xl bg-primary/10 animate-pulse" />
              <BookOpen className="relative h-5 w-5 text-primary-foreground" strokeWidth={2.5} />
              <div className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full bg-secondary border-2 border-background" />
            </div>    
            <div>
              <h1 className="text-lg font-semibold tracking-tight">MLibBot</h1>
              <p className="text-xs text-muted-foreground">Ask me about books</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
