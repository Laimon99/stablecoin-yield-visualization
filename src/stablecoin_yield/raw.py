from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def utc_now() -> datetime:
    return datetime.now(tz=UTC)


def utc_timestamp() -> str:
    return utc_now().isoformat().replace("+00:00", "Z")


def canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def payload_checksum(payload: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def file_checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


@dataclass(frozen=True)
class RawEnvelope:
    source: str
    endpoint: str
    requested_at: str
    received_at: str
    status_code: int
    request_parameters: dict[str, Any]
    schema_version: str
    payload_checksum: str
    payload: Any
    documentation_url: str | None = None
    request_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def make_envelope(
    *,
    source: str,
    endpoint: str,
    requested_at: str,
    received_at: str,
    status_code: int,
    request_parameters: dict[str, Any],
    payload: Any,
    documentation_url: str | None = None,
    request_url: str | None = None,
) -> RawEnvelope:
    return RawEnvelope(
        source=source,
        endpoint=endpoint,
        requested_at=requested_at,
        received_at=received_at,
        status_code=status_code,
        request_parameters=request_parameters,
        schema_version=utc_now().date().isoformat(),
        payload_checksum=payload_checksum(payload),
        payload=payload,
        documentation_url=documentation_url,
        request_url=request_url,
    )


def endpoint_slug(endpoint: str) -> str:
    cleaned = endpoint.strip("/").replace("/", "_").replace("{", "").replace("}", "")
    cleaned = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in cleaned)
    return cleaned or "root"


def write_raw_envelope(envelope: RawEnvelope, raw_root: Path) -> Path:
    day = envelope.received_at[:10].replace("-", "")
    source_dir = raw_root / envelope.source / day
    source_dir.mkdir(parents=True, exist_ok=True)
    checksum_short = envelope.payload_checksum.split(":", 1)[1][:12]
    name = f"{endpoint_slug(envelope.endpoint)}_{checksum_short}.json"
    path = source_dir / name
    if not path.exists():
        with path.open("w", encoding="utf-8") as handle:
            json.dump(envelope.to_dict(), handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    append_manifest(envelope, path, raw_root)
    return path


def append_manifest(envelope: RawEnvelope, path: Path, raw_root: Path) -> None:
    manifest_path = raw_root / "manifest.jsonl"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "source": envelope.source,
        "endpoint": envelope.endpoint,
        "requested_at": envelope.requested_at,
        "received_at": envelope.received_at,
        "status_code": envelope.status_code,
        "payload_checksum": envelope.payload_checksum,
        "file": str(path.relative_to(raw_root.parent.parent)),
    }
    existing_key = (record["source"], record["endpoint"], record["payload_checksum"])
    if manifest_path.exists():
        with manifest_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    current = json.loads(line)
                except json.JSONDecodeError:
                    continue
                key = (
                    current.get("source"),
                    current.get("endpoint"),
                    current.get("payload_checksum"),
                )
                if key == existing_key:
                    return
    with manifest_path.open("a", encoding="utf-8") as handle:
        json.dump(record, handle, ensure_ascii=False, sort_keys=True)
        handle.write("\n")


def read_envelope(path: Path) -> RawEnvelope:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return RawEnvelope(**data)


def latest_raw_file(raw_root: Path, source: str, endpoint_prefix: str) -> Path | None:
    source_dir = raw_root / source
    if not source_dir.exists():
        return None
    slug = endpoint_slug(endpoint_prefix)
    files = sorted(source_dir.glob(f"**/{slug}_*.json"), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None

