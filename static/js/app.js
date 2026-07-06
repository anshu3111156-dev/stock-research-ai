/* ═══════════════════════════════════════════════════════════════════
   StockAI — frontend SPA
   Replaces all Streamlit UI logic.  Talks to Flask /api/* endpoints.
═══════════════════════════════════════════════════════════════════ */

// ── STATE ──────────────────────────────────────────────────────────────
const state = {
  level:          null,
  ticker:         "",
  companyName:    "",
  companies:      {},   // loaded once
};

// ── LEVEL HELPERS ───────────────────────────────────────────────────────
const isBeginner    = () => state.level && (state.level.includes("Beginner")    || state.level.includes("🌱"));
const isLearner     = () => state.level && (state.level.includes("Learner")     || state.level.includes("📈"));
const isExpert      = () => state.level && (state.level.includes("Expert")      || state.level.includes("🏦"));
const isIntermediate= () => state.level && (state.level.includes("Intermediate")|| state.level.includes("💼"));

function levelRank() {
  if (isBeginner())     return 0;
  if (isLearner())      return 1;
  if (isExpert())       return 3;
  return 2;
}

const MAX_EXT_METRICS  = {0:2, 1:3, 2:5, 3:99};
const MAX_SIGNALS      = {0:4, 1:6, 2:10, 3:99};
const MAX_PEER_COLS    = {0:3, 1:4, 2:5, 3:5};

// ── PLAIN EXPLAINERS ────────────────────────────────────────────────────
const PLAIN = {
  technical: [
    "These are technical indicators traders use to study price patterns. You don't need to understand the formulas — just know that they describe what the price has been doing recently, not what it will do next.",
    "RSI, MACD and Bollinger Bands describe recent price momentum and how stretched the price is versus its recent range. They're descriptive, not predictive.",
    "Standard momentum/volatility indicators (RSI, MACD, Bollinger Bands), shown here as descriptive context on recent price action.",
    "Textbook technical readings (RSI-14, MACD, Bollinger Bands) for recent price action.",
  ],
  peers: [
    "This compares the company to a few similar companies in the same industry. A number only means something next to others like it — e.g. a P/E of 30 sounds high, but might be normal for that industry.",
    "Comparing key ratios against a few close industry peers gives context — the same number can mean different things in different sectors.",
    "Ratios for this stock vs its closest listed peers, for relative valuation context.",
    "Peer set ratios (P/E, P/B, ROE, margin, market cap) for relative valuation benchmarking.",
  ],
  correlation: [
    "This shows how closely this stock's price moves track the overall market. A high number means it usually goes up and down WITH the market; a low number means it moves more on its own.",
    "Correlation and beta describe how this stock's moves have related to the broader market index recently — useful context, not a forecast.",
    "Correlation, beta estimate, and annualised volatility vs the relevant benchmark index.",
    "Trailing correlation/beta vs benchmark, with annualised volatility — descriptive co-movement only.",
  ],
};
const plainExplain = (section) => PLAIN[section]?.[levelRank()] ?? "";

// ── GLOSSARY ────────────────────────────────────────────────────────────
const GLOSSARY = {
  "P/E Ratio":        "Price to Earnings — how much you pay for every ₹1 of profit. Lower = potentially cheaper.",
  "Forward P/E":      "Expected P/E based on next year's estimated earnings. Lower than trailing P/E = earnings expected to grow.",
  "P/B Ratio":        "Price to Book — stock price vs net assets. Below 1 means trading below book value.",
  "EPS":              "Earnings Per Share — company profit divided by number of shares. Higher is better.",
  "EV/EBITDA":        "Enterprise Value to EBITDA — accounts for debt in valuation. Popular for comparing companies.",
  "ROE":              "Return on Equity — profit generated per rupee of shareholder money. Above 15% is generally good.",
  "ROA":              "Return on Assets — how efficiently all assets are used to generate profit.",
  "Debt to Equity":   "How much the company has borrowed vs what shareholders own. D/E below 50% is generally low.",
  "Profit Margin":    "% of revenue that becomes profit. Higher = more efficient business model.",
  "Gross Margin":     "Revenue minus cost of goods sold, as a %. High gross margin = strong pricing power.",
  "Operating Margin": "Profit after operating costs. Shows how efficient the core business is.",
  "Free Cash Flow":   "Cash left after all expenses and investments. Positive FCF = real cash being generated.",
  "Current Ratio":    "Current assets / current liabilities. Above 1 = can pay short-term obligations.",
  "Beta":             "How much the stock moves vs the market. Beta 1.5 = 50% more volatile than Nifty/S&P 500.",
  "Revenue Growth":   "How much sales grew year-on-year. Above 10% is healthy for most sectors.",
  "Market Cap":       "Total value of all shares. Large cap >₹20,000 Cr, mid cap ₹5,000–20,000 Cr.",
  "52 Week High/Low": "Highest and lowest price in the past year. Useful for understanding price range.",
  "Moving Average":   "Average price over a period. MA50 = last 50 days. Price above MA200 = positive trend.",
  "Volatility":       "How much the price moves daily. Higher = more risk and potential reward.",
  "Dividend Yield":   "Annual dividend as % of stock price. Good for income-seeking investors.",
  "Bull Market":      "Rising market — prices going up over a sustained period.",
  "Bear Market":      "Falling market — prices going down over a sustained period.",
  "NSE":              "National Stock Exchange — India's largest exchange by trading volume.",
  "BSE":              "Bombay Stock Exchange — oldest exchange in Asia.",
  "SEBI":             "Securities and Exchange Board of India — regulates Indian markets.",
  "FII":              "Foreign Institutional Investors — large foreign funds investing in Indian markets.",
  "DII":              "Domestic Institutional Investors — Indian mutual funds and insurance companies.",
};

