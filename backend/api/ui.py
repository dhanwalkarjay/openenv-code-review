from fastapi.responses import HTMLResponse

def get_ui() -> HTMLResponse:
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OpenEnv Code Review — Live Demo</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: system-ui, -apple-system, sans-serif; background: #0f1117; color: #e0e0e0; min-height: 100vh; }
  
  header { background: #1a1d27; border-bottom: 1px solid #2d3148; padding: 20px 40px; display: flex; align-items: center; gap: 16px; }
  header h1 { font-size: 22px; font-weight: 600; color: #fff; }
  header p { font-size: 13px; color: #888; margin-top: 4px; }
  .badge { background: #1D9E75; color: #fff; font-size: 11px; padding: 3px 8px; border-radius: 4px; font-weight: 600; }

  .container { max-width: 1100px; margin: 0 auto; padding: 32px 24px; }

  .stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 32px; }
  .stat-card { background: #1a1d27; border: 1px solid #2d3148; border-radius: 10px; padding: 20px; text-align: center; }
  .stat-card .num { font-size: 32px; font-weight: 700; color: #7F77DD; }
  .stat-card .label { font-size: 12px; color: #888; margin-top: 4px; }

  .demo-grid { display: grid; grid-template-columns: 260px 1fr; gap: 24px; }
  
  .task-list { background: #1a1d27; border: 1px solid #2d3148; border-radius: 10px; padding: 16px; }
  .task-list h3 { font-size: 13px; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px; }
  .task-btn { width: 100%; text-align: left; background: transparent; border: 1px solid #2d3148; border-radius: 8px; padding: 12px 14px; margin-bottom: 8px; cursor: pointer; color: #e0e0e0; font-size: 13px; transition: all 0.15s; }
  .task-btn:hover { border-color: #7F77DD; background: #22253a; }
  .task-btn.active { border-color: #7F77DD; background: #22253a; color: #fff; }
  .task-btn .task-tag { font-size: 10px; color: #7F77DD; font-weight: 600; display: block; margin-bottom: 2px; }
  .task-btn .task-name { font-size: 13px; }

  .demo-panel { display: flex; flex-direction: column; gap: 16px; }

  .instruction-box { background: #1a1d27; border: 1px solid #2d3148; border-radius: 10px; padding: 20px; }
  .instruction-box .label { font-size: 11px; color: #888; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
  .instruction-box p { font-size: 15px; color: #fff; }

  .code-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  .code-box { background: #1a1d27; border: 1px solid #2d3148; border-radius: 10px; overflow: hidden; }
  .code-box .code-header { padding: 12px 16px; border-bottom: 1px solid #2d3148; display: flex; align-items: center; justify-content: space-between; }
  .code-box .code-header span { font-size: 12px; font-weight: 600; }
  .buggy-label { color: #E24B4A; }
  .fixed-label { color: #1D9E75; }
  .code-box pre { padding: 16px; font-size: 13px; font-family: 'Fira Code', 'Cascadia Code', monospace; line-height: 1.6; min-height: 140px; white-space: pre-wrap; overflow-x: auto; }

  .fix-btn { background: #7F77DD; color: #fff; border: none; border-radius: 8px; padding: 14px 28px; font-size: 15px; font-weight: 600; cursor: pointer; transition: all 0.15s; display: flex; align-items: center; gap: 10px; justify-content: center; }
  .fix-btn:hover { background: #6b63c9; }
  .fix-btn:disabled { background: #3d3d5c; cursor: not-allowed; }

  .result-box { background: #1a1d27; border: 1px solid #2d3148; border-radius: 10px; padding: 20px; display: none; }
  .result-box.show { display: block; }
  .result-box.pass { border-color: #1D9E75; }
  .result-box.fail { border-color: #E24B4A; }
  .result-header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
  .result-header .icon { font-size: 24px; }
  .result-header h3 { font-size: 16px; font-weight: 600; }
  .result-meta { display: flex; gap: 24px; }
  .result-meta .meta-item { text-align: center; }
  .result-meta .meta-val { font-size: 22px; font-weight: 700; }
  .result-meta .meta-key { font-size: 11px; color: #888; margin-top: 2px; }

  .curve-section { background: #1a1d27; border: 1px solid #2d3148; border-radius: 10px; padding: 24px; margin-top: 24px; }
  .curve-section h3 { font-size: 15px; font-weight: 600; margin-bottom: 16px; }
  .curve-section img { width: 100%; border-radius: 6px; }

  .spinner { width: 18px; height: 18px; border: 2px solid rgba(255,255,255,0.3); border-top-color: #fff; border-radius: 50%; animation: spin 0.7s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }

  .loading-dots::after { content: ''; animation: dots 1.2s steps(4, end) infinite; }
  @keyframes dots { 0%,20%{content:'.'} 40%{content:'..'} 60%{content:'...'} 80%,100%{content:''} }
</style>
</head>
<body>

<header>
  <div>
    <h1>🤖 OpenEnv Code Review</h1>
    <p>Live demo — Qwen2.5-0.5B trained with GRPO on 8 Python bug-fixing tasks</p>
  </div>
  <span class="badge">RL Trained</span>
</header>

<div class="container">

  <div class="stats-row">
    <div class="stat-card">
      <div class="num">8</div>
      <div class="label">Bug-fix tasks</div>
    </div>
    <div class="stat-card">
      <div class="num">80</div>
      <div class="label">GRPO training steps</div>
    </div>
    <div class="stat-card">
      <div class="num">0.2→1.0</div>
      <div class="label">Reward improvement</div>
    </div>
    <div class="stat-card">
      <div class="num">5/6</div>
      <div class="label">Tasks solved</div>
    </div>
  </div>

  <div class="demo-grid">
    <div class="task-list">
      <h3>Select a task</h3>
      <button class="task-btn active" onclick="selectTask('easy', this)">
        <span class="task-tag">EASY</span>
        <span class="task-name">Fix index error</span>
      </button>
      <button class="task-btn" onclick="selectTask('medium', this)">
        <span class="task-tag">MEDIUM</span>
        <span class="task-name">Fix syntax error</span>
      </button>
      <button class="task-btn" onclick="selectTask('hard', this)">
        <span class="task-tag">HARD</span>
        <span class="task-name">Division by zero</span>
      </button>
      <button class="task-btn" onclick="selectTask('bonus', this)">
        <span class="task-tag">BONUS</span>
        <span class="task-name">Off-by-one loop</span>
      </button>
      <button class="task-btn" onclick="selectTask('list_len', this)">
        <span class="task-tag">MEDIUM</span>
        <span class="task-name">Fix length check</span>
      </button>
      <button class="task-btn" onclick="selectTask('none_lower', this)">
        <span class="task-tag">HARD</span>
        <span class="task-name">Handle None</span>
      </button>
      <button class="task-btn" onclick="selectTask('max_init', this)">
        <span class="task-tag">HARD</span>
        <span class="task-name">Fix max init</span>
      </button>
      <button class="task-btn" onclick="selectTask('first_item', this)">
        <span class="task-tag">EASY</span>
        <span class="task-name">Fix first item</span>
      </button>
    </div>

    <div class="demo-panel">
      <div class="instruction-box">
        <div class="label">Task instruction</div>
        <p id="instruction">Fix the index error so the function returns the third item safely.</p>
      </div>

      <div class="code-grid">
        <div class="code-box">
          <div class="code-header">
            <span class="buggy-label">❌ Buggy code</span>
          </div>
          <pre id="buggy-code">def get_third_item(items):
    return items[3]</pre>
        </div>
        <div class="code-box">
          <div class="code-header">
            <span class="fixed-label">✅ Fixed by trained model</span>
          </div>
          <pre id="fixed-code" style="color:#888">Click "Fix with Model" to see result...</pre>
        </div>
      </div>

      <button class="fix-btn" id="fix-btn" onclick="runFix()">
        <span>⚡ Fix with Trained Model</span>
      </button>

      <div class="result-box" id="result-box">
        <div class="result-header">
          <span class="icon" id="result-icon">✅</span>
          <h3 id="result-title">All tests passed!</h3>
        </div>
        <div class="result-meta">
          <div class="meta-item">
            <div class="meta-val" id="result-reward" style="color:#7F77DD">1.0</div>
            <div class="meta-key">Reward</div>
          </div>
          <div class="meta-item">
            <div class="meta-val" id="result-tests" style="color:#1D9E75">3/3</div>
            <div class="meta-key">Tests passed</div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="curve-section">
    <h3>📈 Training reward curve — reward climbed from 0.2 → 1.0+ over 80 GRPO steps</h3>
    <img src="https://huggingface.co/dhanwalkarjay/openenv-code-review-model/resolve/main/reward_curve.png" 
         alt="GRPO reward curve showing improvement from 0.2 to 1.0" />
  </div>

</div>

<script>
  let currentTask = 'easy';

  async function selectTask(taskType, btn) {
    currentTask = taskType;
    document.querySelectorAll('.task-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('fixed-code').textContent = 'Click "Fix with Model" to see result...';
    document.getElementById('fixed-code').style.color = '#888';
    document.getElementById('result-box').classList.remove('show', 'pass', 'fail');

    try {
      const res = await fetch('/reset', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({task_type: taskType})
      });
      const data = await res.json();
      document.getElementById('instruction').textContent = data.instruction;
      document.getElementById('buggy-code').textContent = data.buggy_code;
    } catch(e) {}
  }

  async function runFix() {
    const btn = document.getElementById('fix-btn');
    btn.disabled = true;
    btn.innerHTML = '<div class="spinner"></div><span>Model is thinking<span class="loading-dots"></span></span>';

    try {
      const res = await fetch('/demo-fix', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({task_type: currentTask})
      });
      const data = await res.json();

      document.getElementById('fixed-code').textContent = data.fixed_code;
      document.getElementById('fixed-code').style.color = data.all_tests_passed ? '#1D9E75' : '#E24B4A';
      document.getElementById('result-reward').textContent = data.reward.toFixed(2);
      document.getElementById('result-tests').textContent = data.tests_passed + '/' + data.tests_total;

      const resultBox = document.getElementById('result-box');
      resultBox.classList.add('show');
      if (data.all_tests_passed) {
        resultBox.classList.add('pass');
        resultBox.classList.remove('fail');
        document.getElementById('result-icon').textContent = '✅';
        document.getElementById('result-title').textContent = 'All tests passed!';
        document.getElementById('result-tests').style.color = '#1D9E75';
      } else {
        resultBox.classList.add('fail');
        resultBox.classList.remove('pass');
        document.getElementById('result-icon').textContent = '❌';
        document.getElementById('result-title').textContent = 'Some tests failed';
        document.getElementById('result-tests').style.color = '#E24B4A';
      }
    } catch(e) {
      document.getElementById('fixed-code').textContent = 'Error: ' + e.message;
    }

    btn.disabled = false;
    btn.innerHTML = '<span>⚡ Fix with Trained Model</span>';
  }
</script>
</body>
</html>"""
    return HTMLResponse(content=html)