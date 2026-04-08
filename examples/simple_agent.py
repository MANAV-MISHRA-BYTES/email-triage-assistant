# examples/simple_agent.py
"""
Simple example agent for Email Triage Assistant
"""
import requests
import json

ENV_URL = "http://localhost:8000"


def simple_categorization_agent():
    """Simple rule-based agent for email categorization"""
    
    # Reset environment
    response = requests.post(f"{ENV_URL}/reset", json={"task_name": "easy_categorization"})
    obs = response.json()
    
    print("Starting Email Categorization Task")
    print(f"Inbox has {len(obs['inbox'])} emails")
    print()
    
    # Simple categorization rules
    categorization_rules = {
        "boss": "work",
        "team": "meeting",
        "newsletter": "newsletter",
        "friend": "personal",
        "spam": "spam",
        "fake": "spam"
    }
    
    total_reward = 0
    step = 0
    
    for email in obs['inbox']:
        step += 1
        sender = email['sender'].lower()
        
        # Determine category based on sender
        category = "work"  # default
        for keyword, cat in categorization_rules.items():
            if keyword in sender:
                category = cat
                break
        
        # Take action
        action = {
            "action_type": "categorize_email",
            "email_id": email['id'],
            "category": category
        }
        
        print(f"Step {step}: Categorizing email from {email['sender']} as '{category}'")
        
        response = requests.post(f"{ENV_URL}/step", json={"action": action})
        result = response.json()
        
        reward = result['reward']['value']
        total_reward += reward
        
        print(f"  Reward: {reward:.2f}")
        print(f"  Message: {result['reward']['message']}")
        print()
        
        if result['done']:
            break
    
    print(f"Task completed!")
    print(f"Total reward: {total_reward:.2f}")
    print(f"Steps taken: {step}")
    
    # Calculate score
    score = total_reward / 1.0  # Max possible for easy task
    print(f"Score: {score:.3f}")
    
    return score


if __name__ == "__main__":
    score = simple_categorization_agent()
    print(f"\nFinal Score: {score:.3f}")
    
    if score >= 0.8:
        print("✅ SUCCESS!")
    else:
        print("❌ FAILED - Score too low")