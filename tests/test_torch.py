import pytest

from sheetgrad.engine import Value

torch = pytest.importorskip("torch")


def karsilastir(f, girdiler):
    bizim = [Value(x) for x in girdiler]
    sonuc = f(*bizim)
    sonuc.backward()

    onlarin = [torch.tensor(x, dtype=torch.float64, requires_grad=True) for x in girdiler]
    t_sonuc = f(*onlarin)
    t_sonuc.backward()

    assert sonuc.data == pytest.approx(t_sonuc.item())
    for b, o in zip(bizim, onlarin):
        assert b.grad == pytest.approx(o.grad.item())


def test_kar_modeli():
    karsilastir(lambda f, a, m, k: f * a - m * a - k, [100.0, 50.0, 60.0, 500.0])


def test_bolme_ve_us():
    karsilastir(lambda x, y: (x ** 3 - 2 * x) / (y ** 2 + 1), [1.5, -0.7])


def test_exp_ve_log():
    karsilastir(lambda x, y: (x * y).exp() + (x + y ** 2).log(), [0.3, 1.2])


def test_degisken_us():
    karsilastir(lambda a, r, n: a * (1 + r) ** n, [1000.0, 0.05, 10.0])


def test_ayni_degisken_cok_yerde():
    karsilastir(lambda x: x * x * x + x / (x + 1) - (x ** 2).log(), [2.5])