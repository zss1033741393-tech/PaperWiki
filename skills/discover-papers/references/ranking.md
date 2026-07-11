# Ranking policy

Normalize available signals to `[0, 1]`. Default weights are relevance `.30`, venue `.20`, citations `.15`, recency `.15`, reproducibility `.10`, author continuity `.05`, and novelty `.05`.

Renormalize over available signals instead of assigning missing signals zero. Emit `coverage`, the sum of available original weights. Prefer field- and year-normalized citations.

Emit the renormalized value as `raw_score`, then confidence-adjust it as `score = raw_score * (0.5 + 0.5 * coverage)`. Rank and band by `score`. This prevents a paper supported only by relevance and recency from receiving the same final score as a paper with venue, citation, and reproducibility evidence.

Emit all seven signal keys. Use `null` plus `missing_evidence` when a provider cannot support a dimension. Attach `signal_evidence` so a reviewer can distinguish measured values from proxies. Use Hugging Face Daily Papers upvotes as the community-interest component of `novelty`, logarithmically normalized and explicitly labeled; never describe it as proof of academic quality or semantic novelty.

Bands: `must-read >= .80`, `recommended >= .65`, `candidate >= .50`, otherwise `watch`. A low-coverage record cannot be `must-read` without an explicit qualitative reason.
