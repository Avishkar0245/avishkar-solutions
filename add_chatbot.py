# Run inside the avishkar-solutions folder:  python add_chatbot.py
import pathlib

CHATBOT_PY = r'''import os, json, time, datetime, re
from collections import defaultdict, deque
from flask import Blueprint, request, jsonify, current_app

chat_bp = Blueprint("chat", __name__)

MODEL = os.getenv("CHAT_MODEL", "claude-haiku-5-5")
LIMIT, WINDOW = 20, 600          # 20 messages per 10 minutes per visitor
_hits = defaultdict(deque)


def _limited(ip):
    now = time.time()
    q = _hits[ip]
    while q and now - q[0] > WINDOW:
        q.popleft()
    if len(q) >= LIMIT:
        return True
    q.append(now)
    return False


def _system_prompt():
    d = current_app.config.get("BOT_DATA", {})
    site = d.get("site", {})
    services = "\n".join(f"- {s['title']}: {s['text']} (price: {s['price']})" for s in d.get("services", []))
    projects = "\n".join(f"- {p['title']}: {p['text']} (tech: {', '.join(p['tags'])})" for p in d.get("projects", []))
    return f"""You are the website assistant for Avishkar Solutions, run by Avishkar, an MCA student and full stack developer (Python, Flask, JavaScript, MySQL, MongoDB). The business helps students with final-year and MCA project mentoring, resume and LinkedIn help, and fresher career guidance (IT and Banking/Finance).

Services:
{services}

Projects built by Avishkar:
{projects}

Contact: Contact page at /contact, WhatsApp https://wa.me/{site.get('whatsapp', '')}, email {site.get('email', '')}.

Rules:
- Answer only about these services, the projects above, and closely related student or fresher questions (project ideas, resume tips, interview preparation). Politely decline unrelated requests.
- Keep replies short: 2 to 4 sentences, plain text, no markdown.
- Reply in the language the visitor writes in.
- Never invent prices, discounts, timelines or guarantees. If asked about price or availability, say it depends on the requirement and invite them to use the Contact page or WhatsApp so Avishkar can reply personally.
- You are an AI assistant, not Avishkar. If the visitor wants to hire, book or discuss details, point them to the Contact page or WhatsApp.
- If you do not know something, say so and suggest contacting Avishkar."""


FAQ = [
    (("price", "cost", "fee", "fees", "charge", "rate", "how much"),
     "Pricing depends on the requirement. Share your details on the Contact page or WhatsApp and Avishkar will reply with a quote."),
    (("project", "mentor", "mentoring", "final year", "mca", "flask", "idea"),
     "I help with final-year and MCA projects: choosing an idea, building it (Flask and web apps) and deploying it. Tell Avishkar your topic or tech stack on the Contact page and he will take it from there."),
    (("resume", "cv", "linkedin"),
     "I build clean, ATS-friendly resumes and LinkedIn profiles for freshers. Send your details on the Contact page to get started."),
    (("interview", "career", "job", "jobs", "fresher", "bank", "banking", "finance"),
     "I offer interview preparation and job search guidance for IT and Banking/Finance roles. Message Avishkar on the Contact page or WhatsApp to discuss your goals."),
    (("deploy", "deployment", "hosting", "domain", "live"),
     "Deployment is part of project guidance: getting your app live with a public link. Ask on the Contact page or WhatsApp for details."),
    (("contact", "call", "whatsapp", "email", "talk", "book", "hire"),
     "You can reach Avishkar through the Contact page or WhatsApp, and he will reply personally."),
    (("hi", "hello", "hey", "namaste"),
     "Hi! Ask me about project guidance, resumes or career help."),
]


def _faq(text):
    t = text.lower()
    words = set(re.findall(r"\w+", t))
    for keys, answer in FAQ:
        if any((k in t) if " " in k else (k in words) for k in keys):
            return answer
    return "I am not sure about that one. Please use the Contact page or WhatsApp and Avishkar will answer personally."


def _log(question, reply, source):
    try:
        with open("chats.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"time": datetime.datetime.utcnow().isoformat(), "question": question,
                                "reply": reply, "source": source}, ensure_ascii=False) + "\n")
    except OSError:
        pass


@chat_bp.post("/chat")
def chat():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "?").split(",")[0].strip()
    if _limited(ip):
        return jsonify(reply="You have sent many messages. Please use the Contact page or WhatsApp to continue."), 429
    data = request.get_json(silent=True) or {}
    msgs = []
    for m in (data.get("messages") or [])[-10:]:
        if isinstance(m, dict) and m.get("role") in ("user", "assistant") and isinstance(m.get("content"), str):
            c = m["content"].strip()[:500]
            if c:
                msgs.append({"role": m["role"], "content": c})
    while msgs and msgs[0]["role"] != "user":
        msgs.pop(0)
    if not msgs or msgs[-1]["role"] != "user":
        return jsonify(reply="Please type your question."), 400

    question = msgs[-1]["content"]
    reply, source = None, "faq"
    key = os.getenv("ANTHROPIC_API_KEY")
    if key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=key)
            r = client.messages.create(model=MODEL, max_tokens=300, system=_system_prompt(),
                                       messages=msgs, timeout=20)
            reply = "".join(b.text for b in r.content if getattr(b, "type", "") == "text").strip()
            source = "ai"
        except Exception as e:
            current_app.logger.warning("Chat AI failed, using FAQ: %s", e)
    if not reply:
        reply, source = _faq(question), "faq"
    _log(question, reply, source)
    return jsonify(reply=reply)
'''

