import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from transcription import transcribe_audio

class AudioTranscriber:
    def __init__(self, model_name="base"):
        # This class is not used anymore, but it's kept for potential future use
        pass

class AudioFileHandler(FileSystemEventHandler):
    def __init__(self, output_dir="transcriptions"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('.wav'):
            # Attendre un court instant pour s'assurer que le fichier est complètement écrit
            time.sleep(0.5)
            # Transcrire l'audio en utilisant l'API FastWhisper
            text = transcribe_audio(event.src_path)
            # Sauvegarder la transcription
            basename = os.path.basename(event.src_path)
            txt_filename = os.path.join(self.output_dir, 
                                      basename.replace('.wav', '.txt'))
            with open(txt_filename, 'w') as f:
                f.write(text)