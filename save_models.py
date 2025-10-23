# save_models.py
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from neucodec import NeuCodec

# --- Configuration ---
BACKBONE_REPO = "neuphonic/neutts-air"
CODEC_REPO = "neuphonic/neucodec"
SAVE_DIR = "./local_models"

# --- 1. Save the Backbone Model and Tokenizer ---
print(f"Loading backbone from '{BACKBONE_REPO}'...")
backbone = AutoModelForCausalLM.from_pretrained(BACKBONE_REPO)
tokenizer = AutoTokenizer.from_pretrained(BACKBONE_REPO)

print(f"Saving backbone and tokenizer to '{SAVE_DIR}/backbone/'...")
backbone.save_pretrained(f"{SAVE_DIR}/backbone")
tokenizer.save_pretrained(f"{SAVE_DIR}/backbone")
print("Backbone saved successfully!")

# --- 2. Save the Codec Model ---
print(f"\nLoading codec from '{CODEC_REPO}'...")
codec = NeuCodec.from_pretrained(CODEC_REPO)

print(f"Saving codec state_dict to '{SAVE_DIR}/codec.pt'...")
# We save the state_dict, which contains all the learned weights
torch.save(codec.state_dict(), f"{SAVE_DIR}/codec.pt")
print("Codec saved successfully!")