#!/usr/bin/env python3
"""Small AMap Web Service client for the place-discovery skill."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


AMAP_API_KEY_ENV = "AMAP_API_KEY"
LOCAL_API_KEY_FILE = Path(__file__).resolve().parents[1] / ".amap_api_key"
BASE_URL = "https://restapi.amap.com"
DEFAULT_TIMEOUT_SECONDS = 12


def clean_value(value: Any) -> str:
    """Normalize AMap scalar fields that may arrive as lists, dicts, or empty arrays."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return " ".join(clean_value(item) for item in value if clean_value(item)).strip()
    return ""


def response_error(code: str, message: str, **extra: Any) -> dict[str, Any]:
    error = {"code": code, "message": message}
    error.update(extra)
    return {
        "ok": False,
        "error": error,
        "fallback": {
            "message": "AMap POI enrichment skipped. Continue with keyword planning and web-search evidence, but do not fabricate POI IDs."
        },
    }


def get_api_key() -> str | None:
    key = os.environ.get(AMAP_API_KEY_ENV, "").strip()
    if key:
        return key
    if LOCAL_API_KEY_FILE.exists():
        return LOCAL_API_KEY_FILE.read_text(encoding="utf-8").strip() or None
    return None


def request_json(path: str, params: dict[str, Any], *, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> dict[str, Any]:
    key = get_api_key()
    if not key:
        return response_error("missing_api_key", f"{AMAP_API_KEY_ENV} is not set")

    clean_params = {
        key_: value
        for key_, value in params.items()
        if value is not None and value != "" and value != []
    }
    clean_params["key"] = key
    clean_params.setdefault("output", "json")

    query = urllib.parse.urlencode(clean_params, doseq=True)
    url = f"{BASE_URL}{path}?{query}"
    request = urllib.request.Request(url, headers={"User-Agent": "place-discovery/1.0"})

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return response_error("http_error", f"HTTP {exc.code}", url_without_key=redact_key(url))
    except urllib.error.URLError as exc:
        return response_error("network_error", str(exc.reason), url_without_key=redact_key(url))
    except TimeoutError:
        return response_error("timeout", "AMap request timed out", url_without_key=redact_key(url))

    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        return response_error("invalid_json", str(exc), raw=payload[:500], url_without_key=redact_key(url))

    if str(data.get("status", "1")) != "1":
        return response_error(
            "amap_error",
            data.get("info") or "AMap returned an error",
            infocode=data.get("infocode", ""),
            url_without_key=redact_key(url),
            raw=data,
        )

    return {"ok": True, "raw": data, "url_without_key": redact_key(url)}


def redact_key(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    redacted = [(key, "***" if key == "key" else value) for key, value in pairs]
    return urllib.parse.urlunsplit(parsed._replace(query=urllib.parse.urlencode(redacted)))


def normalize_poi(poi: dict[str, Any]) -> dict[str, Any]:
    return {
        "poi_id": clean_value(poi.get("id")),
        "name": clean_value(poi.get("name")),
        "address": clean_value(poi.get("address")),
        "location": clean_value(poi.get("location")),
        "adcode": clean_value(poi.get("adcode")),
        "city": clean_value(poi.get("cityname")),
        "district": clean_value(poi.get("adname")),
        "type": clean_value(poi.get("type")),
        "raw": poi,
    }


def normalize_pois(raw: dict[str, Any]) -> list[dict[str, Any]]:
    pois = raw.get("pois") or []
    if isinstance(pois, dict):
        pois = [pois]
    return [normalize_poi(poi) for poi in pois if isinstance(poi, dict)]


def normalize_district(district: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": clean_value(district.get("name")),
        "adcode": clean_value(district.get("adcode")),
        "citycode": clean_value(district.get("citycode")),
        "level": clean_value(district.get("level")),
        "center": clean_value(district.get("center")),
        "polyline": clean_value(district.get("polyline")),
        "raw": district,
    }


def wrap(operation: str, raw_response: dict[str, Any], *, data: Any = None) -> dict[str, Any]:
    if not raw_response.get("ok"):
        raw_response["operation"] = operation
        return raw_response
    return {
        "ok": True,
        "operation": operation,
        "data": data,
        "raw": raw_response["raw"],
        "url_without_key": raw_response.get("url_without_key", ""),
    }


def district(args: argparse.Namespace) -> dict[str, Any]:
    raw = request_json(
        "/v3/config/district",
        {
            "keywords": args.keywords,
            "subdistrict": args.subdistrict,
            "extensions": args.extensions,
        },
    )
    if not raw.get("ok"):
        return wrap("district", raw)
    districts = raw["raw"].get("districts") or []
    return wrap("district", raw, data=[normalize_district(item) for item in districts])


def search(args: argparse.Namespace) -> dict[str, Any]:
    raw = request_json(
        "/v5/place/text",
        {
            "keywords": args.keywords,
            "region": args.city,
            "types": args.types,
            "city_limit": "true" if args.city_limit else "false",
            "page_size": args.limit,
            "page_num": args.page,
            "show_fields": args.show_fields,
        },
    )
    return wrap("search", raw, data=normalize_pois(raw.get("raw", {})) if raw.get("ok") else None)


def around(args: argparse.Namespace) -> dict[str, Any]:
    raw = request_json(
        "/v5/place/around",
        {
            "location": args.location,
            "radius": args.radius,
            "keywords": args.keywords,
            "types": args.types,
            "sortrule": args.sortrule,
            "page_size": args.limit,
            "page_num": args.page,
            "show_fields": args.show_fields,
        },
    )
    return wrap("around", raw, data=normalize_pois(raw.get("raw", {})) if raw.get("ok") else None)


def polygon(args: argparse.Namespace) -> dict[str, Any]:
    raw = request_json(
        "/v5/place/polygon",
        {
            "polygon": args.polygon,
            "keywords": args.keywords,
            "types": args.types,
            "page_size": args.limit,
            "page_num": args.page,
            "show_fields": args.show_fields,
        },
    )
    return wrap("polygon", raw, data=normalize_pois(raw.get("raw", {})) if raw.get("ok") else None)


def detail(args: argparse.Namespace) -> dict[str, Any]:
    raw = request_json(
        "/v5/place/detail",
        {
            "id": args.poi_id,
            "show_fields": args.show_fields,
        },
    )
    return wrap("detail", raw, data=normalize_pois(raw.get("raw", {})) if raw.get("ok") else None)


def geocode(args: argparse.Namespace) -> dict[str, Any]:
    raw = request_json(
        "/v3/geocode/geo",
        {
            "address": args.address,
            "city": args.city,
        },
    )
    if not raw.get("ok"):
        return wrap("geocode", raw)
    geocodes = raw["raw"].get("geocodes") or []
    data = [
        {
            "formatted_address": clean_value(item.get("formatted_address")),
            "country": clean_value(item.get("country")),
            "province": clean_value(item.get("province")),
            "city": clean_value(item.get("city")),
            "district": clean_value(item.get("district")),
            "adcode": clean_value(item.get("adcode")),
            "location": clean_value(item.get("location")),
            "level": clean_value(item.get("level")),
            "raw": item,
        }
        for item in geocodes
        if isinstance(item, dict)
    ]
    return wrap("geocode", raw, data=data)


def regeo(args: argparse.Namespace) -> dict[str, Any]:
    raw = request_json(
        "/v3/geocode/regeo",
        {
            "location": args.location,
            "radius": args.radius,
            "extensions": args.extensions,
            "roadlevel": args.roadlevel,
        },
    )
    if not raw.get("ok"):
        return wrap("regeo", raw)
    regeocode = raw["raw"].get("regeocode") or {}
    data = {
        "formatted_address": clean_value(regeocode.get("formatted_address")),
        "address_component": regeocode.get("addressComponent", {}),
        "pois": [normalize_poi(item) for item in regeocode.get("pois", []) if isinstance(item, dict)],
    }
    return wrap("regeo", raw, data=data)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AMap Web Service helper for place-discovery")
    subparsers = parser.add_subparsers(dest="command", required=True)

    district_parser = subparsers.add_parser("district", help="Administrative district lookup")
    district_parser.add_argument("keywords")
    district_parser.add_argument("--subdistrict", default="1")
    district_parser.add_argument("--extensions", choices=["base", "all"], default="base")
    district_parser.set_defaults(func=district)

    search_parser = subparsers.add_parser("search", help="Keyword POI search")
    search_parser.add_argument("keywords")
    search_parser.add_argument("--city", default="")
    search_parser.add_argument("--types", default="")
    search_parser.add_argument("--limit", default="20")
    search_parser.add_argument("--page", default="1")
    search_parser.add_argument("--city-limit", action="store_true")
    search_parser.add_argument("--show-fields", default="business,children")
    search_parser.set_defaults(func=search)

    around_parser = subparsers.add_parser("around", help="Around POI search")
    around_parser.add_argument("location", help="lng,lat")
    around_parser.add_argument("radius")
    around_parser.add_argument("keywords", nargs="?", default="")
    around_parser.add_argument("--types", default="")
    around_parser.add_argument("--limit", default="20")
    around_parser.add_argument("--page", default="1")
    around_parser.add_argument("--sortrule", choices=["distance", "weight"], default="weight")
    around_parser.add_argument("--show-fields", default="business,children")
    around_parser.set_defaults(func=around)

    polygon_parser = subparsers.add_parser("polygon", help="Polygon POI search")
    polygon_parser.add_argument("polygon", help="lng,lat|lng,lat|lng,lat")
    polygon_parser.add_argument("keywords", nargs="?", default="")
    polygon_parser.add_argument("--types", default="")
    polygon_parser.add_argument("--limit", default="20")
    polygon_parser.add_argument("--page", default="1")
    polygon_parser.add_argument("--show-fields", default="business,children")
    polygon_parser.set_defaults(func=polygon)

    detail_parser = subparsers.add_parser("detail", help="POI detail lookup by ID")
    detail_parser.add_argument("poi_id")
    detail_parser.add_argument("--show-fields", default="business,children")
    detail_parser.set_defaults(func=detail)

    geocode_parser = subparsers.add_parser("geocode", help="Geocode an address")
    geocode_parser.add_argument("address")
    geocode_parser.add_argument("--city", default="")
    geocode_parser.set_defaults(func=geocode)

    regeo_parser = subparsers.add_parser("regeo", help="Reverse geocode a coordinate")
    regeo_parser.add_argument("location", help="lng,lat")
    regeo_parser.add_argument("--radius", default="1000")
    regeo_parser.add_argument("--extensions", choices=["base", "all"], default="base")
    regeo_parser.add_argument("--roadlevel", default="0")
    regeo_parser.set_defaults(func=regeo)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = args.func(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("ok") or result.get("error", {}).get("code") == "missing_api_key":
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
