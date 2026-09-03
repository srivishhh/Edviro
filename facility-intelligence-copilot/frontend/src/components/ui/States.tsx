import { AlertCircle, Loader2 } from 'lucide-react';

export function LoadingState({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center space-y-3">
      <Loader2 className="animate-spin text-zinc-900" size={24} />
      <p className="text-xs text-zinc-500 font-mono">{message}</p>
    </div>
  );
}

export function EmptyState({ message = 'No data available' }: { message?: string }) {
  return (
    <div className="p-8 rounded-2xl bg-zinc-50 border border-dashed border-zinc-200 text-center space-y-2">
      <p className="text-xs text-zinc-500">{message}</p>
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="p-8 rounded-2xl bg-rose-50/50 border border-rose-200 text-center space-y-3">
      <AlertCircle className="text-rose-600 mx-auto" size={24} />
      <p className="text-xs text-rose-800 font-mono">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-4 py-1.5 rounded-full bg-rose-700 text-white text-xs font-semibold cursor-pointer"
        >
          Retry
        </button>
      )}
    </div>
  );
}
