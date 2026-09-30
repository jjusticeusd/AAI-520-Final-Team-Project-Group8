"""Shared local-LLM helper (2.1).

One place to load Phi-3-mini and generate text, so every agent function and
workflow calls the same helper with the same settings and error handling.
"""

import json
import logging

MODEL_ID = "microsoft/Phi-3-mini-4k-instruct"

log = logging.getLogger(__name__)

_tokenizer = None
_model = None
_device = None


def _select_device():
    import torch

    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    log.warning(
        "No MPS/CUDA device; falling back to CPU "
        "(Phi-3-mini is not viable on CPU)."
    )
    return "cpu"


def _load():
    global _tokenizer, _model, _device
    if _model is not None:
        return
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    _device = _select_device()
    _tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    _model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, dtype=torch.bfloat16
    ).to(_device)


def llm(prompt, max_new_tokens=512, temperature=0.7, system=None):
    _load()
    import torch

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        enc = _tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt",
            return_dict=True,
        ).to(_device)
        gen_kwargs = {
            "max_new_tokens": max_new_tokens,
            "pad_token_id": _tokenizer.eos_token_id,
        }
        if temperature > 0:
            gen_kwargs["do_sample"] = True
            gen_kwargs["temperature"] = temperature
        else:
            gen_kwargs["do_sample"] = False
        with torch.no_grad():
            out = _model.generate(**enc, **gen_kwargs)
        new_tokens = out[0, enc["input_ids"].shape[1]:]
        return _tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
    except Exception as e:
        raise RuntimeError(
            f"llm() generation failed on device={_device}: {e}"
        ) from e


def parse_json(text):
    starts = [i for i in (text.find("{"), text.find("[")) if i >= 0]
    if not starts:
        raise ValueError("no JSON object in response")
    obj, _ = json.JSONDecoder().raw_decode(text[min(starts):])
    return obj


def llm_json(prompt, system, max_new_tokens=512, validate=None):
    request = prompt
    for _ in range(2):
        raw = llm(request, max_new_tokens=max_new_tokens, temperature=0,
                  system=system)
        try:
            obj = parse_json(raw)
            if validate:
                validate(obj)
            return obj
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            error = e
            request = (
                f"{prompt}\n\nYour previous reply was rejected: {e}. "
                "Return only corrected JSON."
            )
    raise ValueError(f"invalid JSON after retry: {error}")
