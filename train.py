from transformers import PegasusForConditionalGeneration, PegasusTokenizer
from transformers import pipeline 
from transformers import AutoTokenizer


import torch
from transformers import PegasusForConditionalGeneration, PegasusTokenizer
from transformers import DataCollatorForSeq2Seq, AutoModelForSeq2SeqLM, Seq2SeqTrainingArguments, Seq2SeqTrainer
if torch.cuda.is_available():
    device = torch.device('cuda:0')  
    torch.cuda.set_device(device)  
else:
    device = torch.device('cpu')

prefix = "summarize: "

def preprocess_function(examples):
    inputs = [prefix + doc for doc in examples["content"]]
    model_inputs = tokenizer(inputs, max_length=8192, truncation=True)

    labels = tokenizer(text_target=examples["summary"], max_length=128, truncation=True)

    model_inputs["labels"] = labels["input_ids"]
    return model_inputs


dataset_train = dataset['train'].train_test_split(test_size=0.1)
dataset_train = dataset_train.map(preprocess_function, batched=True)



data_collator = DataCollatorForSeq2Seq(tokenizer=tokenizer, model=checkpoint)

model_name = "google/pegasus-xsum"
tokenizer = PegasusTokenizer.from_pretrained(model_name,)
model = PegasusForConditionalGeneration.from_pretrained(model_name,max_position_embeddings=8192).to(device)
data_collator = DataCollatorForSeq2Seq(tokenizer=tokenizer, model=model)

training_args = Seq2SeqTrainingArguments(
    output_dir="pegasus_model",
    evaluation_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=4,
    per_device_eval_batch_size=4,
    weight_decay=0.01,
    save_total_limit=3,
    num_train_epochs=8,
    predict_with_generate=True,
    fp16=True,
    push_to_hub=True,
)

trainer = Seq2SeqTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset_train["train"],
    eval_dataset=dataset_train["test"],
    tokenizer=tokenizer,
    data_collator=data_collator,
    compute_metrics=compute_metrics,
)

trainer.train()