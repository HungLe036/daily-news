import os
import re
import json
from datetime import datetime

BRIEFS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "briefs")
WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")
DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")

def strip_emojis(text):
    """Removes all emoji symbols and extra trailing punctuation."""
    if not text:
        return ""
    # Standard emoji ranges
    emoji_pattern = re.compile(
        "["
        "\U00010000-\U0010ffff"
        "\U0001f300-\U0001f5ff"
        "\U0001f600-\U0001f64f"
        "\U0001f680-\U0001f6ff"
        "\U0001f700-\U0001f77f"
        "\U0001f780-\U0001f7ff"
        "\U0001f800-\U0001f8ff"
        "\U0001f900-\U0001f9ff"
        "\U0001fa00-\U0001fa6f"
        "\U0001fa70-\U0001faff"
        "\u2600-\u26ff"
        "\u2700-\u27bf"
        "\ufe0f"
        "]+", flags=re.UNICODE
    )
    cleaned = emoji_pattern.sub('', text)
    # Clean up leading non-alphanumeric except Vietnamese characters / quotes
    cleaned = re.sub(r'^[^\w\s"\'\[]+', '', cleaned).strip()
    return cleaned

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
    date_match = re.search(r"#\s*(?:[^\w\s]*\s*)?Daily Intelligence Briefing\s*—\s*([^\n]+)", md_content)
    if date_match:
        data["date"] = strip_emojis(date_match.group(1).strip())

    # Extract Global Posture
    posture_match = re.search(r"\*\*Global Posture\*\*:\s*\*([^*]+)\*(?:\s*—\s*([^\n]+))?", md_content)
    if posture_match:
        headline = posture_match.group(1).strip() if posture_match.group(1) else ""
        desc = posture_match.group(2).strip() if posture_match.group(2) else ""
        data["global_posture"] = strip_emojis(f"{headline} — {desc}" if desc else headline)

    article_counter = 0

    # Helper to parse news blocks
    def extract_articles(section_text, section_key):
        nonlocal article_counter
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
            facts_block = re.search(r"(?:\* \*\*(?:Core Facts|The Facts|Sự Kiện Cốt Lõi)[^*]*\*\*:\s*)([\s\S]*?)(?=\* \*\*(?:Strategic Implication|The \"So What\?\"|Phân Tích Hệ Quả|Chỉ Số|Key Metric)|\Z)", block)
            if facts_block:
                facts = [strip_emojis(f.strip("- *").strip()) for f in facts_block.group(1).strip().split("\n") if f.strip().startswith("-")]

            # So what extraction
            so_what_match = re.search(r"(?:\* \*\*(?:Strategic Implication|The \"So What\?\"|Phân Tích Hệ Quả)[^*]*\*\*:\s*)([\s\S]*?)(?=\* \*\*(?:Key Metric|Chỉ Số|Chỉ Số Quan Trọng)|\Z)", block)
            so_what = strip_emojis(so_what_match.group(1).strip()) if so_what_match else ""

            # Metric extraction
            metric_match = re.search(r"(?:\* \*\*(?:Key Metric|Chỉ Số Quan Trọng|Chỉ Số)\*\*:\s*)([^\n]+)", block)
            metric = strip_emojis(metric_match.group(1).strip()) if metric_match else ""

            if title_match:
                article_counter += 1
                articles.append({
                    "id": f"art-{article_counter}",
                    "title": strip_emojis(title_match.group(1).strip()),
                    "score": float(score_match.group(1)) if score_match else 7.0,
                    "score_breakdown": score_match.group(2) if score_match and score_match.group(2) else "",
                    "sources": strip_emojis(sources_match.group(1).strip()) if sources_match else "",
                    "facts": facts,
                    "so_what": so_what,
                    "metric": metric,
                    "section": section_key
                })
        return articles

    # Global Section
    global_block = re.search(r"##\s*(?:[^\w\s]*\s*)?(?:1\.\s*)?Global Macro & Geopolitics([\s\S]*?)(?=\n## [^\n#]|\Z)", md_content)
    if global_block:
        data["sections"]["global"] = extract_articles(global_block.group(1), "global")

    # Vietnam Section
    vn_block = re.search(r"##\s*(?:[^\w\s]*\s*)?(?:2\.\s*)?(?:Vietnam Spotlight|Tiêu Điểm Việt Nam)[^\n]*([\s\S]*?)(?=\n## [^\n#]|\Z)", md_content)
    if vn_block:
        data["sections"]["vietnam"] = extract_articles(vn_block.group(1), "vietnam")

    # Science Section
    sci_block = re.search(r"##\s*(?:[^\w\s]*\s*)?(?:3\.\s*)?Medicine, Psychology & Science([\s\S]*?)(?=\n## [^\n#]|\Z)", md_content)
    if sci_block:
        data["sections"]["science"] = extract_articles(sci_block.group(1), "science")

    # Extract Executive Radar and match with article IDs
    radar_block = re.search(r"##\s*(?:[^\w\s]*\s*)?Executive Radar[^\n]*\n([\s\S]*?)(?=\n## |\Z)", md_content)
    if radar_block:
        items = re.findall(r"\d+\.\s+\*\*\[([^\]]+)\]\s+([^*]+)\*\*\s+`\[Impact:\s*([0-9.]+)/10\]`(?:\s+`\[([^\]]+)\]`)?", radar_block.group(1))
        all_articles = data["sections"]["global"] + data["sections"]["vietnam"] + data["sections"]["science"]
        for cat, title, score, tier in items:
            clean_title = strip_emojis(title.strip())
            clean_words = set(re.findall(r'\w+', clean_title.lower()))
            matching_id = None
            max_overlap = 0
            for art in all_articles:
                art_words = set(re.findall(r'\w+', art["title"].lower()))
                overlap = len(clean_words.intersection(art_words))
                if overlap > max_overlap and overlap >= 2:
                    max_overlap = overlap
                    matching_id = art["id"]
            
            data["executive_radar"].append({
                "category": strip_emojis(cat.strip()),
                "title": clean_title,
                "score": float(score.strip()),
                "tier": strip_emojis((tier or "").strip()),
                "article_id": matching_id
            })

    # Radar Skim
    skim_block = re.search(r"##\s*(?:[^\w\s]*\s*)?Quick-Scan Signals[^\n]*([\s\S]*?)$", md_content)
    if skim_block:
        skim_items = re.findall(r"\*\s+\*\*([^*]+)\*\*:\s+([^\n`]+)(?:`\[Impact:\s*([0-9.]+)/10\]`)?", skim_block.group(1))
        for topic, desc, score in skim_items:
            data["sections"]["radar_skim"].append({
                "topic": strip_emojis(topic.strip()),
                "desc": strip_emojis(desc.strip()),
                "score": float(score.strip()) if score else 6.5
            })

    return data

