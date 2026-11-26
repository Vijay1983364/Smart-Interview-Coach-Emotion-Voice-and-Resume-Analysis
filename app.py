from __future__ import annotations
import json
import math
import os
import re
import socket
import uuid
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "frontend"
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8000"))
MAX_PORT_ATTEMPTS = 10


ROLE_SKILLS = {
    "ai-engineer": {
        "title": "AI / ML Engineer",
        "skills": [
            "python",
            "machine learning",
            "deep learning",
            "tensorflow",
            "pytorch",
            "nlp",
            "computer vision",
            "opencv",
            "model deployment",
            "feature engineering",
        ],
        "questions": [
            "Explain how you would design a real-time emotion detection pipeline for interview feedback.",
            "How do you detect and reduce overfitting in a deep learning model?",
            "Walk me through an NLP project where you transformed raw text into useful predictions.",
            "How would you deploy a computer vision model for low-latency inference?",
        ],
    },
    "software-engineer": {
        "title": "Software Engineer",
        "skills": [
            "data structures",
            "algorithms",
            "api design",
            "databases",
            "testing",
            "system design",
            "python",
            "javascript",
            "git",
            "cloud",
        ],
        "questions": [
            "Design a scalable backend for an interview practice platform.",
            "Describe a bug you solved that required careful debugging.",
            "How do you choose between SQL and NoSQL for a product feature?",
            "Explain how you would test a resume parsing service.",
        ],
    },
    "data-scientist": {
        "title": "Data Scientist",
        "skills": [
            "statistics",
            "python",
            "sql",
            "machine learning",
            "experimentation",
            "visualization",
            "pandas",
            "model evaluation",
            "feature engineering",
            "communication",
        ],
        "questions": [
            "How would you measure whether interview coaching improves candidate outcomes?",
            "Explain precision, recall, and F1 score with a hiring-related example.",
            "Tell me about an analysis where the first answer was misleading.",
            "How do you communicate uncertainty to non-technical stakeholders?",
        ],
    },
    "frontend-developer": {
        "title": "Frontend Developer",
        "skills": ["html", "css", "javascript", "react", "typescript", "accessibility", "responsive design", "performance", "testing", "api integration"],
        "questions": [
            "How would you build a responsive dashboard for an interview analytics product?",
            "Explain how you improve frontend performance in a data-heavy application.",
            "How do you make a web app accessible for keyboard and screen-reader users?",
            "Describe a time you integrated frontend UI with backend APIs.",
        ],
    },
    "backend-developer": {
        "title": "Backend Developer",
        "skills": ["python", "java", "node.js", "api design", "databases", "authentication", "caching", "microservices", "testing", "deployment"],
        "questions": [
            "Design a backend API for storing interview sessions and reports.",
            "How would you secure user resume and interview data?",
            "Explain how you handle database performance problems in production.",
            "How do you design reliable APIs for frontend and mobile clients?",
        ],
    },
    "full-stack-developer": {
        "title": "Full Stack Developer",
        "skills": ["javascript", "python", "react", "api design", "databases", "authentication", "testing", "deployment", "system design", "ui design"],
        "questions": [
            "How would you design this interview coach as a production full-stack product?",
            "Describe a feature you built from database schema to final UI.",
            "How do you debug an issue that may be in the frontend, API, or database?",
            "How would you add user accounts and saved interview history to this app?",
        ],
    },
    "data-engineer": {
        "title": "Data Engineer",
        "skills": ["sql", "python", "etl", "data pipelines", "spark", "airflow", "warehousing", "data quality", "cloud", "analytics"],
        "questions": [
            "Design a data pipeline for interview recordings, transcripts, and scoring events.",
            "How do you validate data quality in an automated analytics pipeline?",
            "Explain batch versus streaming processing with an interview analytics example.",
            "How would you model resume, voice, and emotion metrics for reporting?",
        ],
    },
    "devops-cloud-engineer": {
        "title": "DevOps / Cloud Engineer",
        "skills": ["linux", "docker", "kubernetes", "ci/cd", "aws", "azure", "gcp", "monitoring", "terraform", "security"],
        "questions": [
            "How would you deploy this interview coach application reliably to the cloud?",
            "Explain how you would monitor latency, errors, and uptime for this system.",
            "How do you design a CI/CD pipeline for a Python web application?",
            "What steps would you take to containerize and scale this project?",
        ],
    },
    "cybersecurity-analyst": {
        "title": "Cybersecurity Analyst",
        "skills": ["network security", "threat analysis", "vulnerability assessment", "incident response", "siem", "risk management", "python", "authentication", "encryption", "compliance"],
        "questions": [
            "How would you protect sensitive interview videos, resumes, and transcripts?",
            "Describe how you investigate a suspicious login or data access event.",
            "How do you prioritize vulnerabilities found in a web application?",
            "Explain encryption at rest and in transit for candidate data.",
        ],
    },
    "mobile-app-developer": {
        "title": "Mobile App Developer",
        "skills": ["android", "ios", "flutter", "react native", "api integration", "mobile ui", "offline storage", "performance", "testing", "app store"],
        "questions": [
            "How would you build a mobile version of this interview coach?",
            "How do you handle camera and microphone permissions in a mobile app?",
            "Explain how you optimize app performance on lower-end devices.",
            "How would you sync offline interview practice sessions with a backend?",
        ],
    },
    "ui-ux-designer": {
        "title": "UI / UX Designer",
        "skills": ["user research", "wireframing", "prototyping", "figma", "accessibility", "visual design", "design systems", "usability testing", "interaction design", "product thinking"],
        "questions": [
            "How would you design feedback screens for nervous interview candidates?",
            "Describe your process from user research to high-fidelity prototype.",
            "How do you make an analytics-heavy interface simple and trustworthy?",
            "How would you test whether this product helps users improve interviews?",
        ],
    },
    "product-manager": {
        "title": "Product Manager",
        "skills": ["roadmapping", "prioritization", "user research", "metrics", "experimentation", "stakeholder management", "requirements", "go-to-market", "analytics", "communication"],
        "questions": [
            "How would you prioritize features for the first release of this interview coach?",
            "What success metrics would you define for an AI interview preparation product?",
            "How would you handle concerns about fairness and privacy in AI feedback?",
            "Tell me about a time you made a product tradeoff with incomplete data.",
        ],
    },
    "business-analyst": {
        "title": "Business Analyst",
        "skills": ["requirements gathering", "process mapping", "sql", "excel", "dashboards", "stakeholder management", "documentation", "data analysis", "user stories", "communication"],
        "questions": [
            "How would you gather requirements for an AI interview coach platform?",
            "Explain how you translate business needs into user stories.",
            "How would you design a dashboard for candidate improvement trends?",
            "Describe a time you found a gap between user needs and product behavior.",
        ],
    },
    "data-analyst": {
        "title": "Data Analyst",
        "skills": ["sql", "excel", "python", "tableau", "power bi", "statistics", "data cleaning", "dashboards", "business metrics", "communication"],
        "questions": [
            "How would you analyze whether this interview coach improves user performance?",
            "Explain how you clean and validate a messy dataset before analysis.",
            "How do you choose the right chart for a business question?",
            "Tell me about a time your analysis changed a business decision.",
        ],
    },
    "software-tester": {
        "title": "Software Testing / QA Engineer",
        "skills": ["manual testing", "automation testing", "selenium", "test cases", "bug reporting", "api testing", "regression testing", "performance testing", "jira", "quality assurance"],
        "questions": [
            "How would you test the resume analysis feature in this interview coach?",
            "Explain the difference between smoke, sanity, regression, and acceptance testing.",
            "How do you write clear bug reports that developers can act on quickly?",
            "Describe how you would automate browser tests for this application.",
        ],
    },
    "hr-recruiter": {
        "title": "HR / Recruiter",
        "skills": ["talent acquisition", "screening", "interviewing", "candidate experience", "communication", "ats", "sourcing", "assessment", "stakeholder management", "hiring process"],
        "questions": [
            "How would you evaluate whether this tool improves candidate readiness?",
            "Describe how you create a positive candidate experience.",
            "How do you screen resumes fairly and consistently?",
            "How would you use interview analytics without replacing human judgment?",
        ],
    },
}


