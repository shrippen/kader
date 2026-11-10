# Bericht: Rahmenkanten je Rolle

Stand 2026-11-10, Branch `frame-edges` (nicht committet). Grundlage `main` bei `cd6afeb` (0.4.0).
Alle Zahlen selbst gemessen, bei 2000 px langer Kante.

**Kurzfassung.** Das bisherige Kriterium (nur Breite und Höhe) hat Lagefehler nicht gesehen: von 198 „Treffern“ auf
den Handcrops lagen bei 89 nicht alle vier Kanten näher als 25 px, Film 31 galt mit 12/12 als getroffen und lag im Median
133 px daneben. Gemessen an den Kanten war die Erkennung bei 52 % (Handcrops) und 67 % (darktable-Crops), von den Grünen
stimmten 70 % und 79 %. Eine neue Erkennung (`frame_edges.py`) misst die Rahmenkanten direkt und summiert sie über die
Rolle: 80 % und 81 %, Grüne 98 % und 96 % richtig, bei mehr Grünen und halber Laufzeit.

## 1. Ergebnis

Treffer = alle vier Kanten näher als 25 px an der Referenz. darktable-Crops ohne gedrehte Referenzen (Abschnitt 3).

| | Handcrops (209) alt | neu | darktable (1164) alt | neu |
| --- | --- | --- | --- | --- |
| Kanten < 15 px | 78 (37 %) | **156 (75 %)** | 449 (39 %) | **875 (75 %)** |
| Kanten < 25 px | 109 (52 %) | **167 (80 %)** | 779 (67 %) | **945 (81 %)** |
| Kanten < 40 px | 136 (65 %) | **173 (83 %)** | 858 (74 %) | **990 (85 %)** |
| nur Größe < 60 px (altes Kriterium) | 198 | 191 | 1028 | 1062 |
| grün (≥ 0,5) | 138 | 146 | 795 | 903 |
| davon Kanten < 25 px | 70 % | **98 %** | 79 % | **96 %** |
| davon Kanten < 40 px | 78 % | **99 %** | 84 % | **97 %** |

Alle 1662 darktable-Crops (mit gedrehten): Kanten < 25 px 1090 → 1328, grün 1168 → 1328, davon richtig 79 % → 93 %.
Laufzeit über die 3666 Bilder der 62 Rollen: 149 s → 58 s (24 Kerne).

Der Rückgang beim alten Kriterium auf den Handcrops (198 → 191) ist Film 34: verschleierte Negative ohne sichtbare
Oberkante, Konfidenz dort durchweg unter 0,3.

Einzelne Rollen (Kanten < 25 px / grün / falsch grün):

| Rolle | Bilder | alt | neu |
| --- | --- | --- | --- |
| 07.07.2014 – Leipzig (ohne Takt) | 34 | 0 / 0 / 0 | 27 / 24 / 1 |
| Film 14 | 32 | 9 / 19 / 14 | 28 / 30 / 2 |
| Film 16 | 23 | 2 / 18 / 16 | 19 / 21 / 2 |
| Film 13 | 67 | 37 / 40 / 10 | 56 / 54 / 3 |
| Film 31 (quadratisch) | 12 | 2 / 1 / 0 | 6 / 2 / 0 |
| Film 33 | 37 | 7 / 37 / 30 | 37 / 35 / 0 |
| Film 32 | 9 | 0 / 4 / 4 | 9 / 8 / 0 |
| Küste 1, Küste 2, Freibad 3 (Rahmen füllt die Datei) | 19 | 2 / 0 / 0 | 10 / 0 / 0 |

Schlechter: *Viktorianisches Wasser* 9 → 0 (Studio vor schwarzem Tuch, kein Takt: die Seitenkanten sind nicht im Bild,
die Rolle findet stattdessen den Vorhang; keine Grünen). Sonst höchstens 3 Bilder je Rolle.

## 2. Was sich geändert hat

Bisher: vier Kandidaten-Strategien je Bild, Größe aus Takt × Konvention (36,2 × 24,1 mm), Lage per Mittelwert-Sprung
± 10 px. Die Größe war damit eine Annahme, keine Messung.

Neu (`frame_edges.py`, 35-mm-Rollen):

