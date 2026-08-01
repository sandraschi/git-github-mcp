import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useState,
} from "react";

type LoggerContextValue = {
  lines: string[];
  append: (level: string, msg: string) => void;
};

const LoggerContext = createContext<LoggerContextValue | null>(null);

export function LoggerProvider({ children }: { children: ReactNode }) {
  const [lines, setLines] = useState<string[]>([]);
  const append = useCallback((level: string, msg: string) => {
    const stamp = new Date().toLocaleTimeString();
    setLines((prev) => [`[${stamp}] [${level}] ${msg}`, ...prev].slice(0, 200));
  }, []);
  return (
    <LoggerContext.Provider value={{ lines, append }}>
      {children}
    </LoggerContext.Provider>
  );
}

export function useLogger() {
  const ctx = useContext(LoggerContext);
  if (!ctx) {
    return { lines: [], append: () => {} };
  }
  return ctx;
}
