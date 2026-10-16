from openpyxl import Workbook

from sheetgrad.cli import main


def excel_yap(tmp_path, hucreler, sayfa="Model"):
    wb = Workbook()
    ws = wb.active
    ws.title = sayfa
    for ref, deger in hucreler.items():
        ws[ref] = deger
    yol = tmp_path / "model.xlsx"
    wb.save(yol)
    return str(yol)


def test_rapor(tmp_path, capsys):
    yol = excel_yap(tmp_path, {
        "A1": "Fiyat", "B1": 100,
        "A2": "Adet", "B2": 50,
        "A3": "Ciro", "B3": "=B1*B2",
    })
    assert main([yol, "B3"]) == 0
    cikti = capsys.readouterr().out
    assert "Ciro (B3) = 5,000.00" in cikti
    assert "Fiyat" in cikti and "+50.00" in cikti
    assert "Adet" in cikti and "+100.00" in cikti
    assert "\033[" not in cikti   # terminal değilse renk kodu yok


def test_kucuk_harf_hucre(tmp_path, capsys):
    yol = excel_yap(tmp_path, {"B1": 2, "B2": "=B1*3"})
    assert main([yol, "b2"]) == 0
    assert "(B2) = 6.00" in capsys.readouterr().out


def test_dosya_yok(capsys):
    assert main(["yok.xlsx", "B1"]) == 1
    assert "dosya bulunamadı" in capsys.readouterr().err


def test_sayfa_yok(tmp_path, capsys):
    yol = excel_yap(tmp_path, {"B1": 1})
    assert main([yol, "B1", "--sayfa", "Yanlis"]) == 1
    assert "Yanlis" in capsys.readouterr().err


def test_sayfa_secimi(tmp_path, capsys):
    yol = excel_yap(tmp_path, {"B1": 2, "B2": "=B1*3"}, sayfa="Hesap")
    assert main([yol, "B2", "--sayfa", "Hesap"]) == 0


def test_formul_hatasi(tmp_path, capsys):
    yol = excel_yap(tmp_path, {"A1": "=B1", "B1": "=A1"})
    assert main([yol, "A1"]) == 1
    assert "Döngüsel" in capsys.readouterr().err


def test_girdisiz_hucre(tmp_path, capsys):
    yol = excel_yap(tmp_path, {"B1": "=2*3"})
    assert main([yol, "B1"]) == 0
    assert "hiçbir girdiye bağlı değil" in capsys.readouterr().out


def kar_dosyasi(tmp_path):
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


def test_hedef_arama(tmp_path, capsys):
    yol = kar_dosyasi(tmp_path)
    assert main([yol, "B13", "--hedef", "10000", "--degistir", "B2,B4"]) == 0
    cikti = capsys.readouterr().out
    assert "Hedefe ulaşıldı" in cikti
    assert "Fiyat" in cikti and "Reklam bütçesi" in cikti
    assert "Kira" not in cikti


def test_ulasilamayan_hedef_kodu(tmp_path, capsys):
    yol = kar_dosyasi(tmp_path)
    assert main([yol, "B13", "--hedef", "10000", "--degistir", "B2"]) == 2
    cikti = capsys.readouterr().out
    assert "ulaşılamadı" in cikti
    assert "6,000.00" in cikti


def test_hedef_zaten_tutuyor(tmp_path, capsys):
    yol = kar_dosyasi(tmp_path)
    assert main([yol, "B13", "--hedef", "5000"]) == 0
    assert "zaten hedefte" in capsys.readouterr().out


def test_girdi_olmayan_hucre(tmp_path, capsys):
    yol = kar_dosyasi(tmp_path)
    assert main([yol, "B13", "--hedef", "10000", "--degistir", "B9"]) == 1
    assert "B9" in capsys.readouterr().err
