import {createRoot} from 'react-dom/client'
import App from './main'
import './style.css'

createRoot(document.getElementById('app')!).render(<App/>)

if('serviceWorker' in navigator){
 window.addEventListener('load',()=>{
  navigator.serviceWorker.register('/sw.js',{updateViaCache:'none'})
   .catch(error=>console.warn('App installation support is unavailable',error))
 })
}
