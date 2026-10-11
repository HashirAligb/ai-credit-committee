export function Button({ children, onClick, type = "button", variant = "primary" }: { children: React.ReactNode; onClick?: () => void; type?: "button" | "submit"; variant?: "primary" | "secondary" }) {
  return <button type={type} onClick={onClick} className={variant === "primary" ? "rounded-xl bg-cyan-400 px-5 py-3 font-bold text-slate-950 transition hover:bg-cyan-300" : "rounded-xl border border-slate-600 px-5 py-3 font-semibold text-white hover:bg-slate-700"}>{children}</button>;
}
