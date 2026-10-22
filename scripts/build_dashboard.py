import os
import re
import json
from datetime import datetime

BRIEFS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "briefs")
WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")
DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")

def parse_markdown_brief(md_content):
    """Parses a structured Daily Intelligence Brief markdown file into JSON data."""
    data = {
        "date": "",
        "global_posture": "",
        "executive_radar": [],
        "sections": {
            "global": [],
            "vietnam": [],
            "science": [],
            "radar_skim": []
        }
    }

    # Extract Date
    date_match = re.search(r"# 🌅 Daily Intelligence Briefing — ([^\n]+)", md_content)
    if date_match:
        data["date"] = date_match.group(1).strip()

    # Extract Global Posture
    posture_match = re.search(r"\*\*Global Posture\*\*:\s*\*([^*]+)\*(?:\s*—\s*([^\n]+))?", md_content)
    if posture_match:
        headline = posture_match.group(1).strip() if posture_match.group(1) else ""
        desc = posture_match.group(2).strip() if posture_match.group(2) else ""
        data["global_posture"] = f"{headline} — {desc}" if desc else headline

    # Extract Executive Radar
    radar_block = re.search(r"## ⚡ Executive Radar \([^)]+\)([\s\S]*?)(?=## 🌐|\Z)", md_content)
    if radar_block:
        items = re.findall(r"\d+\.\s+\*\*\[([^\]]+)\]\s+([^*]+)\*\*\s+`\[Impact:\s*([0-9.]+)/10\]`(?:\s+`\[([^\]]+)\]`)?", radar_block.group(1))
        for cat, title, score, tier in items:
            data["executive_radar"].append({
                "category": cat.strip(),
                "title": title.strip(),
                "score": float(score.strip()),
                "tier": (tier or "").strip()
            })

    # Helper to parse news blocks
    def extract_articles(section_text, section_key):
        article_blocks = re.split(r"(?=###\s+)", section_text)
        articles = []
        for block in article_blocks:
            if not block.strip() or not block.startswith("###"):
                continue
            
            title_match = re.search(r"###\s+(?:[^\w\s]*\s*)?([^\n]+)", block)
            score_match = re.search(r"\* \*\*Impact Score\*\*:\s*`([0-9.]+)\s*/\s*10`(?:\s*\(([^)]+)\))?", block)
            sources_match = re.search(r"\* \*\*Sources\*\*:\s*\*([^*]+)\*", block)
            
            # Facts extraction
            facts = []
            facts_block = re.search(r"(?:\* \*\*(?:The Facts|Sự Kiện Cốt Lõi)[^*]*\*\*:\s*)([\s\S]*?)(?=\* \*\*(?:The \"So What\?\"|Phân Tích Hệ Quả|Chỉ Số|Key Metric)|\Z)", block)
            if facts_block:
                facts = [f.strip("- *").strip() for f in facts_block.group(1).strip().split("\n") if f.strip().startswith("-")]

            # So what extraction
            so_what_match = re.search(r"(?:\* \*\*(?:The \"So What\?\"|Phân Tích Hệ Quả)[^*]*\*\*:\s*)([\s\S]*?)(?=\* \*\*(?:Chỉ Số|Key Metric)|\Z)", block)
            so_what = so_what_match.group(1).strip() if so_what_match else ""

            # Metric extraction
            metric_match = re.search(r"(?:\* \*\*(?:Key Metric|Chỉ Số Quan Trọng)\*\*:\s*)([^\n]+)", block)
            metric = metric_match.group(1).strip() if metric_match else ""

            if title_match:
                articles.append({
                    "title": title_match.group(1).strip(),
                    "score": float(score_match.group(1)) if score_match else 7.0,
                    "score_breakdown": score_match.group(2) if score_match and score_match.group(2) else "",
                    "sources": sources_match.group(1).strip() if sources_match else "",
                    "facts": facts,
                    "so_what": so_what,
                    "metric": metric,
                    "section": section_key
                })
        return articles

    # Global Section
    global_block = re.search(r"## 🌐 1\. Global Macro & Geopolitics([\s\S]*?)(?=## 🇻🇳|\Z)", md_content)
    if global_block:
        data["sections"]["global"] = extract_articles(global_block.group(1), "global")

    # Vietnam Section
    vn_block = re.search(r"## 🇻🇳 2\. Tiêu Điểm Việt Nam[^\n]*([\s\S]*?)(?=## 🔬|\Z)", md_content)
    if vn_block:
        data["sections"]["vietnam"] = extract_articles(vn_block.group(1), "vietnam")

    # Science Section
    sci_block = re.search(r"## 🔬 3\. Medicine, Psychology & Science([\s\S]*?)(?=## 📊|\Z)", md_content)
    if sci_block:
        data["sections"]["science"] = extract_articles(sci_block.group(1), "science")

    # Radar Skim
    radar_block = re.search(r"## 📊 Quick-Scan Signals \([^)]+\)([\s\S]*?)$", md_content)
    if radar_block:
        skim_items = re.findall(r"\*\s+\*\*([^*]+)\*\*:\s+([^\n`]+)(?:`\[Impact:\s*([0-9.]+)/10\]`)?", radar_block.group(1))
        for topic, desc, score in skim_items:
            data["sections"]["radar_skim"].append({
                "topic": topic.strip(),
                "desc": desc.strip(),
                "score": float(score.strip()) if score else 6.5
            })

    return data

