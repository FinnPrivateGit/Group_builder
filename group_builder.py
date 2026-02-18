import pandas as pd

file_name = "Fragebogen_Basis.xlsx"

# Erste Zeile überspringen (nur Überschriften)
df = pd.read_excel(file_name)

# Erste Spalte entfernen (Zeitstempel)
df = df.iloc[:, 1:]

# Leere Zeilen entfernen
df = df.dropna()

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

print("Anzahl Personen:", len(persons))
for person in persons:
    print(person)