const POPULAR = {
  "Reliance Industries": "RELIANCE.NS",
  "HDFC Bank":           "HDFCBANK.NS",
  "Infosys":             "INFY.NS",
  "Tata Motors":         "TATAMOTORS.NS",
  "Tesla":               "TSLA",
  "NVIDIA":              "NVDA",
  "Apple":               "AAPL",
  "Zomato":              "ZOMATO.NS",
};

// ── PAGE ROUTING ────────────────────────────────────────────────────────
function showPage(id) {
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  document.getElementById(`page-${id}`).classList.add("active");
  window.scrollTo(0, 0);
}

function syncBadges() {
  ["level-badge", "level-badge-g", "level-badge-a"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.textContent = state.level || "";
  });
}

// ── TICKER STRIP ─────────────────────────────────────────────────────────
async function loadStrip() {
  try {
    const res   = await fetch("/api/strip");
    const items = await res.json();
    if (!items.length) return;
    const inner = document.getElementById("stripInner");
    const html  = items.map(it => {
      const cls = it.chg >= 0 ? "tt-strip-up" : "tt-strip-down";
      const arr = it.chg >= 0 ? "▲" : "▼";
      return `<span class="tt-strip-item">
        <span class="tt-strip-name">${it.label}</span>
        <span class="tt-strip-price">${it.price}</span>
        <span class="${cls}">${arr} ${Math.abs(it.chg).toFixed(2)}%</span>
      </span>`;
    }).join("");
    inner.innerHTML = html + html; // doubled for seamless loop
  } catch(e) {}
}

// ── LEVEL SELECTION ──────────────────────────────────────────────────────
document.querySelectorAll(".tt-level-card").forEach(card => {
  card.addEventListener("click", () => {
    state.level = card.dataset.level;
    syncBadges();
    loadCompanies().then(() => {
      showPage("search");
      buildPopular();
    });
  });
});

function changeLevel() {
  state.level = null;
  showPage("level");
}
document.getElementById("btn-change-level").addEventListener("click", changeLevel);
document.getElementById("btn-change-level-g").addEventListener("click", changeLevel);
document.getElementById("btn-change-level-a").addEventListener("click", changeLevel);

// ── COMPANY DATA ─────────────────────────────────────────────────────────
async function loadCompanies() {
  if (Object.keys(state.companies).length) return; // already loaded
  try {
    const res  = await fetch("/api/companies");
    const data = await res.json();
    state.companies = data;
    buildExchangeSelect(data);
  } catch(e) {}
}

function buildExchangeSelect(data) {
  const sel = document.getElementById("exc-select");
  Object.keys(data).forEach(exc => {
    const opt = document.createElement("option");
    opt.value = exc; opt.textContent = exc;
    sel.appendChild(opt);
  });
}

// ── POPULAR BUTTONS ──────────────────────────────────────────────────────
function buildPopular() {
  const grid = document.getElementById("popular-grid");
  grid.innerHTML = "";
  Object.entries(POPULAR).forEach(([name, ticker]) => {
    const btn = document.createElement("button");
    btn.className   = "pop-btn";
    btn.textContent = name;
    btn.onclick     = () => runAnalysis(ticker, name);
    grid.appendChild(btn);
  });
}

