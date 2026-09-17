const form=document.getElementById("monitor-form");
const startButton=document.getElementById("start-button");
const result=document.getElementById("result");
const monitorStatus=document.getElementById("monitor-status");
const statusText=document.getElementById("status-text");
const stopButton=document.getElementById("stop-button");
let currentJobId=null,statusTimer=null;

function showResult(message,type="success"){
  result.className=`result ${type}`;
  result.innerHTML=message;
  result.classList.remove("hidden");
}
function escapeHtml(v){
  return String(v).replaceAll("&","&amp;").replaceAll("<","&lt;")
    .replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;");
}

form.addEventListener("submit",async e=>{
  e.preventDefault();
  startButton.disabled=true;
  startButton.textContent="Monitor wird gestartet...";
  try{
    const r=await fetch("/api/monitor/start",{method:"POST",body:new FormData(form)});
    const d=await r.json();
    if(!r.ok) throw new Error(d.error||"Start fehlgeschlagen.");
    currentJobId=d.job.job_id;
    form.classList.add("hidden");
    monitorStatus.classList.remove("hidden");
    const found=d.test_appointments||[];
    if(found.length){
      let html="<h2>🎉 Test-Termine gefunden</h2><p>Aktuell ist dies noch der Testmodus.</p><ul>";
      for(const a of found){
        html+=`<li>${escapeHtml(a.date)} – ${escapeHtml(a.time)} – ${escapeHtml(a.location)}</li>`;
      }
      html+="</ul>";
      showResult(html);
    }
    updateStatus();
    statusTimer=setInterval(updateStatus,5000);
  }catch(err){
    showResult(escapeHtml(err.message),"error");
    startButton.disabled=false;
    startButton.textContent="Monitor starten";
  }
});

async function updateStatus(){
  if(!currentJobId)return;
  try{
    const r=await fetch(`/api/monitor/${currentJobId}`);
    if(!r.ok) throw new Error("Monitor nicht mehr verfügbar.");
    const d=await r.json();
    let t=`Prüfungen: ${d.checks}<br>Gefundene Termine: ${d.appointments_found}<br>`;
    if(d.last_check)t+=`Letzte Prüfung: ${new Date(d.last_check).toLocaleTimeString("de-CH")}`;
    statusText.innerHTML=t;
  }catch(e){statusText.textContent=e.message;}
}

stopButton.addEventListener("click",async()=>{
  if(!currentJobId)return;
  stopButton.disabled=true;
  try{
    await fetch(`/api/monitor/${currentJobId}/stop`,{method:"POST"});
  }finally{
    clearInterval(statusTimer);
    currentJobId=null;
    monitorStatus.classList.add("hidden");
    form.classList.remove("hidden");
    form.reset();
    startButton.disabled=false;
    startButton.textContent="Monitor starten";
  }
});
