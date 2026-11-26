const sessionId = crypto.randomUUID();
const state = {
  role: "ai-engineer",
  question: "",
  resumeText: "",
  cameraStream: null,
  audioStream: null,
  audioContext: null,
  analyser: null,
  recordingStartedAt: null,
  rmsSamples: [],
  lastFrame: null,
  recognition: null,
};

const $ = (id) => document.getElementById(id);

async function api(path, payload = {}) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sessionId, role: state.role, ...payload }),
  });
  if (!response.ok) throw new Error((await response.json()).error || "Request failed");
  return response.json();
}

function scoreCard(label, value) {
  return `<div class="scoreCard"><span>${label}</span><strong>${value}</strong></div>`;
}

function metric(label, value) {
  return `<div class="metric"><span>${label}</span><strong>${value}</strong></div>`;
}

function pills(items, missing = false) {
  if (!items || !items.length) return "<p>None detected yet.</p>";
  return `<div class="pillList">${items.map((item) => `<span class="pill ${missing ? "missing" : ""}">${item}</span>`).join("")}</div>`;
}

function list(items) {
  return `<ul>${items.map((item) => `<li>${item}</li>`).join("")}</ul>`;
}

async function loadRoles() {
  const response = await fetch("/api/roles");
  const data = await response.json();
  $("roleSelect").innerHTML = data.roles.map((role) => `<option value="${role.id}">${role.title}</option>`).join("");
}

async function analyzeResume() {
  state.resumeText = $("resumeText").value.trim();
  if (!state.resumeText) {
    $("resumeResult").innerHTML = "<p>Paste resume text first.</p>";
    return;
  }
  const result = await api("/api/resume", { text: state.resumeText });
  $("resumeResult").innerHTML = `
    ${scoreCard("Resume score", result.score)}
    <p><b>${result.wordCount}</b> words for ${result.roleTitle}</p>
    <p><b>Matched skills</b></p>${pills(result.matchedSkills)}
    <p><b>Missing skills</b></p>${pills(result.missingSkills, true)}
    <p><b>Suggestions</b></p>${list(result.suggestions)}
  `;
}

async function newQuestion() {
  const result = await api("/api/question", { resumeText: $("resumeText").value.trim() });
  state.question = result.question;
  $("questionText").textContent = result.question;
}

async function startCamera() {
  state.cameraStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
  $("video").srcObject = state.cameraStream;
  $("cameraStatus").textContent = "Camera on";
}

function readFrameFeatures() {
  const video = $("video");
  const canvas = $("frameCanvas");
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
  let total = 0;
  let totalSq = 0;
  let centerLight = 0;
  let centerCount = 0;
  let lowerLight = 0;
  let lowerCount = 0;
  for (let y = 0; y < canvas.height; y += 4) {
    for (let x = 0; x < canvas.width; x += 4) {
      const i = (y * canvas.width + x) * 4;
      const light = (data[i] + data[i + 1] + data[i + 2]) / 765;
      total += light;
      totalSq += light * light;
      const centered = x > canvas.width * 0.28 && x < canvas.width * 0.72 && y > canvas.height * 0.18 && y < canvas.height * 0.78;
      if (centered) {
        centerLight += light;
        centerCount++;
      }
      const lowerFace = x > canvas.width * 0.35 && x < canvas.width * 0.65 && y > canvas.height * 0.52 && y < canvas.height * 0.72;
      if (lowerFace) {
        lowerLight += light;
        lowerCount++;
      }
    }
  }
  const samples = Math.ceil(canvas.width / 4) * Math.ceil(canvas.height / 4);
  const brightness = total / samples;
  const contrast = Math.sqrt(Math.max(0, totalSq / samples - brightness * brightness));
  const centerAvg = centerLight / Math.max(1, centerCount);
  const lowerAvg = lowerLight / Math.max(1, lowerCount);
  let movement = 0.12;
  if (state.lastFrame) movement = Math.abs(brightness - state.lastFrame.brightness) * 6 + Math.abs(centerAvg - state.lastFrame.centerAvg) * 4;
  state.lastFrame = { brightness, centerAvg };
  return {
    brightness,
    contrast,
    centerPresence: Math.min(1, centerAvg / Math.max(0.08, brightness)),
    movement: Math.min(1, movement),
    smileProxy: Math.min(1, lowerAvg / Math.max(0.08, centerAvg)),
  };
}

