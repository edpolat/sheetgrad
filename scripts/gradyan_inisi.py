from sheetgrad.engine import Value

print("--- Deney 1: türevi sıfırlamadan")
x = Value(10.0)
for adim in range(5):
    y = (x - 3) ** 2
    y.backward()
    x.data -= 0.1 * x.grad
    print(f"{adim + 1}: x={x.data:.4f}  grad={x.grad:.4f}")

print("\n--- Deney 2: türevi her adımda sıfırlayarak")
x = Value(10.0)
for adim in range(20):
    x.grad = 0.0
    y = (x - 3) ** 2
    y.backward()
    x.data -= 0.1 * x.grad
    print(f"{adim + 1}: x={x.data:.4f}  y={y.data:.6f}")

print("\n--- Deney 3: kârı 2000 TL yapacak fiyatı bul")
fiyat = Value(100.0)
for adim in range(10):
    fiyat.grad = 0.0
    kar = fiyat * 50 - 60 * 50 - 500
    hata = (kar - 2000) ** 2
    hata.backward()
    fiyat.data -= 0.0001 * fiyat.grad
    print(f"{adim + 1}: kar={kar.data:.2f}  →  yeni fiyat={fiyat.data:.4f}")