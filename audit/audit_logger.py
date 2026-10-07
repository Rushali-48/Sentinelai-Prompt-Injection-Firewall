import json
from datetime import datetime
from pathlib import Path


class AuditLogger:
    def __init__(self, log_file="logs/sentinelai_audit.jsonl"):

        self.log_file = Path(log_file)

        # Create logs directory if it doesn't exist
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log_event(self, firewall_result: dict):

        context = firewall_result.get("context_analysis")
        validator = firewall_result.get("validator")

        # Create audit record
        audit_record = {
            "timestamp": datetime.now().isoformat(),
            "decision": firewall_result.get("decision"),
            "original_content": firewall_result.get("original_content"),
            "sanitized_content": firewall_result.get("sanitized_content"),
            "detector": {
                "benign_probability": (
                    firewall_result.get("detector", {}).get("benign_probability")
                ),
                "malicious_probability": (
                    firewall_result.get("detector", {}).get("malicious_probability")
                ),
                "threshold": (firewall_result.get("detector", {}).get("threshold")),
                "is_malicious": (
                    firewall_result.get("detector", {}).get("is_malicious")
                ),
            },
            "context_analysis": {
                "is_malicious": (context.get("is_malicious") if context else None),
                "attack_types": (context.get("attack_types") if context else []),
                "malicious_spans": (context.get("malicious_spans") if context else []),
                "legitimate_content": (
                    context.get("legitimate_content") if context else []
                ),
                "risk_level": (context.get("risk_level") if context else None),
                "reason": (context.get("reason") if context else None),
            },
            "validator": {
                "is_valid": (validator.get("is_valid") if validator else None),
                "validation_status": (
                    validator.get("validation_status") if validator else None
                ),
                "reason": (validator.get("reason") if validator else None),
            },
        }

        # Write one JSON object per line
        with open(self.log_file, "a", encoding="utf-8") as file:
            file.write(json.dumps(audit_record, ensure_ascii=False) + "\n")

        return audit_record
