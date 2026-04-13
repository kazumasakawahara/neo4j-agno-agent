"""Tests for dedup.py text normalization functions."""
import unicodedata
import pytest
from app.lib.dedup import normalize_text, normalize_name


class TestNormalizeText:
    def test_strips_leading_trailing_whitespace(self):
        assert normalize_text("  田中  ") == "田中"

    def test_collapses_multiple_spaces(self):
        assert normalize_text("田中  太郎") == "田中 太郎"

    def test_collapses_mixed_whitespace(self):
        assert normalize_text("田中\t 太郎") == "田中 太郎"

    def test_nfc_normalization(self):
        # NFD form of "が" (か + combining dakuten)
        nfd_ga = unicodedata.normalize("NFD", "が")
        assert normalize_text(nfd_ga) == "が"
        assert normalize_text(nfd_ga) == unicodedata.normalize("NFC", "が")

    def test_fullwidth_ascii_to_halfwidth(self):
        # ＡＢＣ → ABC, １２３ → 123
        assert normalize_text("ＡＢＣ１２３") == "ABC123"

    def test_fullwidth_symbols_to_halfwidth(self):
        assert normalize_text("！＠＃") == "!@#"

    def test_none_returns_empty_string(self):
        assert normalize_text(None) == ""

    def test_empty_string_returns_empty_string(self):
        assert normalize_text("") == ""

    def test_whitespace_only_returns_empty_string(self):
        assert normalize_text("   ") == ""

    def test_normal_text_unchanged(self):
        assert normalize_text("田中太郎") == "田中太郎"

    def test_mixed_fullwidth_and_japanese(self):
        assert normalize_text("田中ＡＢＣ") == "田中ABC"


class TestNormalizeName:
    def test_strips_san_suffix(self):
        assert normalize_name("田中さん") == "田中"

    def test_strips_sama_suffix(self):
        assert normalize_name("田中様") == "田中"

    def test_strips_kun_suffix(self):
        assert normalize_name("田中くん") == "田中"

    def test_strips_chan_suffix(self):
        assert normalize_name("田中ちゃん") == "田中"

    def test_strips_shi_suffix(self):
        assert normalize_name("田中氏") == "田中"

    def test_strips_sensei_suffix(self):
        assert normalize_name("田中先生") == "田中"

    def test_preserves_non_suffix_san(self):
        # "さんま" should not be stripped — さん is not at word boundary here
        # but さんま ends with ま, not さん at end
        assert normalize_name("さんま") == "さんま"

    def test_preserves_san_in_middle(self):
        assert normalize_name("さんま太郎") == "さんま太郎"

    def test_none_returns_empty_string(self):
        assert normalize_name(None) == ""

    def test_empty_string_returns_empty_string(self):
        assert normalize_name("") == ""

    def test_normalize_text_called_first(self):
        # Fullwidth + honorific: ＡＢＣさん → ABCさん → ABC
        assert normalize_name("ＡＢＣさん") == "ABC"

    def test_whitespace_stripped_before_honorific_check(self):
        assert normalize_name("  田中さん  ") == "田中"

    def test_name_without_honorific_unchanged(self):
        assert normalize_name("田中太郎") == "田中太郎"

    def test_only_honorific_returns_empty(self):
        assert normalize_name("さん") == ""


class TestNormalizeCondition:
    def test_canonical_name_unchanged(self):
        from app.lib.dedup import normalize_condition
        assert normalize_condition("自閉症スペクトラム障害") == "自閉症スペクトラム障害"

    def test_alias_asd_resolved(self):
        from app.lib.dedup import normalize_condition
        assert normalize_condition("ASD") == "自閉症スペクトラム障害"

    def test_alias_short_form_resolved(self):
        from app.lib.dedup import normalize_condition
        assert normalize_condition("自閉スペクトラム") == "自閉症スペクトラム障害"

    def test_alias_adhd_resolved(self):
        from app.lib.dedup import normalize_condition
        assert normalize_condition("ADHD") == "注意欠如多動症"

    def test_case_insensitive_asd(self):
        from app.lib.dedup import normalize_condition
        assert normalize_condition("asd") == "自閉症スペクトラム障害"

    def test_unknown_name_passthrough(self):
        from app.lib.dedup import normalize_condition
        assert normalize_condition("希少疾患X") == "希少疾患X"

    def test_none_returns_empty(self):
        from app.lib.dedup import normalize_condition
        assert normalize_condition(None) == ""

    def test_empty_returns_empty(self):
        from app.lib.dedup import normalize_condition
        assert normalize_condition("") == ""
