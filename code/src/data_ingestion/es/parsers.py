"""Compatibility imports for parser functions."""

from .omie import normalize_omie_directory, parse_omie, standardize_omie_rows, write_standardized_csv
from .ree import REDataClient
from .entsoe import parse_entsoe_xml

standardize_redata_rows = REDataClient.standardize_rows

__all__ = ["parse_omie", "standardize_omie_rows", "normalize_omie_directory", "write_standardized_csv", "standardize_redata_rows", "parse_entsoe_xml"]
