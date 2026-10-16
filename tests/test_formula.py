import math

import pytest

from sheetgrad.engine import Value
from sheetgrad.formula import (
    column_to_number,
    evaluate,
    expand_range,
    number_to_column,
    tokenize,
)


def hucreler(**degerler):
    """Testler için sahte bir tablo: hucreler(B2=100, B3=50)"""
    tablo = {ad: Value(float(v)) for ad, v in degerler.items()}
    return tablo, lambda ref: tablo[ref]


# --- tokenizer ---

def test_tokenize():
    assert tokenize("=B2*(1+$B$3)^B4") == [
        ("CELL", "B2"), ("OP", "*"), ("LPAREN", "("), ("NUMBER", "1"),
        ("OP", "+"), ("CELL", "B3"), ("RPAREN", ")"), ("OP", "^"), ("CELL", "B4"),
    ]


def test_tokenize_fonksiyon_ve_aralik():
    assert tokenize("=sum(A1:A3, 2.5)") == [
        ("FUNC", "SUM"), ("LPAREN", "("), ("CELL", "A1"), ("COLON", ":"),
        ("CELL", "A3"), ("COMMA", ","), ("NUMBER", "2.5"), ("RPAREN", ")"),
    ]


def test_tokenize_bilinmeyen_karakter():
    with pytest.raises(ValueError):
        tokenize("=A1 & A2")


# --- sütun harfleri ---

@pytest.mark.parametrize("harf, sayi", [("A", 1), ("Z", 26), ("AA", 27), ("AZ", 52), ("BA", 53), ("XFD", 16384)])
def test_sutun_donusumu(harf, sayi):
    assert column_to_number(harf) == sayi
    assert number_to_column(sayi) == harf


def test_aralik_acma():
    assert expand_range("A1", "B2") == ["A1", "B1", "A2", "B2"]
    assert expand_range("C3", "C1") == ["C1", "C2", "C3"]


# --- hesaplama ---

@pytest.mark.parametrize("formul, beklenen", [
    ("=1+2*3", 7),
    ("=(1+2)*3", 9),
    ("=10-4-3", 3),
    ("=12/4/3", 1),
    ("=2^3", 8),
    ("=-2^2", 4),       # Excel: eksi işareti önce → (-2)^2
    ("=2^3^2", 64),     # Excel: soldan sağa → (2^3)^2
    ("=2*-3", -6),
    ("=1.5e2", 150),
])
def test_islem_onceligi(formul, beklenen):
    _, get = hucreler()
    assert evaluate(formul, get).data == pytest.approx(beklenen)


def test_hucre_referansi():
    _, get = hucreler(B2=100, B3=50, B4=60, B5=500)
    assert evaluate("=B2*B3-B4*B3-B5", get).data == 1500


def test_fonksiyonlar():
    _, get = hucreler(A1=1, A2=2, A3=3)
    assert evaluate("=SUM(A1:A3)", get).data == 6
    assert evaluate("=SUM(A1:A3, 10)", get).data == 16
    assert evaluate("=AVERAGE(A1:A3)", get).data == 2
    assert evaluate("=EXP(A1)", get).data == pytest.approx(math.e)
    assert evaluate("=LN(A1)", get).data == 0


def test_desteklenmeyen_fonksiyon():
    _, get = hucreler(A1=1)
    with pytest.raises(NotImplementedError, match="VLOOKUP"):
        evaluate("=VLOOKUP(A1, A1:A1, 1)", get)


def test_hatali_formuller():
    _, get = hucreler(A1=1)
    for formul in ["=(A1+1", "=A1+", "=A1 A1", "=A1:A1"]:
        with pytest.raises(ValueError):
            evaluate(formul, get)


# --- asıl hedef: türev ---

def test_bilesik_faiz_formulunun_turevi():
    tablo, get = hucreler(B2=1000, B3=0.05, B4=10)
    sonuc = evaluate("=B2*(1+B3)^B4", get)
    sonuc.backward()
    assert sonuc.data == pytest.approx(1000 * 1.05 ** 10)
    assert tablo["B2"].grad == pytest.approx(1.05 ** 10)
    assert tablo["B3"].grad == pytest.approx(10 * 1000 * 1.05 ** 9)
    assert tablo["B4"].grad == pytest.approx(1000 * 1.05 ** 10 * math.log(1.05))


def test_sum_turevi():
    tablo, get = hucreler(A1=1, A2=2, A3=3)
    sonuc = evaluate("=SUM(A1:A3)*A1", get)
    sonuc.backward()
    assert tablo["A1"].grad == 7    # 6 + 1
    assert tablo["A2"].grad == 1
    assert tablo["A3"].grad == 1