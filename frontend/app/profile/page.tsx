"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { BookOpen, ArrowLeft, Eye, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";

const Profile = () => {
  const { user, updateProfile, updatePassword } = useAuth();
  const router = useRouter();
  const { toast } = useToast();

  const [fullName, setFullName] = useState(user?.fullName || "");
  const [email, setEmail] = useState(user?.email || "");

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");
  
  const [showPasswords, setShowPasswords] = useState(false);
  const [showNewPasswords, setShowNewPasswords] = useState(false);
  const [showConfPasswords, setShowConfPasswords] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (user) {
      setFullName(user.fullName);
      setEmail(user.email);
    } else {
      // router.push("/login");
    }
  }, [user]);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    if (!fullName || !email) {
      toast({
        title: "Error",
        description: "Please fill in all fields",
        variant: "destructive",
      });
      setIsLoading(false);
      return;
    }

    try {
      await updateProfile(fullName, email);
      toast({
        title: "Success",
        description: "Profile updated successfully",
      });
    } catch (error: Error | unknown) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to update profile",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdatePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    if (!currentPassword || !newPassword || !confirmNewPassword) {
      toast({
        title: "Error",
        description: "Please fill in all password fields",
        variant: "destructive",
      });
      setIsLoading(false);
      return;
    }

    if (newPassword !== confirmNewPassword) {
      toast({
        title: "Error",
        description: "New passwords do not match",
        variant: "destructive",
      });
      setIsLoading(false);
      return;
    }

    if (currentPassword === newPassword) {
      toast({
        title: "Error",
        description: "New password cannot be the same as the current password",
        variant: "destructive",
      });
      setIsLoading(false);
      return;
    }

    try {
      const success = await updatePassword(currentPassword, newPassword);
      
      if (success) {
        toast({
          title: "Success",
          description: "Password updated successfully",
        });
        setCurrentPassword("");
        setNewPassword("");
        setConfirmNewPassword("");
      }
    } catch (error: Error | unknown) {
      // 5. Menangkap Error dari Backend (Misal: "Incorrect current password")
      toast({
        title: "Update Failed",
        description: error instanceof Error ? error.message : "Failed to verify current password",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-10 border-b border-border bg-card/80 backdrop-blur-sm">
        <div className="flex h-16 items-center px-4 md:px-6">
          <Button variant="ghost" size="icon" onClick={() => router.push("/")}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div className="flex items-center gap-2 ml-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-primary via-secondary to-primary shadow-lg shadow-primary/20">
              <BookOpen className="h-5 w-5 text-primary-foreground" strokeWidth={2.5} />
            </div>
            <h1 className="text-lg font-semibold">Profile Settings</h1>
          </div>
        </div>
      </header>

      <main className="container max-w-2xl py-8 px-4">
        {/* Form Profile */}
        <form onSubmit={handleUpdateProfile} className="space-y-4 bg-card p-6 rounded-lg border border-border">
          <h2 className="text-xl font-semibold">Personal Information</h2>

          <div className="space-y-2">
            <Label htmlFor="fullName">Full Name</Label>
            <Input 
              id="fullName" 
              type="text" 
              value={fullName} 
              onChange={(e) => setFullName(e.target.value)} 
              disabled={isLoading}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input 
              id="email" 
              type="email" 
              value={email} 
              onChange={(e) => setEmail(e.target.value)} 
              disabled={isLoading}
            />
          </div>

          <Button type="submit" disabled={isLoading}>
            {isLoading ? "Saving..." : "Save Changes"}
          </Button>
        </form>

        <Separator className="my-8" />

        {/* Form Password */}
        <form onSubmit={handleUpdatePassword} className="space-y-4 bg-card p-6 rounded-lg border border-border">
          <h2 className="text-xl font-semibold">Change Password</h2>

          <div className="space-y-2">
            <Label htmlFor="currentPassword">Current Password</Label>
            <div className="relative">
              <Input 
                id="currentPassword" 
                type={showPasswords ? "text" : "password"} 
                value={currentPassword} 
                onChange={(e) => setCurrentPassword(e.target.value)} 
                placeholder="Enter current password"
                disabled={isLoading}
              />
              <Button type="button" variant="ghost" size="icon" className="absolute right-0 top-0 h-full px-3" onClick={() => setShowPasswords(!showPasswords)}>
                {showPasswords ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </Button>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="newPassword">New Password</Label>
            <div className="relative">
              <Input 
                id="newPassword" 
                type={showNewPasswords ? "text" : "password"} 
                value={newPassword} 
                onChange={(e) => setNewPassword(e.target.value)} 
                placeholder="Enter new password"
                disabled={isLoading}
              />
              <Button type="button" variant="ghost" size="icon" className="absolute right-0 top-0 h-full px-3" onClick={() => setShowNewPasswords(!showNewPasswords)}>
                {showNewPasswords ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </Button>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirmNewPassword">Confirm New Password</Label>
            <div className="relative">
              <Input 
                id="confirmNewPassword" 
                type={showConfPasswords ? "text" : "password"} 
                value={confirmNewPassword} 
                onChange={(e) => setConfirmNewPassword(e.target.value)} 
                placeholder="Confirm new password"
                disabled={isLoading}
              />
              <Button type="button" variant="ghost" size="icon" className="absolute right-0 top-0 h-full px-3" onClick={() => setShowConfPasswords(!showConfPasswords)}>
                {showConfPasswords ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </Button>
            </div>
          </div>

          <Button type="submit" disabled={isLoading}>
            {isLoading ? "Updating..." : "Update Password"}
          </Button>
        </form>
      </main>
    </div>
  );
};

export default Profile;