1. **Kantenevidenz** je Bild und Position: mittlerer gedeckelter Sprung dunkel → hell über 24 Abschnitte der Kante.
   Bildinhalt springt in einzelnen Abschnitten, die Rahmenkante in allen. Gamma 0,5 hebt Sprünge im Dunkeln.
2. **Rahmengröße der Rolle**: Maximum der über alle Bilder summierten Kantenpaare, beide Achsen gemeinsam, unter
   Seitenverhältnis 1,48–1,525 (oder quadratisch) und, mit Takt, 35,2–37,8 mm.
3. **Lage je Bild**: das Kantenpaar dieser Größe; Kanten auf den steilsten Punkt gelegt. Eine ungesehene Kante liegt um
   die Rollengröße neben der gesehenen, ohne jede Kante gilt die übliche Lage der Rolle. Ein Bild darf bis 4 % von der
   Rollengröße abweichen, wenn beide Kanten klar sind (Film 12 enthält Bilder in anderem Maßstab).
4. **Schräglage**: Evidenz wird unter −2 … +2 Grad gelesen, der schärfste Winkel gilt.
5. **Konfidenz** = schwächste der vier Kanten. Geprüft gegen Mittelwerte je Achse: AUC 0,93 gegen 0,85.
6. **Crop** 0,5 % der langen Rahmenkante innerhalb der Kante; mit gelernter Konvention und Takt deren halbe Differenz
   zum gemessenen Bildfenster.

Rollen ohne Takt und ohne Kantenpaare sowie andere Formate laufen wie bisher (Kandidaten-Strategien, Film-Konsens).

## 3. Befunde nebenbei

* **Die „zwei Crop-Gewohnheiten“ aus dem Bericht vom 22.09. sind zwei Kameras.** Gemessene Bildfenster: Rollen
  „Film N“ 36,7–36,9 × 24,3–24,5 mm, datierte Rollen 36,1–36,3 × 24,2–24,4 mm. Der Rest von 1 % war Physik.
* **Gedrehte darktable-Referenzen sind keine Rahmen.** Der Crop ist dort um Kantenlänge × tan(Winkel) kleiner als der
  Rahmen (9 px bei 0,3 Grad, 32 px bei 0,6–1 Grad): im gedrehten Bild eingepasst. Für die Güte zählt
  `tools/eval_darktable_crops.py --no-rotated`.
* **Konvention**: Handcrops liegen im Median 2 px außerhalb der gemessenen Kante, darktable-Crops 10 px innerhalb.
* **Dunkle Bilder**: in *Zwiebelmarkt*, Film 10, Film 15 liegen Filmrand und Bild im JPEG beide bei Grauwert 0–1.
  Dort steht keine Kante in der Datei. Die Erkennung meldet das als niedrige Konfidenz; holen ließe sich das nur mit
  einem helleren Export für die Erkennung.

## 4. Geprüft und nicht übernommen

| Idee | Ergebnis |
| --- | --- |
| Perforationsphase als Lageanker (Rahmen liegt je Rolle fest zum Lochraster) | hält bei 23 von 45 Rollen (mit Takt und mindestens 4 sicheren Bildern) auf ±6 % des Takts; +5 von 1662 Bildern, weil dunkle Rollen zu wenige sichere Bilder zum Einmessen haben |
| Farbkanäle statt Grau | kein Gewinn |
| Alte Erkennung als Rückfall bei niedriger Konfidenz | dort gleich schlecht (31 gegen 24 von 147) |
| Dunkler Rand um die Datei für angeschnittene Rahmen | der Halter am Dateirand wird zur stärksten Kante; stattdessen feste schwache Evidenz am Dateirand |

## 5. Offen

* Landing Page (`docs/index.html`, Abschnitt Erkennung) beschreibt noch die vier Strategien; gehört zum Release.
* `tests/ui_smoke.py` (Playwright) nicht gelaufen.
* Hellerer Export für die Erkennung bei dunklen Rollen (Abschnitt 3).
* Mittelformat: keine Testdaten; läuft über den alten Weg.
* Halbformat (18 × 24 mm) kennt `FORMATS` nicht.
* `measure_skew` (Web-UI) misst die Schräglage weiter selbst; `frame_edges` kennt sie jetzt auch (`tilt_deg`).