// ── SEARCH ───────────────────────────────────────────────────────────────
const searchInput = document.getElementById("search-input");
const suggestBox  = document.getElementById("search-suggestions");
const browseSection = document.getElementById("browse-section");

searchInput.addEventListener("input", debounce(handleSearchInput, 200));

function handleSearchInput() {
  const q = searchInput.value.trim();
  if (q.length < 2) {
    suggestBox.innerHTML = "";
    browseSection.style.display = "block";
    return;
  }
  browseSection.style.display = "none";
  fetchSuggestions(q);
}

async function fetchSuggestions(q) {
  try {
    const res     = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
    const matches = await res.json();
    renderSuggestions(matches, q);
  } catch(e) {}
}

function renderSuggestions(matches, q) {
  if (!matches.length) {
    suggestBox.innerHTML = `<div class="no-match-msg">Company not found — enter a ticker manually below</div>`;
    return;
  }
  suggestBox.innerHTML = `<div class="tt-section-label" style="margin-top:12px;">MATCHING COMPANIES</div>` +
    matches.map(m => `
      <div class="suggestion-item" data-ticker="${m.ticker}" data-name="${m.name}">
        <span class="sug-name">${m.name}</span>
        <span class="sug-ticker">${m.ticker}</span>
      </div>
    `).join("");
  suggestBox.querySelectorAll(".suggestion-item").forEach(el => {
    el.addEventListener("click", () => runAnalysis(el.dataset.ticker, el.dataset.name));
  });
}

document.getElementById("btn-search").addEventListener("click", () => {
  const q = searchInput.value.trim();
  if (q.length < 2) return;
  // Try as raw ticker if no suggestions yet
  fetchSuggestions(q).then(() => {
    const first = suggestBox.querySelector(".suggestion-item");
    if (first) first.click();
    else {
      const clean = sanitiseTicker(q);
      if (clean) runAnalysis(clean, clean);
    }
  });
});

searchInput.addEventListener("keydown", e => {
  if (e.key === "Enter") document.getElementById("btn-search").click();
});

// ── BROWSE BY EXCHANGE ────────────────────────────────────────────────────
const excSel  = document.getElementById("exc-select");
const coSel   = document.getElementById("co-select");
const browseCta = document.getElementById("browse-cta");

excSel.addEventListener("change", () => {
  const exc = excSel.value;
  coSel.innerHTML = '<option value="">— Choose a company —</option>';
  coSel.style.display = "none";
  browseCta.innerHTML = "";
  if (!exc) return;
  const cos = state.companies[exc] || {};
  Object.entries(cos).forEach(([name, tk]) => {
    const opt = document.createElement("option");
    opt.value = tk; opt.textContent = name;
    coSel.appendChild(opt);
  });
  coSel.style.display = "block";
});

coSel.addEventListener("change", () => {
  const tk   = coSel.value;
  const name = coSel.options[coSel.selectedIndex]?.text || tk;
  if (!tk) { browseCta.innerHTML = ""; return; }
  browseCta.innerHTML = `<button class="btn-primary" style="width:100%;margin-top:8px;" id="btn-exc-analyse">
    📊 Analyse: ${name}
  </button>`;
  document.getElementById("btn-exc-analyse").onclick = () => runAnalysis(tk, name);
});

// ── MANUAL TICKER ─────────────────────────────────────────────────────────
document.getElementById("btn-manual").addEventListener("click", () => {
  const val   = document.getElementById("manual-ticker").value.trim();
  const clean = sanitiseTicker(val);
  if (!clean) { alert("Invalid ticker. Use only letters, numbers, dots and hyphens."); return; }
  runAnalysis(clean, clean);
});

// ── GLOSSARY ──────────────────────────────────────────────────────────────
function showGlossary() { renderGlossary(""); showPage("glossary"); }
document.getElementById("btn-glossary").addEventListener("click", showGlossary);
document.getElementById("btn-glossary-a").addEventListener("click", showGlossary);
document.getElementById("btn-glossary-back").addEventListener("click", () => showPage("search"));

const glossSearch = document.getElementById("gloss-search");
glossSearch.addEventListener("input", () => renderGlossary(glossSearch.value));

function renderGlossary(q) {
  const list = document.getElementById("gloss-list");
  const lq   = q.toLowerCase();
  list.innerHTML = Object.entries(GLOSSARY)
    .filter(([term, def]) => !lq || term.toLowerCase().includes(lq) || def.toLowerCase().includes(lq))
    .map(([term, def]) => `
      <div class="tt-gloss-card">
        <div class="tt-gloss-word">${term}</div>
        <div class="tt-gloss-def">${def}</div>
      </div>
    `).join("");
}