RESUME_QUESTION_TEMPLATES = [
    "Based on your resume, which project best proves you are ready for a {title} role?",
    "Your resume mentions {skill1}. Tell me about the strongest example where you used it.",
    "Pick one resume bullet related to {skill1} and explain the problem, action, and result.",
    "Which resume project involved {skill1} or {skill2}, and what was your exact contribution?",
    "What is the most impressive measurable result on your resume for a {title} position?",
    "Tell me about one resume project you would improve if you had another week.",
    "Which skill on your resume is strongest for {title}, and how can you prove it in an interview?",
    "What is one weak area or missing skill in your resume for {title}, and how are you improving it?",
    "Walk me through your most recent resume experience and connect it to this {title} role.",
    "Choose one resume project and explain the tools, tradeoffs, and final outcome.",
    "If I question one claim on your resume about {skill2}, how would you defend it with evidence?",
    "Which resume achievement shows leadership, ownership, or independent problem solving?",
]


QUESTION_TEMPLATES = [
    "Tell me about a {title} project where you used {skill1} to solve a real problem.",
    "What is the hardest technical challenge you have faced in {skill1}, and how did you solve it?",
    "How would you explain {skill1} to a non-technical interviewer?",
    "Describe a time you improved quality, speed, or reliability using {skill1}.",
    "How do you decide whether {skill1} is the right approach for a project?",
    "Walk me through your strongest project involving {skill1} and {skill2}.",
    "What mistakes should a beginner avoid when working with {skill1}?",
    "How do you test or validate work related to {skill1}?",
    "Describe a time you learned {skill1} quickly for a deadline.",
    "How would you debug a production issue involving {skill1}?",
    "What metrics would you track to measure success in a {title} project?",
    "Tell me about a time you disagreed with a teammate on a {title} decision.",
    "How do you prioritize tasks when several {title} problems are urgent?",
    "Describe a project where communication mattered as much as technical execution.",
    "How would you handle incomplete requirements for a {title} assignment?",
    "What tradeoffs would you consider when using {skill2} in a real product?",
    "Tell me about a failure or bug in a {title} project and what you learned.",
    "How do you keep your {title} skills current?",
    "Describe a time you improved user, customer, or stakeholder outcomes.",
    "How would you design a small proof of concept using {skill1}, {skill2}, and {skill3}?",
    "What security, privacy, or ethics risks should a {title} consider?",
    "How would you document your work so another person can maintain it?",
    "Describe a time you used data or feedback to change your approach.",
    "What would you do in your first 30 days in a {title} role?",
    "How would you mentor a junior teammate learning {skill1}?",
    "Give an example of a project where you balanced speed with quality.",
]


