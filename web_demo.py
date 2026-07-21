from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from rag_demo import build_index, generate_answer, load_documents, search


HOST = "127.0.0.1"
PORT = 8000


def render_page(question="", response=None):
    safe_question = escape(question)

    answer_block = ""
    if response is not None:
        evidence_items = "".join(f"<li>{escape(item)}</li>" for item in response["sources"]) or "<li>No matching source found.</li>"
        answer_block = f"""
        <section class=\"card\">
          <h2>Final answer</h2>
          <p class=\"answer\">{escape(response['final_answer'])}</p>
          <p><strong>Confidence:</strong> {escape(response['confidence'])}</p>
          <h3>Supporting evidence</h3>
          <ul>{evidence_items}</ul>
        </section>
        """

    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Simple RAG Web Demo</title>
  <style>
    :root {{
      --bg: #f4f7fb;
      --card: #ffffff;
      --text: #14213d;
      --muted: #4b5563;
      --accent: #1d4ed8;
      --border: #dbe4f0;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Segoe UI, system-ui, -apple-system, sans-serif;
      background: linear-gradient(135deg, #eef4ff, #f9fbff 40%, #eef7f3 100%);
      color: var(--text);
      min-height: 100vh;
      padding: 24px;
    }}
    .container {{
      max-width: 900px;
      margin: 0 auto;
      display: grid;
      gap: 16px;
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 18px;
      box-shadow: 0 6px 16px rgba(11, 18, 32, 0.05);
    }}
    h1 {{ margin: 0 0 8px; }}
    p {{ margin: 6px 0; color: var(--muted); }}
    form {{
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 10px;
      margin-top: 10px;
    }}
    input[type=\"text\"] {{
      width: 100%;
      font-size: 16px;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 12px;
    }}
    button {{
      border: 0;
      border-radius: 10px;
      padding: 12px 16px;
      color: #fff;
      background: var(--accent);
      font-weight: 600;
      cursor: pointer;
    }}
    .answer {{ color: var(--text); font-size: 18px; }}
    ul {{ margin: 0; padding-left: 18px; }}
    li {{ margin: 4px 0; color: var(--muted); }}
    code {{
      background: #f3f4f6;
      border: 1px solid #e5e7eb;
      border-radius: 6px;
      padding: 2px 6px;
    }}
    @media (max-width: 700px) {{
      form {{ grid-template-columns: 1fr; }}
      button {{ width: 100%; }}
    }}
  </style>
</head>
<body>
  <main class=\"container\">
    <section class=\"card\">
      <h1>Simple RAG Web Demo</h1>
      <p>Ask a question and get a grounded answer with confidence and evidence.</p>
      <p>Try: <code>Who owns delivery readiness?</code></p>
      <form method=\"GET\" action=\"/\">
        <input name=\"q\" type=\"text\" placeholder=\"Type your question\" value=\"{safe_question}\" />
        <button type=\"submit\">Ask</button>
      </form>
    </section>
    {answer_block}
  </main>
</body>
</html>
"""


class RAGRequestHandler(BaseHTTPRequestHandler):
    index = None

    def do_GET(self):
        parsed = urlparse(self.path)
        question = parse_qs(parsed.query).get("q", [""])[0].strip()

        response = None
        if question:
            results = search(question, self.index)
            response = generate_answer(question, results)

        body = render_page(question, response).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


def main():
    documents = load_documents()
    RAGRequestHandler.index = build_index(documents)

    server = HTTPServer((HOST, PORT), RAGRequestHandler)
    print(f"Web demo running at http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()