# BC-ResNet Upstream Attribution

Baseline family: BC-ResNet / Broadcasted Residual Learning for Efficient
Keyword Spotting.

Primary source:

- Paper: "Broadcasted Residual Learning for Efficient Keyword Spotting",
  Interspeech 2021.
- Official repository: https://github.com/Qualcomm-AI-research/bcresnet
- Repository license at planning time: BSD-3-Clause-Clear.

Local integration policy:

- No upstream source files are vendored in this scaffold.
- `model.py` is a project-local minimal Keras implementation intended for
  same-split Drone baseline training.
- If future work copies any upstream code, preserve the upstream license, source
  URL, source commit, and local modification notes in this file.
