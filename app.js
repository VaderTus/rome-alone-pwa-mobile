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
  M_LuoMaDouShouChang:{name:"罗马斗兽场",type:"FlatGP",v:2,special:"IgnoreInvasions",desc:"完成后+2分，忽略后续入侵"},
  M_DiGuoGuangChang:{name:"帝国广场",type:"FlatGP",v:2,special:"SenateSwap",desc:"完成后+2分，文/军可互换支付"},
  M_HaDeLiangLingQin:{name:"哈德良陵寝",type:"PerBuilding",v:1,desc:"完成后每建筑+1分"},
  M_KaiXuanMen:{name:"凯旋门",type:"PerRegion",v:1,desc:"完成后每地区+1分"},
  M_TuLaZhenShiChang:{name:"图拉真市场",type:"MinResource",v:1,desc:"完成后按最小资源计分"},
};

const BUILDINGS = {
  B_KaiXuanDiaoSu:{gp:2}, B_DiGuoYinShuiDao:{gp:2},
  B_JunTuanYaoSai:{on:"military",bonus:2}, B_DiGuoJinKuang:{on:"industry",bonus:2}, B_YuanXingJingJiChang:{on:"culture",bonus:2}
};

const CITY_IDS = ["C1","C2","C3","I1","I2","I3"];
const INVASIONS = [{pay:2,lose:1},{pay:3,lose:1},{pay:5,lose:2}];

function cardById(id){ return CARDS.find(c=>c.id===id); }
function clone(x){ return JSON.parse(JSON.stringify(x)); }
function shuffle(a){ for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];} return a; }

let state, hand, legal, pending, trace, undoStack, sessionId;
let uiMode = "normal"; 
let pendingConquestAction = null;
let pendingInvasion = null;

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
  const n = Math.min(3, state.deck.length);
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
    const curRegs = (state.rome?1:0) + CITY_IDS.filter(id=>state.cities[id]).length;
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
function addRes(type,amt){ const k=type==="Culture"?"culture":type==="Military"?"military":"industry"; const b=state[k]; state[k]=Math.min(9,state[k]+amt); return state[k]-b; }
function gainWithTriggers(g){
  let c=g.Culture||0,m=g.Military||0,i=g.Industry||0;
  if(senateActive()){ let t=c+m; c=0; m=0; while(t>0){ if(state.culture<=state.military)c++; else m++; t--; } }
  const gc=addRes("Culture",c), gm=addRes("Military",m), gi=addRes("Industry",i);
  if(gc>0 && state.built.includes("B_YuanXingJiChang")) addRes("Culture",2);
  if(gm>0 && state.built.includes("B_JunTuanYaoSai")) addRes("Military",2);
  if(gi>0 && state.built.includes("B_DiGuoJinKuang")) addRes("Industry",2);
}

// ===== 关键修复：返回最佳动作的 INDEX =====
function getAIBestIndex() {
  if (!legal || legal.length === 0) return -1;
  const idx = Math.min(state.inv + 1, 3);
  const invCost = INVASIONS[idx-1].pay;
  const regions = occupiedRegions();
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
    if (a.kind === "Conquest") estMil -= regions;
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
  
  // 找到最高分对应的索引
  let maxScore = -999999;
  let bestIdx = -1;
  for(let i=0; i<scores.length; i++){
    if(scores[i] > maxScore){
      maxScore = scores[i];
      bestIdx = i;
    }
  }
  return bestIdx;
}