// ── ANALYSIS ──────────────────────────────────────────────────────────────
async function runAnalysis(ticker, companyName) {
  state.ticker      = ticker;
  state.companyName = companyName;
  syncBadges();
  showPage("analysis");

  document.getElementById("analysis-loading").style.display  = "block";
  document.getElementById("analysis-content").style.display  = "none";
  document.getElementById("loading-msg").textContent = "Fetching live market data…";

  setTimeout(() => {
    document.getElementById("loading-msg").textContent = "Generating AI research brief…";
  }, 2000);

  try {
    const res  = await fetch("/api/analyse", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ticker, level: state.level}),
    });

    if (!res.ok) {
      const err = await res.json();
      handleApiError(err);
      return;
    }

    const d = await res.json();
    renderAnalysis(d);

  } catch(e) {
    alert("Network error. Please try again.");
    showPage("search");
  }
}

function handleApiError(err) {
  document.getElementById("analysis-loading").style.display = "none";
  const msgs = {
    "invalid_ticker": "Invalid ticker symbol.",
    "session_limit":  "Session request limit reached. Please refresh the page.",
    "rate_limit":     `Please wait ${err.wait}s before the next request.`,
    "busy":           "Market data service is busy. Please wait 2 minutes and try again.",
    "fetch_error":    `Could not fetch data for ${state.companyName}. Check the ticker and try again.`,
  };
  alert(msgs[err.error] || "An error occurred. Please try again.");
  showPage("search");
}

// ── BACK BUTTON ───────────────────────────────────────────────────────────
document.getElementById("btn-back").addEventListener("click", () => {
  searchInput.value      = "";
  suggestBox.innerHTML   = "";
  browseSection.style.display = "block";
  showPage("search");
});

