type QueryValue = string | number | boolean | null | undefined;

const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api/v1';

const buildUrl = (path: string, params?: Record<string, QueryValue>) => {
  const url = new URL(`${API_BASE_URL.replace(/\/$/, '')}/${path.replace(/^\//, '')}`);
  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      url.searchParams.set(key, String(value));
    }
  });
  return url.toString();
};

const parseJson = async <T>(response: Response): Promise<T> => {
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
};

export const apiGet = async <T>(path: string, params?: Record<string, QueryValue>) => (
  parseJson<T>(await fetch(buildUrl(path, params)))
);

export const apiPost = async <T>(path: string, body: unknown) => (
  parseJson<T>(await fetch(buildUrl(path), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }))
);
