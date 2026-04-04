from __future__ import annotations

import base64
import json
import logging
import sys

from provider.config import Settings
from provider.engines import build_engine

log = logging.getLogger("ocr_provider_worker")
logging.basicConfig(level="INFO")


def _emit(payload: dict[str, object]) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def main() -> int:
    settings = Settings.from_env()
    try:
        engine = build_engine(settings, ocr_device_override="cuda")
    except Exception as exc:
        _emit({"status": "error", "error": repr(exc)})
        return 1

    _emit({"status": "ready", "device": engine.device_name, "model": engine.model_id})

    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue
        request = json.loads(line)
        op = str(request.get("op") or "")
        if op == "shutdown":
            _emit({"status": "ok"})
            return 0
        if op != "ocr_image":
            _emit({"status": "error", "error": f"unsupported op: {op}"})
            continue
        try:
            data = base64.b64decode(str(request["data_base64"]))
            result = engine.ocr_image(data)
        except Exception as exc:
            _emit({"status": "error", "error": repr(exc)})
            continue
        _emit(
            {
                "status": "ok",
                "text": result.text,
                "confidence": result.confidence,
                "warnings": result.warnings,
            }
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
