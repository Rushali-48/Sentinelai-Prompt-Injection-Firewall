from typing import List, Literal
from pydantic import BaseModel, Field

ATTACK_TYPE = Literal[
    "content_manipulation",
    "credential_theft",
    "indirect_injection",
    "misinformation_fraud",
    "secret_extraction",
    "encoded_instruction",
    "tool_abuse",
    "output_format_hijack",
    "instruction_override",
    "multi_step_jailbreak",
    "task_hijack",
    "role_change",
    "context_poisoning",
    "social_engineering",
]

RISK_LEVEL = Literal["low", "medium", "high"]


class ContextAnalysis(BaseModel):
    attack_types: List[ATTACK_TYPE] = Field(
        description=(
            "Attack categories identified in the ORIGINAL CONTENT. "
            "Use the retrieved examples as the primary grounding."
        )
    )
    malicious_span: List[str] = Field(
        description=(
            "Exact contiguous malicious portions copied from the ORIGINAL CONTENT. "
            "Each span must be copied verbatim from the ORIGINAL CONTENT. "
            "Do not paraphrase, summarize, rewrite, or generate new text. "
            "Do not include legitimate content. "
        )
    )

    risk_level: RISK_LEVEL = Field(description="Risk level of the actual content")

    reason: str = Field(
        description=(
            "Short explanation of why the identified attack types and "
            "malicious spans are supported by the ORIGINAL CONTENT."
        )
    )