// ═══════════════════════════════════════════════════════════════════════
// RENDER ANALYSIS
// ═══════════════════════════════════════════════════════════════════════
function renderAnalysis(d) {
  const { brief, signals, price_data, history, currency, tech, peers, fin_trend, corr, ext_metrics, has_rag } = d;

  // ── Company header ────────────────────────────────────────────────────
  const price_val = brief.key_metrics?.price ?? "N/A";
  const ret_val   = brief.key_metrics?.one_year_return ?? "N/A";
  let retCls = "tt-return-up", retArrow = "";
  try {
    const rf = parseFloat(String(ret_val).replace("%","").replace("+",""));
    retCls   = rf >= 0 ? "tt-return-up" : "tt-return-down";
    retArrow = rf >= 0 ? "▲" : "▼";
  } catch(e) {}

  document.getElementById("company-header").innerHTML = `
    <div>
      <div class="tt-company-name">${brief.company_name || state.companyName}</div>
      <div class="tt-company-meta">
        ${brief.sector || "N/A"} &nbsp;·&nbsp;
        <span class="ticker-pill">${state.ticker}</span>
      </div>
    </div>
    <div>
      <div class="tt-price">${price_val}</div>
      <div class="${retCls}">${retArrow} ${ret_val}
        <span style="font-weight:400;color:#475569;font-size:12px;">1Y return</span>
      </div>
    </div>
  `;

  // ── Traffic light (beginner) ──────────────────────────────────────────
  const tlWrap = document.getElementById("traffic-light-wrap");
  tlWrap.innerHTML = "";
  if (isBeginner()) {
    const tl    = String(brief.traffic_light || "").toUpperCase();
    const why   = brief.traffic_light_reason || "";
    const cfg   = tl === "GREEN"
      ? {cls:"tl-green",  dot:"green",  emoji:"🟢", label:"Looks stable"}
      : tl === "RED"
      ? {cls:"tl-red",    dot:"red",    emoji:"🔴", label:"Concerning signals"}
      : {cls:"tl-yellow", dot:"yellow", emoji:"🟡", label:"Mixed signals"};
    tlWrap.innerHTML = `
      <div class="${cfg.cls}">
        <div class="tl-dot ${cfg.dot}"></div>
        <div class="tl-text">${cfg.emoji} <b>${cfg.label}</b> — ${why}</div>
      </div>`;
  }

  // ── Key metrics ───────────────────────────────────────────────────────
  const m = brief.key_metrics || {};
  document.getElementById("metrics-row").innerHTML = [
    ["P/E Ratio",      m.pe_ratio],
    ["P/B Ratio",      m.pb_ratio],
    ["Profit Margin",  m.profit_margin],
    ["ROE",            m.roe],
    ["Debt / Equity",  m.debt_to_equity],
    ["Revenue Growth", m.revenue_growth],
  ].map(([lbl, v]) => metricCard(lbl, v ?? "N/A")).join("");

  const cap    = MAX_EXT_METRICS[levelRank()] ?? 99;
  const extCap = (ext_metrics || []).slice(0, cap);
  document.getElementById("ext-metrics-row").innerHTML = extCap.length
    ? extCap.map(([lbl, v]) => metricCard(lbl, v, "tt-metric-small")).join("") : "";

  // ── Price chart ───────────────────────────────────────────────────────
  const chartSec = document.getElementById("chart-section");
  if (price_data?.dates?.length) {
    chartSec.style.display = "block";
    const traces = [{
      x: price_data.dates, y: price_data.closes,
      mode: "lines", name: "Price",
      line: {color: "#ff8c00", width: 2},
      fill: "tozeroy", fillcolor: "rgba(255,140,0,0.05)",
    }];
    if (history?.ma50) {
      const n = price_data.dates.length;
      traces.push({
        x: price_data.dates.slice(-50),
        y: Array(Math.min(50,n)).fill(history.ma50),
        mode: "lines",
        name: isBeginner() ? "50-day average" : "MA50",
        line: {color:"#6366f1", width:1.5, dash:"dash"},
      });
      traces.push({
        x: price_data.dates,
        y: Array(n).fill(history.ma200),
        mode: "lines",
        name: isBeginner() ? "200-day average" : "MA200",
        line: {color:"#ef4444", width:1.5, dash:"dash"},
      });
    }
    Plotly.newPlot("price-chart", traces, {
      paper_bgcolor:"#222836", plot_bgcolor:"#222836",
      font:{color:"#94a3b8",size:11},
      height:340, margin:{l:12,r:12,t:12,b:12},
      xaxis:{gridcolor:"#2d3548",showgrid:true,zeroline:false},
      yaxis:{gridcolor:"#2d3548",showgrid:true,zeroline:false,tickprefix:currency},
      hovermode:"x unified",
      legend:{orientation:"h",yanchor:"bottom",y:1.02,xanchor:"right",x:1,
              bgcolor:"rgba(0,0,0,0)",font:{size:11}},
    }, {responsive:true, displayModeBar:false});

    if (history) {
      document.getElementById("history-stats").innerHTML = [
        ["52W High",  `${currency}${Number(history.high_52w).toLocaleString("en-IN",{minimumFractionDigits:2,maximumFractionDigits:2})}`],
        ["52W Low",   `${currency}${Number(history.low_52w).toLocaleString("en-IN",{minimumFractionDigits:2,maximumFractionDigits:2})}`],
        ["Avg Price", `${currency}${Number(history.avg_price).toLocaleString("en-IN",{minimumFractionDigits:2,maximumFractionDigits:2})}`],
        ["Volatility",`${history.volatility}% daily`],
      ].map(([l,v]) => metricCard(l, v)).join("");
    }
  } else {
    chartSec.style.display = "none";
  }

  // ── Technical indicators ──────────────────────────────────────────────
  renderTech(tech, currency);

  // ── Peer comparison ───────────────────────────────────────────────────
  renderPeers(peers);

  // ── Historical financials ─────────────────────────────────────────────
  renderFinTrend(fin_trend, currency);

  // ── Correlation ───────────────────────────────────────────────────────
  renderCorr(corr);

  // ── Signals ───────────────────────────────────────────────────────────
  const sigCap   = MAX_SIGNALS[levelRank()] ?? 99;
  const warnings = (signals || []).filter(s => s.includes("WARNING"));
  const others   = (signals || []).filter(s => !s.includes("WARNING"));
  const shown    = [...warnings, ...others].slice(0, sigCap);

  let sigHtml = shown.map(s => {
    if (s.includes("WARNING")) return `<span class="chip-red">⚠ ${s}</span>`;
    if (/STRONG|HIGH ROE|VERY LOW|BUY|dividend/i.test(s)) return `<span class="chip-green">✓ ${s}</span>`;
    return `<span class="chip-amber">ℹ ${s}</span>`;
  }).join("");
  if ((signals||[]).length > sigCap)
    sigHtml += `<span class="chip-amber">+${signals.length - sigCap} more (raise your level to see all)</span>`;
  document.getElementById("signals-wrap").innerHTML = sigHtml;

  // ── AI Brief ──────────────────────────────────────────────────────────
  const left = document.getElementById("brief-left");
  const right = document.getElementById("brief-right");

  const risks = brief.risk_flags || [];
  const risksHtml = risks.length
    ? risks.map(r => `<span class="risk-pill">⚠ ${r}</span>`).join("")
    : '<span style="color:#475569;font-size:13px;">No specific risks flagged.</span>';

  left.innerHTML = [
    ["📌 Analyst Summary", "analyst_summary"],
    ["💰 Valuation",       "valuation_commentary"],
    ["📈 Growth Outlook",  "growth_outlook"],
  ].map(([t, k]) => `<div class="tt-card"><div class="tt-card-title">${t}</div><div class="tt-card-text">${brief[k]||"N/A"}</div></div>`).join("") +
  `<div class="tt-card"><div class="tt-card-title">⚠️ Risk Flags</div><div>${risksHtml}</div></div>`;

  right.innerHTML = [
    ["💪 Financial Health",  "financial_health"],
    ["👤 Investor Profile",  "investor_profile"],
    ["🔍 Watch Out For",     "watch_out_for"],
  ].map(([t, k]) => `<div class="tt-card"><div class="tt-card-title">${t}</div><div class="tt-card-text">${brief[k]||"N/A"}</div></div>`).join("");

  // ── News ──────────────────────────────────────────────────────────────
  document.getElementById("news-section").innerHTML = `
    <div class="tt-news-card">
      <div class="tt-card-title">📰 Latest News & Market Context</div>
      <div class="tt-card-text">${brief.news_context || "No recent news available."}</div>
    </div>`;

  // ── Annual report / RAG ───────────────────────────────────────────────
  const ari = brief.annual_report_insights;
  const ragSec = document.getElementById("rag-section");
  if (has_rag && ari && !ari.toLowerCase().includes("not loaded")) {
    ragSec.innerHTML = `
      <div class="tt-rag-card">
        <div class="tt-card-title">📋 Annual Report Insights</div>
        <div class="tt-card-text">${ari}</div>
      </div>`;
  } else {
    ragSec.innerHTML = "";
  }

  // ── Beginner guide ────────────────────────────────────────────────────
  const begSec = document.getElementById("beginner-section");
  if (isBeginner()) {
    const rows = [
      ["P/E Ratio",      "How much you pay for every ₹1 of company profit. Lower is generally cheaper."],
      ["ROE",            "If you gave ₹100, ROE shows how much profit the company made. 15% = ₹15 on your ₹100."],
      ["Debt/Equity",    "How much the company borrowed vs what it owns. Very high debt can be risky."],
      ["Profit Margin",  "Of every ₹100 in sales, how much is actual profit. Higher is better."],
      ["Revenue Growth", "How much sales grew vs last year. 15% growth means they sold 15% more."],
      ["1Y Return",      "If you had bought one year ago, this is what you would have gained or lost."],
    ].map(([t,d]) => `<div class="beginner-row"><strong>${t}</strong> — ${d}</div>`).join("");
    begSec.innerHTML = `
      <div class="tt-section-label">WHAT DO THESE NUMBERS MEAN?</div>
      <div class="tt-beginner">
        <div class="tt-card-title">📖 Simple Guide — What You Just Read</div>
        ${rows}
      </div>`;
  } else {
    begSec.innerHTML = "";
  }

  // ── Show ──────────────────────────────────────────────────────────────
  document.getElementById("analysis-loading").style.display = "none";
  document.getElementById("analysis-content").style.display = "block";

  // Expose brief globally so chatbot can read current stock context
  window._lastBrief = brief;
  if (typeof Chat !== "undefined") Chat.notifyReady(brief.company_name || state.companyName);
}

