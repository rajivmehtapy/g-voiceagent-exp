# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a LiveKit voice agent experiment project (`g-voiceagent-exp`) that implements AI-powered voice assistants using different models and configurations.

## Architecture

The project contains three main agent implementations:

- `agent.py` - OpenAI Realtime API voice agent with basic assistant functionality
- `agent_gemini.py` - Google Gemini 2.0 Flash voice agent with web search and weather checking tools
- `agent_v1.py` - Google Gemini multimodal agent with audio-only mode

All agents use the LiveKit framework for real-time communication and voice processing.

### Key Components

- **Agent Classes**: Inherit from `Agent` base class with custom instructions and optional tools
- **Entry Points**: Each file has an async `entrypoint` function that sets up the agent session
- **Model Configuration**: Different LLM backends (OpenAI Realtime, Google Gemini) with voice settings
- **Noise Cancellation**: Uses LiveKit Cloud's BVC noise cancellation for better audio quality
- **Function Tools**: Extensible tool system for web search and weather data
- **Logging Infrastructure**: Comprehensive logging with daily rotation and structured data

## Development Commands

This project uses `uv` as the package manager.

### Running Agents
```bash
# Run the OpenAI-based agent
python agent.py

# Run the Gemini-based agent with tools
python agent_gemini.py

# Run the multimodal Gemini agent
python agent_v1.py
```

### Environment Setup
- Requires Python 3.12+
- Uses `.env` file for environment variables (API keys, etc.)
- Required environment variables: `MISTRAL_API_KEY` for web search functionality
- Install dependencies: `uv sync`
- Create virtual environment: `uv venv` (if needed)

### Testing Tools
```bash
# Test web search functionality independently
python test_web_search.py
```

### Dependencies
- `livekit-agents[google]~=1.0` - Core LiveKit agents framework with Google plugin
- `mistralai` - Mistral AI client for web search functionality
- `loguru` - Advanced logging with daily rotation
- `dotenv` - Environment variable management

## Function Tools Implementation

### Current Tools in agent_gemini.py:
- **web_search**: Uses Mistral AI's web search capability for real-time information retrieval
- **check_weather**: Mock weather data generator with realistic seasonal variations

### Function Tools Pattern
When adding function tools:
- Use `@function_tool` decorator
- First parameter must be `context: RunContext`
- Include descriptive docstring for the LLM
- Register tools in Agent constructor: `tools=[your_tool_1, your_tool_2]`
- Use context parameter for session tracking and logging

### Web Search Implementation
- Creates temporary Mistral AI agents with web search capability
- Handles API key validation and error handling
- Includes comprehensive logging and performance metrics
- Automatically cleans up temporary agents after use

## Voice Configuration

Voice settings are configured in the LLM model initialization:
- OpenAI: `voice="coral"`
- Google: `voice="Kore"`
- Temperature controls randomness (0.66-0.8 range used)

## Agent Implementation Patterns

### Session Management
All agents follow the same pattern:
1. Create `AgentSession` with LLM model configuration
2. Start session with room, agent instance, and input options
3. Connect to LiveKit room via `ctx.connect()`
4. Generate initial greeting with `session.generate_reply()`

### Model Differences
- **OpenAI Realtime**: Uses `openai.realtime.RealtimeModel` 
- **Google Gemini**: Uses `google.beta.realtime.RealtimeModel` with model specification
- **Multimodal**: Uses `multimodal.MultimodalAgent` wrapper for different workflow

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