## 6. Nachmessen

```
tools/eval.py                                  # Handcrops, Baseline 167/209
tools/eval_darktable_crops.py --no-rotated     # 945/1164
.venv/bin/python -m unittest discover -s tests # 203 Tests
```

## Nachtrag: Erkennungsbild aus dem RAW (dunkle Rollen)

Versuch auf Zwiebelmarkt, Film 10 und Film 15 (91 NEFs unter `Testphotos raw/`). Das Erkennungsbild kommt
direkt aus dem RAW statt aus dem bearbeiteten JPEG: mit rawpy linear entwickelt (halbe Auflösung), Grauwert
logarithmiert, beim Negativ invertiert, dann 0,4 Dichtestufen ab dem Filmrand (5. Perzentil) auf 0–255 gestreckt.
Ausrichtung und Größe wie der darktable-Export. Sonst unveränderte Erkennung.

Referenz: `review_data/reviews_raw.json`, von Hand auf das Bildfeld gesetzt, auf den aufgehellten Bildern.
57 Bilder mit Referenz, 20 als Problemfall markiert (keine Kante auf einer Achse) und nicht gewertet.

| | JPEG (bearbeitet) | RAW (Erkennungsbild) |
| --- | --- | --- |
| alle vier Kanten < 25 px | 32 von 57 | 47 von 57 |
| Zwiebelmarkt (17) | 11 | 16 |
| Film 10 (29) | 21 | 26 |
| Film 15 (11) | 0 | 5 |
| grün | 35 | 43 |
| davon Kanten < 25 px | 29 (83 %) | 41 (95 %) |

Einschränkungen:

- Die Referenzen wurden auf den RAW-Bildern gesetzt, mit dem Crop des RAW-Laufs als Ausgangslage. Keine wurde
  unverändert übernommen, eine Neigung zum RAW-Lauf ist trotzdem möglich.
- Die Streckung ist empfindlich: 0,25 und 0,15 Dichtestufen waren gegen die alten darktable-Crops deutlich
  schlechter (Dias brechen ein). Gegen die neuen Referenzen ist nur 0,4 gemessen.
- Negativ oder Dia war von Hand gesetzt.
- Film 15 bleibt schwach (5 von 11, zwei von fünf Grünen falsch); das Bildfeld reicht dort bis in die Perforation.
- Die darktable-Crops dieser drei Rollen sind Bildausschnitte, keine Bildfelder, und taugen hier nicht als Referenz.

### Eingebaut

`companion/rawdetect.py` rechnet das Erkennungsbild bei RAW-Eingabe selbst (braucht `rawpy`). Lage und
Seitenverhältnis kommen vom Export (acht Lagen, Korrelation der Bildmitte), die Polung je Rolle aus der Kantenevidenz
einer Stichprobe. Die Ergebnisse werden auf den Export umgerechnet. Ein Bild, dessen Export einen anderen Ausschnitt
zeigt (Seitenverhältnis weicht um mehr als 0,5 % ab), wird auf dem Export gemessen.

Lauf durch die echte Analyse (Ordner mit NEFs und Sidecars, darktable-cli als Konverter, ohne gespeicherte
Crop-Konvention): 46 von 57 mit allen vier Kanten < 25 px, 44 grün, davon 41 richtig. Alle 91 Lagen und alle drei
Polungen stimmen. Bei Film 10 laufen 3 von 39 Bildern über den Export.

Dabei gefunden und behoben: `frame_edges.detect` verwarf alle Bilder einer Rolle, deren Arbeitsgröße von der des
ersten Bilds abwich (hier: Exporte, die im RAW-Entwickler gedreht waren), ohne Ergebnis. Solche Bilder bilden jetzt
eine eigene Gruppe.

Offen: Die Grenzen für Lage und Ausschnitt sind nur an diesen 91 Bildern einer Kamera gesetzt. Der Weg über das
darktable-Plugin ist nicht im laufenden darktable geprüft.

## Nachtrag: Schräglage aus der Perforation

