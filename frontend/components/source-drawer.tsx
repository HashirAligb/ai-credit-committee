import type { Rule } from "../lib/api";

// Slide-over that shows the contract sentence behind a loan rule.
export function SourceDrawer({ rule, onClose }: { rule: Rule | null; onClose: () => void }) {
  if (!rule) return null;
  return (
    <div className="fixed inset-0 z-10 flex justify-end bg-slate-950/70" onClick={onClose}>
      <aside className="panel h-full w-full max-w-md rounded-none border-y-0 border-r-0 p-7" onClick={(e) => e.stopPropagation()}>
        <p className="mb-1 text-sm font-bold text-cyan-300">Credit agreement §{rule.section}</p>
        <p className="mb-6 text-xs text-slate-400">The sentence this rule comes from</p>
        <blockquote className="border-l-2 border-cyan-300 pl-4 text-lg leading-8">“{rule.quote}”</blockquote>
        <button onClick={onClose} className="mt-8 text-sm text-slate-400 hover:text-white">Close</button>
      </aside>
    </div>
  );
}
