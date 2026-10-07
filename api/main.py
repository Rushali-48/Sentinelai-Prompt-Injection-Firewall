from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from typing import Optional
import tempfile
import os

from input_processor.input_processor import InputProcessor
from firewall.firewall_engine import SentinelAIFirewall
from downstream_ai.downstream_ai import DownstreamAI


# ==========================================================
# FASTAPI APPLICATION
# ==========================================================

app = FastAPI(
    title="SentinelAI Prompt Injection Firewall",
    description="Agentic Prompt Injection Firewall API",
    version="1.0.0",
)


# ==========================================================
# INITIALIZE COMPONENTS
# ==========================================================

input_processor = InputProcessor()
firewall = SentinelAIFirewall()
downstream_ai = DownstreamAI()

# ==========================================================
# HEALTH CHECK
# ==========================================================


@app.get("/")
def root():

    return {"status": "running", "service": "SentinelAI Prompt Injection Firewall"}


@app.get("/health")
def health():

    return {"status": "healthy"}


# ==========================================================
# CHAT ENDPOINT
# ==========================================================


@app.post("/chat")
async def chat(
    content: Optional[str] = Form(None), file: Optional[UploadFile] = File(None)
):
    """
    Single backend entry point.
    """

    # ------------------------------------------------------
    # 1. validate that user provided
    # ------------------------------------------------------

    has_text = content is not None and content.strip() != ""
    has_file = file is not None

    if not has_text and not has_file:
        raise HTTPException(
            status_code=400, detail="Please enter a message or upload a file."
        )

    # ------------------------------------------------------
    # 2. input processing
    # ------------------------------------------------------

    processed_contents = []
    source_information = []

    # direct user text
    if has_text:
        text_result = input_processor.process_text(content)

        processed_contents.append(text_result["content"])

        source_information.append(
            {
                "source_type": text_result["source_type"],
                "source_name": text_result["source_name"],
                "metadata": text_result["metadata"],
            }
        )

    # uploaded file
    if has_file:
        temp_file_path = None

        try:
            # Save uploaded file temporarily
            suffix = os.path.splitext(file.filename)[1]

            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file_path = temp_file.name

                file_bytes = await file.read()

                temp_file.write(file_bytes)

            # Send file ONLY to InputProcessor
            file_result = input_processor.process_file(temp_file_path)

            # Keep the actual filename uploaded by the user
            file_result["source_name"] = file.filename

            processed_contents.append(file_result["content"])

            source_information.append(
                {
                    "source_type": file_result["source_type"],
                    "source_name": file_result["source_name"],
                    "metadata": file_result["metadata"],
                }
            )

        finally:
            # Remove temporary uploaded file
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    # ------------------------------------------------------
    # 3.combine text + file if user has entered both
    # ------------------------------------------------------
    combined_content = "\n\n".join(processed_contents)

    if not combined_content.strip():
        raise HTTPException(
            status_code=400,
            detail="No readable text could be extracted from the input.",
        )

    # ------------------------------------------------------
    # 4.create firewall input
    # ------------------------------------------------------

    firewall_input = {"content": combined_content, "sources": source_information}

    # ------------------------------------------------------
    # 5. Send request through SentinelAI Firewall
    # ------------------------------------------------------

    firewall_result = firewall.process(firewall_input)

    decision = firewall_result["decision"]

    # ------------------------------------------------------
    # 3. BLOCK
    # ------------------------------------------------------

    if decision == "BLOCK":
        context = firewall_result["context_analysis"]

        return {
            "decision": "BLOCK",
            "status": "blocked",
            "message": firewall_result["block_message"],
            "attack_types": context["attack_types"],
            "malicious_spans": context["malicious_spans"],
            "reason": context["reason"],
            "risk_level": context["risk_level"],
            "original_content": combined_content,
            "sanitized_content": None,
            "ai_response": None,
            "sources": source_information,
        }

    # ------------------------------------------------------
    # 4. ALLOW / SANITIZE
    # ------------------------------------------------------

    safe_content = firewall_result["sanitized_content"]

    # ------------------------------------------------------
    # 5. Validator safety check
    # ------------------------------------------------------

    validator_result = firewall_result.get("validator")

    if validator_result:
        if not validator_result["is_valid"]:
            context = firewall_result["context_analysis"]

            return {
                "decision": "BLOCK",
                "status": "blocked",
                "message": (
                    "Request blocked because the final content "
                    "did not pass security validation."
                ),
                "attack_types": (context["attack_types"] if context else []),
                "malicious_spans": context["malicious_spans"] if context else [],
                "reason": context["reason"],
                "risk_level": (context["risk_level"] if context else "low"),
                "original_content": combined_content,
                "sanitized_content": None,
                "ai_response": None,
                "sources": source_information,
            }

    # ------------------------------------------------------
    # 6. Send ONLY safe content to downstream AI
    # ------------------------------------------------------

    ai_response = downstream_ai.generate_response(safe_content)

    # ------------------------------------------------------
    # 7. Return final response
    # ------------------------------------------------------

    context = firewall_result["context_analysis"]

    return {
        "decision": decision,
        "status": "allowed",
        "attack_types": (context["attack_types"] if context else []),
        "malicious_spans": (context["malicious_spans"] if context else []),
        "reason": context["reason"] if context else "",
        "risk_level": (context["risk_level"] if context else "low"),
        "original_content": combined_content,
        "sanitized_content": safe_content,
        "ai_response": ai_response,
        "sources": source_information,
    }
