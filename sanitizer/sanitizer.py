import re


def remove_malicious_spans(content: str, malicious_span: list[str]) -> str:
    """
    Remove malicious portions from the original content
    """
    sanitized_content = content

    for span in malicious_span:
        if not span:
            continue

        # exact match
        if span in sanitized_content:
            sanitized_content = sanitized_content.replace(span, " ")

        # Fallback: allow whitespace differences
        normalized_span = re.sub(r"\s+", " ", span).strip()
        pattern = re.escape(normalized_span)
        pattern = pattern.replace(r"\ ", r"\s+")

        match = re.search(pattern, sanitized_content, flags=re.IGNORECASE)

        if match:
            start, end = match.span()

            sanitized_content = (
                sanitized_content[:start] + " " + sanitized_content[end:]
            )

    # Clean excessive spaces
    sanitized_content = re.sub(r"[ \t]+", " ", sanitized_content)

    # Clean excessive blank lines
    sanitized_content = re.sub(r"\n\s*\n+", "\n\n", sanitized_content)

    return sanitized_content.strip()
