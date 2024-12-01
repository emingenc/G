import os
import time
import uuid
import threading
import base64
import asyncio
import argparse
from elevenlabs import play, VoiceSettings
from elevenlabs.client import ElevenLabs
from langgraph.pregel.remote import RemoteGraph
from langgraph.graph import StateGraph, MessagesState, END, START
from langchain_core.messages import HumanMessage
from RealtimeSTT import AudioToTextRecorder
from dotenv import load_dotenv
from utils import transcribe_words
from even_glasses_redis_control.command_sender import CommandSender

# Argument Parsing
parser = argparse.ArgumentParser(description="Audio Assistant")
parser.add_argument('--no-elevenlab', action='store_true', help='Disable ElevenLabs integration')
parser.add_argument('--no-redis', action='store_true', help='Disable Redis integration')
args = parser.parse_args()

use_G1 = not args.no_redis
use_elevenlabs = not args.no_elevenlab

use_elevenlabs = True

# Load environment variables
load_dotenv()

sender = None
if use_G1:
    sender = CommandSender(redis_url="redis://localhost")

# Initialize ElevenLabs client
elevenlabs_client = None
if use_elevenlabs:
    elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))


def my_start_callback():
    print("Recording started!")
    if use_G1:
        asyncio.run(sender.send_text_command(text_message="Listening...", duration=1))


def my_stop_callback():
    print("Recording stopped!")
    if use_G1:
        asyncio.run(sender.send_text_command(text_message="Thinking...", duration=0.5))


def display_message(alignment_data, group_size=7):
    """
    Displays a message on the screen.

    Args:
        message (str): The message to display.
    """
    words = transcribe_words(alignment_data, group_size=group_size)
    for group in words:
        print(" ".join([word["word"] for word in group]))
        # await sender.send_text_command(text_message=" ".join([word["word"] for word in group]), duration=group[-1]["end_time"] - group[0]["start_time
        
        asyncio.run(sender.send_text_command(
                text_message=" ".join([word["word"] for word in group]),
                duration=abs(group[-1]["end_time"] - group[0]["start_time"]),
            )
        )
        time.sleep(group[-1]["end_time"] - group[0]["start_time"])


def play_audio(state: MessagesState):
    """Plays the audio response from the remote graph with ElevenLabs."""

    # Response from the agent
    response = state["messages"][-1]

    # Prepare text by replacing ** with empty strings
    # These can cause unexpected behavior in ElevenLabs
    cleaned_text = response.content.replace("**", "")

    # Call text_to_speech API with turbo model for low latency
    if elevenlabs_client:
        response = elevenlabs_client.text_to_speech.convert_with_timestamps(
            voice_id="pNInz6obpgDQGcFmaJgB",  # Adam pre-made voice
            output_format="mp3_22050_32",
            text=cleaned_text,
            model_id="eleven_turbo_v2_5",
            voice_settings=VoiceSettings(
                stability=0.0,
                similarity_boost=1.0,
                style=0.0,
                use_speaker_boost=True,
            ),
        )
        if use_G1:
            group_size = 13
            t = threading.Thread(target=display_message, args=(response, group_size))
            t.start()

        audio_base64 = response["audio_base64"]
        audio_bytes = base64.b64decode(audio_base64)
        play(audio_bytes)
    else:
        if use_G1:
            asyncio.run(sender.send_text_command(text_message=cleaned_text, duration=3))


# Define parent graph
builder = StateGraph(MessagesState)
# Local deployment (via LangGraph Studio)
local_deployment_url = "http://localhost:8123"
# Graph name
graph_name = "task_maistro"
# Connect to the deployment. you can change any remote graph by changing the url after deployment
remote_graph = RemoteGraph(graph_name, url=local_deployment_url)

# Add remote graph directly as a node
builder.add_node("llm_app", remote_graph)
builder.add_node("audio_output", play_audio)
builder.add_edge(START, "llm_app")
builder.add_edge("llm_app", "audio_output")
builder.add_edge("audio_output", END)
graph = builder.compile()


def process_text(text, graph, thread_id):
    print(f"Transcribed text: {text}")
    if use_G1:
        asyncio.run(sender.send_text_command(text_message=text, duration=1))
    config = {"configurable": {"user_id": "Test-Audio-UX", "thread_id": thread_id}}
    for chunk in graph.stream(
        {"messages": HumanMessage(content=text)}, stream_mode="values", config=config
    ):
        chunk["messages"][-1].pretty_print()


async def main():
    # Start the graph
    if use_G1:
        await sender.connect()
    thread_id = str(uuid.uuid4())

    with AudioToTextRecorder(
        model="small",
        wake_words="jarvis",
        on_recording_start=my_start_callback,
        on_recording_stop=my_stop_callback,
        wakeword_backend="oww",
        wake_words_sensitivity=0.35,
        wake_word_buffer_duration=1,
    ) as recorder:
        print('Say "Jarvis" to start recording.')
        # Start listening and processing text
        while True:
            recorder.text(lambda text: process_text(text, graph, thread_id))


if __name__ == "__main__":
    asyncio.run(main())
