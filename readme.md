# MyCrawler4Tang

Forum magnet-link crawler with both CLI tools and a Flask dashboard. It scrapes thread pages, writes magnet links to files, and can optionally download post images. Intended for learning and research only.

## Features
- Multi-page forum crawl via `CrawlSHT.py`; single-thread crawl via `CrawlOne.py`
- Flask UI (`app.py`) to start/pause/resume/stop jobs, view progress, and download outputs
- Optional image downloads with separate image-cookie support and per-thread folders
- Configurable base URL, forum id, page range, delay, and cookies (env vars or form inputs)
- Outputs magnet lists, crawled URL lists, and image directories under `data/`
- Lightweight parser unit tests in `test_crawler.py` (no network required)

## Project layout
- `CrawlSHT.py` - multi-page CLI entry point
- `CrawlOne.py` - single-thread CLI entry point
- `crawler_core.py` - shared HTTP session, parsing, and image download helpers
- `app.py` and `templates/index.html` - Flask dashboard
- `data/` - runtime outputs (magnet files, URL files, images)
- `test_crawler.py` - parsing regression tests
- `AGENTS.md` - repository guidance
- `readme.md` - this file

## Requirements
- Python 3.8+
- Dependencies: `requests`, `beautifulsoup4`, `lxml`, `flask`

## Setup
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install requests beautifulsoup4 lxml flask
```

## CLI usage

### Crawl multiple forum pages
```bash
python CrawlSHT.py \
  --base-url https://btd5.thsf7.net \
  --forum-id 103 \
  --start-page 1 --end-page 5 \
  --cookie "cPNj_2132=..." \
  --save-images \
  --figures-dir data/figures \
  --delay 1.0
```
- Magnet links are written to `data/magnet_file_<timestamp>.txt` unless `--output` is provided.
- Images (when `--save-images`) land in `data/figures/forum_<id>_<timestamp>/`.
- `--delay` controls the per-page sleep (seconds).

### Crawl a single thread
```bash
python CrawlOne.py \
  https://btd5.thsf7.net/thread-3182886-1-1.html \
  --save-images \
  --output-file data/magnet_links.txt \
  --image-dir data/figures/custom \
  --cookie "cPNj_2132=..."
```
- Default base URL can be overridden with `--base-url` or `CRAWLER_BASE_URL`.
- If no output path is given, a timestamped file is created in `data/`.

## Flask dashboard
```bash
python app.py
# Open http://127.0.0.1:5000
```
- Configure base URL, forum id, page count, cookies, and image saving from the form.
- Controls: start, pause, resume, stop; view live progress, current URL, counts.
- Downloads: magnet file, crawled URL file, and (when enabled) image folder path shown.
- Keeps a short crawl history in the UI.

## Configuration
- `CRAWLER_COOKIE`: default Cookie header for forum requests.
- `CRAWLER_IMAGE_COOKIE`: optional Cookie header for image requests (falls back to `CRAWLER_COOKIE`).
- `CRAWLER_BASE_URL`: optional default base URL for single-thread CLI.
- Cookies can also be pasted directly into the CLI flags or Flask form.

## Outputs
- Magnet lists: `data/magnet_file_<timestamp>.txt`
- Crawled URLs: `data/url_file_<timestamp>.txt` (Flask flow)
- Images: `data/figures/...` organized per forum and per thread with sanitized names
- Timestamps use `YYYY_MM_DD_HH_MM_SS` for easy sorting.

## Testing
```bash
python test_crawler.py
```
Tests cover parser helpers and filename sanitization without hitting the network.

## Safety and etiquette
- For educational/research use only; respect the target site's terms and robots rules.
- Keep crawl delays reasonable to avoid throttling; defaults include a 1s sleep.
- Do not commit or share cookies or other secrets; load them via env vars or local input.
- Verify cookies are current if you see 302/403 responses.