CHAT_JS = r'''(function () {
  var root = document.getElementById("chat");
  if (!root) return;
  var panel = root.querySelector(".chat-panel");
  var log = root.querySelector(".chat-log");
  var form = root.querySelector("form");
  var input = form.querySelector("input");
  var send = form.querySelector("button");
  var toggle = root.querySelector(".chat-toggle");
  var history = [];

  function add(role, text) {
    var d = document.createElement("div");
    d.className = "msg " + role;
    d.textContent = text;
    log.appendChild(d);
    log.scrollTop = log.scrollHeight;
    return d;
  }
  function openChat() {
    panel.hidden = false;
    toggle.setAttribute("aria-expanded", "true");
    if (!log.children.length) {
      add("bot", "Hi! I am the Avishkar Solutions assistant. Ask me about project guidance, resumes or career help.");
    }
    input.focus();
  }
  function closeChat() {
    panel.hidden = true;
    toggle.setAttribute("aria-expanded", "false");
    toggle.focus();
  }
  toggle.addEventListener("click", function () { panel.hidden ? openChat() : closeChat(); });
  root.querySelector(".chat-close").addEventListener("click", closeChat);
  document.querySelectorAll("[data-open-chat]").forEach(function (b) { b.addEventListener("click", openChat); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && !panel.hidden) closeChat(); });

  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    var text = input.value.trim();
    if (!text) return;
    input.value = "";
    add("user", text);
    history.push({ role: "user", content: text });
    var wait = add("bot", "Typing...");
    wait.classList.add("wait");
    send.disabled = true;
    try {
      var r = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: history })
      });
      var d = await r.json();
      wait.textContent = d.reply || "Sorry, something went wrong.";
      if (r.ok) history.push({ role: "assistant", content: d.reply });
    } catch (err) {
      wait.textContent = "Network problem. Please try again or use the Contact page.";
    }
    wait.classList.remove("wait");
    send.disabled = false;
    input.focus();
  });
})();
'''

CHAT_CSS = r'''.chat{position:fixed;right:1rem;bottom:1rem;z-index:50;display:flex;flex-direction:column;align-items:flex-end;gap:.6rem}
.chat-panel{width:min(360px,calc(100vw - 2rem));height:min(480px,70vh);background:#fff;border:1px solid var(--line);border-radius:10px;box-shadow:0 8px 30px rgba(8,57,113,.18);display:flex;flex-direction:column;overflow:hidden}
.chat-panel[hidden]{display:none}
.chat-panel header{display:flex;justify-content:space-between;align-items:center;padding:.7rem 1rem;background:var(--navy);color:#fff}
.chat-close{background:none;border:0;color:#fff;font-size:1.5rem;line-height:1;cursor:pointer}
.chat-log{flex:1;overflow-y:auto;padding:1rem;display:flex;flex-direction:column;gap:.6rem}
.msg{max-width:85%;padding:.55rem .8rem;border-radius:10px;font-size:.95rem;line-height:1.45;white-space:pre-wrap}
.msg.bot{background:#EAF2F4;align-self:flex-start}
.msg.user{background:var(--blue);color:#fff;align-self:flex-end}
.msg.wait{opacity:.6}
.chat form{display:flex;gap:.5rem;padding:.6rem;border-top:1px solid var(--line)}
.chat form input{flex:1;min-width:0}
.chat-note{margin:0;padding:.4rem .8rem .6rem;font-size:.75rem;color:var(--mute)}
.chat-toggle{box-shadow:0 4px 14px rgba(8,57,113,.25)}
'''

