"""Archive the official URLs listed in the source register, without overwriting evidence."""

import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import re
import subprocess
from datetime import datetime, timezone
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]


class PageText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.links = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden += 1
        if tag in {"p", "br", "tr", "h1", "h2", "li", "div"}:
            self.parts.append("\n")
        if tag == "a":
            self.links.extend(value for key, value in attrs if key == "href")

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.hidden = max(0, self.hidden - 1)
        if tag in {"td", "th"}:
            self.parts.append(" | ")

    def handle_data(self, value):
        if not self.hidden:
            self.parts.append(value)


def registry():
    records = {}
    for line in (ROOT / "docs/QUELLENUEBERSICHT.md").read_text().splitlines():
        if not line.startswith("| **"):
            continue
        municipality = re.search(r"\*\*(.*?)\*\*", line).group(1)
        for title, url in re.findall(r"\[([^\]]+)\]\((https?://[^)]+)\)", line):
            source_id = hashlib.sha256(url.encode()).hexdigest()[:12]
            records[source_id] = {"id": source_id, "municipality": municipality,
                                  "title": title, "url": url}
    return list(records.values())


def fetch(record):
    directory = ROOT / "data/sources" / record["id"]
    directory.mkdir(parents=True, exist_ok=True)
    metadata = directory / "metadata.json"
    if metadata.exists():
        return json.loads(metadata.read_text())
    output = directory / "response.bin"
    response = subprocess.run(
        ["curl", "-L", "--silent", "--show-error", "--max-time", "35",
         "--user-agent", "Kita-costs-map source research", "-o", str(output),
         "-w", "%{http_code}\n%{content_type}\n%{url_effective}", record["url"]],
        capture_output=True, text=True)
    fields = response.stdout.splitlines()
    item = dict(record, retrieved_at=datetime.now(timezone.utc).isoformat(),
                http_status=int(fields[0]) if fields and fields[0].isdigit() else 0,
                content_type=fields[1] if len(fields) > 1 else None,
                final_url=fields[2] if len(fields) > 2 else None,
                error=response.stderr.strip() or None)
    if output.exists():
        payload = output.read_bytes()
        is_pdf = payload.startswith(b"%PDF")
        target = directory / ("document.pdf" if is_pdf else "document.html")
        output.rename(target)
        item.update(local_path=str(target.relative_to(ROOT)),
                    sha256=hashlib.sha256(payload).hexdigest())
        if item["http_status"] == 200:
            if is_pdf:
                subprocess.run(["pdftotext", "-layout", str(target), str(directory / "text.txt")], check=True)
            else:
                parser = PageText()
                parser.feed(payload.decode("utf-8", errors="replace"))
                lines = [re.sub(r"[ \t]+", " ", value).strip() for value in "".join(parser.parts).splitlines()]
                (directory / "text.txt").write_text("\n".join(value for value in lines if value) + "\n")
                (directory / "links.json").write_text(json.dumps(parser.links, ensure_ascii=False, indent=2))
    metadata.write_text(json.dumps(item, ensure_ascii=False, indent=2) + "\n")
    print(f"{item['http_status']} {item['municipality']}: {item['title']}", flush=True)
    return item


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", action="append", default=[])
    parser.add_argument("--municipality", default="additional")
    parser.add_argument("--refresh", action="store_true", help="Archive a new snapshot and retain existing evidence")
    args = parser.parse_args()
    records = registry() if not args.url else [
        {"id": hashlib.sha256(url.encode()).hexdigest()[:12], "municipality": args.municipality,
         "title": "Additional official source", "url": url} for url in args.url]
    if args.refresh:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        records = [dict(record, id=record["id"] + "_" + stamp) for record in records]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(fetch, records))
    manifest = [json.loads(path.read_text()) for path in sorted((ROOT / "data/sources").glob("*/metadata.json"))]
    (ROOT / "data/source_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
