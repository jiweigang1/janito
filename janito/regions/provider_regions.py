"""
Static region definitions for LLM providers.

This module contains region mappings for major LLM providers with their
respective API endpoints and data center locations.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class RegionEndpoint:
    """Represents a provider's endpoint in a specific region."""

    region_code: str
    name: str
    endpoint: str
    location: str  # City, Country format
    priority: int = 1  # Lower = higher priority


# Region definitions for major LLM providers
PROVIDER_REGIONS: Dict[str, List[RegionEndpoint]] = {
    "openai": [
        RegionEndpoint(
            "US-EAST", "US East", "https://api.openai.com/v1", "Ashburn, US", 1
        ),
        RegionEndpoint(
            "US-WEST", "US West", "https://api.openai.com/v1", "San Jose, US", 2
        ),
        RegionEndpoint(
            "EU-CENTRAL", "EU Central", "https://api.openai.com/v1", "Frankfurt, DE", 3
        ),
        RegionEndpoint(
            "ASIA-PACIFIC",
            "Asia Pacific",
            "https://api.openai.com/v1",
            "Singapore, SG",
            4,
        ),
    ],
    "anthropic": [
        RegionEndpoint(
            "US-EAST", "US East", "https://api.anthropic.com", "Ashburn, US", 1
        ),
        RegionEndpoint(
            "US-WEST", "US West", "https://api.anthropic.com", "San Jose, US", 2
        ),
        RegionEndpoint(
            "EU-CENTRAL", "EU Central", "https://api.anthropic.com", "Frankfurt, DE", 3
        ),
    ],
    "google": [
        RegionEndpoint(
            "US-CENTRAL",
            "US Central",
            "https://generativelanguage.googleapis.com/v1beta",
            "Council Bluffs, US",
            1,
        ),
        RegionEndpoint(
            "US-EAST",
            "US East",
            "https://generativelanguage.googleapis.com/v1beta",
            "Moncks Corner, US",
            2,
        ),
        RegionEndpoint(
            "EU-WEST",
            "EU West",
            "https://generativelanguage.googleapis.com/v1beta",
            "St. Ghislain, BE",
            3,
        ),
        RegionEndpoint(
            "ASIA-EAST",
            "Asia East",
            "https://generativelanguage.googleapis.com/v1beta",
            "Tokyo, JP",
            4,
        ),
    ],
    "azure-openai": [
        RegionEndpoint(
            "US-EAST",
            "East US",
            "https://{resource}.openai.azure.com",
            "Virginia, US",
            1,
        ),
        RegionEndpoint(
            "US-WEST",
            "West US",
            "https://{resource}.openai.azure.com",
            "California, US",
            2,
        ),
        RegionEndpoint(
            "EU-WEST",
            "West Europe",
            "https://{resource}.openai.azure.com",
            "Netherlands, NL",
            3,
        ),
        RegionEndpoint(
            "EU-NORTH",
            "North Europe",
            "https://{resource}.openai.azure.com",
            "Ireland, IE",
            4,
        ),
    ],
    "alibaba": [
        RegionEndpoint(
            "CN-EAST",
            "China East",
            "https://dashscope.aliyuncs.com/api/v1",
            "Hangzhou, CN",
            1,
        ),
        RegionEndpoint(
            "CN-NORTH",
            "China North",
            "https://dashscope.aliyuncs.com/api/v1",
            "Beijing, CN",
            2,
        ),
        RegionEndpoint(
            "CN-SOUTH",
            "China South",
            "https://dashscope.aliyuncs.com/api/v1",
            "Shenzhen, CN",
            3,
        ),
    ],
    "moonshot": [
        RegionEndpoint(
            "CN-EAST", "China East", "https://api.moonshot.cn/v1", "Shanghai, CN", 1
        ),
        RegionEndpoint(
            "CN-NORTH", "China North", "https://api.moonshot.cn/v1", "Beijing, CN", 2
        ),
    ],
    "zai": [
        RegionEndpoint(
            "US-CENTRAL", "US Central", "https://api.zai.dev/v1", "Chicago, US", 1
        ),
        RegionEndpoint(
            "EU-CENTRAL", "EU Central", "https://api.zai.dev/v1", "Frankfurt, DE", 2
        ),
        RegionEndpoint(
            "ASIA-PACIFIC", "Asia Pacific", "https://api.zai.dev/v1", "Singapore, SG", 3
        ),
    ],
}

# Geographic region mappings
REGION_MAPPINGS = {
    "US": ["US-EAST", "US-WEST", "US-CENTRAL", "US-NORTH", "US-SOUTH"],
    "EU": ["EU-CENTRAL", "EU-WEST", "EU-NORTH", "EU-SOUTH", "EU-EAST"],
    "CN": ["CN-EAST", "CN-NORTH", "CN-SOUTH", "CN-WEST", "CN-CENTRAL"],
    "CH": ["CH-NORTH", "CH-SOUTH", "CH-EAST", "CH-WEST"],
    "ASIA": ["ASIA-EAST", "ASIA-PACIFIC", "ASIA-SOUTH", "ASIA-CENTRAL"],
    "GLOBAL": ["GLOBAL", "WORLDWIDE"],
}


def get_provider_regions(provider: str) -> List[RegionEndpoint]:
    """Get all regions for a specific provider."""
    return PROVIDER_REGIONS.get(provider.lower(), [])


def get_optimal_endpoint(provider: str, user_region: str = "US") -> Optional[str]:
    """
    Get the optimal endpoint for a provider based on user region.

    Args:
        provider: The provider name (e.g., 'openai', 'anthropic')
        user_region: User's geographic region (US, EU, CN, CH, ASIA)

    Returns:
        The optimal endpoint URL or None if provider not found
    """
    regions = get_provider_regions(provider)
    if not regions:
        return None

    # Map user region to provider regions
    preferred_region_codes = REGION_MAPPINGS.get(user_region.upper(), [])

    # Find the highest priority region that matches
    for region_code in preferred_region_codes:
        for region in regions:
            if region.region_code == region_code:
                return region.endpoint

    # Fallback to first available region
    return regions[0].endpoint if regions else None


def get_all_providers() -> List[str]:
    """Get list of all supported providers."""
    return list(PROVIDER_REGIONS.keys())
