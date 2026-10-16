import pytest

from sheetgrad.engine import Value


def test_kar_modeli_turevleri():
    fiyat = Value(100)
    adet = Value(50)
    maliyet = Value(60)
    kira = Value(500)
    kar = fiyat * adet - maliyet * adet - kira
    kar.backward()
    assert fiyat.grad == 50
    assert adet.grad == 40
    assert maliyet.grad == -50
    assert kira.grad == -1


def test_kare():
    x = Value(3)
    y = x ** 2
    y.backward()
    assert x.grad == 6


def test_ayni_degisken_iki_kez():
    a = Value(4)
    b = a * a
    b.backward()
    assert a.grad == 8


def test_bolme():
    a = Value(6)
    b = Value(2)
    c = a / b
    c.backward()
    assert a.grad == pytest.approx(0.5)
    assert b.grad == pytest.approx(-1.5)


def test_zincir_kurali():
    x = Value(2)
    y = (3 * x + 1) ** 2
    y.backward()
    assert x.grad == 42


def sayisal_turev(f, x, h=1e-6):
    return (f(x + h) - f(x - h)) / (2 * h)


def test_sayisal_turev_ile_ayni():
    def f(x):
        return (x ** 3 - 2 * x) / (x ** 2 + 1)

    x = Value(1.5)
    y = f(x)
    y.backward()
    assert x.grad == pytest.approx(sayisal_turev(f, 1.5), rel=1e-6)