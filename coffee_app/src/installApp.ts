export type InstallKind='installed'|'native'|'ios-safari'|'ios-other'|'mac-safari'|'manual'

type InstallPromptEvent=Event&{
 prompt:()=>Promise<void>
 userChoice:Promise<{outcome:'accepted'|'dismissed'}>
}

const changeEvent='ezcoffee-install-change'
let deferredPrompt:InstallPromptEvent|null=null
let captureStarted=false

function standalone(){
 return window.matchMedia('(display-mode: standalone)').matches||
  (navigator as Navigator&{standalone?:boolean}).standalone===true
}

function safari(){
 const agent=navigator.userAgent
 return /Safari/i.test(agent)&&!/CriOS|FxiOS|EdgiOS|OPiOS|Chrome|Chromium|Android/i.test(agent)
}

function ios(){
 return /iPhone|iPad|iPod/i.test(navigator.userAgent)||
  (/Macintosh/i.test(navigator.userAgent)&&navigator.maxTouchPoints>1)
}

function changed(){window.dispatchEvent(new Event(changeEvent))}

export function captureInstallPrompt(){
 if(captureStarted)return
 captureStarted=true
 window.addEventListener('beforeinstallprompt',event=>{
  event.preventDefault()
  deferredPrompt=event as InstallPromptEvent
  changed()
 })
 window.addEventListener('appinstalled',()=>{
  deferredPrompt=null
  changed()
 })
}

export function installKind():InstallKind{
 if(standalone())return'installed'
 if(deferredPrompt)return'native'
 if(ios())return safari()?'ios-safari':'ios-other'
 if(safari()&&/Macintosh/i.test(navigator.userAgent))return'mac-safari'
 return'manual'
}

export function onInstallChange(update:()=>void){
 window.addEventListener(changeEvent,update)
 return()=>window.removeEventListener(changeEvent,update)
}

export async function promptInstall(){
 const prompt=deferredPrompt
 if(!prompt)return null
 await prompt.prompt()
 const choice=await prompt.userChoice
 deferredPrompt=null
 changed()
 return choice.outcome
}
