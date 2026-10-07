from pathlib import Path
import torch
import json
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# project path
PROJECT_ROOT = Path(__file__).resolve().parent.parent

MODEL_PATH = PROJECT_ROOT / "models" / "sentinelai_prompt_injection_model"

THRESHOLD_PATH = MODEL_PATH / "sentinelai_threshold.json"


class PromptInjectionDetector:
    """load Finetuned DeBERTa model to classify content in benign or malicious"""

    def __init__(self):

        # load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)

        # load fine tune model
        self.model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)

        # load thresold
        with open(THRESHOLD_PATH, "r") as f:
            threshold_data = json.load(f)
        self.threshold = threshold_data["malicious_threshold"]

        # Device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()

    def predict(self, content: str):
        inputs = self.tokenizer(
            content, truncation=True, max_length=512, return_tensors="pt"
        )
        inputs = {key: value.to(self.device) for key, value in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)

            probabilities = torch.softmax(outputs.logits, dim=-1)

        benign_probability = probabilities[0, 0].item()

        malicious_probability = probabilities[0, 1].item()

        is_malicious = malicious_probability >= self.threshold

        return {
            "is_malicious": is_malicious,
            "benign_probability": benign_probability,
            "malicious_probability": malicious_probability,
            "threshold": self.threshold,
        }
