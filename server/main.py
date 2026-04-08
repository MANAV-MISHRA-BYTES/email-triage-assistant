# server/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn

from .models import Action, Observation, Reward
from .environment import EmailTriageEnv

app = FastAPI(title="Email Triage Assistant Environment")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global environment instance
_env = None


class ResetRequest(BaseModel):
    task_name: Optional[str] = "easy_categorization"


class StepRequest(BaseModel):
    action: Action


@app.post("/reset")
async def reset(request: ResetRequest = None) -> Observation:
    """Reset the environment"""
    global _env
    
    task_name = "easy_categorization"
    if request and request.task_name:
        task_name = request.task_name
    
    _env = EmailTriageEnv(task_name=task_name)
    return _env.reset(task_name)


@app.post("/step")
async def step(request: StepRequest) -> Dict[str, Any]:
    """Execute a step in the environment"""
    global _env
    
    if _env is None:
        raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")
    
    observation, reward, done, info = _env.step(request.action)
    
    return {
        "observation": observation.dict(),
        "reward": reward.dict(),
        "done": done,
        "info": info
    }


@app.get("/state")
async def state() -> Dict[str, Any]:
    """Get the current state of the environment"""
    global _env
    
    if _env is None:
        raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")
    
    return _env.state()


@app.get("/health")
async def health() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)