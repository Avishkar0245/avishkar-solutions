import os, json, time, datetime, re
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
