// ==========================================
// 📜 1. 独立自然语言数据库 (UI显示专用)
// ==========================================
const CARD_TEXT_DB = {
  "C01": { top: "获得 1文, 1军, 1工", bottom: "【建雕塑】耗费 1文 2工\n(结束+2分)" },
  "C02": { top: "获得 1文, 1军, 1工", bottom: "【建引水道】耗费 1文 2工\n(结束+2分)" },
  "C03": { top: "获得 1文, 2军", bottom: "【建要塞】耗费 1军 2工\n(军事引擎)" },
  "C04": { top: "获得 3工", bottom: "【建金矿】耗费 3工\n(工业引擎)" },
  "C05": { top: "获得 2文, 1工", bottom: "【建竞技场】耗费 1文 2工\n(文化引擎)" },
  "C06": { top: "获得 2工", bottom: "【征服】支付=[地区数]军事\n占领1个地区" },
  "C07": { top: "获得 1文, 1工", bottom: "【征服】支付=[地区数]军事\n占领1个地区" },
  "C08": { top: "获得 2工", bottom: "【征收文化】\n获得=[地区数]的文化" },
  "C09": { top: "获得 1文, 1工", bottom: "【征收工业】\n获得=[地区数]的工业" },
  "C10": { top: "获得 1文, 1工", bottom: "【万神庙1】耗费 3文\n(建成+4分)" },
  "C11": { top: "获得 2文", bottom: "【万神庙2】耗费 3文 1工\n(建成+4分)" },
  "C12": { top: "获得 1军, 1工", bottom: "【斗兽场1】耗费 3文\n(建成免疫入侵)" },
  "C13": { top: "获得 2军", bottom: "【斗兽场2】耗费 1军 2工\n(建成免疫入侵)" },
  "C14": { top: "获得 1文, 1工", bottom: "【帝国广场1】耗费 3文\n(文军互换)" },
  "C15": { top: "获得 2文", bottom: "【帝国广场2】耗费 3工\n(文军互换)" },
  "C16": { top: "获得 2工", bottom: "【陵寝1】耗费 1军 2工\n(按建筑数得分)" },
  "C17": { top: "获得 1军, 1工", bottom: "【陵寝2】耗费 3文\n(按建筑数得分)" },
  "C18": { top: "获得 1文, 1军", bottom: "【凯旋门1】耗费 3文\n(按地区数得分)" },
  "C19": { top: "获得 2军", bottom: "【凯旋门2】耗费 1军 2工\n(按地区数得分)" },
  "C20": { top: "获得 2工", bottom: "【市场1】耗费 1文 2工\n(按木桶短板得分)" },
  "C21": { top: "获得 1军, 1工", bottom: "【市场2】耗费 3文\n(按木桶短板得分)" }
};

// ==========================================
// 🎨 2. 动态样式
// ==========================================
const uiStyles = document.createElement('style');
uiStyles.innerHTML = `
  /* 屏蔽原本 HTML 里的旧确认按钮 */
  #btnConfirm { display: none !important; }

  .modal-overlay { display: none; position: fixed; top:0; left:0; right:0; bottom:0; background: rgba(0,0,0,0.7); z-index: 1000; justify-content: center; align-items: center; }
  .modal-content { background: white; padding: 20px; border-radius: 12px; width: 90%; max-width: 400px; }
  .discard-item { padding: 8px; border-bottom: 1px solid #eee; font-size: 14px; }
  
  .hand-container { display: flex; flex-direction: column; gap: 12px; padding: 5px 0; margin-bottom: 80px; }
  .poker-card { border: 2px solid #ccc; border-radius: 8px; background: #fff; overflow: hidden; display: flex; flex-direction: column; }
  .card-header { background: #333; color: white; padding: 6px; text-align: center; font-weight: bold; font-size: 14px; }
  .card-half { padding: 12px; cursor: pointer; text-align: center; border-bottom: 1px dashed #ddd; transition: 0.2s; white-space: pre-line; font-size: 14px; }
  .card-half.disabled { opacity: 0.3; cursor: not-allowed; background: #f5f5f5; }
  .card-half.selected { background: #e3f2fd; border: 2px solid #1976d2; font-weight: bold; box-shadow: inset 0 0 8px rgba(25,118,210,0.2); }
  
  .fab-confirm { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); width: 90%; max-width: 400px; padding: 15px; font-size: 18px; font-weight: bold; background: #4caf50; color: white; border: none; border-radius: 8px; cursor: pointer; box-shadow: 0 4px 15px rgba(0,0,0,0.3); z-index: 100; }
  .fab-confirm:active { transform: scale(0.95); background: #388e3c; }
`;
document.head.appendChild(uiStyles);

