import requests
from openai import OpenAI

def test_transcription(audio_file_path):
    #fast_url = "http://host.docker.internal:5403"
    fast_url = "http://localhost:5403"
    #checked_fastwhisperapi = False
    endpoint = f"{fast_url}/v1/transcriptions"
    
    endpoint = f"{fast_url}/v1/"

    client = OpenAI(api_key="cant-be-empty", base_url=endpoint)

    audio_file = open(audio_file_path, "rb")
    print(endpoint)
    transcript = client.audio.transcriptions.create(model="Systran/faster-whisper-tiny", file=audio_file)
    print(transcript.text)

    return transcript.text


if __name__ == "__main__":
    wav_file = "/Users/vinh/RTLightRAG/audio_batches/recording_1731966474.wav"
    test_transcription(wav_file)