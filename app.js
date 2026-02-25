// ===== AI 黄金权重 =====
const GOLDEN_WEIGHTS = { amphi: 765, senate: 581, arc: 418, pan: 204, conq_base: 241, conq_arc: 355, trib: 65, top_cul: 35, top_mil: 23, top_ind: 21 };

// ===== 基础数据 =====
const CARDS = [
  {id:"C01",name:"凯旋雕塑",class:"Building",top:{c:1,m:1,i:1},bottom:{type:"Build_Building",cost:{c:1,m:0,i:2},ref:"B_KaiXuanDiaoSu"}},
  {id:"C02",name:"帝国引水道",class:"Building",top:{c:1,m:1,i:1},bottom:{type:"Build_Building",cost:{c:1,m:0,i:2},ref:"B_DiGuoYinShuiDao"}},
  {id:"C03",name:"军团要塞",class:"Building",top:{c:1,m:2,i:0},bottom:{type:"Build_Building",cost:{c:0,m:1,i:2},ref:"B_JunTuanYaoSai"}},
  {id:"C04",name:"帝国金矿",class:"Building",top:{c:0,m:0,i:3},bottom:{type:"Build_Building",cost:{c:0,m:0,i:3},ref:"B_DiGuoJinKuang"}},
  {id:"C05",name:"圆形竞技场",class:"Building",top:{c:2,m:0,i:1},bottom:{type:"Build_Building",cost:{c:1,m:0,i:2},ref:"B_YuanXingJingJiChang"}},
  {id:"C06",name:"军团征服敕令1",class:"Action",top:{c:0,m:0,i:2},bottom:{type:"Conquest"}},
  {id:"C07",name:"军团征服敕令2",class:"Action",top:{c:1,m:0,i:1},bottom:{type:"Conquest"}},
  {id:"C08",name:"行省贡赋征召令1",class:"Action",top:{c:0,m:0,i:2},bottom:{type:"Tribute",target:"Culture"}},
  {id:"C09",name:"行省贡赋征召令2",class:"Action",top:{c:1,m:0,i:1},bottom:{type:"Tribute",target:"Industry"}},
  {id:"C10",name:"万神庙1",class:"Monument",top:{c:1,m:0,i:1},bottom:{type:"Build_Monument",cost:{c:3,m:0,i:0},ref:"M_WanShenMiao"}},
  {id:"C11",name:"万神庙2",class:"Monument",top:{c:2,m:0,i:0},bottom:{type:"Build_Monument",cost:{c:3,m:0,i:1},ref:"M_WanShenMiao"}},
  {id:"C12",name:"罗马斗兽场1",class:"Monument",top:{c:0,m:1,i:1},bottom:{type:"Build_Monument",cost:{c:3,m:0,i:0},ref:"M_LuoMaDouShouChang"}},
  {id:"C13",name:"罗马斗兽场2",class:"Monument",top:{c:0,m:2,i:0},bottom:{type:"Build_Monument",cost:{c:0,m:1,i:2},ref:"M_LuoMaDouShouChang"}},
  {id:"C14",name:"帝国广场1",class:"Monument",top:{c:1,m:0,i:1},bottom:{type:"Build_Monument",cost:{c:3,m:0,i:0},ref:"M_DiGuoGuangChang"}},
  {id:"C15",name:"帝国广场2",class:"Monument",top:{c:2,m:0,i:0},bottom:{type:"Build_Monument",cost:{c:0,m:0,i:3},ref:"M_DiGuoGuangChang"}},
  {id:"C16",name:"哈德良陵寝1",class:"Monument",top:{c:0,m:0,i:2},bottom:{type:"Build_Monument",cost:{c:0,m:1,i:2},ref:"M_HaDeLiangLingQin"}},
  {id:"C17",name:"哈德良陵寝2",class:"Monument",top:{c:0,m:1,i:1},bottom:{type:"Build_Monument",cost:{c:3,m:0,i:0},ref:"M_HaDeLiangLingQin"}},
  {id:"C18",name:"凯旋门1",class:"Monument",top:{c:1,m:1,i:0},bottom:{type:"Build_Monument",cost:{c:3,m:0,i:0},ref:"M_KaiXuanMen"}},
  {id:"C19",name:"凯旋门2",class:"Monument",top:{c:0,m:2,i:0},bottom:{type:"Build_Monument",cost:{c:0,m:1,i:2},ref:"M_KaiXuanMen"}},
  {id:"C20",name:"图拉真市场1",class:"Monument",top:{c:0,m:0,i:2},bottom:{type:"Build_Monument",cost:{c:1,m:0,i:2},ref:"M_TuLaZhenShiChang"}},
  {id:"C21",name:"图拉真市场2",class:"Monument",top:{c:0,m:1,i:1},bottom:{type:"Build_Monument",cost:{c:3,m:0,i:0},ref:"M_TuLaZhenShiChang"}},
];

