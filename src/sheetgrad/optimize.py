import math


def goal_seek(model, output_ref, target, cells=None, max_steps=2000, tolerance=1e-6, max_move=0.02):
    start_output, rows = model.sensitivities(output_ref)
    base = {row["cell"]: row["value"] for row in rows}

    cells = [c.upper() for c in cells] if cells else list(base)
    unknown = [c for c in cells if c not in base]
    if unknown:
        raise ValueError(f"Bu hücreler sonucu etkileyen girdiler değil: {', '.join(unknown)}")

    # Her girdiyi kendi ölçeğinde hareket ettiriyoruz: u = 0.1, "%10 artır" demek.
    scale = {c: abs(base[c]) if base[c] != 0 else 1.0 for c in cells}
    norm = max(abs(target), abs(start_output), 1.0)

    def to_values(u):
        values = dict(base)
        for c in cells:
            values[c] = base[c] + scale[c] * u[c]
        return values

    def project(u):
        # Başlangıçta negatif olmayan bir girdi negatife düşmesin (fiyat, adet, bütçe...)
        for c in cells:
            if base[c] >= 0 and base[c] + scale[c] * u[c] < 0:
                u[c] = -base[c] / scale[c]
        return u

    def evaluate(u):
        output = model.run(output_ref, to_values(u))
        loss = ((output - target) / norm) ** 2
        loss.backward()
        grad = {c: model.inputs[c].grad * scale[c] for c in cells}
        return loss.data, output.data, grad

    u = {c: 0.0 for c in cells}
    loss, output, grad = evaluate(u)
    step_size = 0.1
    steps = 0

    while steps < max_steps and abs(output - target) > tolerance * norm:
        steps += 1
        improved = False
        while step_size > 1e-12:
            move = {c: step_size * grad[c] for c in cells}
            largest = max(abs(m) for m in move.values())
            if largest > max_move:
                # Tek adımda hiçbir girdi kendi ölçeğinin %2'sinden fazla oynamasın
                move = {c: m * max_move / largest for c, m in move.items()}
            candidate = project({c: u[c] - move[c] for c in cells})
            new_loss, new_output, new_grad = evaluate(candidate)
            if new_loss < loss:
                u, loss, output, grad = candidate, new_loss, new_output, new_grad
                step_size *= 1.5
                improved = True
                break
            step_size /= 2
        if not improved:
            break

    final = to_values(u)
    changes = []
    for c in cells:
        old, new = base[c], final[c]
        if not math.isclose(old, new, rel_tol=1e-9, abs_tol=1e-9):
            changes.append({
                "cell": c,
                "label": model.label(c),
                "old": old,
                "new": new,
                "change_pct": (new - old) / old * 100 if old != 0 else math.nan,
            })
    changes.sort(key=lambda row: abs(row["new"] - row["old"]) / scale[row["cell"]], reverse=True)

    return {
        "start": start_output,
        "output": output,
        "target": target,
        "reached": abs(output - target) <= tolerance * norm,
        "steps": steps,
        "changes": changes,
    }
