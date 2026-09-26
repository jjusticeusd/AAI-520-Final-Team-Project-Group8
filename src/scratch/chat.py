"""Interactive multi-turn chat with the local model. Loads the model, so run
it yourself:

    uv run python src/scratch/chat.py

Type 'exit' or an empty line to quit.
"""

import torch

import llm as L

SYSTEM = "You are a financial analyst."


def main():
    L._load()
    tok, model, dev = L._tokenizer, L._model, L._device
    history = [{"role": "system", "content": SYSTEM}]

    print("Chat ready. Type 'exit' or an empty line to quit.")
    while True:
        prompt = input("\n> ").strip()
        if prompt in ("", "exit", "quit"):
            break
        history.append({"role": "user", "content": prompt})
        enc = tok.apply_chat_template(
            history,
            add_generation_prompt=True,
            return_tensors="pt",
            return_dict=True,
        ).to(dev)
        with torch.no_grad():
            out = model.generate(
                **enc,
                max_new_tokens=512,
                do_sample=True,
                temperature=0.7,
                pad_token_id=tok.eos_token_id,
            )
        reply = tok.decode(
            out[0, enc["input_ids"].shape[1]:],
            skip_special_tokens=True,
        ).strip()
        print(f"\nbot> {reply}")
        history.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    main()
