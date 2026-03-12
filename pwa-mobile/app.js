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

let aiBestCard = null;    
let aiBestMode = null;    
let aiBestMeta = {};      
let isAiThinking = false; 

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
  // 🏁 拦截死亡或通关状态
  if(state.lost || state.inv >= 3){ 
      uiMode = "game_over";
      render(); 
      return; 
  }
  state.turn++;
  const n = Math.min(3, state.deck.length);
  hand=[]; for(let i=0;i<n;i++) hand.push(state.deck.pop());
  pending=null; uiMode="normal";
  computeLegal(); 
}

function computeLegal(){
  legal = [];
  hand.forEach(cid => {
    const c = cardById(cid);
    legal.push({card_id:cid, mode:"top", kind:"TopResource", meta:{}});
    const b = c.bottom;
    const curRegs = (state.rome?1:0) + CITY_IDS.filter(id=>state.cities[id]).length;
    
    if(b.type==="Conquest" && canPay(0,curRegs,0)) {
      // 🚀 修复点：严密检查到底还有没有空地！
      let cul_free = !state.cities["C1"] || !state.cities["C2"] || !state.cities["C3"];
      let ind_free = !state.cities["I1"] || !state.cities["I2"] || !state.cities["I3"];
      if (cul_free || ind_free) legal.push({card_id:cid, mode:"bottom", kind:"Conquest", meta:{}});
    }
    else if(b.type==="Tribute") legal.push({card_id:cid, mode:"bottom", kind:"Tribute", meta:{target:b.target}});
    else if(b.type==="Build_Building" && !state.built.includes(b.ref) && canPay(b.cost.c, b.cost.m, b.cost.i))
      legal.push({card_id:cid, mode:"bottom", kind:"Build_Building", meta:{building_id:b.ref}});
    else if(b.type==="Build_Monument" && state.mono[b.ref]<2 && canPay(b.cost.c, b.cost.m, b.cost.i))
      legal.push({card_id:cid, mode:"bottom", kind:"Build_Monument", meta:{monument_id:b.ref}});
  });
  
  if (uiMode !== "game_over") fetchAIRecommendation();
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
    const k=type==="Culture"?"culture":type==="Military"?"military":"industry"; 
    const b=state[k]; 
    state[k]=Math.min(9,state[k]+amt); 
    return state[k]-b; 
}

// 🧠 修复点：彻底重写高智商的分配机制
function gainWithTriggers(g){
  let c = g.Culture || 0, m = g.Military || 0, i = g.Industry || 0;
  
  if(senateActive()){
    let base_cm = c + m;
    let total_cm = base_cm;
    // 触发器加成放入总池
    if(base_cm > 0 && state.built.includes("B_YuanXingJingJiChang")) total_cm += 2;
    if(base_cm > 0 && state.built.includes("B_JunTuanYaoSai")) total_cm += 2;

    // 智能防溢出分配器
    let final_c = 0; let final_m = 0;
    for(let step=0; step < total_cm; step++){
        if (state.culture + final_c >= 9 && state.military + final_m < 9) {
            final_m++; // 文化满了，塞给军事
        } else if (state.military + final_m >= 9 && state.culture + final_c < 9) {
            final_c++; // 军事满了，塞给文化
        } else if (state.culture + final_c <= state.military + final_m) {
            final_c++; // 优先补平短板
        } else {
            final_m++;
        }
    }
    c = final_c; m = final_m;
  } else {
    // 正常触发
    if(c > 0 && state.built.includes("B_YuanXingJingJiChang")) c += 2;
    if(m > 0 && state.built.includes("B_JunTuanYaoSai")) m += 2;
  }

  if(i > 0 && state.built.includes("B_DiGuoJinKuang")) i += 2;

  addRes("Culture", c); addRes("Military", m); addRes("Industry", i);
}

