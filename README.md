# Smart AI Interview Coach

Full-stack local project for interview preparation with:

- Resume analysis using NLP-style keyword, structure, impact, and role-match scoring.
- Interview question generation for AI/ML Engineer, Software Engineer, and Data Scientist roles.
- Answer analysis with STAR coverage, clarity, relevance, technical depth, and filler-word checks.
- Webcam-based emotion/posture proxy analysis using computer-vision frame features.
- Microphone-based voice analysis using pace, volume, energy, fluency, and transcript data.
- Final readiness report combining resume, answer, emotion, and voice signals.

## Run Clearly

```bash
cd "/Users/mvijayakumarreddy/Desktop/Smart AI Interview Coach with Emotion, Voice and Resume Analysis"
bash run_project.sh
```

Then open:

```text
http://127.0.0.1:8000
```

Keep the terminal open while using the website. Press `Ctrl+C` to stop the project.

## Run in VS Code

1. Open this folder in VS Code.
2. Press `Cmd+Shift+B`.
3. Select `Run Smart AI Interview Coach`.
5. Open `http://127.0.0.1:8000`.

You can also open the Run and Debug panel and select `Run Smart AI Interview Coach`.

## Publish as a Website

This project has a backend API, so deploy it as a Python web service, not as a static-only site.

Recommended Render settings:

```text
Service type: Web Service
Runtime: Python
Build command: pip install -r requirements.txt
Start command: python app.py
Health check path: /api/health
Environment variable: HOST=0.0.0.0
```

The included `render.yaml` file already contains these settings for Render Blueprint deployment.

## Project Structure

```text
app.py              # Backend API and static file server
frontend/index.html # App UI
frontend/styles.css # Responsive styling
frontend/app.js     # Browser camera, voice, resume, and API logic
```

## Notes

This version is intentionally dependency-free so it runs immediately on a fresh machine with Python installed. The backend is organized so real models can be added later:

- Replace `analyze_resume` with spaCy, sentence-transformers, or an LLM scoring pipeline.
- Replace `analyze_emotion` with OpenCV plus a CNN/ViT emotion model.
- Replace `analyze_voice` with librosa, wav2vec2, or Whisper-based fluency analysis.
