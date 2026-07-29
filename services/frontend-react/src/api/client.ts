import axios from "axios";
import type { AnalysisResult } from "../types";


function resolveBaseUrl(): string {
  const { hostname, protocol } = window.location;
  // Codespaces forwards each port as <codespace-name>-<port>.<domain>
  const m = hostname.match(/^(.+)-\d+((?:\.[a-z0-9-]+)+)$/i);
  if (m) return `${protocol}//${m[1]}-8080${m[2]}`; // swap our port for the API's
  return import.meta.env.VITE_API_BASE_URL || "http://localhost:8080";
}

const BASE_URL = resolveBaseUrl();



const client = axios.create({ baseURL: BASE_URL });

// Attach the JWT to every outgoing request automatically, if present
client.interceptors.request.use((config) => {
  const token = localStorage.getItem("meridian_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Centralized error handling: if the token is invalid/expired, force logout
// so the user isn't stuck in a broken state seeing confusing errors
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("meridian_token");
      localStorage.removeItem("meridian_user");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export async function login(username: string, password: string) {
  const response = await client.post("/auth/login", { username, password });
  return response.data as { access_token: string; role: string };
}

export async function analyze(ticker: string, query: string, timeoutMs = 180000) {
  const response = await client.post<AnalysisResult>(
    "/analyze",
    { ticker, query },
    { timeout: timeoutMs }
  );
  return response.data;
}

export default client;