// ===== UI 渲染 =====
function render(){
  const coachOn = document.getElementById("aiCoachSwitch") ? document.getElementById("aiCoachSwitch").checked : false;
  // 直接拿最佳动作的索引
  const bestIdx = coachOn ? getAIBestIndex() : -1;

  document.getElementById("statePanel").innerHTML = `
    <h2>状态</h2>
    <div>回合: ${state.turn} | 入侵: ${state.inv}/3 | 牌库: ${state.deck.length} | 弃牌: ${state.discard.length}</div>
    <div>资源: 文 ${state.culture}, 军 ${state.military}, 工 ${state.industry} | 地区: ${occupiedRegions()}</div>
    <div>当前得分: <b>${calcScore()}</b></div>
  `;

  const mapArea = document.getElementById("mapArea");
  mapArea.innerHTML = `
    <div class="map-wrap">
      <div class="map-col">${CITY_IDS.slice(0,3).map(id=>`<button class="city culture ${state.cities[id]?'occupied':''} ${(uiMode==='choose_conquest_city'&&!state.cities[id])||(uiMode==='choose_lose_city'&&state.cities[id])?'pickable':''}" onclick="onCityClick('${id}')">${id}${state.cities[id]?'✅':''}</button>`).join("")}</div>
      <div class="rome">ROME ${state.rome?'✅':'❌'}</div>
      <div class="map-col">${CITY_IDS.slice(3).map(id=>`<button class="city industry ${state.cities[id]?'occupied':''} ${(uiMode==='choose_conquest_city'&&!state.cities[id])||(uiMode==='choose_lose_city'&&state.cities[id])?'pickable':''}" onclick="onCityClick('${id}')">${id}${state.cities[id]?'✅':''}</button>`).join("")}</div>
    </div>
  `;

  document.getElementById("handArea").innerHTML = hand.map(cid => {
    const c = cardById(cid);
    return `<div class="card"><h3>${c.name}</h3><small>${cid}</small><div class="sep"></div>上: ${c.top.c}/${c.top.m}/${c.top.i}<br>下: ${c.bottom.type}</div>`;
  }).join("");

  const actionArea = document.getElementById("actionArea");
  actionArea.innerHTML = "";
  
  if(uiMode==="normal"){
    legal.forEach((a, i) => {
      // 只要索引对上，就高亮
      const isBest = (i === bestIdx);
      const b = document.createElement("button");
      b.className = "action-btn";
      
      // 暴力内联样式，确保必须变黄
      if (isBest) {
        b.style.backgroundColor = "#fffde7";
        b.style.border = "3px solid #ffcc00";
        b.style.fontWeight = "bold";
        b.style.boxShadow = "0 0 10px rgba(255,204,0,0.5)";
      }
      
      b.textContent = `${i+1}. ${cardById(a.card_id).name} - ${a.mode==="top"?"取资源":a.kind} ${isBest?'(✨ AI推荐)':''}`;
      b.onclick = () => { pending=a; document.getElementById("btnConfirm").disabled=false; setMsg(`已选: ${b.textContent}`); };
      actionArea.appendChild(b);
    });
  } else if(uiMode==="invasion_choice"){
    actionArea.innerHTML = `<button onclick="pay(0,${pendingInvasion.pay},0);finishInvasionStep()">支付军事 ${pendingInvasion.pay}</button><button onclick="uiMode='choose_lose_city';render()">丢弃地区</button>`;
  }

  document.getElementById("monumentInfo").innerHTML = Object.entries(MONUMENTS).map(([k,v])=>`<div class="card"><b>${v.name}</b> (${state.mono[k]}/2)<br><small>${v.desc}</small></div>`).join("");
  document.getElementById("historyArea").innerHTML = trace.map(t=>`T${t.turn}: ${t.event} (${t.after_score}分)`).join("<br>");
}

// 事件绑定
function onCityClick(cityId){
  if(uiMode==="choose_conquest_city"){
    if(state.cities[cityId]) return;
    pushUndo();
    const before = clone(state);
    pay(0, occupiedRegions()-1, 0); // 扣除之前预扣的费用
    state.cities[cityId]=true;
    cityId.startsWith("C") ? gainWithTriggers({Culture:1}) : gainWithTriggers({Industry:1});
    hand.forEach(x=>state.discard.push(x));
    finishMove(before, `征服 ${cityId}`);
  } else if(uiMode==="choose_lose_city"){
    if(!state.cities[cityId]) return;
    state.cities[cityId]=false;
    if(--pendingInvasion.loseLeft <= 0) finishInvasionStep();
    render();
  }
}

