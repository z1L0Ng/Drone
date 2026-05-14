# DS-CNN Upstream Attribution

Baseline family: Depthwise Separable Convolutional Neural Network for keyword
spotting, commonly used in the "Hello Edge" / MCU keyword spotting line.

Primary source:

- Paper: "Hello Edge: Keyword Spotting on Microcontrollers", arXiv 1711.07128.
- Arm reference repository: https://github.com/ARM-software/ML-KWS-for-MCU
- Repository license at planning time: Apache-2.0.

Local integration policy:

- No upstream source files are vendored in this scaffold.
- `model.py` is a project-local minimal Keras DS-CNN-S-style implementation
  intended for same-split Drone baseline training.
- If future work copies any upstream code, preserve the upstream license, source
  URL, source commit, and local modification notes in this file.
