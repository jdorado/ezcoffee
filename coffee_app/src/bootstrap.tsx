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
 if(!ready||!connected)return <LoadingLogbook/>
 if(!authenticated)return <div className="sign-in"><img className="sign-in-logo" src="/ezcoffee-logo-header.png" alt="ezcoffee"/><p>Your coffees. Your brews. Your daily ritual.</p><button className="primary" onClick={login}>Sign in</button></div>
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