def expand_role_questions() -> None:
    for role_data in ROLE_SKILLS.values():
        title = role_data["title"]
        skills = role_data["skills"]
        context = {
            "title": title,
            "skill1": skills[0],
            "skill2": skills[1],
            "skill3": skills[2],
        }
        generated = [template.format(**context) for template in QUESTION_TEMPLATES]
        resume_generated = [template.format(**context) for template in RESUME_QUESTION_TEMPLATES]
        role_data["questions"] = list(dict.fromkeys(role_data["questions"] + generated))[:30]
        role_data["resumeQuestions"] = list(dict.fromkeys(resume_generated))


expand_role_questions()


POWER_VERBS = {
    "built",
    "created",
    "designed",
    "deployed",
    "implemented",
    "improved",
    "optimized",
    "reduced",
    "increased",
    "led",
    "automated",
    "analyzed",
    "trained",
    "fine-tuned",
}


FILLERS = {"um", "uh", "like", "actually", "basically", "literally", "you know", "sort of", "kind of"}


@dataclass
class SessionStore:
    resumes: dict[str, dict[str, Any]] = field(default_factory=dict)
    answers: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    signals: dict[str, dict[str, Any]] = field(default_factory=dict)


STORE = SessionStore()


def clamp(value: float, low: float = 0, high: float = 100) -> int:
    return int(max(low, min(high, round(value))))


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z+#.\-]*", text.lower())


def sentence_count(text: str) -> int:
    return max(1, len(re.findall(r"[.!?]+", text)))


