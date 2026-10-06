import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Link, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { session } from "./api";
import Login from "./pages/Login";
import Jobs from "./pages/Jobs";
import CandidateDetail from "./pages/CandidateDetail";
import "./style.css";

function Shell({ children }: { children: React.ReactNode }) {
  const nav = useNavigate();
  const u = session.user;
  if (!u) return <Navigate to="/login" />;
  return (
    <>
      <header><Link to="/"><b>Mini ATS</b></Link><span>{u.name} · {u.role}
        <button onClick={() => { session.clear(); nav("/login"); }}>Log out</button></span></header>
      <main>{children}</main>
    </>
  );
}

createRoot(document.getElementById("root")!).render(
  <BrowserRouter><Routes>
    <Route path="/login" element={<Login />} />
    <Route path="/" element={<Shell><Jobs /></Shell>} />
    <Route path="/candidates/:id" element={<Shell><CandidateDetail /></Shell>} />
  </Routes></BrowserRouter>
);
