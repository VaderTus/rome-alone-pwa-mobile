// ===== AI 逻辑块 (不干扰引擎) =====
const GOLDEN_WEIGHTS = { amphi: 765, senate: 581, arc: 418, pan: 204, conq_base: 241, conq_arc: 355, trib: 65, top_cul: 35, top_mil: 23, top_ind: 21 };

function getAIChoice() {
  if (!legal || legal.length === 0) return null;
  const invCost = INVASIONS[state.inv] ? INVASIONS[state.inv].pay : 5;
  const regs = (state.rome?1:0) + CITY_IDS.filter(id=>state.cities[id]).length;
  const sa = state.mono["M_DiGuoGuangChang"] >= 2;
  const aa = state.mono["M_KaiXuanMen"] >= 2;
  let redLine = 0;
  if (state.turn < 19) {
    if (state.deck.length >= 6) redLine = 1;
    else if (state.deck.length >= 3) redLine = Math.max(1, invCost - 2);
    else redLine = invCost;
  }
  const scores = legal.map(a => {
    const card = cardById(a.card_id);
    let estMil = state.military, estCul = state.culture;
    if (a.kind === "Conquest") estMil -= regs;
    else if (a.mode === "bottom" && card.bottom.cost) {
      estMil -= (card.bottom.cost.m||0); estCul -= (card.bottom.cost.c||0);
    }
    const effMil = sa ? (estMil + estCul) : estMil;
    if (state.turn < 19 && effMil < redLine && a.mode !== "top") return -10000;
    let sc = 0;
    if (a.mode === "top") {
      if (state.military < redLine) sc += card.top.m * 400 + card.top.c * 20;
      else sc += card.top.c * (sa ? 35 : 25) + card.top.m * 23 + card.top.i * 21;
      sc += 20;
    } else {
      if (a.kind === "Build_Building") {
        if (a.meta.building_id === "B_YuanXingJingJiChang") sc += 765;
        else if (["B_KaiXuanDiaoSu","B_DiGuoYinShuiDao"].includes(a.meta.building_id)) sc += 160;
      }
      if (a.kind === "Build_Monument") {
        if (a.meta.monument_id === "M_DiGuoGuangChang") sc += 581;
        else if (a.meta.monument_id === "M_KaiXuanMen") sc += 418;
        else if (a.meta.monument_id === "M_WanShenMiao") sc += 204;
      }
      if (a.kind === "Conquest") sc += aa ? 355 : 241;
      if (a.kind === "Tribute") sc += 65;
    }
    return sc;
  });
  return legal[scores.indexOf(Math.max(...scores))];
}

// ===== 原始引擎逻辑 (恢复 V2 Map 版) =====
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

const CITY_IDS = ["C1","C2","C3","I1","I2","I3"];
const INVASIONS = [{pay:2,lose:1},{pay:3,lose:1},{pay:5,lose:2}];

function cardById(id){ return CARDS.find(c=>c.id===id); }
function clone(x){ return JSON.parse(JSON.stringify(x)); }
function shuffle(a){ for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];} return a; }

