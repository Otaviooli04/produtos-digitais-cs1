// Marca do sistema (mesmo símbolo do favicon).
export default function Logo({ className = 'w-8 h-8' }) {
  return (
    <svg className={className} viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="logoGrad" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
          <stop stopColor="#8b5cf6" />
          <stop offset="1" stopColor="#6d28d9" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="8" fill="url(#logoGrad)" />
      <g fill="#fff">
        <rect x="7" y="17" width="4.2" height="9" rx="2.1" />
        <rect x="13.9" y="12" width="4.2" height="14" rx="2.1" />
        <rect x="20.8" y="7" width="4.2" height="19" rx="2.1" />
      </g>
      <polyline
        points="9.1,14 16,9 22.9,4.5"
        fill="none" stroke="#fff" strokeOpacity="0.5"
        strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"
      />
      <g fill="#fff" fillOpacity="0.9">
        <circle cx="9.1" cy="14" r="1.5" />
        <circle cx="16" cy="9" r="1.5" />
        <circle cx="22.9" cy="4.5" r="1.5" />
      </g>
    </svg>
  )
}
