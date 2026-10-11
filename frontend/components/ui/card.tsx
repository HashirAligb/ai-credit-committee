export function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <section className={`panel p-5 ${className}`}>{children}</section>;
}
