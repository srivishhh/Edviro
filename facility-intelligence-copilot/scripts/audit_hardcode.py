import os
import re
import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SEARCH_PATTERNS = [
    "Math.random", "random.", "hardcoded", "damper_stuck", "coi_stuck", "oa_bias",
    "0.92", "85.0", "AHU-007", "efficiency", "resolved", "simulation",
    "predicted_state", "candidate_actions"
]

EXCLUDE_DIRS = {"node_modules", ".git", "venv", "__pycache__", "brain", ".gemini", "artifacts"}

results = []

for root, dirs, files in os.walk(PROJECT_ROOT):
    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
    for file in files:
        if file.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".json")):
            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, PROJECT_ROOT)
            is_test = any(x in rel_path.lower() for x in ["test", "scripts", "spec", "fixture"])
            
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                    for idx, line in enumerate(lines, 1):
                        for pattern in SEARCH_PATTERNS:
                            if pattern in line:
                                results.append({
                                    "file": rel_path.replace("\\", "/"),
                                    "line": idx,
                                    "pattern": pattern,
                                    "content": line.strip()[:120],
                                    "is_production": not is_test
                                })
            except Exception as e:
                pass

print(f"--- PHASE 1: FORENSIC CODEBASE AUDIT RESULTS ---")
print(f"Total Matches Found: {len(results)}")
print(f"Production Matches: {sum(1 for r in results if r['is_production'])}")
print(f"Test/Script Matches: {sum(1 for r in results if not r['is_production'])}\n")

print("Sample Production Matches:")
for r in [x for x in results if x['is_production']][:15]:
    print(f"  [{'PROD' if r['is_production'] else 'TEST'}] {r['file']}:{r['line']} -> {r['pattern']} | {r['content']}")

with open(os.path.join(PROJECT_ROOT, "audit_results.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
print(f"\nSaved full audit to audit_results.json")
