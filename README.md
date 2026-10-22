# 🌅 Daily Intelligence Briefing System

Automated morning executive intelligence briefing combining Global Macro, Vietnam Domestic Policy, and Medicine/Psychology breakthroughs with a 5-stage causal impact analysis.

---

## 📱 Mobile Web App UI (Full Design Control)

The dashboard is built as a **Progressive Web App (PWA)** in [`web/index.html`](file:///e:/Work/Antigravity/Daily%20nws/web/index.html) using Tailwind CSS.

### Key UI Features
* **Bilingual Multi-Track Feed**: Dedicated filter tabs for **All Feed**, **🇻🇳 Việt Nam**, **🌐 Global Macro**, **🔬 Science & Med**, and **⚡ Radar Skim**.
* **Impact Badges**: Color-coded severity pills (`🔴 Tier 1 (8.5+)`, `🟠 Tier 2 (7.0+)`, `🟡 Tier 3 (5.0+)`).
* **Deep Analysis Accordions**: Each story displays verified facts, second- and third-order consequence mapping (*The "So What?"*), and critical key metrics.
* **Instant Keyword Filter**: Search bar for fast skimming (e.g. *GDP*, *SBV*, *Fed*, *Nobel*).
* **Install to Phone Home Screen**:
  1. Open the dashboard URL in Safari (iOS) or Chrome (Android).
  2. Tap **Share** (iOS) or the three-dot menu (Android) $\rightarrow$ **"Add to Home Screen"**.
  3. Launches full-screen like a native app without a browser URL bar.

### Customizing the UI
You have 100% control over the styling and layout:
* Edit [`web/index.html`](file:///e:/Work/Antigravity/Daily%20nws/web/index.html) to tweak colors, typography, or cards.
* Re-run `python scripts/build_dashboard.py` at any time to regenerate the UI from the latest Markdown brief.

---

## 🔔 Instant Phone Notifications (Zero Account Required)

1. Install the free **ntfy** app on your phone ([iOS App Store](https://apps.apple.com/app/ntfy/id1625396347) / [Google Play](https://play.google.com/store/apps/details?id=io.heckel.ntfy)).
2. Tap **"+"** and subscribe to:
   ```
   hung-daily-intel-melbourne
   ```
3. Whenever the briefing runs at 6:30 AM, your phone receives a high-priority push notification. Tapping it opens your custom web dashboard.
*(You can customize this topic or switch to a Telegram bot in [`config/notify_config.json`](file:///e:/Work/Antigravity/Daily%20nws/config/notify_config.json)).*

---

## ⏰ Schedule & Automation

* **Schedule**: Every morning at **6:30 AM Melbourne Time** (`CRON_TZ=Australia/Melbourne 30 6 * * *`).
* **Execution Flow**:
  1. Multi-Vector Parallel Scouting (Global + Vietnam + Science + Anomaly).
  2. 5-Stage Causal Impact Reasoning & Scoring.
  3. Archives Markdown brief to [`briefs/YYYY-MM-DD.md`](file:///e:/Work/Antigravity/Daily%20nws/briefs/).
  4. Generates updated PWA web dashboard in [`web/index.html`](file:///e:/Work/Antigravity/Daily%20nws/web/index.html).
  5. Sends lock-screen push notification to your phone.
