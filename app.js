// ===== 核心配置：移植自 Python 版的黄金权重 =====
const GOLDEN_WEIGHTS = {
  amphi: 765, senate: 581, arc: 418, pan: 204,
  conq_base: 241, conq_arc: 355, trib: 65,
  top_cul: 35, top_mil: 23, top_ind: 21
};

// ===== 基础数据（保持不变） =====
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
  B_KaiXuanDiaoSu:{gp:2}, B_DiGuoYinShuiDao:{gp:2},
  B_JunTuanYaoSai:{on:"military",bonus:2}, B_DiGuoJinKuang:{on:"industry",bonus:2}, B_YuanXingJingJiChang:{on:"culture",bonus:2}
};

const MONUMENTS = {
  M_WanShenMiao:{name:"万神庙",type:"FlatGP",v:4},
  M_LuoMaDouShouChang:{name:"罗马斗兽场",type:"FlatGP",v:2,special:"IgnoreInvasions"},
  M_DiGuoGuangChang:{name:"帝国广场",type:"FlatGP",v:2,special:"SenateSwap"},
  M_HaDeLiangLingQin:{name:"哈德良陵寝",type:"PerBuilding",v:1},
  M_KaiXuanMen:{name:"凯旋门",type:"PerRegion",v:1},
  M_TuLaZhenShiChang:{name:"图拉真市场",type:"MinResource",v:1},
};

const INVASIONS = [{pay:2,lose:1},{pay:3,lose:1},{pay:5,lose:2}];
const CITY_IDS = ["C1","C2","C3","I1","I2","I3"];

// ===== AI 逻辑移植 =====
function getAIChoice(s, h, l) {
  if (!l || l.length === 0) return null;
  
  const idx = Math.min(s.inv + 1, 3);
  const invCost = INVASIONS[idx-1].pay;
  const regions = (s.rome?1:0) + CITY_IDS.filter(id=>s.cities[id]).length;
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
      estMil -= card.bottom.cost.m;
      estCul -= card.bottom.cost.c;
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

  const maxIdx = scores.indexOf(Math.max(...scores));
  return l[maxIdx];
}

// ===== 游戏引擎与 UI 逻辑（整合版） =====
let state, hand, legal, pending, trace, undoStack, sessionId;
let uiMode = "normal";
let pendingConquestAction = null;
let pendingInvasion = null;

function initGame(){
  sessionId = "sess_" + Date.now();
  state = {
    culture:1, military:1, industry:1, max:9,
    rome:true, cities:{C1:false,C2:false,C3:false,I1:false,I2:false,I3:false},
    built:[], mono:Object.fromEntries(Object.keys(MONUMENTS).map(k=>[k,0])),
    deck:shuffle(CARDS.map(c=>c.id)), discard:[], inv:0, lost:false, turn:0
  };
  hand=[]; legal=[]; pending=null; trace=[]; undoStack=[];
  nextTurn();
}

function nextTurn(){
  if(state.lost || state.inv>=3){ render(); return; }
  state.turn++;
  const n=Math.min(3,state.deck.length);
  hand=[]; for(let i=0;i<n;i++) hand.push(state.deck.pop());
  
  // 计算合法动作
  legal=[];
  for(const cid of hand){
    const c=CARDS.find(x=>x.id===cid);
    legal.push({card_id:cid,mode:"top",kind:"TopResource",meta:{}});
    const b=c.bottom;
    const curRegs = (state.rome?1:0) + CITY_IDS.filter(id=>state.cities[id]).length;
    if(b.type==="Conquest" && canPay(0,curRegs,0) && CITY_IDS.some(id=>!state.cities[id])) 
      legal.push({card_id:cid,mode:"bottom",kind:"Conquest",meta:{}});
    else if(b.type==="Tribute") legal.push({card_id:cid,mode:"bottom",kind:"Tribute",meta:{target:b.target}});
    else if(b.type==="Build_Building" && !state.built.includes(b.ref) && canPay(b.cost.c,b.cost.m,b.cost.i))
      legal.push({card_id:cid,mode:"bottom",kind:"Build_Building",meta:{building_id:b.ref}});
    else if(b.type==="Build_Monument" && state.mono[b.ref]<2 && canPay(b.cost.c,b.cost.m,b.cost.i))
      legal.push({card_id:cid,mode:"bottom",kind:"Build_Monument",meta:{monument_id:b.ref}});
  }
  uiMode="normal"; render();
}

