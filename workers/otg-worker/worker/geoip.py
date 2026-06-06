"""Optional GeoIP / ASN enrichment backed by MaxMind GeoLite2 databases.

GeoLite2 ``.mmdb`` files are licensed and cannot be redistributed, so this
enricher is *optional and self-disabling*: if the databases (or the ``geoip2``
library) are absent, :meth:`GeoIP.lookup` returns ``(None, None)`` and the
pipeline runs exactly as before. Point ``GEOIP_DB_DIR`` at a directory holding
``GeoLite2-Country.mmdb`` and ``GeoLite2-ASN.mmdb`` to turn it on.

Get the databases free from https://dev.maxmind.com/geoip/geolite2-free-geolocation-data
(account required) or via the ``geoipupdate`` tool.
"""

from __future__ import annotations

import ipaddress
import logging
from pathlib import Path

logger = logging.getLogger("otg.geoip")

COUNTRY_DB = "GeoLite2-Country.mmdb"
ASN_DB = "GeoLite2-ASN.mmdb"


class GeoIP:
    """Resolves an IP to (ISO country code, ``ASxxxx Org``).

    Readers are opened lazily and any failure degrades to a no-op so a missing
    or corrupt database never breaks ingestion.
    """

    def __init__(self, db_dir: str | None) -> None:
        self._country_reader = None
        self._asn_reader = None
        self.enabled = False
        if not db_dir:
            return
        self._open(Path(db_dir))

    def _open(self, db_dir: Path) -> None:
        try:
            import geoip2.database
        except ImportError:
            logger.info("geoip2 not installed; GeoIP enrichment disabled")
            return

        country_path = db_dir / COUNTRY_DB
        asn_path = db_dir / ASN_DB
        try:
            if country_path.exists():
                self._country_reader = geoip2.database.Reader(str(country_path))
            if asn_path.exists():
                self._asn_reader = geoip2.database.Reader(str(asn_path))
        except Exception as exc:  # noqa: BLE001 - never fail the pipeline
            logger.warning("Failed opening GeoIP databases in %s: %s", db_dir, exc)
            return

        self.enabled = bool(self._country_reader or self._asn_reader)
        if self.enabled:
            logger.info("GeoIP enrichment enabled (country=%s asn=%s)",
                        bool(self._country_reader), bool(self._asn_reader))

    @staticmethod
    def _is_public(ip: str) -> bool:
        try:
            return ipaddress.ip_address(ip).is_global
        except ValueError:
            return False

    def lookup(self, ip: str | None) -> tuple[str | None, str | None]:
        """Return ``(country_iso, asn)`` for a public IP, or ``(None, None)``."""
        if not self.enabled or not ip or not self._is_public(ip):
            return None, None

        country: str | None = None
        asn: str | None = None
        if self._country_reader is not None:
            try:
                country = self._country_reader.country(ip).country.iso_code
            except Exception:  # noqa: BLE001 - address not in db
                country = None
        if self._asn_reader is not None:
            try:
                resp = self._asn_reader.asn(ip)
                number = resp.autonomous_system_number
                org = resp.autonomous_system_organization or ""
                asn = f"AS{number} {org}".strip() if number else None
            except Exception:  # noqa: BLE001
                asn = None
        return country, asn
