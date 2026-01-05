# voice_service.py
"""
Voice service for handling speech-to-text and text-to-speech conversions
"""

import os
from openai import OpenAI
from pathlib import Path
import tempfile
from dotenv import load_dotenv
import io

load_dotenv()


class VoiceService:
    """Handle voice-related operations using OpenAI's APIs"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.enabled = os.getenv('ENABLE_VOICE', 'True').lower() == 'true'
        
        # Supported voices: alloy, echo, fable, onyx, nova, shimmer
        self.default_voice = os.getenv('TTS_VOICE', 'nova')
        
    def transcribe_audio(self, audio_file) -> dict:
        """
        Convert speech to text using OpenAI Whisper
        
        Args:
            audio_file: Audio file object (can be file path or file-like object)
        
        Returns:
            dict: {"success": bool, "text": str, "error": str}
        """
        if not self.enabled:
            return {
                "success": False,
                "text": "",
                "error": "Voice service is disabled"
            }
        
        try:
            # Transcribe the audio file
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en"  # Can be changed to auto-detect or specific language
            )
            
            return {
                "success": True,
                "text": transcript.text,
                "error": None
            }
            
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            return {
                "success": False,
                "text": "",
                "error": str(e)
            }
    
    def text_to_speech(self, text: str, voice: str = None) -> dict:
        """
        Convert text to speech using OpenAI TTS
        
        Args:
            text: Text to convert to speech
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
        
        Returns:
            dict: {"success": bool, "audio_data": bytes, "error": str}
        """
        if not self.enabled:
            return {
                "success": False,
                "audio_data": None,
                "error": "Voice service is disabled"
            }
        
        try:
            voice = voice or self.default_voice
            
            # Generate speech
            response = self.client.audio.speech.create(
                model="tts-1",  # or "tts-1-hd" for higher quality
                voice=voice,
                input=text,
                response_format="mp3"
            )
            
            # Get audio data
            audio_data = response.content
            
            return {
                "success": True,
                "audio_data": audio_data,
                "error": None
            }
            
        except Exception as e:
            print(f"Error generating speech: {e}")
            return {
                "success": False,
                "audio_data": None,
                "error": str(e)
            }
    
    def save_audio_to_file(self, audio_data: bytes, filename: str = None) -> str:
        """
        Save audio data to a file
        
        Args:
            audio_data: Audio bytes
            filename: Optional filename (will generate temp file if not provided)
        
        Returns:
            str: Path to saved file
        """
        if filename is None:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            filename = temp_file.name
            temp_file.close()
        
        with open(filename, 'wb') as f:
            f.write(audio_data)
        
        return filename


# Initialize voice service
voice_service = VoiceService()


# # Helper function for testing
# def test_voice_service():
#     """Test the voice service"""
#     print("Testing Voice Service...")
    
#     # Test TTS
#     print("\n1. Testing Text-to-Speech...")
#     result = voice_service.text_to_speech("Hello! This is a test of the voice service.")
    
#     if result['success']:
#         print("✅ TTS successful!")
#         # Save to file
#         filepath = voice_service.save_audio_to_file(result['audio_data'], 'test_output.mp3')
#         print(f"   Audio saved to: {filepath}")
#     else:
#         print(f"❌ TTS failed: {result['error']}")
    
#     print("\nVoice service test completed!")


# if __name__ == "__main__":
#     test_voice_service()