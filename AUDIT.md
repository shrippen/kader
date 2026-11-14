# Code-Audit kader, 14.11.2026, Stand 1df940d

## Urteil
Das Repo lässt sich nur mit Mühe warten. Der neuere Teil, die Web-Oberfläche mit ihren Ausgabe-Adaptern unter `companion/`, ist sauber nach Aufgaben getrennt und gut getestet. Die Erkennung dagegen steckt fast ganz in einer einzigen Datei mit 2425 Zeilen. Daneben liegt im Hauptordner noch ein ganzer alter Rechenweg, der bei Änderungen mitgezogen werden muss. Mehrere Regeln stehen doppelt, einmal in Python und einmal im darktable-Plugin (Lua) oder in den Messwerkzeugen. An einer Stelle sind diese Kopien schon auseinandergelaufen: Die Web-Oberfläche zählt einen Crop nach einer anderen Regel als „Treffer“ als die Messung. Dies ist das erste Audit, einen Vergleich gibt es also noch nicht.

## Kennzahlen
| | letztes Audit | jetzt |
|---|---|---|
| Quelldateien (von der Strukturprüfung gemessen) | – | 75 |
| Einträge in der Bestandsliste | – | 60 |
| größte Datei (Zeilen) | – | 2425 (`kader.py`) |
| längste Funktion (Zeilen) | – | 352 (`kader.py`, `apply_film_consensus`) |

## Funde

### 1. Die Regel, wann ein Crop als „Treffer“ zählt, steht dreimal im Repo, und die Kopien sind schon auseinandergelaufen
Ein „Treffer“ ist ein automatischer Crop, der nah genug an deinem Handcrop liegt. Das Messwerkzeug hat die Regel im November verschärft: Jede der vier Kanten muss näher als 25 px liegen. Vorher galt nur die Größe, und nach dem Kommentar im Messwerkzeug galten damit 89 von 198 „Treffern“ zu Unrecht als richtig. Die Web-Oberfläche und der Feedback-Bericht haben eigene Kopien der alten Regel behalten: Breite und Höhe dürfen höchstens 60 px abweichen. Das Abzeichen „Treffer“ in der Galerie und im Editor nennt deshalb einen Crop richtig, der die richtige Größe hat, aber an der falschen Stelle liegt. Jede künftige Änderung der Regel muss an drei Stellen von Hand nachgezogen werden. Vorschlag: Die Regel steht an einer Stelle, und Web-Oberfläche, Messwerkzeug und Bericht rufen diese Stelle auf. Aufwand klein. Risiko gering: Die Anzeige ist getestet (`tests/test_companion.py:942`), der Test muss die neue Regel bekommen. Beleg: `companion/session.py:49`, `companion/session.py:473`, `companion/static/gallery.js:103`, `tools/eval.py:44`, `tools/eval.py:131`, `tools/feedback_report.py:38`, `tools/feedback_report.py:120`.

### 2. Ein alter Rechenweg liegt neben dem echten und muss bei Änderungen mitgezogen werden
Testlauf und Prüfung laufen heute über die Web-Oberfläche mit derselben Erkennung wie in darktable (so steht es in `start_review_gui.sh`). Im Hauptordner liegt aber noch der frühere Weg aus fünf Dateien: das Testlauf-Skript, die Film-Analyse, die alte Tk-Oberfläche und zwei Analyse-Skripte. Dazu kommen die Ergebnisdateien dieses Wegs in `review_data/`. Das Testlauf-Skript enthält eine eigene Kopie der Berechnung, die das Seitenverhältnis einer Rolle bestimmt; sie stimmt fast Zeile für Zeile mit der in `kader.py` überein. Der Schalter `--tk` im Startskript ruft eine Datei auf, die es nicht mehr gibt. Trotzdem kostet der alte Weg Arbeit: Ein Test prüft ihn auf Erkennungsgründe mit, und der Commit 2e3414e vom 10.11. musste ihn deshalb mitändern. Vorschlag: Du prüfst, ob du eines der Skripte noch benutzt; alles andere wird gelöscht, samt `--tk` und der Erwähnung im Test und in der README. Das nimmt sieben Einträge aus der Bestandsliste. Aufwand klein. Risiko gering, weil nichts im Produkt diese Dateien aufruft. Beleg: `batch_test.py:112`, `kader.py:2133`, `start_review_gui.sh:31`, `tests/test_reasons.py:22`, `review_gui.py:724`, `film_analysis.py:1`, `analyze_manual_crops.py:1`, `diagnose.py:1`.

