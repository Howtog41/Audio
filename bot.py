import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InputFile
from aiogram.dispatcher.filters import Command
from aiogram.types.message import Audio, Voice
from aiogram.utils import executor
from pydub import AudioSegment
import whisper
from transformers import pipeline
import asyncio

# Initialize bot and dispatcher
API_TOKEN = "7486102855:AAHTSup6gBCUnFn02nTQZF5GhmwlmMfuwZc"
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Load Whisper and Summarization models
whisper_model = whisper.load_model("base")
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# Function to enhance audio
async def enhance_audio(input_path, output_path):
    audio = AudioSegment.from_file(input_path)
    enhanced_audio = audio.low_pass_filter(3000).normalize()  # Example: reduce noise and normalize
    enhanced_audio.export(output_path, format="wav")
    return output_path

# Transcribe audio
async def transcribe_audio(file_path):
    result = whisper_model.transcribe(file_path)
    return result["text"]

# Summarize text
async def summarize_text(text):
    summary = summarizer(text, max_length=50, min_length=10, do_sample=False)
    return summary[0]["summary_text"]

# Handle audio and voice messages
@dp.message_handler(content_types=[types.ContentType.VOICE, types.ContentType.AUDIO])
async def handle_audio(message: types.Message):
    try:
        # Download file
        file = await message.voice.get_file() if message.voice else await message.audio.get_file()
        file_path = f"{file.file_id}.ogg"
        await bot.download_file(file.file_path, file_path)

        # Convert and enhance audio
        wav_path = f"{file.file_id}.wav"
        enhanced_audio_path = await enhance_audio(file_path, wav_path)

        # Transcription and summarization
        transcription = await transcribe_audio(enhanced_audio_path)
        summary = await summarize_text(transcription)

        # Send results to user
        await message.reply(f"**Transcription:**\n{transcription}\n\n**Summary:**\n{summary}")

        # Send enhanced audio
        enhanced_audio = InputFile(enhanced_audio_path)
        await message.reply_audio(enhanced_audio)

        # Cleanup files
        os.remove(file_path)
        os.remove(wav_path)

    except Exception as e:
        await message.reply(f"An error occurred: {e}")

# Start command handler
@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message):
    await message.reply("Welcome! Send me an audio file or voice note to process.")

# Run bot
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
