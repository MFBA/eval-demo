const form = document.querySelector("#questionForm");
const questionInput = document.querySelector("#question");
const topKInput = document.querySelector("#topK");
const answerOutput = document.querySelector("#answerOutput");
const contextOutput = document.querySelector("#contextOutput");
const sectionPills = document.querySelector("#sectionPills");
const sectionCount = document.querySelector("#sectionCount");
const modeBadge = document.querySelector("#modeBadge");
const caseList = document.querySelector("#caseList");
const caseCount = document.querySelector("#caseCount");
const configText = document.querySelector("#configText");
const retrieveOnlyButton = document.querySelector("#retrieveOnly");
const clearButton = document.querySelector("#clearButton");

function setLoading(isLoading, label = "Running") {
  modeBadge.textContent = isLoading ? label : "Ready";
  form.querySelectorAll("button").forEach((button) => {
    button.disabled = isLoading;
  });
}

function renderContext(payload) {
  const sections = payload.retrieved_sections || [];
  sectionCount.textContent = `${sections.length} section${sections.length === 1 ? "" : "s"}`;
  sectionPills.innerHTML = "";

  sections.forEach((section) => {
    const pill = document.createElement("span");
    pill.textContent = section;
    sectionPills.appendChild(pill);
  });

  contextOutput.textContent = payload.context || "No relevant policy context was retrieved.";
}

function renderAnswer(text, state = "Ready") {
  answerOutput.classList.remove("error");
  answerOutput.textContent = text || "No answer returned.";
  modeBadge.textContent = state;
}

function renderError(message, retrieval) {
  answerOutput.classList.add("error");
  answerOutput.textContent = `LLM request failed.\n\n${message}\n\nRetrieval context is still shown so you can debug what the model would have received.`;
  modeBadge.textContent = "LLM error";
  if (retrieval) {
    renderContext(retrieval);
  }
}

async function postJson(path, payload) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();

  if (!response.ok) {
    const error = new Error(data.error || "Request failed.");
    error.payload = data;
    throw error;
  }

  return data;
}

async function runTest({ retrievalOnly = false } = {}) {
  const question = questionInput.value.trim();
  const topK = Number.parseInt(topKInput.value, 10) || 4;

  if (!question) {
    questionInput.focus();
    return;
  }

  setLoading(true, retrievalOnly ? "Retrieving" : "Testing");
  answerOutput.classList.remove("error");

  try {
    const data = await postJson(retrievalOnly ? "/api/retrieve" : "/api/answer", { question, top_k: topK });
    if (retrievalOnly) {
      renderAnswer("Retrieval-only mode: no LLM answer was requested.", "Retrieval only");
      renderContext(data);
    } else {
      renderAnswer(data.answer, "Answered");
      renderContext(data);
    }
  } catch (error) {
    renderError(error.message, error.payload?.retrieval);
  } finally {
    setLoading(false);
  }
}

async function loadCases() {
  const response = await fetch("/api/breaker-questions");
  const data = await response.json();
  const cases = data.questions || [];

  caseCount.textContent = cases.length;
  caseList.innerHTML = "";

  cases.forEach((item) => {
    const button = document.createElement("button");
    button.className = "case-button";
    button.type = "button";
    button.innerHTML = `<strong>${item.id.replaceAll("_", " ")}</strong><span>${item.question}</span>`;
    button.addEventListener("click", () => {
      questionInput.value = item.question;
      answerOutput.classList.remove("error");
      modeBadge.textContent = "Case loaded";
      questionInput.focus();
    });
    caseList.appendChild(button);
  });
}

async function loadConfig() {
  try {
    const response = await fetch("/api/config");
    const data = await response.json();
    configText.textContent = `${data.model} at ${data.base_url}`;
  } catch {
    configText.textContent = "Unable to read server config.";
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  runTest();
});

retrieveOnlyButton.addEventListener("click", () => {
  runTest({ retrievalOnly: true });
});

clearButton.addEventListener("click", () => {
  questionInput.value = "";
  renderAnswer("Run a question to see the assistant response.");
  renderContext({ retrieved_sections: [], context: "No context loaded." });
  questionInput.focus();
});

loadConfig();
loadCases();
