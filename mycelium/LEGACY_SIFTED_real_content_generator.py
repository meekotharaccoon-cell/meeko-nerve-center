import json
import subprocess
import os
from datetime import datetime


def load_my_style():
    """Load your personal writing style.

    Uses utf-8-sig so it can safely handle files that include a UTF-8 BOM,
    which previously caused JSONDecodeError when loading my_style.json.
    """
    with open("my_style.json", "r", encoding="utf-8-sig") as f:
        return json.load(f)

def generate_with_ollama(prompt, model="mistral"):
    """Use Ollama to generate content"""
    try:
        # Run Ollama with the prompt
        cmd = ['ollama', 'run', model, prompt]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Error: {result.stderr}"
    except Exception as e:
        return f"Ollama error: {str(e)}"

def create_article(topic, my_style):
    """Create an article in YOUR style"""
    prompt = f"""Write a helpful article about {topic}.
    
Write it in this specific style:
- Tone: {my_style['tone']}
- Writing style: {my_style['writing_style']}
- Use phrases like: {', '.join(my_style['phrases_to_use'])}
- Avoid: {', '.join(my_style['phrases_to_avoid'])}
- Signature: {my_style['signature_style']}
- Target audience: {my_style['target_audience']}

Make it practical, useful, and no-pressure. Include real advice that actually helps people.
End with simple next steps if someone is interested.
"""
    
    print(f" Generating article about: {topic}")
    content = generate_with_ollama(prompt)
    
    article = {
        "title": f"About {topic} - A No-Hype Guide",
        "topic": topic,
        "content": content,
        "author": my_style["author_name"],
        "generated_at": str(datetime.now()),
        "style": my_style["writing_style"]
    }
    
    return article

def save_article(article):
    """Save the article to a file"""
    filename = f"articles/article_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs("articles", exist_ok=True)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(article, f, indent=2, ensure_ascii=False)
    
    # Also create HTML version
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{article['title']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; line-height: 1.6; }}
        h1 {{ color: #333; }}
        .article {{ background: #f9f9f9; padding: 30px; border-radius: 10px; }}
        .meta {{ color: #666; font-size: 0.9em; margin-top: 30px; }}
        .author {{ font-style: italic; }}
    </style>
</head>
<body>
    <div class="article">
        <h1>{article['title']}</h1>
        <div>{article['content'].replace(chr(10), '<br>')}</div>
        <div class="meta">
            <p class="author">Written by: {article['author']} in {article['style']} style</p>
            <p>Generated: {article['generated_at']}</p>
            <p> This content was autonomously generated with AI</p>
        </div>
    </div>
</body>
</html>"""
    
    html_filename = f"articles/{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(html_filename, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return filename, html_filename

def main():
    print(" REAL CONTENT GENERATOR - WITH YOUR STYLE")
    print("=" * 50)
    
    # Load your style
    my_style = load_my_style()
    print(f"Loaded style: {my_style['author_name']} - {my_style['writing_style']}")
    
    # Topics that can make actual money (affiliate potential)
    money_topics = [
        "home office setup on a budget",
        "best free tools for small businesses",
        "making extra income online without scams",
        "productivity apps that actually help",
        "affordable tech that makes life easier"
    ]
    
    # Generate one article
    topic = money_topics[0]  # Start with first topic
    article = create_article(topic, my_style)
    
    # Save it
    json_file, html_file = save_article(article)
    
    print(f"\n ARTICLE CREATED!")
    print(f" JSON: {json_file}")
    print(f" HTML: {html_file}")
    print(f" Length: {len(article['content'])} characters")
    print(f"\n Open the HTML file in your browser to see it!")
    print("=" * 50)

if __name__ == "__main__":
    main()
