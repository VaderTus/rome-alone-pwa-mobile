// ===== Supabase 上传器（Phase 1） =====
// TODO: 替换为你的 Supabase 项目配置
const SUPABASE_URL = "https://nrwfiocjkwqmfthdydeu.supabase.co";
const SUPABASE_ANON_KEY = "sb_publishable_Ta2S-07WvkElnhChbmcvlw_ywJTmhV5";
const TABLE_NAME = "rome_highscores";

const QUEUE_KEY = "rome_upload_queue_v1";
const AUTO_UPLOAD_KEY = "rome_auto_upload_v1";        // "1" or "0"
const SCORE_THRESHOLD_KEY = "rome_upload_min_score_v1"; // int

function getQueue() {
  try { return JSON.parse(localStorage.getItem(QUEUE_KEY) || "[]"); }
  catch { return []; }
}
function setQueue(q) {
  localStorage.setItem(QUEUE_KEY, JSON.stringify(q));
}
function getAutoUploadEnabled() {
  return localStorage.getItem(AUTO_UPLOAD_KEY) !== "0";
}
function setAutoUploadEnabled(v) {
  localStorage.setItem(AUTO_UPLOAD_KEY, v ? "1" : "0");
}
function getScoreThreshold() {
  const v = parseInt(localStorage.getItem(SCORE_THRESHOLD_KEY) || "14", 10);
  return Number.isFinite(v) ? v : 14;
}
function setScoreThreshold(v) {
  localStorage.setItem(SCORE_THRESHOLD_KEY, String(v));
}

async function uploadOne(payload) {
  const row = {
    session_id: payload.session_id,
    final_score: payload.final_summary.score,
    lost: payload.final_summary.lost,
    turns: payload.final_summary.turns,
    source: payload.source || "mobile_pwa",
    app_version: payload.app_version || "pwa_v2_map_upload",
    payload: payload
  };

  const res = await fetch(`${SUPABASE_URL}/rest/v1/${TABLE_NAME}`, {
    method: "POST",
    headers: {
      "apikey": SUPABASE_ANON_KEY,
      "Authorization": `Bearer ${SUPABASE_ANON_KEY}`,
      "Content-Type": "application/json",
      "Prefer": "return=minimal"
    },
    body: JSON.stringify(row)
  });

  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`${res.status} ${txt}`);
  }
}

async function flushQueue(updateStatusCb = null) {
  if (!navigator.onLine) {
    if (updateStatusCb) updateStatusCb("离线状态，队列待上传");
    return;
  }

  const q = getQueue();
  if (!q.length) {
    if (updateStatusCb) updateStatusCb("队列为空");
    return;
  }

  let ok = 0;
  const remain = [];
  for (const item of q) {
    try {
      await uploadOne(item);
      ok += 1;
    } catch {
      remain.push(item);
    }
  }
  setQueue(remain);

  if (updateStatusCb) updateStatusCb(`上传完成：成功${ok}，剩余${remain.length}`);
}

function enqueueIfQualified(payload, updateStatusCb = null) {
  if (!payload || !payload.final_summary) return;
  const threshold = getScoreThreshold();

  if (payload.final_summary.score < threshold) {
    if (updateStatusCb) updateStatusCb(`分数<${threshold}，未入队`);
    return;
  }

  const q = getQueue();
  q.push(payload);
  setQueue(q);

  if (updateStatusCb) updateStatusCb(`已入队，当前${q.length}条`);
}

window.RomeUploader = {
  getQueue,
  setQueue,
  flushQueue,
  enqueueIfQualified,
  getAutoUploadEnabled,
  setAutoUploadEnabled,
  getScoreThreshold,
  setScoreThreshold,
};

window.addEventListener("online", () => {
  window.RomeUploader.flushQueue();
});