// ── RENDER HELPERS ────────────────────────────────────────────────────────
function metricCard(label, value, extra="") {
  return `<div class="tt-metric">
    <div class="tt-metric-label">${label}</div>
    <div class="tt-metric-value ${extra}">${value}</div>
  </div>`;
}

function plainExplainHtml(section) {
  const text = plainExplain(section);
  if (!text) return "";
  return `<div class="tt-plain-explain"><span>💡</span><span>${text}</span></div>`;
}

function renderTech(tech, currency) {
  const sec = document.getElementById("tech-section");
  if (!tech || !Object.keys(tech).length) { sec.innerHTML = ""; return; }

  const toneClass = {good:"tt-tag-good", warn:"tt-tag-warn", bad:"tt-tag-bad", neutral:"tt-tag-neutral"};
  const cells = [];

  if (tech.rsi) {
    const r = tech.rsi;
    const label = isBeginner()
      ? (r.tone==="warn" && r.value>=70 ? "Price has risen a lot recently"
        : r.tone==="warn" ? "Price has fallen a lot recently"
        : "Nothing extreme either way")
      : r.label;
    cells.push(["RSI (14)", `${r.value}`, label, toneClass[r.tone] || "tt-tag-neutral"]);
  }
  if (tech.macd) {
    const mc = tech.macd;
    const label = isBeginner()
      ? (mc.tone==="good" ? "Momentum leaning positive" : "Momentum leaning negative")
      : mc.label;
    cells.push(["MACD", `${mc.macd}`, label, toneClass[mc.tone] || "tt-tag-neutral"]);
    if (!isBeginner())
      cells.push(["Signal Line", `${mc.signal}`, `Histogram ${mc.histogram >= 0 ? "+" : ""}${mc.histogram?.toFixed(2)}`, "tt-tag-neutral"]);
  }
  if (tech.bollinger) {
    const bb = tech.bollinger;
    const lbl = isBeginner()
      ? (bb.tone==="warn" && bb.label?.toLowerCase().includes("upper") ? "Price is near the top of its recent range"
        : bb.tone==="warn" ? "Price is near the bottom of its recent range"
        : "Price is in the middle of its recent range")
      : bb.label;
    cells.push([
      isBeginner() ? `Price Range (${currency})` : `Bollinger (${currency})`,
      `${Math.round(bb.lower)} — ${Math.round(bb.upper)}`,
      lbl, toneClass[bb.tone] || "tt-tag-neutral",
    ]);
  }

  const grid = cells.map(([lbl,val,tag,tcls]) => `
    <div class="tt-num-cell">
      <div class="tt-num-label">${lbl}</div>
      <div class="tt-num-value">${val}</div>
      <div class="tt-num-tag ${tcls}">${tag}</div>
    </div>`).join("");

  sec.innerHTML = `
    <div class="tt-section-label">TECHNICAL INDICATORS</div>
    ${plainExplainHtml("technical")}
    <div class="tt-disclaimer"><span>ℹ️</span><span>These describe <b>past</b> price action using standard textbook formulas. There is no reliable evidence that technical indicators predict future returns — treat these as context, not signals to act on.</span></div>
    <div class="tt-panel"><div class="tt-num-grid">${grid}</div></div>
    <hr class="tt-divider">`;
}

