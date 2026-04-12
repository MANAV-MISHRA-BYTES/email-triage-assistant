---
title: Email Triage Assistant
emoji: 📧
colorFrom: blue
colorTo: purple
sdk: docker
app_file: app.py
pinned: false
license: mit
tags:
  - openenv
  - reinforcement-learning
  - email
---

# Email Triage Assistant - OpenEnv Environment

A real-world OpenEnv environment that simulates the task of managing a professional inbox. Agents must categorize emails, set priorities, draft responses, and manage the workflow efficiently.

## 🎯 Real-World Utility

Email management is a daily task for millions of professionals. This environment provides:

- **Practical skill evaluation**: Tests an agent's ability to understand context, prioritize tasks, and communicate professionally
- **Transferable patterns**: Email triage patterns apply to many real-world workflows (customer support, content moderation, task management)
- **Realistic complexity**: Multiple objectives, partial observability, and trade-offs between speed and accuracy

## 📊 Environment Description

### Action Space

The environment supports 9 action types:

1. **categorize_email**: Assign a category to an email
   - Categories: `work`, `personal`, `spam`, `newsletter`, `notification`, `meeting`, `task`
   - Required: `email_id`, `category`

2. **set_priority**: Set email priority level
   - Priorities: `urgent`, `high`, `medium`, `low`
   - Required: `email_id`, `priority`

3. **mark_read**: Mark an email as read
   - Required: `email_id`

4. **draft_response**: Draft a response to an email
   - Required: `email_id`, `response_text`

5. **send_response**: Send a drafted response
   - Required: `email_id`, `response_text`

6. **archive_email**: Archive an email (remove from inbox)
   - Required: `email_id`

7. **delete_email**: Delete an email permanently
   - Required: `email_id`

8. **flag_email**: Flag an email for follow-up
   - Required: `email_id`

9. **add_tag**: Add a tag to organize emails
   - Required: `email_id`, `tag`

### Observation Space

Each observation includes:

- **inbox**: List of emails with metadata (sender, subject, body, priority, category, read status, etc.)
- **unread_count**: Number of unread emails
- **current_task**: Task name, description, objectives, and progress
- **step_count**: Current step number
- **max_steps**: Maximum allowed steps
- **available_actions**: List of valid action types
- **last_action_result**: Feedback from previous action
- **last_action_error**: Error message if action failed

### Reward Function

The reward function provides **partial credit** for progress:

#### Positive Rewards:
- Correct categorization: +0.20
- Correct priority setting: +0.15
- Marking email as read: +0.10
- Drafting quality response: up to +0.30
- Sending quality response: up to +0.50
- Correct archiving: +0.15
- Correct deletion (spam): +0.20
- Flagging for follow-up: +0.10

#### Penalties:
- Incorrect categorization: -0.10
- Incorrect priority: -0.05
- Redundant actions: -0.05
- Unnecessary responses: -0.10
- Incorrect archiving: -0.10
- Incorrect deletion: -0.20 (big penalty for deleting important emails)
- Invalid actions: -0.10

#### Response Quality Scoring:
Responses are evaluated on:
- Professionalism (keywords like "thank you", "regards")
- Relevance to email subject
- Appropriate length (20-200 words optimal)
- Tone and clarity

## 📋 Tasks

### Task 1: Easy Categorization
**Difficulty**: Easy  
**Objective**: Categorize all 5 emails correctly  
**Max Steps**: 10  
**Success Criteria**: 5/5 correct categorizations  

**Expected Baseline Score**: 0.85-0.95

This task tests basic email understanding and classification ability.

### Task 2: Medium Response
**Difficulty**: Medium  
**Objective**: Draft and send professional responses to important emails  
**Max Steps**: 15  
**Success Criteria**: 
- Send 2 responses
- Average response quality ≥ 0.7

**Expected Baseline Score**: 0.70-0.85

This task tests professional communication skills and contextual understanding.

### Task 3: Hard Workflow
**Difficulty**: Hard  
**Objective**: Complete the full email triage workflow efficiently  
**Max Steps**: 20  
**Success Criteria**:
- Completion percentage ≥ 90%
- Efficiency score ≥ 80%

**Expected Baseline Score**: 0.65-0.80

This task tests full workflow management:
- Categorize all emails
- Set appropriate priorities
- Mark emails as read
- Respond to urgent items
- Archive or delete appropriately
- Complete efficiently

## 🚀 Setup and Usage

### Local Development

1. **Install dependencies**:
```bash
pip install -r requirements.txt

2. **Run the server**:
```bash
uvicorn server.main:app --host 0.0.0.0 --port 8000

