import asyncio
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from lightrag import LightRAG, QueryParam
from lightrag.utils import EmbeddingFunc
from lightrag.llm import openai_embedding, gpt_4o_mini_complete

class TranscriptionHandler(FileSystemEventHandler):
    def __init__(self, rag_instance, loop):
        self.rag = rag_instance
        self.loop = loop
        
    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('.txt'):
            # Attendre un court instant pour s'assurer que le fichier est complètement écrit
            time.sleep(0.5)
            with open(event.src_path, 'r') as f:
                text = f.read()
            # Utiliser le loop existant pour exécuter la coroutine
            asyncio.run_coroutine_threadsafe(self.rag.ainsert(text), self.loop)

class GraphUpdater:
    def __init__(self, working_dir="rag_workspace", openai_api_key=None):
        self.working_dir = working_dir
        if not os.path.exists(working_dir):
            os.makedirs(working_dir)
        
        # Configuration de l'API OpenAI
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
            
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        self.rag = LightRAG(
            working_dir=working_dir,
            embedding_func=EmbeddingFunc(
                embedding_dim=1536,  # Dimension pour OpenAI embeddings
                max_token_size=8192,
                func=openai_embedding
            ),
            llm_model_func=lambda query: gpt_4o_mini_complete(query, max_tokens=1000),
            chunk_token_size=200,
            llm_model_kwargs={
                "entity_extraction_prompt": """
                Extrait les entités importantes de ce texte. Une entité peut être:
                - Un nombre ou une séquence de nombres
                - Une action ou un verbe important
                - Un concept ou une idée clé
                - Une référence temporelle
                
                Texte: {text}
                
                Format de réponse:
                - Liste d'entités, une par ligne
                - Pour chaque entité: "TYPE: valeur"
                - Types possibles: NUMBER, ACTION, CONCEPT, TIME
                
                Réponse:""",
                "relation_extraction_prompt": """
                Identifie les relations entre les entités suivantes extraites du texte.
                Une relation peut être:
                - Une séquence (SEQUENCE)
                - Une action (ACTION)
                - Une référence (REFERENCE)
                
                Texte: {text}
                Entités: {entities}
                
                Format de réponse:
                - Une relation par ligne
                - Format: "entité1 | TYPE_RELATION | entité2"
                
                Réponse:"""
            }
        )
        
    def start_monitoring(self, directory_to_watch):
        event_handler = TranscriptionHandler(self.rag, self.loop)
        observer = Observer()
        observer.schedule(event_handler, directory_to_watch, recursive=False)
        observer.start()
        return observer