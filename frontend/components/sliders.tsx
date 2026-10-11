import { Card } from "./ui/card";

type Props = { drop: number; rate: number; onDrop: (value: number) => void; onRate: (value: number) => void };

export function Sliders({ drop, rate, onDrop, onRate }: Props) {
  return (
    <Card>
      <h2 className="mb-5 text-lg font-bold">What-if controls</h2>
      <label htmlFor="drop" className="mb-2 flex justify-between text-sm text-slate-300">
        Earnings decline <b className="text-cyan-300">{drop}%</b>
      </label>
      <input id="drop" className="mb-8 w-full accent-cyan-300" type="range" min="0" max="60" value={drop} onChange={(e) => onDrop(+e.target.value)} />
      <label htmlFor="rate" className="mb-2 flex justify-between text-sm text-slate-300">
        Refinancing rate <b className="text-cyan-300">{+rate.toFixed(2)}%</b>
      </label>
      <input id="rate" className="w-full accent-cyan-300" type="range" min="0.5" max="15" step="0.1" value={rate} onChange={(e) => onRate(+e.target.value)} />
    </Card>
  );
}
