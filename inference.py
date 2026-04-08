#!/usr/bin/env python3
"""
Baseline inference script for Email Triage Assistant environment.
Must follow exact stdout format requirements.
"""
import asyncio
import os
import json
import textwrap
from typing import List, Optional, Dict, Any
from datetime import datetime

from openai import OpenAI
import requests

# Environment configuration
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")
ENV_URL = os.getenv("ENV_URL", "http://localhost:8000")

# Task configuration
TASKS = ["easy_categorization", "medium_response", "hard_workflow"]
BENCHMARK = "email-triage-assistant"
MAX_STEPS = 20
TEMPERATURE = 0.7
MAX_TOKENS = 500

# System prompts for different tasks
SYSTEM_PROMPTS = {
    "easy_categorization": textwrap.dedent("""
        You are an email triage assistant. Your task is to categorize emails correctly.
        
        Available actions:
        1. categorize_email - Categorize an email (work, personal, spam, newsletter, notification, meeting, task)
        2. set_priority - Set email priority (urgent, high, medium, low)
        3. mark_read - Mark an email as read
        4. Other actions are available but focus on categorization for this task.
        
        Instructions:
        - Read each email carefully
        - Categorize emails based on sender, subject, and content
        - Work emails: from professional contacts, about work topics
        - Personal emails: from friends/family, about personal matters
        - Spam: suspicious senders, too good to be true offers
        - Newsletter: mass emails from companies/organizations
        - Meeting: emails about meetings, appointments
        - Task: emails assigning work tasks
        
        Respond with a JSON object containing:
        {
            "action_type": "categorize_email",
            "email_id": "<email_id>",
            "category": "<category>"
        }
        
        Only respond with the JSON object, no other text.
    """),
    
    "medium_response": textwrap.dedent("""
        You are an email triage assistant. Your task is to draft and send appropriate responses.
        
        Available actions:
        1. mark_read - Mark important emails as read first
        2. draft_response - Draft a response to an email
        3. send_response - Send a drafted response
        4. categorize_email - Categorize emails if needed
        
        Instructions:
        - First, mark urgent/important emails as read
        - Draft professional responses to work-related emails
        - Responses should be polite, concise, and address the email content
        - Send responses when they are ready
        - Ignore spam and newsletters
        
        Respond with a JSON object containing the action.
        Example for drafting response:
        {
                        "action_type": "draft_response",
            "email_id": "<email_id>",
            "response_text": "Your professional response here"
        }
        
        Example for sending:
        {
            "action_type": "send_response",
            "email_id": "<email_id>",
            "response_text": "Your professional response here"
        }
        
        Only respond with the JSON object, no other text.
    """),
    
    "hard_workflow": textwrap.dedent("""
        You are an email triage assistant. Complete the full email management workflow.
        
        Available actions:
        1. categorize_email - Categorize emails
        2. set_priority - Set appropriate priorities
        3. mark_read - Mark emails as read
        4. draft_response - Draft responses
        5. send_response - Send responses
        6. archive_email - Archive less important emails
        7. delete_email - Delete spam
        8. flag_email - Flag emails for follow-up
        9. add_tag - Add tags to organize emails
        
        Instructions:
        - Categorize all emails correctly
        - Set appropriate priorities (urgent for deadlines, low for newsletters)
        - Mark non-spam emails as read
        - Draft and send responses to urgent work emails
        - Archive newsletters and personal emails after reading
        - Delete spam immediately
        - Flag important items needing follow-up
        - Complete the workflow efficiently
        
        Respond with a JSON object containing the action.
        Only respond with the JSON object, no other text.
    """)
}


def log_start(task: str, env: str, model: str) -> None:
    """Log the start of an episode"""
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    """Log a step"""
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    """Log the end of an episode"""
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)


def build_user_prompt(observation: Dict[str, Any], task_name: str, step: int) -> str:
    """Build the user prompt based on observation"""
    inbox = observation.get("inbox", [])
    current_task = observation.get("current_task", {})
    unread_count = observation.get("unread_count", 0)
    last_result = observation.get("last_action_result", "")
    
    # Format inbox for display
    inbox_summary = []
    for i, email in enumerate(inbox[:5]):  # Show first 5 emails
        inbox_summary.append(
            f"{i+1}. ID: {email['id'][:8]}... | From: {email['sender']} | Subject: {email['subject']}\n"
            f"   Category: {email.get('category', 'unknown')} | Priority: {email.get('priority', 'medium')} | "
            f"Read: {email.get('read', False)} | Responded: {email.get('responded', False)}\n"
            f"   Body preview: {email['body'][:100]}..."
        )
    
    inbox_text = "\n\n".join(inbox_summary) if inbox_summary else "No emails in inbox"
    
    prompt = textwrap.dedent(f"""
        Task: {current_task.get('name', task_name)}
        Description: {current_task.get('description', '')}
        Step: {step}
        
        Inbox ({len(inbox)} emails, {unread_count} unread):
        {inbox_text}
        
        Last action result: {last_result if last_result else 'None'}
        
        What action should you take next? Respond with a JSON object only.
    """).strip()
    
    return prompt


