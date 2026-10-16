import argparse
import math
import os
import sys

from sheetgrad.model import CircularReferenceError, FormulaError, Model
from sheetgrad.optimize import goal_seek

GREEN = "\033[32m"
RED = "\033[31m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def use_color():
    return sys.stdout.isatty() and "NO_COLOR" not in os.environ


def paint(text, code, enabled):
    return f"{code}{text}{RESET}" if enabled else text


def fmt(number):
    if math.isnan(number):
        return "tanımsız"
    return f"{number:+,.2f}"


def bar(value, largest, width=20):
    if math.isnan(value) or largest == 0:
        return ""
    return "█" * max(1, round(abs(value) / largest * width))


def print_report(model, output_ref, output_value, rows, color):
    label = model.label(output_ref.upper())
    print()
    print(paint(f"{label} ({output_ref.upper()}) = {output_value:,.2f}", BOLD, color))
    print()

    if not rows:
        print("Bu hücre hiçbir girdiye bağlı değil.")
        return

    name_width = max(len("Girdi"), *(len(str(r["label"])) for r in rows))
    header = f"{'Girdi':<{name_width}}  {'Hücre':<6}  {'Değer':>14}  {'1 birim artarsa':>16}  {'%1 artarsa':>14}"
    print(paint(header, DIM, color))
    print(paint("─" * (len(header) + 22), DIM, color))

    largest = max((abs(r["impact_1pct"]) for r in rows if not math.isnan(r["impact_1pct"])), default=0)

    for r in rows:
        impact = r["impact_1pct"]
        tone = RED if impact < 0 else GREEN
        line = (
            f"{str(r['label']):<{name_width}}  {r['cell']:<6}  {r['value']:>14,.2f}  "
            f"{fmt(r['gradient']):>16}  {fmt(impact):>14}  "
        )
        print(line + paint(bar(impact, largest), tone, color))

    undefined = [r["label"] for r in rows if math.isnan(r["gradient"])]
    if undefined:
        print()
        print(f"Uyarı: {', '.join(map(str, undefined))} için türev tanımsız "
              "(ör. negatif tabanlı bir sayının üssü).")
    print()


def print_goal_report(model, output_ref, result, color):
    label = model.label(output_ref.upper())
    print()
    print(paint(f"Hedef: {label} ({output_ref.upper()}) = {result['target']:,.2f}", BOLD, color))
    print(f"Şu an: {result['start']:,.2f}")
    print()

    if result["reached"] and not result["changes"]:
        print(paint("✓ Sonuç zaten hedefte.", GREEN, color))
        print()
        return

    if result["reached"]:
        print(paint(f"✓ Hedefe ulaşıldı: {result['output']:,.2f}", GREEN, color))
    else:
        print(paint("✗ Hedefe ulaşılamadı.", RED, color))
        print(f"  Seçilen girdilerle ulaşılabilen en yakın değer: {result['output']:,.2f}")
    print()

    rows = result["changes"]
    name_width = max(len("Girdi"), *(len(str(r["label"])) for r in rows))
    header = f"{'Girdi':<{name_width}}  {'Hücre':<6}  {'Şu an':>14}  {'Önerilen':>14}  {'Değişim':>9}"
    print(paint(header, DIM, color))
    print(paint("─" * len(header), DIM, color))
    for r in rows:
        pct = "yeni" if math.isnan(r["change_pct"]) else f"{r['change_pct']:+.1f}%"
        tone = GREEN if r["new"] > r["old"] else RED
        print(
            f"{str(r['label']):<{name_width}}  {r['cell']:<6}  {r['old']:>14,.2f}  "
            f"{r['new']:>14,.2f}  " + paint(f"{pct:>9}", tone, color)
        )
    print()


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="sheetgrad",
        description="Excel modelindeki bir sonucun hangi girdilere ne kadar duyarlı olduğunu hesaplar.",
    )
    parser.add_argument("dosya", help="Excel dosyası (.xlsx)")
    parser.add_argument("hucre", help="Sonuç hücresi, ör. B13")
    parser.add_argument("--sayfa", help="Sayfa adı (varsayılan: açık olan sayfa)")
    parser.add_argument("--hedef", type=float, help="Sonuç hücresinin ulaşması istenen değer")
    parser.add_argument(
        "--degistir",
        help="Hedef ararken değiştirilebilecek hücreler, virgülle: B2,B4 (varsayılan: tüm girdiler)",
    )
    args = parser.parse_args(argv)
    cells = [c.strip() for c in args.degistir.split(",")] if args.degistir else None

    try:
        model = Model.from_excel(args.dosya, args.sayfa)
        if args.hedef is not None:
            result = goal_seek(model, args.hucre, args.hedef, cells=cells)
        else:
            value, rows = model.sensitivities(args.hucre)
    except FileNotFoundError:
        print(f"Hata: dosya bulunamadı: {args.dosya}", file=sys.stderr)
        return 1
    except KeyError:
        print(f"Hata: '{args.sayfa}' adında bir sayfa yok", file=sys.stderr)
        return 1
    except (FormulaError, CircularReferenceError, ValueError) as error:
        print(f"Hata: {error}", file=sys.stderr)
        return 1

    if args.hedef is not None:
        print_goal_report(model, args.hucre, result, use_color())
        return 0 if result["reached"] else 2

    print_report(model, args.hucre, value, rows, use_color())
    return 0


if __name__ == "__main__":
    sys.exit(main())
