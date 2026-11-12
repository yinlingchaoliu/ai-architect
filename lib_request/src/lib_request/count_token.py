"""Local token counting; importing the SDK needs no API credentials or tokenizer download."""

import tiktoken


def count_tokens(text):
    # tiktoken caches the encoder. Its first use may fetch tokenizer data;
    # defer that work until counting is explicitly requested.
    encoder = tiktoken.encoding_for_model("gpt-4")
    return len(encoder.encode(text))
