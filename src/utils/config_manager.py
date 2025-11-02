"""
Configuration management for the AST-Solidity pipeline.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class LLMProviderConfig:
    """Configuration for LLM provider."""
    name: str = "qwen"  # qwen, deepseek, openai
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    
    def load_from_env(self):
        """Load configuration from environment variables."""
        if self.api_key is None:
            self.api_key = os.getenv("LLM_API_KEY")
        if self.base_url is None:
            self.base_url = os.getenv("LLM_BASE_URL")
        if self.model is None:
            self.model = os.getenv("LLM_MODEL")
        
        # Set defaults based on provider
        if self.name == "qwen" and not self.base_url:
            self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
            self.model = self.model or "qwen-plus"
        elif self.name == "deepseek" and not self.base_url:
            self.base_url = "https://api.deepseek.com"
            self.model = self.model or "deepseek-chat"
        elif self.name == "openai" and not self.base_url:
            self.base_url = "https://api.openai.com/v1"
            self.model = self.model or "gpt-4"


@dataclass
class DetectionConfig:
    """Configuration for Ponzi detection."""
    enabled: bool = False
    concurrency_limit: int = 40
    cache_enabled: bool = True
    cache_dir: str = "cache"
    timeout: int = 60
    max_retries: int = 3
    provider: LLMProviderConfig = field(default_factory=LLMProviderConfig)


@dataclass
class DFGConfig:
    """Configuration for DFG generation."""
    mode: str = "standard"  # compact, standard, verbose
    include_types: list = field(default_factory=lambda: [
        "contract_definition",
        "function_definition",
        "variable_declaration",
        "assignment",
        "function_call",
        "if_statement",
        "while_statement",
        "for_statement",
        "return",
        "modifier_invocation"
    ])
    edge_types: list = field(default_factory=lambda: [
        "data_dependency",
        "control_flow",
        "call"
    ])


@dataclass
class OutputConfig:
    """Configuration for output."""
    format: str = "json"
    output_dir: str = "output"
    prettify: bool = True
    include_metadata: bool = True
    include_source_code: bool = False


@dataclass
class PipelineConfig:
    """Main configuration for the pipeline."""
    solidity_version: str = "0.4.x"
    dfg: DFGConfig = field(default_factory=DFGConfig)
    detection: DetectionConfig = field(default_factory=DetectionConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    verbose: bool = False
    
    @classmethod
    def load_from_file(cls, config_path: str) -> 'PipelineConfig':
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
            
            # Parse nested configs
            config = cls()
            
            if 'solidity_version' in data:
                config.solidity_version = data['solidity_version']
            
            if 'dfg' in data:
                config.dfg = DFGConfig(**data['dfg'])
            
            if 'detection' in data:
                det_data = data['detection']
                if 'provider' in det_data:
                    provider = LLMProviderConfig(**det_data['provider'])
                    det_data['provider'] = provider
                config.detection = DetectionConfig(**det_data)
            
            if 'output' in data:
                config.output = OutputConfig(**data['output'])
            
            if 'verbose' in data:
                config.verbose = data['verbose']
            
            return config
            
        except FileNotFoundError:
            # Return default config if file not found
            return cls()
        except Exception as e:
            print(f"Warning: Failed to load config from {config_path}: {e}")
            return cls()
    
    @classmethod
    def load_from_args(cls, args) -> 'PipelineConfig':
        """Load configuration from command line arguments."""
        config = cls()
        
        # Load from file if specified
        if hasattr(args, 'config') and args.config:
            config = cls.load_from_file(args.config)
        
        # Override with command line arguments
        if hasattr(args, 'output') and args.output:
            config.output.output_dir = args.output
        
        if hasattr(args, 'mode') and args.mode:
            config.dfg.mode = args.mode
        
        if hasattr(args, 'detect') and args.detect:
            config.detection.enabled = True
        
        if hasattr(args, 'concurrency') and args.concurrency:
            config.detection.concurrency_limit = args.concurrency
        
        if hasattr(args, 'verbose') and args.verbose:
            config.verbose = True
        
        # Load LLM config from args
        if hasattr(args, 'api_key') and args.api_key:
            config.detection.provider.api_key = args.api_key
        
        if hasattr(args, 'base_url') and args.base_url:
            config.detection.provider.base_url = args.base_url
        
        if hasattr(args, 'model') and args.model:
            config.detection.provider.model = args.model
        
        if hasattr(args, 'llm_provider') and args.llm_provider:
            config.detection.provider.name = args.llm_provider
        
        # Load from environment if not set
        config.detection.provider.load_from_env()
        
        return config
    
    def save_to_file(self, config_path: str):
        """Save configuration to JSON file."""
        Path(config_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(asdict(self), f, indent=2)
    
    def __repr__(self) -> str:
        return f"PipelineConfig(solidity_version={self.solidity_version}, dfg_mode={self.dfg.mode}, detection_enabled={self.detection.enabled})"
