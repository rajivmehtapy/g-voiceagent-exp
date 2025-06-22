from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    openai,
    google,
    cartesia,
    deepgram,
    noise_cancellation,
    silero,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

load_dotenv()


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="You are a helpful voice AI assistant.")


async def entrypoint(ctx: agents.JobContext):

    session = AgentSession(
        # tts = google.TTS(gender="female",voice_name="en-US-Standard-H",),
        tts = google.TTS(voice_name="en-US-Chirp-HD-F"),
        llm=openai.LLM(model="gpt-4.1-nano"),
        stt = google.STT(model="latest_long", spoken_punctuation=False),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    # session = AgentSession(
    #     stt=deepgram.STT(model="nova-3", language="multi"),
    #     llm=openai.LLM(model="gpt-4.1-nano"),
    #     tts=cartesia.TTS(model="sonic-2", voice="f786b574-daa5-4673-aa0c-cbe3e8534c02"),
    #     vad=silero.VAD.load(),
    #     turn_detection=MultilingualModel(),
    # )

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