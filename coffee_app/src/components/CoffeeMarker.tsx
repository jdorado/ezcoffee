// Keep the existing API keys so saved canister assignments stay intact.
export const coffeeMarkers = [
 {value:'black', label:'Blackberry', fruit:'blackberry'},
 {value:'green', label:'Watermelon', fruit:'watermelon'},
 {value:'red', label:'Cherries', fruit:'cherries'},
 {value:'blue', label:'Lemon', fruit:'lemon'},
 {value:'orange', label:'Pineapple', fruit:'pineapple'},
 {value:'purple', label:'Strawberry', fruit:'strawberry'},
] as const

type Fruit = typeof coffeeMarkers[number]['fruit']
const artwork: Record<Fruit, JSX.Element> = {
 blackberry: <>
  <path fill="#58a77c" d="m25 16-11-5 8-1-1-8 7 6 7-3-2 8 7 4-12 3Z"/>
  <path fill="#9e509a" stroke="#fffdf0" strokeWidth="2" d="M19 14c-4-2-9 1-9 5-5 1-7 6-5 10-3 4-1 9 3 11 1 5 6 7 10 5 4 3 9 1 11-2 5 1 9-3 8-7 5-3 4-9 1-12 1-5-3-9-8-8-3-4-8-5-11-2Z"/>
  <path fill="none" stroke="#b769ac" strokeWidth="1.8" strokeLinecap="round" d="M15 20c2-2 5-1 6 1m5 0c3-1 5 1 5 3M9 29c2-2 5-2 7 0m4-1c3-2 6 0 6 2m4 0c3 0 4 2 3 4m-19 2c3-2 5-1 6 2m4-2c3-1 5 1 5 3"/>
 </>,
 watermelon: <>
  <path fill="#57a77d" stroke="#fffdf0" strokeWidth="2" strokeLinejoin="round" d="M5 38A33 33 0 0 1 38 5v33Z"/>
  <path fill="#f5f0c4" d="M9 36A27 27 0 0 1 36 9v27Z"/>
  <path fill="#ed4d83" d="M13 34A21 21 0 0 1 34 13v21Z"/>
  <g fill="#fff9e9">
   <ellipse cx="30" cy="18" rx="1.2" ry="2" transform="rotate(-12 30 18)"/>
   <ellipse cx="23" cy="23" rx="1.2" ry="2" transform="rotate(-40 23 23)"/>
   <ellipse cx="18" cy="30" rx="1.2" ry="2" transform="rotate(-65 18 30)"/>
  </g>
 </>,
 cherries: <>
  <path fill="none" stroke="#58a77c" strokeWidth="3.5" strokeLinecap="round" d="M14 30c7-8 13-13 15-23 1 11 4 16 8 20"/>
  <path fill="#58a77c" d="M29 11C22 2 15 4 14 5c3 7 8 9 15 6Z"/>
  <path fill="#e53976" stroke="#fffdf0" strokeWidth="2" d="M15 25c-8-4-15 3-12 11 2 7 9 10 14 6 8 0 12-15 3-17-2-1-3 0-5 0Zm22-3c-8-4-15 3-12 11 2 7 9 10 14 6 8 0 12-15 3-17-2-1-3 0-5 0Z"/>
 </>,
 lemon: <>
  <path fill="#f6df64" stroke="#fffdf0" strokeWidth="2" strokeLinejoin="round" d="M7 15c-2-3-1-7 3-7 3 0 4-4 11-4 12 0 20 9 20 21 0 6-4 10-2 14 2 5-3 7-7 3-5 1-12 1-18-3C5 33 3 23 7 15Z"/>
  <path fill="none" stroke="#e5c546" strokeWidth="1.5" strokeLinecap="round" d="M10 21c-1 6 2 11 6 14"/>
 </>,
 pineapple: <>
  <path fill="#f5c52f" stroke="#fffdf0" strokeWidth="2" d="M13 19C6 23 6 35 12 41c5 5 15 5 21 0 6-6 7-17 0-22-5-4-14-4-20 0Z"/>
  <path fill="none" stroke="#df9723" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" d="m13 25 3-2 2 3m4-3 3-2 2 3m4 1 2 2-1 3m-21 1 3-2 2 3m4-2 3-2 2 3m4 1 3-1 1 3m-20 3 3-2 2 3m5-2 3-2 2 3m-9 4 3-2 2 2"/>
  <path fill="#58a77c" stroke="#fffdf0" strokeWidth="1.5" strokeLinejoin="round" d="m24 23-9-4-3-10 6 2 1-8 6 5 6-6 1 9 7-2-3 10-12 4Z"/>
 </>,
 strawberry: <>
  <path fill="#e8457e" stroke="#fffdf0" strokeWidth="2" d="M9 13c-7 7-2 20 10 30 3 3 7 3 10 0 12-10 17-23 10-30-7-6-11-1-15-1s-8-5-15 1Z"/>
  <g fill="#fff7d9">
   <ellipse cx="13" cy="20" rx="1.3" ry="1.7"/><ellipse cx="22" cy="21" rx="1.3" ry="1.7"/><ellipse cx="32" cy="20" rx="1.3" ry="1.7"/>
   <ellipse cx="16" cy="29" rx="1.3" ry="1.7"/><ellipse cx="26" cy="29" rx="1.3" ry="1.7"/><ellipse cx="34" cy="28" rx="1.3" ry="1.7"/>
   <ellipse cx="22" cy="37" rx="1.3" ry="1.7"/><ellipse cx="29" cy="36" rx="1.3" ry="1.7"/>
  </g>
  <path fill="none" stroke="#58a77c" strokeWidth="3" strokeLinecap="round" d="m24 10 4-7"/>
  <path fill="#58a77c" d="m24 11-9-7 1 7-9 2 11 4 6-3 7 4 10-5-10-2 3-7-10 7Z"/>
 </>,
}

export default function CoffeeMarker({value, decorative=false}:{value?:string; decorative?:boolean}) {
 const marker=coffeeMarkers.find(marker=>marker.value===value)
 if(!marker)return null
 return <span className="coffee-marker" role={decorative?undefined:'img'} aria-label={decorative?undefined:marker.label+' canister marker'} aria-hidden={decorative||undefined} title={marker.label}>
  <svg viewBox="0 0 48 48" aria-hidden="true" focusable="false">{artwork[marker.fruit]}</svg>
 </span>
}