const MONUMENTS = {
  M_WanShenMiao:{name:"万神庙",type:"FlatGP",v:4,desc:"完成后+4分"},
  M_LuoMaDouShouChang:{name:"罗马斗兽场",type:"FlatGP",v:2,special:"IgnoreInvasions",desc:"+2分，忽略入侵"},
  M_DiGuoGuangChang:{name:"帝国广场",type:"FlatGP",v:2,special:"SenateSwap",desc:"+2分，文/军互换"},
  M_HaDeLiangLingQin:{name:"哈德良陵寝",type:"PerBuilding",v:1,desc:"每建筑+1分"},
  M_KaiXuanMen:{name:"凯旋门",type:"PerRegion",v:1,desc:"每地区+1分"},
  M_TuLaZhenShiChang:{name:"图拉真市场",type:"MinResource",v:1,desc:"按最小资源计分"},
};

const BUILDINGS = {
  B_KaiXuanDiaoSu:{gp:2}, B_DiGuoYinShuiDao:{gp:2},
  B_JunTuanYaoSai:{on:"military",bonus:2}, B_DiGuoJinKuang:{on:"industry",bonus:2}, B_YuanXingJingJiChang:{on:"culture",bonus:2}
};

const CITY_IDS = ["C1","C2","C3","I1","I2","I3"];
const INVASIONS = [{pay:2,lose:1},{pay:3,lose:1},{pay:5,lose:2}];

// ===== 状态 =====
let state, hand, legal, pending, trace, undoStack, sessionId;
let uiMode = "normal"; 
let pendingConquestAction = null;
let pendingInvasion = null;

function cardById(id){ return CARDS.find(c=>c.id===id); }
function clone(x){ return JSON.parse(JSON.stringify(x)); }
function shuffle(a){ for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];} return a; }

// ===== 核心引擎 =====
function initGame(){
  sessionId = "sess_" + Date.now();
  state = {
    culture:1, military:1, industry:1, max:9, rome:true,
    cities:{C1:false,C2:false,C3:false,I1:false,I2:false,I3:false},
    built:[], mono:Object.fromEntries(Object.keys(MONUMENTS).map(k=>[k,0])),
    deck:shuffle(CARDS.map(c=>c.id)), discard:[], inv:0, lost:false, turn:0
  };
  hand=[]; legal=[]; pending=null; trace=[]; undoStack=[];
  nextTurn();
}

function nextTurn(){
  if(state.lost || state.inv>=3){ render(); return; }
  state.turn++;
  const n=Math.min(3, state.deck.length);
  hand=[]; for(let i=0;i<n;i++) hand.push(state.deck.pop());
  computeLegal();
  pending=null; uiMode="normal"; render();
}

function computeLegal(){
  legal = [];
  hand.forEach(cid => {
    const c = cardById(cid);
    legal.push({card_id:cid, mode:"top", kind:"TopResource", meta:{}});
    const b = c.bottom;
    const curRegs = occupiedRegions();
    if(b.type==="Conquest" && canPay(0,curRegs,0) && CITY_IDS.some(id=>!state.cities[id]))
      legal.push({card_id:cid, mode:"bottom", kind:"Conquest", meta:{}});
    else if(b.type==="Tribute") legal.push({card_id:cid, mode:"bottom", kind:"Tribute", meta:{target:b.target}});
    else if(b.type==="Build_Building" && !state.built.includes(b.ref) && canPay(b.cost.c, b.cost.m, b.cost.i))
      legal.push({card_id:cid, mode:"bottom", kind:"Build_Building", meta:{building_id:b.ref}});
    else if(b.type==="Build_Monument" && state.mono[b.ref]<2 && canPay(b.cost.c, b.cost.m, b.cost.i))
      legal.push({card_id:cid, mode:"bottom", kind:"Build_Monument", meta:{monument_id:b.ref}});
  });
}

function occupiedRegions(){ return (state.rome?1:0) + CITY_IDS.filter(id=>state.cities[id]).length; }
function senateActive(){ return state.mono["M_DiGuoGuangChang"]>=2; }
function colosseumActive(){ return state.mono["M_LuoMaDouShouChang"]>=2; }

