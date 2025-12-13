# API Contracts: Model Auto-Download Implementation

## Purpose
This document defines interfaces and contracts between parallel workstreams to prevent merge conflicts and ensure compatibility.

**All streams must implement these contracts exactly.** Any deviations require approval from the integration owner before coding.

---

## Stream A → Stream B: Configuration Schema Contract

### Configuration Dataclass Structure
```python
# video_censor_personal/config.py (or existing config module)

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path

@dataclass
class ModelSource:
    """Represents a downloadable model source."""
    name: str                    # e.g., "llava-7b"
    url: str                     # Full HTTP URL
    checksum: str               # SHA256 hash (or other algorithm)
    size_bytes: int             # Expected file size in bytes
    algorithm: str = "sha256"   # Checksum algorithm (default SHA256)
    optional: bool = False      # If True, analysis proceeds if download fails

@dataclass
class ModelsConfig:
    """Model management configuration."""
    cache_dir: Optional[str]     # Custom cache dir; None = platform default
    sources: List[ModelSource]   # List of available models to download
    auto_download: bool = False  # Pre-configured auto-download (future feature)

# Merged into main Config dataclass:
@dataclass
class Config:
    # ... existing fields ...
    models: ModelsConfig
```

### YAML Schema
```yaml
models:
  cache_dir: null  # null = platform default; or "/custom/path"
  sources:
    - name: "llava-7b"
      url: "https://huggingface.co/models/..."
      checksum: "abc123..."
      size_bytes: 13000000000
      algorithm: "sha256"
      optional: false
    - name: "profanity-detector"
      url: "https://..."
      checksum: "def456..."
      size_bytes: 500000000
      optional: false
```

### Config Loading Interface
```python
def load_config(config_path: str) -> Config:
    """Load and validate configuration from YAML file."""
    # Must return Config with .models.cache_dir resolved to platform default if None
    # Must validate all ModelSource entries
    # Raise ConfigError if invalid
    pass
```

### Breaking Changes
- None. Stream B imports Config and reads `.models` field.
- Stream A must ensure `.models` is always present in Config (even if empty).

---

## Stream A + B → Stream C: ModelManager API Contract

### ModelManager Class Interface
```python
# video_censor_personal/model_manager.py

from pathlib import Path
from typing import List, Dict, Optional, Callable
from video_censor_personal.config import Config, ModelSource

class ModelDownloadError(Exception):
    """Raised on download failure after retries."""
    pass

class ModelChecksumError(ModelDownloadError):
    """Raised when checksum validation fails."""
    pass

class DiskSpaceError(ModelDownloadError):
    """Raised when insufficient disk space."""
    pass

class ModelManager:
    """Manages model verification and download."""
    
    def __init__(self, config: Config):
        """
        Initialize ModelManager with configuration.
        
        Args:
            config: Config object with models section
        
        Raises:
            ConfigError: If models config is invalid
        """
        self.config = config
        self.cache_dir: Path = self._resolve_cache_dir()
    
    def verify_models(
        self, 
        sources: Optional[List[ModelSource]] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> Dict[str, bool]:
        """
        Verify and download missing models.
        
        Args:
            sources: List of ModelSource to verify. If None, use config.models.sources
            progress_callback: Optional callback(model_name, bytes_downloaded, total_bytes)
        
        Returns:
            Dict mapping model name → True if verified/downloaded, False if optional and failed
        
        Raises:
            ModelDownloadError: If required model download fails
            DiskSpaceError: If insufficient disk space
        """
        pass
    
    def is_model_valid(self, model_name: str) -> bool:
        """
        Check if model exists in cache with valid checksum.
        
        Args:
            model_name: Name of model (matches ModelSource.name)
        
        Returns:
            True if model exists and checksum matches, False otherwise
        """
        pass
    
    def get_model_path(self, model_name: str) -> Path:
        """
        Get cached path for a model.
        
        Args:
            model_name: Name of model
        
        Returns:
            Path to model file (may not exist)
        """
        pass
    
    def _resolve_cache_dir(self) -> Path:
        """Resolve cache directory from config or platform defaults."""
        # Uses platformdirs library
        pass
    
    def _download_model(self, source: ModelSource) -> Path:
        """Download a single model with retries and progress reporting."""
        # Atomic: downloads to temp file, validates checksum, moves to cache
        pass
    
    def _validate_checksum(self, file_path: Path, source: ModelSource) -> bool:
        """Validate file checksum against source."""
        pass
```

