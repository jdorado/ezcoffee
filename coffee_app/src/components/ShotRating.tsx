import type {Shot} from '../api'
import type {InlineShotEdit} from '../shotEditing'
import Icon from './ui/Icon'

type Props={shot:Shot;edit:InlineShotEdit|null;onEdit:(edit:InlineShotEdit|null)=>void;onSave:(edit:InlineShotEdit)=>void;onReload:()=>void;saving:boolean;error:string}

export default function ShotRating({shot,edit,onEdit,onSave,onReload,saving,error}:Props){
 const active=edit?.shot.id===shot.id&&edit?.field==='rating'
 if(!active||!edit)return <button type="button" className="shot-feedback shot-rating rating-edit-button" disabled={!!edit||saving} aria-label={shot.rating==null?'Rate this shot':`Edit rating: ${shot.rating} out of 5`} title="Edit rating" onClick={()=>onEdit({shot,field:'rating',value:String(shot.rating??'')})}><b aria-hidden="true">{shot.rating==null?'☆':'★'}</b> {shot.rating==null?'Rate':`${shot.rating}/5`}<Icon name="edit"/></button>
 return <div className="inline-rating-editor" role="group" aria-label="Shot rating" onKeyDown={event=>{if(event.key==='Escape'){event.preventDefault();event.stopPropagation();if(!saving)onEdit(null)}}}>
  <div className="inline-rating-options">{[1,2,3,4,5].map(value=><button type="button" key={value} autoFocus={value===(shot.rating||1)} disabled={saving} aria-label={`${value} out of 5`} aria-pressed={Number(edit.value)===value} title={['Poor','Fair','Nice','Lovely','Excellent'][value-1]} onClick={()=>onSave({...edit,value:String(value)})}><span aria-hidden="true">{value<=Number(edit.value)?'★':'☆'}</span></button>)}<button type="button" className="inline-rating-clear" disabled={saving} onClick={()=>onSave({...edit,value:''})}>Clear</button><button type="button" disabled={saving} aria-label="Cancel rating edit" onClick={()=>onEdit(null)}><Icon name="close"/></button></div>
  {saving&&<span role="status">Saving…</span>}
  {error&&<div className="inline-metric-error" role="alert">{error}<button type="button" disabled={saving} onClick={onReload}>Reload values</button></div>}
 </div>
}
