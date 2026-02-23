// ===== 数据 =====
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

const BUILDINGS = {
  B_KaiXuanDiaoSu:{gp:2,name:"凯旋雕塑",desc:"+2分"},
  B_DiGuoYinShuiDao:{gp:2,name:"帝国引水道",desc:"+2分"},
  B_JunTuanYaoSai:{on:"military",bonus:2,name:"军团要塞",desc:"首次得军事+2"},
  B_DiGuoJinKuang:{on:"industry",bonus:2,name:"帝国金矿",desc:"首次得工业+2"},
  B_YuanXingJingJiChang:{on:"culture",bonus:2,name:"圆形竞技场",desc:"首次得文化+2"},
};

const MONUMENTS = {
  M_WanShenMiao:{name:"万神庙",type:"FlatGP",v:4,desc:"完成后+4分"},
  M_LuoMaDouShouChang:{name:"罗马斗兽场",type:"FlatGP",v:2,special:"IgnoreInvasions",desc:"完成后+2分，忽略后续入侵"},
  M_DiGuoGuangChang:{name:"帝国广场",type:"FlatGP",v:2,special:"SenateSwap",desc:"完成后+2分，文化/军事可互换"},
  M_HaDeLiangLingQin:{name:"哈德良陵寝",type:"PerBuilding",v:1,desc:"完成后每建筑+1分"},
  M_KaiXuanMen:{name:"凯旋门",type:"PerRegion",v:1,desc:"完成后每地区+1分"},
  M_TuLaZhenShiChang:{name:"图拉真市场",type:"MinResource",v:1,desc:"完成后按最小资源计分"},
};

const INVASIONS = [{pay:2,lose:1},{pay:3,lose:1},{pay:5,lose:2}];
const CITY_IDS = ["C1","C2","C3","I1","I2","I3"];

function cardById(id){ return CARDS.find(c=>c.id===id); }
function clone(x){ return JSON.parse(JSON.stringify(x)); }
function shuffle(a){ for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1)); [a[i],a[j]]=[a[j],a[i]];} return a; }

// ===== 状态 =====
let state, hand, legal, pending, trace, undoStack, sessionId;
let uiMode = "normal"; // normal | choose_conquest_city | invasion_choice | choose_lose_city
let pendingConquestAction = null;
let pendingInvasion = null;

function initGame(){
  sessionId = "sess_" + Date.now();
  state = {
    culture:1,military:1,industry:1,max:9,
    rome:true,
    cities:{C1:false,C2:false,C3:false,I1:false,I2:false,I3:false},
    built:[],
    mono:Object.fromEntries(Object.keys(MONUMENTS).map(k=>[k,0])),
    deck:shuffle(CARDS.map(c=>c.id)),
    discard:[],
    inv:0,lost:false,turn:0
  };
  hand=[]; legal=[]; pending=null; trace=[]; undoStack=[];
  uiMode="normal"; pendingConquestAction=null; pendingInvasion=null;
  nextTurn();
}

function occupiedRegions(){ return (state.rome?1:0) + CITY_IDS.filter(id=>state.cities[id]).length; }
function senateActive(){ return state.mono["M_DiGuoGuangChang"]>=2; }
function colosseumActive(){ return state.mono["M_LuoMaDouShouChang"]>=2; }

