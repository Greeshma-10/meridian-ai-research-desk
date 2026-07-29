import { createContext, useContext, useState, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { login as apiLogin } from "../api/client";
import type { User } from "../types";

interface AuthContextValue {
  user: User | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
  error: string | null;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    const stored = localStorage.getItem("meridian_user");
    return stored ? JSON.parse(stored) : null;
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  async function login(username: string, password: string) {
    setLoading(true);
    setError(null);
    try {
      const { access_token, role } = await apiLogin(username, password);
      const loggedInUser: User = { username, role: role as "user" | "admin" };
      localStorage.setItem("meridian_token", access_token);
      localStorage.setItem("meridian_user", JSON.stringify(loggedInUser));
      setUser(loggedInUser);
      navigate("/");
    } catch (err: any) {
      setError(
        err.response?.data?.detail || "Login failed — check your username and password."
      );
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    localStorage.removeItem("meridian_token");
    localStorage.removeItem("meridian_user");
    setUser(null);
    navigate("/login");
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, loading, error }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
