# Ranking policy

Normalize available signals to `[0, 1]`. Default weights are relevance `.30`, venue `.20`, citations `.15`, recency `.15`, reproducibility `.10`, author continuity `.05`, and novelty `.05`.

Renormalize over available signals instead of assigning missing signals zero. Emit `coverage`, the sum of available original weights. Prefer field- and year-normalized citations.

Bands: `must-read >= .80`, `recommended >= .65`, `candidate >= .50`, otherwise `watch`. A low-coverage record cannot be `must-read` without an explicit qualitative reason.