### 3. Der Umweg über darktable-cli für RAW-Dateien ist zweimal gebaut
RAW-Dateien müssen vor der Erkennung über darktables Kommandozeilenprogramm `darktable-cli` in JPEG umgewandelt werden. Diese Umwandlung gibt es zweimal: in der Erkennung für den direkten Modus des darktable-Plugins und in der Companion-App. Die Kopien weichen schon voneinander ab. Nur die Companion-Version findet darktable auch in Windows-Installationsordnern, bricht nach zehn Minuten ab und entfernt vorher einen vorhandenen Crop. Auch die Liste der RAW-Dateiendungen steht zweimal. Wer die Umwandlung ändert, etwa weil eine neue darktable-Version andere Optionen braucht, muss beide Kopien finden. Vorschlag: Die Erkennung bekommt immer schon umgewandelte Bilder, und es gibt eine einzige Umwandlung, die beide Wege benutzen. Aufwand mittel. Risiko mittel: Der Test der Umwandlung läuft nur, wenn darktable-cli und Testfotos vorhanden sind, also nicht in der CI (der automatischen Prüfung bei jedem Push). Beleg: `kader.py:52`, `kader.py:62`, `kader.py:73`, `kader.py:2068`, `companion/export.py:21`, `companion/export.py:32`, `companion/export.py:79`.

### 4. Die Sitzungsdatei der Companion-App hat drei Aufgaben, und die Ausgabe-Adapter hängen deshalb im Kreis an ihr
`companion/session.py` (1054 Zeilen, über der Grenze von 800) enthält:
- den Zustand einer Prüfsitzung,
- die Umrechnung von Crops (zwischen Bruchteilen und Pixeln, zwischen gedrehtem und ungedrehtem Bild),
- das Lesen und sichere Schreiben von JSON-Dateien.

Die Ausgabe-Adapter (die Ziele wie darktable, Kopien, XMP) brauchen nur die Umrechnung. Sie holen sie aber aus der Sitzungsdatei, und die Sitzungsdatei ruft ihrerseits die Ausgabe-Adapter auf. Das ist eine Abhängigkeit im Kreis, die eine Stelle nur mit einem verzögerten Import umgeht. Wer an der Crop-Rechnung etwas ändert, muss die ganze Sitzung lesen. Vorschlag: Die Crop-Umrechnung und die JSON-Hilfen kommen in je eine eigene kleine Datei; die Sitzung behält nur den Zustand. Aufwand klein bis mittel. Risiko gering: Die Sitzung ist gründlich getestet (`tests/test_companion.py`, `tests/test_standalone.py`). Beleg: `companion/session.py:31`, `companion/session.py:64`, `companion/session.py:104`, `companion/targets/__init__.py:89`, `companion/targets/copies.py:14`, `companion/targets/manifest.py:15`.

### 5. Die Erkennung steckt fast ganz in einer Datei mit 2425 Zeilen
`kader.py` enthält:
- die Kommandozeile,
- die RAW-Umwandlung,
- vier Suchverfahren für den Bildrahmen,
- die Messung der Schräglage,
- die Abstimmung über eine ganze Rolle,
- den Ablauf eines ganzen Stapels.

Die Abstimmung über die Rolle ist eine einzige Funktion mit 352 Zeilen und 93 Verzweigungen. Sie besteht aber erkennbar aus fünf Schritten nacheinander: Rohgröße je Rolle, Formatgruppen, Maßstab aus der Perforation, Abgleich über alle Rollen, Einpassen in zwei Durchgängen. Die Companion-App greift zudem auf innere Hilfsfunktionen dieser Datei zu, die als nicht öffentlich gekennzeichnet sind. Der Server holt sich die Liste der Filmformate sogar über eine solche Hilfsfunktion direkt aus der Erkennung. Jede Änderung an einem Schritt verlangt, die ganze Funktion zu verstehen. Vorschlag: Die Abstimmung über die Rolle wird in eine eigene Datei mit einer Funktion je Schritt geteilt, danach die Schräglage; die Companion-App bekommt dafür benannte öffentliche Einstiege. Aufwand groß, mehrere PRs. Risiko hoch: Die Abstimmung ist nur indirekt getestet (`tests/test_frame_edges.py:228`), und die eigentliche Messung (`tools/eval.py`) braucht die lokalen Testfotos und läuft nicht in der CI. Vor dem Umbau sollte das Messergebnis als Vergleichswert festgehalten werden. Beleg: `kader.py:1589`, `kader.py:673`, `kader.py:1135`, `companion/detect.py:38`, `companion/detect.py:86`, `companion/detect.py:375`, `companion/server.py:395`.