function addRes(k, amt){
  if(amt<=0) return 0;
  const key = (k==="Culture"?"culture":k==="Military"?"military":"industry");
  const before = state[key];
  state[key] = Math.min(state.max, state[key]+amt);
  return state[key]-before;
}
function canPay(c,m,i){
  if(state.industry<i) return false;
  if(senateActive()) return (state.culture+state.military)>=(c+m);
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
function gainWithTriggers(g){
  let c=g.Culture||0, m=g.Military||0, i=g.Industry||0;
  if(senateActive()){
    let t=c+m; c=0; m=0;
    while(t>0){ if(state.culture<=state.military)c++; else m++; t--; }
  }
  const gotC = addRes("Culture",c)>0;
  const gotM = addRes("Military",m)>0;
  const gotI = addRes("Industry",i)>0;
  if(gotC && state.built.includes("B_YuanXingJingJiChang")) addRes("Culture",2);
  if(gotM && state.built.includes("B_JunTuanYaoSai")) addRes("Military",2);
  if(gotI && state.built.includes("B_DiGuoJinKuang")) addRes("Industry",2);
}

function drawHand(){
  const n=Math.min(3,state.deck.length);
  hand=[]; for(let i=0;i<n;i++) hand.push(state.deck.pop());
}
function computeLegal(){
  legal=[];
  for(const cid of hand){
    const c=cardById(cid);
    legal.push({card_id:cid,mode:"top",kind:"TopResource",meta:{}});
    const b=c.bottom;

    if(b.type==="Conquest"){
      const need=occupiedRegions();
      const hasFreeCity = CITY_IDS.some(id=>!state.cities[id]);
      if(hasFreeCity && canPay(0,need,0)){
        legal.push({card_id:cid,mode:"bottom",kind:"Conquest",meta:{}});
      }
    } else if(b.type==="Tribute"){
      legal.push({card_id:cid,mode:"bottom",kind:"Tribute",meta:{target:b.target}});
    } else if(b.type==="Build_Building"){
      if(!state.built.includes(b.ref) && canPay(b.cost.c,b.cost.m,b.cost.i)){
        legal.push({card_id:cid,mode:"bottom",kind:"Build_Building",meta:{building_id:b.ref}});
      }
    } else if(b.type==="Build_Monument"){
      if(state.mono[b.ref]<2 && canPay(b.cost.c,b.cost.m,b.cost.i)){
        legal.push({card_id:cid,mode:"bottom",kind:"Build_Monument",meta:{monument_id:b.ref}});
      }
    }
  }
}

function sameAction(a,b){ return JSON.stringify(a)===JSON.stringify(b); }

function applyActionCore(a){
  const cid=a.card_id;
  const card=cardById(cid);

  if(a.mode==="top"){
    gainWithTriggers({Culture:card.top.c,Military:card.top.m,Industry:card.top.i});
    hand.forEach(x=>state.discard.push(x));
    return {type:"top"};
  }

  if(a.kind==="Tribute"){
    const amt=occupiedRegions();
    if(a.meta.target==="Culture") gainWithTriggers({Culture:amt});
    else gainWithTriggers({Industry:amt});
    hand.forEach(x=>state.discard.push(x));
    return {type:"tribute"};
  }

  if(a.kind==="Build_Building"){
    const b=card.bottom;
    pay(b.cost.c,b.cost.m,b.cost.i);
    state.built.push(b.ref);
    hand.forEach(x=>{ if(x!==cid) state.discard.push(x); });
    return {type:"build_building",building:b.ref};
  }

  if(a.kind==="Build_Monument"){
    const b=card.bottom;
    pay(b.cost.c,b.cost.m,b.cost.i);
    state.mono[b.ref]=Math.min(2,state.mono[b.ref]+1);
    hand.forEach(x=>state.discard.push(x));
    return {type:"build_monument",monument:b.ref};
  }

  if(a.kind==="Conquest"){
    // 延后到点城市时执行
    return {type:"need_city_pick"};
  }

  return {type:"unknown"};
}

function applyConquestToCity(cityId){
  const need = occupiedRegions();
  pay(0,need,0);
  state.cities[cityId]=true;

  if(cityId.startsWith("C")) gainWithTriggers({Culture:1});
  else gainWithTriggers({Industry:1});

  hand.forEach(x=>state.discard.push(x));
}

function startInvasionIfNeeded(){
  if(state.deck.length>0 || state.inv>=3) return false;

  const inv = INVASIONS[state.inv];
  if(colosseumActive()){
    state.inv++;
    state.deck = shuffle(state.discard);
    state.discard = [];
    return false;
  }

  const can = canPay(0,inv.pay,0);
  pendingInvasion = {idx:state.inv, pay:inv.pay, lose:inv.lose, canPay:can, loseLeft:inv.lose};

  if(can){
    uiMode = "invasion_choice"; // 玩家选择支付或失去城市
  } else {
    uiMode = "choose_lose_city"; // 被迫失去
  }
  return true;
}

function finishInvasionByPay(){
  pay(0,pendingInvasion.pay,0);
  state.inv++;
  state.deck = shuffle(state.discard);
  state.discard = [];
  pendingInvasion = null;
  uiMode = "normal";
}

function finishInvasionByLoseDone(){
  state.inv++;
  state.deck = shuffle(state.discard);
  state.discard = [];
  pendingInvasion = null;
  uiMode = "normal";
}

function loseOneCity(cityId){
  if(state.cities[cityId]){
    state.cities[cityId]=false;
    return true;
  }
  return false;
}

function nextTurn(){
  if(state.lost || state.inv>=3){ render(); return; }
  state.turn++;
  drawHand();
  computeLegal();
  pending=null;
  uiMode = "normal";
  render();
}

function gameOver(){ return state.lost || state.inv>=3; }

function score(){
  if(state.lost) return 0;
  let total = occupiedRegions();

  for(const bid of state.built){
    const b=BUILDINGS[bid];
    if(b?.gp) total += b.gp;
  }
  for(const [mid,p] of Object.entries(state.mono)){
    if(p<2) continue;
    const m = MONUMENTS[mid];
    if(m.type==="FlatGP") total += m.v;
    else if(m.type==="PerBuilding") total += m.v * state.built.length;
    else if(m.type==="PerRegion") total += m.v * occupiedRegions();
    else if(m.type==="MinResource") total += m.v * Math.min(state.culture,state.military,state.industry);
  }
  return total;
}

function snap(){
  return {
    turn:state.turn,
    culture:state.culture,military:state.military,industry:state.industry,
    occupied_regions:occupiedRegions(), inv:state.inv,
    built:[...state.built], mono:clone(state.mono),
    deck_left:state.deck.length, discard:state.discard.length, lost:state.lost
  };
}

// ===== UI =====
function setMsg(text, ok=true){
  const el=document.getElementById("msg");
  el.className = ok ? "msg-ok" : "msg-err";
  el.textContent = text;
}

function renderState(){
  const st = document.getElementById("statePanel");
  st.innerHTML = `
    <h2>状态</h2>
    <div>回合: ${state.turn} ｜ 入侵: ${state.inv}/3 ｜ 牌库: ${state.deck.length} ｜ 弃牌: ${state.discard.length}</div>
    <div>资源: 文化 ${state.culture}/9 ｜ 军事 ${state.military}/9 ｜ 工业 ${state.industry}/9</div>
    <div>占领地区: ${occupiedRegions()}（Rome + 文化城${CITY_IDS.filter(id=>id.startsWith("C")&&state.cities[id]).length} + 工业城${CITY_IDS.filter(id=>id.startsWith("I")&&state.cities[id]).length}）</div>
    <div>建筑: ${state.built.length?state.built.join(", "):"无"}</div>
    <div>当前分数(若终局): <b>${score()}</b></div>
  `;
}

function renderMap(){
  const m = document.getElementById("mapArea");
  const left = ["C1","C2","C3"];
  const right = ["I1","I2","I3"];

  const cityBtn = (id)=>{
    const occ = state.cities[id];
    const type = id.startsWith("C") ? "culture" : "industry";
    let pickable = false;
    if(uiMode==="choose_conquest_city") pickable = !occ;
    if(uiMode==="choose_lose_city") pickable = occ;
    return `<button class="city ${type} ${occ?"occupied":""} ${pickable?"pickable":""}" data-city="${id}">
      ${id} ${type==="culture"?"(文化)":"(工业)"} ${occ?"✅":"⬜"}
    </button>`;
  };

  m.innerHTML = `
    <div class="map-col">${left.map(cityBtn).join("")}</div>
    <div class="rome">ROME ${state.rome?"✅":"❌"}</div>
    <div class="map-col">${right.map(cityBtn).join("")}</div>
  `;

  m.querySelectorAll("[data-city]").forEach(btn=>{
    btn.onclick=()=>onCityClick(btn.getAttribute("data-city"));
  });
}

function renderHand(){
  const area=document.getElementById("handArea");
  area.innerHTML="";
  for(const cid of hand){
    const c=cardById(cid);
    const card=document.createElement("div");
    card.className="card";
    card.innerHTML = `
      <h3>${c.name}</h3>
      <div class="small">${cid}</div>
      <div class="sep"></div>
      <div><b>上半资源：</b>文化+${c.top.c} / 军事+${c.top.m} / 工业+${c.top.i}</div>
      <div class="sep"></div>
      <div><b>下半动作：</b>${bottomText(c)}</div>
    `;
    area.appendChild(card);
  }
}

function bottomText(c){
  const b=c.bottom;
  if(b.type==="Conquest") return "征服（支付军事=占领地区数，地图点选城市）";
  if(b.type==="Tribute") return `征收${b.target}（数量=占领地区数）`;
  if(b.type==="Build_Building") return `建造建筑(消耗 C${b.cost.c}/M${b.cost.m}/I${b.cost.i})`;
  if(b.type==="Build_Monument") return `建造纪念物(消耗 C${b.cost.c}/M${b.cost.m}/I${b.cost.i})`;
  return "无";
}

function renderActions(){
  const area=document.getElementById("actionArea");
  area.innerHTML="";
  document.getElementById("btnConfirm").disabled = true;

  if(gameOver()){
    setMsg(`对局结束：分数=${score()}，失败=${state.lost?"是":"否"}`, true);
    return;
  }

  if(uiMode==="invasion_choice"){
    area.innerHTML = `
      <button id="invPay">支付军事 ${pendingInvasion.pay}（避免入侵）</button>
      <button id="invLose">失去城市 ${pendingInvasion.lose}（自己选择）</button>
    `;
    document.getElementById("invPay").onclick=()=>{ finishInvasionByPay(); nextTurn(); };
    document.getElementById("invLose").onclick=()=>{
      uiMode="choose_lose_city";
      setMsg(`请在地图上选择要失去的城市，剩余 ${pendingInvasion.loseLeft} 座`, true);
      render();
    };
    setMsg(`入侵触发：请选择支付或失去城市`, false);
    return;
  }

  if(uiMode==="choose_conquest_city"){
    setMsg("请在地图上点击一个未占领城市进行征服", true);
    return;
  }

  if(uiMode==="choose_lose_city"){
    setMsg(`请在地图上选择要失去的城市，剩余 ${pendingInvasion.loseLeft} 座`, false);
    return;
  }

  // normal
  legal.forEach((a,idx)=>{
    const c=cardById(a.card_id);
    const b=document.createElement("button");
    b.textContent = `${idx+1}. ${c.name} - ${a.mode==="top"?"上半":"下半"}(${a.kind})`;
    b.onclick=()=>{
      pending = a;
      document.getElementById("btnConfirm").disabled = false;
      setMsg(`已选择：${b.textContent}`, true);
    };
    area.appendChild(b);
  });
}

function renderMonumentPanel(){
  const p=document.getElementById("monumentInfo");
  p.innerHTML = Object.entries(MONUMENTS).map(([k,v])=>{
    const prog = state.mono[k]||0;
    return `<div class="card">
      <h3>${v.name} (${prog}/2)</h3>
      <div>${v.desc}</div>
      <div class="small">${k}</div>
    </div>`;
  }).join("");
}

function renderHistory(){
  const h=document.getElementById("historyArea");
  h.innerHTML = trace.map((t,i)=>`#${i+1} T${t.turn} ${t.event} -> 分:${t.after_score}`).join("<br>");
}

function render(){
  renderState();
  renderMap();
  renderHand();
  renderActions();
  renderMonumentPanel();
  renderHistory();
}

// ===== 交互 =====
function onCityClick(cityId){
  if(uiMode==="choose_conquest_city"){
    if(state.cities[cityId]){ setMsg("该城市已占领，不能再次征服", false); return; }

    // 执行征服动作
    const before = snap();
    applyConquestToCity(cityId);
    const action = clone(pendingConquestAction);

    // 处理入侵或下一回合
    const invasionPending = startInvasionIfNeeded();
    const after = snap();

    trace.push({
      turn: state.turn,
      event: `征服 ${cityId} by ${action.card_id}`,
      chosen_action: action,
      conquest_city: cityId,
      before, after,
      after_score: score(),
      timestamp: new Date().toISOString(),
      source: "mobile_pwa",
      session_id: sessionId
    });

    pendingConquestAction=null;
    pending=null;
    if(!invasionPending && !gameOver()) nextTurn(); else render();
    return;
  }

  if(uiMode==="choose_lose_city"){
    if(!state.cities[cityId]){ setMsg("该城市未占领，不能失去", false); return; }
    loseOneCity(cityId);
    pendingInvasion.loseLeft -= 1;

    if(pendingInvasion.loseLeft <= 0){
      // 失城完成 -> 入侵结算完成
      if(!state.rome && occupiedRegions()<=0) state.lost=true;
      state.inv++;
      state.deck = shuffle(state.discard);
      state.discard = [];
      pendingInvasion = null;
      uiMode = "normal";

      if(!gameOver()) nextTurn(); else render();
    } else {
      setMsg(`还需失去 ${pendingInvasion.loseLeft} 座城市`, false);
      render();
    }
    return;
  }
}

function onConfirm(){
  if(!pending){ setMsg("请先选择动作", false); return; }
  const legalNow = legal.some(x=>sameAction(x,pending));
  if(!legalNow){ setMsg("非法动作，请重选", false); return; }

  undoStack.push({
    state: clone(state), hand: clone(hand), legal: clone(legal), pending: clone(pending),
    trace: clone(trace), uiMode, pendingConquestAction: clone(pendingConquestAction), pendingInvasion: clone(pendingInvasion)
  });

  const before = snap();
  const r = applyActionCore(pending);

  if(r.type==="need_city_pick"){
    pendingConquestAction = clone(pending);
    uiMode = "choose_conquest_city";
    setMsg("请在地图中点选要征服的城市", true);
    render();
    return;
  }

  const invasionPending = startInvasionIfNeeded();
  const after = snap();

  trace.push({
    turn: state.turn,
    event: `${pending.card_id}-${pending.kind}`,
    chosen_action: clone(pending),
    before, after,
    after_score: score(),
    timestamp: new Date().toISOString(),
    source: "mobile_pwa",
    session_id: sessionId
  });

  pending=null;
  if(!invasionPending && !gameOver()) nextTurn(); else render();
}

function onUndo(){
  if(undoStack.length===0){ setMsg("没有可撤销步骤", false); return; }
  const u=undoStack.pop();
  state=u.state; hand=u.hand; legal=u.legal; pending=u.pending; trace=u.trace;
  uiMode=u.uiMode; pendingConquestAction=u.pendingConquestAction; pendingInvasion=u.pendingInvasion;
  setMsg("已撤销上一步", true);
  render();
}

function onExport(){
  const payload = {
    source: "mobile_pwa",
    app_version: "pwa_v2_map",
    session_id: sessionId,
    created_at: new Date().toISOString(),
    final_summary: { score: score(), lost: state.lost, turns: state.turn, invasions_resolved: state.inv },
    records: trace
  };
  const blob = new Blob([JSON.stringify(payload,null,2)], {type:"application/json"});
  const a=document.createElement("a");
  a.href=URL.createObjectURL(blob);
  a.download=`mobile_trace_${sessionId}.json`;
  a.click();
  URL.revokeObjectURL(a.href);
  setMsg("日志已导出 JSON", true);
}

function bindEvents(){
  document.getElementById("btnNew").onclick=()=>initGame();
  document.getElementById("btnUndo").onclick=()=>onUndo();
  document.getElementById("btnExport").onclick=()=>onExport();
  document.getElementById("btnConfirm").onclick=()=>onConfirm();

  document.getElementById("btnToggleMonument").onclick=()=>{
    const panel = document.getElementById("monumentPanel");
    panel.classList.toggle("hide");
  };
}

if("serviceWorker" in navigator){
  window.addEventListener("load", ()=>navigator.serviceWorker.register("./sw.js"));
}

bindEvents();
initGame();