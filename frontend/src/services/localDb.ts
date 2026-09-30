const DB='sports-rehab-ai'; const STORE='pending';
function openDb(){return new Promise<IDBDatabase>((resolve,reject)=>{const r=indexedDB.open(DB,1);r.onupgradeneeded=()=>r.result.createObjectStore(STORE,{keyPath:'id',autoIncrement:true});r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)})}
export async function queue(item:any){const db=await openDb();return new Promise<void>((res,rej)=>{const tx=db.transaction(STORE,'readwrite');tx.objectStore(STORE).add(item);tx.oncomplete=()=>res();tx.onerror=()=>rej(tx.error)})}
export async function list(){const db=await openDb();return new Promise<any[]>((res,rej)=>{const tx=db.transaction(STORE);const r=tx.objectStore(STORE).getAll();r.onsuccess=()=>res(r.result);r.onerror=()=>rej(r.error)})}
