"""
Dataset loader for processing contracts from JSON datasets.
Supports various dataset formats including labeled contract collections.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .result import Result


@dataclass
class ContractEntry:
    """Represents a single contract entry from a dataset."""
    index: int
    code: str
    label: Any = None
    metadata: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], index: int) -> 'ContractEntry':
        """Create ContractEntry from dictionary."""
        return cls(
            index=index,
            code=data.get('code', ''),
            label=data.get('label'),
            metadata={k: v for k, v in data.items() if k not in ['code', 'label']}
        )


class DatasetLoader:
    """Loader for contract datasets."""
    
    @staticmethod
    def load_json_dataset(dataset_path: str) -> Result[List[ContractEntry]]:
        """
        Load contracts from a JSON dataset file.
        
        Supported formats:
        1. Array of objects with 'code' field:
           [{"code": "...", "label": 0}, ...]
        
        2. Object with 'contracts' array:
           {"contracts": [{"code": "...", "label": 0}, ...]}
        
        3. Object with 'data' array:
           {"data": [{"code": "...", "label": 0}, ...]}
        
        Args:
            dataset_path: Path to JSON dataset file
            
        Returns:
            Result containing list of ContractEntry objects
        """
        try:
            path = Path(dataset_path)
            
            if not path.exists():
                return Result.failure(f"Dataset file not found: {dataset_path}")
            
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different dataset formats
            contracts_data = None
            
            if isinstance(data, list):
                # Format 1: Direct array
                contracts_data = data
            elif isinstance(data, dict):
                # Format 2 or 3: Object with contracts/data array
                if 'contracts' in data:
                    contracts_data = data['contracts']
                elif 'data' in data:
                    contracts_data = data['data']
                else:
                    return Result.failure(
                        "Dataset must be an array or object with 'contracts' or 'data' field"
                    )
            else:
                return Result.failure("Invalid dataset format")
            
            # Parse contract entries
            entries = []
            for idx, item in enumerate(contracts_data):
                if not isinstance(item, dict):
                    return Result.failure(f"Invalid contract entry at index {idx}")
                
                if 'code' not in item:
                    return Result.failure(f"Missing 'code' field at index {idx}")
                
                entry = ContractEntry.from_dict(item, idx)
                entries.append(entry)
            
            if not entries:
                return Result.failure("Dataset contains no contracts")
            
            return Result.success(entries)
            
        except json.JSONDecodeError as e:
            return Result.failure(f"Invalid JSON format: {e}")
        except Exception as e:
            return Result.failure(f"Failed to load dataset: {e}")
    
    @staticmethod
    def load_directory(directory_path: str, extension: str = ".sol") -> Result[List[ContractEntry]]:
        """
        Load all contract files from a directory.
        
        Args:
            directory_path: Path to directory containing contract files
            extension: File extension to filter (default: .sol)
            
        Returns:
            Result containing list of ContractEntry objects
        """
        try:
            path = Path(directory_path)
            
            if not path.exists():
                return Result.failure(f"Directory not found: {directory_path}")
            
            if not path.is_dir():
                return Result.failure(f"Not a directory: {directory_path}")
            
            # Find all contract files
            contract_files = list(path.rglob(f"*{extension}"))
            
            if not contract_files:
                return Result.failure(f"No {extension} files found in {directory_path}")
            
            # Load each contract
            entries = []
            for idx, file_path in enumerate(sorted(contract_files)):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        code = f.read()
                    
                    entry = ContractEntry(
                        index=idx,
                        code=code,
                        metadata={'file_path': str(file_path), 'file_name': file_path.name}
                    )
                    entries.append(entry)
                    
                except Exception as e:
                    print(f"Warning: Failed to load {file_path}: {e}")
                    continue
            
            if not entries:
                return Result.failure("Failed to load any contracts from directory")
            
            return Result.success(entries)
            
        except Exception as e:
            return Result.failure(f"Failed to load directory: {e}")
    
    @staticmethod
    def validate_entry(entry: ContractEntry) -> Result[bool]:
        """Validate a contract entry."""
        if not entry.code or not entry.code.strip():
            return Result.failure("Contract code is empty")
        
        if len(entry.code) > 1_000_000:  # 1MB limit
            return Result.failure("Contract code exceeds size limit (1MB)")
        
        return Result.success(True)
