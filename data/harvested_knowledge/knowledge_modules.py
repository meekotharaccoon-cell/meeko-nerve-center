#!/usr/bin/env python3
"""
GAZA ROSE - KNOWLEDGE MODULE SYSTEM
Based on Knoll [7]: A knowledge ecosystem where end-users can create,
curate, and configure custom knowledge modules for LLMs.
"""

import os
import json
import hashlib
import frontmatter
from datetime import datetime
from pathlib import Path

class KnowledgeModule:
    """
    A self-contained repository of information that an LLM can access [7].
    Similar to Python packages but for knowledge.
    """
    
    def __init__(self, module_id, name, author, version="1.0.0"):
        self.id = module_id
        self.name = name
        self.author = author
        self.version = version
        self.created = datetime.now().isoformat()
        self.updated = self.created
        self.content = {}
        self.metadata = {
            "id": module_id,
            "name": name,
            "author": author,
            "version": version,
            "created": self.created,
            "updated": self.updated,
            "tags": [],
            "dependencies": [],
            "license": "MIT"
        }
        self.hash = self._compute_hash()
    
    def _compute_hash(self):
        """Compute unique hash for module"""
        data = f"{self.id}{self.name}{self.created}".encode()
        return hashlib.sha256(data).hexdigest()[:16]
    
    def add_content(self, key, value, content_type="text"):
        """Add content to the module"""
        self.content[key] = {
            "value": value,
            "type": content_type,
            "added": datetime.now().isoformat()
        }
        self.updated = datetime.now().isoformat()
    
    def add_tag(self, tag):
        """Add tag for discoverability"""
        if tag not in self.metadata["tags"]:
            self.metadata["tags"].append(tag)
    
    def export(self, format="json"):
        """Export module in specified format"""
        if format == "json":
            return json.dumps({
                "metadata": self.metadata,
                "content": self.content,
                "hash": self.hash
            }, indent=2)
        elif format == "markdown":
            md = f"# {self.name}\n\n"
            md += f"**Author:** {self.author}  \n"
            md += f"**Version:** {self.version}  \n"
            md += f"**ID:** {self.id}  \n"
            md += f"**Hash:** {self.hash}  \n\n"
            md += "## Content\n\n"
            for key, val in self.content.items():
                md += f"### {key}\n{val['value']}\n\n"
            return md
        return self.content
    
    def save(self, path):
        """Save module to file"""
        with open(path, 'w') as f:
            f.write(self.export("json"))

class ModuleRegistry:
    """
    Registry of all available knowledge modules [7].
    Analogous to PyPI or npm registry for knowledge.
    """
    
    def __init__(self, registry_path):
        self.registry_path = Path(registry_path)
        self.registry_path.mkdir(parents=True, exist_ok=True)
        self.modules = {}
        self.load_registry()
    
    def load_registry(self):
        """Load all modules from registry directory"""
        for module_file in self.registry_path.glob("*.json"):
            try:
                with open(module_file, 'r') as f:
                    data = json.load(f)
                    module = KnowledgeModule(
                        data["metadata"]["id"],
                        data["metadata"]["name"],
                        data["metadata"]["author"]
                    )
                    module.metadata = data["metadata"]
                    module.content = data["content"]
                    module.hash = data["hash"]
                    self.modules[module.id] = module
            except:
                pass
    
    def register_module(self, module):
        """Add a module to the registry"""
        self.modules[module.id] = module
        module_path = self.registry_path / f"{module.id}.json"
        module.save(module_path)
    
    def find_modules(self, tags=None, author=None):
        """Find modules by tags or author"""
        results = []
        for module in self.modules.values():
            match = True
            if tags:
                if not any(tag in module.metadata["tags"] for tag in tags):
                    match = False
            if author and module.author != author:
                match = False
            if match:
                results.append(module)
        return results
    
    def get_module(self, module_id):
        """Retrieve a specific module"""
        return self.modules.get(module_id)

# =========================================================================
# CREATE THE KNOWLEDGE MODULE REPOSITORY
# =========================================================================
if __name__ == "__main__":
    registry = ModuleRegistry("./modules")
    print(f" Knowledge Module System initialized [7]")
    print(f"    Registry: {registry.registry_path}")
    print(f"    Modules: {len(registry.modules)}")
    print(f"    Create modules like Python packages, but for knowledge")
