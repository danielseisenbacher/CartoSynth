"""
Character dictionaries (vocabularies) of text spotting models and the `rec` encoding.

`rec` holds one index per character, padded to `max_length` with `pad` (= number of
characters + 1, the models reserve `pad - 1` for "unknown"). CartoSynth never writes the
unknown index: words the dictionary cannot encode are removed before rendering.
"""
import os

from .config import resolve

# AdelaiDet / ABCNet / DeepSolo "96voc": printable ASCII 32..126 (index = ord(c) - 32), pad 96
VOC96 = [chr(i) for i in range(32, 127)]

# MapTextPipeline (Rumsey model, VOC_SIZE 148), identical to CTLABELS in
# MapTextPipeline/adet/evaluation/text_evaluation_all.py
VOC148 = [' ', '!', '"', '#', '$', '%', '&', "'", '(', ')', '+', ',', '-', '.', '/', '0', '1', '2', '3', '4', '5',
    '6', '7', '8', '9', ':', ';', '<', '=', '>', '?', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K',
    'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '_', '`', 'a', 'b', 'c', 'd',
    'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y',
    'z', '\x8d', '\xa0', '¡', '£', '¨', '©', '®', '¯', '°', '¹', 'Á', 'Â', 'Ã', 'Ä', 'Å', 'É', 'Ê', 'Ì',
    'Í', 'Î', 'Ó', 'ß', 'à', 'á', 'â', 'ä', 'è', 'é', 'ê', 'ë', 'í', 'ï', 'ñ', 'ó', 'ô', 'õ', 'ö', 'ú',
    'û', 'ü', 'ÿ', 'ā', 'ė', 'ī', 'ő', 'Œ', 'ŵ', 'ƙ', 'ˆ', 'ˈ', '̓', 'Ї', 'ї', 'ḙ', 'Ṃ', 'ἀ', '‘', '’',
    '“', '”', '‰', '›']

BUILTIN = {"voc96": VOC96, "voc148": VOC148}


class Vocabulary:
    def __init__(self, characters, max_length=25, case_fallback=None):
        self.characters = list(characters)
        self.char2id = {c: i for i, c in enumerate(self.characters)}
        self.max_length = max_length
        self.pad = len(self.characters) + 1
        self.case_fallback = dict(case_fallback or {})
        for src, dst in self.case_fallback.items():
            if dst not in self.char2id:
                raise ValueError(f"case_fallback maps '{src}' to '{dst}', which is not in the dictionary")

    @classmethod
    def from_config(cls, annotation_cfg):
        name = annotation_cfg["vocabulary"]
        if name in BUILTIN:
            characters = BUILTIN[name]
        else:
            path = resolve(name)
            if not os.path.exists(path):
                raise ValueError(f"Unknown vocabulary '{name}' (use voc96, voc148 or a path to a character file)")
            with open(path, encoding="utf-8") as f:
                characters = [line.rstrip("\n") for line in f if line.rstrip("\n") != ""]
        return cls(characters, annotation_cfg["max_length"], annotation_cfg.get("case_fallback"))

    def unencodable_chars(self, text):
        return {c for c in text if c not in self.char2id and c not in self.case_fallback}

    def is_encodable(self, text):
        return not self.unencodable_chars(text)

    def encode(self, text):
        if not self.is_encodable(text):
            raise ValueError(f"'{text}' contains characters outside the dictionary: {self.unencodable_chars(text)}")
        if len(text) > self.max_length:
            raise ValueError(f"'{text}' is longer than {self.max_length} characters")
        rec = [self.char2id[self.case_fallback.get(c, c)] for c in text]
        return rec + [self.pad] * (self.max_length - len(rec))

    def decode(self, rec):
        return "".join(self.characters[i] for i in rec if i < len(self.characters))