// ==========================================
// ⚙️ 3. 底层物理数据 (🚀已恢复丢失的 top 资源属性！)
// ==========================================
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

const MONUMENTS = { M_WanShenMiao:{name:"万神庙",v:4}, M_LuoMaDouShouChang:{name:"斗兽场",v:2}, M_DiGuoGuangChang:{name:"帝国广场",v:2}, M_HaDeLiangLingQin:{name:"哈德良陵寝",v:1}, M_KaiXuanMen:{name:"凯旋门",v:1}, M_TuLaZhenShiChang:{name:"图拉真市场",v:1} };
const BUILDINGS = { B_KaiXuanDiaoSu:{n:"凯旋雕塑"}, B_DiGuoYinShuiDao:{n:"引水道"}, B_JunTuanYaoSai:{n:"军团要塞"}, B_DiGuoJinKuang:{n:"帝国金矿"}, B_YuanXingJingJiChang:{n:"竞技场"} };

const CITY_IDS = ["C1","C2","C3","I1","I2","I3"];
const INVASIONS = [{pay:2,lose:1},{pay:3,lose:1},{pay:5,lose:2}];

function cardById(id){ return CARDS.find(c=>c.id===id); }
function clone(x){ return JSON.parse(JSON.stringify(x)); }
function shuffle(a){ for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];} return a; }

let state, hand, legal, pending, trace, undoStack;
let uiMode = "normal"; 
let pendingConquestAction = null, pendingInvasion = null;

// AI 状态
let aiBestCard = null, aiBestMode = null, aiBestMeta = {}, isAiThinking = false; 

function initGame(){
  state = {
    culture:1, military:1, industry:1, rome:true,
    cities:{C1:false,C2:false,C3:false,I1:false,I2:false,I3:false},
    built:[], mono:Object.fromEntries(Object.keys(MONUMENTS).map(k=>[k,0])),
    deck:shuffle(CARDS.map(c=>c.id)), discard:[], inv:0, lost:false, turn:0
  };
  hand=[]; legal=[]; pending=null; trace=[]; undoStack=[];
  nextTurn();
}

function nextTurn(){
  if(state.lost || state.inv >= 3){ uiMode = "game_over"; render(); return; }
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
      if (!state.cities["C1"]||!state.cities["C2"]||!state.cities["C3"]||!state.cities["I1"]||!state.cities["I2"]||!state.cities["I3"]) 
        legal.push({card_id:cid, mode:"bottom", kind:"Conquest", meta:{}});
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
    const b=state[k]; state[k]=Math.min(9,state[k]+amt); return state[k]-b; 
}

// 完美防溢出分配
function gainWithTriggers(g){
  let c = g.Culture || 0, m = g.Military || 0, i = g.Industry || 0;
  if(senateActive()){
    let total_cm = c + m;
    if((c+m) > 0 && state.built.includes("B_YuanXingJingJiChang")) total_cm += 2;
    if((c+m) > 0 && state.built.includes("B_JunTuanYaoSai")) total_cm += 2;
    let fc = 0; let fm = 0;
    for(let s=0; s < total_cm; s++){
        if (state.culture + fc >= 9 && state.military + fm < 9) fm++; 
        else if (state.military + fm >= 9 && state.culture + fc < 9) fc++; 
        else if (state.culture + fc <= state.military + fm) fc++; 
        else fm++;
    }
    c = fc; m = fm;
  } else {
    if(c > 0 && state.built.includes("B_YuanXingJingJiChang")) c += 2;
    if(m > 0 && state.built.includes("B_JunTuanYaoSai")) m += 2;
  }
  if(i > 0 && state.built.includes("B_DiGuoJinKuang")) i += 2;
  addRes("Culture", c); addRes("Military", m); addRes("Industry", i);
}

