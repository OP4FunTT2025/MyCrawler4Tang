# Repository Guidelines

## Project Structure & Module Organization
Top-level crawlers live in `CrawlSHT.py` (multi-page forum) and `CrawlOne.py` (single post). `app.py` hosts the Flask dashboard backed by templates in `templates/index.html`. Crawl output (magnet lists and downloaded images) lands in `data/`, grouped by timestamp and forum id, while `test_crawler.py` contains the regression tests.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate`: set up an isolated environment before installing requirements.
- `pip install requests beautifulsoup4 lxml flask`: install runtime dependencies.
- `python app.py`: launch the web UI at `http://127.0.0.1:5000` with live crawl controls.
- `python CrawlSHT.py --pages 5 --board 123 --save-images`: run the forum crawler headless; adjust flags to match target boards.
- `python CrawlOne.py <url> [--save-images --output-file magnet_links.txt]`: fetch one page when reproducing bugs.

## Coding Style & Naming Conventions
Follow PEP 8 with four-space indentation, descriptive snake_case names for functions, and UpperCamelCase only for classes or Flask Blueprints. Module-level constants (such as default headers) should be uppercase snake_case, and docstrings belong on public functions. Keep network helpers pure so they can be reused by CLI and web layers without side effects.

## Testing Guidelines
The project currently relies on `pytest`-style assertions inside `test_crawler.py`; run `python test_crawler.py` before uploading a branch. Name new tests `test_<feature>()`, keep fixtures near the top of the file, and add a failing test before fixing a bug. Focus on parsing edge cases, rate-limiting behavior, and file-write safety.

## Commit & Pull Request Guidelines
Existing history uses short imperative subjects like “Initial commit”; continue with present-tense summaries under 60 characters, optionally followed by a blank line and detail bullets. Each pull request should explain the motivation, outline manual and automated test results, and link to any tracked issue. Include screenshots or curl samples for Flask UI changes and list any configuration secrets the reviewer must supply.

## Security & Configuration Tips
Store forum cookies and API keys in environment variables or `.env` files excluded via `.gitignore`; never commit them. Respect crawl delays (e.g., `time.sleep(2)`) and keep concurrent requests modest to avoid throttling. Validate user-supplied URLs in Flask handlers to prevent server-side request forgery, and sanitize file names before writing to `data/`.
