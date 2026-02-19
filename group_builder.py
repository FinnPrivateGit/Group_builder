import math
import random
import pandas as pd
import argparse
import time


"""
    0. Performance monitor
    Zählt Anzahl Operationen und Dauer
    Nur wenn das Script mit --performance ausgeführt wird
"""
parser = argparse.ArgumentParser()
parser.add_argument("--performance", action="store_true")
args = parser.parse_args()

PERFORMANCE = args.performance
OP_COUNT = 0

def count_op(n=1):
    global OP_COUNT
    if PERFORMANCE:
        OP_COUNT += n

START_TIME = time.perf_counter() if PERFORMANCE else None


"""
    1. Daten aus Excel File einlesen
"""
file_name = "Fragebogen_Basis.xlsx"
#file_name = "Fragebogen_Basis_30_Test.xlsx" # Performance testen, weil ich neugierig bin
#file_name = "Fragebogen_Basis_100_Test.xlsx" # Performance testen, weil ich neugierig bin

df = pd.read_excel(file_name)
df = df.iloc[:, 1:] # erste Spalte (Zeit) entfernen
df = df.dropna() # leere Zeilen entfernen

persons = []
for _, row in df.iterrows():
    name = row.iloc[0]              # zweite Spalte = Name
    answers = row.iloc[1:]        # restliche Spalten = Antworten

    # erste 5 Antworten = Likert
    likert = answers.iloc[:5].astype(int).tolist()

    # letzte Antwort = Kategorie
    category = answers.iloc[5]

    persons.append({
        "name": name,
        "likert": likert,
        "kategorie": category
    })

# sanity check
if len(persons) < 20:
    raise ValueError("Fehler: Es müssen mindestens 20 Personen vorhanden sein, um Gruppen sinnvoll zu bilden.")


"""
    2. Distanz zweier Personen berechnen
    - Likert: Summe der absoluten Differenzen (5 Fragen)
    - Kategorie: +4 falls unterschiedlich, sonst +0
"""
def distanz(p1: dict, p2: dict) -> int:
    count_op()

    # Likert-Distanz (Manhattan)
    d = sum(abs(a - b) for a, b in zip(p1["likert"], p2["likert"]))
    count_op(len(p1["likert"]))  # Anzahl Likert-Vergleiche

    # Kategorie-Strafe
    if p1["kategorie"] != p2["kategorie"]:
        count_op()
        d += 4

    return d


"""
    3. Distanzmatrix berechnen
"""
def build_dist_matrix(persons: list[dict]) -> list[list[int]]:
    n = len(persons)
    m = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            count_op()
            d = distanz(persons[i], persons[j])
            m[i][j] = d
            m[j][i] = d
    return m

dist_matrix = build_dist_matrix(persons)


"""
    4. Bewertungsfunktion
"""
def group_cost(group: list[int], dist_matrix: list[list[int]]) -> int:
    """Summe aller Paar-Distanzen innerhalb der Gruppe"""
    cost = 0
    for a_i in range(len(group)):
        for b_i in range(a_i + 1, len(group)):
            count_op()
            a = group[a_i]
            b = group[b_i]
            cost += dist_matrix[a][b]
    return cost


def total_cost(groups: list[list[int]], dist_matrix: list[list[int]]) -> int:
    return sum(group_cost(g, dist_matrix) for g in groups)


def cost_if_added(group: list[int], person_idx: int, dist_matrix: list[list[int]]) -> int:
    """Zusatzkosten, wenn person_idx zur Gruppe hinzugefügt wird"""
    count_op(len(group))
    return sum(dist_matrix[person_idx][x] for x in group)


"""
    5. Gruppierung:
    Greedy approach + rebalancing + optimization-swaps
"""
def choose_k(n: int, target_size: int = 5) -> int:
    return max(1, round(n / target_size))


def pick_seeds_farthest(n: int, k: int, dist_matrix: list[list[int]]) -> list[int]:
    """
    Seeds wählen: starte mit einem zufälligen Seed, dann jeweils den Punkt,
    der maximal weit von den bereits gewählten Seeds entfernt ist
    """
    all_idx = list(range(n))
    first = random.choice(all_idx)
    seeds = [first]

    while len(seeds) < k:
        best = None
        best_score = -1
        for i in all_idx:
            count_op()

            if i in seeds:
                continue
            # Abstand zu nächstem Seed maximieren (maximin)
            score = min(dist_matrix[i][s] for s in seeds)
            if score > best_score:
                best_score = score
                best = i
        seeds.append(best)
    return seeds


def greedy_fill_groups(n: int, k: int, min_size: int, max_size: int, dist_matrix: list[list[int]]) -> list[list[int]]:
    """
    1) Seeds wählen
    2) Restliche Personen nacheinander zuordnen (immer zur Gruppe, wo die Zusatzkosten minimal sind)
    """
    seeds = pick_seeds_farthest(n, k, dist_matrix)

    groups = [[s] for s in seeds]
    unassigned = [i for i in range(n) if i not in seeds]

    def avg_dist_to_all(i: int) -> float:
        return sum(dist_matrix[i][j] for j in range(n) if j != i) / (n - 1)

    unassigned.sort(key=avg_dist_to_all, reverse=True)

    for p in unassigned:
        best_g = None
        best_delta = math.inf

        for gi, g in enumerate(groups):
            count_op()

            if len(g) >= max_size:
                continue
            delta = cost_if_added(g, p, dist_matrix)
            if delta < best_delta:
                best_delta = delta
                best_g = gi

        # Falls alle Gruppen voll wären, an die "am wenigsten schlechte" anhängen
        if best_g is None:
            best_g = min(range(len(groups)), key=lambda gi: cost_if_added(groups[gi], p, dist_matrix))

        groups[best_g].append(p)

    return groups


