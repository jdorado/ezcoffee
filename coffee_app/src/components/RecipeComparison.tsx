import type {RecipeOption,RecipeOptions,RecipeVariant} from '../api'

export const paperVariants={
  with_paper:'With paper filter',
  without_paper:'Without paper filter',
} satisfies Record<RecipeVariant,string>
const variants=Object.keys(paperVariants) as RecipeVariant[]

const settings: {label:string;read:(option:RecipeOption)=>string|number|null}[]=[
  {label:'Coffee · g',read:option=>option.dose},
  {label:'Grind',read:option=>option.grind},
  {label:'Target · g',read:option=>option.target_yield_g!=null&&option.target_yield_max_g!=null
    ? `${option.target_yield_g}–${option.target_yield_max_g}` : option.target_yield_g},
  {label:'Water · °C',read:option=>option.water_temp_c},
  {label:'Water · g',read:option=>option.water_g},
  {label:'Ice · g',read:option=>option.ice_g},
  {label:'Bloom · s',read:option=>option.bloom_seconds},
  {label:'PID',read:option=>option.temp},
  {label:'Pressure',read:option=>option.pressure},
  {label:'Basket',read:option=>option.basket},
  {label:'Puck screen',read:option=>option.puck_screen==='yes'?'Yes':option.puck_screen==='no'?'No':null},
]

export default function RecipeComparison({options,disabled,onChoose}:{
  options:RecipeOptions;disabled:boolean;onChoose:(variant:RecipeVariant)=>void
}){
  return <table className="recipe-comparison" aria-label="Compare next recipes">
    <thead><tr><td/>{variants.map(variant=><th key={variant} scope="col">{paperVariants[variant]}</th>)}</tr></thead>
    <tbody>
      {settings.map(({label,read})=>{
        const values=variants.map(variant=>read(options[variant]))
        if(values.every(value=>value===null||value===''))return null
        return <tr key={label}><th scope="row">{label}</th>{values.map((value,index)=>
          <td key={variants[index]}>{value===null||value===''?'—':value}</td>)}</tr>
      })}
      <tr className="recipe-reasons"><th scope="row">Why</th>{variants.map(variant=>
        <td key={variant}>{options[variant].reason}</td>)}</tr>
    </tbody>
    <tfoot><tr><td/>{variants.map(variant=><td key={variant}>
      <button type="button" className="next-plan-generate" disabled={disabled}
        aria-label={'Use recipe '+paperVariants[variant].toLowerCase()} onClick={()=>onChoose(variant)}>Use recipe</button>
    </td>)}</tr></tfoot>
  </table>
}
