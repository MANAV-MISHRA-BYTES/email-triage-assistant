# Deployment Guide

## Hugging Face Spaces Deployment

### Prerequisites
1. Hugging Face account
2. Git installed locally
3. Docker (optional, for local testing)

### Step 1: Create a New Space

1. Go to https://huggingface.co/spaces
2. Click "Create new Space"
3. Fill in:
   - **Name**: `email-triage-assistant`
   - **License**: MIT
   - **SDK**: Docker
   - **Hardware**: CPU Basic (free tier works fine)

### Step 2: Clone and Push

```bash
# Clone your new space
git clone https://huggingface.co/spaces/YOUR_USERNAME/email-triage-assistant
cd email-triage-assistant

# Copy all files from this repository
cp -r /path/to/email-triage-assistant/* .

# Add, commit, and push
git add .
git commit -m "Initial deployment"
git push