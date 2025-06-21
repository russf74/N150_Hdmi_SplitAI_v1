from flask import Flask, send_from_directory, jsonify, render_template_string, request
import os
import json
import subprocess

app = Flask(__name__)

STATE_PATH = os.path.join(os.path.dirname(__file__), "output", "state.json")
PAUSE_PATH = os.path.join(os.path.dirname(__file__), "output", "pause_state.json")

HTML_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Processor Monitor</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f7f7f7; color: #222; margin: 0; padding: 0; }
        .container { max-width: 700px; margin: 40px auto; background: #fff; border-radius: 10px; box-shadow: 0 2px 8px #0001; padding: 32px; }
        h1 { text-align: center; }
        .leds { display: flex; justify-content: center; margin: 20px 0; }
        .toggle-section { text-align: center; margin-bottom: 24px; }
        .toggle-switch { position: relative; display: inline-block; width: 60px; height: 34px; }
        .toggle-switch input { opacity: 0; width: 0; height: 0; }
        .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #ccc; transition: .4s; border-radius: 34px; }
        .slider:before { position: absolute; content: ""; height: 26px; width: 26px; left: 4px; bottom: 4px; background-color: white; transition: .4s; border-radius: 50%; }
        input:checked + .slider { background-color: #2196F3; }
        input:checked + .slider:before { transform: translateX(26px); }
        .toggle-label { margin-left: 12px; font-size: 1.1em; }
        body { font-family: Arial, sans-serif; background: #f7f7f7; color: #222; margin: 0; padding: 0; }
        .container { max-width: 700px; margin: 40px auto; background: #fff; border-radius: 10px; box-shadow: 0 2px 8px #0001; padding: 32px; }
        h1 { text-align: center; }
        .leds { display: flex; justify-content: center; margin: 20px 0; }
        .led { width: 32px; height: 32px; border-radius: 50%; margin: 0 6px; border: 2px solid #ccc; box-shadow: 0 0 8px #0002; }
        .led.b { background: #3498db; }
        .led.g { background: #27ae60; }
        .led.a { background: #f1c40f; }
        .led.r { background: #e74c3c; }
        .led.w { background: #fff; border: 2px solid #bbb; }
        .led-label { text-align: center; font-size: 12px; color: #888; }
        .section { margin-bottom: 24px; }
        .answers { width: 100%; border-collapse: collapse; margin: 0 auto; }
        .answers th, .answers td { padding: 6px 12px; border-bottom: 1px solid #eee; }
        .answers th { background: #f7f7f7; }
        .timestamp { color: #888; font-size: 13px; text-align: right; }
        .ocr { background: #f9f9f9; border: 1px solid #eee; padding: 10px; font-size: 13px; border-radius: 6px; margin-top: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Processor Monitor</h1>
        <div class="toggle-section">
            <label class="toggle-switch">
                <input type="checkbox" id="pauseToggle">
                <span class="slider"></span>
            </label>
            <span class="toggle-label" id="toggleLabel">Enabled</span>
        </div>
        <div class="section">
            <div class="leds" id="leds"></div>
            <div class="led-label" id="led-label"></div>
        </div>
        <div class="section">
            <strong>Current Question:</strong>
            <div id="question" style="margin: 8px 0 0 0; font-size: 1.1em;"></div>
        </div>
        <div class="section">
            <strong>Answers &amp; Confidence:</strong>
            <table class="answers" id="answers">
                <thead><tr><th>Label</th><th>Confidence (%)</th></tr></thead>
                <tbody></tbody>
            </table>
        </div>
        <div class="section">
            <strong>Last OCR Text:</strong>
            <div class="ocr" id="ocr"></div>
        </div>
        <div class="section">
            <strong>AI Extracted Question &amp; Answers (raw):</strong>
            <div class="ocr" id="ai_question_raw"></div>
        </div>
        <div class="section">
            <strong>Full AI Answer Response:</strong>
            <div class="ocr" id="ai_answer"></div>
        </div>
        <div class="timestamp" id="timestamp"></div>
    </div>
    <script>
        async function fetchPauseState() {
            const resp = await fetch('/pause_state?_=' + Date.now());
            if (!resp.ok) return;
            const data = await resp.json();
            const paused = data.paused;
            document.getElementById('pauseToggle').checked = !paused;
            document.getElementById('toggleLabel').textContent = paused ? 'Paused' : 'On';
        }
        document.getElementById('pauseToggle').addEventListener('change', async function() {
            const paused = !this.checked;
            await fetch('/toggle_pause', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ paused })
            });
            document.getElementById('toggleLabel').textContent = paused ? 'Paused' : 'On';
        });
        setInterval(fetchPauseState, 2000);

        async function fetchState() {
            const resp = await fetch('/state.json?_=' + Date.now());
            if (!resp.ok) return;
            const state = await resp.json();
            // LED colors
            let ledColors = state.led_colors || [];
            const ledsDiv = document.getElementById('leds');
            ledsDiv.innerHTML = '';
            ledColors.forEach(c => {
                const led = document.createElement('div');
                led.className = 'led ' + c;
                ledsDiv.appendChild(led);
            });
            document.getElementById('led-label').textContent = 'LEDs: ' + ledColors.join('');
            // Defensive: always treat missing or malformed ledColors as all white or all blue
            ledColors = (ledColors || []).map(c => (c || '').trim().toLowerCase());
            const allWhite = ledColors.length === 8 && ledColors.every(c => c === 'w');
            const allBlue = ledColors.length === 8 && ledColors.every(c => c === 'b');
            console.log('LEDs:', ledColors, 'All white:', allWhite, 'All blue:', allBlue);

            if (allWhite || allBlue) {
                // Blank all fields but keep the container visible
                ["question", "ai_question_raw", "ai_answer", "ocr"].forEach(id => {
                    const el = document.getElementById(id);
                    if (el) {
                        el.textContent = '';
                        el.innerHTML = '';
                    }
                });
                // Blank answers table
                const answersTbody = document.getElementById('answers').querySelector('tbody');
                answersTbody.innerHTML = '';
                // Do NOT hide the container, just show the LEDs as normal
                return;
            } else {
                document.querySelector('.container').style.display = '';
                // Question
                document.getElementById('question').textContent = state.question || '(No question)';
                // AI Extracted Question & Answers (raw OpenAI response)
                document.getElementById('ai_question_raw').textContent = state.extracted_question_response || '(No extracted question response)';
                // Full AI Answer Response (raw Anthropic response)
                document.getElementById('ai_answer').textContent = state.evaluations || '(No full AI answer response)';
                // Answers
                const answersTbody = document.getElementById('answers').querySelector('tbody');
                answersTbody.innerHTML = '';
                if (state.answer_labels && state.answer_labels.length) {
                    for (let i = 0; i < state.answer_labels.length; ++i) {
                        if (state.answer_labels[i] !== 'NA') {
                            const tr = document.createElement('tr');
                            tr.innerHTML = `<td>${state.answer_labels[i]}</td><td>${state.confidences && state.confidences[i] ? state.confidences[i] : ''}</td>`;
                            answersTbody.appendChild(tr);
                        }
                    }
                }
                // OCR
                document.getElementById('ocr').textContent = state.ocr_text || '';
            }
            // Timestamp
            document.getElementById('timestamp').textContent = 'Last updated: ' + new Date().toLocaleTimeString();
        }
        fetchState();
        setInterval(fetchState, 1500);
    </script>
</body>
</html>
'''

def get_pause_state():
    if os.path.exists(PAUSE_PATH):
        try:
            with open(PAUSE_PATH, "r") as f:
                data = json.load(f)
            return data.get("paused", False)
        except Exception:
            return False
    return False

def set_pause_state(paused):
    with open(PAUSE_PATH, "w") as f:
        json.dump({"paused": paused}, f)

@app.route("/")
def index():
    return render_template_string(HTML_PAGE)

@app.route("/state.json")
def state():
    try:
        with open(STATE_PATH, "r") as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/toggle_pause", methods=["POST"])
def toggle_pause():
    try:
        paused = bool(json.loads(request.data).get("paused", False))
        set_pause_state(paused)
        return jsonify({"success": True, "paused": paused})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/pause_state")
def pause_state():
    return jsonify({"paused": get_pause_state()})

if __name__ == "__main__":
    # Kill any existing web_monitor.py or Flask server on port 5000 (but not self)
    import subprocess
    import os
    import socket
    import logging
    try:
        # Find and kill processes using port 5000
        subprocess.run(['fuser', '-k', '5000/tcp'], check=False)
        # Also kill any stray python web_monitor.py processes except this one
        my_pid = os.getpid()
        # List all web_monitor.py PIDs except self
        pids = subprocess.check_output("pgrep -f web_monitor.py", shell=True).decode().split()
        for pid in pids:
            if int(pid) != my_pid:
                subprocess.run(["kill", "-9", pid], check=False)
    except Exception as e:
        print(f"[WARN] Could not pre-kill web server processes: {e}")
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)  # Suppress Flask's GET/POST logs
    ip = socket.gethostbyname(socket.gethostname())
    print(f"Web monitor running at: http://{ip}:5000/")
    print("Leave this window open to keep the web monitor available.")
    app.run(host="0.0.0.0", port=5000, debug=False)
