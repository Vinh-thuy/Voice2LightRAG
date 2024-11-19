import os
import asyncio
from graph_updater import GraphUpdater
import shutil
from graph_visual_with_html import visualize_graph
import networkx as nx
from audio_capture import AudioCapture
import threading
from utils import reset_workspace


def create_empty_graph():
    """Crée un graphe vide initial"""
    G = nx.Graph()
    graph_path = os.path.join("rag_workspace", "graph_chunk_entity_relation.graphml")
    nx.write_graphml(G, graph_path)
    return graph_path

def ensure_html_exists():
    """S'assure que le fichier HTML de visualisation existe"""
    viz_dir = "graph_viz"
    html_path = os.path.join(viz_dir, "graph.html")
    
    if not os.path.exists(viz_dir):
        os.makedirs(viz_dir)
        print(f"* Création du dossier {viz_dir}")
    
    if not os.path.exists(html_path):
        print("* Création initiale du fichier HTML")
        G = nx.Graph()  # Graphe vide initial
        visualize_graph(G)
    else:
        print("* Fichier HTML existant trouvé")

    return html_path

def force_regenerate_html():
    """Force la régénération du fichier HTML"""
    print("* Forçage de la régénération du fichier HTML...")
    G = nx.Graph()
    if os.path.exists("rag_workspace/graph_chunk_entity_relation.graphml"):
        try:
            G = nx.read_graphml("rag_workspace/graph_chunk_entity_relation.graphml")
            print("* Graphe existant chargé")
        except Exception as e:
            print(f"! Erreur lors du chargement du graphe: {str(e)}")
    visualize_graph(G)
    print("* Régénération du fichier HTML terminée")

def main():
    """Point d'entrée principal"""
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
    
    # S'assurer que le fichier HTML existe
    html_path = ensure_html_exists()
    
    # Créer les dossiers nécessaires
    os.makedirs("audio_segments", exist_ok=True)
    os.makedirs("rag_workspace", exist_ok=True)
    os.makedirs("text_input", exist_ok=True)
    
    # Initialiser l'enregistreur audio
    recorder = AudioCapture(segment_duration=15)
    
    # Démarrer l'enregistrement dans un thread séparé
    recording_thread = threading.Thread(target=recorder.start_recording)
    recording_thread.start()
    
    print("\nEnregistrement audio en cours... Appuyez sur Ctrl+C pour arrêter")
    print("Les transcriptions seront automatiquement ajoutées au fichier text_input/input.txt")
    print("Le graphe sera mis à jour automatiquement après chaque transcription")
    
    try:
        # Attendre que l'utilisateur arrête avec Ctrl+C
        recording_thread.join()
    except KeyboardInterrupt:
        print("\nArrêt de l'enregistrement...")
        recorder.stop_recording()
        recording_thread.join()
        print("Enregistrement terminé")

if __name__ == "__main__":
    try:
        print("* Forçage de la régénération du graphe...")
        force_regenerate_html()
        print("* Régénération terminée avec succès")
    except Exception as e:
        print(f"! Erreur lors de la régénération: {str(e)}")
    main()