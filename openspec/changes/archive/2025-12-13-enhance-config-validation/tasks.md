# Implementation Tasks

## 1. Validation Implementation

- [x] 1.1 Add helper function to validate detection category structure (enabled, sensitivity, model)
- [x] 1.2 Add helper function to validate sensitivity range (0.0-1.0)
- [x] 1.3 Add helper function to validate at least one detection enabled
- [x] 1.4 Add helper function to validate output format is "json"
- [x] 1.5 Add helper function to validate frame sampling strategy enum
- [x] 1.6 Add helper function to validate max_workers is positive integer
- [x] 1.7 Add helper function to validate merge_threshold is non-negative
- [x] 1.8 Integrate all validation helpers into validate_config() function

## 2. Testing

- [x] 2.1 Write tests for sensitivity value validation (edge cases: 0.0, 1.0, out of range)
- [x] 2.2 Write tests for detection category structure validation
- [x] 2.3 Write tests for "at least one detection enabled" constraint
- [x] 2.4 Write tests for output format validation ("json" allowed, others rejected)
- [x] 2.5 Write tests for frame sampling strategy enum validation
- [x] 2.6 Write tests for max_workers positive integer validation
- [x] 2.7 Write tests for merge_threshold non-negative validation
- [x] 2.8 Run full test suite and ensure 100% pass rate

## 3. Verification

- [x] 3.1 Test with video-censor.yaml.example to ensure it passes validation
- [x] 3.2 Verify error messages are clear and actionable (suggest valid values)
- [x] 3.3 Run pytest with coverage to ensure new code is covered
