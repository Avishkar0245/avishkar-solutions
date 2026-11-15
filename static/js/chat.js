(function () {
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
