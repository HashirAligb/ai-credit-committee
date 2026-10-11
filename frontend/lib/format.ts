// $1B and up as $4.36B, smaller amounts as $350M, negatives as -$99M.
export const money = (n: number) => {
  const sign = n < 0 ? "-" : "";
  const abs = Math.abs(n);
  return abs >= 1e9 ? `${sign}$${(abs / 1e9).toFixed(2)}B` : `${sign}$${Math.round(abs / 1e6).toLocaleString("en-US")}M`;
};
export const ratio = (n: number | null) => (n === null ? "—" : `${n.toFixed(2)}x`);
