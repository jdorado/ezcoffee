import type {BrewProfile,TrackedField} from '../api'
import {allFields,fieldLabels,presets} from '../profileSettings'
import Icon from './ui/Icon'

const presetLabels={lelit_mara_x:'Lelit Mara X',generic_espresso:'Generic espresso',standard_pour_over:'Standard pour-over',custom:'Custom setup'} as const

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
  {onLogout&&<section className="profile-section profile-account"><div><span className="profile-step">03</span><h2>Account</h2><p>End this signed-in session on this device.</p></div><div className="account-actions"><button type="button" className="profile-sign-out" onClick={onLogout}><Icon name="logout"/>Sign out</button></div></section>}
 </main>
}