### Expected Behavior
- `verify_models()` is idempotent: calling twice skips already-valid models
- Progress callback fires regularly during downloads (Stream C will use for tqdm)
- Optional models (optional=true) don't raise errors; return False in dict
- Platform-appropriate cache dirs via `platformdirs`
- Temp downloads use `.tmp` suffix or similar; cleaned up on failure

### Breaking Changes
- None. Stream C receives ModelManager instance from main() CLI handler.

---

## Stream A + B + C → Stream D: Testing Contracts

### Test Structure
```
tests/
├── unit/
│   ├── test_config.py           # Stream A validates schema
│   ├── test_model_manager.py    # Stream B validates ModelManager
│   ├── test_cli.py              # Stream C validates CLI flag
│   └── test_huggingface_registry.py  # Stream F validates HF registry
├── integration/
│   ├── test_download_flow.py    # A+B+C: end-to-end download
│   ├── test_pipeline_integration.py  # E: pipeline + download
│   └── test_hf_discovery.py     # F: registry discovery
└── fixtures/
    ├── mock_models/             # Small test model files
    ├── test_config.yaml         # Test configuration
    └── mock_http_server.py      # Mock Hugging Face API
```

### Mock HTTP Server Interface
```python
# tests/fixtures/mock_http_server.py

from http.server import HTTPServer
from typing import Dict, Tuple

class MockHuggingFaceServer:
    """Mock Hugging Face HTTP server for testing."""
    
    def __init__(self, models: Dict[str, bytes]):
        """
        Args:
            models: Dict mapping model name → file content (bytes)
        """
        pass
    
    def start(self) -> Tuple[str, int]:
        """Start server, return (host, port)."""
        pass
    
    def stop(self):
        """Stop server."""
        pass
    
    def get_model_url(self, model_name: str) -> str:
        """Get download URL for a model."""
        pass
```

### Test Requirements
- Unit tests must be isolated (no network calls)
- Integration tests use mock HTTP server
- Fixtures include small (1MB) test models
- Cross-platform path tests for Windows, macOS, Linux
- Concurrent download tests (if Stream F implements async)

### Breaking Changes
- None. Tests are internal to project; no API changes.

---

## Stream B + C → Stream E: Pipeline Integration Contract

### AnalysisPipeline Changes
```python
# video_censor_personal/analysis_pipeline.py (or similar)

from video_censor_personal.config import Config
from video_censor_personal.model_manager import ModelManager
from typing import Optional

class AnalysisPipeline:
    """Main video analysis pipeline."""
    
    def __init__(
        self, 
        config: Config,
        skip_model_check: bool = False  # For backward compatibility
    ):
        """
        Initialize pipeline.
        
        Args:
            config: Configuration with models section
            skip_model_check: If True, skip model verification (legacy behavior)
        """
        self.config = config
        self._model_manager: Optional[ModelManager] = None
        self._models_verified = False
    
    def verify_models(self, download: bool = False) -> bool:
        """
        Verify required models are available.
        
        Args:
            download: If True, auto-download missing models
        
        Returns:
            True if all required models verified, False if optional models missing
        
        Raises:
            ModelDownloadError: If required model unavailable and download=False
        """
        if self._models_verified:
            return True
        
        self._model_manager = ModelManager(self.config)
        
        if download:
            # Auto-download missing models
            result = self._model_manager.verify_models()
            self._models_verified = all(result.values())
        else:
            # Just check existence
            self._models_verified = all(
                self._model_manager.is_model_valid(source.name)
                for source in self.config.models.sources
            )
        
        return self._models_verified
    
    def analyze(self) -> Dict[str, Any]:
        """
        Run full analysis pipeline.
        
        Raises:
            RuntimeError: If models not verified before calling analyze()
        """
        if not self._models_verified:
            raise RuntimeError("Call verify_models() before analyze()")
        
        # ... existing analysis logic ...
        pass
```

### CLI Integration (Stream C ↔ Stream E)
```python
# video_censor_personal/__main__.py or similar

def main():
    args = parse_args()  # Includes --download-models flag from Stream C
    config = load_config(args.config)
    
    pipeline = AnalysisPipeline(config)
    
    # Stream E: Auto-invoke if flag set
    pipeline.verify_models(download=args.download_models)
    
    # Proceed to analysis
    results = pipeline.analyze()
    output_results(results, args.output)
```

