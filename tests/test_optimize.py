import pytest
from openpyxl import Workbook

from sheetgrad.model import Model
from sheetgrad.optimize import goal_seek


def excel_yap(tmp_path, hucreler):
    wb = Workbook()
    ws = wb.active
    for ref, deger in hucreler.items():
        ws[ref] = deger
    yol = tmp_path / "model.xlsx"
    wb.save(yol)
    return Model.from_excel(yol)


@pytest.fixture
def kar_modeli(tmp_path):
    return excel_yap(tmp_path, {
        "A2": "Fiyat", "B2": 100,
        "A3": "Birim maliyet", "B3": 60,
        "A4": "Reklam bütçesi", "B4": 20000,
        "A5": "Kira", "B5": 15000,
        "A6": "Maaşlar", "B6": 40000,
        "B9": "=5000-40*B2+0.05*B4",
        "B10": "=B2*B9",
        "B11": "=B3*B9",
        "B12": "=B11+B4+B5+B6",
        "A13": "Kâr", "B13": "=B10-B12",
    })


def test_tek_girdi_ile_hedef(kar_modeli):
    sonuc = goal_seek(kar_modeli, "B13", 5500, cells=["B2"])
    assert sonuc["reached"]
    assert sonuc["output"] == pytest.approx(5500, rel=1e-4)
    # (f-60)(6000-40f) = 80500 → f ≈ 101.46 veya 108.54; başlangıca yakın olanı bulmalı
    assert sonuc["changes"][0]["new"] == pytest.approx(101.464, abs=0.01)


def test_ulasilamayan_hedef_en_iyiyi_bulur(kar_modeli):
    # Sadece fiyatla kâr en fazla 6000 olabilir (fiyat = 105'te)
    sonuc = goal_seek(kar_modeli, "B13", 10000, cells=["B2"])
    assert not sonuc["reached"]
    assert sonuc["output"] == pytest.approx(6000, abs=1)
    assert sonuc["changes"][0]["new"] == pytest.approx(105, abs=0.1)


def test_tum_girdilerle_hedef(kar_modeli):
    sonuc = goal_seek(kar_modeli, "B13", 10000)
    assert sonuc["reached"]
    assert kar_modeli.run("B13", {c["cell"]: c["new"] for c in sonuc["changes"]}).data == pytest.approx(10000, rel=1e-4)


def test_esit_olcekli_girdiler_esit_artar(tmp_path):
    model = excel_yap(tmp_path, {"A1": 10, "A2": 10, "A3": "=A1+A2"})
    sonuc = goal_seek(model, "A3", 30)
    yeni = {c["cell"]: c["new"] for c in sonuc["changes"]}
    assert yeni["A1"] == pytest.approx(15, rel=1e-3)
    assert yeni["A2"] == pytest.approx(15, rel=1e-3)


def test_buyuk_girdi_daha_cok_degisir(tmp_path):
    model = excel_yap(tmp_path, {"A1": 10, "A2": 1000, "A3": "=A1+A2"})
    sonuc = goal_seek(model, "A3", 1111)
    yeni = {c["cell"]: c["new"] for c in sonuc["changes"]}
    assert sonuc["reached"]
    # İkisi de yüzde olarak aynı oranda değişmeli, mutlak değişimde büyük olan baskın
    assert (yeni["A2"] - 1000) > (yeni["A1"] - 10) * 50


def test_negatife_dusmez(tmp_path):
    model = excel_yap(tmp_path, {"A1": 10, "A2": "=A1*2"})
    sonuc = goal_seek(model, "A2", -20)
    assert not sonuc["reached"]
    assert sonuc["changes"][0]["new"] == pytest.approx(0)


def test_sifir_degerli_girdi(tmp_path):
    model = excel_yap(tmp_path, {"A1": 0, "A2": 5, "A3": "=A1+A2"})
    sonuc = goal_seek(model, "A3", 7)
    assert sonuc["reached"]


def test_zaten_hedefteyse_degisiklik_yok(kar_modeli):
    sonuc = goal_seek(kar_modeli, "B13", 5000)
    assert sonuc["reached"]
    assert sonuc["changes"] == []
    assert sonuc["steps"] == 0


def test_girdi_olmayan_hucre_hata_verir(kar_modeli):
    with pytest.raises(ValueError, match="B9"):
        goal_seek(kar_modeli, "B13", 10000, cells=["B9"])


def test_model_degismeden_kalir(kar_modeli):
    goal_seek(kar_modeli, "B13", 10000)
    assert kar_modeli.run("B13").data == 5000
