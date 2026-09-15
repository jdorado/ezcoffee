import {useEffect,useState} from 'react'
import type {BrewProfile,TrackedField} from '../api'
import {installKind,onInstallChange,promptInstall} from '../installApp'
import {allFields,fieldLabels,presets} from '../profileSettings'
import Icon from './ui/Icon'

const presetLabels={lelit_mara_x:'Lelit Mara X',generic_espresso:'Generic espresso',standard_pour_over:'Standard pour-over',custom:'Custom setup'} as const

function InstallApp(){
 const [kind,setKind]=useState(installKind)
 const [showHelp,setShowHelp]=useState(false)
 useEffect(()=>onInstallChange(()=>setKind(installKind())),[])
 if(kind==='installed')return null
 async function install(){
  if(kind==='native'){
   await promptInstall()
   setKind(installKind())
  }else setShowHelp(current=>!current)
 }
 const help=kind==='ios-safari'
  ?<ol><li>Tap Safari's <strong>Share</strong> button.</li><li>Choose <strong>Add to Home Screen</strong>.</li><li>Turn on <strong>Open as Web App</strong>, then tap <strong>Add</strong>.</li></ol>
  :kind==='ios-other'
   ?<p>Open ezcoffee in Safari, then use <strong>Share → Add to Home Screen</strong>.</p>
   :kind==='mac-safari'
    ?<p>In Safari, choose <strong>File → Add to Dock</strong>, then click <strong>Add</strong>.</p>
    :<p>Open your browser menu and choose <strong>Install app</strong> or <strong>Add to Home Screen</strong>.</p>
 return <section className="profile-section profile-install"><div><span className="profile-step">03</span><h2>Install ezcoffee</h2><p>Keep your coffee journal on your home screen and open it like an app.</p></div><div className="install-actions"><button type="button" className="profile-install-button" onClick={install}><Icon name="install"/>{kind==='native'?'Install ezcoffee':showHelp?'Hide install steps':'Show install steps'}</button>{showHelp&&<div className="install-help" aria-live="polite">{help}</div>}</div></section>
}

export default function ProfileView({value,onChange,onSave,onLogout,saving}:{value:BrewProfile;onChange:(next:BrewProfile)=>void;onSave:()=>void;onLogout?:()=>void;saving:boolean}){
 const rows=[...value.tracked_fields,...allFields.filter(field=>!value.tracked_fields.includes(field))]
 function choose(preset:BrewProfile['equipment_preset']){onChange({...value,equipment_preset:preset,...presets[preset]})}
 function toggle(field:TrackedField){const enabled=value.tracked_fields.includes(field);const tracked_fields=enabled?value.tracked_fields.filter(item=>item!==field):[...value.tracked_fields,field];if(tracked_fields.length)onChange({...value,equipment_preset:'custom',tracked_fields})}
 function move(field:TrackedField,direction:-1|1){const index=value.tracked_fields.indexOf(field),next=[...value.tracked_fields],target=index+direction;if(index<0||target<0||target>=next.length)return;[next[index],next[target]]=[next[target],next[index]];onChange({...value,equipment_preset:'custom',tracked_fields:next})}
 return <main className="profile-view">
  <div className="heading"><div><div className="eyebrow">YOUR BREWING SETUP</div><h1>Profile</h1></div><button className="primary" disabled={saving} onClick={onSave}><Icon name="check"/>{saving?'Saving…':'Save profile'}</button></div>
  <p className="profile-intro">Choose a starting setup, then decide which details appear when you log a brew. Enabled fields appear in this order.</p>
  <section className="profile-section"><div><span className="profile-step">01</span><h2>What do you brew?</h2><p>This changes the language and sensible defaults; it never removes existing records.</p></div><div className="preset-grid">{(Object.keys(presetLabels) as BrewProfile['equipment_preset'][]).map(key=><button key={key} type="button" aria-pressed={value.equipment_preset===key} onClick={()=>choose(key)}><strong>{presetLabels[key]}</strong><span>{key==='lelit_mara_x'?'Includes Mara X PID levels':key==='standard_pour_over'?'Water, ice, bloom and ratio':'Start with common fields'}</span></button>)}</div>
   <label>Setup name<input value={value.equipment_name} placeholder="My coffee setup" onChange={event=>onChange({...value,equipment_name:event.target.value})}/></label>
  </section>
  <section className="profile-section"><div><span className="profile-step">02</span><h2>What do you track?</h2><p>Turn fields on or off. Use the arrows to set the order used in the brew form and cards.</p></div><div className="tracking-list">{rows.map(field=>{const enabled=value.tracked_fields.includes(field),index=value.tracked_fields.indexOf(field);return <div key={field} className={enabled?'enabled':''}><label><input type="checkbox" checked={enabled} onChange={()=>toggle(field)}/><span>{fieldLabels[field]}</span></label><div><button type="button" aria-label={`Move ${fieldLabels[field]} up`} disabled={!enabled||index===0} onClick={()=>move(field,-1)}>↑</button><button type="button" aria-label={`Move ${fieldLabels[field]} down`} disabled={!enabled||index===value.tracked_fields.length-1} onClick={()=>move(field,1)}>↓</button></div></div>})}</div></section>
  <InstallApp/>
  {onLogout&&<section className="profile-section profile-account"><div><span className="profile-step">04</span><h2>Account</h2><p>End this signed-in session on this device.</p></div><div className="account-actions"><button type="button" className="profile-sign-out" onClick={onLogout}><Icon name="logout"/>Sign out</button></div></section>}
 </main>
}
