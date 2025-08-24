from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any

ADAPTERS: Dict[str, 'DataAdapter'] = {}

class DataAdapter(ABC):
    @abstractmethod
    def load(self, path: str):
        raise NotImplementedError

def register(name: str, adapter: 'DataAdapter') -> None:
    ADAPTERS[name] = adapter

def get(name: str) -> 'DataAdapter':
    return ADAPTERS[name]
