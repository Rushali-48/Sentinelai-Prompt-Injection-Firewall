from detector.detector import PromptInjectionDetector
from context_analyzer.analyzer import analyze_content
from sanitizer.sanitizer import remove_malicious_spans
from validator.validator import ContentValidator
from audit.audit_logger import AuditLogger

BLOCK_MESSAGE = (
    "Request blocked. The submitted content contains instructions "
    "that could interfere with the AI's intended behavior or request "
    "protected information. The content was not forwarded to the "
    "downstream AI. Please submit a legitimate request."
)


class SentinelAIFirewall:
    """
    The Firewall Engine orchestrates the detection and contextual analysis layers and applies the
    final security policy before content reaches the downstream AI
    """

    def __init__(self):

        # load finetune model
        self.detector = PromptInjectionDetector()
        self.validator = ContentValidator()
        self.audit_logger = AuditLogger()

    def process(self, firewall_input):

        # input from fastapi
        content = firewall_input["content"]
        sources = firewall_input["sources"]

        # step - 1 screening using finetuned model
        detector_result = self.detector.predict(content)

        # case - 1 if model says benign
        if not detector_result["is_malicious"]:
            firewall_result = {
                "decision": "ALLOW",
                "original_content": content,
                "detector": detector_result,
                "context_analysis": None,
                "sanitized_content": content,
                "validator": None,
                "sources": sources,
                "block_message": None,
            }

            # Audit every request, including benign requests
            self.audit_logger.log_event(firewall_result)

            return firewall_result

        # step - 2 context analyzer
        context_result = analyze_content(content)

        # step - 3 sanitization

        sanitized_content = remove_malicious_spans(
            content=content, malicious_span=(context_result.malicious_span)
        )

        # check is there any legitimate content remains
        if not sanitized_content.strip():
            decision = "BLOCK"

            validator_result = self.validator.validate(
                original_content=content,
                sanitized_content=sanitized_content,
                malicious_spans=context_result.malicious_span,
                decision=decision,
            )

            firewall_result = {
                "decision": decision,
                "original_content": content,
                "detector": detector_result,
                "context_analysis": {
                    "attack_types": context_result.attack_types,
                    "malicious_spans": context_result.malicious_span,
                    "risk_level": context_result.risk_level,
                    "reason": context_result.reason,
                },
                "sanitized_content": None,
                "validator": validator_result,
                "sources": sources,
                "block_message": BLOCK_MESSAGE,
            }

            self.audit_logger.log_event(firewall_result)

            return firewall_result

        # legitimate content remains

        decision = "SANITIZE"

        # step- 4 validator

        validator_result = self.validator.validate(
            original_content=content,
            sanitized_content=sanitized_content,
            malicious_spans=context_result.malicious_span,
            decision=decision,
        )

        # validation failure -> block
        if not validator_result["is_valid"]:
            firewall_result = {
                "decision": "BLOCK",
                "original_content": content,
                "detector": detector_result,
                "context_analysis": {
                    "attack_types": context_result.attack_types,
                    "malicious_spans": context_result.malicious_span,
                    "risk_level": context_result.risk_level,
                    "reason": context_result.reason,
                },
                "sanitized_content": None,
                "validator": validator_result,
                "sources": sources,
                "block_message": BLOCK_MESSAGE,
            }

            self.audit_logger.log_event(firewall_result)

            return firewall_result

        # step - 5 final security result

        firewall_result = {
            "decision": "SANITIZE",
            "original_content": content,
            "detector": detector_result,
            "context_analysis": {
                "attack_types": context_result.attack_types,
                "malicious_spans": context_result.malicious_span,
                "risk_level": context_result.risk_level,
                "reason": context_result.reason,
            },
            "sanitized_content": sanitized_content,
            "validator": validator_result,
            "sources": sources,
            "block_message": None,
        }

        # step -6 Audit logging

        self.audit_logger.log_event(firewall_result)

        return firewall_result