function canPay(c,m,i){
  if(state.industry<i) return false;
  return senateActive() ? (state.culture+state.military >= c+m) : (state.culture>=c && state.military>=m);
}
function pay(c,m,i){
  state.industry -= i;
  if(!senateActive()){ state.culture-=c; state.military-=m; return; }
  let need=c+m;
  while(need>0){ if(state.culture>=state.military && state.culture>0) state.culture--; else if(state.military>0) state.military--; else state.culture--; need--; }
}
function addRes(type,amt){
  const k = type==="Culture"?"culture":type==="Military"?"military":"industry";
  const b = state[k]; state[k]=Math.min(9, state[k]+amt); return state[k]-b;
}
function gainWithTriggers(g){
  let c=g.Culture||0, m=g.Military||0, i=g.Industry||0;
  if(senateActive()){ let t=c+m; c=0; m=0; while(t>0){ if(state.culture<=state.military)c++; else m++; t--; } }
  if(addRes("Culture",c)>0 && state.built.includes("B_YuanXingJingJiChang")) addRes("Culture",2);
  if(addRes("Military",m)>0 && state.built.includes("B_JunTuanYaoSai")) addRes("Military",2);
  if(addRes("Industry",i)>0 && state.built.includes("B_DiGuoJinKuang")) addRes("Industry",2);
}

// ===== AI 计算 (修复版) =====
function getAIChoice() {
  if (!legal || legal.length === 0) return null;
  const idx = Math.min(state.inv + 1, 3);
  const invCost = INVASIONS[idx-1].pay;
  const regs = occupiedRegions();
  const sa = senateActive();
  const aa = state.mono["M_KaiXuanMen"] >= 2;

  let redLine = 0;
  if (state.turn < 19) {
    if (state.deck.length >= 6) redLine = 1;
    else if (state.deck.length >= 3) redLine = Math.max(1, invCost - 2);
    else redLine = invCost;
  }

  const scores = legal.map(a => {
    const card = cardById(a.card_id);
    let estMil = state.military;
    let estCul = state.culture;
    if (a.kind === "Conquest") estMil -= regs;
    else if (a.mode === "bottom" && (a.kind.startsWith("Build"))) {
      estMil -= card.bottom.cost.m; estCul -= card.bottom.cost.c;
    }
    const effMil = sa ? (estMil + estCul) : estMil;
    if (state.turn < 19 && effMil < redLine && a.mode !== "top") return -10000;

    let sc = 0;
    if (a.mode === "top") {
      if (state.military < redLine) sc += card.top.m * 400 + card.top.c * 20;
      else sc += card.top.c * (sa ? GOLDEN_WEIGHTS.top_cul : GOLDEN_WEIGHTS.top_cul - 10) + card.top.m * GOLDEN_WEIGHTS.top_mil + card.top.i * GOLDEN_WEIGHTS.top_ind;
      if (state.culture + card.top.c > 9) sc -= 40;
      if (state.military + card.top.m > 9) sc -= 40;
      sc += 20;
    } else {
      if (a.kind === "Build_Building") {
        if (a.meta.building_id === "B_YuanXingJingJiChang") sc += GOLDEN_WEIGHTS.amphi;
        else if (["B_KaiXuanDiaoSu","B_DiGuoYinShuiDao"].includes(a.meta.building_id)) sc += 160;
      }
      if (a.kind === "Build_Monument") {
        if (a.meta.monument_id === "M_DiGuoGuangChang") sc += GOLDEN_WEIGHTS.senate;
        else if (a.meta.monument_id === "M_KaiXuanMen") sc += GOLDEN_WEIGHTS.arc;
        else if (a.meta.monument_id === "M_WanShenMiao") sc += GOLDEN_WEIGHTS.pan;
      }
      if (a.kind === "Conquest") sc += aa ? GOLDEN_WEIGHTS.conq_arc : GOLDEN_WEIGHTS.conq_base;
      if (a.kind === "Tribute") sc += GOLDEN_WEIGHTS.trib;
    }
    return sc;
  });
  return legal[scores.indexOf(Math.max(...scores))];
}

