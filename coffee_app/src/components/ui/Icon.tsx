type Name = 'cup' | 'chat' | 'plus' | 'arrow' | 'edit' | 'bean' | 'close' | 'check' | 'lock' | 'logout' | 'install' | 'retry' | 'expand' | 'shrink'
const paths: Record<Name, JSX.Element> = {
 cup: <><path d="M5 8h11v6a5.5 5.5 0 0 1-11 0V8Z"/><path d="M16 9h2a3 3 0 0 1 0 6h-2M3 21h16M8 3v2m5-2v2"/></>,
 chat: <path d="M20 11.5a7.5 7.5 0 0 1-7.5 7.5H5l-3 3V11.5A7.5 7.5 0 0 1 9.5 4h3a7.5 7.5 0 0 1 7.5 7.5Z"/>,
 plus: <path d="M12 5v14M5 12h14"/>,
 arrow: <path d="M5 12h14m-5-5 5 5-5 5"/>,
 edit: <><path d="m15 4 5 5M4 20l5-1L21 7a2 2 0 0 0-5-5L4 14v6Z"/></>,
 bean: <><ellipse cx="12" cy="12" rx="7" ry="10" transform="rotate(35 12 12)"/><path d="M17 4c-8 2-2 14-10 16"/></>,
 close: <path d="m6 6 12 12M6 18 18 6"/>,
 logout: <><path d="M9 4H4v16h5m5-13 5 5-5 5M9 12h10"/></>,
 check: <path d="m5 12 4 4L19 6"/>,
 lock: <><rect x="5" y="10" width="14" height="10" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3m-4 4v2"/></>,
 install: <><path d="M12 3v12m-4-4 4 4 4-4"/><path d="M5 20h14"/></>,
 retry: <><path d="M4 7v5h5"/><path d="M4.7 12A8 8 0 1 0 7 5.7L4 8"/></>,
 expand: <><path d="M9 4H4v5M15 4h5v5M9 20H4v-5M15 20h5v-5"/></>,
 shrink: <><path d="M4 9h5V4M20 9h-5V4M4 15h5v5M20 15h-5v5"/></>,
}
export default function Icon({name}: {name: Name}) {
 return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>
}