async function fetchAIRecommendation() {
  const coachOn = document.getElementById("aiCoachSwitch") ? document.getElementById("aiCoachSwitch").checked : false;
  if (!coachOn || legal.length === 0 || uiMode === "game_over") {
    aiBestCard = null; aiBestMode = null; aiBestMeta = {};
    render(); 
    return;
  }
  isAiThinking = true;
  render(); 
  try {
    const res = await fetch("/ask_ai", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ state: state, hand: hand, legal: legal })
    });
    const data = await res.json();
    aiBestCard = data.best_card;
    aiBestMode = data.best_mode;
    aiBestMeta = data.best_meta || {};
  } catch (e) {
    console.error("❌ 无法连接 AI:", e);
    aiBestCard = null; aiBestMode = null; aiBestMeta = {};
  }
  isAiThinking = false;
  render();
}

function render(){
  document.getElementById("statePanel").innerHTML = `
    <h2>状态</h2>
    <div>回合: ${state.turn} | 入侵: ${state.inv}/3 | 牌库: ${state.deck.length} | 弃牌: ${state.discard.length}</div>
    <div>资源: 文 ${state.culture}, 军 ${state.military}, 工 ${state.industry} | 地区: ${occupiedRegions()}</div>
    <div>当前得分: <b>${calcScore()}</b></div>
  `;

  // 🏁 游戏结束画面
  if (uiMode === "game_over") {
      const score = calcScore();
      let title = ""; let color = "";
      if (state.lost) { title = "卡利古拉 (暴君 - 罗马沦陷)"; color = "#d32f2f"; }
      else if (score <= 5) { title = "提比略 (平庸之主)"; color = "#757575"; }
      else if (score <= 10) { title = "克劳狄乌斯 (守成之君)"; color = "#1976d2"; }
      else if (score <= 15) { title = "尤利乌斯·凯撒 (传奇大帝)"; color = "#7b1fa2"; }
      else { title = "奥古斯都 (孤城真神)"; color = "#fbc02d"; }

      document.getElementById("actionArea").innerHTML = `
          <div style="text-align:center; padding: 20px; background: ${state.lost ? '#ffebee' : '#fff8e1'}; border-radius: 10px; border: 2px solid ${color};">
              <h1 style="color: ${color}; margin-top: 0;">${state.lost ? '☠️ 罗马沦陷' : '👑 帝国时代结束'}</h1>
              <h2>最终得分: ${score} 分</h2>
              <h3 style="color: #333;">史书评价: ${title}</h3>
              <p>存活回合: ${state.turn} | 建造奇观: ${Object.values(state.mono).filter(v=>v>=2).length} 座</p>
              <button onclick="initGame()" style="padding:15px 30px; font-size:18px; font-weight:bold; background:#4CAF50; color:white; border:none; border-radius:8px; cursor:pointer; margin-top:10px;">再创辉煌 (新开一局)</button>
          </div>
      `;
      document.getElementById("mapArea").innerHTML = "";
      document.getElementById("handArea").innerHTML = "";
      return; 
  }

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
  
  const coachOn = document.getElementById("aiCoachSwitch") ? document.getElementById("aiCoachSwitch").checked : false;
  if (coachOn) {
    const aiBox = document.createElement("div");
    aiBox.style.padding = "10px";
    aiBox.style.marginBottom = "15px";
    aiBox.style.backgroundColor = "#e8f5e9";
    aiBox.style.borderLeft = "5px solid #2e7d32";
    aiBox.style.color = "#1b5e20";
    aiBox.style.fontFamily = "monospace, sans-serif";
    
    if (isAiThinking) {
      aiBox.innerHTML = "<b>📡 正在连接云端 V5 神经网络...</b>";
    } else if (aiBestCard && aiBestMode) {
      const c = cardById(aiBestCard);
      const cModeText = aiBestMode === "top" ? "【上半区】(获取资源)" : "【下半区】(执行动作)";
      
      let extraHint = "";
      if (uiMode === "choose_conquest_city" && c.bottom.type === "Conquest") {
          const targetType = aiBestMeta.target === "Culture" ? "文化地区 (C)" : (aiBestMeta.target === "Industry" ? "工业地区 (I)" : "任意地区");
          extraHint = `<br><span style='color:#d32f2f; font-weight:bold;'>🎯 战略指引：请在上方地图点击占领【${targetType}】</span>`;
      } 
      else if (uiMode === "normal" && aiBestMode === "bottom" && c.bottom.type === "Conquest") {
          const targetType = aiBestMeta.target === "Culture" ? "文化地区" : (aiBestMeta.target === "Industry" ? "工业地区" : "地区");
          extraHint = `<br><span style='color:#0277bd;'>💡 备注：随后请选择占领【${targetType}】</span>`;
      }

      aiBox.innerHTML = `<b>🤖 V5 神明法旨：</b><br>打出：<b>${aiBestCard} - ${c.name}</b><br>选择：<b>${cModeText}</b>${extraHint}`;
    } else {
      aiBox.innerHTML = "<b>🤖 AI 军师已就绪 (当前无动作建议)</b>";
    }
    actionArea.appendChild(aiBox);
  }

  if(uiMode==="normal"){
    legal.forEach((a, i) => {
      const b = document.createElement("button");
      b.className = "action-btn";
      b.textContent = `${i+1}. ${cardById(a.card_id).name} - ${a.mode==="top"?"取资源":a.kind}`;
      b.onclick = () => { pending=a; document.getElementById("btnConfirm").disabled=false; setMsg(`已选: ${b.textContent}`); };
      actionArea.appendChild(b);
    });
  } else if(uiMode==="choose_conquest_city"){
    const hint = document.createElement("p");
    hint.innerHTML = "👆 <b>请在上方地图中点击要占领的城市...</b>";
    hint.style.color = "#666";
    actionArea.appendChild(hint);
  } else if(uiMode==="invasion_choice"){
    actionArea.innerHTML += `<button onclick="pay(0,${pendingInvasion.pay},0);finishInvasionStep()" style="margin-right:10px;">支付军事 ${pendingInvasion.pay} 防御</button><button onclick="uiMode='choose_lose_city';render()">割地求生 (丢弃地区)</button>`;
  }

  document.getElementById("monumentInfo").innerHTML = Object.entries(MONUMENTS).map(([k,v])=>`<div class="card"><b>${v.name}</b> (${state.mono[k]}/2)<br><small>${v.desc}</small></div>`).join("");
  document.getElementById("historyArea").innerHTML = trace.map(t=>`T${t.turn}: ${t.event} (${t.after_score}分)`).join("<br>");
}

