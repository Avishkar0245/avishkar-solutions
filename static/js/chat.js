document.addEventListener("DOMContentLoaded", function () {
  const panel = document.getElementById("aiChatPanel");
  const log = document.getElementById("aiChatLog");
  const form = document.getElementById("aiChatForm");
  const input = document.getElementById("aiChatInput");
  const sendBtn = document.getElementById("aiSendBtn");
  const floatBtn = document.getElementById("aiFloatingBtn");
  const closeBtn = document.getElementById("aiCloseBtn");
  const chips = document.querySelectorAll(".ai-chip");
  const openButtons = document.querySelectorAll("[data-open-chat]");

  let history = [];

  function openChat() {
    if (!panel) return;
    panel.style.display = "flex";
    if (input) input.focus();
  }

  function closeChat() {
    if (!panel) return;
    panel.style.display = "none";
  }

  // फ्लोटिंग बटण क्लिक
  if (floatBtn) {
    floatBtn.addEventListener("click", function () {
      if (panel.style.display === "none" || !panel.style.display) {
        openChat();
      } else {
        closeChat();
      }
    });
  }

  // क्लोज बटण क्लिक
  if (closeBtn) {
    closeBtn.addEventListener("click", closeChat);
  }

  // हेडर किंवा इतर ठिकाणच्या "Ask AI" बटन्ससाठी
  openButtons.forEach(function (btn) {
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      openChat();
    });
  });

  // Quick Chips क्लिक
  chips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      const question = chip.getAttribute("data-chip");
      if (question) {
        sendMessage(question);
      }
    });
  });

  // मेसेज पाठवणे
  async function sendMessage(text) {
    if (!text || !log) return;
    if (input) input.value = "";

    // युझरचा मेसेज दाखवा
    const userMsg = document.createElement("div");
    userMsg.className = "ai-msg user";
    userMsg.textContent = text;
    log.appendChild(userMsg);

    history.push({ role: "user", content: text });

    // AI टाईपिंग स्टेटस दाखवा
    const botMsg = document.createElement("div");
    botMsg.className = "ai-msg bot wait";
    botMsg.textContent = "Thinking...";
    log.appendChild(botMsg);
    log.scrollTop = log.scrollHeight;

    if (sendBtn) sendBtn.disabled = true;

    try {
      const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: history })
      });
      const data = await res.json();
      botMsg.classList.remove("wait");
      botMsg.textContent = data.reply || "Sorry, something went wrong.";
      if (res.ok) {
        history.push({ role: "assistant", content: data.reply });
      }
    } catch (err) {
      botMsg.classList.remove("wait");
      botMsg.textContent = "Network error. Please try again or WhatsApp Avishkar directly.";
    }

    if (sendBtn) sendBtn.disabled = false;
    if (input) input.focus();
    log.scrollTop = log.scrollHeight;
  }

  // फॉर्म सबमिट
  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (input && input.value.trim()) {
        sendMessage(input.value.trim());
      }
    });
  }
});