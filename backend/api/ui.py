from fastapi.responses import HTMLResponse


def get_ui() -> HTMLResponse:
    html = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OpenEnv — RL Code Repair Agent</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Syne:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
:root {
  --bg:       #080b10;
  --surface:  #0e1219;
  --card:     #131920;
  --border:   #1e2a38;
  --border2:  #243040;
  --accent:   #00d4ff;
  --accent2:  #7c3aed;
  --green:    #10b981;
  --red:      #ef4444;
  --yellow:   #f59e0b;
  --text:     #e2e8f0;
  --muted:    #64748b;
  --mono:     'JetBrains Mono', monospace;
  --sans:     'Syne', sans-serif;
}

* { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body {
  font-family: var(--sans);
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  overflow-x: hidden;
}

/* Grid noise texture overlay */
body::before {
  content: '';
  position: fixed;
  inset: 0;
  background-image:
    linear-gradient(rgba(0,212,255,0.015) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,212,255,0.015) 1px, transparent 1px);
  background-size: 40px 40px;
  pointer-events: none;
  z-index: 0;
}

/* ── HEADER ── */
header {
  position: relative;
  z-index: 10;
  padding: 0 40px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border);
  background: rgba(8,11,16,0.9);
  backdrop-filter: blur(12px);
}
.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 16px;
  font-weight: 800;
  letter-spacing: -0.3px;
  color: #fff;
}
.logo-dot {
  width: 8px; height: 8px;
  background: var(--accent);
  border-radius: 50%;
  box-shadow: 0 0 12px var(--accent);
  animation: pulse-dot 2s ease-in-out infinite;
}
@keyframes pulse-dot {
  0%,100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(0.8); }
}
.header-tags { display: flex; gap: 8px; }
.tag {
  font-family: var(--mono);
  font-size: 10px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 4px;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}
.tag-blue { background: rgba(0,212,255,0.1); color: var(--accent); border: 1px solid rgba(0,212,255,0.2); }
.tag-purple { background: rgba(124,58,237,0.1); color: #a78bfa; border: 1px solid rgba(124,58,237,0.2); }
.tag-green { background: rgba(16,185,129,0.1); color: var(--green); border: 1px solid rgba(16,185,129,0.2); }

/* ── HERO ── */
.hero {
  position: relative;
  z-index: 1;
  padding: 60px 40px 40px;
  max-width: 1200px;
  margin: 0 auto;
}
.hero-label {
  font-family: var(--mono);
  font-size: 11px;
  color: var(--accent);
  letter-spacing: 2px;
  text-transform: uppercase;
  margin-bottom: 16px;
}
.hero h1 {
  font-size: clamp(28px, 4vw, 48px);
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: -1px;
  color: #fff;
  margin-bottom: 16px;
}
.hero h1 span {
  background: linear-gradient(135deg, var(--accent), var(--accent2));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.hero-sub {
  font-size: 15px;
  color: var(--muted);
  max-width: 600px;
  line-height: 1.7;
  margin-bottom: 32px;
}

/* ── RL LOOP DIAGRAM ── */
.rl-loop {
  display: flex;
  align-items: center;
  gap: 0;
  margin-bottom: 48px;
  flex-wrap: wrap;
  gap: 4px;
}
.rl-node {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px 16px;
  font-family: var(--mono);
  font-size: 11px;
  font-weight: 600;
  color: var(--text);
  white-space: nowrap;
}
.rl-node.accent { border-color: rgba(0,212,255,0.4); color: var(--accent); }
.rl-node.purple { border-color: rgba(124,58,237,0.4); color: #a78bfa; }
.rl-node.green  { border-color: rgba(16,185,129,0.4); color: var(--green); }
.rl-arrow {
  font-size: 16px;
  color: var(--border2);
  padding: 0 4px;
}

/* ── STATS ── */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 40px;
  max-width: 1200px;
  margin-left: auto;
  margin-right: auto;
  padding: 0 40px;
  position: relative;
  z-index: 1;
}
.stat {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px 24px;
  position: relative;
  overflow: hidden;
}
.stat::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, var(--accent), var(--accent2));
}
.stat-val {
  font-family: var(--mono);
  font-size: 28px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 4px;
}
.stat-key {
  font-size: 12px;
  color: var(--muted);
  font-weight: 600;
}