// ===== UI 渲染 =====
function render(){
  const coachOn = document.getElementById("aiCoachSwitch").checked;
  const aiSug = coachOn ? getAIChoice() : null;

  // 状态
  document.getElementById("statePanel").innerHTML = `
    <div>回合: ${state.turn} | 入侵: ${state.inv}/3 | 牌库: ${state.deck.length} | 弃牌: ${state.discard.length}</div>
    <div>资源: 文${state.culture} 军${state.military} 工${state.industry} | 地区: ${occupiedRegions()}</div>
    <div><b>当前预测分: ${calcScore()}</b></div>
  `;

  // 地图
  const mapArea = document.getElementById("mapArea");
  mapArea.innerHTML = `
    <div class="map-wrap">
      <div class="map-col">${CITY_IDS.slice(0,3).map(id=>`<button class="city culture ${state.cities[id]?'occupied':''} ${(uiMode==='choose_conquest_city'&&!state.cities[id])||(uiMode==='choose_lose_city'&&state.cities[id])?'pickable':''}" onclick="onCityClick('${id}')">${id}${state.cities[id]?'✅':''}</button>`).join("")}</div>
      <div class="rome ${state.rome?'':'lost'}">ROME</div>
      <div class="map-col">${CITY_IDS.slice(3).map(id=>`<button class="city industry ${state.cities[id]?'occupied':''} ${(uiMode==='choose_conquest_city'&&!state.cities[id])||(uiMode==='choose_lose_city'&&state.cities[id])?'pickable':''}" onclick="onCityClick('${id}')">${id}${state.cities[id]?'✅':''}</button>`).join("")}</div>
    </div>
  `;

  // 手牌
  document.getElementById("handArea").innerHTML = hand.map(cid=>{
    const c=cardById(cid);
    return `<div class="card-item"><h3>${c.name}</h3><div>上: C${c.top.c} M${c.top.m} I${c.top.i}</div><div>下: ${c.bottom.type}</div></div>`;
  }).join("");

  // 动作
  const actionArea = document.getElementById("actionArea");
  actionArea.innerHTML = "";
  if(uiMode==="normal"){
    legal.forEach((a, i) => {
      // 修复高亮判定：对比 card_id + mode + kind
      const isBest = aiSug && (a.card_id === aiSug.card_id && a.mode === aiSug.mode && a.kind === aiSug.kind);
      const b = document.createElement("button");
      b.className = `action-btn ${isBest ? 'ai-highlight' : ''}`;
      b.textContent = `${i+1}. ${cardById(a.card_id).name} - ${a.mode==="top"?"取资源":a.kind}`;
      b.onclick = () => { pending=legal[i]; document.getElementById("btnConfirm").disabled=false; setMsg(`已选: ${b.textContent}`); };
      actionArea.appendChild(b);
    });
  } else if(uiMode==="invasion_choice"){
    actionArea.innerHTML = `<button onclick="onInvasionPay()">支付军事</button><button onclick="uiMode='choose_lose_city';render()">放弃地区</button>`;
  }

  // 历史
  document.getElementById("historyArea").innerHTML = trace.map(t=>`<div>T${t.turn}: ${t.event} (${t.after_score}分)</div>`).join("");
}

// ===== 交互 =====
function onConfirm(){
  if(!pending) return;
  const before = clone(state);
  pushUndo();
  const card = cardById(pending.card_id);
  
  // 记录AI建议
  const aiSug = document.getElementById("aiCoachSwitch").checked ? getAIChoice() : null;

  if(pending.mode==="top"){ gainWithTriggers({Culture:card.top.c,Military:card.top.m,Industry:card.top.i}); finishMove(before, "取资源", aiSug); }
  else if(pending.kind==="Conquest"){ uiMode="choose_conquest_city"; render(); return; }
  else if(pending.kind==="Tribute"){ const amt=occupiedRegions(); pending.meta.target==="Culture"?gainWithTriggers({Culture:amt}):gainWithTriggers({Industry:amt}); finishMove(before,"征收", aiSug); }
  else if(pending.kind==="Build_Building"){ pay(card.bottom.cost.c,card.bottom.cost.m,card.bottom.cost.i); state.built.push(pending.meta.building_id); finishMove(before,"建造建筑", aiSug); }
  else if(pending.kind==="Build_Monument"){ pay(card.bottom.cost.c,card.bottom.cost.m,card.bottom.cost.i); state.mono[pending.meta.monument_id]++; finishMove(before,"纪念物", aiSug); }
  
  hand.forEach(x=>{ if(x!==pending.card_id || pending.mode==='top') state.discard.push(x); });
  nextTurn();
}

