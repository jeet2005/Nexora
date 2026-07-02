import re

LINK_PATTERNS = {
    "github": re.compile(r"^https?://(www\.)?github\.com/[A-Za-z0-9_-]+/?$"),
    "linkedin": re.compile(r"^https?://(www\.)?linkedin\.com/in/[A-Za-z0-9_-]+/?$"),
    "orcid": re.compile(r"^https?://(www\.)?orcid\.org/\d{4}-\d{4}-\d{4}-\d{3}[\dXx]$"),
    "portfolio": re.compile(r"^https?://[^\s/$.?#].[^\s]*$"),
}


def validate_link(platform: str, url: str) -> str | None:
    pattern = LINK_PATTERNS.get(platform)
    if not pattern:
        return f"Unknown platform: {platform}"
    if not pattern.match(url.strip()):
        return f"Invalid {platform} URL format"
    return None
