# tests/test_environment.py
"""
Unit tests for Email Triage Assistant environment
"""
import pytest
from datetime import datetime
from server.environment import EmailTriageEnv
from server.models import Action, EmailCategory, EmailPriority


class TestEmailTriageEnv:
    """Test cases for the email triage environment"""
    
    def test_reset(self):
        """Test environment reset"""
        env = EmailTriageEnv(task_name="easy_categorization")
        obs = env.reset()
        
        assert obs.step_count == 0
        assert len(obs.inbox) == 5
        assert obs.unread_count == 5
        assert env.score == 0.0
    
    def test_categorize_email_correct(self):
        """Test correct email categorization"""
        env = EmailTriageEnv(task_name="easy_categorization")
        env.reset()
        
        # Find the spam email
        spam_email = None
        for email in env.inbox:
            if email.sender == "spam@fake.com":
                spam_email = email
                break
        
        assert spam_email is not None
        
        # Categorize as spam
        action = Action(
            action_type="categorize_email",
            email_id=spam_email.id,
            category=EmailCategory.SPAM
        )
        
        obs, reward, done, info = env.step(action)
        
        assert reward.value > 0.0
        assert "correct_categorization" in reward.breakdown
    
    def test_categorize_email_incorrect(self):
        """Test incorrect email categorization"""
        env = EmailTriageEnv(task_name="easy_categorization")
        env.reset()
        
        # Find the work email
        work_email = None
        for email in env.inbox:
            if email.sender == "boss@company.com":
                work_email = email
                break
        
        assert work_email is not None
        
        # Incorrectly categorize as personal
        action = Action(
            action_type="categorize_email",
            email_id=work_email.id,
            category=EmailCategory.PERSONAL
        )
        
        obs, reward, done, info = env.step(action)
        
        assert reward.value == 0.0  # Clamped negative to 0
        assert "incorrect_categorization" in reward.breakdown
    
    def test_set_priority(self):
        """Test setting email priority"""
        env = EmailTriageEnv(task_name="easy_categorization")
        env.reset()
        
        # Find urgent email
        urgent_email = None
        for email in env.inbox:
            if email.sender == "boss@company.com":
                urgent_email = email
                break
        
        assert urgent_email is not None
        
        # Set priority to urgent
        action = Action(
            action_type="set_priority",
            email_id=urgent_email.id,
            priority=EmailPriority.URGENT
        )
        
        obs, reward, done, info = env.step(action)
        
        assert reward.value > 0.0
        assert urgent_email.priority == EmailPriority.URGENT
    
    def test_mark_read(self):
        """Test marking email as read"""
        env = EmailTriageEnv(task_name="easy_categorization")
        env.reset()
        
        email = env.inbox[0]
        assert not email.read
        
        action = Action(
            action_type="mark_read",
            email_id=email.id
        )
        
        obs, reward, done, info = env.step(action)
        
        assert reward.value > 0.0
        assert email.read
        assert obs.unread_count == 4
    
    def test_draft_response(self):
        """Test drafting a response"""
        env = EmailTriageEnv(task_name="medium_response")
        env.reset()
        
        # Find work email
        work_email = None
        for email in env.inbox:
            if email.sender == "boss@company.com":
                work_email = email
                break
        
        assert work_email is not None
        
        response_text = "Thank you for the reminder. I will complete the quarterly report by EOD tomorrow. Best regards."
        
        action = Action(
            action_type="draft_response",
            email_id=work_email.id,
            response_text=response_text
        )
        
        obs, reward, done, info = env.step(action)
        
        assert reward.value > 0.0
    
    def test_send_response(self):
        """Test sending a response"""
        env = EmailTriageEnv(task_name="medium_response")
        env.reset()
        
        # Find work email
        work_email = None
        for email in env.inbox:
            if email.sender == "boss@company.com":
                work_email = email
                break
        
        assert work_email is not None
        
        response_text = "Thank you for the reminder. I will complete the quarterly report by EOD tomorrow. Best regards."
        
        action = Action(
            action_type="send_response",
            email_id=work_email.id,
            response_text=response_text
        )
        
        obs, reward, done, info = env.step(action)
        
        assert reward.value > 0.0
        assert work_email.responded
        assert len(env.sent_responses) == 1
    
    def test_delete_email(self):
        """Test deleting spam email"""
        env = EmailTriageEnv(task_name="hard_workflow")
        env.reset()
        
        initial_inbox_size = len(env.inbox)
        
        # Find spam email
        spam_email = None
        for email in env.inbox:
            if email.sender == "spam@fake.com":
                spam_email = email
                break
        
        assert spam_email is not None
        
        action = Action(
            action_type="delete_email",
            email_id=spam_email.id
        )
        
        obs, reward, done, info = env.step(action)
        
        assert reward.value > 0.0
        assert len(env.inbox) == initial_inbox_size - 1
    
    def test_archive_email(self):
        """Test archiving newsletter"""
        env = EmailTriageEnv(task_name="hard_workflow")
        env.reset()
        
        initial_inbox_size = len(env.inbox)
        
        # Find newsletter
        newsletter_email = None
        for email in env.inbox:
            if email.sender == "newsletter@tech.com":
                newsletter_email = email
                break
        
        assert newsletter_email is not None
        
        action = Action(
            action_type="archive_email",
            email_id=newsletter_email.id
        )
        
        obs, reward, done, info = env.step(action)
        
        assert reward.value > 0.0
        assert len(env.inbox) == initial_inbox_size - 1
    
    def test_invalid_email_id(self):
        """Test action with invalid email ID"""
        env = EmailTriageEnv(task_name="easy_categorization")
        env.reset()
        
        action = Action(
            action_type="mark_read",
            email_id="invalid-id-12345"
        )
        
        obs, reward, done, info = env.step(action)
        
        assert reward.value == 0.0  # Clamped penalty
        assert obs.last_action_error is not None
    
    def test_max_steps(self):
        """Test episode ends at max steps"""
        env = EmailTriageEnv(task_name="easy_categorization")
        env.max_steps = 5
        env.reset()
        
        email = env.inbox[0]
        
        for i in range(6):
            action = Action(
                action_type="mark_read",
                email_id=email.id
            )
            obs, reward, done, info = env.step(action)
            
            if i < 4:
                assert not done
            else:
                assert done
    
    def test_task_completion_easy(self):
        """Test easy task completion"""
        env = EmailTriageEnv(task_name="easy_categorization")
        env.reset()
        
        # Categorize all emails correctly
        correct_categories = {
            "boss@company.com": EmailCategory.WORK,
            "team@project.com": EmailCategory.MEETING,
            "newsletter@tech.com": EmailCategory.NEWSLETTER,
            "friend@gmail.com": EmailCategory.PERSONAL,
            "spam@fake.com": EmailCategory.SPAM
        }
        
        for email in env.inbox:
            category = correct_categories.get(email.sender)
            if category:
                action = Action(
                    action_type="categorize_email",
                    email_id=email.id,
                    category=category
                )
                obs, reward, done, info = env.step(action)
        
        # Should be complete
        assert env._check_task_completion()
    
    def test_state_method(self):
        """Test state() method returns correct structure"""
        env = EmailTriageEnv(task_name="easy_categorization")
        env.reset()
        
        state = env.state()
        
        assert "inbox" in state
        assert "step_count" in state
        assert "score" in state
        assert "task_name" in state
        assert "sent_responses" in state
        assert "task_progress" in state
        
        assert isinstance(state["inbox"], list)
        assert state["step_count"] == 0
        assert state["score"] == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])