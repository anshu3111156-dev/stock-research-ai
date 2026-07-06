/* ═══════════════════════════════════════════════════════════════════
   StockAI Chatbot Widget
   - Floating bubble, site-wide
   - Reads stock context from main app when on analysis page
   - Full conversation history sent each turn (Groq stateless)
═══════════════════════════════════════════════════════════════════ */

const Chat = (() => {
  // ── DOM refs ────────────────────────────────────────────────────────
  const bubble    = document.getElementById("chatBubble");
  const panel     = document.getElementById("chatPanel");
  const chatIcon  = document.getElementById("chatIcon");
  const closeIcon = document.getElementById("closeIcon");
  const unread    = document.getElementById("chatUnread");
  const msgArea   = document.getElementById("chatMessages");
  const input     = document.getElementById("chatInput");
  const sendBtn   = document.getElementById("chatSend");
  const typing    = document.getElementById("chatTyping");
  const clearBtn  = document.getElementById("chatClear");
  const subtitle  = document.getElementById("chatSubtitle");
  const suggBox   = document.getElementById("chatSuggestions");

  // ── State ────────────────────────────────────────────────────────────
  let isOpen      = false;
  let isLoading   = false;
  let history     = [];   // [{role:"user"|"assistant", content:"..."}]
  let stockCtx    = {};   // populated from main app state

  // ── Toggle panel ─────────────────────────────────────────────────────
  function toggle() {
    isOpen = !isOpen;
    panel.classList.toggle("open", isOpen);
    chatIcon.style.display  = isOpen ? "none" : "block";
    closeIcon.style.display = isOpen ? "block" : "none";
    unread.style.display    = "none";
    if (isOpen) {
      refreshContext();
      input.focus();
      scrollToBottom();
    }
  }

  bubble.addEventListener("click", toggle);

  // Close panel if user clicks outside
  document.addEventListener("click", e => {
    if (isOpen && !panel.contains(e.target) && !bubble.contains(e.target)) toggle();
  });

  // ── Context from main app ─────────────────────────────────────────────
  // Called every time panel opens so it picks up freshly analysed stock.
  function refreshContext() {
    // `state` is defined in app.js (same global scope)
    if (typeof state !== "undefined" && state.ticker && window._lastBrief) {
      const brief = window._lastBrief;
      stockCtx = {
        ticker:       state.ticker,
        company_name: brief.company_name || state.companyName,
        sector:       brief.sector,
        key_metrics:  brief.key_metrics || {},
        analyst_summary: brief.analyst_summary,
        risk_flags:   brief.risk_flags || [],
        traffic_light: brief.traffic_light,
        traffic_light_reason: brief.traffic_light_reason,
      };
      subtitle.textContent = `Analysing: ${stockCtx.company_name || state.ticker}`;

      // Show/update context pill
      let pill = document.getElementById("chatCtxPill");
      if (!pill) {
        pill = document.createElement("div");
        pill.id = "chatCtxPill";
        pill.className = "chat-context-pill";
        panel.insertBefore(pill, document.querySelector(".chat-input-row"));
      }
      pill.textContent = `📊 Context: ${stockCtx.company_name || state.ticker} · ${stockCtx.sector || ""}`;
    } else {
      stockCtx = {};
      subtitle.textContent = "General finance & investing";
      const pill = document.getElementById("chatCtxPill");
      if (pill) pill.remove();
    }
  }

  // ── Render a message ──────────────────────────────────────────────────
  function appendMsg(role, text, withSuggestions = false) {
    const wrap = document.createElement("div");
    wrap.className = `chat-msg ${role === "user" ? "user" : "bot"}`;

    const bbl = document.createElement("div");
    bbl.className = "chat-bubble-msg";
    bbl.innerHTML = formatText(text);

    if (withSuggestions && suggBox) {
      bbl.appendChild(suggBox);
    }

    wrap.appendChild(bbl);
    msgArea.appendChild(wrap);
    scrollToBottom();
    return bbl;
  }

  // Convert basic markdown-ish to HTML (bold, bullets, newlines)
  function formatText(t) {
    return t
      .replace(/\*\*(.*?)\*\*/g, "<b>$1</b>")
      .replace(/\*(.*?)\*/g, "<i>$1</i>")
      .replace(/^[-•] (.+)$/gm, "<li>$1</li>")
      .replace(/(<li>.*<\/li>)/s, "<ul>$1</ul>")
      .replace(/\n/g, "<br>");
  }

  function scrollToBottom() {
    msgArea.scrollTop = msgArea.scrollHeight;
  }

  // ── Send message ─────────────────────────────────────────────────────
  async function send(text) {
    text = text.trim();
    if (!text || isLoading) return;

    // Hide suggestions after first user message
    if (suggBox) suggBox.style.display = "none";

    appendMsg("user", text);
    history.push({ role: "user", content: text });
    input.value   = "";
    isLoading     = true;
    sendBtn.disabled = true;
    typing.style.display = "flex";
    scrollToBottom();

    try {
      const res  = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: history,
          context:  stockCtx,
          level:    (typeof state !== "undefined" ? state.level : null) || "💼 Intermediate",
        }),
      });
      const data = await res.json();
      const reply = data.reply || "Sorry, something went wrong. Please try again.";

      typing.style.display = "none";
      appendMsg("bot", reply);
      history.push({ role: "assistant", content: reply });

    } catch (e) {
      typing.style.display = "none";
      appendMsg("bot", "⚠️ Network error. Please check your connection and try again.");
    }

    isLoading        = false;
    sendBtn.disabled = false;
    input.focus();
  }

  // ── Event listeners ───────────────────────────────────────────────────
  sendBtn.addEventListener("click", () => send(input.value));
  input.addEventListener("keydown", e => { if (e.key === "Enter") send(input.value); });

  // Quick suggestion chips
  document.querySelectorAll(".chat-sugg").forEach(btn => {
    btn.addEventListener("click", () => {
      if (!isOpen) toggle();
      send(btn.dataset.q);
    });
  });

  // Clear chat
  clearBtn.addEventListener("click", () => {
    history = [];
    msgArea.innerHTML = "";
    // Re-add welcome message
    const wrap = document.createElement("div");
    wrap.className = "chat-msg bot";
    const bbl = document.createElement("div");
    bbl.className = "chat-bubble-msg";
    bbl.innerHTML = "👋 Chat cleared! Ask me anything about investing or the stock you're analysing.";
    wrap.appendChild(bbl);
    msgArea.appendChild(wrap);
  });

  // ── Unread badge ──────────────────────────────────────────────────────
  // Show unread dot when panel is closed and analysis completes
  function notifyReady(companyName) {
    if (!isOpen) {
      unread.style.display = "flex";
      // Optionally pulse the bubble
      bubble.style.animation = "none";
      setTimeout(() => bubble.style.animation = "", 10);
    }
  }

  // Expose so app.js can call Chat.notifyReady() after analysis loads
  return { notifyReady, refreshContext };
})();

// ── Hook into app.js analysis flow ───────────────────────────────────────
// After renderAnalysis() runs, store the brief globally and notify chat.
const _origRenderAnalysis = window.renderAnalysis;
// We patch via a flag since renderAnalysis is defined in app.js scope.
// Instead, app.js sets window._lastBrief — chat.js reads it on open.
