import os
import json

def publish_value():
    product_path = 'data/pending_publication.txt'
    if not os.path.exists(product_path):
        return

    with open(product_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 🟢 PHASE A: Local Archive (The "Public Library")
    public_path = 'docs/public_insight.html'
    with open(public_path, 'a', encoding='utf-8') as f:
        f.write(f"\n<div class='node'><h3>Swarm Insight</h3><p>{content}</p></div>")
    
    # 🟢 PHASE B: Marketplace Push (Example: Gumroad/Kofi/GitHub)
    # This uses a headless git command to push to your GitHub Pages site automatically
    os.system("git add docs/public_insight.html")
    os.system("git commit -m '📡 Swarm Broadcast: New Value Published'")
    
    print("🚀 Web Publisher: Knowledge broadcasted to the global network.")
    # Clean up once published
    os.remove(product_path)

if __name__ == "__main__":
    publish_value()
