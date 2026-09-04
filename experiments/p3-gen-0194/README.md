# P3 generation half — post-fix confirmation (`memnet-llm` 0.19.4)

Same protocol as [`../p3-gen/`](../p3-gen/): OpenRouter `openai/gpt-4o-mini` at $T=0$, RAW vs CANONICAL, $n_{\mathrm{sessions}}=8$, $n_{\mathrm{perms}}=15$, $M=12$, $k=2$.

This directory records the **honesty $c$ confirmation** after [MemNet PR #148](https://github.com/chouswei/MemNet/pull/148) (nickname `id` off `pin_map` emit), published as `memnet-llm` 0.19.4. It is not a new prediction and not a SemVer $a$ or $b$ claim.

Authoritative numbers: [`results.summary.json`](results.summary.json) / [`REPORT.md`](REPORT.md).

## Re-run (requires your key)

No keys are stored in this repo. Protocol harness is [`../p3-gen/run_p3_gen.py`](../p3-gen/run_p3_gen.py). Do not overwrite this directory's `results.summary.json` from a different model or package.

```bash
python3 -m venv .venv
.venv/bin/pip install "memnet-llm==0.19.4"
# or: .venv/bin/pip install "git+https://github.com/chouswei/MemNet.git@1242c467bc9052360b4d61d754e944cc7ddf6cd9"
export OPENROUTER_API_KEY=  # your key; never commit it
.venv/bin/python experiments/p3-gen/run_p3_gen.py
```
