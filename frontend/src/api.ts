export type User = { id: number; email: string; name: string; role: "recruiter" | "interviewer" };
export const session = {
  get token() { return localStorage.getItem("token"); },
  get user(): User | null { const u = localStorage.getItem("user"); return u ? JSON.parse(u) : null; },
  set(token: string, user: User) { localStorage.setItem("token", token); localStorage.setItem("user", JSON.stringify(user)); },
  clear() { localStorage.removeItem("token"); localStorage.removeItem("user"); },
};

export async function api<T = any>(path: string, opts: RequestInit & { json?: unknown } = {}): Promise<T> {
  const headers: Record<string, string> = {};
  if (session.token) headers.Authorization = `Bearer ${session.token}`;
  let body = opts.body;
  if (opts.json !== undefined) { headers["Content-Type"] = "application/json"; body = JSON.stringify(opts.json); }
  const res = await fetch(`/api${path}`, { ...opts, headers: { ...headers, ...(opts.headers as object) }, body });
  if (res.status === 401 && path !== "/auth/login") { session.clear(); location.href = "/"; }
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText);
  return res.status === 204 ? (undefined as T) : res.json();
}
