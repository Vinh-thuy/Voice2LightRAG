from graph_visual_with_html import save_graph_snapshot
import sys

if __name__ == "__main__":
    if len(sys.argv) > 1:
        name = sys.argv[1]
    else:
        name = "snapshot"

    save_graph_snapshot(name)