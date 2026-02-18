import pandas as pd

file_name = "Fragebogen_Basis.xlsx"

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


def distanz(p1: dict, p2: dict) -> int:
    """
    Distanz nach diesem System:
    - Likert: Summe der absoluten Differenzen (5 Fragen)
    - Kategorie: +3 falls unterschiedlich, sonst +0
    """
    # Likert-Distanz (Manhattan)
    d = sum(abs(a - b) for a, b in zip(p1["likert"], p2["likert"]))

    # Kategorie-Strafe
    if p1["kategorie"] != p2["kategorie"]:
        d += 3

    return d

