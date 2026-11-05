'use strict';
let latest=null,selected=null,metric='internal_temp_c',events=null,history=[],historyInFlight=false,historyQueued=false;
let previousStatus={},lastSeq=null,displayMode='LIVE';
const el=id=>document.getElementById(id);
const escapeHtml=str=>String(str).replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const label=name=>name.replaceAll('_',' ');
const units={internal_temp_c:'Internal temperature (°C)',vibration_rms_mms:'Vibration (mm/s)',power_kw:'Power draw (kW)'};
const names={bearing_wear:'Bearing wear',overheating:'Thermal overload',power_surge:'Power surge',normal:'Normal operation'};
function showError(message){el('error').textContent=message;el('error').hidden=false;}
function clearError(){el('error').hidden=true;}
async function request(path,init){const response=await fetch(path,init);if(!response.ok){let detail='Server error '+response.status;try{const obj=await response.json();detail=typeof obj.detail==='string'?obj.detail:detail;}catch{}throw Error(detail);}return response.json();}
function log(message){const node=document.createElement('div');node.textContent=`${new Date().toLocaleTimeString()}  ·  ${message}`;el('eventLog').prepend(node);while(el('eventLog').children.length>8)el('eventLog').lastChild.remove();}
function setConnection(ok){el('socketStatus').textContent=ok?'Live stream connected':'Stream disconnected · retrying';el('modePill').classList.toggle('offline',!ok);el('modePill').innerHTML=ok?'<span class="dot"></span> LIVE SYNTHETIC':'● RECONNECTING';}
function setOverview(data){latest=data;clearError();const states=data.assets;el('assetCount').textContent=states.length;el('avgHealth').textContent=data.average_health+'%';el('attentionCount').textContent=data.counts.WARNING+data.counts.CRITICAL;el('ticks').textContent=data.sequence.toLocaleString();el('speedNote').textContent=`At simulation speed ${data.speed}×`;
 el('simState').textContent=data.running?'● RUNNING':'Ⅱ PAUSED';el('simState').classList.toggle('paused',!data.running);el('pause').textContent=data.running?'Ⅱ Pause stream':'▶ Resume stream';el('simSpeed').value=data.speed;
 el('lastUpdate').textContent=`Updated ${new Date(data.updated_at).toLocaleTimeString()}`;
 if(!selected||!states.some(s=>s.asset_id===selected)){selected=states[0].asset_id;}
 for(const state of states){if(previousStatus[state.asset_id]&&previousStatus[state.asset_id]!==state.status)log(`${label(state.asset_id)} changed from ${previousStatus[state.asset_id]} to ${state.status}`);previousStatus[state.asset_id]=state.status;}
 if(lastSeq!==null&&data.sequence<lastSeq){previousStatus={};history=[];log('Simulation restarted');}lastSeq=data.sequence;
 drawAssets(states);drawAdvisor(states.find(s=>s.asset_id===selected));if(data.running)queueHistory();
 el('liveClock').textContent=new Date().toLocaleTimeString();
}
function iconFor(t){return t==='HVAC'?'❄':t==='Pump'?'◉':'↟';}
function drawAssets(states){el('assetGrid').innerHTML=states.map(s=>`<button class="asset-card ${s.asset_id===selected?'selected':''}" type="button" data-asset="${escapeHtml(s.asset_id)}" aria-label="Inspect ${escapeHtml(s.asset_id)}"><div class="asset-top"><span class="asset-icon">${iconFor(s.asset_type)}</span><span class="status ${s.status}">${s.status}</span></div><h4>${escapeHtml(label(s.asset_id))}</h4><div class="asset-kind">${escapeHtml(s.asset_type)} · ${escapeHtml(s.scenario==='normal'?'Nominal':names[s.scenario]||s.scenario)}</div><div class="bar"><div class="${s.status}" style="width:${Math.max(0,Math.min(100,s.health_score))}%"></div></div><div class="asset-footer"><span>Current health</span><b>${s.health_score}%</b></div></button>`).join('');
 el('assetGrid').querySelectorAll('button[data-asset]').forEach(b=>b.addEventListener('click',()=>{selected=b.dataset.asset;drawAssets(latest.assets);drawAdvisor(latest.assets.find(s=>s.asset_id===selected));queueHistory();}));
}
function drawAdvisor(s){if(!s)return;el('advisorName').textContent=label(s.asset_id);el('advisorHealth').textContent=s.health_score+'%';el('advisorHealth').style.color=s.status==='CRITICAL'?'#ff889b':s.status==='WARNING'?'#ffc477':'#65e5bf';el('advisorRisk').textContent=(100*s.failure_probability).toFixed(1)+'%';el('advisorRul').textContent=s.estimated_rul_hours.toFixed(1)+' h';el('advisorScenario').textContent=names[s.scenario]||s.scenario;el('advisorAction').textContent=s.action;el('chartSubtitle').textContent=`${label(s.asset_id)} · ${units[metric]}`;}
async function queueHistory(){if(historyInFlight){historyQueued=true;return;}historyInFlight=true;const current=selected;try{const data=await request('/api/live/assets/'+encodeURIComponent(current)+'/history?limit=100');if(current===selected){history=data.readings;drawChart();}}catch(e){showError('History retrieval failed: '+e.message);}finally{historyInFlight=false;if(historyQueued){historyQueued=false;queueHistory();}}}
function drawChart(){const canvas=el('sensorChart'),rect=canvas.getBoundingClientRect();if(rect.width<50)return;const ratio=window.devicePixelRatio||1;const w=rect.width,h=rect.height;canvas.width=Math.round(w*ratio);canvas.height=Math.round(h*ratio);const ctx=canvas.getContext('2d');ctx.scale(ratio,ratio);ctx.clearRect(0,0,w,h);
 const pad={left:46,right:18,top:15,bottom:30};const dw=w-pad.left-pad.right,dh=h-pad.top-pad.bottom;const values=history.map(r=>Number(r[metric])).filter(Number.isFinite);el('chartEmpty').hidden=values.length>0;if(!values.length)return;
 let min=Math.min(...values),max=Math.max(...values);const spread=max-min||Math.max(1,Math.abs(max)*.08);min-=spread*.2;max+=spread*.2;const y=v=>pad.top+(max-v)/(max-min)*dh;const x=i=>pad.left+(values.length===1?.5:i/(values.length-1))*dw;
 ctx.font='11px Arial';ctx.textBaseline='middle';ctx.strokeStyle='#293c53';ctx.lineWidth=1;ctx.fillStyle='#8298b1';ctx.textAlign='right';for(let i=0;i<=4;i++){let v=min+(max-min)*(4-i)/4,yy=y(v);ctx.beginPath();ctx.moveTo(pad.left,yy);ctx.lineTo(w-pad.right,yy);ctx.stroke();ctx.fillText(v.toFixed(v>=10?1:2),pad.left-8,yy);}
 const labels=[0,Math.floor((values.length-1)/2),values.length-1];ctx.textBaseline='top';ctx.textAlign='center';for(const idx of labels){const s=history[idx]?.timestamp||'';let txt=s?new Date(s).toLocaleTimeString():'';ctx.fillText(txt,x(idx),h-22);}
 const gradient=ctx.createLinearGradient(0,pad.top,0,h-pad.bottom);gradient.addColorStop(0,'rgba(77,220,196,.25)');gradient.addColorStop(1,'rgba(77,220,196,.006)');ctx.beginPath();values.forEach((v,i)=>i?ctx.lineTo(x(i),y(v)):ctx.moveTo(x(i),y(v)));ctx.lineTo(x(values.length-1),h-pad.bottom);ctx.lineTo(x(0),h-pad.bottom);ctx.closePath();ctx.fillStyle=gradient;ctx.fill();
 ctx.beginPath();values.forEach((v,i)=>i?ctx.lineTo(x(i),y(v)):ctx.moveTo(x(i),y(v)));ctx.strokeStyle='#58e1ca';ctx.lineWidth=2.5;ctx.lineJoin='round';ctx.stroke();ctx.beginPath();ctx.arc(x(values.length-1),y(values.at(-1)),4,0,Math.PI*2);ctx.fillStyle='#b4ffee';ctx.fill();
 el('chartLegend').textContent=units[metric];
}
async function send(action,extra={}){try{clearError();const data=await request('/api/live/control',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action,...extra})});setOverview(data);return true;}catch(e){showError(e.message);return false;}}
function connect(){if(events)events.close();events=new EventSource('/api/live/events');events.addEventListener('overview',event=>{setConnection(true);try{setOverview(JSON.parse(event.data));}catch(e){showError('Invalid stream data: '+e.message);}});events.onerror=()=>setConnection(false);}
async function init(){try{let first=await request('/api/live/overview');setOverview(first);el('faultAsset').innerHTML=first.assets.map(s=>`<option value="${escapeHtml(s.asset_id)}">${escapeHtml(label(s.asset_id))}</option>`).join('');el('faultAsset').value=selected;connect();log('Live simulator initialized · four synthetic assets online');}catch(e){showError('Could not initialize simulator: '+e.message);setConnection(false);}}
el('inject').onclick=async()=>{let asset_id=el('faultAsset').value,scenario=el('faultType').value;if(await send('inject',{asset_id,scenario})){selected=asset_id;log(`Injected ${names[scenario]} scenario into ${label(asset_id)}`);}};
el('clear').onclick=async()=>{let asset_id=el('faultAsset').value;if(await send('clear',{asset_id})){log(`Cleared injected fault for ${label(asset_id)}`);}};
el('pause').onclick=async()=>{let action=latest?.running?'pause':'resume';if(await send(action))log(action==='pause'?'Simulation paused':'Simulation resumed');};
el('reset').onclick=async()=>{if(await send('reset')){history=[];log('All synthetic scenarios and readings reset');}};
el('simSpeed').onchange=async()=>{let speed=Number(el('simSpeed').value);if(await send('speed',{speed}))log('Simulation speed set to '+speed+'×');};
for(const tab of document.querySelectorAll('.tab'))tab.addEventListener('click',()=>{metric=tab.dataset.metric;document.querySelectorAll('.tab').forEach(node=>node.classList.toggle('selected',node===tab));drawChart();const state=latest?.assets.find(s=>s.asset_id===selected);if(state)drawAdvisor(state);});
window.addEventListener('resize',drawChart);window.addEventListener('beforeunload',()=>{if(events)events.close();});setInterval(()=>el('liveClock').textContent=new Date().toLocaleTimeString(),1000);init();
