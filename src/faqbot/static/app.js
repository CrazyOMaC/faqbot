"use strict";

const byId = (id) => document.getElementById(id);
const historyKey = "faqbot.conversation.v1";
const dialog = byId("faq-dialog");
const question = byId("question");
let faqs = [];
let messages = [];
let busy = false;
let editingTopic = null;
let toastTimer;

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function toast(message) {
  clearTimeout(toastTimer);
  byId("toast").textContent = message;
  byId("toast").hidden = false;
  toastTimer = setTimeout(() => {
    byId("toast").hidden = true;
  }, 4500);
}

async function api(path, options = {}) {
  let response;
  try {
    response = await fetch(path, {
      ...options,
      headers: { "Content-Type": "application/json", ...options.headers },
    });
  } catch {
    throw new Error(
      "Couldn't reach FAQbot. Check that the server is running and try again.",
    );
  }
  const body = response.status === 204 ? null : await response.json();
  if (!response.ok) {
    const detail = body?.detail;
    throw new Error(
      Array.isArray(detail)
        ? detail.map((issue) => `${issue.loc.at(-1)}: ${issue.msg}`).join(" ")
        : typeof detail === "string"
          ? detail
          : "Something went wrong. Please try again.",
    );
  }
  return body;
}

function example(faq) {
  const defaults = {
    assignment: "When is the assignment due?",
    notes: "Where can I find the notes?",
    exam: "Where is the exam timetable?",
    library: "When is the library open?",
    attendance: "How can I check my attendance?",
    syllabus: "Where can I download the syllabus?",
    fees: "How do I pay my fees?",
    results: "Where can I check my results?",
    scholarship: "How do I apply for a scholarship?",
    registration: "Where can I find course registration help?",
    practical: "When is the practical lab?",
    project: "What are the project requirements?",
    transport: "Where can I find the transport bus schedule?",
    hostel: "How do I apply for a hostel room?",
    contact: "Who should I contact for department help?",
  };
  const candidate = defaults[faq.topic];
  const words = candidate?.toLowerCase().match(/\b\w+\b/g) ?? [];
  if (candidate && faq.keywords.some((word) => words.includes(word)))
    return candidate;
  if (faq.keywords.includes(faq.topic)) return `Where can I find ${faq.topic}?`;
  return `Tell me about ${faq.topic} ${faq.keywords[0]}.`;
}

function showView(name) {
  for (const view of ["chat", "library"]) {
    const active = view === name;
    byId(`${view}-view`).hidden = !active;
    byId(`nav-${view}`).classList.toggle("active", active);
    byId(`nav-${view}`).setAttribute("aria-pressed", String(active));
  }
}

function renderTopics() {
  const starters = byId("starter-prompts");
  starters.replaceChildren();
  for (const faq of faqs.slice(0, 6)) {
    const button = element("button", "starter-card", example(faq));
    button.addEventListener("click", () => sendMessage(example(faq)));
    starters.append(button);
  }
  if (!faqs.length)
    starters.append(
      element("p", "empty-topics", "No FAQs yet. Add one in the FAQs tab."),
    );
  renderLibrary();
}

function renderLibrary() {
  const search = byId("faq-search").value.trim().toLowerCase();
  const filtered = faqs.filter((faq) =>
    `${faq.topic} ${faq.keywords.join(" ")} ${faq.answer}`
      .toLowerCase()
      .includes(search),
  );
  const list = byId("faq-list");
  list.replaceChildren();
  for (const faq of filtered) {
    const card = element("article", "faq-card");
    const heading = element("div", "faq-card-heading");
    const actions = element("div", "card-actions");
    const edit = element("button", "", "Edit");
    edit.setAttribute("aria-label", `Edit ${faq.topic}`);
    edit.addEventListener("click", () => openEditor(faq));
    const remove = element("button", "delete-button", "Delete");
    remove.setAttribute("aria-label", `Delete ${faq.topic}`);
    remove.addEventListener("click", () => deleteFaq(faq, remove));
    actions.append(edit, remove);
    heading.append(element("h2", "", faq.topic), actions);
    card.append(
      heading,
      element("p", "faq-answer", faq.answer),
      element("p", "faq-keywords", `Keywords: ${faq.keywords.join(", ")}`),
    );
    list.append(card);
  }
  if (!filtered.length)
    list.append(
      element(
        "p",
        "empty-library",
        search ? "No matching FAQs." : "No FAQs yet. Add one to get started.",
      ),
    );
}

async function loadFaqs() {
  try {
    faqs = await api("/api/faqs");
    renderTopics();
    byId("load-error").hidden = true;
  } catch {
    byId("load-error").hidden = false;
  }
}

function persistMessages() {
  messages = messages.slice(-100);
  try {
    localStorage.setItem(historyKey, JSON.stringify(messages));
  } catch {
    /* Storage is optional. */
  }
}

function renderMessage(message) {
  const row = element("article", `message ${message.role}`);
  row.append(
    element("div", "message-label", message.role === "user" ? "You" : "FAQbot"),
    element("p", "message-text", message.content),
  );
  if (message.suggestions?.length) {
    const suggestions = element("div", "message-suggestions");
    for (const suggestion of message.suggestions) {
      const button = element("button", "", suggestion);
      button.addEventListener("click", () => sendMessage(suggestion));
      suggestions.append(button);
    }
    row.append(suggestions);
  }
  byId("messages").append(row);
  byId("welcome").hidden = true;
  byId("new-chat").hidden = false;
  return row;
}

