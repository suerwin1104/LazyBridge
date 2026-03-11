import os
from gtts import gTTS
from core.config import log

class VoiceService:
    @staticmethod
    async def generate_tts(text, filename="response.mp3"):
        """Generate TTS audio file using gTTS."""
        try:
            reports_dir = os.path.join(os.getcwd(), "reports")
            if not os.path.exists(reports_dir):
                os.makedirs(reports_dir)
            
            filepath = os.path.join(reports_dir, filename)
            tts = gTTS(text=text, lang='zh-tw')
            tts.save(filepath)
            log(f"🔊 TTS 檔案已生成: {filepath}")
            return filepath
        except Exception as e:
            log(f"❌ TTS 生成失敗: {e}")
            return None

    @staticmethod
    async def play_voice(voice_client, audio_path):
        """Play audio file in the voice channel."""
        import discord
        if not voice_client or not voice_client.is_connected():
            log("⚠️ 語音客戶端未連線，無法播放。")
            return

        try:
            # Requires FFmpeg
            executable_path = r"C:\Users\USER\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe"
            source = discord.FFmpegPCMAudio(executable=executable_path, source=audio_path)
            voice_client.play(source, after=lambda e: log(f"✅ 語音播放完成: {e}" if e else "✅ 語音播放完成"))
        except Exception as e:
            log(f"❌ 語音播放失敗: {e}")