function renderPeers(peers) {
  const sec = document.getElementById("peer-section");
  if (!peers?.rows?.length) { sec.innerHTML = ""; return; }

  const colCap = MAX_PEER_COLS[levelRank()] ?? 5;
  const allCols = ["Company","P/E","P/B","ROE","Margin","Mkt Cap"];
  const cols    = allCols.slice(0, colCap);

  const thead = cols.map(c => `<th>${c}</th>`).join("");
  const tbody = peers.rows.map(row => {
    const cells = [
      row.name,
      row.pe   != null ? `${row.pe}x`     : "—",
      row.pb   != null ? `${row.pb}x`     : "—",
      row.roe  != null ? `${row.roe}%`    : "—",
      row.margin != null ? `${row.margin}%` : "—",
      row.mcap ? fmtMcap(row.mcap) : "—",
    ].slice(0, colCap);
    const cls = row.is_subject ? "subject" : "";
    return `<tr class="${cls}">${cells.map(c => `<td>${c}</td>`).join("")}</tr>`;
  }).join("");

  sec.innerHTML = `
    <div class="tt-section-label">PEER COMPARISON</div>
    ${plainExplainHtml("peers")}
    <div class="tt-disclaimer"><span>ℹ️</span><span>Ratios fetched live for this stock and its closest listed peers. Useful for relative context — a high P/E only means something next to similar companies.</span></div>
    <div class="tt-panel">
      <table class="tt-table"><thead><tr>${thead}</tr></thead><tbody>${tbody}</tbody></table>
    </div>
    <hr class="tt-divider">`;
}