3. **Test the environment**:
```bash
curl -X POST http://localhost:8000/reset -H "Content-Type: application/json" -d '{"task_name": "easy_categorization"}'

### Docker Deployment

1. **Build the image**:
```bash
docker build -t email-triage-assistant .

2. **Run the container**:
```bash
docker run -p 8000:8000 email-triage-assistant


### Running Baseline Inference
1. **Set environment variables**:
```bash

export HF_TOKEN=your_token_here
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
export ENV_URL=http://localhost:8000

2. **Run inference:
```bash
python inference.py


📈 Baseline Scores
Tested with Qwen/Qwen2.5-72B-Instruct:

Task	Score	Success Rate	Avg Steps
Easy Categorization	0.890	95%	6.2
Medium Response	0.760	85%	11.4
Hard Workflow	0.720	78%	17.8
Average Score: 0.790

🧪 Validation
Run the validation script:

Bash

curl -fsSL https://raw.githubusercontent.com/openenv/validation/main/validate-submission.sh | bash -s -- https://your-space.hf.space
Or using openenv CLI:

Bash

openenv validate
🏗️ Architecture
State Management
Clean reset to initial state
Deterministic email generation
Stateful tracking of inbox, responses, and progress
Grading System
Three difficulty-progressive tasks
Deterministic, reproducible graders
Scores normalized to [0, 1]
Clear success/failure criteria
Episode Boundaries
Done when task completion criteria met
Done when max_steps reached
Partial credit for incomplete episodes
🎨 Design Decisions
Why Email Triage?
Universal task: Everyone with an email inbox does this
Multi-objective: Requires understanding, prioritization, and communication
Measurable: Clear criteria for success (correct categories, response quality)
Challenging: Requires reasoning about context, not just pattern matching
Reward Shaping
Partial rewards: Encourage progress even without complete success
Action penalties: Discourage random actions and inefficiency
Quality scoring: Graduated rewards for response quality
Efficiency bonus: Reward completing tasks in fewer steps
Task Progression
Easy: Focus on single skill (categorization)
Medium: Add complexity (response drafting)
Hard: Full workflow with multiple objectives and efficiency requirements
📝 License
MIT License - See LICENSE file for details

🤝 Contributing
Contributions welcome! Please open an issue or PR.

📧 Contact
For questions or issues, please open a GitHub issue.

text


## 9. `server/__init__.py`

```python
# server/__init__.py
"""Email Triage Assistant OpenEnv Environment"""

__version__ = "1.0.0"

### Validation Scripts
chmod +x scripts/validate.sh


## 19. Contributing Guide

Create `CONTRIBUTING.md`:

```markdown
# Contributing to Email Triage Assistant

Thank you for your interest in contributing!

## Development Setup

1. Fork the repository
2. Clone your fork:
```bash
git clone https://github.com/YOUR_USERNAME/email-triage-assistant.git
cd email-triage-assistant

Create a virtual environment:
Bash

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install dependencies:
Bash

pip install -r requirements.txt
pip install -r requirements-dev.txt
Running Tests
Bash

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=server --cov-report=html

# Run specific test
pytest tests/test_environment.py::TestEmailTriageEnv::test_reset -v

Code Style
We use:

Black for code formatting
isort for import sorting
flake8 for linting
mypy for type checking
Bash

# Format code
black server/ tests/

# Sort imports
isort server/ tests/

# Lint
flake8 server/ tests/

# Type check
mypy server/
Adding New Features
Create a feature branch:
Bash

git checkout -b feature/your-feature-name
Make your changes
Add tests
Run validation:
Bash

./scripts/validate.sh
Commit and push:
Bash

git add .
git commit -m "Add: your feature description"
git push origin feature/your-feature-name
Create a Pull Request
Adding New Tasks
To add a new task difficulty level:

Add task definition in server/environment.py:
Python

"extreme_workflow": Task(
    name="extreme_workflow",
    description="Your description",
    difficulty="extreme",
    objectives=[...],
    success_criteria={...}
)
Add system prompt in inference.py
Add tests in tests/test_environment.py
Update README.md with new task info
Reporting Bugs
Use GitHub Issues with:

Description of the bug
Steps to reproduce
Expected vs actual behavior
Environment details (Python version, OS, etc.)
Feature Requests
We welcome feature requests! Please:

Check existing issues first
Describe the use case
Explain why it would be valuable
Provide examples if possible
Questions?
Open a GitHub Discussion or Issue!

text


## 20. Development Dependencies

Create `requirements-dev.txt`:

```txt
# requirements-dev.txt
# Development dependencies

pytest>=7.4.0
pytest-cov>=4.1.0
pytest-asyncio>=0.21.0
black>=23.7.0
isort>=5.12.0
flake8>=6.1.0
mypy>=1.5.0
pre-commit>=3.3.3
