import { createContext, useContext, useState, ReactNode } from "react";

interface User {
  id: string;
  email: string;
  fullName: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => void;
  register: (fullName: string, email: string, password: string) => void;
  logout: () => void;
  updateProfile: (fullName: string, email: string) => void;
  updatePassword: (currentPassword: string, newPassword: string) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);

  const login = (email: string, _password: string) => {
    // Mock login - just set user
    setUser({
      id: "1",
      email,
      fullName: "User Demo",
    });
  };

  const register = (fullName: string, email: string, _password: string) => {
    // Mock register - just set user
    setUser({
      id: "1",
      email,
      fullName,
    });
  };

  const logout = () => {
    setUser(null);
  };

  const updateProfile = (fullName: string, email: string) => {
    if (user) {
      setUser({ ...user, fullName, email });
    }
  };

  const updatePassword = (_currentPassword: string, _newPassword: string) => {
    // Mock password update - always succeed
    return true;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        updateProfile,
        updatePassword,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};