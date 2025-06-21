from dotenv import load_dotenv
import os
from datetime import datetime
import time

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions ,function_tool,RunContext
from livekit.plugins import (
    google,
    noise_cancellation,
)
from mistralai import Mistral
from loguru import logger

load_dotenv()

# Configure loguru logging with daily rotation
logger.remove()  # Remove default handler
logger.add(
    "logs/{time:YYYY-MM-DD}_data.log",
    rotation="00:00",  # Rotate at midnight
    retention="30 days",  # Keep logs for 30 days
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
    level="INFO",
    serialize=True  # JSON format for structured logging
)

@function_tool
async def web_search(
    context: RunContext,
    query: str,
):
    """Search the web for current information on any topic including news, weather, sports, and general knowledge."""
    
    start_time = time.time()
    session_id = getattr(context, 'session_id', 'unknown') if context else 'no_context'
    
    logger.info("Web search initiated", extra={
        "query": query,
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "function": "web_search"
    })
    
    try:
        # Get Mistral API key from environment
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            logger.error("Mistral API key not configured", extra={
                "query": query,
                "session_id": session_id,
                "error": "missing_api_key"
            })
            return {"error": "Mistral API key not configured"}
        
        logger.debug("API key validation successful", extra={
            "session_id": session_id,
            "has_api_key": True
        })
        
        # Initialize Mistral client
        client = Mistral(api_key=api_key)
        logger.debug("Mistral client initialized", extra={"session_id": session_id})
        
        # Create a temporary agent with web search capability
        search_agent = client.beta.agents.create(
            model="mistral-medium-2505",
            description="Agent able to search information over the web",
            name="Web Search Agent",
            instructions="You have the ability to perform web searches to find up-to-date information. Provide concise, accurate answers suitable for voice responses.",
            tools=[{"type": "web_search"}],
            completion_args={
                "temperature": 0.3,
                "top_p": 0.95,
            }
        )
        
        logger.info("Search agent created", extra={
            "agent_id": search_agent.id,
            "session_id": session_id,
            "query": query
        })
        
        # Perform the search
        search_start = time.time()
        response = client.beta.conversations.start(
            agent_id=search_agent.id,
            inputs=[{"role": "user", "content": query}]
        )
        search_duration = time.time() - search_start
        
        # Extract the search result
        result = response.model_dump()['outputs'][1]['content'][0]['text']
        result_length = len(result)
        
        logger.info("Search completed successfully", extra={
            "query": query,
            "session_id": session_id,
            "agent_id": search_agent.id,
            "search_duration_seconds": round(search_duration, 3),
            "result_length_chars": result_length,
            "result_preview": result[:100] + "..." if len(result) > 100 else result
        })
        
        # Clean up the temporary agent
        try:
            client.beta.agents.delete(agent_id=search_agent.id)
            logger.debug("Search agent cleanup successful", extra={
                "agent_id": search_agent.id,
                "session_id": session_id
            })
        except Exception as cleanup_error:
            logger.warning("Agent cleanup failed", extra={
                "agent_id": search_agent.id,
                "session_id": session_id,
                "cleanup_error": str(cleanup_error)
            })
        
        total_duration = time.time() - start_time
        logger.info("Web search operation completed", extra={
            "query": query,
            "session_id": session_id,
            "total_duration_seconds": round(total_duration, 3),
            "success": True
        })
        
        return {"result": result}
        
    except Exception as e:
        total_duration = time.time() - start_time
        logger.error("Web search failed with exception", extra={
            "query": query,
            "session_id": session_id,
            "error_type": type(e).__name__,
            "error_message": str(e),
            "total_duration_seconds": round(total_duration, 3),
            "success": False
        })
        return {"error": f"Web search failed: {str(e)}"}

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="You are a helpful voice AI assistant with web search capabilities. You can search for current information on any topic.",tools=[web_search])


async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            model="gemini-2.0-flash-exp",
            voice="Kore",
            temperature=0.8,
            instructions="You are a helpful assistant with web search capabilities. You can find current information on news, weather, sports, and any other topics by using web search."

        ),
    )
    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            # LiveKit Cloud enhanced noise cancellation
            # - If self-hosting, omit this parameter
            # - For telephony applications, use `BVCTelephony` for best results
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()

    await session.generate_reply(
        instructions="Greet the user and offer your assistance."
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))