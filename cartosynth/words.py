"""Loads the word list and keeps only rows the annotation dictionary can encode."""
import random
import unicodedata
from collections import Counter

from .config import resolve


def load_words(words_cfg, vocab):
    """
    Rows of the word list (one label per line, may contain spaces). Skipped are rows
    - with a word shorter than min_word_length or longer than max_word_length, and
    - with characters the vocabulary cannot encode, in any case variant (a font style may
      upper- or lower-case the label), so no label is rendered without a valid annotation.
    """
    words, dropped_chars = [], Counter()
    too_short = too_long = unencodable = 0
    with open(resolve(words_cfg["file"]), encoding="utf-8") as f:
        for row in f:
            row = unicodedata.normalize("NFKC", row.strip())
            if not row:
                continue
            lengths = [len(w) for w in row.split(" ") if w]
            if min(lengths) < words_cfg["min_word_length"]:
                too_short += 1
                continue
            if max(lengths) > words_cfg["max_word_length"]:
                too_long += 1
                continue
            variants = (row, row.upper(), row.lower())
            if not all(vocab.is_encodable(v) for v in variants):
                unencodable += 1
                dropped_chars.update(set().union(*(vocab.unencodable_chars(v) for v in variants)))
                continue
            words.append(row)

    if words_cfg.get("shuffle"):
        random.shuffle(words)
    print(f"Word list {words_cfg['file']}: {len(words)} rows kept, skipped {too_short} (too short), "
          f"{too_long} (too long), {unencodable} (characters not in dictionary: {''.join(sorted(dropped_chars))})")
    if not words:
        raise ValueError("No usable words in the word list")
    return words


def check_short_tokens(short_cfg, vocab):
    """Short label tokens must be encodable and not longer than the annotation length."""
    if short_cfg["share"] <= 0:
        return []
    bad = [t for t in short_cfg["tokens"] if not vocab.is_encodable(t) or len(t) > vocab.max_length]
    if bad:
        raise ValueError(f"short_labels.tokens not encodable in the annotation dictionary: {bad}")
    tokens = list(short_cfg["tokens"])
    print(f"Short labels: {len(tokens)} tokens, share {short_cfg['share']:.0%}")
    return tokens