### Breaking Changes
- `AnalysisPipeline.__init__()` now requires `config` parameter (already required)
- `verify_models()` is new; old code skipping this continues to work (lazy init)

---

## Stream B → Stream F: HuggingFace Registry Contract

### HuggingFaceRegistry Class Interface
```python
# video_censor_personal/huggingface_registry.py (new module)

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
from pathlib import Path

@dataclass
class ModelMetadata:
    """Metadata for a Hugging Face model."""
    name: str                    # e.g., "llava-7b"
    versions: List[str]          # Available versions
    checksums: Dict[str, str]    # version → checksum
    sizes: Dict[str, int]        # version → size_bytes
    deprecated: bool = False
    replacement: Optional[str] = None  # Suggested replacement if deprecated
    last_updated: Optional[datetime] = None

class HuggingFaceRegistry:
    """Interact with Hugging Face model registry."""
    
    def __init__(self, cache_dir: Optional[Path] = None, ttl_hours: int = 24):
        """
        Initialize registry.
        
        Args:
            cache_dir: Where to cache metadata (default: temp or ~/.cache)
            ttl_hours: Metadata cache TTL in hours
        """
        self.cache_dir = cache_dir or Path.home() / ".cache" / "video-censor" / "hf-metadata"
        self.ttl_hours = ttl_hours
    
    def query_model(self, model_name: str, force_refresh: bool = False) -> ModelMetadata:
        """
        Query Hugging Face for model metadata.
        
        Args:
            model_name: Name of model on Hugging Face (e.g., "llava-7b")
            force_refresh: If True, bypass cache and fetch from API
        
        Returns:
            ModelMetadata with available versions and checksums
        
        Raises:
            ModelNotFoundError: If model not found on Hugging Face
            RegistryError: If API call fails
        """
        pass
    
    def get_cached_metadata(self, model_name: str) -> Optional[ModelMetadata]:
        """Get cached metadata if valid (not expired), else None."""
        pass
    
    def is_metadata_valid(self, model_name: str) -> bool:
        """Check if cached metadata is within TTL."""
        pass
    
    def _fetch_from_api(self, model_name: str) -> ModelMetadata:
        """Fetch from Hugging Face API (no caching)."""
        pass
    
    def _save_metadata(self, model_name: str, metadata: ModelMetadata):
        """Save metadata to cache with timestamp."""
        pass
```

### Integration with ModelManager (Stream F → B)
```python
# In ModelManager (Stream B)

from huggingface_registry import HuggingFaceRegistry

class ModelManager:
    def __init__(self, config: Config, registry: Optional[HuggingFaceRegistry] = None):
        self.registry = registry or HuggingFaceRegistry()
    
    def get_model_info(self, model_name: str) -> ModelMetadata:
        """Query registry for model info (used by Pipeline)."""
        return self.registry.query_model(model_name)
```

### Breaking Changes
- None. HuggingFaceRegistry is optional (ModelManager works without it).
- Pipeline can use registry for deprecation checks (Stream E).

---

## Integration Sequence & Approval Gates

### Gate 1: Stream A Complete
✅ Approval: Config schema is valid, example files realistic  
🔓 Unblocks: Stream B begins production (was using mocks)

### Gate 2: Stream B Complete
✅ Approval: ModelManager tests pass, API matches contract  
🔓 Unblocks: Stream C begins production; Stream D begins integration tests

### Gate 3: Stream C Complete
✅ Approval: CLI flag works, ModelManager called correctly  
🔓 Unblocks: Stream E begins production

### Gate 4: Stream E Complete
✅ Approval: Pipeline calls verify_models(), analysis resumes after download  
🔓 Unblocks: Stream F begins production

### Gate 5: Stream F Complete
✅ Approval: HuggingFaceRegistry works, deprecation warnings display  
🔓 Unblocks: Stream G finalizes documentation

---

## API Compatibility Checklist

**Before any merge, verify:**
- [ ] Config dataclass includes `.models` field
- [ ] ModelManager implements all methods in contract (exact signatures)
- [ ] CLI passes `--download-models` flag to pipeline.verify_models()
- [ ] AnalysisPipeline.verify_models() is idempotent
- [ ] HuggingFaceRegistry matches contract interface
- [ ] All tests pass (unit + integration for completed phases)
- [ ] No breaking changes to existing public APIs
- [ ] Type hints match contracts exactly
- [ ] Docstrings include Args, Returns, Raises sections
