from fastapi.responses import HTMLResponse


def get_ui() -> HTMLResponse:
    return HTMLResponse(
        """
    <html>
    <head>
        <title>OpenEnv Dashboard</title>
        <style>
            body { font-family: Arial; padding: 20px; }
            button { margin: 5px; padding: 10px; }
            pre { background: #111; color: #0f0; padding: 10px; }
        </style>
    </head>
    <body>
        <h1>OpenEnv Code Review Dashboard</h1>

        <button onclick="resetEnv()">Reset</button>
        <button onclick="baseline()">Run Baseline</button>

        <h3>Output:</h3>
        <pre id="output"></pre>

        <script>
        async function resetEnv() {
            const res = await fetch('/reset');
            const data = await res.json();
            document.getElementById('output').innerText = JSON.stringify(data, null, 2);
        }

        async function baseline() {
            const res = await fetch('/baseline');
            const data = await res.json();
            document.getElementById('output').innerText = JSON.stringify(data, null, 2);
        }
        </script>
    </body>
    </html>
    """
    )
