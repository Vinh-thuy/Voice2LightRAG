import sounddevice as sd
import soundfile as sf
import numpy as np
import time
import os
import shutil
import threading
import asyncio
from datetime import datetime
from lightrag import LightRAG, QueryParam
from lightrag.llm import openai_embedding, gpt_4o_mini_complete
from transcription import transcribe_audio
from graph_visual_with_html import visualize_graph
import networkx as nx
from utils import reset_workspace
import json

class AudioCapture:
    def __init__(self, segment_duration=15, openai_api_key=None):
        self.segment_duration = segment_duration
        self.recording = False
        self.sample_rate = 44100
        self.channels = 1
        self.transcription_file = "text_input/input.txt"
        self.rag_workspace = "/Users/vinh/RTLightRAG/rag_workspace"
        self.text_file = "text_input/input.txt"
        
        # Configuration de l'API OpenAI
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
        
        # Initialisation de LightRAG avec configuration de base
        self.rag = LightRAG(
            working_dir=self.rag_workspace,
            llm_model_func=gpt_4o_mini_complete,
            embedding_func=openai_embedding
        )
        
    def reset_rag_workspace(self):
        """Réinitialise tous les dossiers de travail"""
        reset_workspace()
        print("* Tous les dossiers de travail ont été réinitialisés")
        
    def append_transcription(self, text):
        """Ajoute la transcription au fichier texte"""
        os.makedirs(os.path.dirname(self.transcription_file), exist_ok=True)
        
        # Ajouter un timestamp et la nouvelle transcription
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.transcription_file, 'a', encoding='utf-8') as f:
            f.write(f"\n[{timestamp}] {text}")
        
        print(f"* Transcription ajoutée au fichier {self.transcription_file}")
        
    async def update_rag(self, text):
        """Met à jour la base RAG avec le nouveau texte"""
        try:
            print(f"* Début de la mise à jour RAG")
            print(f"* Workspace path: {self.rag_workspace}")
            
            # Sauvegarder l'ancien graphe si il existe
            old_graph = None
            old_graph_path = os.path.join(self.rag_workspace, "graph_chunk_entity_relation.graphml")
            if os.path.exists(old_graph_path):
                old_graph = nx.read_graphml(old_graph_path)
                print("* Ancien graphe sauvegardé")
            
            # Réinitialiser complètement le workspace RAG
            if os.path.exists(self.rag_workspace):
                print("* Suppression de l'ancien workspace")
                shutil.rmtree(self.rag_workspace)
            os.makedirs(self.rag_workspace)
            
            # Lire tout le texte du fichier
            print("* Lecture du fichier texte")
            with open(self.text_file, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Créer le fichier de configuration
            config_path = os.path.join(self.rag_workspace, "config.json")
            print(f"* Création du fichier de configuration: {config_path}")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "model": "gpt-4",
                    "embedding_model": "text-embedding-ada-002"
                }, f, indent=4)
            
            # Créer le fichier de texte dans le workspace
            workspace_text_file = os.path.join(self.rag_workspace, "text.txt")
            print(f"* Copie du texte vers: {workspace_text_file}")
            with open(workspace_text_file, 'w', encoding='utf-8') as f:
                f.write(text)
            
            # Réinitialiser l'instance de LightRAG
            print("* Initialisation de LightRAG")
            self.rag = LightRAG(
                working_dir=self.rag_workspace,
                llm_model_func=gpt_4o_mini_complete,
                embedding_func=openai_embedding
            )
            
            # Reconstruire la base RAG
            print("* Reconstruction de la base RAG")
            await self.rag.ainsert(text)
            print("* Base RAG reconstruite avec le texte complet")
            
            # Mettre à jour la visualisation
            graph_path = os.path.join(self.rag_workspace, "graph_chunk_entity_relation.graphml")
            print(f"* Recherche du graphe: {graph_path}")
            
            # Attendre un peu que le fichier soit créé si nécessaire
            for _ in range(3):  # 3 tentatives
                if os.path.exists(graph_path):
                    print("* Graphe trouvé, création de la visualisation")
                    G = nx.read_graphml(graph_path)
                    if len(G.nodes()) > 0:
                        visualize_graph(G)
                        print("* Visualisation mise à jour")
                        break
                    else:
                        print("! Graphe vide")
                else:
                    print("! Fichier graphe non trouvé, nouvelle tentative dans 1s")
                    await asyncio.sleep(1)
            else:  # Si toutes les tentatives échouent
                print("! Impossible de trouver un graphe valide")
                if old_graph is not None:
                    print("* Utilisation de l'ancien graphe pour la visualisation")
                    visualize_graph(old_graph)
        
        except Exception as e:
            print(f"! Erreur lors de la mise à jour RAG: {str(e)}")
            import traceback
            print(traceback.format_exc())
        
    async def process_audio_segment(self, audio_file):
        """Traite un segment audio de manière asynchrone"""
        try:
            # Transcription du segment audio
            print(f"* Segment audio sauvegardé: {audio_file}")
            transcription = transcribe_audio(audio_file)
            print(transcription)
                
            # Ajouter la transcription au fichier texte
            self.append_transcription(transcription)
            print("* Transcription ajoutée au fichier text_input/input.txt")
                
            # Réinitialiser le workspace RAG pour la nouvelle base
            self.reset_rag_workspace()
                
            # Mettre à jour la base RAG de manière asynchrone
            await self.update_rag(transcription)
                
            print(f"* Segment audio traité: {audio_file}")
            
            # Nettoyer le fichier audio après traitement
            try:
                os.remove(audio_file)
            except:
                pass
            
        except Exception as e:
            print(f"Erreur lors du traitement du segment audio: {e}")
            
    def process_audio_segment_wrapper(self, audio_file):
        """Wrapper pour exécuter process_audio_segment dans une boucle asyncio"""
        try:
            # Créer une nouvelle boucle pour ce thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Exécuter la coroutine et s'assurer que la boucle est fermée proprement
            try:
                loop.run_until_complete(self.process_audio_segment(audio_file))
            finally:
                loop.close()
        except Exception as e:
            print(f"Erreur dans le wrapper du segment audio: {e}")

    def start_recording(self, output_dir="audio_segments"):
        """Démarre l'enregistrement audio en continu"""
        self.recording = True
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            while self.recording:
                # Enregistrer un segment audio
                print(f"\n* Enregistrement d'un segment de {self.segment_duration} secondes...")
                audio_data = sd.rec(
                    int(self.segment_duration * self.sample_rate),
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    dtype=np.float32
                )
                sd.wait()
                
                # Sauvegarder le segment
                timestamp = int(time.time())
                audio_file = os.path.join(output_dir, f"segment_{timestamp}.wav")
                sf.write(audio_file, audio_data, self.sample_rate)
                
                # Traiter le segment de manière asynchrone
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.process_audio_segment(audio_file))
                    loop.close()
                except Exception as e:
                    print(f"! Erreur dans la boucle de traitement: {str(e)}")
                    import traceback
                    print(traceback.format_exc())
                    
        except KeyboardInterrupt:
            print("\n* Arrêt de l'enregistrement...")
        except Exception as e:
            print(f"! Erreur lors de l'enregistrement: {str(e)}")
            import traceback
            print(traceback.format_exc())
        finally:
            self.recording = False

    def stop_recording(self):
        """Arrête l'enregistrement"""
        self.recording = False
        print("* Enregistrement arrêté")

if __name__ == "__main__":
    # Test de la classe
    recorder = AudioCapture()
    print("Appuyez sur Ctrl+C pour arrêter l'enregistrement")
    try:
        recorder.start_recording()
    except KeyboardInterrupt:
        recorder.stop_recording()
        print("\nEnregistrement terminé")