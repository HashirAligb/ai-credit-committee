import type { Rule } from "../lib/api";
import { ruleNames } from "./rules-panel";

// Slide-over that shows the contract sentence behind a loan rule.
export function SourceDrawer({ rule, onClose }: { rule: Rule | null; onClose: () => void }) {
  if (!rule) return null;
  return (
    <div className="fixed inset-0 z-10 flex justify-end bg-slate-950/70" onClick={onClose}>
      <aside className="panel h-full w-full max-w-md overflow-y-auto rounded-none border-y-0 border-r-0 p-7" onClick={(e) => e.stopPropagation()}>
        <p className="mb-1 text-sm font-bold text-cyan-300">Credit agreement §{rule.section}</p>
        <p className="mb-6 text-xs text-slate-400">{ruleNames[rule.type]} · the sentence this rule comes from</p>
        <blockquote className="border-l-2 border-cyan-300 pl-4 text-lg leading-8">“{rule.quote}”</blockquote>
        {rule.schedule.length > 1 && (
          <table className="mt-6 w-full text-sm">
            <thead><tr className="text-left text-xs text-slate-400"><th className="pb-2 font-normal">Period</th><th className="pb-2 text-right font-normal">Limit</th></tr></thead>
            <tbody>
              {rule.schedule.map((step, index) => (
                <tr key={step.year} className="border-t border-slate-700/70">
                  <td className="py-2">{index === 0 ? `Through ${step.year}` : index === rule.schedule.length - 1 ? `${step.year} onward` : step.year}</td>
                  <td className="py-2 text-right font-semibold">{step.threshold.toFixed(2)}x</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {rule.source_url && (
          <a href={rule.source_url} target="_blank" rel="noreferrer" className="mt-6 block text-sm text-cyan-300 underline hover:text-cyan-200">
            Open the credit agreement amendment on SEC.gov ↗
          </a>
        )}
        <button onClick={onClose} className="mt-8 text-sm text-slate-400 hover:text-white">Close</button>
      </aside>
    </div>
  );
}
