"""Official Spanish electricity data ingestion utilities.

The package intentionally has no third-party runtime dependencies.  Network
access is isolated in the small client classes so parsers and validators can
be used with offline fixtures in tests.
"""

from .omie import (
    OMIE_KIND_CONFIG,
    build_omie_url,
    download_omie,
    parse_omie,
    standardize_omie_rows,
)
from .ree import ESIOSClient, REDataClient, CredentialError
from .entsoe import BASE_URL as ENTSOE_BASE_URL, SPAIN_EIC, build_entsoe_url, download_entsoe, parse_entsoe_xml
standardize_redata_rows = REDataClient.standardize_rows

__all__ = [
    "OMIE_KIND_CONFIG", "build_omie_url", "download_omie", "parse_omie",
    "standardize_omie_rows", "standardize_redata_rows", "ESIOSClient", "REDataClient", "CredentialError", "ENTSOE_BASE_URL", "SPAIN_EIC", "build_entsoe_url", "download_entsoe", "parse_entsoe_xml",
]
