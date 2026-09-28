/** Small, legible cow mark for headers; full illustrations live in public/assets. */
export function BullMark({ size = 28, className = '', strokeWidth = 2.5 }: { size?: number; className?: string; strokeWidth?: number }) {
  return <svg width={size} height={size} viewBox="0 0 48 48" fill="none" className={className} aria-hidden="true">
    <path d="M14 17Q5 10 7 5Q16 6 18 13M34 17Q43 10 41 5Q32 6 30 13" fill="#EDBD65" stroke="currentColor" strokeWidth={strokeWidth} strokeLinejoin="round" />
    <path d="M13 17Q1 11 3 22Q6 28 13 24M35 17Q47 11 45 22Q42 28 35 24" fill="#F0B6A0" stroke="currentColor" strokeWidth={strokeWidth} />
    <rect x="11" y="11" width="26" height="31" rx="12" fill="#FFF7E7" stroke="currentColor" strokeWidth={strokeWidth} />
    <path d="M17 12Q28 8 26 20Q19 25 16 17" fill="currentColor" />
    <circle cx="18" cy="27" r="1.7" fill="currentColor" /><circle cx="30" cy="27" r="1.7" fill="currentColor" />
    <rect x="13" y="30" width="22" height="12" rx="6" fill="#F0B6A0" stroke="currentColor" strokeWidth={strokeWidth * 0.8} />
    <path d="M19 35V36M29 35V36" stroke="currentColor" strokeWidth={strokeWidth} strokeLinecap="round" />
  </svg>
}