function onCityClick(id){
  if(uiMode==="choose_conquest_city"){
    if(state.cities[id]) return;
    const before=clone(state); pushUndo(); state.cities[id]=true; pay(0,occupiedRegions()-1,0); 
    id.startsWith("C")?gainWithTriggers({Culture:1}):gainWithTriggers({Industry:1});
    finishMove(before, `征服${id}`, null); nextTurn();
  } else if(uiMode==="choose_lose_city"){
    if(!state.cities[id]) return; state.cities[id]=false; if(--pendingInvasion.loseLeft<=0) finishInvasionStep(); render();
  }
}

function finishMove(before, name, aiSug){
  const s = calcScore();
  trace.push({turn:state.turn, event:name, after_score:s, before, after:clone(state), user_choice:pending, ai_choice:aiSug});
  if(checkInvasion()) return;
}

// 辅助
function pushUndo(){ undoStack.push({state:clone(state),hand:clone(hand),legal:clone(legal),trace:clone(trace),uiMode,pendingConquestAction:clone(pendingConquestAction),pendingInvasion:clone(pendingInvasion)}); }
function onUndo(){ if(undoStack.length===0) return; const u=undoStack.pop(); state=u.state; hand=u.hand; legal=u.legal; trace=u.trace; uiMode=u.uiMode; pendingConquestAction=u.pendingConquestAction; pendingInvasion=u.pendingInvasion; render(); }
function checkInvasion(){ if(state.deck.length>0 || state.inv>=3) return false; if(colosseumActive()){ state.inv++; state.deck=shuffle(state.discard); state.discard=[]; return false; } const inv=INVASIONS[state.inv]; if(canPay(0,inv.pay,0)){ uiMode="invasion_choice"; pendingInvasion={pay:inv.pay,loseLeft:inv.lose}; render(); return true; } else { uiMode="choose_lose_city"; pendingInvasion={loseLeft:inv.lose}; render(); return true; } }
function onInvasionPay(){ pay(0,pendingInvasion.pay,0); finishInvasionStep(); }
function finishInvasionStep(){ state.inv++; state.deck=shuffle(state.discard); state.discard=[]; uiMode="normal"; nextTurn(); }
function setMsg(t){ document.getElementById("msg").textContent=t; }
function calcScore(){ if(state.lost) return 0; let s=occupiedRegions(); state.built.forEach(b=>{ if(BUILDINGS[b]&&BUILDINGS[b].gp) s+=BUILDINGS[b].gp; }); Object.entries(state.mono).forEach(([m,p])=>{ if(p>=2){ const mo=MONUMENTS[m]; if(mo.type==="FlatGP") s+=mo.v; else if(mo.type==="PerBuilding") s+=mo.v*state.built.length; else if(mo.type==="PerRegion") s+=mo.v*occupiedRegions(); else if(mo.type==="MinResource") s+=mo.v*Math.min(state.culture,state.military,state.industry); } }); return s; }

// 导出与上传
function onExport(){
  const payload = { source: "mobile_pwa", session_id: sessionId, final_summary: { score: calcScore(), lost: state.lost }, records: trace };
  if(window.RomeUploader && window.RomeUploader.getAutoUploadEnabled()) {
    window.RomeUploader.enqueueIfQualified(payload, setMsg);
    window.RomeUploader.flushQueue(setMsg);
  }
  const blob = new Blob([JSON.stringify(payload,null,2)], {type:"application/json"});
  const a=document.createElement("a"); a.href=URL.createObjectURL(blob); a.download=`trace_${sessionId}.json`; a.click();
}

document.getElementById("btnNew").onclick = initGame;
document.getElementById("btnUndo").onclick = onUndo;
document.getElementById("aiCoachSwitch").onchange = render;
document.getElementById("btnConfirm").onclick = onConfirm;
document.getElementById("btnToggleMonument").onclick = () => document.getElementById("monumentPanel").classList.toggle("hide");
document.getElementById("btnExport").onclick = onExport;

// 上传UI初始化
if(window.RomeUploader) {
  const sw = document.getElementById("autoUploadSwitch");
  const th = document.getElementById("uploadThreshold");
  const btn = document.getElementById("btnFlushUpload");
  if(sw && th && btn) {
    sw.checked = window.RomeUploader.getAutoUploadEnabled();
    th.value = window.RomeUploader.getScoreThreshold();
    sw.onchange = () => window.RomeUploader.setAutoUploadEnabled(sw.checked);
    th.onchange = () => { window.RomeUploader.setScoreThreshold(parseInt(th.value)); };
    btn.onclick = () => window.RomeUploader.flushQueue(setMsg);
  }
}

if("serviceWorker" in navigator){ window.addEventListener("load", ()=>navigator.serviceWorker.register("./sw.js")); }

initGame();