Frage: Lässt sich die Schräglage zuverlässiger an der Perforation messen als an den Rahmenkanten? Referenz: die
Drehung aus darktable (`rotation` in `review_data/darktable_crops.json`), 498 Bilder aus 33 Rollen, Median 0,32°.
Die RAWs wurden nur gelesen.

**Auf den Exporten** (drei Ansätze: Schwerpunkt der Lochkanten-Energie, Taktfrequenz je Zeile mit langen und mit
kurzen Fenstern): unbrauchbar, kein Zusammenhang mit der Referenz. Die Löcher heben sich dort kaum vom Filmrand ab.

**Im RAW** (linear, log): Der Filmhalter deckt die Löcher bis auf einen schmalen Rest ab (6–35 px hoch bei 4140 px
Bildbreite). Die Kante dieses Rests zum Bild hin ist die Lochkante im Film, die andere gehört zum Halter. Messung:
Schwelle mittig zwischen Lochhelligkeit (99,8. Perzentil) und häufigstem Wert des Randstreifens (äußere 28 %),
zusammenhängende helle Flecken gleicher Breite im Lochabstand, je Loch die innere Kante im mittleren Teil
(Schwelle zwischen zwei Zeilen interpoliert), Gerade durch die Kanten einer Reihe. Restfehler der Geraden 1,3 px,
im Median 7 Löcher je Reihe; zwei Reihen eines Bilds weichen im Median 0,11° voneinander ab.

Befund: Die Lochreihe läuft nicht parallel zum Bildfeld. Je Rolle liegt die Drehung aus darktable um einen festen
Betrag neben dem Winkel der Lochreihe (−0,1° bis +0,4°, bei den Rollen „Film N“ meist +0,1° bis +0,4°), mit
kleiner Streuung in der Rolle (0,04–0,10°). Der Winkel der Lochreihe allein trifft die Referenz darum schlecht
(Median 0,25°).

| Verfahren | Bilder | Fehler Median | < 0,1° | < 0,2° | < 0,3° |
| --- | --- | --- | --- | --- | --- |
| Kanten auf dem Export (bisher, am Referenz-Crop) | 484 | 0,13° | 38 % | 64 % | 80 % |
| Kanten auf dem RAW-Bild | 443 | 0,14° | 37 % | 61 % | 80 % |
| Lochreihe + Versatz der Rolle aus den Kanten | 331 | 0,12° | 45 % | 69 % | 82 % |
| Kanten, dieselben 323 Bilder | 323 | 0,14° | 38 % | 64 % | 80 % |
| Lochreihe + Versatz der Rolle aus der Referenz (Obergrenze) | 335 | 0,10° | 53 % | 78 % | 89 % |

Versatz der Rolle = Median über die anderen Bilder der Rolle von (Kantenwinkel − Lochwinkel). Verworfen wurden
Reihen mit weniger als 5 Löchern, mit Restfehler über 2,5 px und Bilder, deren zwei Reihen um mehr als 0,3°
auseinanderliegen. Bei rund einem Drittel der Bilder ist keine Lochreihe messbar.

Nicht eingebaut. Der Gewinn ist klein, und die Referenz ist nach Augenmaß gesetzt (die Obergrenze von 0,10° ist
vermutlich ihr eigenes Rauschen). In einigen Rollen (Film 2, 9, 26) weicht der Versatz aus den Kanten um 0,2–0,3°
von dem aus der Referenz ab; ob dort die Kantenmessung schief liegt oder die Drehung von Hand am Motiv statt am
Rahmen ausgerichtet wurde, ist offen.

### Lange und kurze Kanten

Die Drehung von Hand ist an der Kante des Bildfelds ausgerichtet. Gemessen am Referenz-Crop (324 Bilder mit vier
gemessenen Seiten) liegen die langen Kanten im Median 0,12° neben der Referenz, in Richtung der Lochreihe, die
kurzen 0,01°. Die Regel „die zwei kurzen Kanten entscheiden, wenn sie sich einig sind“ brachte am Referenz-Crop
64 % → 70 % unter 0,2°, in der echten Pipeline mit erkanntem Crop aber nur 74 % → 75 % (Median 0,110° → 0,115°).
Darum nicht übernommen. `tests/test_skew.py` deckt die Messung jetzt mit zwei Tests ab.
