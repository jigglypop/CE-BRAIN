# A0 parser failure v1

Status: PRESERVED_FAILURE

Failed source SHA-256: `657fb5ce228747ccf8b89c908ccb697ff86c9ad55edf24572b67aeeb17e018b4`

No metadata receipt or trial manifest was promoted, and no `.eeg` signal value was opened.

Exact defect:

```python
channels[int(match.group(1))] = match.group(2).strip()
```

The parser accepted both `[Channel Infos]` and later `[Coordinates]` lines, so coordinate values overwrote the 64 channel names. The repaired source uses `setdefault` so the first channel declaration remains authoritative. No dataset identity, split, formula, threshold, or claim ceiling changed.

Observed terminal result:

```text
A0_SOURCE_PARSE_PASS
RuntimeError: header channel schema mismatch: sub-01/ses-02
```
