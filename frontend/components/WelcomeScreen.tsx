import { motion } from "framer-motion";
import { BookOpen, Sparkles, Library, Search } from "lucide-react";
import libraryHero from "@/assets/Profesional.jpg";
import Image from "next/image";

interface WelcomeScreenProps {
  onSuggestedQuestion: (question: string) => void;
}

const suggestedQuestions = [
  {
    icon: Search,
    text: "Carikan Buku Natural Language Processing",
    question: "Carikan Buku Natural Language Processing",
  },
  {
    icon: Library,
    text: "Jam Buka Perpustakaan",
    question: "Jam Layanan Perpustakaan",
  },
  {
    icon: BookOpen,
    text: "Buku tahun 2020",
    question: "Bisa Carikan buku yang terbit tahun 2020?",
  },
  {
    icon: Sparkles,
    text: "Layanan Perpustakaan",
    question: "Apa saja layanan yang disediakan di Perpustakaan?",
  },
];

export const WelcomeScreen = ({ onSuggestedQuestion }: WelcomeScreenProps) => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-12rem)] px-4 py-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="max-w-3xl w-full"
      >
        <div className="relative mb-8 overflow-hidden rounded-2xl h-48 shadow-lg">
          <Image
            src={libraryHero}
            alt="Library interior"
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-background via-background/50 to-transparent" />
        </div>

        <div className="text-center mb-12">
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.2, duration: 0.5 }}
            className="flex justify-center mb-6"
          >
            <div className="relative flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-primary via-secondary to-primary shadow-lg shadow-primary/20">
              <div className="absolute inset-0 rounded-xl bg-primary/10 animate-pulse" />
              <BookOpen className="relative h-8 w-8 text-primary-foreground" strokeWidth={2.5} />
              <div className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full bg-secondary border-2 border-background" />  
            </div>
          </motion.div>
          <motion.h1
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="text-4xl font-bold mb-4 bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent"
          >
            Welcome to Maranatha Library ChatBot
          </motion.h1>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="text-lg text-muted-foreground max-w-2xl mx-auto"
          >
            I&apos;m here to help you discover books, get recommendations, and answer all your literary
            questions. What would you like to explore today?
          </motion.p>
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="grid grid-cols-1 md:grid-cols-2 gap-4"
        >
          {suggestedQuestions.map((item, index) => (
            <motion.button
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 + index * 0.1 }}
              onClick={() => onSuggestedQuestion(item.question)}
              className="group relative flex items-center gap-4 rounded-xl border border-border bg-card p-4 text-left transition-all hover:shadow-md hover:border-primary/50 hover:scale-[1.02]"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                <item.icon className="h-5 w-5" />
              </div>
              <span className="font-medium text-sm">{item.text}</span>
            </motion.button>
          ))}
        </motion.div>
      </motion.div>
    </div>
  );
};
