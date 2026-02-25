// ===== 1. AI 黄金权重（移植自 Python Final 版） =====
const GOLDEN_WEIGHTS = {
  amphi: 765, senate: 581, arc: 418, pan: 204,
  conq_base: 241, conq_arc: 355, trib: 65,
  top_cul: 35, top_mil: 23, top_ind: 21
};

// ===== 2. 基础数据 (与 CSV 保持同步) =====
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
  M_LuoMaDouShouChang:{name:"罗马斗兽场",type:"FlatGP",v:2,special:"IgnoreInvasions",desc:"+2分，且后续入侵不掉地不扣钱"},
  M_DiGuoGuangChang:{name:"帝国广场",type:"FlatGP",v:2,special:"SenateSwap",desc:"+2分，文化/军事图标可互换支付"},
  M_HaDeLiangLingQin:{name:"哈德良陵寝",type:"PerBuilding",v:1,desc:"完成后每个已建建筑+1分"},
  M_KaiXuanMen:{name:"凯旋门",type:"PerRegion",v:1,desc:"完成后每个已占领地区+1分"},
  M_TuLaZhenShiChang:{name:"图拉真市场",type:"MinResource",v:1,desc:"完成后按三资源最小值计分"},
};

const BUILDINGS = {
  B_KaiXuanDiaoSu:{gp:2}, B_DiGuoYinShuiDao:{gp:2},
  B_JunTuanYaoSai:{on:"military",bonus:2}, B_DiGuoJinKuang:{on:"industry",bonus:2}, B_YuanXingJingJiChang:{on:"culture",bonus:2}
};

const CITY_IDS = ["C1","C2","C3","I1","I2","I3"];
const INVASIONS = [{pay:2,lose:1},{pay:3,lose:1},{pay:5,lose:2}];

// ===== 3. 游戏核心引擎状态 =====
let state, hand, legal, pending, trace, undoStack, sessionId;
let uiMode = "normal"; // normal, choose_conquest_city, invasion_choice, choose_lose_city
let pendingConquestAction = null;
let pendingInvasion = null;

function cardById(id){ return CARDS.find(c=>c.id===id); }
function clone(x){ return JSON.parse(JSON.stringify(x)); }
function shuffle(a){ for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];} return a; }

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

function occupiedRegions(){ return (state.rome?1:0) + CITY_IDS.filter(id=>state.cities[id]).length; }
function senateActive(){ return state.mono["M_DiGuoGuangChang"]>=2; }
function colosseumActive(){ return state.mono["M_LuoMaDouShouChang"]>=2; }

function canPay(c,m,i){
  if(state.industry<i) return false;
  if(senateActive()) return (state.culture+state.military) >= (c+m);
  return state.culture>=c && state.military>=m;
}

function pay(c,m,i){
  state.industry -= i;
  if(!senateActive()){ state.culture-=c; state.military-=m; return; }
  let need=c+m;
  while(need>0){
    if(state.culture>=state.military && state.culture>0) state.culture--;
    else if(state.military>0) state.military--;
    else if(state.culture>0) state.culture--;
    need--;
  }
}

function addRes(type,amt){
  const k = type==="Culture"?"culture":type==="Military"?"military":"industry";
  const b = state[k]; state[k]=Math.min(9, state[k]+amt); return state[k]-b;
}

