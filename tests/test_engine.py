from sheetgrad.engine import Value


def test_toplama():
    assert (Value(2) + Value(3)).data == 5


def test_sayi_ile_toplama():
    assert (Value(2) + 3).data == 5
    assert (3 + Value(2)).data == 5


def test_carpma():
    assert (Value(4) * Value(5)).data == 20
    assert (2 * Value(5)).data == 10


def test_us():
    assert (Value(3) ** 2).data == 9


def test_cikarma_ve_bolme():
    assert (Value(10) - Value(4)).data == 6
    assert (Value(10) / Value(4)).data == 2.5


def test_sayi_soldayken_cikarma_ve_bolme():
    assert (10 - Value(4)).data == 6
    assert (10 / Value(4)).data == 2.5


def test_negatif():
    assert (-Value(7)).data == -7


def test_gecmis_kaydediliyor():
    a = Value(2)
    b = Value(3)
    c = a * b
    assert c._op == "*"
    assert a in c._children and b in c._children


def test_kar_modeli():
    fiyat = Value(100)
    adet = Value(50)
    maliyet = Value(60)
    kira = Value(500)
    kar = fiyat * adet - maliyet * adet - kira
    assert kar.data == 1500