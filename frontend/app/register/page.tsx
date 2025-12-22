"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { BookOpen, Eye, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";

const Register = () => {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfPassword, setShowConfPassword] = useState(false);

  const { register } = useAuth();
  const router = useRouter();
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!fullName || !email || !password || !confirmPassword) {
      toast({
        title: "Register Failed",
        description: "Please fill in all fields",
        variant: "destructive",
      });
      return;
    }

    if (password !== confirmPassword) {
      toast({
        title: "Register Failed",
        description: "Passwords do not match",
        variant: "destructive",
      });
      return;
    }

    try {
      await register(fullName, email, password);

      toast({
        title: "Success",
        description: "Account created successfully",
      });

      router.push("/");
    } catch (error) {
      toast({
        title: "Register Failed",
        description: "Email Already Registered, Use Another Email.",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="flex flex-col items-center mb-8">
          <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br from-primary via-secondary to-primary shadow-lg shadow-primary/20 mb-4">
            <BookOpen className="h-7 w-7 text-primary-foreground" strokeWidth={2.5} />
          </div>
          <h1 className="text-2xl font-bold">Create Account</h1>
          <p className="text-muted-foreground">Join MLibBot today</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 bg-card p-6 rounded-lg border border-border">
          <div className="space-y-2">
            <Label htmlFor="fullName">Full Name</Label>
            <Input id="fullName" type="text" placeholder="John Doe" value={fullName} onChange={(e) => setFullName(e.target.value)} />
          </div>

          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <div className="relative">
              <Input id="password" type={showPassword ? "text" : "password"} placeholder="••••••••" value={password} onChange={(e) => setPassword(e.target.value)} />
              <Button type="button" variant="ghost" size="icon" className="absolute right-0 top-0 h-full px-3" onClick={() => setShowPassword(!showPassword)}>
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </Button>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirmPassword">Confirm Password</Label>
            <div className="relative">
              <Input id="confirmPassword" type={showConfPassword ? "text" : "password"} placeholder="••••••••" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} />
              <Button type="button" variant="ghost" size="icon" className="absolute right-0 top-0 h-full px-3" onClick={() => setShowConfPassword(!showConfPassword)}>
                {showConfPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </Button>
            </div>
          </div>

          <Button type="submit" className="w-full">
            Create Account
          </Button>

          <p className="text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link href="/login" className="text-primary hover:underline">
              Sign in
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
};

export default Register;
