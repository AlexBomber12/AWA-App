"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

type ToastVariant = "default" | "success" | "error";

type ToastAction = {
  label: string;
  onClick: () => void;
};

export type ToastOptions = {
  title: string;
  description?: string;
  variant?: ToastVariant;
  duration?: number;
  action?: ToastAction;
};

type ToastRecord = ToastOptions & {
  id: string;
};

type ToastContextValue = {
  pushToast: (toast: ToastOptions) => string;
  dismissToast: (id: string) => void;
  clearToasts: () => void;
};

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

const variantStyles: Record<ToastVariant, string> = {
  default: "border-border bg-background/95 text-foreground",
  success: "border-emerald-200 bg-emerald-50 text-emerald-900",
  error: "border-red-200 bg-red-50 text-red-900",
};

const DEFAULT_DURATION = 5000;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastRecord[]>([]);
  const timersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());
  const counterRef = useRef(0);

  const clearTimer = useCallback((id: string) => {
    const timer = timersRef.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timersRef.current.delete(id);
    }
  }, []);

  const dismissToast = useCallback(
    (id: string) => {
      setToasts((current) => current.filter((toast) => toast.id !== id));
      clearTimer(id);
    },
    [clearTimer]
  );

  const clearToasts = useCallback(() => {
    timersRef.current.forEach((_, id) => clearTimer(id));
    timersRef.current.clear();
    setToasts([]);
  }, [clearTimer]);

  const pushToast = useCallback(
    (toast: ToastOptions) => {
      counterRef.current += 1;
      const id = `toast-${counterRef.current}`;
      const record: ToastRecord = {
        id,
        ...toast,
        variant: toast.variant ?? "default",
      };
      setToasts((current) => [...current, record]);

      const duration = typeof toast.duration === "number" ? toast.duration : DEFAULT_DURATION;
      if (duration > 0) {
        const timerId = setTimeout(() => dismissToast(id), duration);
        timersRef.current.set(id, timerId);
      }

      return id;
    },
    [dismissToast]
  );

  useEffect(() => {
    const timers = timersRef.current;
    return () => {
      timers.forEach((timer) => clearTimeout(timer));
      timers.clear();
    };
  }, []);

  const contextValue = useMemo(
    () => ({
      pushToast,
      dismissToast,
      clearToasts,
    }),
    [pushToast, dismissToast, clearToasts]
  );

  return (
    <ToastContext.Provider value={contextValue}>
      {children}
      <div className="pointer-events-none fixed inset-x-0 top-4 z-50 flex flex-col items-center gap-3 px-4">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            role="status"
            className={cn(
              "pointer-events-auto w-full max-w-sm rounded-xl border px-4 py-3 shadow-lg transition-all",
              variantStyles[toast.variant ?? "default"]
            )}
          >
            <div className="flex items-start gap-3">
              <div className="flex-1 space-y-1">
                <p className="text-sm font-semibold">{toast.title}</p>
                {toast.description ? <p className="text-xs text-muted-foreground">{toast.description}</p> : null}
              </div>
              <div className="flex flex-col items-end gap-2">
                {toast.action ? (
                  <button
                    type="button"
                    className="rounded-md border border-current px-3 py-1 text-xs font-semibold uppercase tracking-wide"
                    onClick={() => {
                      toast.action?.onClick?.();
                      dismissToast(toast.id);
                    }}
                  >
                    {toast.action.label}
                  </button>
                ) : null}
                <button
                  type="button"
                  className="text-xs font-semibold uppercase tracking-wide opacity-70 transition-opacity hover:opacity-100"
                  onClick={() => dismissToast(toast.id)}
                  aria-label="Dismiss notification"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}
