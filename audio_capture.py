import sounddevice as sd
import soundfile as sf
import numpy as np
import time
import os

class AudioCapture:
    def __init__(self, batch_duration=10):
        self.batch_duration = batch_duration
        self.recording = False
        self.sample_rate = 44100
        self.channels = 1
        
    def start_recording(self, output_dir="audio_batches"):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        self.recording = True
        print("* Enregistrement démarré")
        
        try:
            while self.recording:
                # Enregistrer un segment
                recording = sd.rec(
                    int(self.sample_rate * self.batch_duration),
                    samplerate=self.sample_rate,
                    channels=self.channels
                )
                
                # Attendre que l'enregistrement soit terminé
                sd.wait()
                
                if self.recording:  # Vérifier si on doit encore sauvegarder
                    timestamp = int(time.time())
                    filename = os.path.join(output_dir, f"batch_{timestamp}.wav")
                    sf.write(filename, recording, self.sample_rate)
                    print(f"* Segment audio sauvegardé: {filename}")
                    
        except Exception as e:
            print(f"Erreur lors de l'enregistrement: {e}")
            self.recording = False
    
    def stop_recording(self):
        self.recording = False