async function analyzeEmotion() {
  if (!state.cameraStream) await startCamera();
  const result = await api("/api/emotion", readFrameFeatures());
  $("emotionResult").innerHTML = `
    ${metric("Confidence", result.confidence)}
    ${metric("Calm", result.calm)}
    ${metric("Engagement", result.engagement)}
    ${metric("Eye contact", result.eyeContact)}
    <p>${result.mood}: ${result.note}</p>
  `;
}

async function startVoice() {
  state.audioStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
  state.audioContext = new AudioContext();
  const source = state.audioContext.createMediaStreamSource(state.audioStream);
  state.analyser = state.audioContext.createAnalyser();
  state.analyser.fftSize = 1024;
  source.connect(state.analyser);
  state.rmsSamples = [];
  state.recordingStartedAt = performance.now();
  sampleAudio();
  startSpeechRecognition();
  $("speechStatus").textContent = "Listening";
}

function sampleAudio() {
  if (!state.analyser) return;
  const buffer = new Uint8Array(state.analyser.fftSize);
  state.analyser.getByteTimeDomainData(buffer);
  const rms = Math.sqrt(buffer.reduce((sum, value) => sum + ((value - 128) / 128) ** 2, 0) / buffer.length);
  state.rmsSamples.push(rms);
  requestAnimationFrame(sampleAudio);
}

function startSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    $("speechStatus").textContent = "Speech API unavailable";
    return;
  }
  state.recognition = new SpeechRecognition();
  state.recognition.continuous = true;
  state.recognition.interimResults = true;
  state.recognition.onresult = (event) => {
    let transcript = "";
    for (const result of event.results) transcript += `${result[0].transcript} `;
    $("answerText").value = transcript.trim();
  };
  state.recognition.start();
}

async function stopVoice() {
  if (state.recognition) state.recognition.stop();
  if (state.audioStream) state.audioStream.getTracks().forEach((track) => track.stop());
  const samples = state.rmsSamples;
  const avg = samples.reduce((sum, value) => sum + value, 0) / Math.max(1, samples.length);
  const variability = Math.sqrt(samples.reduce((sum, value) => sum + (value - avg) ** 2, 0) / Math.max(1, samples.length));
  const durationSeconds = (performance.now() - (state.recordingStartedAt || performance.now())) / 1000;
  const result = await api("/api/voice", {
    transcript: $("answerText").value,
    durationSeconds,
    rms: avg,
    variability,
  });
  $("speechStatus").textContent = "Voice analyzed";
  $("voiceResult").innerHTML = `
    ${metric("WPM", result.wordsPerMinute)}
    ${metric("Pace", result.pace)}
    ${metric("Energy", result.energy)}
    ${metric("Fluency", result.fluency)}
  `;
}

async function analyzeAnswer() {
  const answer = $("answerText").value.trim();
  if (!answer) {
    $("answerResult").innerHTML = "<p>Type or record an answer first.</p>";
    return;
  }
  const result = await api("/api/answer", { answer, question: state.question });
  $("answerResult").innerHTML = `
    <div class="report">
      ${scoreCard("Answer", result.score)}
      ${scoreCard("Clarity", result.clarity)}
      ${scoreCard("Structure", result.structure)}
      ${scoreCard("Tech depth", result.technicalDepth)}
    </div>
    <p><b>Technical terms</b></p>${pills(result.technicalTerms)}
    <p><b>Feedback</b></p>${list(result.feedback)}
  `;
}

async function buildReport() {
  const response = await fetch(`/api/report?sessionId=${encodeURIComponent(sessionId)}`);
  const result = await response.json();
  $("reportResult").innerHTML = `
    ${scoreCard("Overall", result.overall)}
    ${scoreCard("Resume", result.resumeScore)}
    ${scoreCard("Answers", result.answerScore)}
    ${scoreCard("Delivery", result.deliveryScore)}
    <div class="scoreCard wide">
      <span>Next steps</span>
      ${list(result.nextSteps)}
    </div>
  `;
}

$("roleSelect").addEventListener("change", (event) => {
  state.role = event.target.value;
});
$("resumeFile").addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  $("resumeText").value = await file.text();
});
$("analyzeResumeBtn").addEventListener("click", analyzeResume);
$("questionBtn").addEventListener("click", newQuestion);
$("cameraBtn").addEventListener("click", startCamera);
$("emotionBtn").addEventListener("click", analyzeEmotion);
$("recordBtn").addEventListener("click", startVoice);
$("stopRecordBtn").addEventListener("click", stopVoice);
$("answerBtn").addEventListener("click", analyzeAnswer);
$("reportBtn").addEventListener("click", buildReport);

loadRoles();
