# Gruppenbildung nach Interessen (Basiskurs)

## Zusammenfassung

Dieses kleine Projekt dient zur automatischen Gruppenbildung für einen
Basiskurs, den ich leite.\
Ziel ist es, Teilnehmerinnen und Teilnehmer für einen gemeinsamen
Gruppenausflug so einzuteilen, dass Personen mit möglichst ähnlichen
Interessen zusammen in einer Gruppe sind.

Die Gruppen werden anhand eines Fragebogens erstellt, der folgende Dinge
erfasst:

-   5 Likert-Skalen (z.B. Präferenzen oder Verhaltensweisen)
-   eine Multiple-Choice-Kategorie: *"Was beschreibt dich am besten?"*

Der Algorithmus versucht Gruppen von **4-6 Personen** zu bilden, sodass
die Unterschiede innerhalb einer Gruppe möglichst klein sind.

Das Projekt ist bewusst "einfach" gehalten und soll nachvollziehbar und
transparent bleiben.

------------------------------------------------------------------------

# Wie der Code funktioniert

Er besteht aus sieben Schritten:

    0. Performance monitoring
    1. Daten einlesen
    2. Distanz zwischen Personen berechnen
    3. Distanzmatrix berechnen
    4. Gruppen bewerten
    5. Gruppen optimieren
    6. Ergebnis ausgeben

------------------------------------------------------------------------

## 0. Performance Monitoring (optional)

Das Script enthält einen optionalen Performance-Monitor zur Analyse der Laufzeit und der Anzahl ausgeführter Berechnungen.

Dieser dient primär zur Evaluation des Algorithmus und zur Untersuchung der Skalierbarkeit bei steigender Teilnehmerzahl (und weil ich Lust darauf hatte).

### Aktivierung

Der Performance-Monitor wird nur aktiviert, wenn das Script mit folgendem Flag gestartet wird:
```
    python .\group_builder.py --performance
```


Ohne dieses Flag läuft das Programm normal ohne zusätzliche Messungen.

---

### Gemessene Metriken

Der Performance-Monitor misst zwei Kennzahlen:

#### Anzahl Operationen

Zählt die wichtigsten algorithmischen Berechnungen während der Ausführung.

Dies dient als approximatives Mass für die algorithmische Komplexität.

---

#### Gesamtlaufzeit

Misst die gesamte Ausführungsdauer des Scripts in Sekunden.

Die Messung startet beim Programmstart und endet nach der Gruppenausgabe.


---

### Warum Performance Monitoring?

Das Performance Monitoring ermöglicht:

- Analyse der Skalierbarkeit bei unterschiedlichen Teilnehmerzahlen
- Vergleich verschiedener Parameter oder Gewichtungen
- Bewertung von Optimierungsschritten
- Verständnis der Laufzeitkomplexität des heuristischen Ansatzes

Die Messung ist optional implementiert, damit im normalen Betrieb keine zusätzliche Rechenzeit entsteht.


------------------------------------------------------------------------

## 1. Daten aus Excel einlesen

Der Code liest ein Excel-File (`Fragebogen_Basis.xlsx`) ein, das im
gleichen Ordner liegen muss.

### Erwartetes Format der Excel-Datei

  ------------------------------------------------------------------------------------
  Zeitstempel   Name     Likert1   Likert2   Likert3   Likert4   Likert5   Kategorie
  ------------- -------- --------- --------- --------- --------- --------- -----------
  ...           ...      1-5       1-5       1-5       1-5       1-5       Text

  ------------------------------------------------------------------------------------

-   erste Spalte → Zeitstempel (wird ignoriert)
-   zweite Spalte → Name (wird gespeichert)
-   nächste 5 Spalten → Likert-Werte (1--5)
-   letzte Spalte → Kategorie

### Was passiert im Code

-   Zeitstempel wird entfernt
-   leere Zeilen werden entfernt
-   jede Person wird als Objekt gespeichert:

``` python
{
  "name": "Anna",
  "likert": [3,4,2,5,1],
  "kategorie": "Kreativ"
}
```

Zusätzlich gibt es einen **Sanity-Check**: - mindestens 20 Personen
erforderlich - sonst wird ein Fehler ausgelöst

**Warum?** Bei zu wenigen Personen können keine sinnvollen Gruppen von
4-6 Personen gebildet werden.

------------------------------------------------------------------------

## 2. Distanz zwischen zwei Personen berechnen

Der wichtigste Teil des Projekts ist die Definition von "Ähnlichkeit".

### Distanzdefinition

Die Distanz zwischen zwei Personen besteht aus:

### Likert-Differenz

Summe der absoluten Unterschiede:

    |a1 - b1| + |a2 - b2| + ... + |a5 - b5|