function onCityClick(cityId){
  if(uiMode==="choose_conquest_city"){
    if(state.cities[cityId]) return;
    const before = clone(state); 
    pay(0, occupiedRegions(), 0); 
    state.cities[cityId]=true;
    cityId.startsWith("C") ? gainWithTriggers({Culture:1}) : gainWithTriggers({Industry:1});
    hand.forEach(x=>state.discard.push(x));
    const aiSug = (aiBestCard && aiBestMode) ? {card_id: aiBestCard, mode: aiBestMode} : null;
    finishMove(before, `征服 ${cityId}`, aiSug);
  } else if(uiMode==="choose_lose_city"){
    if(!state.cities[cityId]) return;
    state.cities[cityId]=false;
    if(--pendingInvasion.loseLeft <= 0) finishInvasionStep();
    render();
  }
}

function onConfirm(){
  if(!pending) return;
  if(pending.kind==="Conquest"){
    pushUndo(); 
    pendingConquestAction = pending;
    uiMode = "choose_conquest_city";
    render(); 
    return;
  }
  pushUndo();
  const aiSug = (aiBestCard && aiBestMode) ? {card_id: aiBestCard, mode: aiBestMode} : null;
  const before = clone(state);
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
  fetchAIRecommendation();
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
document.getElementById("aiCoachSwitch").onchange = fetchAIRecommendation;
document.getElementById("btnConfirm").onclick = onConfirm;
document.getElementById("btnToggleMonument").onclick = () => document.getElementById("monumentPanel").classList.toggle("hide");
document.getElementById("btnExport").onclick = onExport;

initGame();