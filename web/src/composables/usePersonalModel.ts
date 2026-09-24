import { onUnmounted, ref } from 'vue'
import type { RealtimeChannel } from '@supabase/supabase-js'
import { supabase } from '../lib/supabase'
import { portal } from '../lib/observerPortal'
/** No localStorage, cookies, database writes or project-file credentials. */
export function usePersonalModel(){
  const endpoint=ref(''),model=ref(''),key=ref(''),connected=ref(false),status=ref<'idle'|'connected'|'working'|'failed'>('idle')
  const channels=new Map<string,RealtimeChannel>(),seen=new Set<string>()
  let fetching=false,disposed=false
  async function refresh(){
    if(!connected.value||fetching||disposed)return
    fetching=true
    try{
      const routes=await portal<{run_id:string;topic:string}[]>('model_routes')
      for(const [topic,channel] of channels)if(!routes.some(r=>r.topic===topic)){void supabase.removeChannel(channel);channels.delete(topic)}
      for(const route of routes){
        if(channels.has(route.topic))continue
        const channel=supabase.channel(route.topic)
        channels.set(route.topic,channel)
        channel.on('broadcast',{event:'request'},async message=>{
          const request=message.payload
          if(!connected.value||!key.value||request?.run_id!==route.run_id||typeof request.call_id!=='string'||seen.has(request.call_id))return
          seen.add(request.call_id);status.value='working'
          try{
            const response=await portal<{completed:boolean}>('personal_model',{
              run_id:route.run_id,call_id:request.call_id,body:request.body,
              base_url:endpoint.value,model:model.value,api_key:key.value,
            })
            if(!disposed)status.value=response.completed?'connected':'failed'
          }catch{if(!disposed)status.value='failed'}
        }).subscribe()
      }
    }finally{fetching=false}
  }
  async function connect(){connected.value=true;status.value='connected';await refresh()}
  function clear(){
    connected.value=false;key.value='';status.value='idle'
    for(const channel of channels.values())void supabase.removeChannel(channel)
    channels.clear();seen.clear()
  }
  onUnmounted(()=>{disposed=true;clear()})
  return {endpoint,model,key,connected,status,refresh,connect,clear}
}
