"""
148-character dictionary of MapTextPipeline (Rumsey model, MODEL.TRANSFORMER.VOC_SIZE = 148).

Identical to CTLABELS (voc_size 148) in MapTextPipeline/adet/evaluation/text_evaluation_all.py.
Encoding: index into CTLABELS_148, padding = 148 (= voc_size), 147 = unknown (never written here).

Words containing characters that cannot be encoded are filtered out before rendering
(synth_map_maker.create_svg), so every rendered word has a complete transcription.
"""

CTLABELS_148 = [' ', '!', '"', '#', '$', '%', '&', "'", '(', ')', '+', ',', '-', '.', '/', '0', '1', '2', '3', '4', '5',
    '6', '7', '8', '9', ':', ';', '<', '=', '>', '?', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K',
    'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '_', '`', 'a', 'b', 'c', 'd',
    'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y',
    'z', '\x8d', '\xa0', '¡', '£', '¨', '©', '®', '¯', '°', '¹', 'Á', 'Â', 'Ã', 'Ä', 'Å', 'É', 'Ê', 'Ì',
    'Í', 'Î', 'Ó', 'ß', 'à', 'á', 'â', 'ä', 'è', 'é', 'ê', 'ë', 'í', 'ï', 'ñ', 'ó', 'ô', 'õ', 'ö', 'ú',
    'û', 'ü', 'ÿ', 'ā', 'ė', 'ī', 'ő', 'Œ', 'ŵ', 'ƙ', 'ˆ', 'ˈ', '̓', 'Ї', 'ї', 'ḙ', 'Ṃ', 'ἀ', '‘', '’',
    '“', '”', '‰', '›']

VOC_SIZE = 148
MAX_LEN = 25        # MODEL.TRANSFORMER.NUM_POINTS
PAD = VOC_SIZE

assert len(CTLABELS_148) == VOC_SIZE - 1

CHAR2ID = {c: i for i, c in enumerate(CTLABELS_148)}

# not in the dictionary, but encoded as their lowercase variant (evaluation is case-insensitive)
CASE_FALLBACK = {'Ö': 'ö', 'Ü': 'ü'}


def is_encodable(word):
    return all(c in CHAR2ID or c in CASE_FALLBACK for c in word)


def unencodable_chars(word):
    return {c for c in word if c not in CHAR2ID and c not in CASE_FALLBACK}


def encode(word, max_len=MAX_LEN):
    if not is_encodable(word):
        raise ValueError(f"Word '{word}' contains characters outside the 148voc dictionary: {unencodable_chars(word)}")
    if len(word) > max_len:
        raise ValueError(f"Word '{word}' is longer than {max_len} characters")
    rec = [CHAR2ID[CASE_FALLBACK.get(c, c)] for c in word]
    return rec + [PAD] * (max_len - len(rec))
