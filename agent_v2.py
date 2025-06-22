from dotenv import load_dotenv
import os
from datetime import datetime
import time
import random
import asyncio

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, function_tool, RunContext
from livekit.plugins import (
    openai,
    google,
    deepgram,
    cartesia,
    noise_cancellation,
    silero,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel
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
async def web_search_mistral(
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
        "function": "web_search_mistral"
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


@function_tool
async def check_weather(
    context: RunContext,
    city: str,
):
    """Check current weather information for a specific city. Returns comprehensive weather data including temperature, humidity, wind, and forecasts."""
    
    start_time = time.time()
    session_id = getattr(context, 'session_id', 'unknown') if context else 'no_context'
    
    logger.info("Weather check initiated", extra={
        "city": city,
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "function": "check_weather"
    })
    
    try:
        # Simulate API call delay
        await asyncio.sleep(random.uniform(0.1, 0.3))
        
        # Get current month for seasonal variations
        current_month = datetime.now().month
        
        # Define seasonal temperature ranges
        if current_month in [12, 1, 2]:  # Winter
            temp_base = random.uniform(-5, 15)
        elif current_month in [3, 4, 5]:  # Spring
            temp_base = random.uniform(10, 25)
        elif current_month in [6, 7, 8]:  # Summer
            temp_base = random.uniform(20, 35)
        else:  # Fall
            temp_base = random.uniform(5, 20)
        
        # Weather conditions pool
        weather_conditions = [
            {"main": "Clear", "description": "clear sky", "icon": "01d"},
            {"main": "Clouds", "description": "few clouds", "icon": "02d"},
            {"main": "Clouds", "description": "scattered clouds", "icon": "03d"},
            {"main": "Clouds", "description": "broken clouds", "icon": "04d"},
            {"main": "Clouds", "description": "overcast clouds", "icon": "04d"},
            {"main": "Rain", "description": "light rain", "icon": "10d"},
            {"main": "Rain", "description": "moderate rain", "icon": "10d"},
            {"main": "Rain", "description": "heavy rain", "icon": "10d"},
            {"main": "Thunderstorm", "description": "thunderstorm", "icon": "11d"},
            {"main": "Snow", "description": "light snow", "icon": "13d"},
            {"main": "Mist", "description": "mist", "icon": "50d"},
            {"main": "Fog", "description": "fog", "icon": "50d"}
        ]
        
        # Select weather condition (bias towards clear/cloudy for realism)
        weather_weights = [0.3, 0.25, 0.15, 0.1, 0.05, 0.05, 0.03, 0.02, 0.02, 0.02, 0.005, 0.005]
        selected_weather = random.choices(weather_conditions, weights=weather_weights)[0]
        
        # Adjust temperature based on weather condition
        if selected_weather["main"] == "Rain":
            temp_base -= random.uniform(2, 8)
        elif selected_weather["main"] == "Snow":
            temp_base = random.uniform(-15, 5)
        elif selected_weather["main"] == "Thunderstorm":
            temp_base -= random.uniform(3, 10)
        
        # Generate comprehensive weather data
        temperature = round(temp_base, 1)
        feels_like = round(temperature + random.uniform(-5, 5), 1)
        humidity = random.randint(20, 100)
        pressure = random.randint(980, 1040)
        wind_speed = round(random.uniform(0, 25), 1)
        wind_direction = random.randint(0, 360)
        wind_gust = round(wind_speed + random.uniform(0, 10), 1) if wind_speed > 5 else wind_speed
        visibility = round(random.uniform(1, 20), 1)
        uv_index = random.randint(0, 11)
        air_quality = random.randint(1, 5)  # 1=Good, 5=Hazardous
        
        # Generate coordinates (mock)
        lat = round(random.uniform(-90, 90), 4)
        lon = round(random.uniform(-180, 180), 4)
        
        # Generate timestamps
        current_time = datetime.now()
        sunrise_hour = random.randint(5, 8)
        sunset_hour = random.randint(17, 20)
        sunrise = current_time.replace(hour=sunrise_hour, minute=random.randint(0, 59))
        sunset = current_time.replace(hour=sunset_hour, minute=random.randint(0, 59))
        
        # Create comprehensive weather response
        weather_data = {
            "location": {
                "city": city.title(),
                "country": random.choice(["US", "UK", "CA", "AU", "DE", "FR", "JP", "IN", "BR", "CN"]),
                "coordinates": {
                    "latitude": lat,
                    "longitude": lon
                }
            },
            "current": {
                "timestamp": current_time.isoformat(),
                "temperature": {
                    "current": temperature,
                    "feels_like": feels_like,
                    "unit": "°C"
                },
                "weather": {
                    "main": selected_weather["main"],
                    "description": selected_weather["description"],
                    "icon": selected_weather["icon"]
                },
                "atmospheric": {
                    "humidity": humidity,
                    "pressure": pressure,
                    "pressure_unit": "hPa",
                    "visibility": visibility,
                    "visibility_unit": "km"
                },
                "wind": {
                    "speed": wind_speed,
                    "direction": wind_direction,
                    "gust": wind_gust,
                    "unit": "km/h"
                },
                "sun": {
                    "sunrise": sunrise.strftime("%H:%M"),
                    "sunset": sunset.strftime("%H:%M")
                },
                "indices": {
                    "uv_index": uv_index,
                    "air_quality_index": air_quality,
                    "air_quality_description": ["Good", "Fair", "Moderate", "Poor", "Very Poor"][air_quality-1]
                }
            },
            "forecast": {
                "summary": f"Expect {selected_weather['description']} with temperatures around {temperature}°C",
                "next_24h": "Conditions will remain similar with slight temperature variations"
            },
            "metadata": {
                "source": "Mock Weather Service",
                "last_updated": current_time.isoformat(),
                "response_time_ms": round((time.time() - start_time) * 1000, 2)
            }
        }
        
        total_duration = time.time() - start_time
        logger.info("Weather check completed successfully", extra={
            "city": city,
            "session_id": session_id,
            "temperature": temperature,
            "weather_condition": selected_weather["main"],
            "total_duration_seconds": round(total_duration, 3),
            "success": True
        })
        
        return weather_data
        
    except Exception as e:
        total_duration = time.time() - start_time
        logger.error("Weather check failed with exception", extra={
            "city": city,
            "session_id": session_id,
            "error_type": type(e).__name__,
            "error_message": str(e),
            "total_duration_seconds": round(total_duration, 3),
            "success": False
        })
        return {"error": f"Weather check failed: {str(e)}"}


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="You are a helpful voice AI assistant with web search and weather checking capabilities. You can search for current information on any topic and check weather for any city.", tools=[web_search_mistral, check_weather])


async def entrypoint(ctx: agents.JobContext):

    # session = AgentSession(
    #     # tts = google.TTS(gender="female",voice_name="en-US-Standard-H",),
    #     tts = google.TTS(voice_name="en-US-Chirp-HD-F"),
    #     # llm=google.LLM(model="gemini-2.0-flash-exp",temperature=0.8),
    #     llm=google.LLM(model="gemini-2.5-flash-lite-preview-06-17",temperature=0.8),
    #     stt = google.STT(model="latest_long", spoken_punctuation=False),
    #     vad=silero.VAD.load(),
    #     turn_detection=MultilingualModel(),
    # )

    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        # llm=openai.LLM(model="gpt-4.1-nano"),
        llm=google.LLM(model="gemini-2.5-flash-lite-preview-06-17",temperature=0.4),
        tts=cartesia.TTS(model="sonic-2", voice="f786b574-daa5-4673-aa0c-cbe3e8534c02"),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    import logging
    import json
    from livekit.agents._exceptions import APIConnectionError
    from json.decoder import JSONDecodeError

    try:
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
            instructions="Greet the user and offer your assistance. Mention that you can help with web searches for current information and weather checks for any city."
        )
    except (APIConnectionError, JSONDecodeError) as e:
        logger.error("LLM streaming or API connection error encountered", extra={
            "error_type": type(e).__name__,
            "error_message": str(e),
            "suggestion": "This may be due to a bug in google/genai streaming or malformed JSON. Try upgrading google-generativeai and aiohttp."
        })
        print("[ERROR] LLM streaming/API connection error. Consider upgrading google-generativeai and aiohttp.")
    except Exception as e:
        logger.error("Unexpected error in entrypoint", extra={
            "error_type": type(e).__name__,
            "error_message": str(e)
        })
        print(f"[ERROR] Unexpected error: {e}")
    finally:
        # Warn if aiohttp sessions are not closed
        # (This is a best-effort check; if you use aiohttp elsewhere, ensure proper closing.)
        import warnings
        warnings.warn("If you see 'Unclosed client session' errors, ensure all aiohttp.ClientSession objects are closed properly.")



if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))