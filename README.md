# place-discovery

Codex skill for discovering city places with real local function: industry spaces, training and research spaces, infrastructure landscapes, city systems, and low-commercial exploration nodes.

## Contents

- `SKILL.md`: skill instructions and output rules.
- `scripts/amap_client.py`: AMap Web Service helper. It reads `AMAP_API_KEY` from the environment, or a local `.amap_api_key` file that is intentionally ignored by Git.
- `references/place_taxonomy.json`: categories, keywords, exclusions, and score weights.
- `agents/openai.yaml`: skill display metadata.

## Notes

Do not commit API keys. Put a local key in `.amap_api_key` or export `AMAP_API_KEY` before using the AMap helper.

