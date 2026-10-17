import json
from collections import Counter
from pathlib import Path

path = Path("out/smoke-envelopes.jsonl")
rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

orgs = [str(r.get("organisation_number", "")) for r in rows]
record_states = Counter(r.get("state", "MISSING") for r in rows)
module_states = Counter()
evidence_statuses = Counter()
evidence_sources = Counter()
available_missing_url = []
profile_missing = []
evidence_total = 0

for r in rows:
    profile = r.get("profile") or {}
    if not profile:
        profile_missing.append(r.get("organisation_number"))

    modules = r.get("modules") or {}
    for name, info in modules.items():
        module_states[f"{name}:{(info or {}).get('state', 'MISSING')}"] += 1

    evidence = profile.get("evidence") or {}
    for field, item in evidence.items():
        evidence_total += 1
        item = item or {}
        status = item.get("status", "MISSING")
        evidence_statuses[f"{field}:{status}"] += 1

        url = item.get("source_url")
        if url:
            evidence_sources[url] += 1
        if status == "available" and not url:
            available_missing_url.append({
                "organisation_number": r.get("organisation_number"),
                "field": field
            })

report = json.loads(Path("out/smoke-report.json").read_text(encoding="utf-8"))
ops = report.get("operations") or {}

print("=== SMOKE OUTPUT AUDIT ===")
print("Records:", len(rows))
print("Unique organisation numbers:", len(set(orgs)))
print("Missing organisation numbers:", sum(not x for x in orgs))
print("Record states:", dict(record_states))
print("Missing profiles:", len(profile_missing))
print("Total profile evidence items:", evidence_total)
print("Evidence statuses by field:", json.dumps(evidence_statuses, ensure_ascii=False))
print("Module states:", json.dumps(module_states, ensure_ascii=False))
print("Available evidence missing source URL:", len(available_missing_url))
print("Distinct evidence source URLs:", len(evidence_sources))
print("Report operation fields:", list(ops.keys()))
print("Third-party cost field present:", "third_party_cost_usd" in ops)
print("Validation passed:", (report.get("validation") or {}).get("passed"))
if available_missing_url:
    print("Examples missing evidence URLs:", available_missing_url[:10])
if profile_missing:
    print("Examples missing profiles:", profile_missing[:10])
print("Top evidence URLs:")
for url, count in evidence_sources.most_common(10):
    print(count, url)
