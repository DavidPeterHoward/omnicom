from typing import List, Dict, Any, Optional
from modules.base_module import EnhancedBaseModule
import json
from pathlib import Path
import re
import importlib
from concurrent.futures import ThreadPoolExecutor
import logging


class SearchDomain:
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.description = config.get('description', '')
        self.keywords = config.get('keywords', [])
        self.priority = config.get('priority', 0)
        self.enabled = config.get('enabled', True)
        self.search_function = None
        
        if 'module' in config and 'function' in config:
            try:
                module = importlib.import_module(config['module'])
                self.search_function = getattr(module, config['function'])
            except Exception as e:
                logging.error(f"Error loading search function for domain {name}: {e}")


class DomainRegistry:
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.domains: Dict[str, SearchDomain] = {}
        self.load_domains()

    def load_domains(self):
        config_file = self.storage_path / 'domains.json'
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    configs = json.load(f)
                for name, config in configs.items():
                    self.domains[name] = SearchDomain(name, config)
            except Exception as e:
                logging.error(f"Error loading domain configurations: {e}")

    def save_domains(self):
        try:
            configs = {
                name: {
                    'description': domain.description,
                    'keywords': domain.keywords,
                    'priority': domain.priority,
                    'enabled': domain.enabled
                }
                for name, domain in self.domains.items()
            }
            with open(self.storage_path / 'domains.json', 'w') as f:
                json.dump(configs, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving domain configurations: {e}")

    def add_domain(self, name: str, config: Dict[str, Any]):
        self.domains[name] = SearchDomain(name, config)
        self.save_domains()

    def remove_domain(self, name: str):
        if name in self.domains:
            del self.domains[name]
            self.save_domains()

    def get_matching_domains(self, query: str) -> List[SearchDomain]:
        matching = []
        for domain in self.domains.values():
            if not domain.enabled:
                continue

            if query.startswith(f"{domain.name}:"):
                return [domain]

            for keyword in domain.keywords:
                if keyword in query.lower():
                    matching.append(domain)
                    break

        if not matching:
            matching = [d for d in self.domains.values() if d.enabled]

        return sorted(matching, key=lambda d: d.priority, reverse=True)


class DomainSearchModule(EnhancedBaseModule):
    def __init__(self):
        super().__init__()
        self.storage_path = Path.home() / '.omnibar' / 'domains'
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.registry = DomainRegistry(self.storage_path)
        self.executor = ThreadPoolExecutor(max_workers=4)

    @property
    def name(self) -> str:
        return "Multi-domain Search"

    @property
    def commands(self) -> List[str]:
        return [":d", ":domain", "$"]

    @property
    def example(self) -> str:
        return "math:integral"

    @property
    def icon(self) -> str:
        return "⊚"

    def _parse_query(self, query: str) -> tuple:
        parts = query.split(':', 1)
        if len(parts) == 2 and parts[0].strip() in self.registry.domains:
            return parts[0].strip(), parts[1].strip()
        return None, query.strip()

    def _search_domain(self, domain: SearchDomain, query: str) -> List[Dict[str, Any]]:
        if not domain.search_function:
            return []

        try:
            results = domain.search_function(query)

            normalized = []
            for result in results:
                if isinstance(result, dict):
                    normalized.append({
                        "display": result.get("display", str(result)),
                        "value": result.get("value", str(result)),
                        "details": result.get("details", {}),
                        "score": result.get("score", 0.5),
                        "domain": domain.name
                    })

            return normalized
        except Exception as e:
            self.logger.error(f"Error searching domain {domain.name}: {e}")
            return []

    def _get_results_impl(self, query: str) -> List[Dict[str, Any]]:
        domain_name, search_query = self._parse_query(query)

        results = []
        if domain_name:
            domain = self.registry.domains[domain_name]
            results = self._search_domain(domain, search_query)
        else:
            matching_domains = self.registry.get_matching_domains(search_query)

            for domain in matching_domains:
                domain_results = self._search_domain(domain, search_query)
                results.extend(domain_results)

        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:15]

    def add_search_domain(self, name: str, config: Dict[str, Any]):
        self.registry.add_domain(name, config)

    def remove_search_domain(self, name: str):
        self.registry.remove_domain(name)

    def get_available_domains(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": domain.name,
                "description": domain.description,
                "keywords": domain.keywords,
                "enabled": domain.enabled,
                "priority": domain.priority
            }
            for domain in self.registry.domains.values()
        ]

    def enable_domain(self, name: str, enabled: bool = True):
        if name in self.registry.domains:
            self.registry.domains[name].enabled = enabled
            self.registry.save_domains()

    def set_domain_priority(self, name: str, priority: int):
        if name in self.registry.domains:
            self.registry.domains[name].priority = priority
            self.registry.save_domains()