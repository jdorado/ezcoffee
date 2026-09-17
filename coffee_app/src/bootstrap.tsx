import {useEffect,useState} from 'react'
import {createRoot} from 'react-dom/client'
import {PrivyProvider,usePrivy} from '@privy-io/react-auth'
import App from './main'
import {setAccessTokenProvider} from './api'
import LoadingLogbook from './components/LoadingLogbook'
import {captureInstallPrompt} from './installApp'
import './style.css'
declare const process:{env:{NODE_ENV?:string;PRIVY_APP_ID?:string;PRIVY_CLIENT_ID?:string}}
function AuthenticatedApp(){
 const {ready,authenticated,login,logout,getAccessToken}=usePrivy()
 const [connected,setConnected]=useState(false)
 useEffect(()=>{setAccessTokenProvider(getAccessToken);setConnected(true);return()=>setAccessTokenProvider(async()=>null)},[getAccessToken])
 if(!ready||!connected)return <main className="initial-loading-view"><LoadingLogbook/></main>
 if(!authenticated)return <main className="landing">
  <header className="landing-header">
   <img className="landing-logo" src="/ezcoffee-logo-header.png" alt="ezcoffee"/>
   <span>A coffee logbook</span>
  </header>
  <section className="landing-hero">
   <div className="landing-copy">
    <p className="landing-kicker">Brew with intention</p>
    <h1>Remember what<br/>made it <em>good.</em></h1>
    <p className="landing-intro">A focused logbook for espresso and pour-over—with an expert barista that knows your shots, learns your taste, and helps you brew the next one better.</p>
    <button className="landing-cta" onClick={login}>
     Start your logbook
     <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M4 10h11M11 6l4 4-4 4" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
    </button>
    <small>Free to use · Sign in or create an account</small>
   </div>
   <div className="landing-preview" aria-hidden="true">
    <div className="preview-meta"><span>Today · 08:42</span><span className="preview-status">Well brewed</span></div>
    <div className="preview-coffee"><i/>Ethiopia · Natural</div>
    <div className="preview-metrics">
     <div><span>Coffee</span><strong>18<small>g</small></strong></div>
     <div><span>Out</span><strong>36<small>g</small></strong></div>
     <div><span>Time</span><strong>29<small>s</small></strong></div>
    </div>
    <div className="preview-note"><span>Taste note</span>Sweet, bright and balanced. Stone fruit finish.</div>
    <div className="preview-tags"><span>1 : 2</span><span>Grind 8</span><span>Temp I</span></div>
    <div className="preview-advice">
     <div><i/><span>Your barista</span><small>Knows your last 8 shots</small></div>
     <p>You like this coffee brighter. Try one click coarser and stop at 34 g.</p>
    </div>
   </div>
  </section>
  <footer className="landing-footer"><span>Espresso</span><i/><span>Pour-over</span><i/><span>Your way</span></footer>
 </main>
 return <App onLogout={logout}/>
}
const appId=process.env.PRIVY_APP_ID
const production=process.env.NODE_ENV==='production'
if(!appId)throw new Error('The authenticated profile requires PRIVY_APP_ID')
captureInstallPrompt()
createRoot(document.getElementById('app')!).render(<PrivyProvider appId={appId} clientId={process.env.PRIVY_CLIENT_ID||undefined} config={{loginMethods:['google','email'],appearance:{theme:'light',accentColor:'#171717'}}}><AuthenticatedApp/></PrivyProvider>)

if(production && 'serviceWorker' in navigator){
 window.addEventListener('load',()=>{
  navigator.serviceWorker.register('/sw.js',{updateViaCache:'none'})
   .catch(error=>console.warn('App installation support is unavailable',error))
 })
}