function onConfirm(){
  if(!pending) return;
  pushUndo();
  // 记录 AI 选择用于导出，但不影响逻辑
  const bestIdx = getAIBestIndex();
  const aiSug = bestIdx >= 0 ? legal[bestIdx] : null;
  
  const before = clone(state);
  const card = cardById(pending.card_id);

  if(pending.mode==="top"){
    gainWithTriggers({Culture:card.top.c, Military:card.top.m, Industry:card.top.i});
    hand.forEach(x=>state.discard.push(x));
    finishMove(before, "上半资源", aiSug);
  } else if(pending.kind==="Conquest"){
    pay(0, occupiedRegions(), 0); // 征服先扣钱
    pendingConquestAction = pending;
    uiMode = "choose_conquest_city";
    render();
    return;
  } else if(pending.kind==="Tribute"){
    const amt = occupiedRegions();
    pending.meta.target==="Culture" ? gainWithTriggers({Culture:amt}) : gainWithTriggers({Industry:amt});
    hand.forEach(x=>state.discard.push(x));
    finishMove(before, "征收", aiSug);
  } else if(pending.kind==="Build_Building"){
    pay(card.bottom.cost.c, card.bottom.cost.m, card.bottom.cost.i);
    state.built.push(pending.meta.building_id);
    hand.forEach(x=>{ if(x!==pending.card_id) state.discard.push(x); });
    finishMove(before, "建筑", aiSug);
  } else if(pending.kind==="Build_Monument"){
    pay(card.bottom.cost.c, card.bottom.cost.m, card.bottom.cost.i);
    state.mono[pending.meta.monument_id]++;
    hand.forEach(x=>state.discard.push(x));
    finishMove(before, "纪念物", aiSug);
  }
}

function pushUndo(){
  undoStack.push({
    state:clone(state), hand:clone(hand), legal:clone(legal), trace:clone(trace),
    uiMode, pendingConquestAction:clone(pendingConquestAction), pendingInvasion:clone(pendingInvasion)
  });
}

function onUndo(){
  if(undoStack.length===0) return;
  const u = undoStack.pop();
  state=u.state; hand=u.hand; legal=u.legal; trace=u.trace;
  uiMode=u.uiMode; pendingConquestAction=u.pendingConquestAction; pendingInvasion=u.pendingInvasion;
  render();
}

function finishMove(before, eventName, aiSug){
  const after = clone(state);
  trace.push({turn:state.turn, event:eventName, before, after, user_choice:pending, ai_choice:aiSug, after_score:calcScore()});
  if(!checkInvasion()) nextTurn();
}

function checkInvasion(){
  if(state.deck.length>0 || state.inv>=3) return false;
  if(colosseumActive()){ state.inv++; state.deck=shuffle(state.discard); state.discard=[]; return false; }
  const inv = INVASIONS[state.inv];
  if(canPay(0, inv.pay, 0)) { uiMode="invasion_choice"; pendingInvasion={pay:inv.pay, loseLeft:inv.lose}; render(); return true; }
  else { uiMode="choose_lose_city"; pendingInvasion={loseLeft:inv.lose}; render(); return true; }
}
function finishInvasionStep(){ state.inv++; state.deck=shuffle(state.discard); state.discard=[]; uiMode="normal"; nextTurn(); }
function setMsg(t){ document.getElementById("msg").textContent=t; }
function calcScore(){ if(state.lost) return 0; let s = occupiedRegions(); state.built.forEach(bid => { if(BUILDINGS[bid]&&BUILDINGS[bid].gp) s += BUILDINGS[bid].gp; }); Object.entries(state.mono).forEach(([mid,p])=>{ if(p>=2){ const m=MONUMENTS[mid]; if(m.type==="FlatGP") s+=m.v; else if(m.type==="PerBuilding") s+=m.v*state.built.length; else if(m.type==="PerRegion") s+=m.v*occupiedRegions(); else if(m.type==="MinResource") s+=m.v*Math.min(state.culture,state.military,state.industry); } }); return s; }

function onExport(){
  const payload = { source: "mobile_pwa", session_id: sessionId, final_summary: { score: calcScore(), lost: state.lost }, records: trace };
  if(window.RomeUploader && window.RomeUploader.getAutoUploadEnabled()){
    window.RomeUploader.enqueueIfQualified(payload, setMsg);
    window.RomeUploader.flushQueue(setMsg);
  }
  const blob = new Blob([JSON.stringify(payload,null,2)], {type:"application/json"});
  const a=document.createElement("a"); a.href=URL.createObjectURL(blob); a.download=`trace_${sessionId}.json`; a.click();
  setMsg("日志已导出 JSON");
}

document.getElementById("btnNew").onclick = initGame;
document.getElementById("btnUndo").onclick = onUndo;
document.getElementById("aiCoachSwitch").onchange = render;
document.getElementById("btnConfirm").onclick = onConfirm;
document.getElementById("btnToggleMonument").onclick = () => document.getElementById("monumentPanel").classList.toggle("hide");
document.getElementById("btnExport").onclick = onExport;

initGame();