/* ── MAIN LAYOUT ── */
.main {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 40px 60px;
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 24px;
  position: relative;
  z-index: 1;
}

/* ── TASK SIDEBAR ── */
.sidebar {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.sidebar-label {
  font-family: var(--mono);
  font-size: 10px;
  color: var(--muted);
  letter-spacing: 1.5px;
  text-transform: uppercase;
  margin-bottom: 4px;
  padding: 0 4px;
}
.task-btn {
  width: 100%;
  text-align: left;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 12px 14px;
  cursor: pointer;
  color: var(--text);
  transition: all 0.15s;
  position: relative;
  overflow: hidden;
}
.task-btn::before {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 3px;
  background: var(--accent);
  transform: scaleY(0);
  transition: transform 0.15s;
  border-radius: 0 2px 2px 0;
}
.task-btn:hover { border-color: var(--border2); background: #161e2a; }
.task-btn:hover::before { transform: scaleY(1); }
.task-btn.active { border-color: rgba(0,212,255,0.3); background: rgba(0,212,255,0.05); }
.task-btn.active::before { transform: scaleY(1); }
.task-difficulty {
  font-family: var(--mono);
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 1px;
  text-transform: uppercase;
  margin-bottom: 3px;
}
.diff-easy { color: var(--green); }
.diff-medium { color: var(--yellow); }
.diff-hard { color: var(--red); }
.task-name {
  font-size: 12px;
  font-weight: 600;
  color: #cbd5e1;
}

/* ── DEMO PANEL ── */
.panel { display: flex; flex-direction: column; gap: 16px; }

.instruction-bar {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px 20px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
}
.instruction-icon { font-size: 18px; flex-shrink: 0; margin-top: 1px; }
.instruction-text { font-size: 14px; color: #94a3b8; line-height: 1.5; }
.instruction-text strong { color: #fff; font-weight: 700; }

/* ── CODE SECTION ── */
.code-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.code-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
}
.code-card-header {
  padding: 10px 16px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(255,255,255,0.02);
}
.code-card-title {
  font-family: var(--mono);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}
.title-buggy { color: var(--red); }
.title-fixed { color: var(--green); }
.dot-row { display: flex; gap: 5px; }
.dot { width: 8px; height: 8px; border-radius: 50%; }
.dot-r { background: #ff5f57; }
.dot-y { background: #febc2e; }
.dot-g { background: #28c840; }

code, pre {
  font-family: var(--mono);
  font-size: 12.5px;
  line-height: 1.7;
}
.code-body {
  padding: 16px;
  min-height: 120px;
  white-space: pre-wrap;
  word-break: break-word;
}
.code-body.muted { color: var(--muted); font-style: italic; }
.code-body.buggy { color: #fca5a5; }
.code-body.fixed { color: #6ee7b7; }

/* ── RUN BUTTON ── */
.run-btn {
  background: linear-gradient(135deg, var(--accent), #0099cc);
  color: #000;
  border: none;
  border-radius: 10px;
  padding: 15px 28px;
  font-family: var(--sans);
  font-size: 14px;
  font-weight: 800;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  transition: all 0.15s;
  letter-spacing: 0.3px;
  position: relative;
  overflow: hidden;
}
.run-btn::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255,255,255,0.2), transparent);
  opacity: 0;
  transition: opacity 0.15s;
}
.run-btn:hover::after { opacity: 1; }
.run-btn:hover { transform: translateY(-1px); box-shadow: 0 8px 24px rgba(0,212,255,0.3); }
.run-btn:disabled { background: #1e2a38; color: var(--muted); cursor: not-allowed; transform: none; box-shadow: none; }
.run-btn:disabled::after { display: none; }

/* ── EPISODE STEPS ── */
.episode-section {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
}
.episode-header {
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(255,255,255,0.02);
}
.episode-title {
  font-family: var(--mono);
  font-size: 11px;
  font-weight: 700;
  color: var(--muted);
  letter-spacing: 1px;
  text-transform: uppercase;
}
.step-counter {
  font-family: var(--mono);
  font-size: 11px;
  color: var(--accent);
}
.episode-body { padding: 16px; display: flex; flex-direction: column; gap: 12px; }

.step-row {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
  opacity: 0;
  transform: translateY(8px);
  transition: all 0.3s ease;
}
.step-row.visible { opacity: 1; transform: translateY(0); }
.step-row-header {
  padding: 8px 14px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 10px;
}
.step-num {
  font-family: var(--mono);
  font-size: 10px;
  font-weight: 700;
  color: var(--muted);
  background: rgba(255,255,255,0.05);
  padding: 2px 8px;
  border-radius: 4px;
}
.step-reward-badge {
  font-family: var(--mono);
  font-size: 11px;
  font-weight: 700;
  padding: 2px 10px;
  border-radius: 4px;
}
.badge-good { background: rgba(16,185,129,0.15); color: var(--green); border: 1px solid rgba(16,185,129,0.3); }
.badge-mid  { background: rgba(245,158,11,0.15);  color: var(--yellow); border: 1px solid rgba(245,158,11,0.3); }
.badge-bad  { background: rgba(239,68,68,0.15);   color: var(--red); border: 1px solid rgba(239,68,68,0.3); }
.step-tests {
  font-family: var(--mono);
  font-size: 10px;
  color: var(--muted);
  margin-left: auto;
}
.step-code {
  padding: 10px 14px;
  font-family: var(--mono);
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  color: #94a3b8;
}

/* ── REWARD GRAPH ── */
.graph-section {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
}
.graph-header {
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(255,255,255,0.02);
}
.graph-title {
  font-family: var(--mono);
  font-size: 11px;
  font-weight: 700;
  color: var(--muted);
  letter-spacing: 1px;
  text-transform: uppercase;
}
.graph-body { padding: 20px; }
canvas { width: 100%; border-radius: 6px; }

/* ── TRAINING CURVE ── */
.training-section {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
  grid-column: 1 / -1;
}
.training-header {
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
  background: rgba(255,255,255,0.02);
  display: flex;
  align-items: center;
  gap: 12px;
}
.training-title {
  font-family: var(--mono);
  font-size: 11px;
  font-weight: 700;
  color: var(--muted);
  letter-spacing: 1px;
  text-transform: uppercase;
}
.live-badge {
  font-family: var(--mono);
  font-size: 9px;
  font-weight: 700;
  background: rgba(16,185,129,0.15);
  color: var(--green);
  border: 1px solid rgba(16,185,129,0.3);
  padding: 2px 8px;
  border-radius: 4px;
  letter-spacing: 1px;
  display: flex;
  align-items: center;
  gap: 5px;
}
.live-dot {
  width: 5px; height: 5px;
  background: var(--green);
  border-radius: 50%;
  animation: blink 1s ease-in-out infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.2} }
.training-body { padding: 20px; }
.training-body img { width: 100%; border-radius: 8px; border: 1px solid var(--border); }

/* ── FINAL RESULT ── */
.final-result {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  display: none;
  align-items: center;
  gap: 20px;
}
.final-result.show { display: flex; }
.final-result.pass { border-color: rgba(16,185,129,0.4); background: rgba(16,185,129,0.05); }
.final-result.fail { border-color: rgba(245,158,11,0.4); background: rgba(245,158,11,0.05); }
.final-icon { font-size: 32px; }
.final-text h3 { font-size: 16px; font-weight: 700; color: #fff; margin-bottom: 4px; }
.final-text p { font-size: 13px; color: var(--muted); }
.final-metrics { display: flex; gap: 24px; margin-left: auto; }
.final-metric { text-align: center; }
.final-metric .val {
  font-family: var(--mono);
  font-size: 24px;
  font-weight: 700;
  color: var(--accent);
}
.final-metric .key { font-size: 11px; color: var(--muted); margin-top: 2px; }

/* ── SPINNER ── */
.spinner {
  width: 16px; height: 16px;
  border: 2px solid rgba(0,0,0,0.3);
  border-top-color: #000;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 768px) {
  header { padding: 0 20px; }
  .hero, .stats-row, .main { padding-left: 20px; padding-right: 20px; }
  .stats-row { grid-template-columns: repeat(2, 1fr); }
  .main { grid-template-columns: 1fr; }
  .code-section { grid-template-columns: 1fr; }
}
</style>
</head>
<body>

<header>
  <div class="logo">
    <div class="logo-dot"></div>
    OpenEnv — RL Code Repair
  </div>
  <div class="header-tags">
    <span class="tag tag-blue">GRPO</span>
    <span class="tag tag-purple">Qwen 2.5-0.5B</span>
    <span class="tag tag-green">Live RL Agent</span>
  </div>
</header>

<div class="hero">
  <div class="hero-label">// Reinforcement Learning Demo</div>
  <h1>An agent that <span>learns to fix code</span><br>through trial and reward</h1>
  <p class="hero-sub">
    Watch the RL agent run a full multi-step episode — attempting fixes,
    receiving verifiable rewards from real test execution, and refining its approach.
    Not static output. A live decision loop.
  </p>

  <div class="rl-loop">
    <div class="rl-node accent">Buggy Code</div>
    <div class="rl-arrow">→</div>
    <div class="rl-node">Agent Action</div>
    <div class="rl-arrow">→</div>
    <div class="rl-node purple">Run Tests</div>
    <div class="rl-arrow">→</div>
    <div class="rl-node">Compute Reward</div>
    <div class="rl-arrow">→</div>
    <div class="rl-node green">Update Policy</div>
    <div class="rl-arrow">→</div>
    <div class="rl-node accent">Better Fix</div>
  </div>
</div>

<div class="stats-row">
  <div class="stat">
    <div class="stat-val">0.2→1.0</div>
    <div class="stat-key">Reward improvement over training</div>
  </div>
  <div class="stat">
    <div class="stat-val">80</div>
    <div class="stat-key">GRPO training steps</div>
  </div>
  <div class="stat">
    <div class="stat-val">8</div>
    <div class="stat-key">Unique bug-fix tasks</div>
  </div>
  <div class="stat">
    <div class="stat-val">3×</div>
    <div class="stat-key">Independent reward signals</div>
  </div>
</div>

<div class="main">

  <!-- SIDEBAR -->
  <div class="sidebar">
    <div class="sidebar-label">Select task</div>

    <button class="task-btn active" onclick="selectTask('easy', this)">
      <div class="task-difficulty diff-easy">Easy</div>
      <div class="task-name">Fix index error</div>
    </button>
    <button class="task-btn" onclick="selectTask('medium', this)">
      <div class="task-difficulty diff-medium">Medium</div>
      <div class="task-name">Fix syntax error</div>
    </button>
    <button class="task-btn" onclick="selectTask('hard', this)">
      <div class="task-difficulty diff-hard">Hard</div>
      <div class="task-name">Division by zero</div>
    </button>
    <button class="task-btn" onclick="selectTask('bonus', this)">
      <div class="task-difficulty diff-medium">Bonus</div>
      <div class="task-name">Off-by-one loop</div>
    </button>
    <button class="task-btn" onclick="selectTask('list_len', this)">
      <div class="task-difficulty diff-medium">Medium</div>
      <div class="task-name">Fix length check</div>
    </button>
    <button class="task-btn" onclick="selectTask('none_lower', this)">
      <div class="task-difficulty diff-hard">Hard</div>
      <div class="task-name">Handle None</div>
    </button>
    <button class="task-btn" onclick="selectTask('max_init', this)">
      <div class="task-difficulty diff-hard">Hard</div>
      <div class="task-name">Fix max init</div>
    </button>
    <button class="task-btn" onclick="selectTask('first_item', this)">
      <div class="task-difficulty diff-easy">Easy</div>
      <div class="task-name">Fix first item</div>
    </button>
  </div>

  <!-- MAIN PANEL -->
  <div class="panel">

    <!-- Instruction -->
    <div class="instruction-bar">
      <div class="instruction-icon">🎯</div>
      <div class="instruction-text">
        <strong>Task:</strong>
        <span id="instruction-text">Fix the index error so the function returns the third item safely.</span>
      </div>
    </div>

    <!-- Code side by side -->
    <div class="code-section">
      <div class="code-card">
        <div class="code-card-header">
          <div class="dot-row"><div class="dot dot-r"></div><div class="dot dot-y"></div><div class="dot dot-g"></div></div>
          <span class="code-card-title title-buggy">❌ Buggy Input</span>
        </div>
        <pre class="code-body buggy" id="buggy-display">def get_third_item(items):
    return items[3]</pre>
      </div>
      <div class="code-card">
        <div class="code-card-header">
          <div class="dot-row"><div class="dot dot-r"></div><div class="dot dot-y"></div><div class="dot dot-g"></div></div>
          <span class="code-card-title title-fixed">✅ Agent Output</span>
        </div>
        <pre class="code-body muted" id="fixed-display">Waiting for agent to run...</pre>
      </div>
    </div>

    <!-- Run button -->
    <button class="run-btn" id="run-btn" onclick="runEpisode()">
      <span id="run-icon">⚡</span>
      <span id="run-label">Run RL Episode</span>
    </button>

    <!-- Episode steps -->
    <div class="episode-section">
      <div class="episode-header">
        <span class="episode-title">// Episode Steps</span>
        <span class="step-counter" id="step-counter">0 / 3 steps</span>
      </div>
      <div class="episode-body" id="episode-body">
        <div style="font-family: var(--mono); font-size: 12px; color: var(--muted); text-align: center; padding: 24px;">
          Run an episode to see the agent's step-by-step decisions
        </div>
      </div>
    </div>

    <!-- Live reward graph for this episode -->
    <div class="graph-section">
      <div class="graph-header">
        <span class="graph-title">// Episode Reward Trajectory</span>
        <div class="live-badge"><div class="live-dot"></div>LIVE</div>
      </div>
      <div class="graph-body">
        <canvas id="episode-chart" height="140"></canvas>
      </div>
    </div>

    <!-- Final result -->
    <div class="final-result" id="final-result">
      <div class="final-icon" id="final-icon">✅</div>
      <div class="final-text">
        <h3 id="final-title">Agent solved the task!</h3>
        <p id="final-sub">All test cases passed after multi-step refinement</p>
      </div>
      <div class="final-metrics">
        <div class="final-metric">
          <div class="val" id="final-reward">1.0</div>
          <div class="key">Final reward</div>
        </div>
        <div class="final-metric">
          <div class="val" id="final-tests" style="color:var(--green)">3/3</div>
          <div class="key">Tests passed</div>
        </div>
      </div>
    </div>

    <!-- Training curve from real run -->
    <div class="training-section">
      <div class="training-header">
        <span class="training-title">// GRPO Training Run — Reward over 80 Steps</span>
        <div class="live-badge"><div class="live-dot"></div>REAL RUN</div>
      </div>
      <div class="training-body">
        <img
          src="https://huggingface.co/dhanwalkarjay/openenv-code-review-model/resolve/main/reward_curve.png"
          alt="GRPO reward curve — reward climbed from 0.2 to 1.0 over 80 training steps"
          onerror="this.style.display='none'; this.nextElementSibling.style.display='block';"
        />
        <div style="display:none; font-family:var(--mono); font-size:12px; color:var(--muted); padding:40px; text-align:center; border: 1px dashed var(--border); border-radius:8px;">
          Reward curve image loading... visit the model repo to see it.
        </div>
      </div>
    </div>

  </div><!-- end panel -->
</div><!-- end main -->

<script>
// ── State ──────────────────────────────────────────────────────────────────
let currentTask = 'easy';
let episodeRewards = [];
let chartCtx = null;

// Known correct fixes as fallback when model inference is slow
const KNOWN_FIXES = {
  easy:      "def get_third_item(items):\n    return items[2]",
  medium:    "def greet(name):\n    return 'hi ' + name",
  hard:      "def safe_div(a, b):\n    if b == 0:\n        return 0\n    return a / b",
  bonus:     "def sum_to_n(n):\n    return sum(range(n + 1))",
  list_len:  "def has_three(items):\n    return len(items) >= 3",
  none_lower:"def normalize_name(name):\n    if name is None:\n        return ''\n    return name.lower()",
  max_init:  "def max_value(nums):\n    best = nums[0]\n    for n in nums:\n        if n > best:\n            best = n\n    return best",
  first_item:"def first_item(items):\n    return items[0]",
};

// Simulate 3-step refinement progression for richer demo
const STEP_PROGRESSIONS = {
  easy: [
    { code: "def get_third_item(items):\n    return items[3]", note: "Initial attempt (unchanged)" },
    { code: "def get_third_item(items):\n    if len(items) > 2:\n        return items[3]", note: "Added guard but index still wrong" },
    { code: "def get_third_item(items):\n    return items[2]", note: "Corrected index to 2" },
  ],
  medium: [
    { code: "def greet(name)\n    return 'hi ' + name", note: "Initial (syntax error)" },
    { code: "def greet(name)  :\n    return 'hi ' + name", note: "Partial fix — extra space" },
    { code: "def greet(name):\n    return 'hi ' + name", note: "Correct colon added" },
  ],
  hard: [
    { code: "def safe_div(a, b):\n    return a / b", note: "Initial (no guard)" },
    { code: "def safe_div(a, b):\n    try:\n        return a / b\n    except:\n        pass", note: "Try/except but returns None" },
    { code: "def safe_div(a, b):\n    if b == 0:\n        return 0\n    return a / b", note: "Explicit guard — correct" },
  ],
  bonus: [
    { code: "def sum_to_n(n):\n    total = 0\n    for i in range(n):\n        total += i\n    return total", note: "Initial (off by one)" },
    { code: "def sum_to_n(n):\n    total = 0\n    for i in range(n+1):\n        total += i\n    return total", note: "Fixed range" },
    { code: "def sum_to_n(n):\n    return sum(range(n + 1))", note: "Elegant rewrite" },
  ],
  list_len: [
    { code: "def has_three(items):\n    return len(items) > 3", note: "Initial (> instead of >=)" },
    { code: "def has_three(items):\n    return len(items) > 2", note: "Changed threshold" },
    { code: "def has_three(items):\n    return len(items) >= 3", note: "Correct operator" },
  ],
  none_lower: [
    { code: "def normalize_name(name):\n    return name.lower()", note: "Initial (no None check)" },
    { code: "def normalize_name(name):\n    if name:\n        return name.lower()\n    return None", note: "Partial — returns None not ''" },
    { code: "def normalize_name(name):\n    if name is None:\n        return ''\n    return name.lower()", note: "Correct None check" },
  ],
  max_init: [
    { code: "def max_value(nums):\n    best = 0\n    for n in nums:\n        if n > best:\n            best = n\n    return best", note: "Initial (best=0 fails for negatives)" },
    { code: "def max_value(nums):\n    best = -999\n    for n in nums:\n        if n > best:\n            best = n\n    return best", note: "Hardcoded -999 — fragile" },
    { code: "def max_value(nums):\n    best = nums[0]\n    for n in nums:\n        if n > best:\n            best = n\n    return best", note: "Correct initialisation" },
  ],
  first_item: [
    { code: "def first_item(items):\n    return items[1]", note: "Initial (index 1 not 0)" },
    { code: "def first_item(items):\n    return items[-1]", note: "Wrong — last item" },
    { code: "def first_item(items):\n    return items[0]", note: "Correct index 0" },
  ],
};

// ── Canvas chart ────────────────────────────────────────────────────────────
function initChart() {
  const canvas = document.getElementById('episode-chart');
  chartCtx = canvas.getContext('2d');
  canvas.width = canvas.offsetWidth * window.devicePixelRatio || 600;
  canvas.height = 140 * (window.devicePixelRatio || 1);
  canvas.style.width = '100%';
  canvas.style.height = '140px';
  drawChart([]);
}

function drawChart(rewards) {
  const canvas = document.getElementById('episode-chart');
  const ctx = chartCtx;
  if (!ctx) return;
  const W = canvas.width, H = canvas.height;
  const dpr = window.devicePixelRatio || 1;
  ctx.clearRect(0, 0, W, H);

  // Background
  ctx.fillStyle = '#0e1219';
  ctx.fillRect(0, 0, W, H);

  const pad = { t: 20*dpr, r: 20*dpr, b: 36*dpr, l: 52*dpr };
  const cW = W - pad.l - pad.r;
  const cH = H - pad.t - pad.b;

  // Grid lines
  ctx.strokeStyle = '#1e2a38';
  ctx.lineWidth = dpr;
  for (let i = 0; i <= 4; i++) {
    const y = pad.t + (cH / 4) * i;
    ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(pad.l + cW, y); ctx.stroke();
    const val = (1.0 - i * 0.25).toFixed(2);
    ctx.fillStyle = '#64748b';
    ctx.font = `${10*dpr}px JetBrains Mono, monospace`;
    ctx.textAlign = 'right';
    ctx.fillText(val, pad.l - 8*dpr, y + 4*dpr);
  }

  // Zero line
  const zeroY = pad.t + cH * (1.0 / 1.0);
  ctx.strokeStyle = 'rgba(100,116,139,0.3)';
  ctx.setLineDash([4*dpr, 4*dpr]);
  ctx.beginPath(); ctx.moveTo(pad.l, zeroY); ctx.lineTo(pad.l + cW, zeroY); ctx.stroke();
  ctx.setLineDash([]);

  if (rewards.length < 2) {
    // Placeholder text
    ctx.fillStyle = '#334155';
    ctx.font = `${11*dpr}px JetBrains Mono, monospace`;
    ctx.textAlign = 'center';
    ctx.fillText('Episode rewards will appear here', W/2, H/2);
    return;
  }

  // Map reward to y (range -1 to 1.2)
  const minR = -1, maxR = 1.2;
  const toY = r => pad.t + cH * (1 - (r - minR) / (maxR - minR));
  const toX = i => pad.l + (cW / (rewards.length - 1)) * i;

  // Gradient fill
  const grad = ctx.createLinearGradient(0, pad.t, 0, pad.t + cH);
  grad.addColorStop(0, 'rgba(0,212,255,0.3)');
  grad.addColorStop(1, 'rgba(0,212,255,0.0)');
  ctx.beginPath();
  ctx.moveTo(toX(0), toY(rewards[0]));
  rewards.forEach((r, i) => { if (i > 0) ctx.lineTo(toX(i), toY(r)); });
  ctx.lineTo(toX(rewards.length-1), pad.t + cH);
  ctx.lineTo(toX(0), pad.t + cH);
  ctx.closePath();
  ctx.fillStyle = grad;
  ctx.fill();

  // Line
  ctx.strokeStyle = '#00d4ff';
  ctx.lineWidth = 2.5 * dpr;
  ctx.lineJoin = 'round';
  ctx.beginPath();
  ctx.moveTo(toX(0), toY(rewards[0]));
  rewards.forEach((r, i) => { if (i > 0) ctx.lineTo(toX(i), toY(r)); });
  ctx.stroke();

  // Dots + labels
  rewards.forEach((r, i) => {
    const x = toX(i), y = toY(r);
    ctx.beginPath();
    ctx.arc(x, y, 5*dpr, 0, Math.PI*2);
    ctx.fillStyle = r >= 1.0 ? '#10b981' : r >= 0.5 ? '#f59e0b' : '#ef4444';
    ctx.fill();
    ctx.strokeStyle = '#0e1219';
    ctx.lineWidth = 1.5*dpr;
    ctx.stroke();

    ctx.fillStyle = '#e2e8f0';
    ctx.font = `bold ${10*dpr}px JetBrains Mono, monospace`;
    ctx.textAlign = 'center';
    ctx.fillText(r.toFixed(2), x, y - 10*dpr);

    ctx.fillStyle = '#64748b';
    ctx.font = `${9*dpr}px JetBrains Mono, monospace`;
    ctx.fillText(`step ${i+1}`, x, pad.t + cH + 20*dpr);
  });
}

// ── Task selection ──────────────────────────────────────────────────────────
async function selectTask(taskType, btn) {
  currentTask = taskType;
  document.querySelectorAll('.task-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');

  // Reset UI
  document.getElementById('fixed-display').textContent = 'Waiting for agent to run...';
  document.getElementById('fixed-display').className = 'code-body muted';
  document.getElementById('episode-body').innerHTML = `
    <div style="font-family:var(--mono);font-size:12px;color:var(--muted);text-align:center;padding:24px;">
      Run an episode to see the agent's step-by-step decisions
    </div>`;
  document.getElementById('step-counter').textContent = '0 / 3 steps';
  document.getElementById('final-result').className = 'final-result';
  episodeRewards = [];
  drawChart([]);

  try {
    const res = await fetch('/reset', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({task_type: taskType})
    });
    const data = await res.json();
    document.getElementById('buggy-display').textContent = data.buggy_code || '';
    document.getElementById('instruction-text').textContent = data.instruction || '';
  } catch(e) {}
}

// ── Run episode ─────────────────────────────────────────────────────────────
async function runEpisode() {
  const btn = document.getElementById('run-btn');
  btn.disabled = true;
  btn.innerHTML = '<div class="spinner"></div><span id="run-label">Agent running episode...</span>';

  document.getElementById('episode-body').innerHTML = '';
  document.getElementById('step-counter').textContent = '0 / 3 steps';
  document.getElementById('final-result').className = 'final-result';
  document.getElementById('fixed-display').textContent = 'Agent thinking...';
  document.getElementById('fixed-display').className = 'code-body muted';
  episodeRewards = [];
  drawChart([]);

  let lastReward = 0;
  let lastTests = '0/0';
  let lastCode = '';

  try {
    const episodeRes = await fetch('/run-rl-episode', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({task_type: currentTask, max_steps: 3})
    });
    const episodeData = await episodeRes.json();

    const history = Array.isArray(episodeData.history) ? episodeData.history : [];
    for (const item of history) {
      const reward = Number(item.reward ?? 0);
      const testsPassed = Number(item.tests_passed ?? 0);
      const testsTotal = Number(item.tests_total ?? 0);
      const outputCode = item.output_code || item.candidate_code || '';
      const mode = item.source === 'policy'
        ? `policy update (${item.action_id}) | epsilon=${Number(item.epsilon ?? 0).toFixed(3)}`
        : `model output | temp=${Number(item.temperature ?? 0).toFixed(2)}`;

      episodeRewards.push(reward);
      lastReward = reward;
      lastTests = `${testsPassed}/${testsTotal}`;
      lastCode = outputCode;

      addStepRow(item.step || (episodeRewards.length), outputCode, reward, testsPassed, testsTotal, mode);
      document.getElementById('step-counter').textContent = `${episodeRewards.length} / 3 steps`;
      drawChart([...episodeRewards]);
    }

    if (!history.length) {
      addStepRow(1, '', 0, 0, 0, 'episode returned no steps');
      document.getElementById('step-counter').textContent = '0 / 3 steps';
    }
  } catch (e) {
    addStepRow(1, '', 0, 0, 0, 'episode call failed');
    document.getElementById('step-counter').textContent = '0 / 3 steps';
  }

  // Show final code in output panel
  document.getElementById('fixed-display').textContent = lastCode;
  document.getElementById('fixed-display').className = 'code-body fixed';

  // Final result banner
  const finalEl = document.getElementById('final-result');
  const solved = lastReward >= 1.0 || lastTests.split('/')[0] === lastTests.split('/')[1];
  finalEl.className = `final-result show ${solved ? 'pass' : 'fail'}`;
  document.getElementById('final-icon').textContent = solved ? '✅' : '⚠️';
  document.getElementById('final-title').textContent = solved ? 'Agent solved the task!' : 'Agent made progress';
  document.getElementById('final-sub').textContent = solved
    ? 'All tests passed using real action → reward → policy update loop.'
    : 'Partial progress from real RL-style episode loop.';
  document.getElementById('final-reward').textContent = lastReward.toFixed(2);
  document.getElementById('final-tests').textContent = lastTests;

  btn.disabled = false;
  btn.innerHTML = '<span>⚡</span><span>Run RL Episode Again</span>';
}

function addStepRow(stepNum, code, reward, passed, total, note) {
  const body = document.getElementById('episode-body');
  const badgeClass = reward >= 1.0 ? 'badge-good' : reward >= 0.3 ? 'badge-mid' : 'badge-bad';
  const rewardLabel = reward >= 0 ? `+${reward.toFixed(2)}` : reward.toFixed(2);

  const row = document.createElement('div');
  row.className = 'step-row';
  row.innerHTML = `
    <div class="step-row-header">
      <span class="step-num">STEP ${stepNum}</span>
      <span class="step-reward-badge ${badgeClass}">reward ${rewardLabel}</span>
      <span class="step-tests">${passed}/${total} tests</span>
    </div>
    <div class="step-code">${escapeHtml(code)}<br><span style="color:#475569;font-size:11px;">// ${note}</span></div>
  `;
  body.appendChild(row);
  requestAnimationFrame(() => row.classList.add('visible'));
}

function escapeHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ── Init ───────────────────────────────────────────────────────────────────
window.addEventListener('load', () => {
  initChart();
  // Load first task
  fetch('/reset', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({task_type: 'easy'})
  }).then(r => r.json()).then(data => {
    document.getElementById('buggy-display').textContent = data.buggy_code || '';
    document.getElementById('instruction-text').textContent = data.instruction || '';
  }).catch(() => {});
});

window.addEventListener('resize', () => {
  initChart();
  drawChart([...episodeRewards]);
});
</script>

</body>
</html>"""
    return HTMLResponse(content=html)