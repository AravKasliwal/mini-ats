import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, session } from "../api";

type Rubric = { name: string; category: string; weight: number; description: string; keywords: string[] };

export default function Jobs() {
  const isRec = session.user?.role === "recruiter";
  const [jobs, setJobs] = useState<any[]>([]);
  const [cands, setCands] = useState<any[]>([]);
  const [err, setErr] = useState("");
  const [title, setTitle] = useState("");
  const [crit, setCrit] = useState<Rubric[]>([{ name: "", category: "skills", weight: 1, description: "", keywords: [] }]);
  const load = () => { api("/jobs").then(setJobs); api("/candidates").then(setCands); };
  useEffect(load, []);
  const run = (p: Promise<unknown>) => p.then(load).catch((e: Error) => setErr(e.message));

  async function upload(jobId: number, e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0]; if (!f) return;
    const fd = new FormData(); fd.append("job_id", String(jobId)); fd.append("file", f);
    run(api("/candidates", { method: "POST", body: fd })); e.target.value = "";
  }
  const setC = (i: number, patch: Partial<Rubric>) => setCrit(crit.map((c, j) => (j === i ? { ...c, ...patch } : c)));

  return (<>
    {err && <p className="err">{err}</p>}
    {jobs.map(j => (
      <div className="card" key={j.id}>
        <div className="row"><h3 style={{ margin: 0, flex: 1 }}>{j.title}</h3>
          {isRec && <><label>Upload resume (PDF/txt) <input type="file" accept=".pdf,.txt,.md" onChange={e => upload(j.id, e)} /></label>
            <button className="ghost" onClick={() => run(api(`/jobs/${j.id}`, { method: "DELETE" }))}>Delete</button></>}</div>
        <small>{j.rubric.map((r: any) => `${r.name} (×${r.weight})`).join(" · ")} — pass ≥ {j.pass_threshold}</small>
        <table><tbody>{cands.filter(c => c.job_id === j.id).map(c => (
          <tr key={c.id}><td><Link to={`/candidates/${c.id}`}>{c.name}</Link></td>
            <td>{c.latest_total == null ? "not scored" : `${c.latest_total}/100`}</td></tr>))}</tbody></table>
      </div>))}
    {isRec && <div className="card"><h3>New job + rubric</h3>
      <div className="row"><input placeholder="Job title" value={title} onChange={e => setTitle(e.target.value)} /></div>
      {crit.map((c, i) => (<div className="row" key={i}>
        <input placeholder="Criterion" value={c.name} onChange={e => setC(i, { name: e.target.value })} />
        <select value={c.category} onChange={e => setC(i, { category: e.target.value })}>
          <option>skills</option><option>experience</option><option>education</option></select>
        <input type="number" min={0.5} step={0.5} style={{ width: 70 }} value={c.weight} onChange={e => setC(i, { weight: +e.target.value })} />
        <input placeholder="description" value={c.description} onChange={e => setC(i, { description: e.target.value })} />
        <input placeholder="keywords, comma separated" value={c.keywords.join(", ")}
          onChange={e => setC(i, { keywords: e.target.value.split(",").map(s => s.trim()).filter(Boolean) })} />
      </div>))}
      <div className="row"><button className="ghost" onClick={() => setCrit([...crit, { name: "", category: "skills", weight: 1, description: "", keywords: [] }])}>+ criterion</button>
        <button disabled={!title || crit.some(c => !c.name)} onClick={() => run(api("/jobs", { method: "POST", json: { title, rubric: crit } }).then(() => setTitle("")))}>Create job</button></div>
    </div>}
  </>);
}
