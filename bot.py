import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InputFile
from aiogram.filters import Command  # Corrected import
from aiogram import F
from aiogram.utils import executor
from pydub import AudioSegment
import whisper
from transformers import pipeline
import asyncio

# Initialize bot and dispatcher
API_TOKEN = "7486102855:AAHTSup6gBCUnFn02nTQZF5GhmwlmMfuwZc"
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

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
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.reply("Welcome! Send me an audio file or voice note to process.")

@dp.message(F.voice | F.audio)
async def handle_audio(message: types.Message):
    try:
        # Download file
        file = await bot.get_file(message.voice.file_id if message.voice else message.audio.file_id)
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

# Run bot
async def main():
    dp.include_router(dp)  # Add dispatcher to router
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
