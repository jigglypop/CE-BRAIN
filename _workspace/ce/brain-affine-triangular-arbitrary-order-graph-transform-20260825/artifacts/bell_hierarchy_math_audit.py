from math import factorial


def terms(order: int):
    out = []
    def visit(j, remaining, reverse):
        if j == 0:
            if remaining == 0:
                m = tuple(reversed(reverse))
                den = 1
                for k, count in enumerate(m, 1):
                    den *= factorial(k) ** count * factorial(count)
                out.append((m, factorial(order) // den))
            return
        for count in range(remaining // j, -1, -1):
            visit(j - 1, remaining - count * j, reverse + [count])
    visit(order, order, [])
    return out


assert len(terms(4)) == 5 and sum(c for _, c in terms(4)) == 15
assert len(terms(5)) == 7 and sum(c for _, c in terms(5)) == 52
assert len(terms(6)) == 11 and sum(c for _, c in terms(6)) == 203
print("OK: exact Bell hierarchy partition audit")