function scrollToLatest() {
  const scroll = byId("chat-scroll");
  scroll.scrollTop = scroll.scrollHeight;
}

function resizeComposer() {
  question.style.height = "auto";
  question.style.height = `${Math.min(question.scrollHeight, 150)}px`;
}

async function sendMessage(text) {
  const content = text.trim();
  if (!content || busy) return;
  if (content.length > 2000) {
    toast("Keep questions under 2,000 characters.");
    return;
  }
  showView("chat");
  busy = true;
  byId("send").disabled = true;
  byId("new-chat").disabled = true;
  question.value = "";
  resizeComposer();
  const user = { role: "user", content };
  messages.push(user);
  renderMessage(user);
  const pending = renderMessage({
    role: "assistant",
    content: "Finding your answer...",
  });
  pending.classList.add("pending");
  scrollToLatest();
  try {
    const reply = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message: content }),
    });
    const message = {
      role: "assistant",
      content: reply.message,
      suggestions: reply.suggestions,
    };
    messages.push(message);
    pending.remove();
    renderMessage(message);
  } catch (error) {
    const message = {
      role: "assistant",
      content: `${error.message} Your question hasn't been answered yet.`,
    };
    messages.push(message);
    pending.remove();
    renderMessage(message);
  } finally {
    persistMessages();
    busy = false;
    byId("send").disabled = false;
    byId("new-chat").disabled = false;
    question.focus();
    scrollToLatest();
  }
}

function openEditor(faq = null) {
  editingTopic = faq?.topic ?? null;
  byId("faq-form").reset();
  byId("editor-title").textContent = faq ? "Edit FAQ" : "Add FAQ";
  byId("faq-topic").value = faq?.topic ?? "";
  byId("faq-topic").disabled = Boolean(faq);
  byId("faq-keywords").value = faq?.keywords.join(", ") ?? "";
  byId("faq-answer").value = faq?.answer ?? "";
  byId("editor-error").hidden = true;
  dialog.showModal();
}

async function saveFaq(event) {
  event.preventDefault();
  const faq = {
    topic: byId("faq-topic").value.trim().toLowerCase(),
    keywords: byId("faq-keywords")
      .value.trim()
      .split(/[\s,]+/)
      .filter(Boolean),
    answer: byId("faq-answer").value.trim(),
  };
  byId("save-faq").disabled = true;
  byId("cancel-editor").disabled = true;
  byId("editor-error").hidden = true;
  try {
    const saved = await api(
      editingTopic
        ? `/api/faqs/${encodeURIComponent(editingTopic)}`
        : "/api/faqs",
      { method: editingTopic ? "PUT" : "POST", body: JSON.stringify(faq) },
    );
    const index = faqs.findIndex((item) => item.topic === saved.topic);
    if (index === -1) faqs.push(saved);
    else faqs[index] = saved;
    renderTopics();
    dialog.close();
    toast("FAQ saved.");
  } catch (error) {
    byId("editor-error").textContent = error.message;
    byId("editor-error").hidden = false;
  } finally {
    byId("save-faq").disabled = false;
    byId("cancel-editor").disabled = false;
  }
}

async function deleteFaq(faq, button) {
  if (!window.confirm(`Delete the FAQ for "${faq.topic}"?`)) return;
  button.disabled = true;
  try {
    await api(`/api/faqs/${encodeURIComponent(faq.topic)}`, {
      method: "DELETE",
    });
    faqs = faqs.filter((item) => item.topic !== faq.topic);
    renderTopics();
    toast("FAQ deleted.");
  } catch (error) {
    toast(error.message);
    button.disabled = false;
  }
}

byId("nav-chat").addEventListener("click", () => showView("chat"));
byId("nav-library").addEventListener("click", () => showView("library"));
byId("new-chat").addEventListener("click", () => {
  messages = [];
  persistMessages();
  byId("messages").replaceChildren();
  byId("welcome").hidden = false;
  byId("new-chat").hidden = true;
  question.focus();
});
byId("library-add").addEventListener("click", () => openEditor());
byId("cancel-editor").addEventListener("click", () => dialog.close());
dialog.addEventListener("cancel", (event) => {
  if (byId("save-faq").disabled) event.preventDefault();
});
byId("faq-search").addEventListener("input", renderLibrary);
byId("faq-form").addEventListener("submit", saveFaq);
byId("chat-form").addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage(question.value);
});
question.addEventListener("input", resizeComposer);
question.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    sendMessage(question.value);
  }
});
byId("retry-load").addEventListener("click", loadFaqs);

try {
  const stored = JSON.parse(localStorage.getItem(historyKey) ?? "[]");
  if (Array.isArray(stored)) {
    messages = stored
      .filter(
        (message) =>
          message &&
          ["user", "assistant"].includes(message.role) &&
          typeof message.content === "string",
      )
      .slice(-100)
      .map((message) => ({ role: message.role, content: message.content }));
    messages.forEach(renderMessage);
    scrollToLatest();
  }
} catch {
  /* Invalid or unavailable storage starts a fresh conversation. */
}
loadFaqs();
