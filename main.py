import os
import asyncio
from transcriber import AudioFileHandler
from graph_updater import GraphUpdater
from watchdog.observers import Observer
import shutil
from graph_visual_with_html import visualize_graph
import networkx as nx
import sounddevice as sd
import soundfile as sf
import numpy as np
import time
import threading

def create_empty_graph():
    """Crée un graphe vide initial"""
    G = nx.Graph()
    graph_path = os.path.join("rag_workspace", "graph_chunk_entity_relation.graphml")
    nx.write_graphml(G, graph_path)
    return graph_path

def reset_workspace():
    """Réinitialise tous les répertoires de travail sauf text_input/input.txt"""
    # Sauvegarder le contenu de input.txt s'il existe
    input_file = os.path.join("text_input", "input.txt")
    input_content = None
    if os.path.exists(input_file) and os.path.isfile(input_file):
        with open(input_file, 'r', encoding='utf-8') as f:
            input_content = f.read()

    dirs_to_clean = [
        'rag_workspace',
        'audio_batches',
        'transcriptions',
        'graph_viz',
        'text_input'
    ]
    for dir_path in dirs_to_clean:
        if os.path.exists(dir_path):
            # Si c'est un fichier, le supprimer d'abord (sauf input.txt)
            if os.path.isfile(dir_path):
                if dir_path != "text_input/input.txt":
                    os.remove(dir_path)
            # Si c'est un dossier, le supprimer récursivement
            elif os.path.isdir(dir_path):
                if dir_path == "text_input":
                    # Pour text_input, supprimer tous les fichiers sauf input.txt
                    for f in os.listdir(dir_path):
                        if f != "input.txt":
                            file_path = os.path.join(dir_path, f)
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                            elif os.path.isdir(file_path):
                                shutil.rmtree(file_path)
                else:
                    shutil.rmtree(dir_path)
        # Créer le nouveau dossier
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

    # Restaurer le contenu de input.txt
    if input_content is not None:
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write(input_content)

def record_audio(duration=10, fs=44100):
    """Enregistre l'audio en continu par segments"""
    print(f"Enregistrement audio en cours... (segments de {duration} secondes)")
    print("Appuyez sur Ctrl+C pour arrêter")
    
    while True:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
        sd.wait()
        
        audio_path = f'audio_batches/audio_{timestamp}.wav'
        sf.write(audio_path, recording, fs)

def main():
    # Votre clé API OpenAI (à remplacer par votre vraie clé)
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("Erreur: La clé API OpenAI n'est pas définie dans les variables d'environnement")
        return
    
    # Demander si reset
    reset = input("Voulez-vous réinitialiser le graphe ? (Y/N): ").strip().upper()
    if reset == 'Y':
        print("Réinitialisation des répertoires de travail...")
        reset_workspace()
    
    # Créer les dossiers nécessaires
    os.makedirs("audio_batches", exist_ok=True)
    os.makedirs("transcriptions", exist_ok=True)
    os.makedirs("rag_workspace", exist_ok=True)
    os.makedirs("graph_viz", exist_ok=True)
    os.makedirs("text_input", exist_ok=True)
    
    # Initialiser le graphe et la visualisation
    graph_updater = GraphUpdater(working_dir="rag_workspace", openai_api_key=openai_api_key)
    
    # Créer ou charger le graphe et sa visualisation
    graph_path = os.path.join("rag_workspace", "graph_chunk_entity_relation.graphml")
    if not os.path.exists(graph_path):
        graph_path = create_empty_graph()
    
    # Charger le graphe et créer la visualisation
    G = nx.read_graphml(graph_path)
    visualize_graph(G)
    print("Visualisation du graphe initialisée - ouvrez graph.html dans votre navigateur")

    # Demander le mode d'entrée
    print("\nChoisissez le mode d'entrée :")
    print("1: Audio en temps réel")
    print("2: Fichier text_input/input.txt")
    mode = input("Votre choix (1 ou 2): ").strip()
    
    # Initialiser l'observateur pour LightRAG
    rag_observer = graph_updater.start_monitoring("transcriptions")
    
    try:
        if mode == "2":
            # Mode fichier texte
            input_file = os.path.join("text_input", "input.txt")
            if not os.path.exists(input_file):
                print(f"\nErreur: Le fichier {input_file} n'existe pas")
                return
                
            with open(input_file, 'r', encoding='utf-8') as f:
                texte = f.read()
                if not texte.strip():
                    print(f"\nErreur: Le fichier {input_file} est vide")
                    return
                    
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                transcription_path = os.path.join("transcriptions", f"text_{timestamp}.txt")
                with open(transcription_path, 'w', encoding='utf-8') as tf:
                    tf.write(texte)
                print(f"\nFichier texte traité et sauvegardé dans {transcription_path}")
                print("Le graphe va être mis à jour...")
                input("Appuyez sur Entrée pour terminer...")
                
        else:
            # Mode audio en temps réel
            audio_observer = Observer()
            file_handler = AudioFileHandler()
            audio_observer.schedule(file_handler, "audio_batches", recursive=False)
            audio_observer.start()
            
            print("\nDémarrage de l'enregistrement audio...")
            print("Parlez dans le microphone")
            print("Appuyez sur Ctrl+C pour arrêter")
            record_audio()
            
    except KeyboardInterrupt:
        print("\nArrêt du programme...")
    finally:
        if mode != "2":
            audio_observer.stop()
            audio_observer.join()
        rag_observer.stop()
        rag_observer.join()

if __name__ == "__main__":
    main()