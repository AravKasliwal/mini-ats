import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, session } from "../api";

export default function Login() {
  const nav = useNavigate();
  const [email, setEmail] = useState("recruiter@demo.com");
  const [password, setPassword] = useState("demo1234");
  const [err, setErr] = useState("");
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    try {
      const r = await api("/auth/login", { method: "POST", body: new URLSearchParams({ username: email, password }) });
      session.set(r.access_token, r.user);
      nav("/");
    } catch (e: any) { setErr(e.message); }
  }
  return (
    <main><form className="card" onSubmit={submit} style={{ maxWidth: 360, margin: "80px auto" }}>
      <h2>Mini ATS</h2>
      <div className="row"><input style={{ flex: 1 }} value={email} onChange={e => setEmail(e.target.value)} /></div>
      <div className="row"><input style={{ flex: 1 }} type="password" value={password} onChange={e => setPassword(e.target.value)} /></div>
      <button>Log in</button>{err && <p className="err">{err}</p>}
      <p><small>Demo: recruiter@demo.com or interviewer@demo.com / demo1234</small></p>
    </form></main>
  );
}
