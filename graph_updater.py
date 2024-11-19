import asyncio
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from lightrag import LightRAG, QueryParam
from lightrag.llm import openai_embedding, gpt_4o_mini_complete
from graph_visual_with_html import visualize_graph
import networkx as nx

class TranscriptionHandler(FileSystemEventHandler):
    def __init__(self, rag_instance):
        self.rag = rag_instance
        
    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('.txt'):
            # Attendre un court instant pour s'assurer que le fichier est complètement écrit
            time.sleep(0.5)
            with open(event.src_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Utiliser asyncio pour exécuter l'insertion
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # Insérer le texte dans LightRAG
                loop.run_until_complete(self.rag.ainsert(text))
                print(f"Texte inséré dans LightRAG: {text}")
                
                # Mettre à jour la visualisation
                graph_path = os.path.join(self.rag.working_dir, "graph_chunk_entity_relation.graphml")
                if os.path.exists(graph_path):
                    G = nx.read_graphml(graph_path)
                    visualize_graph(G)
                    print("Visualisation mise à jour")
            finally:
                loop.close()

class GraphUpdater:
    def __init__(self, working_dir="rag_workspace", openai_api_key=None):
        self.working_dir = working_dir
        if not os.path.exists(working_dir):
            os.makedirs(working_dir)
        
        # Configuration de l'API OpenAI
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
        
        # Initialisation de LightRAG avec configuration de base
        self.rag = LightRAG(
            working_dir=working_dir,
            llm_model_func=gpt_4o_mini_complete,
            embedding_func=openai_embedding
        )
        
    def start_monitoring(self, directory_to_watch):
        # Créer et démarrer l'observateur
        event_handler = TranscriptionHandler(self.rag)
        observer = Observer()
        observer.schedule(event_handler, directory_to_watch, recursive=False)
        observer.start()
        return observer