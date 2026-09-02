const DEFAULT_API_BASE_URL = 'http://127.0.0.1:8000';

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? DEFAULT_API_BASE_URL;

type QueryValue = string | number | boolean | undefined | null;

export async function apiGet<T>(path: string, params?: Record<string, QueryValue>): Promise<T> {
  const url = new URL(`${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`);

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
