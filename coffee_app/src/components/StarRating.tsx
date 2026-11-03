import {useId,useState} from 'react'
import {shotRatingValues} from '../shotEditing'
import Icon from './ui/Icon'

type Props={value:number|null;onChange:(value:number|null)=>void;disabled?:boolean;autoFocus?:boolean;clearable?:boolean}

export default function StarRating({value,onChange,disabled=false,autoFocus=false,clearable=false}:Props){
 const name=useId()
 const [preview,setPreview]=useState<number|null>(null)
 const shown=preview??value??0
 return <div className="star-rating" data-disabled={disabled||undefined}>
  <div className="star-rating-stars" role="radiogroup" aria-label="Enjoyment rating" onPointerLeave={()=>setPreview(null)}>
   {[1,2,3,4,5].map(star=><span className="star-rating-item" key={star}>
    <span className="star-rating-outline" aria-hidden="true"><Icon name="star"/></span>
    <span className="star-rating-fill" aria-hidden="true" style={{clipPath:`inset(0 ${(1-Math.min(1,Math.max(0,shown-star+1)))*100}% 0 0)`}}><Icon name="star"/></span>
    {shotRatingValues.filter(option=>Math.ceil(option)===star).map(option=><label key={option} className={'star-rating-hit '+(star===1?'first':option===star?'whole':'half')} title={`${option} out of 5`} onPointerEnter={event=>{if(!disabled&&event.pointerType==='mouse')setPreview(option)}}>
     <input type="radio" name={name} value={option} aria-label={`${option} out of 5`} checked={value===option} disabled={disabled} autoFocus={autoFocus&&option===(value??1)} onFocus={()=>setPreview(option)} onBlur={()=>setPreview(null)} onClick={()=>{if(clearable&&value===option)onChange(null)}} onChange={()=>onChange(option)}/>
    </label>)}
   </span>)}
  </div>
  <span className="star-rating-value" aria-hidden="true">{shown||'—'}</span>
 </div>
}
