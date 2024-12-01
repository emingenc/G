# G
even-realities G one audio -> LLM -> audio  assistant


![audio_task_maistro](https://github.com/user-attachments/assets/170e1088-499a-4373-b724-da51e9778296)

## Quickstart
1. Clone the repository with submodules:

```bash
git clone --recurse-submodules https://github.com/emingenc/G.git
```

2. Populate the `.env` files in LLM_APP and other envfile:

```bash
cp .env.example .env
cp ./LLM_APP/.env.example ./LLM_APP/.env
```

And also populate .env in LLM_APP

### Setup

1. Install FFmpeg (required for ElevenLabs):

```bash 
brew install ffmpeg
```


2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

### Running the System

Docker is required to run the system.

1. Start the Redis server:

```bash
docker run --name g1-redis-server -p 6379:6379 -d redis
```

2. Run the LLM app:

for mac brew install langraph-cli
```bash
brew install langraph-cli
```

```bash
cd LLM_APP
langraph up
```

3. Run the g1 redis connector:

```bash
python3 even_glasses_redis_control/glasses_pubsub.py
```

4. Run the audio assistant:

```bash
python3 even-realities/audio_assistant.py
```

you can use without elevenlab ( without audio ) and without glasses_pubsub ( without redis ) by running:

```bash
python3 even-realities/audio_assistant.py --no-elevenlab --no-redis
```