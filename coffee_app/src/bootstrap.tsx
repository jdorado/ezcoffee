import {useEffect,useState} from 'react'
import {createRoot} from 'react-dom/client'
import {PrivyProvider,usePrivy} from '@privy-io/react-auth'
import App from './main'
import {setAccessTokenProvider} from './api'
import Icon from './components/ui/Icon'
import LoadingLogbook from './components/LoadingLogbook'
import './style.css'
import {profile} from './profile'
declare const process:{env:{NODE_ENV?:string;PRIVY_APP_ID?:string;PRIVY_CLIENT_ID?:string}}
function AuthenticatedApp(){
 const {ready,authenticated,login,logout,getAccessToken}=usePrivy()
 const [connected,setConnected]=useState(false)
 useEffect(()=>{setAccessTokenProvider(getAccessToken);setConnected(true);return()=>setAccessTokenProvider(async()=>null)},[getAccessToken])
 if(!ready||!connected)return <LoadingLogbook/>
 if(!authenticated)return <div className="sign-in"><span className="brand-icon"><Icon name="cup"/></span><h1>Coffee logbook</h1><p>Your coffees. Your shots. Your daily ritual.</p><button className="primary" onClick={login}>Sign in</button></div>
 return <App onLogout={logout}/>
}
const appId=process.env.PRIVY_APP_ID
const production=process.env.NODE_ENV==='production'
if(production&&profile.mode==='personal'&&!appId)throw new Error('The personal profile requires PRIVY_APP_ID')
createRoot(document.getElementById('app')!).render(appId?<PrivyProvider appId={appId} clientId={process.env.PRIVY_CLIENT_ID||undefined} config={{loginMethods:['google','email'],appearance:{theme:'light',accentColor:'#171717'}}}><AuthenticatedApp/></PrivyProvider>:<App/>)

if(production && 'serviceWorker' in navigator){
 window.addEventListener('load',()=>{
  navigator.serviceWorker.register('/sw.js',{updateViaCache:'none'})
   .catch(error=>console.warn('App installation support is unavailable',error))
 })
}
