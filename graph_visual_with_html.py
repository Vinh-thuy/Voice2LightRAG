import os
import webbrowser
import networkx as nx
from pyvis.network import Network
import shutil
from datetime import datetime
import json
import stat
import asyncio
import nest_asyncio

# Permet d'éviter les conflits d'event loop
nest_asyncio.apply()

async def async_visualize_graph(G):
    """Version asynchrone de la visualisation du graphe"""
    # Vérifier que le graphe est valide
    if G is None:
        print("! Graphe invalide")
        G = nx.Graph()  # Créer un graphe vide si invalide
    
    try:
        print(f"* Création du réseau avec {len(G.nodes())} nœuds et {len(G.edges())} arêtes")
        
        # Forcer la suppression et recréation du fichier HTML
        viz_dir = "graph_viz"
        html_path = os.path.join(viz_dir, "graph.html")
        
        if os.path.exists(html_path):
            try:
                os.remove(html_path)
                print("* Ancien fichier HTML supprimé")
            except Exception as e:
                print(f"! Erreur lors de la suppression du fichier HTML: {str(e)}")
        
        if not os.path.exists(viz_dir):
            os.makedirs(viz_dir)
            print(f"* Création du dossier {viz_dir}")

        # Créer un nouveau réseau
        net = Network(height="90vh", width="90vw", bgcolor="#ffffff", font_color="black")
        net.force_atlas_2based()
        
        # Configurer les options du réseau
        options_str = """
        {
            "physics": {
                "forceAtlas2Based": {
                    "gravitationalConstant": -50,
                    "centralGravity": 0.01,
                    "springLength": 100,
                    "springConstant": 0.08,
                    "damping": 0.4,
                    "avoidOverlap": 1
                },
                "solver": "forceAtlas2Based",
                "stabilization": {
                    "enabled": true,
                    "iterations": 1000,
                    "updateInterval": 100
                }
            },
            "interaction": {
                "hover": true,
                "tooltipDelay": 200,
                "zoomView": true,
                "dragView": true,
                "hideEdgesOnDrag": true,
                "hideEdgesOnZoom": true
            },
            "edges": {
                "smooth": {
                    "type": "continuous",
                    "forceDirection": "none"
                },
                "color": {
                    "inherit": false
                }
            },
            "nodes": {
                "shape": "dot",
                "scaling": {
                    "min": 20,
                    "max": 40
                }
            }
        }
        """
        
        # Appliquer les options directement comme une chaîne JSON
        net.set_options(options_str)
        
        # Couleurs par type d'entité
        color_map = {
            'CONCEPT': '#e15759',       # Rouge
            'ACTEUR': '#edc949',        # Jaune
            'CONTEXTE': '#76b7b2',      # Turquoise
            'IMPACT': '#f28e2c',        # Orange
            'SOLUTION': '#4e79a7',      # Bleu
            'EXEMPLE': '#af7aa1',       # Violet
            'PROCESSUS': '#59a14f',     # Vert
            'DEFI': '#ff9da7'           # Rose
        }
        
        # Ajouter les nœuds
        for node in G.nodes(data=True):
            node_id = node[0]
            node_data = node[1]
            
            # Obtenir le type et la couleur
            node_type = node_data.get('entity_type', '')
            if isinstance(node_type, str):
                node_type = node_type.strip('"')
            
            if not node_type:
                node_type = node_data.get('d0', '')
                if isinstance(node_type, str):
                    node_type = node_type.strip('"')
            
            color = color_map.get(node_type, '#808080')
            
            # Obtenir le label et le contenu
            label = node_id.strip('"')
            content = node_data.get('description', '')
            if not content:
                content = node_data.get('d1', label)
            if isinstance(content, str):
                content = content.strip('"')
                
            if len(label) > 30:
                label = label[:27] + "..."
            
            # Créer le titre avec le type
            title = f"Type: {node_type}<br>"
            title += f"Contenu: {content}"
            
            # Ajouter le nœud avec ses propriétés
            net.add_node(
                node_id,
                label=label,
                title=title,
                color=color,
                size=30,
                font={'size': 14, 'face': 'arial'},
                borderWidth=2,
                borderWidthSelected=4
            )
        
        # Ajouter les arêtes avec des flèches
        for edge in G.edges(data=True):
            source = edge[0]
            target = edge[1]
            edge_data = edge[2]
            
            # Obtenir le label de la relation
            edge_label = edge_data.get('type', '')
            if len(edge_label) > 20:
                edge_label = edge_label[:17] + "..."
            
            # Récupérer les données de l'arête
            keywords = edge_data.get('keywords', '')
            if not keywords:
                keywords = edge_data.get('d5', '')
            if isinstance(keywords, str):
                keywords = keywords.strip('"')
                
            description = edge_data.get('description', '')
            if not description:
                description = edge_data.get('d4', '')
            if isinstance(description, str):
                description = description.strip('"')
            
            # Créer le titre pour l'arête avec les mots-clés
            edge_title = f"Mots-clés: {keywords}<br>"
            edge_title += f"Description: {description}"
            
            # Ajouter l'arête avec ses propriétés
            net.add_edge(
                source,
                target,
                title=edge_title,
                label=edge_label,
                arrows={'to': {'enabled': True}},
                color={'color': '#666666'},
                font={'size': 10}
            )
        
        # Template HTML personnalisé avec correction pour l'affichage complet
        html_template = """
        <html>
        <head>
            <meta charset="utf-8">
            <title>Graph Visualization</title>
            <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.6/dist/vis-network.min.js"></script>
            <link href="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.6/dist/vis-network.min.css" rel="stylesheet" type="text/css" />
            <style type="text/css">
                html, body {
                    width: 100%;
                    height: 100%;
                    margin: 0;
                    padding: 0;
                    overflow: hidden;
                }
                #mynetwork {
                    width: 100%;
                    height: 100%;
                    position: absolute;
                    top: 0;
                    left: 0;
                }
                #legend {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: rgba(255, 255, 255, 0.9);
                    padding: 10px;
                    border-radius: 5px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                    z-index: 1000;
                }
                .legend-item {
                    margin: 5px 0;
                    display: flex;
                    align-items: center;
                }
                .legend-color {
                    width: 20px;
                    height: 20px;
                    margin-right: 10px;
                    border-radius: 3px;
                }
            </style>
        </head>
        <body>
            <div id="mynetwork"></div>
            <div id="legend">
                <h3 style="margin-top: 0;">Légende</h3>
                <div id="legend-content"></div>
            </div>
        </body>
        </html>
        """
        
        # Sauvegarder avec le template personnalisé
        try:
            net.template = html_template
            
            net.show(html_path, notebook=False)
            
            # Ajouter la légende au HTML généré
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Remplacer le placeholder des couleurs
            colors_json = {k: v for k, v in color_map.items()}
            colors_str = str(colors_json).replace("'", '"')
            html_content = html_content.replace("{% for type, color in colors.items() %}", "")
            html_content = html_content.replace("{% endfor %}", "")
            
            # Générer les items de la légende
            legend_items = ""
            for type_, color in color_map.items():
                legend_items += f'''
                <div class="legend-item">
                    <div class="legend-color" style="background-color: {color}"></div>
                    <div>{type_}</div>
                </div>'''
            
            html_content = html_content.replace("{{ type }}", "")
            html_content = html_content.replace("{{ color }}", "")
            html_content = html_content.replace('<div id="legend">\n                <h3>Légende</h3>\n                \n            </div>', 
                                              f'<div id="legend">\n                <h3>Légende</h3>{legend_items}\n            </div>')
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Vérifier que le fichier a été créé et n'est pas vide
            if os.path.exists(html_path):
                size = os.path.getsize(html_path)
                print(f"* HTML généré avec succès ({size} bytes): {html_path}")
                if size < 100:  # Si le fichier est trop petit, il y a probablement un problème
                    print("! Attention: Le fichier HTML semble trop petit")
            else:
                print(f"! Erreur: Le fichier HTML n'a pas été créé: {html_path}")
                
        except Exception as e:
            print(f"! Erreur lors de la sauvegarde du HTML: {str(e)}")
            import traceback
            print(traceback.format_exc())
        
        # Toujours ouvrir le fichier HTML dans le navigateur
        webbrowser.open('file://' + os.path.abspath(html_path))
    
    except Exception as e:
        print(f"! Erreur lors de la visualisation du graphe: {str(e)}")
        import traceback
        print(traceback.format_exc())

