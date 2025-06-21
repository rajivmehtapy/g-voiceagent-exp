# LiveKit Voice Agent Experiment

This project implements AI-powered voice assistants using LiveKit framework with different models and configurations, featuring web search and weather checking capabilities.

## Project Overview

The project contains three main agent implementations:

- `agent.py` - OpenAI Realtime API voice agent with basic assistant functionality
- `agent_gemini.py` - Google Gemini 2.0 Flash voice agent with web search and weather checking tools
- `agent_v1.py` - Google Gemini multimodal agent with audio-only mode

## Features

- **Real-time Voice Communication**: Using LiveKit framework
- **Web Search Integration**: Powered by Mistral AI's web search capability
- **Weather Information**: Mock weather data with realistic seasonal variations
- **Comprehensive Logging**: Daily rotating logs with structured JSON format
- **Web Demo Interface**: Browser-based client for testing and interaction

## Prerequisites

- Python 3.12+
- Node.js and npm (for demo interface)
- LiveKit server (local or cloud)
- API keys for various services

## Installation

### 1. Environment Setup

```bash
# Install dependencies
uv sync

# Create virtual environment (if needed)
uv venv
```

### 2. Environment Variables

Create a `.env` file with the following variables:

```env
# Required for web search functionality
MISTRAL_API_KEY=your_mistral_api_key_here

# Required for LiveKit server
LIVEKIT_URL=wss://your-livekit-server.com
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret

# Required for Google Gemini
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
# OR
GOOGLE_AI_STUDIO_API_KEY=your_google_ai_studio_key
```

### 3. Demo Interface Setup

```bash
# Install TypeScript compiler globally
npm install -g typescript

# Navigate to demo directory
cd demo

# Compile TypeScript to JavaScript
tsc
```

## Running the Agents

### Basic Agent Execution

```bash
# Run the OpenAI-based agent
python agent.py

# Run the Gemini-based agent with tools
python agent_gemini.py

# Run the multimodal Gemini agent
python agent_v1.py
```

### Testing Tools Functionality

```bash
# Test web search functionality independently
python test_web_search.py
```

## Web Demo Integration Guide

### Step 1: Generate Room Token

Create a `token_generator.py` script:

```python
import jwt
import time
from datetime import datetime, timedelta

def generate_token(room_name="test-room", participant_name="user"):
    api_key = "your_livekit_api_key"
    api_secret = "your_livekit_api_secret"
    
    payload = {
        "iss": api_key,
        "exp": int((datetime.now() + timedelta(hours=1)).timestamp()),
        "nbf": int(datetime.now().timestamp()),
        "sub": participant_name,
        "name": participant_name,
        "room": room_name,
        "video": True,
        "audio": True,
        "canPublish": True,
        "canSubscribe": True,
    }
    
    token = jwt.encode(payload, api_secret, algorithm="HS256")
    return token

print(generate_token())
```

### Step 2: Start LiveKit Server

**Option A: Use LiveKit Cloud (Recommended)**
1. Sign up at https://livekit.io
2. Get your server URL and API credentials
3. Use provided URL/keys in `.env` file

**Option B: Run Local Server**
```bash
# Download LiveKit server from https://github.com/livekit/livekit/releases
./livekit-server --dev
```

### Step 3: Run Your Voice Agent

```bash
# Start agent_gemini.py with enhanced tools
python agent_gemini.py
```

### Step 4: Open Web Demo

1. Open `demo/index.html` in a web browser
2. Configure connection:
   - **LiveKit URL**: `wss://your-server.com` or `ws://localhost:7880`
   - **Token**: Paste the generated token from Step 1
   - **Crypto Key**: Leave default or set custom
3. Click "Connect"
4. Enable microphone to start talking to your agent

### Step 5: Test Integration

1. **Voice Chat**: Speak to test basic functionality
2. **Web Search**: Say "Search for latest AI news"
3. **Weather**: Say "What's the weather in New York?"
4. **Check Logs**: Monitor `logs/YYYY-MM-DD_data.log` for detailed operation logs

