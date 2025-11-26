"""
Policy Repository - Simple Dict-Based Implementation
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PolicyRepository:
    """Simple repository using dict policies"""
    
    def __init__(self, policy_dir: Optional[str] = None):
        self.policies: Dict[str, Dict] = {}
        self.action_index: Dict[str, set] = defaultdict(set)
        self.subject_index: Dict[str, set] = defaultdict(set)
        self.resource_index: Dict[str, set] = defaultdict(set)
        self.logger = logger
        
        if policy_dir:
            count = self.load_all_policies_from_directory(policy_dir)
            self.logger.info(f"Loaded {count} policies from {policy_dir}")
    
    def load_all_policies_from_directory(self, directory: str) -> int:
        """Load all YAML files from directory"""
        count = 0
        policy_path = Path(directory)
        
        if not policy_path.exists():
            self.logger.warning(f"Policy directory {directory} does not exist")
            return 0
        
        yaml_files = list(policy_path.glob("**/*.yaml"))
        for yaml_file in yaml_files:
            if ".disabled" not in str(yaml_file):
                try:
                    policies = self.load_policies_from_yaml(str(yaml_file))
                    count += len(policies)
                    self.logger.info(f"Loaded {len(policies)} policies from {yaml_file.name}")
                except Exception as e:
                    self.logger.error(f"Failed to load {yaml_file}: {e}")
        return count
    
    def load_policies_from_yaml(self, yaml_path: str, level=None) -> List[Dict]:
        """Load policies from YAML as simple dicts"""
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        
        if not data or 'policies' not in data:
            return []
        
        policies = []
        for p in data.get('policies', []):
            policy = {
                'id': p.get('id'),
                'action': p.get('action'),
                'subject': p.get('subject', '*'),
                'resource': p.get('resource', '*'),
                'effect': p.get('effect', 'deny'),
                'description': p.get('description', ''),
                'level': p.get('level', 'agent'),
                'match': p.get('match', {}),
                'priority': p.get('priority', 50),
            }
            
            if policy['id'] and policy['action']:
                self.add_policy(policy)
                policies.append(policy)
        
        return policies
    
    def add_policy(self, policy: Dict) -> None:
        """Add a dict policy"""
        policy_id = policy.get('id')
        if not policy_id:
            return
        
        self.policies[policy_id] = policy
        
        self.action_index[policy.get('action', '*')].add(policy_id)
        self.subject_index[policy.get('subject', '*')].add(policy_id)
        self.resource_index[policy.get('resource', '*')].add(policy_id)
    
    def list(self) -> List[Dict]:
        """List all policies"""
        return list(self.policies.values())
    
    def get(self, policy_id: str) -> Optional[Dict]:
        """Get a policy by ID"""
        return self.policies.get(policy_id)
    
    def size(self) -> int:
        """Get number of policies"""
        return len(self.policies)
