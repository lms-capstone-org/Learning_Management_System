import re
import uuid
import requests
import azure.cognitiveservices.speech as speechsdk
from core.config import settings

# Map of Language Codes -> Azure Neural Voice Names
VOICE_MAP = {
    "hi": "hi-IN-SwaraNeural",  # Hindi
    "es": "es-ES-ElviraNeural",  # Spanish
    "fr": "fr-FR-DeniseNeural",  # French
    "de": "de-DE-KatjaNeural",  # German
    "ja": "ja-JP-NanamiNeural",  # Japanese
    "ar": "ar-AE-FatimaNeural",  # Arabic
    "zh-Hans": "zh-CN-XiaoxiaoNeural",  # Chinese
    "en": "en-IN-NeerjaNeural"  # English (India)
}


def clean_markdown(text: str) -> str:
    """
    Removes Markdown syntax (**, ##, etc.) so the AI doesn't read special characters aloud.
    """
    if not text:
        return ""
    # Remove bold/italic markers (** or *)
    text = re.sub(r'\*\*|__', '', text)
    text = re.sub(r'\*|_', '', text)
    # Remove headers (## Title)
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    # Remove links [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    return text.strip()


def translate_text(text: str, target_lang: str) -> str:
    """
    Translates text using Azure Translator API.
    """
    # Skip translation if target is English
    if target_lang == "en":
        return text

    # Construct URL
    endpoint = "https://api.cognitive.microsofttranslator.com"
    path = f'/translate?api-version=3.0&to={target_lang}'
    constructed_url = endpoint + path

    # Headers (Ensure these keys are in your settings.py or .env)
    headers = {
        'Ocp-Apim-Subscription-Key': settings.AZURE_SPEECH_KEY,
        'Ocp-Apim-Subscription-Region': settings.AZURE_SPEECH_REGION,  # Often same as speech
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }

    body = [{'text': text}]

    response = requests.post(constructed_url, headers=headers, json=body)

    if response.status_code != 200:
        raise Exception(f"Translation API Error: {response.text}")

    return response.json()[0]['translations'][0]['text']


def synthesize_speech_to_stream(text: str, lang_code: str) -> bytes:
    """
    Synthesizes speech and returns the audio bytes (WAV format).
    Does NOT play on the server speakers.
    """
    voice_name = VOICE_MAP.get(lang_code, "en-US-JennyNeural")  # Fallback voice

    speech_config = speechsdk.SpeechConfig(
        subscription=settings.AZURE_SPEECH_KEY,
        region=settings.AZURE_SPEECH_REGION
    )
    speech_config.speech_synthesis_voice_name = voice_name

    # CRITICAL: Set audio_config to None to prevent server speaker playback
    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config,
        audio_config=None
    )

    result = synthesizer.speak_text_async(text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return result.audio_data  # Returns bytes
    elif result.reason == speechsdk.ResultReason.Canceled:
        details = result.cancellation_details
        raise Exception(f"Speech Synthesis Failed: {details.reason} - {details.error_details}")