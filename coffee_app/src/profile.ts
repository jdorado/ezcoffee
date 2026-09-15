declare const process:{env:{APP_MODE?:string;CHAT_ENABLED?:string;PRIVY_APP_ID?:string;ESPRESSO_MACHINE_LABEL?:string;GRINDER_LABEL?:string;DEFAULT_DOSE_G?:string;DEFAULT_GRIND?:string;DEFAULT_BASKET?:string;DEFAULT_PAPER?:string;DEFAULT_TEMP?:string;DEFAULT_PUCK_SCREEN?:string}}

const enabled=(value:string|undefined)=>value?.toLowerCase()==='true'
const numberOrNull=(value:string|undefined)=>{
 const parsed=value?.trim()===''?NaN:Number(value)
 return Number.isFinite(parsed)?parsed:null
}

const mode=process.env.APP_MODE||(process.env.PRIVY_APP_ID?'personal':'selfhost')
export const profile={
 mode,
 chatEnabled:process.env.CHAT_ENABLED?enabled(process.env.CHAT_ENABLED):mode==='hosted'||mode==='personal',
 setupLabel:[process.env.ESPRESSO_MACHINE_LABEL,process.env.GRINDER_LABEL].filter(Boolean).join(' / '),
 defaults:{
  dose:numberOrNull(process.env.DEFAULT_DOSE_G),
  grind:process.env.DEFAULT_GRIND||'',
  basket:process.env.DEFAULT_BASKET||'',
  paper:['yes','no'].includes(process.env.DEFAULT_PAPER||'')?process.env.DEFAULT_PAPER!:'unknown',
  temp:['0','I','II'].includes(process.env.DEFAULT_TEMP||'')?process.env.DEFAULT_TEMP!:'',
  puckScreen:['yes','no'].includes(process.env.DEFAULT_PUCK_SCREEN||'')?process.env.DEFAULT_PUCK_SCREEN!:'unknown',
 }
}
