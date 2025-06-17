import logging
import os
from pathlib import Path
from typing import Dict, List

from datasets import load_dataset, DatasetDict, Dataset  # type: ignore
from transformers import T5Tokenizer, T5ForConditionalGeneration  # type: ignore
from transformers.data.data_collator import DataCollatorForSeq2Seq  # type: ignore
from transformers.trainer_seq2seq import Seq2SeqTrainer  # type: ignore
from transformers.training_args_seq2seq import Seq2SeqTrainingArguments  # type: ignore
from typing import Any
from pydantic import BaseModel, ValidationError

# ------------------- CONFIG -------------------
MODEL_NAME = "google/flan-t5-base"
DATA_PATH = "./data/cms_rules.json"
OUTPUT_DIR = "./models/flan-t5-cms"
LOG_PATH = "./logs/training.log"

BATCH_SIZE = 4
EPOCHS = 3
MAX_INPUT_LENGTH = 512
MAX_TARGET_LENGTH = 128

os.makedirs(Path(OUTPUT_DIR), exist_ok=True)
os.makedirs(Path(LOG_PATH).parent, exist_ok=True)

# ------------------- LOGGING -------------------
logging.basicConfig(
    filename=LOG_PATH,
    filemode='w',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ------------------- VALIDATION -------------------
class RuleSample(BaseModel):
    input: str
    output: str

# ------------------- LOAD & VALIDATE DATA -------------------
def load_and_validate_dataset(path: str) -> List[Dict[str, str]]:
    raw_dataset = load_dataset("json", data_files=path)
    valid_data: List[Dict[str, str]] = []
      # Handle the dataset properly
    train_data = raw_dataset["train"]  # type: ignore
    for sample in train_data:  # type: ignore
        try:
            # Ensure sample is a dict-like object
            if isinstance(sample, dict):
                validated = RuleSample(**sample)  # type: ignore
                valid_data.append({"input": validated.input, "output": validated.output})
        except ValidationError as e:
            logger.warning(f"Invalid data sample skipped: {e.json()}")
    return valid_data

# ------------------- TOKENIZATION -------------------
def tokenize_function(examples: Dict[str, Any], tokenizer: Any) -> Dict[str, Any]:
    model_inputs = tokenizer(
        examples["input"], 
        max_length=MAX_INPUT_LENGTH, 
        padding="max_length", 
        truncation=True
    )
    # Remove the deprecated as_target_tokenizer context manager
    labels = tokenizer(
        examples["output"], 
        max_length=MAX_TARGET_LENGTH, 
        padding="max_length", 
        truncation=True
    )
    model_inputs["labels"] = labels["input_ids"]
    return model_inputs

# ------------------- MAIN TRAINING PIPELINE -------------------
def train():
    logger.info("Loading and validating dataset...")
    data = load_and_validate_dataset(DATA_PATH)    # Use Dataset.from_list instead of DatasetDict.from_list
    from datasets import Dataset  # type: ignore
    dataset = DatasetDict({"train": Dataset.from_list(data)})  # type: ignore

    logger.info("Loading model and tokenizer...")
    tokenizer = T5Tokenizer.from_pretrained(MODEL_NAME)  # type: ignore
    model = T5ForConditionalGeneration.from_pretrained(MODEL_NAME)  # type: ignore

    logger.info("Tokenizing dataset...")
    tokenized_dataset = dataset["train"].map(lambda x: tokenize_function(x, tokenizer), batched=True)  # type: ignore

    logger.info("Starting training...")
    training_args = Seq2SeqTrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=BATCH_SIZE,
        num_train_epochs=EPOCHS,
        eval_strategy="no",  # Changed from evaluation_strategy to eval_strategy
        save_total_limit=2,
        save_steps=500,
        logging_dir="./logs",
        learning_rate=5e-5,
        weight_decay=0.01,
        load_best_model_at_end=True
    )    data_collator = DataCollatorForSeq2Seq(tokenizer, model=model)  # type: ignore

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        data_collator=data_collator,  # Removed tokenizer parameter as it's not needed
    )

    trainer.train()  # type: ignore
    logger.info("Training complete.")

if __name__ == "__main__":
    train()
