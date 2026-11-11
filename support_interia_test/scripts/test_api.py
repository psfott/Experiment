"""Send one tiny request to a model in models.local.json."""
import argparse
import json
import os
from pathlib import Path
import urllib.error
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", help="Model alias; defaults to the first enabled model")
    args = parser.parse_args()
    config = Path(__file__).resolve().parents[1] / "models.local.json"
    models = json.loads(config.read_text(encoding="utf-8"))["models"]
    model = next((m for m in models if m.get("enabled", True) and
                  (not args.model or m["alias"] == args.model)), None)
    if model is None:
        parser.error("No enabled model matches --model")
    source = next((m for m in models if m["alias"] == model.get("api_key_from")), None) if model.get("api_key_from") else model
    key = (source.get("api_key") or os.getenv(source.get("api_key_env") or "")) if source else None
    if not key or "YOUR_" in model["model_id"] or "YOUR_" in model["base_url"]:
        parser.error("Set a real api_key, model_id, and base_url in models.local.json")
    body = {"model": model["model_id"],
            "messages": [{"role": "user", "content": "Reply with OK only."}],
            "max_tokens": 256}
    request = urllib.request.Request(
        model["base_url"].rstrip("/") + "/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": "Bearer " + key,
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.load(response)
        content = result["choices"][0]["message"].get("content")
        if not isinstance(content, str) or not content.strip():
            parser.exit(1, f"API responded [{model['alias']}] but returned no visible text\n")
        print(f"API OK [{model['alias']}]: {content}")
    except urllib.error.HTTPError as exc:
        parser.exit(1, f"API failed [{model['alias']}]: HTTP {exc.code}\n")
    except urllib.error.URLError:
        parser.exit(1, f"API failed [{model['alias']}]: connection error\n")


if __name__ == "__main__":
    main()
