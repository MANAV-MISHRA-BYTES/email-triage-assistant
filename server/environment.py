# server/environment.py
import random
import json
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import uuid

from .models import *


@dataclass
class Task:
    """Represents a task in the environment"""
    name: str
    description: str
    difficulty: str  # "easy", "medium", "hard"
    objectives: List[str]
    success_criteria: Dict[str, Any]
    current_objective_index: int = 0
    completed: bool = False


class EmailTriageEnv:
    """Email Triage Assistant Environment"""
    
    def __init__(self, task_name: str = "easy_categorization"):
        self.task_name = task_name
        self.step_count = 0
        self.max_steps = 20
        self.inbox: List[Email] = []
        self.sent_responses: List[Dict] = []
        self.score = 0.0
        self.total_possible_score = 0.0
        self.current_task: Optional[Task] = None
        self.last_action_result: Optional[str] = None
        self.last_action_error: Optional[str] = None
        
        # Initialize with sample emails
        self._initialize_inbox()
        self._initialize_task()
    
    def _initialize_inbox(self):
        """Initialize the inbox with sample emails"""
        sample_emails = [
            {
                "sender": "boss@company.com",
                "subject": "Urgent: Quarterly Report Due Tomorrow",
                "body": "Please complete the quarterly report by EOD tomorrow. This is a high priority task.",
                "priority": EmailPriority.URGENT,
                "category": EmailCategory.WORK,
                "tags": ["report", "deadline"]
            },
            {
                "sender": "team@project.com", 
                "subject": "Weekly Team Meeting",
                "body": "Reminder: Weekly team meeting tomorrow at 10 AM in Conference Room B.",
                "priority": EmailPriority.MEDIUM,
                "category": EmailCategory.MEETING,
                "tags": ["meeting", "reminder"]
            },
            {
                "sender": "newsletter@tech.com",
                "subject": "Weekly Tech News Digest",
                "body": "This week in tech: AI breakthroughs, new frameworks, and industry trends.",
                "priority": EmailPriority.LOW,
                "category": EmailCategory.NEWSLETTER,
                "tags": ["newsletter"]
            },
            {
                "sender": "friend@gmail.com",
                "subject": "Dinner plans this weekend?",
                "body": "Hey! Are you free for dinner this Saturday? Let me know!",
                "priority": EmailPriority.LOW,
                "category": EmailCategory.PERSONAL,
                "tags": ["personal", "social"]
            },
            {
                "sender": "spam@fake.com",
                "subject": "YOU WON $1,000,000!",
                "body": "Congratulations! You've won $1,000,000. Click here to claim!",
                "priority": EmailPriority.LOW,
                "category": EmailCategory.SPAM,
                "tags": ["spam"]
            }
        ]
        
        self.inbox = []
        for i, email_data in enumerate(sample_emails):
            email = Email(
                id=str(uuid.uuid4()),
                sender=email_data["sender"],
                subject=email_data["subject"],
                body=email_data["body"],
                received_at=datetime.now() - timedelta(hours=i*2),
                priority=email_data["priority"],
                category=email_data["category"],
                read=False,
                responded=False,
                tags=email_data["tags"]
            )
            self.inbox.append(email)
    
    def _initialize_task(self):
        """Initialize the current task based on task_name"""
        tasks = {
            "easy_categorization": Task(
                name="easy_categorization",
                description="Categorize all emails correctly by type",
                difficulty="easy",
                objectives=[
                    "Categorize the urgent work email as 'work'",
                    "Categorize the meeting email as 'meeting'", 
                    "Categorize the newsletter as 'newsletter'",
                    "Categorize the personal email as 'personal'",
                    "Categorize the spam email as 'spam'"
                ],
                success_criteria={
                    "required_correct_categorizations": 5,
                    "max_steps": 10,
                    "min_score": 0.8
                }
            ),
            "medium_response": Task(
                name="medium_response",
                description="Draft and send appropriate responses to important emails",
                difficulty="medium",
                objectives=[
                    "Mark the urgent email as read",
                    "Draft a professional response to the urgent email",
                    "Send the response to the urgent email",
                    "Mark the meeting email as read",
                    "Draft a response confirming attendance to the meeting"
                ],
                success_criteria={
                    "required_responses": 2,
                    "response_quality_threshold": 0.7,
                    "max_steps": 15,
                    "min_score": 0.7
                }
            ),
            "hard_workflow": Task(
                name="hard_workflow",
                description="Complete the full email triage workflow efficiently",
                difficulty="hard",
                objectives=[
                    "Categorize all emails correctly",
                    "Set appropriate priorities for all emails",
                    "Mark all non-spam emails as read",
                    "Draft responses to work-related emails",
                    "Send responses to urgent emails",
                    "Archive or delete spam emails"
                ],
                success_criteria={
                    "completion_percentage": 0.9,
                    "efficiency_score": 0.8,
                    "max_steps": 20,
                    "min_score": 0.8
                }
            )
        }
        
        self.current_task = tasks.get(self.task_name, tasks["easy_categorization"])
        self.total_possible_score = self._calculate_total_possible_score()
    
    def _calculate_total_possible_score(self) -> float:
        """Calculate total possible score for the current task"""
        if self.current_task.difficulty == "easy":
            return 1.0
        elif self.current_task.difficulty == "medium":
            return 1.5
        else:  # hard
            return 2.0
    
    def reset(self, task_name: Optional[str] = None) -> Observation:
        """Reset the environment to initial state"""
        if task_name:
            self.task_name = task_name
        
        self.step_count = 0
        self.score = 0.0
        self.sent_responses = []
        self.last_action_result = None
        self.last_action_error = None
        
        self._initialize_inbox()
        self._initialize_task()
        self.total_possible_score = self._calculate_total_possible_score()
        
        return self._get_observation()
    
    def step(self, action: Action) -> Tuple[Observation, Reward, bool, Dict[str, Any]]:
        """Execute an action and return the result"""
        self.step_count += 1
        self.last_action_result = None
        self.last_action_error = None
        
        reward_value = 0.0
        reward_breakdown = {}
        
        try:
            # Validate action
            self._validate_action(action)
            
            # Execute action
            if action.action_type == "categorize_email":
                reward_value, reward_breakdown = self._categorize_email(action)
            elif action.action_type == "set_priority":
                reward_value, reward_breakdown = self._set_priority(action)
            elif action.action_type == "mark_read":
                reward_value, reward_breakdown = self._mark_read(action)
            elif action.action_type == "draft_response":
                reward_value, reward_breakdown = self._draft_response(action)
            elif action.action_type == "send_response":
                reward_value, reward_breakdown = self._send_response(action)
            elif action.action_type == "archive_email":
                reward_value, reward_breakdown = self._archive_email(action)
            elif action.action_type == "delete_email":
                reward_value, reward_breakdown = self._delete_email(action)
            elif action.action_type == "flag_email":
                reward_value, reward_breakdown = self._flag_email(action)
            elif action.action_type == "add_tag":
                reward_value, reward_breakdown = self._add_tag(action)
            else:
                raise ValueError(f"Unknown action type: {action.action_type}")
            
            # Update score
            self.score += reward_value
            self.last_action_result = f"Action '{action.action_type}' completed successfully"
            
        except Exception as e:
            self.last_action_error = str(e)
            reward_value = -0.1  # Penalty for invalid action
            reward_breakdown = {"error_penalty": -0.1}
        
        # Check if task is completed
        done = self._check_task_completion() or self.step_count >= self.max_steps
        
        # Calculate normalized reward
        normalized_reward = min(max(reward_value, 0.0), 1.0)
        
        reward = Reward(
            value=normalized_reward,
            breakdown=reward_breakdown,
            message=self.last_action_result or ""
        )
        
        info = {
            "step": self.step_count,
            "score": self.score,
            "task_progress": self._calculate_task_progress(),
            "done": done
        }
        
        return self._get_observation(), reward, done, info
    
    def _validate_action(self, action: Action):
        """Validate the action before execution"""
        if action.email_id:
            email = self._get_email_by_id(action.email_id)
            if not email:
                raise ValueError(f"Email with ID {action.email_id} not found")
    
    def _get_email_by_id(self, email_id: str) -> Optional[Email]:
        """Find an email by its ID"""
        for email in self.inbox:
            if email.id == email_id:
                return email
        return None
    
    def _categorize_email(self, action: Action) -> Tuple[float, Dict[str, float]]:
        """Categorize an email"""
        email = self._get_email_by_id(action.email_id)
        if not email:
            raise ValueError("Email not found")
        
        old_category = email.category
        email.category = action.category
        
        # Calculate reward based on correctness
        reward = 0.0
        breakdown = {}
        
        # Ground truth mapping (simplified - in reality this would be more complex)
        ground_truth = {
            "boss@company.com": EmailCategory.WORK,
            "team@project.com": EmailCategory.MEETING,
            "newsletter@tech.com": EmailCategory.NEWSLETTER,
            "friend@gmail.com": EmailCategory.PERSONAL,
            "spam@fake.com": EmailCategory.SPAM
        }
        
        correct_category = ground_truth.get(email.sender)
        if correct_category and email.category == correct_category:
            reward = 0.2
            breakdown["correct_categorization"] = 0.2
        else:
            reward = -0.1
            breakdown["incorrect_categorization"] = -0.1
        
        return reward, breakdown
    
    def _set_priority(self, action: Action) -> Tuple[float, Dict[str, float]]:
        """Set email priority"""
        email = self._get_email_by_id(action.email_id)
        if not email:
            raise ValueError("Email not found")
        
        old_priority = email.priority
        email.priority = action.priority
        
        # Calculate reward based on appropriateness
        reward = 0.0
        breakdown = {}
        
        # Ground truth priorities
        ground_truth_priority = {
            "boss@company.com": EmailPriority.URGENT,
            "team@project.com": EmailPriority.MEDIUM,
            "newsletter@tech.com": EmailPriority.LOW,
            "friend@gmail.com": EmailPriority.LOW,
            "spam@fake.com": EmailPriority.LOW
        }
        
        correct_priority = ground_truth_priority.get(email.sender)
        if correct_priority and email.priority == correct_priority:
            reward = 0.15
            breakdown["correct_priority"] = 0.15
        else:
            reward = -0.05
            breakdown["incorrect_priority"] = -0.05
        
        return reward, breakdown
    
    def _mark_read(self, action: Action) -> Tuple[float, Dict[str, float]]:
        """Mark an email as read"""
        email = self._get_email_by_id(action.email_id)
        if not email:
            raise ValueError("Email not found")
        
        if not email.read:
            email.read = True
            reward = 0.1
            breakdown = {"mark_read": 0.1}
        else:
            reward = -0.05  # Penalty for redundant action
            breakdown = {"redundant_action": -0.05}
        
        return reward, breakdown
    
    def _draft_response(self, action: Action) -> Tuple[float, Dict[str, float]]:
        """Draft a response to an email"""
        email = self._get_email_by_id(action.email_id)
        if not email:
            raise ValueError("Email not found")
        
        # Check if email should have a response
        should_respond = email.sender in ["boss@company.com", "team@project.com"]
        
        if not should_respond:
            reward = -0.1
            breakdown = {"unnecessary_response": -0.1}
            return reward, breakdown
        
        # Evaluate response quality (simplified)
        response_quality = self._evaluate_response_quality(action.response_text, email)
        
        reward = response_quality * 0.3  # Max 0.3 for drafting
        breakdown = {
            "response_draft_quality": reward,
            "response_length_bonus": min(len(action.response_text) / 500, 0.1)
        }
        
        # Add small bonus for drafting
        reward += 0.05
        breakdown["drafting_bonus"] = 0.05
        
        return min(reward, 0.3), breakdown
    
    def _send_response(self, action: Action) -> Tuple[float, Dict[str, float]]:
        """Send a drafted response"""
        email = self._get_email_by_id(action.email_id)
        if not email:
            raise ValueError("Email not found")
        
        # Check if email should have a response
        should_respond = email.sender in ["boss@company.com", "team@project.com"]
        
        if not should_respond:
            reward = -0.2
            breakdown = {"unnecessary_send": -0.2}
            return reward, breakdown
        
        # Evaluate response quality
        response_quality = self._evaluate_response_quality(action.response_text, email)
        
        # Record the sent response
        self.sent_responses.append({
            "email_id": email.id,
            "response": action.response_text,
            "quality": response_quality,
            "timestamp": datetime.now()
        })
        
        email.responded = True
        
        reward = response_quality * 0.5  # Max 0.5 for sending
        breakdown = {
            "response_send_quality": reward,
            "timeliness_bonus": 0.1 if self.step_count < 10 else 0.05
        }
        
        return min(reward, 0.5), breakdown
    
    def _archive_email(self, action: Action) -> Tuple[float, Dict[str, float]]:
        """Archive an email (remove from inbox)"""
        email = self._get_email_by_id(action.email_id)
        if not email:
            raise ValueError("Email not found")
        
        # Check if email should be archived
        should_archive = email.sender in ["newsletter@tech.com", "friend@gmail.com"]
        
        if should_archive:
            self.inbox = [e for e in self.inbox if e.id != email.id]
            reward = 0.15
            breakdown = {"correct_archive": 0.15}
        else:
            reward = -0.1
            breakdown = {"incorrect_archive": -0.1}
        
        return reward, breakdown
    
    def _delete_email(self, action: Action) -> Tuple[float, Dict[str, float]]:
        """Delete an email"""
        email = self._get_email_by_id(action.email_id)
        if not email:
            raise ValueError("Email not found")
        
        # Check if email should be deleted (spam)
        should_delete = email.sender == "spam@fake.com"
        
        if should_delete:
            self.inbox = [e for e in self.inbox if e.id != email.id]
            reward = 0.2
            breakdown = {"correct_deletion": 0.2}
        else:
            reward = -0.2  # Big penalty for deleting important email
            breakdown = {"incorrect_deletion": -0.2}
        
        return reward, breakdown
    
    def _flag_email(self, action: Action) -> Tuple[float, Dict[str, float]]:
        """Flag an email for follow-up"""
        email = self._get_email_by_id(action.email_id)
        if not email:
            raise ValueError("Email not found")
        
        if "flagged" not in email.tags:
            email.tags.append("flagged")
            reward = 0.1
            breakdown = {"flag_email": 0.1}
        else:
            reward = -0.05
            breakdown = {"redundant_flag": -0.05}
        
        return reward, breakdown
    
    def _add_tag(self, action: Action) -> Tuple[float, Dict[str, float]]:
        """Add a tag to an email"""
        email = self._get_email_by_id(action.email_id)
        if not email:
            raise ValueError("Email not found")
        
        if action.tag and action.tag not in email.tags:
            email.tags.append(action.tag)
            reward = 0.05
            breakdown = {"add_tag": 0.05}
        else:
            reward = -0.02
            breakdown = {"redundant_tag": -0.02}
        
        return reward, breakdown
    
    def _evaluate_response_quality(self, response: str, email: Email) -> float:
        """Evaluate the quality of a response (simplified)"""
        if not response or len(response.strip()) < 10:
            return 0.0
        
        quality = 0.5  # Base score
        
        # Check for professionalism
        professional_keywords = ["thank you", "regards", "sincerely", "best", "please"]
        if any(keyword in response.lower() for keyword in professional_keywords):
            quality += 0.2
        
        # Check for relevance to email subject
        subject_keywords = email.subject.lower().split()
        relevant_words = sum(1 for word in subject_keywords if word in response.lower())
        if relevant_words > 0:
            quality += 0.1
        
        # Check response length (not too short, not too long)
        word_count = len(response.split())
        if 20 <= word_count <= 200:
            quality += 0.2
        
        return min(quality, 1.0)
    
    def _check_task_completion(self) -> bool:
        """Check if the current task is completed"""
        if not self.current_task:
            return False
        
        progress = self._calculate_task_progress()
        
        if self.current_task.difficulty == "easy":
            # Need all categorizations correct
            correct_categorizations = self._count_correct_categorizations()
            required = self.current_task.success_criteria["required_correct_categorizations"]
            return correct_categorizations >= required
            
        elif self.current_task.difficulty == "medium":
            # Need responses sent with good quality
            sent_count = len(self.sent_responses)
            required = self.current_task.success_criteria["required_responses"]
            
            if sent_count < required:
                return False
            
            # Check response quality
            avg_quality = sum(r["quality"] for r in self.sent_responses) / sent_count
            quality_threshold = self.current_task.success_criteria["response_quality_threshold"]
            
            return avg_quality >= quality_threshold
            
        else:  # hard
            # Need high completion percentage
            completion_pct = progress.get("completion_percentage", 0.0)
            required_pct = self.current_task.success_criteria["completion_percentage"]
            
            return completion_pct >= required_pct
    
    def _count_correct_categorizations(self) -> int:
        """Count correctly categorized emails"""
        ground_truth = {
            "boss@company.com": EmailCategory.WORK,
            "team@project.com": EmailCategory.MEETING,
            "newsletter@tech.com": EmailCategory.NEWSLETTER,
            "friend@gmail.com": EmailCategory.PERSONAL,
            "spam@fake.com": EmailCategory.SPAM
        }
        
        correct = 0
        for email in self.inbox:
            correct_category = ground_truth.get(email.sender)
            if correct_category and email.category == correct_category:
                correct += 1
        
        return correct
    
    def _calculate_task_progress(self) -> Dict[str, float]:
        """Calculate progress towards task completion"""
        if not self.current_task:
            return {}
        
        progress = {}
        
        if self.current_task.difficulty == "easy":
            correct = self._count_correct_categorizations()
            total = len(self.inbox)
            progress["categorization_accuracy"] = correct / total if total > 0 else 0.0
            progress["completion_percentage"] = correct / self.current_task.success_criteria["required_correct_categorizations"]
            
        elif self.current_task.difficulty == "medium":
            sent_count = len(self.sent_responses)
            required = self.current_task.success_criteria["required_responses"]
            
            progress["responses_sent"] = sent_count
            progress["responses_required"] = required
            progress["completion_percentage"] = sent_count / required if required > 0 else 0.0
            
            if sent_count > 0:
                avg_quality = sum(r["quality"] for r in self.sent_responses) / sent_count
                progress["average_response_quality"] = avg_quality
            else:
                progress["average_response_quality"] = 0.0
                
        else:  # hard
            # Calculate multiple metrics
            correct_categorizations = self._count_correct_categorizations()
            total_emails = len(self.inbox) + len(self.sent_responses)  # Include archived/deleted
            
            read_count = sum(1 for email in self.inbox if email.read)
            should_be_read = sum(1 for email in self.inbox if email.sender != "spam@fake.com")
            
            progress["categorization_accuracy"] = correct_categorizations / total_emails if total_emails > 0 else 0.0
            progress["inbox_read_rate"] = read_count / should_be_read if should_be_read > 0 else 0.0
            progress["response_rate"] = len(self.sent_responses) / 2  # 2 emails should have responses
            progress["efficiency"] = 1.0 - (self.step_count / self.max_steps)
            
            # Weighted average
            weights = {
                "categorization_accuracy": 0.3,
                "inbox_read_rate": 0.2,
                "response_rate": 0.3,
                "efficiency": 0.2
            }
            
            completion = sum(progress.get(metric, 0.0) * weight 
                           for metric, weight in weights.items())
            progress["completion_percentage"] = completion
        
        return progress
    
    def _get_observation(self) -> Observation:
        """Get the current observation"""
        return Observation(
            inbox=self.inbox,
            unread_count=sum(1 for email in self.inbox if not email.read),
            current_task={
                "name": self.current_task.name if self.current_task else "",
                "description": self.current_task.description if self.current_task else "",
                "difficulty": self.current_task.difficulty if self.current_task else "",
                "objectives": self.current_task.objectives if self.current_task else [],
                "current_objective_index": self.current_task.current_objective_index if self.current_task else 0
            },
            step_count=self.step_count,
            max_steps=self.max_steps,
            last_action_result=self.last_action_result,
            last_action_error=self.last_action_error
        )
    
    def state(self) -> Dict[str, Any]:
        """Get the current state of the environment"""
        return {
            "inbox": [email.dict() for email in self.inbox],
            "step_count": self.step_count,
            "score": self.score,
            "task_name": self.task_name,
            "sent_responses": self.sent_responses,
            "task_progress": self._calculate_task_progress()
        }