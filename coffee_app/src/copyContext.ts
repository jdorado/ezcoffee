import {api} from './api'

export async function copyCoffeeContext(coffeeId:string){
 if(!navigator.clipboard)throw new Error('Clipboard is unavailable. Open the app over HTTPS to copy context.')
 const loadText=async()=>{const result=await api('/coffees/'+encodeURIComponent(coffeeId)+'/context');return result.text as string}
 // Start the clipboard write in the click gesture. Safari requires this even
 // though the fresh context arrives asynchronously from the API.
 if(typeof ClipboardItem!=='undefined'&&navigator.clipboard.write){
  await navigator.clipboard.write([new ClipboardItem({'text/plain':loadText().then(text=>new Blob([text],{type:'text/plain'}))})])
 }else{
  await navigator.clipboard.writeText(await loadText())
 }
}
