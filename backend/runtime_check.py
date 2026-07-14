"""Runtime import and provider smoke-check script.

This script is intended to be run inside the production Docker image to
validate that all runtime dependencies and key provider classes can be
imported without raising exceptions. It intentionally avoids making live
network calls to external providers.
"""
import json
import sys

results = {"imports": {}, "providers": {}}

def try_import(name):
    try:
        __import__(name)
        results["imports"][name] = "ok"
    except Exception as e:
        results["imports"][name] = f"error: {type(e).__name__}: {e}"

modules = [
    "langgraph",
    "langchain_core",
    "openai",
    "google.generativeai",
    "httpx",
    "redis",
    "qdrant_client",
    "pydantic",
    "pydantic_settings",
]

for m in modules:
    try_import(m)

# Check internal provider classes
provider_paths = {
    "OpenAIProvider": "app.services.ai_gateway.openai_provider:OpenAIProvider",
    "GeminiProvider": "app.services.ai_gateway.gemini_provider:GeminiProvider",
    "ClaudeProvider": "app.services.ai_gateway.claude_provider:ClaudeProvider",
    "OllamaProvider": "app.services.ai_gateway.ollama_provider:OllamaProvider",
}

for key, path in provider_paths.items():
    mod_path, cls_name = path.split(":")
    try:
        mod = __import__(mod_path, fromlist=[cls_name])
        cls = getattr(mod, cls_name)
        # instantiate but do not call network methods
        try:
            inst = cls()
            results["providers"][key] = "instantiated"
        except Exception as e:
            results["providers"][key] = f"init-error: {type(e).__name__}: {e}"
    except Exception as e:
        results["providers"][key] = f"import-error: {type(e).__name__}: {e}"

print(json.dumps(results, indent=2))

sys.exit(0)
