"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "../components/ui/button";

const examples = [
  { ticker: "SLGN", name: "Silgan Holdings", note: "real company, FY2025 10-K" },
  { ticker: "PZCO", name: "Pizza Co.", note: "fictional example" },
];

export default function Home() {
  const [ticker, setTicker] = useState("SLGN");
  const router = useRouter();
  return <main className="mx-auto flex min-h-screen max-w-5xl items-center px-6">
    <div className="max-w-2xl"><p className="mb-5 text-sm font-bold uppercase tracking-[0.3em] text-cyan-300">AI Credit Committee</p>
      <h1 className="text-6xl font-black leading-tight">Make the lending call <span className="text-cyan-300">before the market does.</span></h1>
      <p className="mt-6 text-lg text-slate-300">A transparent AI committee stress-tests cash flow, covenants, and refinancing risk in seconds.</p>
      <form className="mt-10 flex max-w-md gap-3" onSubmit={(e) => { e.preventDefault(); router.push(`/run/${ticker.toUpperCase()}`); }}>
        <input value={ticker} onChange={(e) => setTicker(e.target.value)} className="w-full rounded-xl border border-slate-600 bg-slate-900 px-4 py-3 uppercase outline-none focus:border-cyan-300" placeholder="Ticker" />
        <Button type="submit">Run committee</Button>
      </form>
      <div className="mt-4 flex flex-wrap gap-2 text-sm text-slate-400">
        {examples.map((example) => (
          <button key={example.ticker} onClick={() => router.push(`/run/${example.ticker}`)} className="rounded-full border border-slate-700 px-3 py-1 hover:border-cyan-300">
            <b className="text-slate-200">{example.ticker}</b> · {example.name} <span className="text-slate-500">({example.note})</span>
          </button>
        ))}
      </div>
    </div>
  </main>;
}
