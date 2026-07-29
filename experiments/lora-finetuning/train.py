"""
Fine-tunes distilbert-base-uncased with a LoRA adapter to classify
risk-factor sentences into categories — a small, CPU-friendly,
end-to-end demonstration of the actual LoRA mechanism.
"""
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
)
from peft import LoraConfig, get_peft_model, TaskType
from datasets import Dataset

from dataset import LABELS, TRAIN_EXAMPLES, EVAL_EXAMPLES

MODEL_NAME = "distilbert-base-uncased"
label2id = {label: i for i, label in enumerate(LABELS)}
id2label = {i: label for label, i in label2id.items()}


def build_dataset(examples):
    texts = [t for t, _ in examples]
    labels = [label2id[l] for _, l in examples]
    return Dataset.from_dict({"text": texts, "label": labels})


def main():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    def tokenize(batch):
        return tokenizer(batch["text"], truncation=True, padding="max_length", max_length=64)

    train_ds = build_dataset(TRAIN_EXAMPLES).map(tokenize, batched=True)
    eval_ds = build_dataset(EVAL_EXAMPLES).map(tokenize, batched=True)

    base_model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME, num_labels=len(LABELS), id2label=id2label, label2id=label2id
    )

    # This is the actual LoRA step: instead of fine-tuning all of
    # distilbert's ~66M parameters, we freeze the base model and inject
    # small trainable low-rank matrices into the attention query/value
    # projections — r=8 means each adapter matrix pair has rank 8,
    # a small fraction of the original layer dimensions.
    lora_config = LoraConfig(
        task_type=TaskType.SEQ_CLS,
        r=8,
        lora_alpha=16,
        lora_dropout=0.1,
        target_modules=["q_lin", "v_lin"],  # distilbert's attention projection layers
    )
    model = get_peft_model(base_model, lora_config)

    trainable, total = model.get_nb_trainable_parameters()
    print(f"\nTrainable parameters: {trainable:,} / {total:,} ({100 * trainable / total:.2f}%)\n")

    training_args = TrainingArguments(
        output_dir="./lora-checkpoints",
        num_train_epochs=15,  # small dataset, more epochs needed to actually learn the pattern
        per_device_train_batch_size=4,
        learning_rate=1e-3,
        logging_steps=5,
        eval_strategy="epoch",
        save_strategy="no",
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
    )

    trainer.train()

    model.save_pretrained("./risk-classifier-lora-adapter")
    tokenizer.save_pretrained("./risk-classifier-lora-adapter")
    print("\nLoRA adapter saved to ./risk-classifier-lora-adapter")


if __name__ == "__main__":
    main()
