# Ranking policy

Normalize available signals to `[0, 1]`. Default weights are relevance `.30`, venue `.20`, citations `.15`, recency `.15`, reproducibility `.10`, author continuity `.05`, and novelty `.05`.

Renormalize over available signals instead of assigning missing signals zero. Emit `coverage`, the sum of available original weights. Prefer field- and year-normalized citations.

Emit all seven signal keys. Use `null` plus `missing_evidence` when a provider cannot support a dimension. Attach `signal_evidence` so a reviewer can distinguish measured values from proxies. Treat the built-in novelty value as a recency proxy requiring human review; do not present it as a semantic novelty measurement.

Bands: `must-read >= .80`, `recommended >= .65`, `candidate >= .50`, otherwise `watch`. A low-coverage record cannot be `must-read` without an explicit qualitative reason.
