import yaml
import sys
import os
from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field, field_validator, ValidationError

class Argument(BaseModel):
    required: bool
    type: str
    default: Any
    label: str
    description: str

    @field_validator('type')
    def validate_type(cls, v):
        allowed_types = {'int', 'float', 'bool', 'timeframe', 'ticker', 'venue'}
        if v not in allowed_types:
            raise ValueError(f"Type must be one of {allowed_types}")
        return v

class StrategySettings(BaseModel):
    market_mode: Optional[str] = Field(default="single")
    market_aliases: Optional[List[str]] = Field(default_factory=list)

    @field_validator('market_mode')
    def validate_market_mode(cls, v):
        allowed_modes = {'single', 'multi'}
        if v not in allowed_modes:
            raise ValueError(f"market_mode must be one of {allowed_modes}")
        return v

class StrategyVersion(BaseModel):
    class_: str = Field(alias="class")
    settings: Optional[StrategySettings] = None
    arguments: Dict[str, Argument]

class StrategyMetadata(BaseModel):
    id: str
    name: str
    description: str
    tags: List[str]
    entry_only: bool
    latest: str
    versions: Dict[str, StrategyVersion]

class RegistryFile(BaseModel):
    strategy: StrategyMetadata

class MainRegistryFile(BaseModel):
    includes: List[str]

def validate_yaml(file_path: str):
    """validates a single strategy registry.yaml file."""
    print(f"Validating {file_path}...")
    try:
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Pydantic validation
        registry = RegistryFile(**data)
        
        # Additional logic checks
        if registry.strategy.latest not in registry.strategy.versions:
            raise ValueError(f"Latest version '{registry.strategy.latest}' not found in versions list")

        print(f"✅ {file_path} is valid!")
        return True

    except ValidationError as e:
        print(f"❌ Validation Error in {file_path}:")
        for err in e.errors():
            loc = ".".join(str(l) for l in err['loc'])
            print(f"  - {loc}: {err['msg']}")
        return False
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return False
    except ValueError as e:
        print(f"❌ Logical Error in {file_path}: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error in {file_path}: {e}")
        return False

def validate_main_registry(file_path: str):
    """Validates the main registry.yaml file."""
    print(f"Validating main registry {file_path}...")
    try:
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        
        registry = MainRegistryFile(**data)
        
        # Check if included files exist
        base_dir = os.path.dirname(file_path)
        all_includes_valid = True
        
        for include_path in registry.includes:
            full_path = os.path.join(base_dir, include_path)
            if not os.path.isfile(full_path):
                print(f"❌ Include not found: {include_path}")
                all_includes_valid = False
        
        if all_includes_valid:
             print(f"✅ Main registry {file_path} is valid!")
             return True
        else:
             return False

    except ValidationError as e:
        print(f"❌ Validation Error in {file_path}:")
        for err in e.errors():
            loc = ".".join(str(l) for l in err['loc'])
            print(f"  - {loc}: {err['msg']}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error in {file_path}: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_registry.py <path_to_registry.yaml>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # If directory provided, scan for registry.yaml files
    if os.path.isdir(file_path):
        success = True
        
        # 1. Validate Main Registry if present
        # Check standard locations
        possible_main_paths = [
            os.path.join(file_path, "coinrule_x_strategies/registry.yaml"),
            os.path.join(file_path, "registry.yaml")
        ]
        
        main_registry_path = None
        for p in possible_main_paths:
            if os.path.exists(p) and "coinrule_x_strategies" in p: # Ensure we are targetting the package registry
                main_registry_path = os.path.abspath(p)
                break
        
        if main_registry_path:
             if not validate_main_registry(main_registry_path):
                 success = False

        # 2. Validate Strategy Registries
        for root, _, files in os.walk(file_path):
            if "registry.yaml" in files:
                full_path = os.path.abspath(os.path.join(root, "registry.yaml"))
                
                # Skip the main registry we just validated
                if main_registry_path and full_path == main_registry_path:
                    continue
                
                # Verify it is inside a 'strategies' folder
                # os.sep + 'strategies' + os.sep ensures we match /strategies/ folder name
                if os.sep + "strategies" + os.sep in full_path: 
                     if not validate_yaml(full_path):
                        success = False
        sys.exit(0 if success else 1)
    else:
        success = validate_yaml(file_path)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
