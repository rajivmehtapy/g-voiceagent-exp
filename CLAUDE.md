# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a LiveKit voice agent experiment project (`g-voiceagent-exp`) that implements AI-powered voice assistants using different models and configurations.

## Architecture

The project contains three main agent implementations:

- `agent.py` - OpenAI Realtime API voice agent with basic assistant functionality
- `agent_gemini.py` - Google Gemini 2.0 Flash voice agent with function tools (weather lookup example)
- `agent_v1.py` - Google Gemini multimodal agent with audio-only mode

All agents use the LiveKit framework for real-time communication and voice processing.

### Key Components

- **Agent Classes**: Inherit from `Agent` base class with custom instructions and optional tools
- **Entry Points**: Each file has an async `entrypoint` function that sets up the agent session
- **Model Configuration**: Different LLM backends (OpenAI Realtime, Google Gemini) with voice settings
- **Noise Cancellation**: Uses LiveKit Cloud's BVC noise cancellation for better audio quality

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
- Install dependencies: `uv sync`
- Create virtual environment: `uv venv` (if needed)

### Dependencies
- `livekit-agents[google]~=1.0` - Core LiveKit agents framework with Google plugin
- `dotenv` - Environment variable management

## Function Tools Pattern

When adding function tools (see `agent_gemini.py:12-19`):
- Use `@function_tool` decorator
- First parameter must be `context: RunContext`
- Include descriptive docstring for the LLM
- Register tools in Agent constructor: `tools=[your_tool]`

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