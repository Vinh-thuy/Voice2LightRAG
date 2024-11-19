import os
import webbrowser
import networkx as nx
from pyvis.network import Network
import shutil
from datetime import datetime

def visualize_graph(G):
    # Créer un réseau
    net = Network(height="100%", width="100%", bgcolor="#ffffff", font_color="black")
    net.force_atlas_2based()
    
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
        
        # Obtenir le type et la couleur (le type est stocké dans d0)
        node_type = node_data.get('entity_type', '')  # Utiliser la clé 'entity_type'
        if isinstance(node_type, str):
            node_type = node_type.strip('"')  # Enlever les guillemets
        
        # Si le type est vide, essayer avec la clé 'd0'
        if not node_type:
            node_type = node_data.get('d0', '')
            if isinstance(node_type, str):
                node_type = node_type.strip('"')  # Enlever les guillemets
        
        color = color_map.get(node_type, '#808080')  # Gris par défaut
        
        # Obtenir le label et le contenu
        label = node_id.strip('"')  # Enlever les guillemets du label
        content = node_data.get('description', '')  # Utiliser la clé 'description'
        if not content:
            content = node_data.get('d1', label)  # Sinon utiliser 'd1'
        if isinstance(content, str):
            content = content.strip('"')  # Nettoyer le contenu
            
        if len(label) > 30:  # Tronquer les labels trop longs
            label = label[:27] + "..."
        
        # Créer le titre (tooltip) avec le type
        title = f"Type: {node_type}<br>"
        title += f"Contenu: {content}"
        
        # Debug: afficher les informations du nœud
        print(f"Node: {node_id}")
        print(f"Type: {node_type}")
        print(f"Color: {color}")
        print("---")
        
        # Ajouter le nœud avec ses propriétés
        net.add_node(
            node_id,
            label=label,
            title=title,  # Tooltip avec le type et le contenu
            color=color,
            size=30,
            font={'size': 14, 'face': 'arial'},
            borderWidth=2,
            borderWidthSelected=4
        )
    
    # Ajouter les arêtes
    for edge in G.edges(data=True):
        source = edge[0]
        target = edge[1]
        edge_data = edge[2]
        
        print("Edge Data Raw:", edge_data)  # Debug: voir toutes les données brutes
        
        # Obtenir le label de la relation
        edge_label = edge_data.get('type', '')
        if len(edge_label) > 20:  # Tronquer les labels trop longs
            edge_label = edge_label[:17] + "..."
        
        # Récupérer les données de l'arête
        keywords = edge_data.get('keywords', '')  # Essayer avec 'keywords'
        if not keywords:
            keywords = edge_data.get('d5', '')    # Puis avec 'd5'
        if isinstance(keywords, str):
            keywords = keywords.strip('"')  # Nettoyer les guillemets
            
        description = edge_data.get('description', '')  # Essayer avec 'description'
        if not description:
            description = edge_data.get('d4', '')       # Puis avec 'd4'
        if isinstance(description, str):
            description = description.strip('"')
            
        # Debug: afficher les données traitées
        print(f"Source: {source}")
        print(f"Target: {target}")
        print(f"Keywords (raw): {edge_data.get('d5', 'Not found')}")
        print(f"Keywords (processed): {keywords}")
        print(f"Description: {description}")
        print("---")
        
        # Créer le titre (tooltip) pour l'arête avec les mots-clés
        edge_title = f"Mots-clés: {keywords}<br>"
        edge_title += f"Description: {description}"
        
        # Ajouter l'arête avec des données de debug
        edge_id = f"{source}-{target}"
        net.add_edge(
            source,
            target,
            id=edge_id,
            title=edge_title,
            label=edge_label,
            font={'size': 10, 'align': 'middle'},
            arrows={'to': {'enabled': True}},
            color={'color': '#666666', 'opacity': 0.8},
            # Ajouter les données brutes pour le debug
            raw_keywords=keywords,
            raw_description=description
        )
    
    # Configurer les options du graphe
    net.set_options("""
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
    """)
    
    # Sauvegarder d'abord dans un fichier temporaire
    temp_path = "temp_network.html"
    net.save_graph(temp_path)
    
    # Lire le contenu du fichier temporaire
    with open(temp_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extraire le script JavaScript
    start_tag = '<script type="text/javascript">'
    end_tag = '</script>'
    start_index = content.find(start_tag) + len(start_tag)
    end_index = content.find(end_tag, start_index)
    
    if start_index == -1 or end_index == -1:
        print("Erreur: impossible de trouver le script JavaScript")
        return
        
    js_content = content[start_index:end_index].strip()
    
    # Créer le HTML wrapper avec auto-refresh et légende
    legend_html = ""
    for node_type, color in color_map.items():
        legend_html += f"""
        <div class="legend-item"><div class="legend-color" style="background: {color}"></div>{node_type}</div>
        """
    
    wrapper_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Graphe de Connaissances IA</title>
        <style>
            html, body {{
                width: 100%;
                height: 100%;
                margin: 0;
                padding: 0;
                overflow: hidden;
            }}
            #mynetwork {{
                width: 100%;
                height: calc(100vh - 60px);
                margin: 0;
                padding: 0;
            }}
            #controls {{
                position: fixed;
                top: 10px;
                right: 10px;
                z-index: 1000;
                display: flex;
                align-items: center;
            }}
            #pause-button {{
                padding: 8px 15px;
                background-color: #4e79a7;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-family: arial;
                font-size: 14px;
            }}
            #pause-button:hover {{
                background-color: #3d5d84;
            }}
            #refresh-status {{
                margin-right: 10px;
                font-family: arial;
                font-size: 12px;
                color: #666;
            }}
            #legend {{
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                height: 60px;
                background: white;
                border-top: 1px solid #ccc;
                display: flex;
                align-items: center;
                padding: 0 20px;
                font-family: arial;
                font-size: 12px;
                overflow-x: auto;
            }}
            .legend-item {{
                display: flex;
                align-items: center;
                margin-right: 20px;
                white-space: nowrap;
            }}
            .legend-color {{
                width: 15px;
                height: 15px;
                border-radius: 50%;
                margin-right: 5px;
            }}
        </style>
        <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.js"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.css" rel="stylesheet" type="text/css" />
    </head>
    <body>
        <div id="controls">
            <span id="refresh-status">Prochain rafraîchissement dans: 5s</span>
            <button id="pause-button">⏸️ Pause</button>
        </div>
        
        <div id="mynetwork"></div>
        <div id="legend">
            {legend_html}
        </div>
        <script type="text/javascript">
            {js_content}
            
            // Gestion du rafraîchissement automatique
            var isPaused = false;
            var refreshInterval = 5; // secondes
            var countdown = refreshInterval;
            var pauseButton = document.getElementById('pause-button');
            var refreshStatus = document.getElementById('refresh-status');
            var refreshTimer;
            
            function updateCountdown() {{
                if (!isPaused) {{
                    countdown--;
                    refreshStatus.textContent = `Prochain rafraîchissement dans: ${{countdown}}s`;
                    if (countdown <= 0) {{
                        location.reload();
                    }}
                }}
            }}
            
            function startRefreshTimer() {{
                refreshTimer = setInterval(updateCountdown, 1000);
            }}
            
            pauseButton.addEventListener('click', function() {{
                isPaused = !isPaused;
                if (isPaused) {{
                    pauseButton.innerHTML = '▶️ Play';
                    pauseButton.style.backgroundColor = '#59a14f';
                    refreshStatus.textContent = 'Rafraîchissement en pause';
                }} else {{
                    pauseButton.innerHTML = '⏸️ Pause';
                    pauseButton.style.backgroundColor = '#4e79a7';
                    countdown = refreshInterval;
                    refreshStatus.textContent = `Prochain rafraîchissement dans: ${{countdown}}s`;
                }}
            }});
            
            // Démarrer le timer
            startRefreshTimer();
            
            // Ajouter des interactions au survol des nœuds
            network.on("hoverNode", function (params) {{
                document.body.style.cursor = 'pointer';
            }});
            
            network.on("blurNode", function (params) {{
                document.body.style.cursor = 'default';
            }});
            
            // Ajouter des interactions au survol des arêtes
            network.on("hoverEdge", function (params) {{
                document.body.style.cursor = 'pointer';
                var edgeId = params.edge;
                var edge = edges.get(edgeId);
                console.log("Edge hover data:", edge);  // Debug hover
            }});
            
            network.on("blurEdge", function (params) {{
                document.body.style.cursor = 'default';
            }});
            
            // Ajouter des interactions au clic
            network.on("click", function (params) {{
                if (params.nodes.length > 0) {{
                    var nodeId = params.nodes[0];
                    var node = nodes.get(nodeId);
                    console.log("Node clicked:", node);
                }}
                if (params.edges.length > 0) {{
                    var edgeId = params.edges[0];
                    var edge = edges.get(edgeId);
                    console.log("Edge clicked - Full data:", edge);  // Debug click
                    console.log("Edge title:", edge.title);
                    console.log("Raw keywords:", edge.raw_keywords);
                    console.log("Raw description:", edge.raw_description);
                }}
            }});
            
            // Debug: Afficher toutes les arêtes au chargement
            console.log("All edges:", edges.get());
        </script>
    </body>
    </html>
    """
    
    # Chemin du fichier de sortie
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graph.html")
    
    # Sauvegarder le fichier HTML final
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(wrapper_html)
    
    # Supprimer le fichier temporaire
    if os.path.exists(temp_path):
        os.remove(temp_path)
    
    # Ouvrir dans le navigateur si c'est la première fois
    if not hasattr(visualize_graph, 'browser_opened'):
        webbrowser.open('file://' + os.path.abspath(html_path))
        visualize_graph.browser_opened = True

if __name__ == "__main__":
    graph_path = "rag_workspace/graph_chunk_entity_relation.graphml"
    G = nx.read_graphml(graph_path)
    visualize_graph(G)

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
    html_src = "graph.html"
    html_dst = os.path.join(snapshot_dir, f"{name}.html")
    shutil.copy2(html_src, html_dst)
    
    print(f"Graphe sauvegardé dans: {snapshot_dir}")
    return snapshot_dir