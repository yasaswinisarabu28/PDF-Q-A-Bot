const pdfInput = document.getElementById("pdf-input");
const uploadStatus = document.getElementById("upload-status");
const pdfList = document.getElementById("pdf-list");
const scopeSelect = document.getElementById("scope-select");
const questionInput = document.getElementById("question-input");
const askBtn = document.getElementById("ask-btn");
const chatLog = document.getElementById("chat-log");
const sidebarToggle = document.getElementById("sidebar-toggle");
const appEl = document.getElementById("app");

// --- Sidebar collapse/expand ---
sidebarToggle.addEventListener("click", () => {
  appEl.classList.toggle("sidebar-collapsed");
});

// --- Shelf management ---
function refreshShelf(pdfs) {
  pdfList.innerHTML = "";
  pdfs.forEach((name) => {
    const li = document.createElement("li");
    li.className = "index-card";
    li.dataset.filename = name;
    li.innerHTML = `
      <span class="index-card__name">${name}</span>
      <button class="index-card__delete" data-filename="${name}" title="Remove" aria-label="Remove ${name}">&times;</button>
    `;
    pdfList.appendChild(li);
  });

  const currentValue = scopeSelect.value;
  scopeSelect.innerHTML = '<option value="">All PDFs on the shelf</option>';
  pdfs.forEach((name) => {
    const opt = document.createElement("option");
    opt.value = name;
    opt.textContent = name;
    scopeSelect.appendChild(opt);
  });
  if (pdfs.includes(currentValue)) {
    scopeSelect.value = currentValue;
  }
}

// Event delegation: handles delete clicks for both server-rendered
// and dynamically added cards, since they're all inside #pdf-list
pdfList.addEventListener("click", async (e) => {
  const btn = e.target.closest(".index-card__delete");
  if (!btn) return;

  const filename = btn.dataset.filename;
  if (!confirm(`Remove "${filename}" from the shelf?`)) return;

  try {
    const res = await fetch("/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename }),
    });
    const data = await res.json();

    if (!res.ok) {
      uploadStatus.textContent = data.error || "Delete failed.";
      uploadStatus.classList.add("is-error");
      return;
    }

    uploadStatus.textContent = data.message;
    uploadStatus.classList.remove("is-error");
    refreshShelf(data.pdfs);
  } catch (err) {
    uploadStatus.textContent = "Something went wrong deleting the file.";
    uploadStatus.classList.add("is-error");
  }
});

pdfInput.addEventListener("change", async () => {
  const file = pdfInput.files[0];
  if (!file) return;

  uploadStatus.textContent = `Processing "${file.name}"…`;
  uploadStatus.classList.remove("is-error");

  const formData = new FormData();
  formData.append("pdf", file);

  try {
    const res = await fetch("/upload", { method: "POST", body: formData });
    const data = await res.json();

    if (!res.ok) {
      uploadStatus.textContent = data.error || "Upload failed.";
      uploadStatus.classList.add("is-error");
      return;
    }

    uploadStatus.textContent = data.message;
    refreshShelf(data.pdfs);
    scopeSelect.value = file.name; // auto-scope to the just-added PDF
  } catch (err) {
    uploadStatus.textContent = "Something went wrong uploading the file.";
    uploadStatus.classList.add("is-error");
  }

  pdfInput.value = "";
});

// --- Recent questions (persisted in the browser) ---
const recentList = document.getElementById("recent-list");
const RECENT_KEY = "pdfqa_recent_questions";
const MAX_RECENT = 8;

function getRecentQuestions() {
  try {
    return JSON.parse(localStorage.getItem(RECENT_KEY)) || [];
  } catch (err) {
    return [];
  }
}

function saveRecentQuestion(question) {
  let recent = getRecentQuestions();
  recent = recent.filter((q) => q !== question); // avoid duplicates
  recent.unshift(question);
  recent = recent.slice(0, MAX_RECENT);
  localStorage.setItem(RECENT_KEY, JSON.stringify(recent));
  renderRecentQuestions();
}

function renderRecentQuestions() {
  const recent = getRecentQuestions();
  recentList.innerHTML = "";
  recent.forEach((q) => {
    const li = document.createElement("li");
    li.className = "recent__item";
    li.textContent = q;
    li.title = q;
    li.addEventListener("click", () => {
      questionInput.value = q;
      questionInput.focus();
    });
    recentList.appendChild(li);
  });
}

renderRecentQuestions(); // populate on page load

// --- Chat log ---
function clearEmptyState() {
  const empty = chatLog.querySelector(".chat__empty");
  if (empty) empty.remove();
}

function addUserMessage(text) {
  clearEmptyState();
  const div = document.createElement("div");
  div.className = "msg msg--user";
  div.textContent = text;
  chatLog.appendChild(div);
  chatLog.scrollTop = chatLog.scrollHeight;
  return div;
}

function addAssistantMessage(loadingText) {
  const div = document.createElement("div");
  div.className = "msg msg--assistant";
  div.innerHTML = `<div class="answer-block is-loading">${loadingText}</div>`;
  chatLog.appendChild(div);
  chatLog.scrollTop = chatLog.scrollHeight;
  return div;
}

function renderAnswerInto(container, text) {
  const html = marked.parse(text);
  const withTabs = html.replace(
    /\(Page[s]?\s*([0-9,\s]+)\)/gi,
    (match, nums) => `<span class="cite-tab">p. ${nums.trim()}</span>`
  );
  container.innerHTML = `<div class="answer-block">${withTabs}</div>`;
  chatLog.scrollTop = chatLog.scrollHeight;
}

async function askQuestion() {
  const question = questionInput.value.trim();
  if (!question) return;

  askBtn.disabled = true;
  addUserMessage(question);
  saveRecentQuestion(question);
  const assistantBubble = addAssistantMessage("Reading through the shelf…");
  questionInput.value = "";

  try {
    const res = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        selected_pdf: scopeSelect.value,
      }),
    });
    const data = await res.json();

    if (!res.ok) {
      assistantBubble.innerHTML = `<div class="answer-block">${data.error || "Something went wrong."}</div>`;
      return;
    }

    renderAnswerInto(assistantBubble, data.answer);
  } catch (err) {
    assistantBubble.innerHTML = `<div class="answer-block">Couldn't reach the server. Is app.py running?</div>`;
  } finally {
    askBtn.disabled = false;
  }
}

askBtn.addEventListener("click", askQuestion);
questionInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") askQuestion();
});
