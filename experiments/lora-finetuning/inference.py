"""Loads the trained LoRA adapter and classifies new, unseen risk sentences."""
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from peft import PeftModel

BASE_MODEL = "distilbert-base-uncased"
ADAPTER_PATH = "./risk-classifier-lora-adapter"

tokenizer = AutoTokenizer.from_pretrained(ADAPTER_PATH)
base_model = AutoModelForSequenceClassification.from_pretrained(
    BASE_MODEL, num_labels=5,
    id2label={0: "supply_chain", 1: "regulatory", 2: "competition", 3: "cybersecurity", 4: "macroeconomic"},
    label2id={"supply_chain": 0, "regulatory": 1, "competition": 2, "cybersecurity": 3, "macroeconomic": 4},
)
model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)
model.eval()

test_sentences = [
    "The Company's factories depend on a single overseas parts supplier.",
    "Regulators may require changes to the Company's data handling practices.",
    "A newly public rival is undercutting prices in key markets.",
    "An unpatched vulnerability could allow attackers to access customer records.",
]

for sentence in test_sentences:
    inputs = tokenizer(sentence, return_tensors="pt", truncation=True, max_length=64)
    with torch.no_grad():
        logits = model(**inputs).logits
    predicted = model.config.id2label[logits.argmax().item()]
    print(f"{sentence}\n  -> {predicted}\n")
