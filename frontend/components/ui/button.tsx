export function Button({ children, onClick, type = "button", variant = "primary", disabled = false }: { children: React.ReactNode; onClick?: () => void; type?: "button" | "submit"; variant?: "primary" | "secondary"; disabled?: boolean }) {
  const style = variant === "primary" ? "bg-cyan-400 font-bold text-slate-950 hover:bg-cyan-300" : "border border-slate-600 font-semibold text-white hover:bg-slate-700";
  return <button type={type} onClick={onClick} disabled={disabled} className={`rounded-xl px-5 py-3 transition disabled:cursor-not-allowed disabled:opacity-50 ${style}`}>{children}</button>;
}