function gainWithTriggers(g){
  let c=g.Culture||0, m=g.Military||0, i=g.Industry||0;
  if(senateActive()){
    let t=c+m; c=0; m=0;
    while(t>0){ if(state.culture<=state.military)c++; else m++; t--; }
  }
  if(addRes("Culture",c)>0 && state.built.includes("B_YuanXingJingJiChang")) addRes("Culture",2);
  if(addRes("Military",m)>0 && state.built.includes("B_JunTuanYaoSai")) addRes("Military",2);
  if(addRes("Industry",i)>0 && state.built.includes("B_DiGuoJinKuang")) addRes("Industry",2);
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

// ===== 4. AI 建议引擎（与 Python 版逻辑严格一致） =====
function getAIChoice(s, h, l) {
  if (!l || l.length === 0) return null;
  const idx = Math.min(s.inv + 1, 3);
  const invCost = INVASIONS[idx-1].pay;
  const regions = occupiedRegions();
  const senateActive = s.mono["M_DiGuoGuangChang"] >= 2;
  const arcActive = s.mono["M_KaiXuanMen"] >= 2;

  let redLine = 0;
  if (s.turn < 19) {
    if (s.deck.length >= 6) redLine = 1;
    else if (s.deck.length >= 3) redLine = Math.max(1, invCost - 2);
    else redLine = invCost;
  }

  const scores = l.map(a => {
    const card = CARDS.find(c => c.id === a.card_id);
    let estMil = s.military;
    let estCul = s.culture;
    if (a.kind === "Conquest") estMil -= regions;
    else if (a.mode === "bottom" && (a.kind.startsWith("Build"))) {
      estMil -= card.bottom.cost.m; estCul -= card.bottom.cost.c;
    }
    const effectiveMil = senateActive ? (estMil + estCul) : estMil;
    if (s.turn < 19 && effectiveMil < redLine && a.mode !== "top") return -10000;

    let sc = 0;
    if (a.mode === "top") {
      if (s.military < redLine) sc += card.top.m * 400 + card.top.c * 20;
      else sc += card.top.c * (senateActive ? GOLDEN_WEIGHTS.top_cul : GOLDEN_WEIGHTS.top_cul - 10) + card.top.m * GOLDEN_WEIGHTS.top_mil + card.top.i * GOLDEN_WEIGHTS.top_ind;
      if (s.culture + card.top.c > 9) sc -= 40;
      if (s.military + card.top.m > 9) sc -= 40;
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
      if (a.kind === "Conquest") sc += arcActive ? GOLDEN_WEIGHTS.conq_arc : GOLDEN_WEIGHTS.conq_base;
      if (a.kind === "Tribute") sc += GOLDEN_WEIGHTS.trib;
    }
    return sc;
  });
  return l[scores.indexOf(Math.max(...scores))];
}

// ===== 5. UI 交互逻辑 =====
function onCityClick(cityId){
  if(uiMode==="choose_conquest_city"){
    if(state.cities[cityId]) return;
    const before = JSON.parse(JSON.stringify(state));
    pay(0, occupiedRegions(), 0);
    state.cities[cityId]=true;
    cityId.startsWith("C") ? gainWithTriggers({Culture:1}) : gainWithTriggers({Industry:1});
    hand.forEach(x=>state.discard.push(x));
    finishMove(before, `征服 ${cityId}`);
  } else if(uiMode==="choose_lose_city"){
    if(!state.cities[cityId]) return;
    state.cities[cityId]=false;
    pendingInvasion.loseLeft--;
    if(pendingInvasion.loseLeft<=0) finishInvasionStep();
    render();
  }
}

function onConfirm(){
  if(!pending) return;
  const aiSug = getAIChoice(state, hand, legal);
  const before = JSON.parse(JSON.stringify(state));
  const card = cardById(pending.card_id);

  if(pending.mode==="top"){
    gainWithTriggers({Culture:card.top.c, Military:card.top.m, Industry:card.top.i});
    hand.forEach(x=>state.discard.push(x));
    finishMove(before, "上半资源", aiSug);
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
  } else if(pending.kind==="Conquest"){
    pendingConquestAction = pending;
    uiMode = "choose_conquest_city";
    render();
  }
}

function finishMove(before, eventName, aiSug){
  const after = JSON.parse(JSON.stringify(state));
  trace.push({turn:state.turn, event:eventName, before, after, user_choice:pending, ai_choice:aiSug, after_score:calcScore()});
  if(!checkInvasion()) nextTurn();
}

function checkInvasion(){
  if(state.deck.length>0 || state.inv>=3) return false;
  if(colosseumActive()){ state.inv++; state.deck=shuffle(state.discard); state.discard=[]; return false; }
  const inv = INVASIONS[state.inv];
  if(canPay(0, inv.pay, 0)) { uiMode="invasion_choice"; pendingInvasion={pay:inv.pay, loseLeft:inv.lose}; }
  else { uiMode="choose_lose_city"; pendingInvasion={loseLeft:inv.lose}; }
  render(); return true;
}

function finishInvasionStep(){
  state.inv++; state.deck=shuffle(state.discard); state.discard=[]; uiMode="normal"; nextTurn();
}

function calcScore(){
  if(state.lost) return 0;
  let s = occupiedRegions();
  state.built.forEach(bid => s += (BUILDINGS[bid].gp||0));
  Object.entries(state.mono).forEach(([mid,p])=>{
    if(p<2) return;
    const m=MONUMENTS[mid];
    if(m.type==="FlatGP") s+=m.v;
    else if(m.type==="PerBuilding") s+=m.v*state.built.length;
    else if(m.type==="PerRegion") s+=m.v*occupiedRegions();
    else if(m.type==="MinResource") s+=m.v*Math.min(state.culture,state.military,state.industry);
  });
  return s;
}

function render(){
  document.getElementById("statePanel").innerHTML = `
    <b>回合 ${state.turn}</b> | 军事: ${state.military}/9 | 地区: ${occupiedRegions()} | 入侵: ${state.inv}/3 | <b>预测分: ${calcScore()}</b>
  `;
  const mapHtml = CITY_IDS.map(id => {
    const occ = state.cities[id];
    const pickable = (uiMode==="choose_conquest_city" && !occ) || (uiMode==="choose_lose_city" && occ);
    return `<button class="city ${id.startsWith('C')?'culture':'industry'} ${occ?'occupied':''} ${pickable?'pickable':''}" onclick="onCityClick('${id}')">${id}</button>`;
  }).join("");
  document.getElementById("mapArea").innerHTML = `<div class="map-grid">${mapHtml}<div class="rome ${state.rome?'':'lost'}">ROME</div></div>`;

  document.getElementById("handArea").innerHTML = hand.map(cid => {
    const c = cardById(cid);
    return `<div class="card"><b>${c.name}</b><br><small>上:C${c.top.c}M${c.top.m}I${c.top.i}</small><br><small>下:${c.bottom.type}</small></div>`;
  }).join("");

  const aiSug = getAIChoice(state, hand, legal);
  document.getElementById("actionArea").innerHTML = (uiMode==="normal"?legal:[]) .map((a, i) => {
    const isBest = aiSug && JSON.stringify(a) === JSON.stringify(aiSug);
    return `<button class="action-btn ${isBest?'ai-best':''}" onclick="pending=legal[${i}];document.getElementById('btnConfirm').disabled=false;render();">${a.card_id} ${a.mode}${isBest?' ✨':''}</button>`;
  }).join("");

  if(uiMode==="invasion_choice") {
    document.getElementById("actionArea").innerHTML = `<button onclick="pay(0,${pendingInvasion.pay},0);finishInvasionStep()">支付军事 ${pendingInvasion.pay}</button>
    <button onclick="uiMode='choose_lose_city';render()">丢弃地区 ${pendingInvasion.loseLeft}</button>`;
  }
}

window.onload = initGame;