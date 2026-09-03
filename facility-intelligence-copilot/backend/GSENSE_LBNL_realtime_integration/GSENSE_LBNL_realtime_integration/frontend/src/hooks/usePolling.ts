import { useEffect, useRef } from 'react';

export function usePolling<T>(callback: () => Promise<T>, intervalMs: number, enabled = true): { refresh: () => Promise<T | undefined> } {
  const timeoutRef = useRef<number | null>(null);

  const run = async (): Promise<T | undefined> => {
    try {
      return await callback();
    } catch (error) {
      console.error('Polling callback failed:', error);
      return undefined;
    }
  };

  useEffect(() => {
    if (!enabled) {
      return undefined;
    }

    let isMounted = true;

    const tick = async () => {
      if (!isMounted) {
        return;
      }

      await run();
      timeoutRef.current = window.setTimeout(tick, intervalMs);
    };

    void tick();

    return () => {
      isMounted = false;
      if (timeoutRef.current !== null) {
        window.clearTimeout(timeoutRef.current);
      }
    };
  }, [callback, enabled, intervalMs]);

  return { refresh: run };
}
