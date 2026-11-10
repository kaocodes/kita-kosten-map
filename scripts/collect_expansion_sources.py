"""Archive the explicitly reviewed URLs in an expansion research register."""

import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path

from fetch_sources import ROOT, fetch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("register", type=Path)
    args = parser.parse_args()
    register = json.loads(args.register.read_text())
    records = {}
    for municipality in register["municipalities"]:
        for source in municipality["sources"]:
            source_id = hashlib.sha256(source["url"].encode()).hexdigest()[:12]
            source["source_id"] = source_id
            records[source_id] = {
                "id": source_id,
                "municipality": municipality["name"],
                "title": source["title"],
                "url": source["url"],
            }
    args.register.write_text(json.dumps(register, ensure_ascii=False, indent=2) + "\n")
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(fetch, records.values()))
    manifest_path = ROOT / "data/source_manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else []
    known_ids = {source["id"] for source in manifest}
    for path in sorted((ROOT / "data/sources").glob("*/metadata.json")):
        source = json.loads(path.read_text())
        if source["id"] not in known_ids:
            manifest.append(source)
            known_ids.add(source["id"])
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"sources": len(results), "http_ok": sum(item["http_status"] == 200 for item in results)}))


if __name__ == "__main__":
    main()