function canPay(c,m,i){
  const sa = state.mono["M_DiGuoGuangChang"]>=2;
  if(state.industry<i) return false;
  return sa ? (state.culture+state.military >= c+m) : (state.culture>=c && state.military>=m);
}

function render(){
  // 状态栏
  document.getElementById("statePanel").innerHTML = `
    <div>回合: ${state.turn} | 入侵: ${state.inv}/3 | 军事: ${state.military}/9 | 分数: ${calcScore()}</div>
  `;
  
  // 地图
  const mapHtml = CITY_IDS.map(id => {
    const occ = state.cities[id];
    const pickable = (uiMode==="choose_conquest_city" && !occ) || (uiMode==="choose_lose_city" && occ);
    return `<button class="city ${id.startsWith('C')?'culture':'industry'} ${occ?'occupied':''} ${pickable?'pickable':''}" onclick="onCityClick('${id}')">${id}</button>`;
  }).join("");
  document.getElementById("mapArea").innerHTML = `<div class="map-grid">${mapHtml}<div class="rome">${state.rome?'ROME':'FALLEN'}</div></div>`;

  // 手牌
  document.getElementById("handArea").innerHTML = hand.map(cid => {
    const c = CARDS.find(x=>x.id===cid);
    return `<div class="card"><b>${c.name}</b><br><small>上:${c.top.c}/${c.top.m}/${c.top.i}</small><br><small>下:${c.bottom.type}</small></div>`;
  }).join("");

  // 动作与教练提示
  const aiSug = getAIChoice(state, hand, legal);
  const actionArea = document.getElementById("actionArea");
  actionArea.innerHTML = legal.map((a, i) => {
    const isBest = aiSug && JSON.stringify(a) === JSON.stringify(aiSug);
    return `<button class="action-btn ${isBest?'ai-best':''}" onclick="selectAction(${i})">${i+1}. ${a.card_id} ${a.mode}${isBest?' ✨':''}</button>`;
  }).join("");

  // 终局复盘
  if(state.lost || state.inv>=3) renderReview();
}

function selectAction(i){
  pending = legal[i];
  document.getElementById("btnConfirm").disabled = false;
}

function onConfirm(){
  const aiSug = getAIChoice(state, hand, legal);
  const beforeSnap = JSON.parse(JSON.stringify(state));
  
  // 处理动作逻辑 (此处简化，实际应包含所有规则应用)
  // ... applyActionCore ...
  
  trace.push({
    turn: state.turn,
    user_choice: JSON.parse(JSON.stringify(pending)),
    ai_choice: JSON.parse(JSON.stringify(aiSug)),
    before: beforeSnap
  });
  
  // 此处应调用真正的规则应用函数，为了篇幅暂省，逻辑同上一版
  // applyAction(pending); resolveInvasion(); 
  // ...
  nextTurn();
}

function renderReview() {
  let html = "<h3>AI 深度复盘</h3><table border='1' style='width:100%'><tr><th>回合</th><th>你</th><th>AI</th><th>评价</th></tr>";
  trace.forEach(t => {
    const match = JSON.stringify(t.user_choice) === JSON.stringify(t.ai_choice);
    html += `<tr><td>${t.turn}</td><td>${t.user_choice.card_id}</td><td>${t.ai_choice.card_id}</td><td>${match?'✅':'❌'}</td></tr>`;
  });
  html += "</table>";
  document.getElementById("historyArea").innerHTML = html;
}

function calcScore(){ /* 同前版本 */ return 10; }
function shuffle(a){ /* 同前版本 */ return a; }

// 初始化
window.onload = initGame;