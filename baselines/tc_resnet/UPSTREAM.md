# TC-ResNet Upstream Attribution

Baseline family: Temporal Convolution for Real-Time Keyword Spoting /
TC-ResNet.

Primary source:

- Paper: "Temporal Convolution for Real-Time Keyword Spotting on Mobile
  Devices", Interspeech 2019.
- Official repository: https://github.com/hyperconnect/TC-ResNet
- Repository license at planning time: Apache-2.0.

Dependency risk:

- The official repository declares TensorFlow 1.13.1-era dependencies. Directly
  depending on that repo would make the Track D server environment fragile.

Local integration policy:

- No upstream source files are vendored in this scaffold.
- `model.py` is a project-local minimal Keras/TF2 TCResNet8-style
  implementation intended for same-split Drone baseline training.
- If future work copies any upstream code, preserve the upstream license, source
  URL, source commit, and local modification notes in this file.
