/*
 * PropMap AI 매물 추천 패널 UI
 * - 플로팅 버튼 + 슬라이드 패널(데스크톱) / 바텀시트(모바일)
 * - propnet_token 쿠키 기반 인증
 * - 크레딧 뱃지 + 소진 시 결제 안내
 */
(function () {
  "use strict";

  const API = "/api";
  const isInApp = new URLSearchParams(location.search).get("inapp") === "1";
  const isMobile = () => window.innerWidth <= 768;

  let sessionId = null;
  let panelOpen = false;
  let creditRemaining = null;

  /* ===== DOM 생성 ===== */
  function injectHTML() {
    // 플로팅 버튼
    const fab = document.createElement("button");
    fab.id = "aiFab";
    fab.className = "ai-fab";
    fab.innerHTML = `<span class="material-symbols-outlined">auto_awesome</span><span class="ai-fab-badge" id="aiFabBadge"></span>`;
    fab.title = "AI 매물 추천";
    document.body.appendChild(fab);

    // 패널
    const panel = document.createElement("div");
    panel.id = "aiPanel";
    panel.className = "ai-panel";
    panel.innerHTML = `
      <div class="ai-panel-header">
        <div class="ai-panel-title">
          <span class="material-symbols-outlined" style="font-size:20px;color:#3b82f6;">auto_awesome</span>
          AI 매물 추천
          <span class="ai-credit-badge" id="aiCreditBadge"></span>
        </div>
        <button class="ai-panel-close" id="aiPanelClose">&times;</button>
      </div>
      <div class="ai-panel-body" id="aiChat"></div>
      <div class="ai-panel-input">
        <input type="text" id="aiInput" placeholder="어떤 매물을 찾으시나요?" maxlength="500" autocomplete="off">
        <button id="aiSend" class="ai-send-btn"><span class="material-symbols-outlined">send</span></button>
      </div>
      <div class="ai-panel-disclaimer">AI 추천 결과입니다. 최종 결정 전 중개사와 직접 상담하세요.</div>
    `;
    document.body.appendChild(panel);

    // 결제 안내 모달
    const modal = document.createElement("div");
    modal.id = "aiPayModal";
    modal.className = "ai-pay-modal";
    modal.innerHTML = `
      <div class="ai-pay-content">
        <div class="ai-pay-title">무료 체험을 모두 사용하셨어요</div>
        <div class="ai-pay-desc">
          PropNet 요금제에 가입하면 AI 매물 추천을<br>매월 이용할 수 있습니다.
        </div>
        <a href="/billing/" target="${isInApp ? '_self' : '_blank'}" class="ai-pay-btn">요금제 보기</a>
        <button class="ai-pay-close" id="aiPayClose">다음에 할게요</button>
      </div>
    `;
    document.body.appendChild(modal);

    injectStyles();
  }

  function injectStyles() {
    const style = document.createElement("style");
    style.textContent = `
      .ai-fab {
        position:fixed; bottom:${isInApp ? '80px' : '24px'}; right:24px; z-index:900;
        width:56px; height:56px; border-radius:50%; border:none;
        background:linear-gradient(135deg,#3b82f6,#8b5cf6); color:white;
        box-shadow:0 4px 16px rgba(59,130,246,.4); cursor:pointer;
        display:flex; align-items:center; justify-content:center;
        transition:transform .2s,box-shadow .2s;
      }
      .ai-fab:hover { transform:scale(1.08); box-shadow:0 6px 24px rgba(59,130,246,.5); }
      .ai-fab .material-symbols-outlined { font-size:28px; }
      .ai-fab-badge {
        position:absolute; top:-2px; right:-2px; min-width:20px; height:20px;
        border-radius:10px; font-size:11px; font-weight:700; line-height:20px;
        text-align:center; padding:0 5px; display:none;
      }
      .ai-fab-badge.has { display:block; background:#10b981; color:white; }
      .ai-fab-badge.empty { display:block; background:#ef4444; color:white; }

      .ai-panel {
        position:fixed; top:0; right:-440px; width:420px; height:100%; z-index:950;
        background:white; box-shadow:-4px 0 24px rgba(0,0,0,.12);
        display:flex; flex-direction:column; transition:right .3s ease;
      }
      .ai-panel.open { right:0; }
      @media(max-width:768px) {
        .ai-panel {
          top:auto; bottom:0; left:0; right:0!important; width:100%;
          height:80vh; border-radius:16px 16px 0 0;
          transform:translateY(100%); transition:transform .3s ease;
        }
        .ai-panel.open { transform:translateY(0); right:0!important; }
      }

      .ai-panel-header {
        padding:14px 16px; border-bottom:1px solid #e5e7eb;
        display:flex; align-items:center; justify-content:space-between; flex-shrink:0;
      }
      .ai-panel-title { display:flex; align-items:center; gap:6px; font-size:15px; font-weight:700; color:#1e293b; }
      .ai-credit-badge {
        font-size:11px; font-weight:600; padding:2px 8px; border-radius:10px;
        background:#eff6ff; color:#3b82f6; margin-left:4px;
      }
      .ai-panel-close {
        width:32px; height:32px; border:none; background:#f1f5f9;
        border-radius:8px; font-size:20px; color:#64748b; cursor:pointer;
        display:flex; align-items:center; justify-content:center;
      }

      .ai-panel-body {
        flex:1; overflow-y:auto; padding:16px; display:flex; flex-direction:column; gap:12px;
      }
      .ai-bubble { max-width:90%; padding:10px 14px; border-radius:12px; font-size:14px; line-height:1.6; word-break:break-word; }
      .ai-bubble.user { align-self:flex-end; background:#3b82f6; color:white; border-bottom-right-radius:4px; }
      .ai-bubble.assistant { align-self:flex-start; background:#f1f5f9; color:#1e293b; border-bottom-left-radius:4px; }
      .ai-bubble.system { align-self:center; background:#fef3c7; color:#92400e; font-size:13px; text-align:center; }
      .ai-typing { align-self:flex-start; color:#94a3b8; font-size:13px; padding:8px 0; }

      .ai-rec-card {
        background:white; border:1px solid #e5e7eb; border-radius:10px; padding:12px;
        margin-top:4px; cursor:pointer; transition:border-color .15s;
      }
      .ai-rec-card:hover { border-color:#3b82f6; }
      .ai-rec-title { font-size:14px; font-weight:600; color:#1e293b; margin-bottom:4px; }
      .ai-rec-meta { font-size:12px; color:#64748b; line-height:1.5; }
      .ai-rec-reason { font-size:12px; color:#3b82f6; margin-top:6px; font-style:italic; }

      .ai-panel-input {
        padding:12px 16px; border-top:1px solid #e5e7eb;
        display:flex; gap:8px; flex-shrink:0;
      }
      .ai-panel-input input {
        flex:1; padding:10px 14px; border:1px solid #d1d5db; border-radius:10px;
        font-size:14px; outline:none; font-family:inherit;
      }
      .ai-panel-input input:focus { border-color:#3b82f6; }
      .ai-send-btn {
        width:40px; height:40px; border:none; border-radius:10px;
        background:#3b82f6; color:white; cursor:pointer;
        display:flex; align-items:center; justify-content:center;
      }
      .ai-send-btn:disabled { background:#94a3b8; cursor:not-allowed; }

      .ai-panel-disclaimer {
        padding:8px 16px; font-size:11px; color:#94a3b8; text-align:center;
        border-top:1px solid #f1f5f9; flex-shrink:0;
      }

      .ai-pay-modal {
        display:none; position:fixed; top:0; left:0; right:0; bottom:0;
        background:rgba(0,0,0,.5); z-index:1000;
        align-items:center; justify-content:center;
      }
      .ai-pay-modal.active { display:flex; }
      .ai-pay-content {
        background:white; border-radius:16px; padding:32px 24px; max-width:360px;
        width:90%; text-align:center;
      }
      .ai-pay-title { font-size:18px; font-weight:700; color:#1e293b; margin-bottom:12px; }
      .ai-pay-desc { font-size:14px; color:#64748b; line-height:1.6; margin-bottom:24px; }
      .ai-pay-btn {
        display:block; padding:12px; background:#3b82f6; color:white;
        border-radius:10px; text-decoration:none; font-weight:600; font-size:15px;
        margin-bottom:12px;
      }
      .ai-pay-close {
        border:none; background:none; color:#94a3b8; font-size:14px;
        cursor:pointer; padding:8px;
      }

      /* 패널 열릴 때 FAB 숨기기 */
      .ai-fab.hidden { display:none; }
    `;
    document.head.appendChild(style);
  }

  /* ===== 크레딧 상태 ===== */
  async function loadCreditStatus() {
    try {
      const resp = await fetch(API + "/ai/billing/status", { credentials: "include" });
      if (resp.status === 401) { creditRemaining = null; updateBadge(); return; }
      const data = await resp.json();
      creditRemaining = data.is_admin ? Infinity : data.remaining;
      updateBadge();
    } catch (e) {
      creditRemaining = null;
      updateBadge();
    }
  }

  function updateBadge() {
    const fabBadge = document.getElementById("aiFabBadge");
    const creditBadge = document.getElementById("aiCreditBadge");

    if (creditRemaining === null) {
      fabBadge.className = "ai-fab-badge";
      fabBadge.textContent = "";
      if (creditBadge) creditBadge.textContent = "";
    } else if (creditRemaining === Infinity) {
      fabBadge.className = "ai-fab-badge has";
      fabBadge.textContent = "∞";
      if (creditBadge) creditBadge.textContent = "관리자";
    } else if (creditRemaining > 0) {
      fabBadge.className = "ai-fab-badge has";
      fabBadge.textContent = creditRemaining;
      if (creditBadge) creditBadge.textContent = `${creditRemaining}회 남음`;
    } else {
      fabBadge.className = "ai-fab-badge empty";
      fabBadge.textContent = "0";
      if (creditBadge) creditBadge.textContent = "소진";
    }
  }

  /* ===== 패널 열기/닫기 ===== */
  function openPanel() {
    const panel = document.getElementById("aiPanel");
    const fab = document.getElementById("aiFab");
    panel.classList.add("open");
    fab.classList.add("hidden");
    panelOpen = true;
    document.getElementById("aiInput").focus();
    if (!sessionId) startSession();
  }

  function closePanel() {
    const panel = document.getElementById("aiPanel");
    const fab = document.getElementById("aiFab");
    panel.classList.remove("open");
    fab.classList.remove("hidden");
    panelOpen = false;
  }

  /* ===== 세션 관리 ===== */
  async function startSession() {
    try {
      const resp = await fetch(API + "/ai/session", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source: isInApp ? "inapp" : "web" }),
      });
      if (!resp.ok) {
        if (resp.status === 401) {
          appendBubble("system", "로그인 후 이용할 수 있습니다.");
          return;
        }
        appendBubble("system", "세션 생성에 실패했습니다.");
        return;
      }
      const data = await resp.json();
      sessionId = data.session_id;
      appendBubble("assistant", "안녕하세요! 어떤 매물을 찾고 계신가요?\n지역, 가격, 용도 등을 자유롭게 말씀해 주세요.");
    } catch (e) {
      appendBubble("system", "네트워크 오류가 발생했습니다.");
    }
  }

  /* ===== 메시지 전송 ===== */
  async function sendMessage() {
    const input = document.getElementById("aiInput");
    const text = input.value.trim();
    if (!text || !sessionId) return;

    input.value = "";
    appendBubble("user", text);
    setSending(true);

    try {
      const resp = await fetch(API + "/ai/chat", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, text: text }),
      });

      if (resp.status === 402) {
        // 크레딧 소진
        setSending(false);
        creditRemaining = 0;
        updateBadge();
        showPayModal();
        return;
      }

      if (resp.status === 401) {
        setSending(false);
        appendBubble("system", "로그인이 필요합니다.");
        return;
      }

      if (resp.status === 429) {
        // 세션 턴 상한 도달
        setSending(false);
        appendBubble("system", "이 대화의 최대 질문 횟수에 도달했습니다.\n아래 '새 검색' 버튼으로 새 대화를 시작해 주세요.");
        showNewSessionButton();
        document.getElementById("aiInput").disabled = true;
        document.getElementById("aiSend").disabled = true;
        return;
      }

      if (!resp.ok) {
        setSending(false);
        appendBubble("system", "오류가 발생했습니다. 다시 시도해 주세요.");
        return;
      }

      const data = await resp.json();
      setSending(false);

      // 크레딧 갱신
      if (data.credit_after) {
        creditRemaining = data.credit_after.remaining;
        updateBadge();
        if (data.credit_after.was_free) {
          appendBubble("system", "무료 체험 1회를 사용했습니다.");
        }
      }

      // 어시스턴트 응답
      if (data.assistant_text) {
        appendBubble("assistant", data.assistant_text);
      }

      // 추천 결과 카드
      if (data.recommendations && data.recommendations.selections) {
        renderRecommendations(data.recommendations);
      }

    } catch (e) {
      setSending(false);
      appendBubble("system", "네트워크 오류가 발생했습니다.");
    }
  }

  /* ===== UI 헬퍼 ===== */
  function appendBubble(role, text) {
    const chat = document.getElementById("aiChat");
    const div = document.createElement("div");
    div.className = "ai-bubble " + role;
    div.textContent = text;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
  }

  function setSending(on) {
    const btn = document.getElementById("aiSend");
    const input = document.getElementById("aiInput");
    btn.disabled = on;
    input.disabled = on;
    // 타이핑 인디케이터
    let typing = document.getElementById("aiTyping");
    if (on) {
      if (!typing) {
        typing = document.createElement("div");
        typing.id = "aiTyping";
        typing.className = "ai-typing";
        typing.textContent = "AI가 매물을 분석하고 있어요...";
        document.getElementById("aiChat").appendChild(typing);
      }
    } else {
      if (typing) typing.remove();
    }
  }

  function fmtPrice(manwon) {
    if (!manwon) return "";
    const n = parseFloat(manwon);
    if (isNaN(n)) return "";
    if (n >= 10000) return (n / 10000).toFixed(n % 10000 === 0 ? 0 : 1) + "억";
    return n.toLocaleString() + "만";
  }

  function parseRecordId(rid) {
    // AI가 "39:recXXX" 포맷으로 반환 → 순수 record_id와 db_id를 분리
    if (typeof rid === "string" && rid.includes(":")) {
      var parts = rid.split(":");
      return { recordId: parts.slice(1).join(":"), dbId: parseInt(parts[0]) || 0 };
    }
    return { recordId: rid, dbId: 0 };
  }

  function renderRecommendations(recs) {
    const chat = document.getElementById("aiChat");
    const sels = recs.selections || [];

    sels.forEach(function (s) {
      const card = document.createElement("div");
      card.className = "ai-rec-card";

      // record_id 파싱: "39:recXXX" → recordId="recXXX", dbId=39
      var parsed = parseRecordId(s.record_id);
      var recordId = parsed.recordId;
      var dbId = s.db_id || parsed.dbId;

      card.innerHTML = `
        ${s.reason ? `<div class="ai-rec-reason">${escHtml(s.reason)}</div>` : ""}
      `;

      card.addEventListener("click", function () {
        // 1. 상세보기 열기 (기존 propmap detail overlay)
        if (window.fetchPropertyDetail) {
          window.fetchPropertyDetail(recordId, dbId);
        }
        // 2. 지도를 해당 매물 위치로 이동 (상세 API에서 좌표 조회)
        fetch("/propsheet/api/propsheet/property-detail?id=" + encodeURIComponent(recordId) + "&db_id=" + dbId, { credentials: "include" })
          .then(function (r) { return r.json(); })
          .then(function (d) {
            var p = d.property || d;
            if (p.lat && p.lon) {
              var iframe = document.getElementById("mapIframe");
              if (iframe && iframe.contentWindow) {
                iframe.contentWindow.postMessage({ action: "panTo", lat: p.lat, lng: p.lon }, "*");
                iframe.contentWindow.postMessage({ action: "setLevel", level: 4 }, "*");
              }
            }
          })
          .catch(function () { /* 좌표 이동 실패는 무시 */ });
        // 모바일에서는 패널을 닫아서 지도+상세를 보여줌
        if (isMobile()) closePanel();
      });

      chat.appendChild(card);
    });

    if (recs.summary) {
      appendBubble("assistant", recs.summary);
    }

    chat.scrollTop = chat.scrollHeight;
  }

  function escHtml(s) {
    const d = document.createElement("div");
    d.textContent = s || "";
    return d.innerHTML;
  }

  function showNewSessionButton() {
    const chat = document.getElementById("aiChat");
    if (document.getElementById("aiNewSessionBtn")) return;
    const btn = document.createElement("button");
    btn.id = "aiNewSessionBtn";
    btn.textContent = "새 검색 시작";
    btn.style.cssText = "align-self:center;margin:8px 0;padding:10px 24px;border:none;border-radius:10px;background:#3b82f6;color:white;font-size:14px;font-weight:600;cursor:pointer;";
    btn.addEventListener("click", function () {
      resetSession();
    });
    chat.appendChild(btn);
    chat.scrollTop = chat.scrollHeight;
  }

  function resetSession() {
    sessionId = null;
    document.getElementById("aiChat").innerHTML = "";
    document.getElementById("aiInput").disabled = false;
    document.getElementById("aiSend").disabled = false;
    const oldBtn = document.getElementById("aiNewSessionBtn");
    if (oldBtn) oldBtn.remove();
    startSession();
    loadCreditStatus();
  }

  function showPayModal() {
    document.getElementById("aiPayModal").classList.add("active");
  }

  function hidePayModal() {
    document.getElementById("aiPayModal").classList.remove("active");
  }

  /* ===== 초기화 ===== */
  function init() {
    injectHTML();

    // FAB 클릭
    document.getElementById("aiFab").addEventListener("click", function () {
      // 로그인 체크 (auth-ui.js의 전역 함수 활용)
      if (window.PropMapAuth && !window.PropMapAuth.isLoggedIn()) {
        if (window.PropMapAuth.showGate) {
          window.PropMapAuth.showGate("AI 매물 추천은 로그인 후 ���용할 수 있어요.\n로그인하면 AI 추천 1회를 무료로 드립니다.");
        }
        return;
      }
      openPanel();
    });

    // 패널 닫기
    document.getElementById("aiPanelClose").addEventListener("click", closePanel);

    // 전송
    document.getElementById("aiSend").addEventListener("click", sendMessage);
    document.getElementById("aiInput").addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });

    // 결제 모달 닫기
    document.getElementById("aiPayClose").addEventListener("click", hidePayModal);

    // ESC로 패널 닫기
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && panelOpen) closePanel();
    });

    // 크레딧 로드 (로그인 상태일 때만)
    if (window.PropMapAuth && window.PropMapAuth.isLoggedIn()) {
      loadCreditStatus();
    }
    // auth-ui에서 로그인 상태 변경 시 크레딧 갱신
    window.addEventListener("propmap:auth-ready", function () {
      if (window.PropMapAuth && window.PropMapAuth.isLoggedIn()) {
        loadCreditStatus();
      } else {
        creditRemaining = null;
        updateBadge();
      }
    });
  }

  // 외부 접근용
  window.PropMapAI = {
    open: openPanel,
    close: closePanel,
    refreshCredit: loadCreditStatus,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
