import os
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential

@dataclass
class Message:
    role: str
    content: str

@dataclass
class CompletionResponse:
    content: str
    usage: Dict
    model: str

class CerebrasClient:
    def __init__(self):
        self.api_key = os.getenv("API_KEY")
        self.base_url = os.getenv("BASE_URL", "https://api.cerebras.ai/v1")
        self.model = os.getenv("MODEL", "llama-3.3-70b")
        self.max_tokens = int(os.getenv("MAX_TOKENS", "4096"))
        self.temperature = float(os.getenv("TEMPERATURE", "0.7"))
        
        if not self.api_key:
            raise ValueError("API_KEY not set in .env file")
        
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=60)
        )
        return self
    
    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def complete(self, messages: List[Message]) -> CompletionResponse:
        if not self.session:
            raise RuntimeError("Client not initialized")
        
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        
        async with self.session.post(f"{self.base_url}/chat/completions", json=payload) as response:
            response.raise_for_status()
            data = await response.json()
            
            return CompletionResponse(
                content=data["choices"][0]["message"]["content"],
                usage=data.get("usage", {}),
                model=data.get("model", self.model)
            )
