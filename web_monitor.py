from flask import Flask, send_from_directory, jsonify, render_template_string
import os
import json

app = Flask(__name__)

STATE_PATH = os.path.join(os.path.dirname(__file__), "output", "state.json")

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
            // Detect transition to all white (processing state)
            const allWhite = ledColors.length === 8 && ledColors.every(c => c === 'w');
            // Use a static variable to track last state
            if (typeof fetchState.lastAllWhite === 'undefined') fetchState.lastAllWhite = false;
            if (allWhite && !fetchState.lastAllWhite) {
                // Just transitioned to all white: clear fields
                document.getElementById('question').textContent = '';
                document.getElementById('ai_question_raw').textContent = '';
                document.getElementById('ai_answer').textContent = '';
                const answersTbody = document.getElementById('answers').querySelector('tbody');
                answersTbody.innerHTML = '';
                document.getElementById('ocr').textContent = '';
            } else if (!allWhite) {
                // Only update fields if not all white
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
            fetchState.lastAllWhite = allWhite;
            // Timestamp
            document.getElementById('timestamp').textContent = 'Last updated: ' + new Date().toLocaleTimeString();
        }
        fetchState();
        setInterval(fetchState, 1500);
    </script>
</body>
</html>
'''

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

if __name__ == "__main__":
    import socket
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)  # Suppress Flask's GET/POST logs
    ip = socket.gethostbyname(socket.gethostname())
    print(f"Web monitor running at: http://{ip}:5000/")
    print("Leave this window open to keep the web monitor available.")
    app.run(host="0.0.0.0", port=5000, debug=False)
