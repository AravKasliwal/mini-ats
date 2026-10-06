import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api, session } from "../api";

export default function CandidateDetail() {
  const { id } = useParams();
  const isRec = session.user?.role === "recruiter";
  const [c, setC] = useState<any>(null);
  const [ivs, setIvs] = useState<any[]>([]);
  const [who, setWho] = useState("");
  const [slot, setSlot] = useState("");
  const [err, setErr] = useState("");
  const [notes, setNotes] = useState<Record<number, string>>({});
  const load = () => api(`/candidates/${id}`).then(setC).catch((e: Error) => setErr(e.message));
  useEffect(() => { load(); if (isRec) api("/auth/interviewers").then(l => { setIvs(l); setWho(String(l[0]?.id ?? "")); }); }, [id]);
  const act = (p: Promise<unknown>) => p.then(load).catch((e: Error) => setErr(e.message));

  if (!c) return <p className={err ? "err" : ""}>{err || "Loading…"}</p>;
  const run = c.runs[0];
  return (<>
    {err && <p className="err">{err}</p>}
    <div className="card"><div className="row"><h2 style={{ margin: 0, flex: 1 }}>{c.name}</h2>
      {isRec && <button onClick={() => act(api(`/candidates/${id}/score`, { method: "POST" }))}>{run ? "Re-score" : "Score vs rubric"}</button>}</div>
      <small>{c.filename}</small></div>

    {run && <div className="card">
      <h3>Score: {run.total}/100 <span className={run.passed ? "pass" : "fail"}>{run.passed ? "PASS" : "BELOW THRESHOLD"}</span>
        <small> · scorer: {run.scorer}</small></h3>
      <table><tbody>{run.results.map((r: any) => (<tr key={r.criterion_id}>
        <td><b>{r.name}</b><br /><small>weight {r.weight}</small></td><td>{r.score}/5</td>
        <td>{r.rationale}{r.evidence.map((q: string, i: number) => <blockquote key={i}>{q}</blockquote>)}</td></tr>))}</tbody></table>
    </div>}

    <div className="card"><h3>Interviews</h3>
      {c.interviews.length === 0 && <p>None scheduled.</p>}
      {c.interviews.map((i: any) => (<div key={i.id} style={{ marginBottom: 16 }}>
        <p><b>{new Date(i.slot).toLocaleString()}</b> — {i.status}</p>
        {i.scorecards.map((sc: any) => (<div key={sc.id} className="card">
          <b>Scorecard: {sc.overall}/100 · {sc.recommendation.replace("_", " ")}</b> <small>scorer: {sc.scorer}</small>
          <table><tbody>{sc.results.map((r: any, k: number) => (<tr key={k}><td><b>{r.criterion}</b></td><td>{r.rating}/5</td>
            <td>{r.summary}{r.quotes.map((q: string, j: number) => <blockquote key={j}>{q}</blockquote>)}</td></tr>))}</tbody></table></div>))}
        <textarea rows={5} style={{ width: "100%", boxSizing: "border-box" }} placeholder="Paste interview notes / transcript…"
          value={notes[i.id] ?? ""} onChange={e => setNotes({ ...notes, [i.id]: e.target.value })} />
        <button disabled={(notes[i.id] ?? "").length < 20} onClick={() => act(api(`/interviews/${i.id}/scorecards`, { method: "POST", json: { transcript: notes[i.id] } }).then(() => setNotes({ ...notes, [i.id]: "" })))}>Generate scorecard</button>
      </div>))}
      {isRec && <div className="row"><select value={who} onChange={e => setWho(e.target.value)}>
        {ivs.map(u => <option key={u.id} value={u.id}>{u.name}</option>)}</select>
        <input type="datetime-local" value={slot} onChange={e => setSlot(e.target.value)} />
        <button disabled={!slot || !who} onClick={() => act(api(`/candidates/${id}/interviews`, { method: "POST", json: { interviewer_id: +who, slot: new Date(slot).toISOString() } }))}>Schedule (stub)</button></div>}
      <small>Scheduling is a stub: it stores a slot and assignee; no calendar or email integration.</small>
    </div>

    <div className="card"><h3>Resume</h3><pre>{c.resume_text}</pre></div>
  </>);
}
