import os
import shutil

def reset_workspace():
    """Réinitialise tous les répertoires de travail sauf text_input/input.txt"""
    print("Réinitialisation des répertoires de travail...")
    
    # Sauvegarder le contenu de input.txt s'il existe
    input_file = os.path.join("text_input", "input.txt")
    input_content = None
    if os.path.exists(input_file) and os.path.isfile(input_file):
        with open(input_file, 'r', encoding='utf-8') as f:
            input_content = f.read()

    # Chemins des dossiers à réinitialiser
    workspace_paths = [
        "rag_workspace",
        "audio_segments"
    ]
    
    for path in workspace_paths:
        if os.path.exists(path):
            try:
                # Vérifier si text.txt est en lecture seule et le rendre modifiable si nécessaire
                text_file = os.path.join(path, "text.txt")
                if os.path.exists(text_file):
                    os.chmod(text_file, 0o644)  # Rendre le fichier modifiable
                
                print(f"* Suppression de {path}")
                shutil.rmtree(path)
            except Exception as e:
                print(f"! Erreur lors de la suppression de {path}: {str(e)}")
        
        # Recréer le dossier
        os.makedirs(path, exist_ok=True)
    
    # Recréer text_input si nécessaire
    if not os.path.exists("text_input"):
        os.makedirs("text_input")
    
    # Restaurer input.txt
    if input_content is not None:
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write(input_content)
    
    print("* Tous les dossiers de travail ont été réinitialisés")
    return True