def analyze_resume(text: str, role: str) -> dict[str, Any]:
    role_data = ROLE_SKILLS.get(role, ROLE_SKILLS["ai-engineer"])
    tokens = tokenize(text)
    token_set = set(tokens)
    words = len(tokens)
    matched = [skill for skill in role_data["skills"] if skill in text.lower() or skill in token_set]
    missing = [skill for skill in role_data["skills"] if skill not in matched]
    verbs = sorted({verb for verb in POWER_VERBS if verb in token_set or verb in text.lower()})
    metrics = re.findall(r"(\d+(?:\.\d+)?\s?%|\$\s?\d+|\d+\s?(?:x|k|m|ms|sec|seconds|users|projects))", text, re.I)
    sections = {
        "experience": bool(re.search(r"\bexperience\b|\bwork\b|\bintern", text, re.I)),
        "projects": bool(re.search(r"\bprojects?\b", text, re.I)),
        "skills": bool(re.search(r"\bskills?\b|\btechnologies\b", text, re.I)),
        "education": bool(re.search(r"\beducation\b|\bdegree\b|\buniversity\b|\bcollege\b", text, re.I)),
    }

    keyword_score = 100 * len(matched) / max(1, len(role_data["skills"]))
    impact_score = min(100, 18 * len(metrics) + 6 * len(verbs))
    structure_score = 25 * sum(1 for present in sections.values() if present)
    length_score = 100 if 250 <= words <= 850 else max(30, 100 - abs(words - 500) / 8)
    score = clamp(keyword_score * 0.38 + impact_score * 0.24 + structure_score * 0.22 + length_score * 0.16)

    suggestions = []
    if missing:
        suggestions.append(f"Add stronger evidence for: {', '.join(missing[:5])}.")
    if len(metrics) < 3:
        suggestions.append("Quantify outcomes with numbers such as accuracy, latency, users, cost, or time saved.")
    if len(verbs) < 5:
        suggestions.append("Start more bullets with action verbs like built, deployed, optimized, trained, or improved.")
    if not all(sections.values()):
        suggestions.append("Include clear sections for experience, projects, skills, and education.")

    return {
        "roleTitle": role_data["title"],
        "score": score,
        "wordCount": words,
        "matchedSkills": matched,
        "missingSkills": missing[:8],
        "powerVerbs": verbs,
        "metricsFound": metrics[:10],
        "sections": sections,
        "suggestions": suggestions or ["Resume is well aligned. Tighten bullets around your highest-impact AI/CV/NLP work."],
    }


def generate_question(role: str, resume_summary: str = "") -> dict[str, Any]:
    role_data = ROLE_SKILLS.get(role, ROLE_SKILLS["ai-engineer"])
    questions = role_data["questions"]
    resume_questions = role_data.get("resumeQuestions", [])
    question_type = "general"
    question_pool = questions

    if resume_summary.strip() and resume_questions:
        question_type = "resume"
        question_pool = resume_questions

    question = question_pool[uuid.uuid4().int % len(question_pool)]
    if resume_summary.strip():
        resume_analysis = analyze_resume(resume_summary, role)
        skills = ", ".join(resume_analysis["matchedSkills"][:3])
        if skills:
            question = f"Your resume mentions {skills}. {question}"
        else:
            question = f"Based on your resume for {role_data['title']}: {question}"

    return {
        "id": str(uuid.uuid4()),
        "roleTitle": role_data["title"],
        "question": question,
        "questionType": question_type,
        "questionCount": len(questions) + len(resume_questions),
        "generalQuestionCount": len(questions),
        "resumeQuestionCount": len(resume_questions),
        "tips": [
            "Use STAR: situation, task, action, result.",
            "Name the model, data, metric, and tradeoff where relevant.",
            "End with what you learned or improved next.",
        ],
    }