def visualize_graph(G):
    """Wrapper synchrone pour la visualisation du graphe"""
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(async_visualize_graph(G))
    finally:
        if not loop.is_closed():
            loop.close()

def protect_text_file():
    """Protège le fichier text.txt en le rendant en lecture seule"""
    text_file = os.path.join("/Users/vinh/RTLightRAG/rag_workspace", "text.txt")
    if os.path.exists(text_file):
        try:
            # Rend le fichier en lecture seule (400 = r--------)
            os.chmod(text_file, stat.S_IRUSR)
            print(f"* Fichier {text_file} protégé en lecture seule")
        except Exception as e:
            print(f"! Erreur lors de la protection du fichier: {str(e)}")

def save_graph_snapshot(name):
    """Sauvegarde une copie du graphe et du HTML dans un dossier horodaté"""
    # Créer un dossier de sauvegarde avec la date
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_graphs")
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    # Créer un sous-dossier pour cette sauvegarde
    snapshot_dir = os.path.join(save_dir, f"{name}_{timestamp}")
    os.makedirs(snapshot_dir)
    
    # Copier le graphe
    graph_src = os.path.join("rag_workspace", "graph_chunk_entity_relation.graphml")
    graph_dst = os.path.join(snapshot_dir, f"{name}.graphml")
    shutil.copy2(graph_src, graph_dst)
    
    # Copier le HTML
    html_src = "graph_viz/graph.html"
    html_dst = os.path.join(snapshot_dir, f"{name}.html")
    shutil.copy2(html_src, html_dst)
    
    print(f"Graphe sauvegardé dans: {snapshot_dir}")
    return snapshot_dir

if __name__ == "__main__":
    graph_path = "rag_workspace/graph_chunk_entity_relation.graphml"
    G = nx.read_graphml(graph_path)
    visualize_graph(G)