def get_model_action(client: OpenAI, observation: Dict[str, Any], task_name: str, step: int) -> Dict[str, Any]:
    """Get the next action from the model"""
    system_prompt = SYSTEM_PROMPTS.get(task_name, SYSTEM_PROMPTS["easy_categorization"])
    user_prompt = build_user_prompt(observation, task_name, step)
    
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )
        
        response_text = (completion.choices[0].message.content or "").strip()
        
        # Try to extract JSON from response
        # Sometimes models add markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        # Parse JSON
        action = json.loads(response_text)
        
        # Validate required fields
        if "action_type" not in action:
            raise ValueError("Missing action_type in response")
        
        return action
        
    except json.JSONDecodeError as e:
        print(f"[DEBUG] JSON decode error: {e}, response: {response_text[:200]}", flush=True)
        # Fallback action
        inbox = observation.get("inbox", [])
        if inbox:
            return {
                "action_type": "mark_read",
                "email_id": inbox[0]["id"]
            }
        return {"action_type": "mark_read", "email_id": "unknown"}
    except Exception as e:
        print(f"[DEBUG] Model request failed: {e}", flush=True)
        # Fallback action
        inbox = observation.get("inbox", [])
        if inbox:
            return {
                "action_type": "mark_read",
                "email_id": inbox[0]["id"]
            }
        return {"action_type": "mark_read", "email_id": "unknown"}


def reset_env(task_name: str) -> Dict[str, Any]:
    """Reset the environment"""
    response = requests.post(
        f"{ENV_URL}/reset",
        json={"task_name": task_name},
        timeout=30
    )
    response.raise_for_status()
    return response.json()


def step_env(action: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a step in the environment"""
    response = requests.post(
        f"{ENV_URL}/step",
        json={"action": action},
        timeout=30
    )
    response.raise_for_status()
    return response.json()


def calculate_score(rewards: List[float], task_name: str) -> float:
    """Calculate normalized score [0, 1] from rewards"""
    if not rewards:
        return 0.0
    
    total_reward = sum(rewards)
    
    # Normalize based on task difficulty
    # Easy: max possible ~1.0 (5 categorizations * 0.2)
    # Medium: max possible ~1.5 (2 responses * 0.5 + extras)
    # Hard: max possible ~2.0 (full workflow)
    
    max_possible = {
        "easy_categorization": 1.0,
        "medium_response": 1.5,
        "hard_workflow": 2.0
    }
    
    max_score = max_possible.get(task_name, 1.0)
    
    # Normalize to [0, 1]
    score = total_reward / max_score
    score = min(max(score, 0.0), 1.0)  # Clamp to [0, 1]
    
    return score


def run_task(client: OpenAI, task_name: str) -> Dict[str, Any]:
    """Run a single task"""
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False
    
    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)
    
    try:
        # Reset environment
        observation = reset_env(task_name)
        
        for step in range(1, MAX_STEPS + 1):
            # Get action from model
            action = get_model_action(client, observation, task_name, step)
            
            # Execute step
            result = step_env(action)
            
            observation = result.get("observation", {})
            reward_data = result.get("reward", {})
            reward = reward_data.get("value", 0.0)
            done = result.get("done", False)
            
            # Get error from observation
            error = observation.get("last_action_error", None)
            
            rewards.append(reward)
            steps_taken = step
            
            # Format action for logging (simplified)
            action_str = f"{action.get('action_type', 'unknown')}"
            if action.get('email_id'):
                action_str += f"({action['email_id'][:8]}...)"
            
            log_step(step=step, action=action_str, reward=reward, done=done, error=error)
            
            if done:
                break
        
        # Calculate final score
        score = calculate_score(rewards, task_name)
        success = score >= 0.5  # Success if score is at least 0.5
        
    except Exception as e:
        print(f"[DEBUG] Task execution error: {e}", flush=True)
        score = 0.0
        success = False
    
    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)
    
    return {
        "task": task_name,
        "score": score,
        "success": success,
        "steps": steps_taken,
        "rewards": rewards
    }


def main():
    """Main entry point"""
    # Initialize OpenAI client
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
    
    # Run all tasks
    results = []
    for task_name in TASKS:
        print(f"\n{'='*60}", flush=True)
        print(f"Running task: {task_name}", flush=True)
        print(f"{'='*60}\n", flush=True)
        
        result = run_task(client, task_name)
        results.append(result)
    
    # Print summary
    print(f"\n{'='*60}", flush=True)
    print("SUMMARY", flush=True)
    print(f"{'='*60}", flush=True)
    for result in results:
        print(f"Task: {result['task']}", flush=True)
        print(f"  Score: {result['score']:.3f}", flush=True)
        print(f"  Success: {result['success']}", flush=True)
        print(f"  Steps: {result['steps']}", flush=True)
        print(f"  Total Reward: {sum(result['rewards']):.2f}", flush=True)
    
    avg_score = sum(r['score'] for r in results) / len(results) if results else 0.0
    print(f"\nAverage Score: {avg_score:.3f}", flush=True)


if __name__ == "__main__":
    main()