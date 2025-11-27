const storySelect = document.getElementById("storySelect");
const modelSelect = document.getElementById("modelSelect");
const generateBtn = document.getElementById("generateBtn");
const childNameInput = document.getElementById("childName");
// const imageInput = document.getElementById("imageInput");
const logEl = document.getElementById("log");
const progress = document.getElementById("progress");
const progressBar = document.getElementById("progressBar");

let templateOptions = [];

function log(msg) {
  if (logEl) logEl.textContent = msg;
}

function formatStoryTitle(baseTitle, childName = "") {
  const cleaned = (childName || "").trim();
  if (!cleaned) return baseTitle;
  const possessive = cleaned.endsWith("s") ? `${cleaned}'` : `${cleaned}'s`;
  return `${possessive} ${baseTitle}`;
}

function renderStoryOptions(childName = "") {
  if (!storySelect) return;
  storySelect.innerHTML = "";
  templateOptions.forEach((t) => {
    const opt = document.createElement("option");
    opt.value = t.key;
    opt.textContent = formatStoryTitle(t.title, childName);
    storySelect.appendChild(opt);
  });
}

async function loadTemplates() {
  log("Loading templates...");
  try {
    const [tRes, mRes] = await Promise.all([fetch("/api/templates"), fetch("/api/models")]);
    const templates = (await tRes.json()).templates || [];
    const models = (await mRes.json()).models || [];
    templateOptions = templates;
    renderStoryOptions(childNameInput ? childNameInput.value : "");
    if (modelSelect) {
      modelSelect.innerHTML = "";
      models.forEach((m) => {
        const opt = document.createElement("option");
        opt.value = m.key;
        opt.textContent = m.title;
        modelSelect.appendChild(opt);
      });
    }
    log("Templates loaded.");
  } catch (err) {
    log("Failed to load templates. Is the server running?");
  }
}

async function generate() {
  const story = storySelect.value;
  const childName = childNameInput.value.trim();
  // const file = imageInput.files[0];
  if (!story || !childName) {
    log("Story and child name are required.");
    return;
  }
  const form = new FormData();
  form.append("story", story);
  form.append("model", modelSelect ? modelSelect.value : "");
  form.append("child_name", childName);
  if (progress) progress.style.display = "block";
  if (progressBar) progressBar.style.width = "20%";
  generateBtn.disabled = true;
  log("Generating...");
  try {
    const res = await fetch("/api/generate", { method: "POST", body: form });
    const text = await res.text();
    let data = null;
    try {
      data = JSON.parse(text);
    } catch {}
    if (progressBar) progressBar.style.width = "80%";
    if (!res.ok) {
      log((data && data.error) || text || "Generation failed");
    } else {
      log(`Done! PDF: ${data.pdf}`);
    }
  } catch (err) {
    log(`Error: ${err}`);
  } finally {
    if (progressBar) progressBar.style.width = "100%";
    setTimeout(() => {
      if (progress) progress.style.display = "none";
      if (progressBar) progressBar.style.width = "0%";
    }, 600);
    generateBtn.disabled = false;
  }
}

if (generateBtn) generateBtn.addEventListener("click", generate);
if (childNameInput) {
  childNameInput.addEventListener("input", (event) => {
    renderStoryOptions(event.target.value);
  });
}
document.addEventListener("DOMContentLoaded", loadTemplates);
