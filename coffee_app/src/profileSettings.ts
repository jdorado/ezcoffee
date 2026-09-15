import type {BrewProfile,TrackedField} from './api'

export const fieldLabels:Record<TrackedField,string>={
 water_temp_c:'Water temperature',water_g:'Water quantity',ice_g:'Ice quantity',dose:'Coffee dose',ratio:'Coffee-to-water ratio',grind:'Grind size',seconds:'Brew time',bloom_seconds:'Bloom time',brand:'Coffee brand',yield_g:'Espresso output',stop_yield_g:'Stop yield',target_yield_g:'Target output',first_drip:'First drip',paper:'Paper filter',temp:'PID setting',pressure:'Pressure',basket:'Basket',puck_screen:'Puck screen',taste_balance:'Taste balance',rating:'Rating',taste:'Tasting note'
}

export const allFields=Object.keys(fieldLabels) as TrackedField[]
export const presets:Record<BrewProfile['equipment_preset'],Omit<BrewProfile,'revision'|'equipment_preset'>>={
 lelit_mara_x:{brew_method:'espresso',equipment_name:'Lelit Mara X',tracked_fields:['dose','yield_g','seconds','grind','ratio','paper','temp','stop_yield_g','target_yield_g','first_drip','pressure','basket','puck_screen','taste_balance','rating','taste']},
 generic_espresso:{brew_method:'espresso',equipment_name:'Espresso machine',tracked_fields:['dose','yield_g','seconds','grind','ratio','paper','water_temp_c','pressure','taste_balance','rating','taste']},
 standard_pour_over:{brew_method:'filter',equipment_name:'Pour-over',tracked_fields:['water_temp_c','water_g','ice_g','dose','ratio','grind','seconds','bloom_seconds','brand','taste_balance','rating','taste']},
 custom:{brew_method:'espresso',equipment_name:'Custom setup',tracked_fields:['dose','ratio','grind','seconds','taste','rating']}
}

export const fallbackProfile:BrewProfile={equipment_preset:'generic_espresso',revision:0,...presets.generic_espresso}
