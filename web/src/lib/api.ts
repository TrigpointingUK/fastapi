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

export interface RotatePhotoRequest {
  angle: number;
}

export interface Photo {
  id: number;
  log_id: number;
  user_id: number;
  icon_url: string;
  photo_url: string;
  caption: string;
}

/**
 * Rotate a photo by a given angle (90, 180, or 270 degrees)
 */
export async function rotatePhoto(
  photoId: number,
  angle: number,
  token?: string
): Promise<Photo> {
  return apiPost<Photo>(`/v1/photos/${photoId}/rotate`, { angle }, token);
}

