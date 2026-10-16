import math

import pytest

from sheetgrad.engine import Value


def sayisal_turev(f, x, h=1e-6):
    return (f(x + h) - f(x - h)) / (2 * h)


def test_exp():
    x = Value(2.0)
    y = x.exp()
    y.backward()
    assert y.data == pytest.approx(math.exp(2))
    assert x.grad == pytest.approx(math.exp(2))


def test_log():
    x = Value(4.0)
    y = x.log()
    y.backward()
    assert y.data == pytest.approx(math.log(4))
    assert x.grad == pytest.approx(0.25)


def test_log_sifir_veya_negatif_hata_verir():
    with pytest.raises(ValueError):
        Value(0.0).log()
    with pytest.raises(ValueError):
        Value(-1.0).log()


def test_us_degisken_olabilir():
    a = Value(2.0)
    b = Value(3.0)
    c = a ** b
    c.backward()
    assert c.data == 8
    assert a.grad == pytest.approx(12)                 # b * a^(b-1)
    assert b.grad == pytest.approx(8 * math.log(2))    # a^b * ln(a)


def test_sayi_tabanli_us():
    x = Value(3.0)
    y = 2 ** x
    y.backward()
    assert y.data == 8
    assert x.grad == pytest.approx(8 * math.log(2))


def test_negatif_tabanda_us_turevi_tanimsiz():
    a = Value(-2.0)
    b = Value(3.0)
    c = a ** b
    c.backward()
    assert c.data == -8
    assert a.grad == pytest.approx(12)
    assert math.isnan(b.grad)


def test_bilesik_faiz():
    anapara = Value(1000.0)
    faiz = Value(0.05)
    yil = Value(10.0)
    sonuc = anapara * (1 + faiz) ** yil
    sonuc.backward()
    assert sonuc.data == pytest.approx(1000 * 1.05 ** 10)
    assert faiz.grad == pytest.approx(
        sayisal_turev(lambda r: 1000 * (1 + r) ** 10, 0.05), rel=1e-6
    )
    assert yil.grad == pytest.approx(
        sayisal_turev(lambda n: 1000 * 1.05 ** n, 10.0), rel=1e-6
    )