→ misst Unterschied in Präferenzen.

### Kategorie-Strafe

Wenn die Kategorie unterschiedlich ist:

    +4 Punkte

→ sorgt dafür, dass gleiche Selbstbeschreibung stärker gruppiert wird.

### Warum diese Methode?

-   sehr einfach erklärbar
-   robust gegen Ausreisser
-   transparent für Teilnehmende
-   Gewichtung zwischen Skalen und Kategorie kontrollierbar

------------------------------------------------------------------------

## 3. Distanzmatrix berechnen

Der Code berechnet die Distanz zwischen **allen Personenpaaren**.

Ergebnis:

    dist_matrix[i][j] = Distanz zwischen Person i und j

### Warum eine Distanzmatrix?

-   schnelle Vergleiche zwischen Personen
-   effizientere Gruppierung
-   Grundlage für Optimierungsschritte
-   erleichtert Bewertung von Gruppen

Bei 30 Personen entstehen z.B. 435 Paarvergleiche.

------------------------------------------------------------------------

## 4. Bewertungsfunktionen für Gruppen

Damit der Algorithmus weiss, was eine "gute" Gruppe ist, wird eine
Kostenfunktion definiert.

### Gruppenkosten

Eine Gruppe ist gut, wenn die Teilnehmer ähnlich sind:

    Kosten = Summe aller Paar-Distanzen innerhalb der Gruppe

→ kleine Kosten = gute Gruppe.

Zusätzlich:

-   Gesamtkosten aller Gruppen werden berechnet
-   Zusatzkosten beim Hinzufügen einer Person werden geschätzt

Diese Funktionen ermöglichen später Optimierungsschritte.

------------------------------------------------------------------------

## 5. Gruppierung (Greedy approach + rebalancing + Optimierung)

Dies ist der Kern des Algorithmus.

Da die optimale Gruppierung ein komplexes kombinatorisches Problem ist,
wird eine heuristische Lösung verwendet.

### Schritt 1 --- Anzahl Gruppen bestimmen

Zielgrösse ≈ 5 Personen pro Gruppe:

    k ≈ n / 5

### Schritt 2 --- Startpunkte (Seeds) wählen

-   erste Person zufällig
-   weitere Seeds möglichst weit entfernt von bestehenden Seeds

**Warum?** → verhindert, dass mehrere Gruppen denselben "Typ" starten.

### Schritt 3 --- Greedy Zuweisung

Alle übrigen Personen werden der Gruppe zugeteilt, in die sie am besten
passen:

    minimale Zusatzkosten

### Schritt 4 --- Rebalancing

Sicherstellen, dass:

-   keine Gruppe \< 4 Personen
-   keine Gruppe \> 6 Personen

Falls nötig werden Personen zwischen Gruppen verschoben.

### Schritt 5 --- Lokale Verbesserung (Swaps)

Der Algorithmus versucht:

-   Personen zwischen Gruppen zu tauschen
-   wenn dadurch Gesamtkosten sinken

Dies verbessert die Qualität der Lösung deutlich.

### Schritt 6 --- Mehrere Neustarts

Der gesamte Prozess wird mehrfach gestartet.

Warum?

-   vermeidet schlechte lokale Lösungen
-   erhöht Robustheit
-   bessere Gruppenqualität

Die beste Lösung wird ausgewählt.

------------------------------------------------------------------------

## 6. Gruppen berechnen und ausgeben

Am Ende gibt der Code folgendes aus:

-   Gesamtkosten der Lösung
-   Gruppengrösse
-   Mitglieder jeder Gruppe
-   Kategorie jeder Person

Beispiel:

    Gruppe 1 (n=5, kosten=12):
      - Anna (Kreativ)
      - Ben (Sportlich)

------------------------------------------------------------------------

# Eigenschaften des Ansatzes

## Vorteile

-   einfach verständlich
-   transparent
-   deterministisch reproduzierbar (mit Seed)
-   flexibel anpassbare Gewichtung
-   garantiert Gruppengrösse 4-6
-   robust für kleine Datensätze (20-40 Personen)

## Limitationen

-   heuristische Lösung, nicht garantiert global optimal
-   Qualität hängt von Distanzdefinition ab
-   Kategoriegewicht muss manuell gewählt werden

------------------------------------------------------------------------

# Voraussetzungen

    Python 3.10+
    pandas
    openpyxl

Installation:

    pip install pandas openpyxl

------------------------------------------------------------------------

# Ziel des Projekts

Das Projekt priorisiert:

-   Verständlichkeit über mathematische Perfektion
-   praktische Anwendbarkeit
-   faire Gruppeneinteilung
-   einfache Anpassbarkeit für zukünftige Kurse
