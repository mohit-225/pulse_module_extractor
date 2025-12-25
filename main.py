import requests
from bs4 import BeautifulSoup
import json
import argparse
from datetime import datetime


def fetch_page(url):
    """Fetch HTML content from a given URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"[ERROR] Failed to fetch URL: {e}")
        return None


def clean_text(text):
    """Clean and normalize extracted text."""
    if not text:
        return ""
    return " ".join(text.strip().split())


def is_valid_heading(text):
    """Filter out weak or meaningless headings."""
    return text and len(text) > 10


def extract_modules(html):
    soup = BeautifulSoup(html, "lxml")

    # Remove irrelevant sections
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    modules = []
    seen_modules = set()
    current_module = None

    for tag in soup.find_all(["h1", "h2", "h3", "p"]):
        text = clean_text(tag.get_text())

        if not text:
            continue

        # Detect module
        if tag.name == "h1" and is_valid_heading(text):
            key = text.lower()
            if key not in seen_modules:
                current_module = {
                    "module": text,
                    "submodules": {}
                }
                modules.append(current_module)
                seen_modules.add(key)

        # Detect submodules
        elif tag.name in ["h2", "h3"] and current_module:
            current_module["submodules"][text] = ""

        # Append description
        elif tag.name == "p" and current_module:
            if current_module["submodules"]:
                last_key = list(current_module["submodules"].keys())[-1]
                current_module["submodules"][last_key] += " " + text
            else:
                current_module.setdefault("description", "")
                current_module["description"] += " " + text

    return modules


def save_output(data, source_url, filename="output.json"):
    final_output = {
        "source_url": source_url,
        "generated_at": datetime.utcnow().isoformat(),
        "modules": data
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=4, ensure_ascii=False)

    print(f"\n✅ Output saved to {filename}")


def main():
    parser = argparse.ArgumentParser(description="Documentation Module Extractor")
    parser.add_argument(
        "--url",
        type=str,
        required=True,
        help="Documentation URL to extract modules from"
    )

    args = parser.parse_args()

    print(f"\nFetching content from: {args.url}")
    html = fetch_page(args.url)

    if not html:
        print("Failed to fetch page.")
        return

    modules = extract_modules(html)

    if not modules:
        print("No modules extracted.")
        return

    save_output(modules, args.url)
    print(f"✅ Extraction complete! Modules found: {len(modules)}")


if __name__ == "__main__":
    main()