function initGame(){
  sessionId = "sess_" + Date.now();
  state = { culture:1, military:1, industry:1, max:9, rome:true, cities:{C1:false,C2:false,C3:false,I1:false,I2:false,I3:false}, built:[], mono:Object.fromEntries(Object.keys(MONUMENTS).map(k=>[k,0])), deck:shuffle(CARDS.map(c=>c.id)), discard:[], inv:0, lost:false, turn:0 };
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
  legal=[];
  hand.forEach(cid=>{
    const c=cardById(cid);
    legal.push({card_id:cid,mode:"top",kind:"TopResource",meta:{}});
    const curRegs = occupiedRegions();
    if(c.bottom.type==="Conquest" && canPay(0,curRegs,0) && CITY_IDS.some(id=>!state.cities[id])) legal.push({card_id:cid,mode:"bottom",kind:"Conquest",meta:{}});
    else if(c.bottom.type==="Tribute") legal.push({card_id:cid,mode:"bottom",kind:"Tribute",meta:{target:c.bottom.target}});
    else if(c.bottom.type==="Build_Building" && !state.built.includes(c.bottom.ref) && canPay(c.bottom.cost.c,c.bottom.cost.m,c.bottom.cost.i)) legal.push({card_id:cid,mode:"bottom",kind:"Build_Building",meta:{building_id:c.bottom.ref}});
    else if(c.bottom.type==="Build_Monument" && state.mono[c.bottom.ref]<2 && canPay(c.bottom.cost.c,c.bottom.cost.m,c.bottom.cost.i)) legal.push({card_id:cid,mode:"bottom",kind:"Build_Monument",meta:{monument_id:c.bottom.ref}});
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
  state.industry-=i;
  if(!senateActive()){ state.culture-=c; state.military-=m; return; }
  let need=c+m;
  while(need>0){ if(state.culture>=state.military && state.culture>0) state.culture--; else if(state.military>0) state.military--; else state.culture--; need--; }
}
function addRes(type,amt){ const k=type==="Culture"?"culture":type==="Military"?"military":"industry"; const b=state[k]; state[k]=Math.min(9,state[k]+amt); return state[k]-b; }
function gainWithTriggers(g){
  let c=g.Culture||0,m=g.Military||0,i=g.Industry||0;
  if(senateActive()){ let t=c+m; c=0; m=0; while(t>0){ if(state.culture<=state.military)c++; else m++; t--; } }
  const gc=addRes("Culture",c), gm=addRes("Military",m), gi=addRes("Industry",i);
  if(gc>0 && state.built.includes("B_YuanXingJingJiChang")) addRes("Culture",2);
  if(gm>0 && state.built.includes("B_JunTuanYaoSai")) addRes("Military",2);
  if(gi>0 && state.built.includes("B_DiGuoJinKuang")) addRes("Industry",2);
}

// ===== UI 与 交互 =====
function render(){
  const coachOn = document.getElementById("aiCoachSwitch").checked;
  const aiSug = coachOn ? getAIChoice() : null;

  // 状态栏
  document.getElementById("statePanel").innerHTML = `
    <h2>状态</h2>
    <div>回合: ${state.turn} | 入侵: ${state.inv}/3 | 牌库: ${state.deck.length} | 弃牌: ${state.discard.length}</div>
    <div>资源: 文 ${state.culture}, 军 ${state.military}, 工 ${state.industry} | 地区: ${occupiedRegions()}</div>
    <div><b>当前预测分: ${calcScore()}</b></div>
  `;

  // 地图
  const mapArea = document.getElementById("mapArea");
  mapArea.innerHTML = `
    <div class="map-wrap">
      <div class="map-col">${CITY_IDS.slice(0,3).map(id=>`<button class="city culture ${state.cities[id]?'occupied':''} ${(uiMode==='choose_conquest_city'&&!state.cities[id])||(uiMode==='choose_lose_city'&&state.cities[id])?'pickable':''}" onclick="onCityClick('${id}')">${id}${state.cities[id]?'✅':''}</button>`).join("")}</div>
      <div class="rome">ROME ${state.rome?'✅':'❌'}</div>
      <div class="map-col">${CITY_IDS.slice(3).map(id=>`<button class="city industry ${state.cities[id]?'occupied':''} ${(uiMode==='choose_conquest_city'&&!state.cities[id])||(uiMode==='choose_lose_city'&&state.cities[id])?'pickable':''}" onclick="onCityClick('${id}')">${id}${state.cities[id]?'✅':''}</button>`).join("")}</div>
    </div>
  `;

  // 手牌
  document.getElementById("handArea").innerHTML = hand.map(cid=>{
    const c=cardById(cid);
    return `<div class="card"><h3>${c.name}</h3><small>${cid}</small><div class="sep"></div>上: ${c.top.c}/${c.top.m}/${c.top.i}<br>下: ${c.bottom.type}</div>`;
  }).join("");

  // 动作按钮高亮
  const actionArea = document.getElementById("actionArea");
  actionArea.innerHTML = "";
  if(uiMode==="normal"){
    legal.forEach((a, i) => {
      const isBest = coachOn && aiSug && (a.card_id === aiSug.card_id && a.mode === aiSug.mode && a.kind === aiSug.kind);
      const b = document.createElement("button");
      b.className = isBest ? "ai-highlight" : "";
      b.textContent = `${i+1}. ${cardById(a.card_id).name} - ${a.mode==="top"?"取资源":a.kind} ${isBest?'✨':''}`;
      b.onclick = () => { pending=a; document.getElementById("btnConfirm").disabled=false; setMsg(`已选: ${b.textContent}`); };
      actionArea.appendChild(b);
    });
  } else if(uiMode==="invasion_choice"){
    actionArea.innerHTML = `<button onclick="onInvasionPay()">支付军事</button><button onclick="uiMode='choose_lose_city';render()">放弃地区</button>`;
  }

  // 历史
  document.getElementById("historyArea").innerHTML = trace.map(t=>`T${t.turn}: ${t.event} (${t.after_score}分)`).join("<br>");
  
  // 纪念物说明 (侧边栏)
  document.getElementById("monumentInfo").innerHTML = Object.entries(MONUMENTS).map(([k,v])=>`<div class="card"><b>${v.name}</b> (${state.mono[k]}/2)<br><small>${v.desc}</small></div>`).join("");
}

// ... 保持 applyAction, onConfirm, onUndo, onExport 等逻辑与 V2 版完全一致 ...
function onConfirm(){
  if(!pending) return;
  const before = clone(state);
  const card = cardById(pending.card_id);
  if(pending.mode==="top"){ gainWithTriggers({Culture:card.top.c,Military:card.top.m,Industry:card.top.i}); finishMove(before, "取资源"); }
  else if(pending.kind==="Conquest"){ uiMode="choose_conquest_city"; render(); return; }
  else if(pending.kind==="Tribute"){ const amt=occupiedRegions(); pending.meta.target==="Culture"?gainWithTriggers({Culture:amt}):gainWithTriggers({Industry:amt}); finishMove(before,"征收"); }
  else if(pending.kind==="Build_Building"){ pay(card.bottom.cost.c,card.bottom.cost.m,card.bottom.cost.i); state.built.push(pending.meta.building_id); finishMove(before,"建造建筑"); }
  else if(pending.kind==="Build_Monument"){ pay(card.bottom.cost.c,card.bottom.cost.m,card.bottom.cost.i); state.mono[pending.meta.monument_id]++; finishMove(before,"推进纪念物"); }
  hand.forEach(x=>{ if(x!==pending.card_id || pending.mode==='top') state.discard.push(x); }); // 建筑逻辑已处理
  nextTurn();
}

function onCityClick(id){
  if(uiMode==="choose_conquest_city"){
    if(state.cities[id]) return;
    const before=clone(state); state.cities[id]=true; pay(0,occupiedRegions()-1,0); id.startsWith("C")?gainWithTriggers({Culture:1}):gainWithTriggers({Industry:1});
    finishMove(before, `征服${id}`); nextTurn();
  } else if(uiMode==="choose_lose_city"){
    if(!state.cities[id]) return; state.cities[id]=false; if(--pendingInvasion.loseLeft<=0) finishInvasionStep(); render();
  }
}

function finishMove(before, name){
  const s = calcScore();
  trace.push({turn:state.turn, event:name, after_score:s, before, after:clone(state)});
  if(checkInvasion()) return;
}

function checkInvasion(){
  if(state.deck.length>0 || state.inv>=3) return false;
  if(colosseumActive()){ state.inv++; state.deck=shuffle(state.discard); state.discard=[]; return false; }
  const inv=INVASIONS[state.inv];
  if(canPay(0,inv.pay,0)){ uiMode="invasion_choice"; pendingInvasion={pay:inv.pay,loseLeft:inv.lose}; render(); return true; }
  else { uiMode="choose_lose_city"; pendingInvasion={loseLeft:inv.lose}; render(); return true; }
}
function onInvasionPay(){ pay(0,pendingInvasion.pay,0); finishInvasionStep(); }
function finishInvasionStep(){ state.inv++; state.deck=shuffle(state.discard); state.discard=[]; uiMode="normal"; nextTurn(); }
function setMsg(t){ document.getElementById("msg").textContent=t; }
function calcScore(){ /* 计分逻辑 ... */ let s=occupiedRegions(); state.built.forEach(b=>{ if(BUILDINGS[b]&&BUILDINGS[b].gp) s+=BUILDINGS[b].gp; }); Object.entries(state.mono).forEach(([m,p])=>{ if(p>=2){ const mo=MONUMENTS[m]; if(mo.type==="FlatGP") s+=mo.v; else if(mo.type==="PerBuilding") s+=mo.v*state.built.length; else if(mo.type==="PerRegion") s+=mo.v*occupiedRegions(); else if(mo.type==="MinResource") s+=mo.v*Math.min(state.culture,state.military,state.industry); } }); return s; }

document.getElementById("btnNew").onclick = initGame;
document.getElementById("btnUndo").onclick = onUndo;
document.getElementById("aiCoachSwitch").onchange = render;
document.getElementById("btnConfirm").onclick = onConfirm;
document.getElementById("btnToggleMonument").onclick = () => document.getElementById("monumentPanel").classList.toggle("hide");
document.getElementById("btnExport").onclick = onExport;

initGame();