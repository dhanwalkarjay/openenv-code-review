# OpenEnv Code Review Environment

## Motivation
This environment simulates a real software engineering workflow: reviewing pull request code and giving high-quality review feedback. It is designed for training and evaluating agent behavior on practical tasks that humans perform daily in software teams.

## Real-World Task Simulation
Domain: code review and static quality feedback.

Agent objective:
1. Inspect code snippet from a task.
2. Submit structured review actions (issue report + optional suggested fix).
3. Maximize grader score by finding valid issues with precise line references and useful remediation advice.

## OpenEnv API
The service exposes the required environment lifecycle endpoints:
- GET /reset?task=easy|medium|hard
- POST /step
- GET /state

Additional required hackathon endpoints:
- GET /tasks
- GET /grader
- GET /baseline

## Action Space
Action model fields:
- comment (string): review feedback text.
- line_number (int >= 1): code line referenced by the feedback.
- suggested_fix (optional string): remediation proposal.
- label (enum): style | performance | bug | security | maintainability.
- confidence (float 0.0 to 1.0): confidence in the finding.

## Observation Space
Observation model fields:
- task_id
- task_type
- title
- objective
- code
- step_count
- max_steps
- discovered_findings
- remaining_findings

## Reward Design
Reward is dense and trajectory-aware (not just terminal):
- Positive reward for discovering new valid findings.
- Bonus for high-quality suggested fix when a new valid finding is reported.
- Small quality bonus for detailed comments.
- Penalty for duplicate actions.
- Penalty for invalid line references.
- Penalty when agent reaches max steps without strong grader score.

This creates meaningful partial progress signals while discouraging looping and low-value behavior.

## Tasks and Difficulty
Three deterministic tasks with graders (0.0 to 1.0):
1. Easy: PEP8/readability review.
2. Medium: correctness + refactoring + robustness.
3. Hard: security review for JWT verification and authorization logic.

## Grader Behavior
Programmatic deterministic grader computes:
- coverage: fraction of expected findings matched.
- precision: fraction of submitted actions that are useful.
- line_accuracy: whether actions reference correct line range.
- fix_quality: whether suggested fixes are concrete and actionable.

Final score is a weighted blend in [0.0, 1.0].

## Local Setup
Windows PowerShell:
1. py -m venv venv
2. .\venv\Scripts\Activate.ps1
3. py -m pip install -r requirements.txt
4. uvicorn api.main:app --host 0.0.0.0 --port 7860 --reload

Git Bash:
1. python -m venv venv
2. source venv/Scripts/activate
3. python -m pip install -r requirements.txt
4. uvicorn api.main:app --host 0.0.0.0 --port 7860 --reload

## Docker
Build:
docker build -t openenv-code-review .

Run:
docker run --rm -p 7860:7860 openenv-code-review

## Baseline Inference
Set credentials:
- API_BASE_URL (optional, default: https://api.openai.com/v1)
- MODEL_NAME (optional, default: gpt-4o-mini)
- HF_TOKEN (preferred) or OPENAI_API_KEY

Run script directly:
- python inference.py

Run endpoint after server starts:
- GET /baseline

Or from Python:
- from inference import run_baseline
- run_baseline(model="gpt-4o-mini")

The baseline uses deterministic prompting with temperature 0 and returns per-task grader score and aggregate score.

## Hugging Face Spaces Deployment
1. Create a Docker Space.
2. Push this repository.
3. Ensure Space port is 7860.
4. Add secret HF_TOKEN (or OPENAI_API_KEY) for baseline endpoint.
5. Tag the Space with openenv.

## Validation Checklist Mapping
- OpenEnv endpoints + typed models: implemented.
- 3 graded tasks: implemented.
- Reward shaping with partial progress: implemented.
- Reproducible baseline: implemented.
- Dockerfile for container execution: included.
- openenv.yaml metadata and API mapping: included.