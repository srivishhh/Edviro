import { createContext, useContext, useState, type ReactNode } from 'react';
import { AlertCircle, CheckCircle, Info, X, XCircle } from 'lucide-react';

type ToastType = 'success' | 'error' | 'warning' | 'info';

interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message: string;
}

interface ToastContextType {
  showToast: (type: ToastType, title: string, message: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = (type: ToastType, title: string, message: string) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, type, title, message }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 pointer-events-none max-w-sm w-full">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className="pointer-events-auto flex items-start gap-3 p-4 rounded-xl bg-white border border-zinc-200/80 shadow-lg animate-fadeIn text-xs"
          >
            {toast.type === 'success' && <CheckCircle className="text-emerald-600 shrink-0 mt-0.5" size={16} />}
            {toast.type === 'error' && <XCircle className="text-rose-600 shrink-0 mt-0.5" size={16} />}
            {toast.type === 'warning' && <AlertCircle className="text-amber-600 shrink-0 mt-0.5" size={16} />}
            {toast.type === 'info' && <Info className="text-zinc-700 shrink-0 mt-0.5" size={16} />}
            
            <div className="flex-1 space-y-0.5">
              <p className="font-bold text-zinc-900">{toast.title}</p>
              <p className="text-zinc-600 leading-relaxed">{toast.message}</p>
            </div>

            <button
              onClick={() => removeToast(toast.id)}
              className="text-zinc-400 hover:text-zinc-600 cursor-pointer"
            >
              <X size={14} />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}
