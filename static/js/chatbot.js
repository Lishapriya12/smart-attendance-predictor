// ==========================================================================
// AI CHATBOT ADVISOR INTERFACE
// ==========================================================================

document.addEventListener("DOMContentLoaded", () => {
  const trigger = document.getElementById("chatbot-trigger");
  const win = document.getElementById("chatbot-window");
  const closeBtn = document.getElementById("chat-close");
  const chatForm = document.getElementById("chat-form");
  const chatInput = document.getElementById("chat-input");

  if (!trigger || !win) return;

  trigger.addEventListener("click", () => {
    win.style.display = win.style.display === "none" ? "flex" : "none";
    if (win.style.display === "flex") {
      chatInput.focus();
    }
  });

  closeBtn.addEventListener("click", () => {
    win.style.display = "none";
  });

  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = chatInput.value.trim();
    if (!query) return;

    chatInput.value = "";
    await sendChatMessage(query);
  });
});

async function sendQuickPrompt(promptText) {
  const win = document.getElementById("chatbot-window");
  win.style.display = "flex";
  await sendChatMessage(promptText);
}

async function sendChatMessage(userQuery) {
  const chatBody = document.getElementById("chat-body");

  // 1. Render User Message Bubble
  const userMsgDiv = document.createElement("div");
  userMsgDiv.className = "chat-msg user-msg";
  userMsgDiv.innerHTML = `
    <div class="msg-avatar"><i class="fa-solid fa-user"></i></div>
    <div class="msg-bubble">${escapeHtml(userQuery)}</div>
  `;
  chatBody.appendChild(userMsgDiv);
  chatBody.scrollTop = chatBody.scrollHeight;

  // 2. Render Loading Bot Bubble
  const botMsgDiv = document.createElement("div");
  botMsgDiv.className = "chat-msg bot-msg";
  botMsgDiv.innerHTML = `
    <div class="msg-avatar"><i class="fa-solid fa-robot"></i></div>
    <div class="msg-bubble" id="latest-bot-bubble">
      <i class="fa-solid fa-spinner fa-spin"></i> Calculating exact timetable & attendance figures...
    </div>
  `;
  chatBody.appendChild(botMsgDiv);
  chatBody.scrollTop = chatBody.scrollHeight;

  // 3. Prepare Payload
  const cfg = JSON.parse(localStorage.getItem("smart_attendance_config") || "{}");
  const payload = {
    query: userQuery,
    section_id: cfg.section_id || "section_A",
    subjects: cfg.subjects || [],
    today_str: cfg.start_date || "2026-09-28",
    plan_end_date: cfg.target_date || "2026-11-29"
  };

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    const bubble = document.getElementById("latest-bot-bubble");
    bubble.removeAttribute("id");
    bubble.innerHTML = formatMarkdownText(data.answer);

    chatBody.scrollTop = chatBody.scrollHeight;
  } catch (err) {
    console.error("Error communicating with AI Advisor:", err);
    const bubble = document.getElementById("latest-bot-bubble");
    if (bubble) {
      bubble.removeAttribute("id");
      bubble.textContent = "Sorry, I encountered an error processing your calculation query. Please try again.";
    }
  }
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function formatMarkdownText(text) {
  if (!text) return "";

  let formatted = text
    .replace(/^### (.*$)/gim, '<h4 style="font-size:1rem; margin-top:0.4rem; margin-bottom:0.3rem;">$1</h4>')
    .replace(/^## (.*$)/gim, '<h3 style="font-size:1.1rem; margin-top:0.4rem; margin-bottom:0.3rem;">$1</h3>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/^\- (.*$)/gim, '<li style="margin-left:1.2rem; list-style-type:disc;">$1</li>')
    .replace(/\n\n/g, '<br/><br/>')
    .replace(/\n/g, '<br/>');

  return formatted;
}