// 📡 呼叫 AI 军师
async function fetchAIRecommendation() {
  const coachOn = document.getElementById("aiCoachSwitch") ? document.getElementById("aiCoachSwitch").checked : false;
  if (!coachOn || legal.length === 0 || uiMode === "game_over") {
    aiBestCard = null; aiBestMode = null; aiBestMeta = {}; render(); return;
  }
  
  isAiThinking = true; render(); 
  
  let apiUrl = "/ask_ai";
  if (window.location.protocol === "file:" || window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost") {
      apiUrl = "http://127.0.0.1:8000/ask_ai";
  }

  try {
    const res = await fetch(apiUrl, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ state: state, hand: hand, legal: legal }) });
    const data = await res.json();
    aiBestCard = data.best_card; aiBestMode = data.best_mode; aiBestMeta = data.best_meta || {};
  } catch (e) { aiBestCard = null; aiBestMode = null; aiBestMeta = {}; }
  isAiThinking = false; render();
}

function getLegalAction(cardId, mode) {
    return legal.find(a => a.card_id === cardId && a.mode === mode);
}
function onCardHalfClick(cardId, mode) {
    if (uiMode !== "normal") return;
    const act = getLegalAction(cardId, mode);
    if (act) { pending = act; render(); }
}

function render(){
  document.getElementById("statePanel").innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <h2 style="margin:0;">📊 帝国中枢</h2>
        <button onclick="document.getElementById('discardModal').style.display='flex'" style="padding:5px 10px; background:#607d8b; color:white; border:none; border-radius:4px; cursor:pointer;">
            🔍 弃牌堆 (${state.discard.length})
        </button>
    </div>
    <div style="font-size:14px; margin:10px 0; color:#555;">
      回合: <b>${state.turn}/21</b> | 防守: <b>${state.inv}/3</b> | 牌库: <b>${state.deck.length}</b>
    </div>
    <div style="font-size:18px; font-weight:bold; background:#f5f5f5; padding:10px; border-radius:8px;">
      资源: <span style="color:#d32f2f">文 ${state.culture}</span> | <span style="color:#1976d2">军 ${state.military}</span> | <span style="color:#f57c00">工 ${state.industry}</span>
      <br><span style="color:#333; font-size:14px;">已占地区: ${occupiedRegions()} | 预估得分: ${calcScore()}</span>
    </div>
  `;

  if (uiMode === "game_over") {
      const score = calcScore();
      document.getElementById("actionArea").innerHTML = `
          <div style="text-align:center; padding:20px; background:#fff8e1; border-radius:10px;">
              <h1>${state.lost ? '☠️ 罗马沦陷' : '👑 帝国时代结束'}</h1>
              <h2>最终得分: ${score} 分</h2>
              <button onclick="initGame()" style="padding:15px 30px; font-size:18px; background:#4CAF50; color:white; border:none; border-radius:8px; cursor:pointer; width:100%;">再来一局</button>
          </div>
      `;
      document.getElementById("handArea").innerHTML = ""; document.getElementById("mapArea").innerHTML = ""; return; 
  }

  document.getElementById("mapArea").innerHTML = `
    <div class="map-wrap">
      <div class="map-col">${CITY_IDS.slice(0,3).map(id=>`<button class="city culture ${state.cities[id]?'occupied':''} ${(uiMode==='choose_conquest_city'&&!state.cities[id])||(uiMode==='choose_lose_city'&&state.cities[id])?'pickable':''}" onclick="onCityClick('${id}')">${id}${state.cities[id]?'✅':''}</button>`).join("")}</div>
      <div class="rome">ROME ${state.rome?'✅':'❌'}</div>
      <div class="map-col">${CITY_IDS.slice(3).map(id=>`<button class="city industry ${state.cities[id]?'occupied':''} ${(uiMode==='choose_conquest_city'&&!state.cities[id])||(uiMode==='choose_lose_city'&&state.cities[id])?'pickable':''}" onclick="onCityClick('${id}')">${id}${state.cities[id]?'✅':''}</button>`).join("")}</div>
    </div>
  `;

  // 🏛️ 基建与奇观面板
  const builtList = state.built.map(b => `<span>✅ ${BUILDINGS[b].n}</span>`).join(" | ");
  const monoList = Object.entries(MONUMENTS).map(([k,v])=> `<span style="color:${state.mono[k]>=2?'#2e7d32':'#757575'};">${state.mono[k]>=2?'✅':'🚧'}${v.name}(${state.mono[k]}/2)</span>`).join("<br>");
  document.getElementById("monumentInfo").innerHTML = `
    <div style="background:#f0f0f0; padding:10px; border-radius:8px; font-size:13px; margin-top:10px;">
      <b>🏛️ 建筑:</b> ${builtList || "无"}<br>
      <b>🏺 奇观:</b><br> ${monoList}
    </div>
  `;

  const actionArea = document.getElementById("actionArea");
  actionArea.innerHTML = "";
  
  // 🧱 AI 军师纯文本框
  const coachOn = document.getElementById("aiCoachSwitch") ? document.getElementById("aiCoachSwitch").checked : false;
  if (coachOn && uiMode==="normal") {
    const aiBox = document.createElement("div");
    aiBox.style.cssText = "padding:12px; margin-bottom:15px; background:#e8f5e9; border-left:6px solid #2e7d32; color:#1b5e20;";
    if (isAiThinking) {
      aiBox.innerHTML = "<b>📡 正在连接神明推演...</b>";
    } else if (aiBestCard && aiBestMode) {
      const cName = cardById(aiBestCard).name;
      const modeStr = aiBestMode === "top" ? "【上半区】(拿资源)" : "【下半区】(执行动作)";
      let hint = "";
      if (aiBestMode === "bottom" && cardById(aiBestCard).bottom.type === "Conquest") {
          const tgt = aiBestMeta.target === "Culture" ? "文化区(C)" : (aiBestMeta.target === "Industry" ? "工业区(I)" : "任意区");
          hint = `<br><span style='color:#d32f2f; font-weight:bold;'>🎯 战略目标：随后占领 ${tgt}</span>`;
      }
      aiBox.innerHTML = `<b>🤖 神明法旨：</b><br>打出：<b>${aiBestCard} ${cName}</b><br>选择：<b>${modeStr}</b>${hint}`;
    } else {
      aiBox.innerHTML = "<b>🤖 AI 待命 (无可用动作)</b>";
    }
    actionArea.appendChild(aiBox);
  }

  // 🃏 垂直列表卡牌交互
  if(uiMode==="normal"){
    let cardsHtml = `<div class="hand-container">`;
    hand.forEach(cid => {
      const dbText = CARD_TEXT_DB[cid];
      const isTopLegal = getLegalAction(cid, "top");
      const isBotLegal = getLegalAction(cid, "bottom");
      const isTopPending = pending && pending.card_id === cid && pending.mode === "top";
      const isBotPending = pending && pending.card_id === cid && pending.mode === "bottom";

      cardsHtml += `
        <div class="poker-card">
            <div class="card-header">${cid} - ${cardById(cid).name}</div>
            <div class="card-half ${isTopLegal ? '' : 'disabled'} ${isTopPending ? 'selected' : ''}" 
                 onclick="onCardHalfClick('${cid}', 'top')">
                ⬆️ ${dbText.top}
            </div>
            <div class="card-half ${isBotLegal ? '' : 'disabled'} ${isBotPending ? 'selected' : ''}" 
                 onclick="onCardHalfClick('${cid}', 'bottom')">
                ⬇️ ${dbText.bottom}
            </div>
        </div>
      `;
    });
    cardsHtml += `</div>`;
    document.getElementById("handArea").innerHTML = cardsHtml;

    // 确认悬浮按钮
    if (pending) {
        let confirmBtn = document.getElementById("globalConfirmBtn");
        if (!confirmBtn) {
            confirmBtn = document.createElement("button");
            confirmBtn.id = "globalConfirmBtn";
            confirmBtn.className = "fab-confirm";
            document.body.appendChild(confirmBtn);
        }
        confirmBtn.style.display = "block";
        confirmBtn.innerHTML = `✅ 确认执行 (${pending.card_id})`;
        confirmBtn.onclick = onConfirm;
    } else {
        const confirmBtn = document.getElementById("globalConfirmBtn");
        if(confirmBtn) confirmBtn.style.display = "none";
    }

  } else if(uiMode==="choose_conquest_city"){
    document.getElementById("handArea").innerHTML = "";
    const btn = document.getElementById("globalConfirmBtn"); if(btn) btn.style.display="none";
    let aiHint = (aiBestMeta && aiBestMeta.target) ? `<br><span style="color:red;">🤖 提示：请点【${aiBestMeta.target}】</span>` : "";
    actionArea.innerHTML = `<h3 style="color:#d32f2f; text-align:center;">⚔️ 征服模式：请在上方点击占领的城市${aiHint}</h3>`;
  } else if(uiMode==="invasion_choice"){
    document.getElementById("handArea").innerHTML = "";
    actionArea.innerHTML = `
        <div style="text-align:center; padding:15px; background:#ffebee; border-radius:8px;">
            <h3 style="color:#d32f2f; margin-top:0;">🔥 蛮族入侵！</h3>
            <button onclick="pay(0,${pendingInvasion.pay},0);finishInvasionStep()" style="width:100%; padding:15px; margin-bottom:10px; background:#d32f2f; color:white; border:none; border-radius:5px; font-size:16px;">🛡️ 支付 ${pendingInvasion.pay} 军事御敌</button>
            <button onclick="uiMode='choose_lose_city';render()" style="width:100%; padding:15px; background:#424242; color:white; border:none; border-radius:5px; font-size:16px;">🩸 割地求生</button>
        </div>
    `;
  }

  // 模态框
  let modal = document.getElementById('discardModal');
  if(!modal) {
      modal = document.createElement('div');
      modal.id = 'discardModal';
      modal.className = 'modal-overlay';
      modal.onclick = (e) => { if(e.target === modal) modal.style.display = 'none'; };
      document.body.appendChild(modal);
  }
  const discardHtml = state.discard.map(cid => `<div class="discard-item"><b>${cid}</b> ${cardById(cid).name}</div>`).join("");
  modal.innerHTML = `
      <div class="modal-content" onclick="event.stopPropagation()">
          <h2 style="margin-top:0; border-bottom:2px solid #eee; padding-bottom:10px;">🗑️ 弃牌堆 (${state.discard.length})</h2>
          <div style="max-height: 50vh; overflow-y: auto;">${discardHtml || "<i>空</i>"}</div>
          <button onclick="document.getElementById('discardModal').style.display='none'" style="margin-top:15px; width:100%; padding:12px; background:#2196f3; color:white; border:none; border-radius:6px;">关闭</button>
      </div>
  `;
}

function onCityClick(cityId){
  if(uiMode==="choose_conquest_city"){
    if(state.cities[cityId]) return;
    const before = clone(state); 
    pay(0, occupiedRegions(), 0); 
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
  if(pending.kind==="Conquest"){
    pushUndo(); 
    pendingConquestAction = pending;
    uiMode = "choose_conquest_city";
    render(); 
    return;
  }
  pushUndo();
  const before = clone(state);
  const card = cardById(pending.card_id);

  if(pending.mode==="top"){
    gainWithTriggers({Culture:card.top.c, Military:card.top.m, Industry:card.top.i});
    hand.forEach(x=>state.discard.push(x));
    finishMove(before, "上半资源");
  } else if(pending.kind==="Tribute"){
    const amt = occupiedRegions();
    pending.meta.target==="Culture" ? gainWithTriggers({Culture:amt}) : gainWithTriggers({Industry:amt});
    hand.forEach(x=>state.discard.push(x));
    finishMove(before, "征收");
  } else if(pending.kind==="Build_Building"){
    pay(card.bottom.cost.c, card.bottom.cost.m, card.bottom.cost.i);
    state.built.push(pending.meta.building_id);
    hand.forEach(x=>{ if(x!==pending.card_id) state.discard.push(x); });
    finishMove(before, "建筑");
  } else if(pending.kind==="Build_Monument"){
    pay(card.bottom.cost.c, card.bottom.cost.m, card.bottom.cost.i);
    state.mono[pending.meta.monument_id]++;
    hand.forEach(x=>state.discard.push(x));
    finishMove(before, "纪念物");
  }
}

function pushUndo(){ undoStack.push({ state:clone(state), hand:clone(hand), legal:clone(legal), uiMode, pendingConquestAction:clone(pendingConquestAction), pendingInvasion:clone(pendingInvasion) }); }
function onUndo(){ if(undoStack.length===0) return; const u = undoStack.pop(); state=u.state; hand=u.hand; legal=u.legal; uiMode=u.uiMode; pendingConquestAction=u.pendingConquestAction; pendingInvasion=u.pendingInvasion; pending=null; fetchAIRecommendation(); }
function finishMove(){ pending=null; if(!checkInvasion()) nextTurn(); }
function checkInvasion(){
  if(state.deck.length>0 || state.inv>=3) return false;
  if(colosseumActive()){ state.inv++; state.deck=shuffle(state.discard); state.discard=[]; return false; }
  const inv = INVASIONS[state.inv];
  if(canPay(0, inv.pay, 0)) { uiMode="invasion_choice"; pendingInvasion={pay:inv.pay, loseLeft:inv.lose}; render(); return true; }
  else { uiMode="choose_lose_city"; pendingInvasion={loseLeft:inv.lose}; render(); return true; }
}
function finishInvasionStep(){ state.inv++; state.deck=shuffle(state.discard); state.discard=[]; uiMode="normal"; nextTurn(); }
function calcScore(){ if(state.lost) return 0; let s = occupiedRegions(); state.built.forEach(bid => { if(BUILDINGS[bid]&&BUILDINGS[bid].gp) s += BUILDINGS[bid].gp; }); Object.entries(state.mono).forEach(([mid,p])=>{ if(p>=2){ const m=MONUMENTS[mid]; if(m.name.includes("4分") || m.name.includes("互换") || m.name.includes("免疫")) s += (m.v || 2); else if(m.name.includes("每建筑")) s+=state.built.length; else if(m.name.includes("每地区")) s+=occupiedRegions(); else if(m.name.includes("木桶")) s+=Math.min(state.culture,state.military,state.industry); } }); return s; }

// --- 移除自动上传的残留代码 ---
function onExport(){
  const payload = { source: "mobile_pwa", session_id: sessionId, final_summary: { score: calcScore(), lost: state.lost }, records: trace };
  const blob = new Blob([JSON.stringify(payload,null,2)], {type:"application/json"});
  const a=document.createElement("a"); a.href=URL.createObjectURL(blob); a.download=`trace_${sessionId}.json`; a.click();
}

document.getElementById("btnNew").onclick = initGame;
document.getElementById("btnUndo").onclick = onUndo;
document.getElementById("aiCoachSwitch").onchange = fetchAIRecommendation;
document.getElementById("btnExport").onclick = onExport; 

initGame();