function renderFinTrend(fin, currency) {
  const sec = document.getElementById("fin-section");
  sec.innerHTML = "";
  if (isBeginner()) {
    sec.innerHTML = `<div class="tt-plain-explain"><span>💡</span><span>We've kept multi-year financial statement trends out of the Beginner view to avoid overload — switch to Learner or above (via 'Change Level' up top) to see revenue and profit history charts.</span></div>`;
    return;
  }
  if (!fin?.years?.length) return;

  sec.innerHTML = `<div class="tt-section-label">HISTORICAL FINANCIALS</div>
    <div class="tt-disclaimer"><span>ℹ️</span><span>Annual figures as reported, most recent years available. Shows trend direction only — not adjusted for one-off items or accounting changes.</span></div>
    <div id="fin-chart" style="margin-bottom:12px;"></div>`;

  const traces = [];
  if (fin.revenue)
    traces.push({x:fin.years, y:fin.revenue, name:"Revenue", type:"bar", marker:{color:"#6366f1"}, opacity:0.85});
  if (fin.net_income)
    traces.push({x:fin.years, y:fin.net_income, name:"Net Income", type:"bar", marker:{color:"#ff8c00"}, opacity:0.85});

  Plotly.newPlot("fin-chart", traces, {
    barmode:"group",
    paper_bgcolor:"#222836", plot_bgcolor:"#222836",
    font:{color:"#94a3b8",size:11},
    height:300, margin:{l:12,r:12,t:12,b:12},
    xaxis:{gridcolor:"#2d3548",showgrid:false},
    yaxis:{gridcolor:"#2d3548",showgrid:true,zeroline:false},
    legend:{orientation:"h",yanchor:"bottom",y:1.02,xanchor:"right",x:1,bgcolor:"rgba(0,0,0,0)",font:{size:11}},
  }, {responsive:true, displayModeBar:false});

  if (fin.net_margin && !isLearner()) {
    const marginCells = fin.years.map((y,i) => fin.net_margin[i] != null
      ? `<div class="tt-num-cell"><div class="tt-num-label">${y} margin</div><div class="tt-num-value" style="font-size:14px;">${fin.net_margin[i]}%</div></div>`
      : "").join("");
    sec.innerHTML += `<div class="tt-num-grid">${marginCells}</div>`;
  }
  sec.innerHTML += `<hr class="tt-divider">`;
}

function renderCorr(corr) {
  const sec = document.getElementById("corr-section");
  if (!corr || !Object.keys(corr).length) { sec.innerHTML = ""; return; }

  const betaLabel = isBeginner() ? "Market sensitivity" : "Beta (est.)";
  const cells = [
    ["Correlation", `${Number(corr.correlation).toFixed(2)}`, corr.correlation_label, "tt-tag-neutral"],
    [betaLabel, corr.beta_estimate != null ? `${Number(corr.beta_estimate).toFixed(2)}` : "—", `vs ${corr.benchmark_name}`, "tt-tag-neutral"],
    ["Stock Volatility", `${corr.stock_volatility}%`, "annualised",
      corr.stock_volatility > corr.bench_volatility ? "tt-tag-warn" : "tt-tag-good"],
  ];
  if (!isBeginner())
    cells.push([`${corr.benchmark_name} Volatility`, `${corr.bench_volatility}%`, "annualised", "tt-tag-neutral"]);

  const grid = cells.map(([l,v,t,cls]) => `
    <div class="tt-num-cell">
      <div class="tt-num-label">${l}</div>
      <div class="tt-num-value">${v}</div>
      <div class="tt-num-tag ${cls}">${t}</div>
    </div>`).join("");

  sec.innerHTML = `
    <div class="tt-section-label">CORRELATION & VOLATILITY</div>
    ${plainExplainHtml("correlation")}
    <div class="tt-disclaimer"><span>ℹ️</span><span>Measures how this stock's daily moves have related to the ${corr.benchmark_name} over the past year. Past co-movement, not a forecast.</span></div>
    <div class="tt-panel"><div class="tt-num-grid">${grid}</div></div>
    <hr class="tt-divider">`;
}

// ── UTILS ──────────────────────────────────────────────────────────────────
function fmtMcap(v) {
  if (v >= 1e12) return `${(v/1e12).toFixed(2)}T`;
  if (v >= 1e9)  return `${(v/1e9).toFixed(1)}B`;
  return `${(v/1e6).toFixed(0)}M`;
}

function sanitiseTicker(raw) {
  const clean = raw.toUpperCase().replace(/[^A-Z0-9.\-&]/g, "").slice(0,15);
  if (!clean) return null;
  if (!/^[A-Z0-9&\-]{1,12}(\.[A-Z]{1,3})?$/.test(clean)) return null;
  return clean;
}

function debounce(fn, ms) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

// ── INIT ───────────────────────────────────────────────────────────────────
loadStrip();
setInterval(loadStrip, 45000);