## Function Tools

### Current Tools in agent_gemini.py

- **web_search_mistral**: Uses Mistral AI's web search capability for real-time information retrieval
- **check_weather**: Mock weather data generator with realistic seasonal variations

### Adding Function Tools

When adding new function tools:
- Use `@function_tool` decorator
- First parameter must be `context: RunContext`
- Include descriptive docstring for the LLM
- Register tools in Agent constructor: `tools=[your_tool_1, your_tool_2]`
- Use context parameter for session tracking and logging

## Logging System

### Daily Log Rotation
- Logs stored in `logs/` directory (gitignored)
- Daily rotation: `YYYY-MM-DD_data.log` format
- Retention: 30 days
- Structured JSON logging with loguru

### Log Content
- Function tool calls (web search, weather checks)
- Performance metrics (response times, result sizes)
- Error handling and debugging information
- Session tracking with unique identifiers
- API usage patterns and success rates

### Test Logging
- Test runs generate separate log files: `YYYY-MM-DD_test_data.log`
- Console output for immediate feedback during testing

## Demo Features

The web demo provides:

- **Audio/Video**: Real-time communication with the agent
- **Chat**: Text-based interaction alongside voice
- **Screen Share**: Share your screen with the agent
- **Device Selection**: Choose microphone/camera
- **Connection Quality**: Monitor connection status
- **E2E Encryption**: Optional secure communication

## Troubleshooting

### Common Issues

1. **Connection Failed**: Check LiveKit server URL and token validity
2. **Audio Not Working**: Verify microphone permissions in browser
3. **Agent Not Responding**: Check API keys in `.env` file
4. **CORS Errors**: Serve demo via HTTP server instead of opening file directly

### Required Information

- **LiveKit Server URL**: Where your LiveKit server is running
- **API Keys**: Mistral AI, Google Gemini, LiveKit credentials
- **Room Tokens**: Generated with proper permissions
- **CORS Settings**: May need to serve demo via HTTP server

## Architecture

### Key Components

- **Agent Classes**: Inherit from `Agent` base class with custom instructions and optional tools
- **Entry Points**: Each file has an async `entrypoint` function that sets up the agent session
- **Model Configuration**: Different LLM backends (OpenAI Realtime, Google Gemini) with voice settings
- **Noise Cancellation**: Uses LiveKit Cloud's BVC noise cancellation for better audio quality
- **Function Tools**: Extensible tool system for web search and weather data
- **Logging Infrastructure**: Comprehensive logging with daily rotation and structured data

### Model Differences

- **OpenAI Realtime**: Uses `openai.realtime.RealtimeModel`
- **Google Gemini**: Uses `google.beta.realtime.RealtimeModel` with model specification
- **Multimodal**: Uses `multimodal.MultimodalAgent` wrapper for different workflow

### Session Management

All agents follow the same pattern:
1. Create `AgentSession` with LLM model configuration
2. Start session with room, agent instance, and input options
3. Connect to LiveKit room via `ctx.connect()`
4. Generate initial greeting with `session.generate_reply()`

## Voice Configuration

Voice settings are configured in the LLM model initialization:
- OpenAI: `voice="coral"`
- Google: `voice="Kore"`
- Temperature controls randomness (0.66-0.8 range used)

## Dependencies

- `livekit-agents[google]~=1.0` - Core LiveKit agents framework with Google plugin
- `mistralai` - Mistral AI client for web search functionality
- `loguru` - Advanced logging with daily rotation
- `dotenv` - Environment variable management

## Integration Benefits

This setup creates a complete voice AI assistant interface where you can:
- Speak naturally and get real-time responses
- Access web search and weather capabilities
- Monitor performance through comprehensive logging
- Use visual interface for debugging and testing
- Enable multi-modal interaction (voice + text + screen sharing)