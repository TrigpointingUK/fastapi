const API_BASE = import.meta.env.VITE_API_BASE as string;

export async function apiGet<T>(url: string, token?: string): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    method: "GET",
    headers: {
      Accept: "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    // No credentials - using Bearer tokens only
  });
  
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status}: ${text || res.statusText}`);
  }
  
  return res.json() as Promise<T>;
}

export async function apiPost<T>(
  url: string,
  data: unknown,
  token?: string
): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(data),
  });
  
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status}: ${text || res.statusText}`);
  }
  
  return res.json() as Promise<T>;
}