def analyze_answer(text: str, question: str) -> dict[str, Any]:
    tokens = tokenize(text)
    words = len(tokens)
    unique_ratio = len(set(tokens)) / max(1, words)
    sentences = sentence_count(text)
    avg_sentence = words / sentences
    filler_hits = {filler: len(re.findall(rf"\b{re.escape(filler)}\b", text.lower())) for filler in FILLERS}
    filler_total = sum(filler_hits.values())
    star_parts = {
        "situation": bool(re.search(r"\bwhen\b|\bwhile\b|\bcontext\b|\bproject\b", text, re.I)),
        "task": bool(re.search(r"\bgoal\b|\bneeded\b|\btask\b|\bchallenge\b", text, re.I)),
        "action": bool(re.search(r"\bi\b|\bwe\b|\bimplemented\b|\bbuilt\b|\btrained\b|\bdesigned\b", text, re.I)),
        "result": bool(re.search(r"\bresult\b|\bimproved\b|\bincreased\b|\breduced\b|\baccuracy\b|\b%\b|\bms\b", text, re.I)),
    }
    technical_terms = [
        "model",
        "data",
        "metric",
        "accuracy",
        "precision",
        "recall",
        "latency",
        "api",
        "pipeline",
        "deployment",
        "opencv",
        "nlp",
        "deep learning",
    ]
    tech_hits = [term for term in technical_terms if term in text.lower()]

    clarity = clamp(100 - abs(avg_sentence - 18) * 2.1 - filler_total * 5)
    structure = clamp(25 * sum(star_parts.values()))
    depth = clamp(18 * len(tech_hits) + min(30, words / 6))
    relevance = clamp(50 + 50 * len(set(tokenize(question)) & set(tokens)) / max(1, len(set(tokenize(question)))))
    score = clamp(clarity * 0.28 + structure * 0.28 + depth * 0.26 + relevance * 0.18)

    feedback = []
    if words < 80:
        feedback.append("Add more detail: describe the problem, your concrete actions, and measurable result.")
    if not star_parts["result"]:
        feedback.append("Close with a measurable result or lesson learned.")
    if filler_total > 2:
        feedback.append("Reduce filler words and leave short pauses instead.")
    if len(tech_hits) < 3:
        feedback.append("Use more technical specifics: data, model, metric, deployment, and tradeoffs.")

    return {
        "score": score,
        "clarity": clarity,
        "structure": structure,
        "technicalDepth": depth,
        "relevance": relevance,
        "wordCount": words,
        "avgSentenceLength": round(avg_sentence, 1),
        "fillerWords": filler_hits,
        "starCoverage": star_parts,
        "technicalTerms": tech_hits,
        "feedback": feedback or ["Strong answer. Make the result even sharper with one memorable number."],
    }


def analyze_emotion(payload: dict[str, Any]) -> dict[str, Any]:
    brightness = float(payload.get("brightness", 0.5))
    contrast = float(payload.get("contrast", 0.3))
    center = float(payload.get("centerPresence", 0.5))
    movement = float(payload.get("movement", 0.2))
    smile = float(payload.get("smileProxy", 0.4))

    confidence = clamp(35 + center * 30 + contrast * 15 + smile * 20 - movement * 12)
    calm = clamp(82 - movement * 55 + brightness * 8)
    engagement = clamp(40 + contrast * 25 + center * 20 + smile * 20)
    eye_contact = clamp(30 + center * 60 - movement * 10)

    mood = "focused"
    if smile > 0.58 and calm > 55:
        mood = "positive"
    elif movement > 0.62:
        mood = "nervous"
    elif brightness < 0.25:
        mood = "low visibility"

    return {
        "confidence": confidence,
        "calm": calm,
        "engagement": engagement,
        "eyeContact": eye_contact,
        "mood": mood,
        "note": "Computer-vision proxy based on webcam frame brightness, contrast, centering, motion, and expression cues.",
    }


def analyze_voice(payload: dict[str, Any]) -> dict[str, Any]:
    transcript = payload.get("transcript", "")
    duration = max(1.0, float(payload.get("durationSeconds", 1)))
    rms = float(payload.get("rms", 0.0))
    variability = float(payload.get("variability", 0.0))
    words = len(tokenize(transcript))
    wpm = words / duration * 60
    filler_count = sum(len(re.findall(rf"\b{re.escape(filler)}\b", transcript.lower())) for filler in FILLERS)

    pace = clamp(100 - abs(wpm - 145) * 0.8)
    volume = clamp(rms * 220)
    energy = clamp(45 + variability * 180 + rms * 80)
    fluency = clamp(100 - filler_count * 8 - abs(wpm - 145) * 0.25)

    return {
        "wordsPerMinute": round(wpm, 1),
        "pace": pace,
        "volume": volume,
        "energy": energy,
        "fluency": fluency,
        "fillerCount": filler_count,
        "note": "Voice analysis uses browser microphone level, variability, transcript length, and filler frequency.",
    }


