import re


class ContentValidator:
    def __init__(self):
        pass

    def validate(
        self,
        original_content: str,
        sanitized_content: str,
        malicious_spans: list[str],
        decision: str,
    ) -> dict:

        # block
        if decision == "BLOCK":
            return {
                "is_valid": False,
                "validation_status": "BLOCKED",
                "reason": "Content was completely malicious and was blocked.",
            }

        # allow
        if decision == "ALLOW":
            return {
                "is_valid": True,
                "validation_status": "SAFE",
                "reason": "Content was classified as safe and no sanitization was required.",
            }

        # sanitized
        if decision == "SANITIZE":
            if not sanitized_content or not sanitized_content.strip():
                return {
                    "is_valid": False,
                    "validation_status": "REJECTED",
                    "reason": "Sanitization removed all content.",
                }
            # Check whether malicious spans still remain
            remaining_malicious_spans = []

            for span in malicious_spans:
                if not span:
                    continue

                pattern = re.escape(span)

                if re.search(pattern, sanitized_content, re.IGNORECASE):
                    remaining_malicious_spans.append(span)

            # Malicious content still exists
            if remaining_malicious_spans:
                return {
                    "is_valid": False,
                    "validation_status": "REJECTED",
                    "reason": "Malicious content remains after sanitization.",
                    "remaining_malicious_spans": remaining_malicious_spans,
                }
            # Sanitization successful
            return {
                "is_valid": True,
                "validation_status": "SAFE",
                "reason": "Malicious spans were removed successfully.",
                "remaining_malicious_spans": [],
            }

        # Unknown decision
        return {
            "is_valid": False,
            "validation_status": "REJECTED",
            "reason": f"Unknown security decision: {decision}",
        }
