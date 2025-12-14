## ADDED Requirements

### Requirement: GPU Device Support

The system SHALL automatically detect and use available GPU acceleration (CUDA, MPS) for model inference, falling back to CPU when no GPU is available.

#### Scenario: Auto-detect CUDA GPU
- **WHEN** LLaVADetector initializes on a system with NVIDIA GPU
- **THEN** model is loaded and moved to CUDA device

#### Scenario: Auto-detect MPS (Apple Silicon)
- **WHEN** LLaVADetector initializes on Apple Silicon Mac
- **THEN** model is loaded and moved to MPS device

#### Scenario: Fallback to CPU
- **WHEN** no GPU is available
- **THEN** model runs on CPU with warning logged about slow performance

#### Scenario: Device logged at startup
- **WHEN** detector initializes
- **THEN** selected device is logged at INFO level

### Requirement: Configurable Device Override

The system SHALL allow users to override automatic device detection via configuration.

#### Scenario: Manual device selection
- **WHEN** detector config includes `device: "cpu"` (or "cuda", "mps")
- **THEN** detector uses specified device instead of auto-detection

#### Scenario: Invalid device raises error
- **WHEN** config specifies unavailable device (e.g., "cuda" on Mac)
- **THEN** detector raises ValueError with available options

### Requirement: Inference Tensor Device Placement

The system SHALL move all inference inputs to the same device as the model before running inference.

#### Scenario: Inputs moved to GPU
- **WHEN** detect() prepares inputs for inference
- **THEN** input tensors are moved to model's device before generate()

#### Scenario: Outputs decoded on CPU
- **WHEN** model.generate() completes
- **THEN** outputs are decoded correctly regardless of device

## MODIFIED Requirements

### Requirement: Resource Management

The system SHALL manage model memory efficiently across multiple frame analyses.

#### Scenario: Single model instance reuse
- **WHEN** detector analyzes multiple frames
- **THEN** same model instance is reused (not reloaded)

#### Scenario: Cleanup releases model
- **WHEN** detector.cleanup() is called
- **THEN** model is unloaded from memory, allowing garbage collection

#### Scenario: Out-of-memory handling
- **WHEN** inference raises RuntimeError due to OOM
- **THEN** error is caught, logged, and empty results returned

#### Scenario: GPU memory released on cleanup
- **WHEN** detector.cleanup() is called with model on GPU
- **THEN** model is moved to CPU before dereferencing to release GPU memory
