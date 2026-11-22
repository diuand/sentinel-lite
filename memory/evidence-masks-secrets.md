# Evidence files must not copy secrets around

**What happened:** the first `baseline-red.txt` was raw pytest output, and
the B-01 assertion printed the full (fake) key into a docs file. Gitleaks
would have flagged it, and with a real key that would be a second leak.

**Rule:** generate evidence with `scripts/evidence_red.sh`, which masks
`slk_*` values and temp paths. Never paste raw output that may contain
headers, tokens or keys.

**Check:** `grep -r "slk_live_FAKE" docs/` returns nothing.
