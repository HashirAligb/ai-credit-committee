export const money = (n: number) => `$${Math.round(n / 1e6).toLocaleString("en-US")}M`;
export const ratio = (n: number | null) => (n === null ? "—" : `${n.toFixed(2)}x`);