def build_report(session_id: str) -> dict[str, Any]:
    resume = STORE.resumes.get(session_id)
    answers = STORE.answers.get(session_id, [])
    signals = STORE.signals.get(session_id, {})
    answer_score = round(sum(a["score"] for a in answers) / len(answers)) if answers else 0
    emotion = signals.get("emotion", {})
    voice = signals.get("voice", {})
    resume_score = resume["score"] if resume else 0
    delivery_score = round(
        (
            emotion.get("confidence", 0)
            + emotion.get("calm", 0)
            + emotion.get("engagement", 0)
            + voice.get("fluency", 0)
            + voice.get("pace", 0)
        )
        / 5
    )
    overall = clamp(resume_score * 0.3 + answer_score * 0.45 + delivery_score * 0.25)
    return {
        "overall": overall,
        "resumeScore": resume_score,
        "answerScore": answer_score,
        "deliveryScore": delivery_score,
        "resume": resume,
        "answers": answers[-3:],
        "emotion": emotion,
        "voice": voice,
        "nextSteps": [
            "Rewrite top resume projects with a model, metric, and measurable impact.",
            "Practice two STAR answers until they fit in 90 seconds.",
            "Record one mock interview daily and compare pace, filler count, and confidence trend.",
        ],
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "SmartInterviewCoach/1.0"

    def log_message(self, format: str, *args: Any) -> None:
        print(f"{self.address_string()} - {format % args}")

    def send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        data = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        return json.loads(raw or "{}")

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self.send_json({"ok": True, "service": "Smart AI Interview Coach"})
            return
        if parsed.path == "/api/roles":
            self.send_json({"roles": [{"id": key, "title": value["title"]} for key, value in ROLE_SKILLS.items()]})
            return
        if parsed.path == "/api/report":
            session_id = parse_qs(parsed.query).get("sessionId", ["demo"])[0]
            self.send_json(build_report(session_id))
            return
        self.serve_static(parsed.path)

    def do_POST(self) -> None:
        try:
            parsed = urlparse(self.path)
            payload = self.read_json()
            session_id = payload.get("sessionId") or "demo"
            role = payload.get("role") or "ai-engineer"

            if parsed.path == "/api/resume":
                result = analyze_resume(payload.get("text", ""), role)
                STORE.resumes[session_id] = result
                self.send_json(result)
                return
            if parsed.path == "/api/question":
                result = generate_question(role, payload.get("resumeText", ""))
                self.send_json(result)
                return
            if parsed.path == "/api/answer":
                result = analyze_answer(payload.get("answer", ""), payload.get("question", ""))
                STORE.answers.setdefault(session_id, []).append(result)
                self.send_json(result)
                return
            if parsed.path == "/api/emotion":
                result = analyze_emotion(payload)
                STORE.signals.setdefault(session_id, {})["emotion"] = result
                self.send_json(result)
                return
            if parsed.path == "/api/voice":
                result = analyze_voice(payload)
                STORE.signals.setdefault(session_id, {})["voice"] = result
                self.send_json(result)
                return
            self.send_json({"error": "Unknown endpoint"}, 404)
        except Exception as exc:
            self.send_json({"error": str(exc)}, 500)

    def serve_static(self, path: str) -> None:
        target = STATIC_DIR / "index.html" if path in {"/", ""} else STATIC_DIR / path.lstrip("/")
        target = target.resolve()
        if not str(target).startswith(str(STATIC_DIR.resolve())) or not target.exists():
            self.send_error(404)
            return
        content_type = "text/plain"
        if target.suffix == ".html":
            content_type = "text/html; charset=utf-8"
        elif target.suffix == ".css":
            content_type = "text/css; charset=utf-8"
        elif target.suffix == ".js":
            content_type = "application/javascript; charset=utf-8"
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def find_available_port(start_port: int) -> int:
    for candidate in range(start_port, start_port + MAX_PORT_ATTEMPTS + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((HOST, candidate))
                return candidate
            except OSError:
                continue
    raise OSError(f"No available port found from {start_port} to {start_port + MAX_PORT_ATTEMPTS}.")


def main() -> None:
    os.chdir(ROOT)
    port = find_available_port(PORT)
    if port != PORT:
        print(f"Port {PORT} is already in use. Starting on port {port} instead.")
    server = ThreadingHTTPServer((HOST, port), Handler)
    print(f"Smart AI Interview Coach running at http://{HOST}:{port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nSmart AI Interview Coach stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