def rebalance_to_min_size(groups: list[list[int]], min_size: int, max_size: int, dist_matrix: list[list[int]]) -> list[list[int]]:
    """
    Sicherstellen, dass alle Gruppen < min_size ist.
    Idee: Bei Gruppen > min_size den am "billigsten" abgebbaren Kandidat rausnehmen
    und in eine kleine Gruppe reintun (wo er auch hinpasst)
    """
    def removal_penalty(g: list[int], idx_in_group: int) -> int:
        p = g[idx_in_group]
        return sum(dist_matrix[p][x] for x in g if x != p)

    changed = True
    while changed:
        changed = False
        small = [gi for gi, g in enumerate(groups) if len(g) < min_size]
        if not small:
            break

        for gi_small in small:
            donors = [gi for gi, g in enumerate(groups) if len(g) > min_size]
            if not donors:
                break

            best_move = None
            best_delta = math.inf

            for gi_donor in donors:
                donor = groups[gi_donor]
                for idx_in_donor in range(len(donor)):
                    count_op()

                    p = donor[idx_in_donor]

                    if len(donor) - 1 < min_size:
                        continue
                    if len(groups[gi_small]) + 1 > max_size:
                        continue

                    add_cost = cost_if_added(groups[gi_small], p, dist_matrix)
                    remove_cost = removal_penalty(donor, idx_in_donor)
                    delta = add_cost - remove_cost

                    if delta < best_delta:
                        best_delta = delta
                        best_move = (gi_donor, idx_in_donor, p)

            if best_move is None:
                continue

            gi_donor, idx_in_donor, p = best_move
            groups[gi_donor].pop(idx_in_donor)
            groups[gi_small].append(p)
            changed = True

    return groups


def improve_by_swaps(groups: list[list[int]], min_size: int, max_size: int, dist_matrix: list[list[int]], max_iters: int = 5000) -> list[list[int]]:
    """
    Lokale Verbesserung: tausche Personen zwischen Gruppen, wenn sich die Gesamtkosten reduzieren
    """
    def try_swap(g1i: int, a_idx: int, g2i: int, b_idx: int) -> int:
        """Gibt neue Gesamtkosten der beiden Gruppen minus alte Kosten zurück (delta)"""
        g1 = groups[g1i]
        g2 = groups[g2i]
        a = g1[a_idx]
        b = g2[b_idx]

        old = group_cost(g1, dist_matrix) + group_cost(g2, dist_matrix)

        # swap simulieren
        g1_new = g1.copy()
        g2_new = g2.copy()
        g1_new[a_idx] = b
        g2_new[b_idx] = a

        new = group_cost(g1_new, dist_matrix) + group_cost(g2_new, dist_matrix)
        return new - old

    improved = True
    it = 0
    while improved and it < max_iters:
        improved = False
        it += 1

        # alle Gruppenpaare probieren
        for g1i in range(len(groups)):
            for g2i in range(g1i + 1, len(groups)):
                g1 = groups[g1i]
                g2 = groups[g2i]

                for a_idx in range(len(g1)):
                    for b_idx in range(len(g2)):
                        count_op()

                        delta = try_swap(g1i, a_idx, g2i, b_idx)
                        if delta < 0:
                            # swap ausführen
                            a = groups[g1i][a_idx]
                            b = groups[g2i][b_idx]
                            groups[g1i][a_idx] = b
                            groups[g2i][b_idx] = a
                            improved = True
                            break
                    if improved:
                        break
                if improved:
                    break
            if improved:
                break

    return groups


def make_groups(persons: list[dict],
                dist_matrix: list[list[int]],
                min_size: int = 4,
                max_size: int = 6,
                target_size: int = 5,
                random_seed: int = 42,
                restarts: int = 30) -> list[list[int]]:
    random.seed(random_seed)
    n = len(persons)
    k = choose_k(n, target_size=target_size)

    best_groups = None
    best_cost = math.inf

    for r in range(restarts):
        count_op()

        # kleine Variation pro restart
        random.seed(random_seed + r)

        groups = greedy_fill_groups(n, k, min_size, max_size, dist_matrix)
        groups = rebalance_to_min_size(groups, min_size, max_size, dist_matrix)
        groups = improve_by_swaps(groups, min_size, max_size, dist_matrix, max_iters=5000)

        # falls Gruppen out of bounds sind, trotzdem bewerten
        c = total_cost(groups, dist_matrix)
        if c < best_cost:
            best_cost = c
            best_groups = groups

    return best_groups


"""
    6. Gruppen berechnen & printen
"""
groups_idx = make_groups(
    persons,
    dist_matrix,
    min_size=4,
    max_size=6,
    target_size=5,
    random_seed=42,
    restarts=50
)

print("\n--------- RESULTAT ---------")
print("Gesamtkosten:", total_cost(groups_idx, dist_matrix))
for gi, g in enumerate(groups_idx, start=1):
    names = [persons[i]["name"] for i in g]
    cats = [persons[i]["kategorie"] for i in g]
    print(f"\nGruppe {gi} (n={len(g)}, kosten={group_cost(g, dist_matrix)}):")
    for n, c in zip(names, cats):
        print(f"  - {n}  ({c})")


if PERFORMANCE:
    elapsed = time.perf_counter() - START_TIME
    print("\n--------- PERFORMANCE ---------")
    print("Anzahl Operationen:", OP_COUNT)
    print(f"Laufzeit gesamt: {elapsed:.3f} Sekunden")
