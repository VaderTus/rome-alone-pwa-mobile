// ===== 数据（与你当前CSV一致的简化字段） =====
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
    M_WanShenMiao:{type:"FlatGP",v:4},
    M_LuoMaDouShouChang:{type:"FlatGP",v:2,special:"IgnoreInvasions"},
    M_DiGuoGuangChang:{type:"FlatGP",v:2,special:"SenateSwap"},
    M_HaDeLiangLingQin:{type:"PerBuilding",v:1},
    M_KaiXuanMen:{type:"PerRegion",v:1},
    M_TuLaZhenShiChang:{type:"MinResource",v:1},
  };
  
  const INVASIONS = [{pay:2,lose:1},{pay:3,lose:1},{pay:5,lose:2}];
  
  function cardById(id){ return CARDS.find(c=>c.id===id); }
  function clone(x){ return JSON.parse(JSON.stringify(x)); }
  function shuffle(a){ for(let i=a.length-1;i>0;i--){ const j=Math.floor(Math.random()*(i+1)); [a[i],a[j]]=[a[j],a[i]];} return a; }
  
  // ===== 状态 =====
  let state = null;
  let hand = [];
  let legal = [];
  let pending = null;
  let trace = [];
  let undoStack = [];
  let sessionId = null;
  
  function newGame(){
    sessionId = "sess_" + Date.now();
    state = {
      culture:1,military:1,industry:1,max:9,
      occC:0,occI:0,totalC:3,totalI:3,rome:true,
      built:[], mono:{},
      deck:shuffle(CARDS.map(c=>c.id)), discard:[],
      inv:0, lost:false, turn:0
    };
    Object.keys(MONUMENTS).forEach(k=>state.mono[k]=0);
    hand=[]; legal=[]; pending=null; trace=[]; undoStack=[];
    nextTurn();
  }
  
  function occupiedRegions(){
    return (state.rome?1:0) + state.occC + state.occI;
  }
  function senateActive(){ return state.mono["M_DiGuoGuangChang"]>=2; }
  function colosseumActive(){ return state.mono["M_LuoMaDouShouChang"]>=2; }
  
  function addRes(type,amt){
    if(amt<=0) return 0;
    const key = type==="Culture"?"culture":(type==="Military"?"military":"industry");
    const b = state[key];
    state[key] = Math.min(state.max, state[key]+amt);
    return state[key]-b;
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
    let c = g.Culture||0, m = g.Military||0, i = g.Industry||0;
    if(senateActive()){
      let t = c+m; c=0; m=0;
      while(t>0){ if(state.culture<=state.military)c++; else m++; t--; }
    }
    const gc = addRes("Culture",c), gm=addRes("Military",m), gi=addRes("Industry",i);
    if(gc>0 && state.built.includes("B_YuanXingJingJiChang")) addRes("Culture",2);
    if(gm>0 && state.built.includes("B_JunTuanYaoSai")) addRes("Military",2);
    if(gi>0 && state.built.includes("B_DiGuoJinKuang")) addRes("Industry",2);
  }
  
  function drawHand(){
    const n = Math.min(3, state.deck.length);
    hand = [];
    for(let i=0;i<n;i++) hand.push(state.deck.pop());
  }
  
  function computeLegal(){
    legal = [];
    for(const cid of hand){
      const c = cardById(cid);
      legal.push({card_id:cid,mode:"top",kind:"TopResource",meta:{}});
      const b = c.bottom;
      if(b.type==="Conquest"){
        const need = occupiedRegions();
        if(canPay(0,need,0)){
          if(state.occC<state.totalC) legal.push({card_id:cid,mode:"bottom",kind:"Conquest",meta:{target:"Culture"}});
          if(state.occI<state.totalI) legal.push({card_id:cid,mode:"bottom",kind:"Conquest",meta:{target:"Industry"}});
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
  
  function sameAction(a,b){
    return JSON.stringify(a)===JSON.stringify(b);
  }
  
  function applyAction(a){
    const cid = a.card_id;
    const card = cardById(cid);
  
    if(a.mode==="top"){
      gainWithTriggers({Culture:card.top.c, Military:card.top.m, Industry:card.top.i});
      hand.forEach(x=>state.discard.push(x));
      return;
    }
  
    if(a.kind==="Conquest"){
      const need = occupiedRegions();
      pay(0,need,0);
      if(a.meta.target==="Culture"){ state.occC++; gainWithTriggers({Culture:1}); }
      else { state.occI++; gainWithTriggers({Industry:1}); }
      hand.forEach(x=>state.discard.push(x));
      return;
    }
  
    if(a.kind==="Tribute"){
      const amt = occupiedRegions();
      if(a.meta.target==="Culture") gainWithTriggers({Culture:amt});
      else gainWithTriggers({Industry:amt});
      hand.forEach(x=>state.discard.push(x));
      return;
    }
  
    if(a.kind==="Build_Building"){
      const b = card.bottom;
      pay(b.cost.c,b.cost.m,b.cost.i);
      state.built.push(b.ref);
      hand.forEach(x=>{ if(x!==cid) state.discard.push(x); }); // 建筑牌移出循环
      return;
    }
  
    if(a.kind==="Build_Monument"){
      const b = card.bottom;
      pay(b.cost.c,b.cost.m,b.cost.i);
      state.mono[b.ref]=Math.min(2,state.mono[b.ref]+1);
      hand.forEach(x=>state.discard.push(x));
      return;
    }
  }
  
  function loseRegions(n){
    for(let k=0;k<n;k++){
      const nonRome = state.occC+state.occI;
      if(nonRome>0){
        if(state.occC>=state.occI && state.occC>0) state.occC--;
        else if(state.occI>0) state.occI--;
        else if(state.occC>0) state.occC--;
      } else {
        state.rome=false; state.lost=true; return;
      }
    }
  }
  
  function resolveInvasionIfNeeded(){
    if(state.deck.length>0 || state.inv>=3) return;
    const inv = INVASIONS[state.inv];
  
    if(colosseumActive()){
      state.inv++;
      state.deck = shuffle(state.discard);
      state.discard = [];
      return;
    }
  
    if(canPay(0,inv.pay,0)) pay(0,inv.pay,0);
    else loseRegions(inv.lose);
  
    state.inv++;
    state.deck = shuffle(state.discard);
    state.discard = [];
  }
  
  function score(){
    if(state.lost) return 0;
    let total = occupiedRegions();
    for(const bid of state.built){
      const b = BUILDINGS[bid];
      if(b && b.gp) total += b.gp;
    }
    for(const mid of Object.keys(state.mono)){
      if(state.mono[mid]<2) continue;
      const m = MONUMENTS[mid];
      if(m.type==="FlatGP") total += m.v;
      else if(m.type==="PerBuilding") total += m.v * state.built.length;
      else if(m.type==="PerRegion") total += m.v * occupiedRegions();
      else if(m.type==="MinResource") total += m.v * Math.min(state.culture,state.military,state.industry);
    }
    return total;
  }
  
  function stateSnap(){
    return {
      turn:state.turn,culture:state.culture,military:state.military,industry:state.industry,
      occupied_regions:occupiedRegions(),occC:state.occC,occI:state.occI,
      invasions_resolved:state.inv,deck_left:state.deck.length,discard_size:state.discard.length,
      built:[...state.built],mono:clone(state.mono),lost:state.lost
    };
  }
  
  function nextTurn(){
    if(state.lost || state.inv>=3){ render(); return; }
    state.turn++;
    drawHand();
    computeLegal();
    pending=null;
    render();
  }
  
  function msg(text,ok=true){
    const el=document.getElementById("msg");
    el.className = ok ? "msg-ok" : "msg-err";
    el.textContent = text;
  }
  
  function cardBottomText(c){
    const b=c.bottom;
    if(b.type==="Conquest") return "征服（军事=占领地区数，新增1地区并获对应资源）";
    if(b.type==="Tribute") return `征收${b.target}（数量=占领地区数）`;
    if(b.type==="Build_Building") return `建造建筑(消耗 C${b.cost.c}/M${b.cost.m}/I${b.cost.i})`;
    if(b.type==="Build_Monument") return `建造纪念物进度(消耗 C${b.cost.c}/M${b.cost.m}/I${b.cost.i})`;
    return "无";
  }
  
  function render(){
    const s = state;
    const st = document.getElementById("statePanel");
    st.innerHTML = `
      <h2>状态</h2>
      <div>回合: ${s.turn} | 入侵: ${s.inv}/3 | 牌库: ${s.deck.length} | 弃牌: ${s.discard.length}</div>
      <div>资源: 文化 ${s.culture}/9, 军事 ${s.military}/9, 工业 ${s.industry}/9</div>
      <div>地区: 总${occupiedRegions()}（文化区${s.occC}, 工业区${s.occI}, Rome=${s.rome?"在":"失守"}）</div>
      <div>建筑: ${s.built.join(", ") || "无"}</div>
      <div>纪念物进度: ${Object.entries(s.mono).map(([k,v])=>`${k}:${v}/2`).join(" | ")}</div>
      <div><b>当前分数(若终局): ${score()}</b></div>
    `;
  
    const handArea = document.getElementById("handArea");
    handArea.innerHTML = "";
    for(const cid of hand){
      const c=cardById(cid);
      const card=document.createElement("div");
      card.className="card";
      card.innerHTML = `
        <h3>${c.name}</h3>
        <div class="small">${cid}</div>
        <div class="sep"></div>
        <div><b>上半资源：</b>C${c.top.c}/M${c.top.m}/I${c.top.i}</div>
        <div class="sep"></div>
        <div><b>下半动作：</b>${cardBottomText(c)}</div>
      `;
      handArea.appendChild(card);
    }
  
    const actionArea=document.getElementById("actionArea");
    actionArea.innerHTML="";
    legal.forEach((a,idx)=>{
      const b=document.createElement("button");
      b.textContent = `${idx+1}. ${a.card_id} ${a.mode==="top"?"上半":"下半"} ${a.kind} ${JSON.stringify(a.meta)}`;
      b.onclick=()=>{
        pending = a;
        document.getElementById("btnConfirm").disabled = false;
        msg(`已选择: ${b.textContent}`, true);
      };
      actionArea.appendChild(b);
    });
  
    const his=document.getElementById("historyArea");
    his.innerHTML = trace.map((r,i)=>`#${i+1} T${r.turn} ${r.chosen_action.card_id}-${r.chosen_action.kind} -> 分:${r.after_score}`).join("<br>");
  
    if(state.lost || state.inv>=3){
      msg(`对局结束。最终分数: ${score()}，失败=${state.lost?"是":"否"}`, true);
      document.getElementById("btnConfirm").disabled = true;
    }
  }
  
  function confirmAction(){
    if(!pending){ msg("请先选择动作", false); return; }
    const stillLegal = legal.some(x=>sameAction(x,pending));
    if(!stillLegal){ msg("非法动作，请重选", false); return; }
  
    undoStack.push({
      state: clone(state),
      hand: clone(hand),
      legal: clone(legal),
      pending: clone(pending),
      trace: clone(trace),
    });
  
    const before = stateSnap();
    applyAction(pending);
    resolveInvasionIfNeeded();
    const after = stateSnap();
  
    trace.push({
      turn: state.turn,
      hand: clone(hand),
      legal_actions: clone(legal),
      chosen_action: clone(pending),
      before, after,
      after_score: score(),
      timestamp: new Date().toISOString()
    });
  
    nextTurn();
  }
  
  function undo(){
    if(undoStack.length===0){ msg("没有可撤销步骤", false); return; }
    const u = undoStack.pop();
    state = u.state; hand=u.hand; legal=u.legal; pending=u.pending; trace=u.trace;
    render();
    msg("已撤销上一步", true);
  }
  
  function exportLogs(){
    const payload = {
      source: "mobile_pwa",
      app_version: "pwa_v1",
      session_id: sessionId,
      created_at: new Date().toISOString(),
      final_summary: {
        score: score(),
        lost: state.lost,
        turns: state.turn,
        invasions_resolved: state.inv
      },
      records: trace
    };
    const blob = new Blob([JSON.stringify(payload,null,2)], {type:"application/json"});
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `mobile_trace_${sessionId}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
    msg("日志已导出JSON", true);
  }
  
  document.getElementById("btnNew").onclick = ()=>newGame();
  document.getElementById("btnUndo").onclick = ()=>undo();
  document.getElementById("btnConfirm").onclick = ()=>confirmAction();
  document.getElementById("btnExport").onclick = ()=>exportLogs();
  
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => navigator.serviceWorker.register("./sw.js"));
  }
  
  newGame();