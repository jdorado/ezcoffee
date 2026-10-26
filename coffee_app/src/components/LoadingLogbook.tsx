import startup from './startup.html'

// The same static, account-free markup is in the initial HTML, before JavaScript or auth can delay it.
export default function LoadingLogbook(){return <div dangerouslySetInnerHTML={{__html:startup}}/>}
