"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "../components/ui/button";

export default function Home() {
  const [ticker, setTicker] = useState("PZCO");
  const router = useRouter();
  return <main className="mx-auto flex min-h-screen max-w-5xl items-center px-6">
    <div className="max-w-2xl"><p className="mb-5 text-sm font-bold uppercase tracking-[0.3em] text-cyan-300">AI Credit Committee</p>
      <h1 className="text-6xl font-black leading-tight">Make the lending call <span className="text-cyan-300">before the market does.</span></h1>
      <p className="mt-6 text-lg text-slate-300">A transparent AI committee stress-tests cash flow, covenants, and refinancing risk in seconds.</p>
      <form className="mt-10 flex max-w-md gap-3" onSubmit={(e) => { e.preventDefault(); router.push(`/run/${ticker.toUpperCase()}`); }}>
        <input value={ticker} onChange={(e) => setTicker(e.target.value)} className="w-full rounded-xl border border-slate-600 bg-slate-900 px-4 py-3 uppercase outline-none focus:border-cyan-300" placeholder="Ticker" />
        <Button type="submit">Run committee</Button>
      </form>
      <p className="mt-4 text-sm text-slate-500">Try PZCO — Pizza Co. is a fictional demo borrower.</p>
    </div>
  </main>;
}
