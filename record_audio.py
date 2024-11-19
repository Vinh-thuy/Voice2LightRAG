import sounddevice as sd
import soundfile as sf
import numpy as np
import time
import os

def record_audio(duration=5, sample_rate=44100, channels=1):
    """
    Enregistre l'audio pendant une durée spécifiée et le sauve en WAV
    
    Args:
        duration (int): Durée d'enregistrement en secondes
        sample_rate (int): Taux d'échantillonnage
        channels (int): Nombre de canaux (1 pour mono, 2 pour stéréo)
    """
    print(f"Début de l'enregistrement pour {duration} secondes...")
    
    # Enregistrement
    recording = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=channels
    )
    
    # Attendre la fin de l'enregistrement
    sd.wait()
    
    # Créer le dossier de sortie s'il n'existe pas
    os.makedirs("audio_recordings", exist_ok=True)
    
    # Générer un nom de fichier avec timestamp
    timestamp = int(time.time())
    filename = f"audio_recordings/recording_{timestamp}.wav"
    
    # Sauvegarder en WAV
    sf.write(filename, recording, sample_rate)
    print(f"Enregistrement sauvegardé dans: {filename}")
    return filename

if __name__ == "__main__":
    try:
        # Enregistrer pendant 5 secondes
        filename = record_audio(duration=5)
        print(f"Fichier audio créé : {filename}")
    except KeyboardInterrupt:
        print("\nEnregistrement interrompu par l'utilisateur")
    except Exception as e:
        print(f"Erreur lors de l'enregistrement : {str(e)}")