### 6. Wie darktable einen Crop und eine Drehung gespeichert haben will, steht in Lua und in Python je einmal
Das darktable-Plugin (Lua) und das Ziel „darktable-Sidecar“ (Python) schreiben beide darktables interne Einstellungen für Zuschnitt und Drehung. Das ist ein festes Binärformat (Zahlenfolgen in genau vorgegebener Länge) samt Versionsnummern und einem festen Mischmodus-Block. Beide Kopien sind von Hand gepflegt. Die Versionsnummer des Zuschnitt-Moduls steht schon verschieden: 3 in Lua, 1 in Python. Ändert eine neue darktable-Version das Format, müssen beide Sprachen gleich angepasst werden, und nichts merkt, wenn eine vergessen wird. Vorschlag: Ein Test erzeugt dieselben Einstellungen über beide Wege und vergleicht die Bytes; die Testhilfe für Lua (`tests/lua_harness.lua`) gibt es schon. Dabei wird entschieden, welche Versionsnummer stimmt. Aufwand klein bis mittel. Risiko gering. Beleg: `kader.lua:525`, `kader.lua:530`, `kader.lua:533`, `kader.lua:548`, `companion/targets/darktable_xmp.py:28`, `companion/targets/darktable_xmp.py:32`, `companion/targets/darktable_xmp.py:70`, `companion/targets/darktable_xmp.py:77`.

### 7. Die Einteilung in Grün, Gelb und Rot und ihre Standardschwellen stehen an drei Stellen
Ob ein Bild grün, gelb oder rot ist, rechnen drei Stellen getrennt aus: das darktable-Plugin, die Sitzung der Companion-App und der Stapelablauf der Erkennung. Die Standardschwellen 0,5 und 0,3 stehen ebenso mehrfach. Das Werkzeug `tools/calibrate.py` ist dafür da, diese Schwellen neu zu bestimmen; jedes Ergebnis muss dann an allen Stellen von Hand eingetragen werden. Vorschlag: Die Regel und die Standardwerte stehen in Python an einer Stelle. Der Stapelablauf liefert dem Plugin die fertige Farbe mit, statt sie dort noch einmal auszurechnen. Aufwand klein. Risiko gering. Beleg: `kader.lua:28`, `kader.lua:39`, `companion/session.py:42`, `companion/session.py:374`, `kader.py:2239`.

### 8. Die Projektbeschreibung für Agenten widerspricht sich und beschreibt den alten Weg
`agent.md` ist die Datei, nach der jede Sitzung hier arbeitet. Sie hat den Abschnitt „Architektur: Drei-Phasen-Pipeline“ und „Wichtige Erkenntnisse“ je zweimal, mit verschiedenem Inhalt. Einmal wird das Seitenverhältnis der Rolle nach der kontraststärksten Messung bestimmt, einmal über den Mittelwert. Der Abschnitt „Pipeline“ nennt das alte Testlauf-Skript und die Tk-Oberfläche aus Fund 2 als Teil des Ablaufs. Die nächste Änderung an der Erkennung beginnt so mit einer falschen Beschreibung. Vorschlag: Die Doppelungen werden gestrichen und die Beschreibung auf den heutigen Weg gebracht, am besten zusammen mit Fund 2; da es eine Regeldatei ist, bestätigst du das. Aufwand klein. Risiko keins. Beleg: `agent.md:24`, `agent.md:54`, `agent.md:76`.

### 9. Bestandsliste: was sich teilen lässt und was bleiben kann
Die Bestandsliste nennt alles, was heute über den Grenzen der Strukturprüfung liegt.

An einer natürlichen Naht teilen lassen sich:
- die Abstimmung über die Rolle und die Rahmenverfeinerung in `kader.py` (Fund 5),
- `companion/session.py` (Fund 4); dort trennt sich `patch_images` außerdem in „Eingabe prüfen“ und „Änderung anwenden“,
- `kader.lua` mit 1546 Zeilen in drei Teile: Steuerung des direkten Modus, Schreiben der darktable-Stile, Steuerung der Companion-App.

In Ordnung, wie sie sind:
- `companion/server.py` `_api`: eine flache Liste von Adressen, je eine Zeile Arbeit,
- die langen Testdateien,
- das Ablaufskript des Browser-Tests,
- die `main`-Funktionen der Messwerkzeuge unter `tools/`.

Sieben Einträge fallen mit Fund 2 ganz weg. Beleg: `structure.baseline:4`, `companion/session.py:605`, `kader.lua:358`, `kader.lua:533`, `kader.lua:1230`, `companion/server.py:386`.

## Seit dem letzten Audit
Erstes Audit.
