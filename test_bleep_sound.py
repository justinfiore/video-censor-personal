#!/usr/bin/env python3
"""Generate a sample audio file with bleep tones to preview the remediation sound."""

import numpy as np
import soundfile as sf

# Parameters
sample_rate = 48000  # 48kHz (common video sample rate)
bleep_frequency = 250  # Hz (deep lower tone)
bleep_amplitude = 0.2  # 0-1 range
silence_duration = 2.0  # seconds
bleep_duration = 1.0  # seconds

# Generate components
silence = np.zeros(int(sample_rate * silence_duration), dtype=np.float32)

# Bleep tone (sine wave)
t = np.arange(int(sample_rate * bleep_duration), dtype=np.float32) / sample_rate
bleep = bleep_amplitude * np.sin(2 * np.pi * bleep_frequency * t).astype(np.float32)

# Concatenate: silence - bleep - silence - bleep - silence
audio = np.concatenate([silence, bleep, silence, bleep, silence])

# Write to file
output_path = "/tmp/test_bleep.wav"
sf.write(output_path, audio, sample_rate)

print(f"Generated test audio: {output_path}")
print(f"  Duration: {len(audio) / sample_rate:.2f} seconds")
print(f"  Sample rate: {sample_rate} Hz")
print(f"  Bleep frequency: {bleep_frequency} Hz")
print(f"  Bleep amplitude: {bleep_amplitude}")
print(f"\nStructure: 2s silence | 1s bleep | 2s silence | 1s bleep | 2s silence")
