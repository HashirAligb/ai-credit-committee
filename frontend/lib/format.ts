// $1B and up as $4.36B, smaller amounts as $350M.
export const money = (n: number) =>
  Math.abs(n) >= 1e9 ? `$${(n / 1e9).toFixed(2)}B` : `$${Math.round(n / 1e6).toLocaleString("en-US")}M`;
export const ratio = (n: number | null) => (n === null ? "—" : `${n.toFixed(2)}x`);
