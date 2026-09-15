export function LogoMark({ size = 24 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect width="24" height="24" rx="7" className="fill-primary" />
      <path
        d="M7 15.5 10 11l2.5 2.8L17 8.5"
        stroke="var(--primary-foreground)"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      <circle cx="17" cy="8.5" r="1.6" className="fill-primary-foreground" />
    </svg>
  );
}