def build():
    os.makedirs(WEB_DIR, exist_ok=True)
    
    # Find most recent markdown brief
    md_files = [f for f in os.listdir(BRIEFS_DIR) if f.endswith(".md")]
    if not md_files:
        print("No briefs found.")
        return

    md_files.sort(reverse=True)
    latest_file = os.path.join(BRIEFS_DIR, md_files[0])
    
    with open(latest_file, "r", encoding="utf-8") as f:
        content = f.read()

    data = parse_markdown_brief(content)
    
    os.makedirs(DOCS_DIR, exist_ok=True)
    
    # Write JSON data for PWA / client fetching
    for folder in [WEB_DIR, DOCS_DIR]:
        json_path = os.path.join(folder, "data.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        html_path = os.path.join(folder, "index.html")
        generate_html(data, html_path)
        
        manifest_src = os.path.join(WEB_DIR, "manifest.json")
        manifest_dst = os.path.join(folder, "manifest.json")
        if os.path.exists(manifest_src) and manifest_src != manifest_dst:
            with open(manifest_src, "r", encoding="utf-8") as rf:
                with open(manifest_dst, "w", encoding="utf-8") as wf:
                    wf.write(rf.read())

    print(f"Successfully generated dashboard at: {os.path.join(DOCS_DIR, 'index.html')}")

def generate_html(data, out_path):
    json_str = json.dumps(data, ensure_ascii=False)
    html_content = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>Daily Intelligence Briefing</title>
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="DailyIntel">
  <link rel="manifest" href="manifest.json">
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          colors: {{
            brand: {{
              50: '#f0fdf4',
              500: '#10b981',
              600: '#059669',
              900: '#064e3b',
            }},
            surface: {{
              light: '#f8fafc',
              dark: '#0f172a',
              cardDark: '#1e293b',
              cardLight: '#ffffff',
              borderDark: '#334155',
              borderLight: '#e2e8f0'
            }}
          }}
        }}
      }}
    }}
  </script>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      -webkit-font-smoothing: antialiased;
    }}
    /* Custom scrollbar */
    ::-webkit-scrollbar {{ width: 4px; height: 4px; }}
    ::-webkit-scrollbar-thumb {{ background: #475569; border-radius: 4px; }}
    /* Impact badge pill */
    .badge-tier-1 {{ background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }}
    .badge-tier-2 {{ background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }}
    .badge-tier-3 {{ background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }}
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen pb-20 selection:bg-emerald-500 selection:text-white">

  <!-- Sticky Top Header -->
  <header class="sticky top-0 z-50 backdrop-blur-md bg-slate-950/85 border-b border-slate-800 px-4 py-3.5 flex items-center justify-between">
    <div class="flex items-center space-x-2.5">
      <div class="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-bold text-sm">
        ⚡
      </div>
      <div>
        <h1 class="text-sm font-semibold tracking-tight text-white leading-tight">Daily Intelligence</h1>
        <p class="text-[11px] text-slate-400 font-medium" id="briefDate">{data.get("date", "Today")}</p>
      </div>
    </div>
    
    <div class="flex items-center space-x-2">
      <!-- Search toggle -->
      <button onclick="toggleSearch()" class="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white transition">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
      </button>
      <!-- Quick Refresh -->
      <button onclick="location.reload()" class="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white transition">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
      </button>
    </div>
  </header>

  <!-- Search input bar (hidden by default) -->
  <div id="searchBar" class="hidden px-4 py-2.5 bg-slate-900/90 border-b border-slate-800">
    <input type="text" id="searchInput" oninput="filterNews()" placeholder="Filter by keyword (e.g. Fed, GDP, SBV, Nobel)..." 
           class="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500">
  </div>

  <main class="max-w-2xl mx-auto px-4 pt-4 space-y-5">
    
    <!-- Global Posture Card -->
    <div class="p-4 rounded-xl bg-gradient-to-br from-slate-900 via-slate-900/90 to-slate-950 border border-slate-800/80 shadow-sm relative overflow-hidden">
      <div class="absolute top-0 right-0 w-32 h-32 bg-emerald-500/5 rounded-full blur-2xl pointer-events-none"></div>
      <div class="flex items-center space-x-2 mb-1.5">
        <span class="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
        <span class="text-[11px] font-semibold uppercase tracking-wider text-emerald-400">Executive Posture</span>
      </div>
      <p class="text-xs text-slate-300 leading-relaxed font-normal">
        {data.get("global_posture", "Calibrated intelligence monitoring active.")}
      </p>
    </div>

    <!-- Category Nav Tabs -->
    <div class="flex space-x-2 overflow-x-auto no-scrollbar py-1">
      <button onclick="setTab('all')" id="tab-all" class="px-3.5 py-1.5 rounded-full text-xs font-medium bg-emerald-500 text-white whitespace-nowrap shadow-sm transition">
        All Feed
      </button>
      <button onclick="setTab('vietnam')" id="tab-vietnam" class="px-3.5 py-1.5 rounded-full text-xs font-medium bg-slate-900 border border-slate-800 text-slate-400 hover:text-white whitespace-nowrap transition">
        🇻🇳 Việt Nam
      </button>
      <button onclick="setTab('global')" id="tab-global" class="px-3.5 py-1.5 rounded-full text-xs font-medium bg-slate-900 border border-slate-800 text-slate-400 hover:text-white whitespace-nowrap transition">
        🌐 Global Macro
      </button>
      <button onclick="setTab('science')" id="tab-science" class="px-3.5 py-1.5 rounded-full text-xs font-medium bg-slate-900 border border-slate-800 text-slate-400 hover:text-white whitespace-nowrap transition">
        🔬 Science & Med
      </button>
      <button onclick="setTab('radar')" id="tab-radar" class="px-3.5 py-1.5 rounded-full text-xs font-medium bg-slate-900 border border-slate-800 text-slate-400 hover:text-white whitespace-nowrap transition">
        ⚡ Radar Skim
      </button>
    </div>

    <!-- Executive Radar Top 3 -->
    <section id="radarSection" class="space-y-2.5">
      <div class="flex items-center justify-between">
        <h2 class="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
          <span>⚡ Top Impact Radar</span>
        </h2>
      </div>
      <div id="radarCards" class="grid gap-2">
        <!-- Injected via JS -->
      </div>
    </section>

    <!-- Main Articles Stream -->
    <section class="space-y-3 pt-2">
      <div class="flex items-center justify-between">
        <h2 id="streamTitle" class="text-xs font-bold uppercase tracking-wider text-slate-400">
          In-Depth Strategic Intelligence
        </h2>
      </div>
      <div id="articlesContainer" class="space-y-3.5">
        <!-- Injected via JS -->
      </div>
    </section>

  </main>

  <!-- Bottom Navigation Bar for Mobile -->
  <nav class="fixed bottom-0 left-0 right-0 z-50 bg-slate-950/90 backdrop-blur-lg border-t border-slate-800/80 px-6 py-2.5 flex items-center justify-around max-w-2xl mx-auto">
    <button onclick="setTab('all')" class="flex flex-col items-center space-y-1 text-emerald-400">
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"></path></svg>
      <span class="text-[10px] font-medium">Briefing</span>
    </button>
    <button onclick="setTab('vietnam')" class="flex flex-col items-center space-y-1 text-slate-400 hover:text-slate-200">
      <span class="text-base leading-none">🇻🇳</span>
      <span class="text-[10px] font-medium">Việt Nam</span>
    </button>
    <button onclick="setTab('global')" class="flex flex-col items-center space-y-1 text-slate-400 hover:text-slate-200">
      <span class="text-base leading-none">🌐</span>
      <span class="text-[10px] font-medium">Global</span>
    </button>
    <button onclick="shareBrief()" class="flex flex-col items-center space-y-1 text-slate-400 hover:text-slate-200">
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"></path></svg>
      <span class="text-[10px] font-medium">Share</span>
    </button>
  </nav>

  <script>
    const briefData = {json_str};
    let currentTab = 'all';

    function getBadgeClass(score) {{
      if (score >= 8.5) return 'badge-tier-1';
      if (score >= 7.0) return 'badge-tier-2';
      return 'badge-tier-3';
    }}

    function renderRadar() {{
      const container = document.getElementById('radarCards');
      container.innerHTML = '';
      (briefData.executive_radar || []).forEach(item => {{
        const el = document.createElement('div');
        el.className = 'p-3 rounded-lg bg-slate-900 border border-slate-800 flex items-start justify-between space-x-3';
        el.innerHTML = `
          <div class="space-y-1">
            <span class="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">${{item.category}}</span>
            <p class="text-xs font-medium text-slate-200 leading-snug">${{item.title}}</p>
          </div>
          <span class="px-2 py-0.5 rounded text-[11px] font-bold shrink-0 ${{getBadgeClass(item.score)}}">
            ${{item.score.toFixed(1)}}
          </span>
        `;
        container.appendChild(el);
      }});
    }}

    function renderArticles(filterCategory = 'all', searchQuery = '') {{
      const container = document.getElementById('articlesContainer');
      container.innerHTML = '';

      let items = [];
      if (filterCategory === 'all' || filterCategory === 'vietnam') items.push(...(briefData.sections.vietnam || []));
      if (filterCategory === 'all' || filterCategory === 'global') items.push(...(briefData.sections.global || []));
      if (filterCategory === 'all' || filterCategory === 'science') items.push(...(briefData.sections.science || []));

      if (searchQuery.trim()) {{
        const q = searchQuery.toLowerCase();
        items = items.filter(i => 
          i.title.toLowerCase().includes(q) || 
          (i.so_what && i.so_what.toLowerCase().includes(q)) ||
          (i.sources && i.sources.toLowerCase().includes(q))
        );
      }}

      // Sort by impact score descending
      items.sort((a, b) => b.score - a.score);

      if (items.length === 0) {{
        container.innerHTML = `
          <div class="text-center py-8 text-xs text-slate-500">
            No developments matching current filter.
          </div>
        `;
        return;
      }}

      items.forEach((art, idx) => {{
        const card = document.createElement('article');
        card.className = 'rounded-xl bg-slate-900 border border-slate-800/90 overflow-hidden shadow-sm transition hover:border-slate-700';

        const categoryTag = art.section === 'vietnam' ? '🇻🇳 Việt Nam' : (art.section === 'global' ? '🌐 Global' : '🔬 Science & Med');
        
        const factsHtml = (art.facts || []).map(f => `
          <li class="flex items-start space-x-2 text-xs text-slate-300">
            <span class="text-emerald-400 shrink-0 font-bold">•</span>
            <span class="leading-relaxed">${{f}}</span>
          </li>
        `).join('');

        card.innerHTML = `
          <!-- Card Header -->
          <div class="p-4 space-y-2 border-b border-slate-800/60">
            <div class="flex items-center justify-between">
              <span class="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider">${{categoryTag}}</span>
              <div class="flex items-center space-x-1.5">
                <span class="text-[10px] text-slate-400 font-medium">Impact</span>
                <span class="px-2 py-0.5 rounded text-xs font-bold ${{getBadgeClass(art.score)}}">
                  ${{art.score.toFixed(1)}}
                </span>
              </div>
            </div>
            <h3 class="text-sm font-semibold text-white leading-snug">${{art.title}}</h3>
            ${{art.sources ? `<p class="text-[10px] text-slate-400 italic">Sources: ${{art.sources}}</p>` : ''}}
          </div>

          <!-- Card Body: Facts & So What -->
          <div class="p-4 space-y-3.5 bg-slate-950/40">
            <!-- Facts list -->
            <div>
              <span class="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-1.5">Sự Kiện Cốt Lõi / The Facts</span>
              <ul class="space-y-1.5">
                ${{factsHtml}}
              </ul>
            </div>

            <!-- The So What -->
            ${{art.so_what ? `
              <div class="p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/20 space-y-1">
                <span class="text-[11px] font-bold uppercase tracking-wider text-emerald-400 flex items-center space-x-1">
                  <span>🎯 Phân Tích Hệ Quả / The "So What?"</span>
                </span>
                <p class="text-xs text-slate-300 leading-relaxed font-normal">${{art.so_what}}</p>
              </div>
            ` : ''}}

            <!-- Key Metric -->
            ${{art.metric ? `
              <div class="flex items-center space-x-2 text-[11px] text-slate-400 bg-slate-900/60 px-2.5 py-1.5 rounded-lg border border-slate-800/80">
                <span class="text-emerald-400 font-bold shrink-0">📊 Chỉ số:</span>
                <span class="font-medium text-slate-300 truncate">${{art.metric}}</span>
              </div>
            ` : ''}}
          </div>
        `;
        container.appendChild(card);
      }});
    }}

    function setTab(tab) {{
      currentTab = tab;
      // Update Tab Pill styles
      ['all', 'vietnam', 'global', 'science', 'radar'].forEach(t => {{
        const btn = document.getElementById('tab-' + t);
        if (!btn) return;
        if (t === tab) {{
          btn.className = 'px-3.5 py-1.5 rounded-full text-xs font-medium bg-emerald-500 text-white whitespace-nowrap shadow-sm transition';
        }} else {{
          btn.className = 'px-3.5 py-1.5 rounded-full text-xs font-medium bg-slate-900 border border-slate-800 text-slate-400 hover:text-white whitespace-nowrap transition';
        }}
      }});

      if (tab === 'radar') {{
        document.getElementById('radarSection').scrollIntoView({{ behavior: 'smooth' }});
      }} else {{
        renderArticles(tab, document.getElementById('searchInput').value);
      }}
    }}

    function toggleSearch() {{
      const bar = document.getElementById('searchBar');
      bar.classList.toggle('hidden');
      if (!bar.classList.contains('hidden')) {{
        document.getElementById('searchInput').focus();
      }}
    }}

    function filterNews() {{
      const q = document.getElementById('searchInput').value;
      renderArticles(currentTab, q);
    }}

    function shareBrief() {{
      if (navigator.share) {{
        navigator.share({{
          title: 'Daily Intelligence Briefing',
          text: briefData.global_posture,
          url: window.location.href
        }}).catch(() => {{}});
      }} else {{
        navigator.clipboard.writeText(window.location.href);
        alert('Dashboard link copied to clipboard!');
      }}
    }}

    // Init
    renderRadar();
    renderArticles('all');
  </script>
</body>
</html>
"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    build()
