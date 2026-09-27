import pytest

from cartosynth.vocab import VOC96, VOC148, Vocabulary


def test_voc96_matches_adelaidet():
    vocab = Vocabulary(VOC96, max_length=5)
    assert vocab.pad == 96
    assert vocab.encode("Ab") == [33, 66, 96, 96, 96]   # index = ord(c) - 32


def test_voc148_matches_maptextpipeline():
    vocab = Vocabulary(VOC148, max_length=25)
    assert vocab.pad == 148
    rec = vocab.encode("Mühle")
    assert len(rec) == 25 and rec[5:] == [148] * 20
    assert vocab.decode(rec) == "Mühle"


def test_case_fallback():
    vocab = Vocabulary(VOC148, max_length=25, case_fallback={"Ö": "ö"})
    assert vocab.is_encodable("ÖTZ")
    assert vocab.decode(vocab.encode("ÖTZ")) == "öTZ"


def test_unencodable_and_too_long():
    vocab = Vocabulary(VOC148, max_length=4)
    assert vocab.unencodable_chars("Čes") == {"Č"}
    with pytest.raises(ValueError):
        vocab.encode("Čes")
    with pytest.raises(ValueError):
        vocab.encode("Wien1")


def test_case_fallback_target_must_exist():
    with pytest.raises(ValueError):
        Vocabulary(VOC96, case_fallback={"Ö": "ö"})


def test_custom_vocabulary_file(tmp_path):
    chars = tmp_path / "chars.txt"
    chars.write_text("a\nb\nc\n", encoding="utf-8")
    vocab = Vocabulary.from_config({"vocabulary": str(chars), "max_length": 3})
    assert vocab.encode("cab") == [2, 0, 1] and vocab.pad == 4
