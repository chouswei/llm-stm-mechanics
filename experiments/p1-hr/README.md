# P1 human-reviewed stratum (n=200)

Sage **author-blind ACCEPT after regen** ([`../p1-blind/SAGE_SIGNOFF.md`](../p1-blind/SAGE_SIGNOFF.md)). Reviewer did not author the graphs.

- 17 topology families, checklist 200/200 (blind agreement 100%)
- Eight `asymmetric-spoke` graphs regenerated (hop-1 non-gold decoy)
- Same coefficient lock as synthetic P1 (a=1,b=1,c=0,d=10)
- Post-regen gold-presence: `memnet-llm` 0.19.4; n_both_perfect=170; mean Δ≈2930.59; 95% CI [2778.71, 3084.10]

```bash
.venv/bin/python experiments/p1-hr/run_p1_hr.py
```

Paper numbers live in [`REPORT.md`](REPORT.md) / [`results.summary.json`](results.summary.json). A live re-run must not silently overwrite the post-regen primary CI from a different package.