def build():
    os.makedirs(WEB_DIR, exist_ok=True)
    os.makedirs(DOCS_DIR, exist_ok=True)
    
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
    
    # Write JSON data for PWA / client fetching
    for folder in [WEB_DIR, DOCS_DIR]:
        json_path = os.path.join(folder, "data.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        html_path = os.path.join(folder, "index.html")
        generate_html(data, html_path)

    # Sync supporting files (manifest, sw, icons)
    for asset in ["manifest.json", "sw.js", "icon-192.png", "icon-512.png"]:
        src = os.path.join(WEB_DIR, asset)
        dst = os.path.join(DOCS_DIR, asset)
        if os.path.exists(src) and not os.path.exists(dst):
            with open(src, "rb") as rf:
                with open(dst, "wb") as wf:
                    wf.write(rf.read())

    print(f"Successfully generated dashboard at: {os.path.join(DOCS_DIR, 'index.html')}")

def generate_html(data, out_path):
    json_str = json.dumps(data, ensure_ascii=False)
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>Daily Intelligence Briefing</title>
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="default">
  <meta name="apple-mobile-web-app-title" content="DailyIntel">
  <link rel="manifest" href="manifest.json">
  
  <!-- Editorial Typography: Newsreader (Serif) + Plus Jakarta Sans (UI) -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;0,6..72,700;1,6..72,400;1,6..72,500&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {{
      theme: {{
        extend: {{
          fontFamily: {{
            serif: ['Newsreader', 'Georgia', 'Cambria', 'serif'],
            sans: ['"Plus Jakarta Sans"', '-apple-system', 'sans-serif'],
          }},
          colors: {{
            paper: {{
              50: '#FDFCF7',
              100: '#FBF9F3',
              200: '#F7F4EB',
              300: '#EFEBE0',
              border: '#E5DFD3',
              borderDark: '#D6CFC3',
            }},
            ink: {{
              900: '#1A1816',
              800: '#2C2825',
              700: '#423D38',
              600: '#5A534B',
              500: '#706A62',
              400: '#948D84',
            }},
            oxblood: {{
              DEFAULT: '#9B2226',
              soft: '#FBF0EE',
              border: '#F0CAC5',
            }},
            amber: {{
              DEFAULT: '#8F5206',
              soft: '#FAF3E8',
              border: '#EDDAC0',
            }},
            slate: {{
              DEFAULT: '#244263',
              soft: '#EEF3F8',
              border: '#CCDCEB',
            }}
          }}
        }}
      }}
    }}
  </script>
  <style>
    /* Paper Page Aesthetics */
    body {{
      background-color: #F8F5EE;
      color: #1A1816;
      font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
      -webkit-font-smoothing: antialiased;
      background-image: radial-gradient(#E8E2D5 0.75px, transparent 0.75px);
      background-size: 16px 16px;
    }}
    
    .font-serif-headline {{
      font-family: 'Newsreader', Georgia, serif;
      letter-spacing: -0.015em;
    }}

    /* Paper Card: Crisp, matte, understated */
    .paper-card {{
      background-color: #FFFFFF;
      border: 1px solid #E5DFD3;
      box-shadow: 0 1px 3px rgba(35, 31, 28, 0.03), 0 1px 2px rgba(35, 31, 28, 0.02);
      transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
    }}

    .paper-inset {{
      background-color: #F4EFE6;
      border: 1px solid #E8E2D7;
    }}

    /* Editorial Wax/Stamp Badges */
    .stamp-tier-1 {{
      background-color: #FDF0EE;
      color: #9B2226;
      border: 1px solid #F0CAC5;
    }}
    .stamp-tier-2 {{
      background-color: #FAF3E8;
      color: #8F5206;
      border: 1px solid #EDDAC0;
    }}
    .stamp-tier-3 {{
      background-color: #EEF3F8;
      color: #244263;
      border: 1px solid #CCDCEB;
    }}

    /* Flash highlight when jumped from radar */
    @keyframes jumpHighlight {{
      0% {{ background-color: #FDF0EE; outline: 2px solid #9B2226; }}
      50% {{ background-color: #FAF3E8; outline: 2px solid #9B2226; }}
      100% {{ background-color: #FFFFFF; outline: none; }}
    }}
    .highlight-target {{
      animation: jumpHighlight 2.4s ease-out;
    }}

    /* Custom scrollbar */
    ::-webkit-scrollbar {{ width: 4px; height: 4px; }}
    ::-webkit-scrollbar-thumb {{ background: #D6CFC3; border-radius: 4px; }}
  </style>
</head>
<body class="min-h-screen pb-12 selection:bg-[#9B2226] selection:text-white">

  <!-- Editorial Top Masthead (Pure Broadsheet Typography, Zero Emojis) -->
  <header class="sticky top-0 z-50 backdrop-blur-md bg-[#F8F5EE]/95 border-b border-[#E5DFD3] px-4 py-3">
    <div class="max-w-2xl mx-auto">
      <!-- Top edition line -->
      <div class="flex items-center justify-between text-[10.5px] tracking-widest uppercase font-semibold text-ink-500 pb-1.5 border-b border-[#EAE4D8]">
        <span>Melbourne Edition</span>
        <span>{data.get("date", "Today")}</span>
        <span>Vol. I</span>
      </div>

      <!-- Main Broadsheet Title Bar -->
      <div class="flex items-center justify-between pt-2">
        <div>
          <h1 class="text-xl sm:text-2xl font-bold font-serif-headline tracking-tight text-ink-900 leading-none">
            DAILY INTELLIGENCE
          </h1>
          <p class="text-[11.5px] font-serif italic text-ink-500 pt-0.5">Verified Global & Vietnam Strategic Analysis</p>
        </div>
        
        <div class="flex items-center space-x-1.5">
          <!-- Search toggle -->
          <button onclick="toggleSearch()" title="Search" class="p-2 rounded-md bg-[#EFEAE0] border border-[#DDD6C8] text-ink-700 hover:text-ink-900 transition">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
          </button>
          <!-- Share -->
          <button onclick="shareBrief()" title="Share" class="p-2 rounded-md bg-[#EFEAE0] border border-[#DDD6C8] text-ink-700 hover:text-ink-900 transition">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"></path></svg>
          </button>
          <!-- Refresh -->
          <button onclick="location.reload()" title="Refresh" class="p-2 rounded-md bg-[#EFEAE0] border border-[#DDD6C8] text-ink-700 hover:text-ink-900 transition">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
          </button>
        </div>
      </div>
    </div>
  </header>

  <!-- Search input bar (hidden by default) -->
  <div id="searchBar" class="hidden max-w-2xl mx-auto px-4 py-2.5 bg-[#EFEAE0] border-b border-[#DDD6C8]">
    <input type="text" id="searchInput" oninput="filterNews()" placeholder="Filter by keyword (e.g. GDP, SBV, Fed, Nobel)..." 
           class="w-full bg-white border border-[#D6CFC3] rounded-md px-3 py-1.5 text-xs text-ink-900 placeholder-ink-400 focus:outline-none focus:border-oxblood">
  </div>

  <main class="max-w-2xl mx-auto px-4 pt-4 space-y-5">
    
    <!-- Executive Posture (Editor's Dispatch) -->
    <div class="p-4 rounded-lg bg-[#FAF7F0] border border-[#E2DBD0] shadow-sm relative">
      <div class="flex items-center space-x-2 mb-1.5">
        <span class="inline-block w-2 h-2 rounded-full bg-oxblood"></span>
        <span class="text-[10.5px] font-bold uppercase tracking-widest text-oxblood">Executive Posture</span>
      </div>
      <p class="text-sm sm:text-[15px] font-serif text-ink-800 leading-relaxed italic">
        "{data.get("global_posture", "Calibrated intelligence monitoring active.")}"
      </p>
    </div>

    <!-- Category Tabs (English Only, No Emojis) -->
    <div class="flex space-x-1.5 overflow-x-auto no-scrollbar py-1">
      <button onclick="setTab('all')" id="tab-all" class="px-3.5 py-1.5 rounded-md text-xs font-semibold bg-ink-900 text-paper-50 whitespace-nowrap shadow-sm transition">
        All Briefings
      </button>
      <button onclick="setTab('vietnam')" id="tab-vietnam" class="px-3.5 py-1.5 rounded-md text-xs font-medium bg-[#EFEBE1] border border-[#DDD7CB] text-ink-700 hover:text-ink-900 whitespace-nowrap transition">
        Vietnam Spotlight
      </button>
      <button onclick="setTab('global')" id="tab-global" class="px-3.5 py-1.5 rounded-md text-xs font-medium bg-[#EFEBE1] border border-[#DDD7CB] text-ink-700 hover:text-ink-900 whitespace-nowrap transition">
        Global Macro
      </button>
      <button onclick="setTab('science')" id="tab-science" class="px-3.5 py-1.5 rounded-md text-xs font-medium bg-[#EFEBE1] border border-[#DDD7CB] text-ink-700 hover:text-ink-900 whitespace-nowrap transition">
        Medicine & Science
      </button>
      <button onclick="setTab('radar')" id="tab-radar" class="px-3.5 py-1.5 rounded-md text-xs font-medium bg-[#EFEBE1] border border-[#DDD7CB] text-ink-700 hover:text-ink-900 whitespace-nowrap transition">
        Radar Signals
      </button>
    </div>

    <!-- Executive Radar Top 3 (Clickable to jump straight to story) -->
    <section id="radarSection" class="space-y-2">
      <div class="flex items-center justify-between border-b border-[#E5DFD3] pb-1">
        <h2 class="text-[11.5px] font-bold uppercase tracking-wider text-ink-700">
          Top Impact Radar
        </h2>
        <span class="text-[10.5px] text-ink-500 font-serif italic">Tap item to read analysis</span>
      </div>
      <div id="radarCards" class="grid gap-2.5">
        <!-- Injected via JS -->
      </div>
    </section>

    <!-- Main Articles Stream -->
    <section class="space-y-3 pt-2">
      <div class="flex items-center justify-between border-b border-[#E5DFD3] pb-1">
        <h2 id="streamTitle" class="text-[11.5px] font-bold uppercase tracking-wider text-ink-700">
          Strategic Intelligence Feed
        </h2>
      </div>
      <div id="articlesContainer" class="space-y-4">
        <!-- Injected via JS -->
      </div>
    </section>

  </main>

  <script>
    const briefData = {json_str};
    let currentTab = 'all';

    function getStampClass(score) {{
      if (score >= 8.5) return 'stamp-tier-1';
      if (score >= 7.0) return 'stamp-tier-2';
      return 'stamp-tier-3';
    }}

    function renderRadar() {{
      const container = document.getElementById('radarCards');
      container.innerHTML = '';
      (briefData.executive_radar || []).forEach(item => {{
        const el = document.createElement('div');
        el.className = 'p-3.5 rounded-lg paper-card flex items-start justify-between space-x-3 cursor-pointer hover:border-oxblood hover:shadow-sm transition';
        el.setAttribute('onclick', `jumpToArticle('${{item.article_id || ''}}', '${{item.category || ''}}')`);
        el.innerHTML = `
          <div class="space-y-1 flex-1">
            <div class="flex items-center space-x-2">
              <span class="text-[9.5px] font-bold text-ink-500 uppercase tracking-widest">${{item.category}}</span>
              <span class="text-[10px] text-oxblood font-serif italic">Read Analysis →</span>
            </div>
            <p class="text-[14px] sm:text-[15px] font-serif font-semibold text-ink-900 leading-snug">${{item.title}}</p>
          </div>
          <span class="px-2.5 py-1 rounded text-xs font-bold shrink-0 ${{getStampClass(item.score)}}">
            ${{item.score.toFixed(1)}}
          </span>
        `;
        container.appendChild(el);
      }});
    }}

    function jumpToArticle(articleId, categoryHint) {{
      if (!articleId) return;

      // Determine target article section
      let targetSec = 'all';
      const allArticles = [...(briefData.sections.vietnam || []), ...(briefData.sections.global || []), ...(briefData.sections.science || [])];
      const target = allArticles.find(a => a.id === articleId);
      if (target) {{
        targetSec = target.section;
      }}

      // Switch tab if article is hidden in current tab
      if (currentTab !== 'all' && currentTab !== targetSec) {{
        setTab('all');
      }}

      setTimeout(() => {{
        const el = document.getElementById(articleId);
        if (el) {{
          el.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
          el.classList.add('highlight-target');
          setTimeout(() => {{
            el.classList.remove('highlight-target');
          }}, 2500);
        }}
      }}, 60);
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
          (i.sources && i.sources.toLowerCase().includes(q)) ||
          (i.metric && i.metric.toLowerCase().includes(q))
        );
      }}

      // Sort by impact score descending
      items.sort((a, b) => b.score - a.score);

      if (items.length === 0) {{
        container.innerHTML = `
          <div class="text-center py-8 text-xs font-serif italic text-ink-400">
            No developments matching current filter.
          </div>
        `;
        return;
      }}

      items.forEach((art) => {{
        const card = document.createElement('article');
        card.id = art.id;
        card.className = 'rounded-lg paper-card overflow-hidden transition scroll-mt-24';

        const categoryTag = art.section === 'vietnam' ? 'Vietnam Spotlight' : (art.section === 'global' ? 'Global Macro' : 'Medicine & Science');
        
        const factsHtml = (art.facts || []).map(f => `
          <li class="flex items-start space-x-2 text-[13.5px] sm:text-[14px] text-ink-800">
            <span class="text-ink-400 shrink-0 font-bold leading-relaxed">•</span>
            <span class="leading-relaxed font-sans">${{f}}</span>
          </li>
        `).join('');

        card.innerHTML = `
          <!-- Card Header -->
          <div class="p-4 sm:p-5 space-y-2 border-b border-[#F0EBE1]">
            <div class="flex items-center justify-between">
              <span class="text-[10.5px] font-bold text-ink-500 uppercase tracking-widest">${{categoryTag}}</span>
              <div class="flex items-center space-x-1.5">
                <span class="text-[9.5px] text-ink-400 uppercase font-semibold">Impact</span>
                <span class="px-2.5 py-0.5 rounded text-xs font-bold ${{getStampClass(art.score)}}">
                  ${{art.score.toFixed(1)}}
                </span>
              </div>
            </div>
            <h3 class="text-lg sm:text-xl font-bold font-serif-headline text-ink-900 leading-snug pt-0.5">${{art.title}}</h3>
            ${{art.sources ? `<p class="text-[11px] text-ink-500 font-serif italic">Sources: ${{art.sources}}</p>` : ''}}
          </div>

          <!-- Card Body: Facts & So What -->
          <div class="p-4 sm:p-5 space-y-4 bg-[#FCFAF6]">
            <!-- Core Facts -->
            <div>
              <span class="text-[11px] font-bold uppercase tracking-wider text-ink-600 block mb-2">Core Facts</span>
              <ul class="space-y-2">
                ${{factsHtml}}
              </ul>
            </div>

            <!-- Strategic Implication (The So What) -->
            ${{art.so_what ? `
              <div class="p-3.5 sm:p-4 rounded-md bg-[#F4EFE6] border-l-[3px] border-oxblood space-y-1.5">
                <span class="text-[10.5px] font-bold uppercase tracking-wider text-oxblood block">
                  Strategic Implication
                </span>
                <p class="text-[14px] sm:text-[14.5px] font-serif text-ink-900 leading-relaxed">${{art.so_what}}</p>
              </div>
            ` : ''}}

            <!-- Key Metric Box (Full display, No truncation) -->
            ${{art.metric ? `
              <div class="p-3 sm:p-3.5 rounded bg-white border border-[#E5DFD3] shadow-xs">
                <span class="text-[10px] font-bold uppercase tracking-wider text-oxblood block mb-1">Key Metric</span>
                <div class="font-sans font-medium text-ink-900 text-xs sm:text-[13px] leading-relaxed break-words">
                  ${{art.metric}}
                </div>
              </div>
            ` : ''}}
          </div>
        `;
        container.appendChild(card);
      }});
    }}

    function setTab(tab) {{
      currentTab = tab;
      ['all', 'vietnam', 'global', 'science', 'radar'].forEach(t => {{
        const btn = document.getElementById('tab-' + t);
        if (!btn) return;
        if (t === tab) {{
          btn.className = 'px-3.5 py-1.5 rounded-md text-xs font-semibold bg-ink-900 text-paper-50 whitespace-nowrap shadow-sm transition';
        }} else {{
          btn.className = 'px-3.5 py-1.5 rounded-md text-xs font-medium bg-[#EFEBE1] border border-[#DDD7CB] text-ink-700 hover:text-ink-900 whitespace-nowrap transition';
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

    // Register Service Worker for PWA installability
    if ('serviceWorker' in navigator) {{
      window.addEventListener('load', () => {{
        navigator.serviceWorker.register('./sw.js').catch(() => {{}});
      }});
    }}
  </script>
</body>
</html>
"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    build()