WIDGET_HTML = r'''<div id="chat" class="chat">
  <section class="chat-panel" role="dialog" aria-label="Chat with the Avishkar Solutions assistant" hidden>
    <header><strong>Ask Avishkar Solutions</strong><button type="button" class="chat-close" aria-label="Close chat">&times;</button></header>
    <div class="chat-log" role="log" aria-live="polite"></div>
    <form>
      <input type="text" maxlength="500" placeholder="Type your question" aria-label="Your question" autocomplete="off">
      <button class="btn small" type="submit">Send</button>
    </form>
    <p class="chat-note">AI assistant. Chats are saved to improve answers. For a personal reply use the <a href="{{ url_for('contact') }}">Contact page</a> or <a href="https://wa.me/{{ site.whatsapp }}">WhatsApp</a>.</p>
  </section>
  <button type="button" class="chat-toggle btn" aria-expanded="false">Ask a question</button>
</div>
'''

def write(path, text):
    p = pathlib.Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8"); print("wrote", path)

def patch(path, pairs):
    p = pathlib.Path(path); s = p.read_text(encoding="utf-8"); o = s
    for a, b in pairs:
        if a in s:
            s = s.replace(a, b, 1)
        else:
            print("  (not found in", path + "):", a[:50])
    if s != o:
        p.write_text(s, encoding="utf-8"); print("patched", path)

if not pathlib.Path("app.py").exists():
    raise SystemExit("Run this inside the avishkar-solutions folder (where app.py is).")

write("chatbot.py", CHATBOT_PY)
write("static/js/chat.js", CHAT_JS)
write("static/css/chat.css", CHAT_CSS)
write("templates/chat_widget.html", WIDGET_HTML)

app = pathlib.Path("app.py").read_text(encoding="utf-8")
if "register_blueprint(chat_bp)" not in app:
    patch("app.py", [('if __name__ == "__main__":',
        'from chatbot import chat_bp\napp.config["BOT_DATA"] = {"site": SITE, "services": SERVICES, "projects": PROJECTS}\napp.register_blueprint(chat_bp)\n\n\nif __name__ == "__main__":')])

base = pathlib.Path("templates/base.html").read_text(encoding="utf-8")
if "chat_widget.html" not in base:
    patch("templates/base.html", [
        ("""<a class="btn small" href="{{ url_for('contact') }}">Free call</a>""",
         """<a href="{{ url_for('contact') }}">Contact</a>\n    <button type="button" class="btn small" data-open-chat>Ask a question</button>"""),
        ("""<link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">""",
         """<link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">\n<link rel="stylesheet" href="{{ url_for('static', filename='css/chat.css') }}">"""),
        ("</body>", """{% include "chat_widget.html" %}\n<script src="{{ url_for('static', filename='js/chat.js') }}"></script>\n</body>"""),
    ])

patch("templates/home.html", [
    ("""<a class="btn" href="{{ url_for('contact') }}">Book a free 15-min call</a>""",
     """<button type="button" class="btn" data-open-chat>Ask a question</button>"""),
])
patch("templates/contact.html", [("Book a free 15-min call", "Contact me")])

req = pathlib.Path("requirements.txt").read_text(encoding="utf-8")
if "anthropic" not in req:
    pathlib.Path("requirements.txt").write_text(req.rstrip() + "\nanthropic>=0.40.0\n", encoding="utf-8")
    print("patched requirements.txt")
env = pathlib.Path(".env.example")
e = env.read_text(encoding="utf-8") if env.exists() else ""
if "ANTHROPIC_API_KEY" not in e:
    env.write_text(e.rstrip() + "\nANTHROPIC_API_KEY=\nCHAT_MODEL=claude-haiku-5-5\n", encoding="utf-8")
    print("patched .env.example")
print("\nDone. Run: pip install -r requirements.txt  then  python app.py")
