# server/models.py
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class EmailPriority(str, Enum):
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EmailCategory(str, Enum):
    WORK = "work"
    PERSONAL = "personal"
    SPAM = "spam"
    NEWSLETTER = "newsletter"
    NOTIFICATION = "notification"
    MEETING = "meeting"
    TASK = "task"


class Email(BaseModel):
    """Represents an email in the inbox"""
    id: str
    sender: str
    subject: str
    body: str
    received_at: datetime
    priority: EmailPriority = EmailPriority.MEDIUM
    category: EmailCategory = EmailCategory.WORK
    read: bool = False
    responded: bool = False
    tags: List[str] = Field(default_factory=list)
    attachments: List[str] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class Action(BaseModel):
    """Available actions for the email triage assistant"""
    action_type: Literal[
        "categorize_email",
        "set_priority",
        "mark_read",
        "draft_response",
        "send_response",
        "archive_email",
        "delete_email",
        "flag_email",
        "add_tag"
    ]
    
    # Action parameters
    email_id: Optional[str] = None
    category: Optional[EmailCategory] = None
    priority: Optional[EmailPriority] = None
    response_text: Optional[str] = None
    tag: Optional[str] = None
    
    @validator('email_id')
    def validate_email_id(cls, v, values):
        if values.get('action_type') in ['categorize_email', 'set_priority', 'mark_read', 
                                        'draft_response', 'send_response', 'archive_email',
                                        'delete_email', 'flag_email', 'add_tag']:
            if not v:
                raise ValueError('email_id is required for this action type')
        return v
    
    @validator('category')
    def validate_category(cls, v, values):
        if values.get('action_type') == 'categorize_email' and not v:
            raise ValueError('category is required for categorize_email action')
        return v
    
    @validator('priority')
    def validate_priority(cls, v, values):
        if values.get('action_type') == 'set_priority' and not v:
            raise ValueError('priority is required for set_priority action')
        return v
    
    @validator('response_text')
    def validate_response_text(cls, v, values):
        if values.get('action_type') in ['draft_response', 'send_response'] and not v:
            raise ValueError('response_text is required for response actions')
        return v
    
    @validator('tag')
    def validate_tag(cls, v, values):
        if values.get('action_type') == 'add_tag' and not v:
            raise ValueError('tag is required for add_tag action')
        return v


class Observation(BaseModel):
    """Observation returned by the environment"""
    inbox: List[Email]
    unread_count: int
    current_task: Dict[str, Any]
    step_count: int
    max_steps: int
    available_actions: List[str] = Field(
        default_factory=lambda: [
            "categorize_email",
            "set_priority", 
            "mark_read",
            "draft_response",
            "send_response",
            "archive_email",
            "delete_email",
            "flag_email",
            "add_tag"
        ]
    )
    last_action_result: Optional[str] = None
    last_action_error: Optional[str] = None


class Reward(BaseModel):
    """Reward model for the environment"""
    value: float = Field(ge=0.0, le=1.0)
    breakdown: Dict[str, float] = Field(default_factory=dict)
    message: str = ""