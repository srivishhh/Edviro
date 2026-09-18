const DEFAULT_API_BASE_URL = '';

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? (import.meta.env.VITE_API_URL as string | undefined) ?? DEFAULT_API_BASE_URL;

type QueryValue = string | number | boolean | undefined | null;

export async function apiGet<T>(path: string, params?: Record<string, QueryValue>): Promise<T> {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  const baseUrl = API_BASE_URL || (typeof window !== 'undefined' ? window.location.origin : 'http://127.0.0.1:8000');
  const url = new URL(`${baseUrl}${normalizedPath}`);


  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') {
      return;
    }
    url.searchParams.set(key, String(value));
  });

  const response = await fetch(url.toString());

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with status ${response.status}`);
  }

  const contentType = response.headers.get('content-type') ?? '';
  if (contentType.includes('application/json')) {
    return (await response.json()) as T;
  }

  return (await response.text()) as unknown as T;
}
