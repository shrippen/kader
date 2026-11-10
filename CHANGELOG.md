# Changelog

## [Unreleased]

## [0.5.0] — 2026-11-10

### English

The crop now sits on the frame: Kader measures the frame edges of a whole roll together, shows how sure each of the four edges is, and reads dark pictures from the RAW file.

#### New

- A scanning guide in the web UI, below the gallery: a labelled drawing shows what the camera should capture (file,
  image area, film border, perforation) and where the crop belongs. The same drawing is in `scan-howto.en.md`, which
  now recommends an image area of about 70–90 % of the file width so that all four edges stay in the file.

#### Improved

- The crop sits on the frame. Kader now measures, for every picture, how completely an edge from film border to
  picture runs along the whole frame, and adds this up over the roll: the camera's frame window is the same for every
  picture. On 209 hand-made crops all four edges are within about 1 % of the reference for 167 pictures instead of
  109; before, a crop of the right size in the wrong place counted as found.
- Green means more. The confidence is the weakest of the four edges, so one unseen edge keeps a picture out of green.
  98 % of the green crops are that exact instead of 70 %, and more pictures are green.
- A picture with a dark side keeps its frame: the unseen edge is placed by the roll's frame size from the edge that is
  visible. A black picture takes the usual position of the roll and is marked for review.
- A single picture in another scale keeps its own edges when both are clearly visible.
- Dark pictures keep their edges when Kader gets the RAW files. A developed export can crush film border and
  picture into the same black; Kader now measures on its own image from the RAW, where the two are still apart, and
  tells negatives from slides by the roll. On three dark rolls all four edges are within about 1 % for 47 of 57
  hand-made crops instead of 32. This applies to 35 mm film in the web UI and needs the Python package `rawpy`;
  without it the export is measured as before.
- The editor shows the four edges as the factors of the confidence.
- A roll is analysed about twice as fast again.

#### Note

- Other formats than 35 mm and rolls without usable edges are detected as before.
- Kader no longer learns a preferred crop size from hand-set crops. The crop sits 0.5 % of the frame's long side
  inside the measured edge; a stored `convention.json` is no longer read.

All changes: https://github.com/shrippen/kader/compare/v0.4.0...v0.5.0

### Deutsch

Der Crop sitzt jetzt auf dem Rahmen: Kader misst die Rahmenkanten einer ganzen Rolle gemeinsam, zeigt für jede der vier Kanten, wie sicher sie ist, und liest dunkle Bilder aus dem RAW.

#### Neu

- Eine Anleitung zum Scannen in der Web-Oberfläche, unter der Galerie: Eine beschriftete Zeichnung zeigt, was die
  Kamera aufnehmen soll (Datei, Bildfeld, Filmrand, Perforation) und wo der Crop hingehört. Dieselbe Zeichnung steht
  in `scan-howto.md`; dort gilt jetzt ein Bildfeld von etwa 70–90 % der Dateibreite als Richtwert, damit alle vier
  Kanten in der Datei bleiben.

#### Verbessert

- Der Crop sitzt auf dem Rahmen. Kader misst jetzt für jedes Bild, wie geschlossen eine Kante vom Filmrand zum Bild
  über den ganzen Rahmen läuft, und summiert das über die Rolle: das Bildfenster der Kamera ist für jedes Bild gleich.
  Bei 209 Crops von Hand liegen bei 167 Bildern alle vier Kanten auf etwa 1 % genau statt bei 109; bisher galt auch
  ein Crop richtiger Größe an falscher Stelle als gefunden.
- Grün sagt mehr. Die Konfidenz ist die schwächste der vier Kanten, eine ungesehene Kante hält ein Bild also aus Grün
  heraus. 98 % der grünen Crops sind so genau statt 70 %, und mehr Bilder sind grün.
- Ein Bild mit dunkler Seite behält seinen Rahmen: die ungesehene Kante liegt um die Rahmengröße der Rolle neben der
  sichtbaren. Ein schwarzes Bild bekommt die übliche Lage der Rolle und wird zur Prüfung markiert.
- Ein einzelnes Bild in anderem Maßstab behält seine eigenen Kanten, wenn beide klar zu sehen sind.
- Dunkle Bilder behalten ihre Kanten, wenn Kader die RAW-Dateien bekommt. Ein entwickelter Export kann Filmrand und
  Bild ins selbe Schwarz drücken; Kader misst jetzt auf einem eigenen Bild aus dem RAW, in dem beide noch getrennt
  sind, und unterscheidet Negativ und Dia an der Rolle. Auf drei dunklen Rollen liegen bei 47 von 57 Crops von Hand
  alle vier Kanten auf etwa 1 % genau statt bei 32. Das gilt für Kleinbild in der Web-Oberfläche und braucht das
  Python-Paket `rawpy`; ohne es wird wie bisher der Export gemessen.
- Der Editor zeigt die vier Kanten als Faktoren der Konfidenz.
- Eine Rolle wird noch einmal etwa doppelt so schnell analysiert.

#### Hinweis

- Andere Formate als Kleinbild und Rollen ohne brauchbare Kanten werden wie bisher erkannt.
- Kader lernt keine bevorzugte Crop-Größe mehr aus von Hand gesetzten Crops. Der Crop liegt 0,5 % der langen
  Rahmenkante innerhalb der gemessenen Kante; eine gespeicherte `convention.json` wird nicht mehr gelesen.

## [0.4.0] — 2026-11-09

### English

Faster and in a new look: a roll is detected about 4.7 times as fast, and the review in the browser uses the Kante design, also on a phone.

#### Improved
- Detection is about 4.7 times as fast: the test rolls took 58 seconds and now take about 12, with the same or slightly better hits (reference crops 1453 → 1467 of 1662). The line search runs on half the resolution, and each analysis process uses one thread instead of all cores at once.
- The web UI uses the Kante design: clearer labels, counts and progress, and dragging an image between green, yellow and red shows where it lands. The status window and the terminal display take the same colours.
- On a phone the page no longer scrolls sideways, the action bar keeps out of the way of the content and messages, and the crop editor opens at the top with the whole picture.

#### Fixed
- The straighten switch (key T) did nothing on an image without a measured tilt. It is now off there, and T says there is no tilt.

All changes: https://github.com/shrippen/kader/compare/v0.3.0...v0.4.0

### Deutsch

Schneller und in neuem Gewand: Eine Rolle ist etwa 4,7-mal so schnell erkannt, und die Prüfung im Browser nutzt das Kante-Design, auch auf dem Handy.

#### Verbessert
- Die Erkennung ist etwa 4,7-mal so schnell: Die Testrollen brauchten 58 Sekunden und jetzt etwa 12, mit gleichen oder etwas besseren Treffern (Referenz-Crops 1453 → 1467 von 1662). Die Liniensuche läuft auf halber Auflösung, und jeder Analyseprozess nutzt einen Thread statt aller Kerne zugleich.
- Die Web-Oberfläche nutzt das Kante-Design: klarere Labels, Zahlen und Fortschritt, und beim Ziehen eines Bildes zwischen Grün, Gelb und Rot sieht man, wo es landet. Statusfenster und Terminal-Anzeige übernehmen dieselben Farben.
- Auf dem Handy scrollt die Seite nicht mehr seitwärts, die Aktionsleiste verdeckt weder Inhalt noch Meldungen, und der Zuschnitt-Editor öffnet oben mit dem ganzen Bild.

#### Behoben
- Der Schalter zum Geradestellen (Taste T) tat bei einem Bild ohne gemessene Neigung nichts. Dort ist er jetzt aus, und T meldet, dass es keine Neigung gibt.

## [0.3.0] — 2026-09-26

### English

darktable and RawTherapee without a terminal: Kader writes darktable's sidecars itself, sets up its darktable plugin from the app and opens the editor when it is done.

#### New
- New target "darktable sidecars" (`darktable_xmp`): writes crop, rotation and colour label straight into darktable's `<file>.xmp`, without the plugin and without darktable running. Existing edits stay. Kader suggests it when the folder already has darktable sidecars, names images darktable has already imported (it reads the XMP only on import) and warns when darktable is running.
- Set up the darktable plugin from the app: the first double click offers it when darktable is installed (or `Kader darktable-plugin install|uninstall|status`). The plugin then starts Kader through the app instead of Python.
- After "Done", the status window offers "Open RawTherapee" or "Open darktable" (also as Flatpak) for those targets, with a hint on what happens there.

#### Improved
- The darktable plugin runs on Windows too (processes, browser, paths and temporary files through `cmd.exe`).
- `darktable-cli` and `rawtherapee-cli` are found in their usual install folders on Windows and macOS; programs started from the exe or AppImage no longer inherit the package's library paths, and Windows opens no console window per image.

#### Fixed
- The exe without a console crashed when it ran with arguments (such as `serve` from the plugin) and no output.

#### Note
- The darktable plugin is not yet checked in a real darktable on Windows.

All changes: https://github.com/shrippen/kader/compare/v0.2.0...v0.3.0

### Deutsch

darktable und RawTherapee ohne Terminal: Kader schreibt die Sidecars von darktable selbst, richtet sein darktable-Plugin aus der App ein und öffnet nach dem Abschluss das Programm.

#### Neu
- Neues Ziel „darktable-Sidecars“ (`darktable_xmp`): schreibt Zuschnitt, Drehung und Farblabel direkt in die `<datei>.xmp` von darktable, ohne Plugin und ohne laufendes darktable. Vorhandene Bearbeitungen bleiben. Kader schlägt es vor, wenn im Ordner schon darktable-Sidecars liegen, nennt Bilder, die darktable schon importiert hat (es liest die XMP nur beim Import), und warnt, wenn darktable läuft.
- Das darktable-Plugin aus der App einrichten: Der erste Doppelklick bietet es an, wenn darktable installiert ist (oder `Kader darktable-plugin install|uninstall|status`). Das Plugin startet Kader dann über die App statt über Python.
- Nach „Fertig“ bietet das Statusfenster bei diesen Zielen „RawTherapee öffnen“ bzw. „darktable öffnen“ (auch als Flatpak), mit einem Hinweis, was dort passiert.

#### Verbessert
- Das darktable-Plugin läuft auch unter Windows (Prozesse, Browser, Pfade und temporäre Dateien über `cmd.exe`).
- `darktable-cli` und `rawtherapee-cli` werden unter Windows und macOS in ihren üblichen Installationsordnern gefunden; aus exe oder AppImage gestartete Programme erben nicht mehr die Bibliothekspfade des Pakets, und Windows öffnet kein Konsolenfenster je Bild.

#### Behoben
- Die exe ohne Konsole stürzte ab, wenn sie mit Argumenten (etwa `serve` aus dem Plugin) und ohne Ausgabe lief.

#### Hinweis
- Das darktable-Plugin ist unter Windows noch nicht in echtem darktable geprüft.

## [0.2.0] — 2026-09-26

### English

Kader works on its own: point it at a folder of scanned negatives, check the crops in the browser and write them for the tool you use, darktable no longer required. Double-click packages for Windows and Linux need no Python and no terminal, and the detection got much more accurate and more honest about its confidence.

#### New
- `kader FOLDER`: scans the folder (subfolders are rolls, RAWs included), analyses it and opens the web UI; "Done" applies the result at once. Running it again resumes the session and adds images that were added to the folder.
- Targets: cropped copies (straightened if wanted, ICC/EXIF and 16 bit kept), `crops.json`/`crops.csv`, XMP sidecars for Lightroom/Camera Raw, RawTherapee profiles (`.pp3`), and darktable as before. Kader suggests one from the sidecars already in the folder; a panel in the web UI explains each and shows which images a target would not write. Only what changed is written again.
- RAW converters: darktable, RawTherapee or rawpy (no extra program needed).
- Double-click packages: `Kader-…-windows-x64.exe` and `Kader-…-x86_64.AppImage`; without an argument a dialog asks for the folder, and a small status window shows progress and the result.
- `--tui`: a status display in the terminal for a NAS over SSH; `--bind`: reach the web UI from another machine in the network, protected by the session token.
- Tilt: Kader measures how skewed a frame is, shows it, straightens it by default when the measurement is reliable and passes the rotation on to the target; a switch (key T) turns it off per image.
- "Size to roll" in the crop editor carries a corrected crop's size over to the other images of the roll.
- The editor shows what the confidence is made of, with the weakest factor highlighted.

#### Improved
- The crop size comes from the film's perforation (a fixed 4.7625 mm pitch) where the scan shows it: on 62 test rolls the hit rate rose from about 63 % to about 87 %.
- The confidence is more honest: a roll whose scale cannot be confirmed is marked down as a whole, so about 96 % of green results are right.
- The frame orientation comes from the image, and the local fit stays closer to the roll's size.
- A port in use is no longer an error: Kader takes the next free one and says so.

#### Fixed
- Windows: a second Kader could run on the same session unnoticed and overwrite corrections; a session is now locked on every platform.
- Windows: checking whether darktable still ran sent it Ctrl+C.
- A second `open` with new images could lose them to the running server.
- `--bind ::` (IPv6) crashed on start, and `--port 80` always answered 403.
- Rejected requests kept the server from stopping when idle.
- A retry during a running re-detection could leave the session stuck in "analysing".
- The LAN address shown with `--bind 0.0.0.0` could be a VPN or Docker interface instead of the real network.

#### Note
- Not yet checked in the real programs: RawTherapee export and `.pp3` profiles, and Lightroom crop coordinates.
- The packages are not signed; Windows warns on the first start.

All changes: https://github.com/shrippen/kader/compare/v0.1...v0.2.0

### Deutsch

Kader arbeitet eigenständig: einen Ordner mit abfotografierten Negativen wählen, die Crops im Browser prüfen und für das eigene Programm schreiben, darktable ist nicht mehr nötig. Doppelklick-Pakete für Windows und Linux brauchen kein Python und kein Terminal, und die Erkennung ist deutlich genauer und ehrlicher in ihrer Konfidenz.

#### Neu
- `kader ORDNER`: durchsucht den Ordner (Unterordner sind Rollen, RAWs eingeschlossen), analysiert ihn und öffnet die Web-Oberfläche; „Fertig“ wendet das Ergebnis sofort an. Ein erneuter Aufruf setzt die Sitzung fort und ergänzt Bilder, die neu im Ordner liegen.
- Ziele: zugeschnittene Kopien (auf Wunsch geradegestellt, ICC/EXIF und 16 Bit bleiben), `crops.json`/`crops.csv`, XMP-Sidecars für Lightroom/Camera Raw, RawTherapee-Profile (`.pp3`) und darktable wie bisher. Kader schlägt eins nach den Sidecars im Ordner vor; ein Bereich in der Web-Oberfläche erklärt jedes und zeigt, welche Bilder ein Ziel nicht schreiben würde. Geschrieben wird nur, was sich geändert hat.
- RAW-Konverter: darktable, RawTherapee oder rawpy (kein weiteres Programm nötig).
- Doppelklick-Pakete: `Kader-…-windows-x64.exe` und `Kader-…-x86_64.AppImage`; ohne Argument fragt ein Dialog nach dem Ordner, und ein kleines Statusfenster zeigt Fortschritt und Ergebnis.
- `--tui`: eine Statusanzeige im Terminal für ein NAS per SSH; `--bind`: die Web-Oberfläche von einem anderen Rechner im Netz erreichen, geschützt durch das Token der Sitzung.
- Schräglage: Kader misst, wie schief ein Rahmen liegt, zeigt es, stellt ihn bei verlässlicher Messung standardmäßig gerade und gibt die Drehung an das Ziel weiter; ein Schalter (Taste T) schaltet das je Bild ab.
- „Größe auf Rolle“ im Crop-Editor überträgt die Größe eines korrigierten Crops auf die übrigen Bilder der Rolle.
- Der Editor zeigt, woraus sich die Konfidenz ergibt, der schwächste Faktor hervorgehoben.

#### Verbessert
- Die Crop-Größe kommt aus der Perforation des Films (fester Lochabstand 4,7625 mm), wo der Scan sie zeigt: Auf 62 Testrollen stieg die Trefferquote von etwa 63 % auf etwa 87 %.
- Die Konfidenz ist ehrlicher: Eine Rolle, deren Maßstab sich nicht bestätigen lässt, wird als Ganzes abgewertet, so stimmen etwa 96 % der grünen Ergebnisse.
- Die Ausrichtung des Rahmens kommt aus dem Bild, und das lokale Einpassen bleibt näher an der Größe der Rolle.
- Ein belegter Port ist kein Fehler mehr: Kader nimmt den nächsten freien und sagt das.

#### Behoben
- Windows: Ein zweites Kader konnte unbemerkt auf derselben Sitzung laufen und Korrekturen überschreiben; eine Sitzung ist jetzt auf jedem System gesperrt.
- Windows: Die Prüfung, ob darktable noch läuft, schickte ihm Strg+C.
- Ein zweites `open` mit neuen Bildern konnte sie an den laufenden Server verlieren.
- `--bind ::` (IPv6) stürzte beim Start ab, und `--port 80` antwortete immer mit 403.
- Abgewiesene Anfragen hielten den Server davon ab, sich bei Leerlauf zu beenden.
- Ein erneuter Versuch während einer laufenden Neu-Erkennung konnte die Sitzung in „Analyse“ festhalten.
- Die bei `--bind 0.0.0.0` gezeigte LAN-Adresse konnte die eines VPN- oder Docker-Netzes sein statt die des echten Netzes.

#### Hinweis
- Noch nicht in den echten Programmen geprüft: RawTherapee-Export und `.pp3`-Profile sowie Lightroom-Crop-Koordinaten.
- Die Pakete sind nicht signiert; Windows warnt beim ersten Start.

## [0.1] — 2026-09-20

### English

The first version with the companion web UI: detection runs in a local web page, you check and correct the crops there and hand them to darktable.

#### New
- Web UI on `127.0.0.1`: gallery grouped green, yellow and red with crop overlays, drag and drop, multi-select, keyboard shortcuts, a crop editor with handles, aspect lock and candidates, re-detection of a selection as a suggestion, two undo levels, German and English, dark and light.
- Hand-over: "Done" locks the view and writes the plan; only then does "Apply plan" in darktable take effect. "Back to review" unlocks it again, and applying again changes only the difference.
- Export from darktable in full resolution, without an existing crop and without changing the XMP.
- darktable plugin buttons: Start review, Apply plan, Open review, Stop server, Reset crop and colours; a server indicator with a clickable URL.
- The server stops when darktable closes and after 30 minutes without activity in the web UI.
- Folder mode without darktable (`python -m companion serve --folder …`).

#### Fixed
- The status display in the plugin hit the undo button instead of its own widget.
- No more markup tags in the plugin's labels (darktable does not render them).

#### Note
- The darktable part is tested against a stub of the darktable API, not yet fully in a real darktable, and not yet with real RAWs in a real library.

### Deutsch

Die erste Version mit der Companion-Web-Oberfläche: Die Erkennung läuft in einer lokalen Webseite, dort prüfst und korrigierst du die Crops und gibst sie an darktable weiter.

#### Neu
- Web-Oberfläche auf `127.0.0.1`: Galerie nach Grün, Gelb und Rot mit Crop-Overlays, Drag-and-drop, Mehrfachauswahl, Tastenkürzel, ein Crop-Editor mit Ziehgriffen, Seitenverhältnis-Sperre und Kandidaten, Neu-Erkennung einer Auswahl als Vorschlag, zwei Undo-Ebenen, Deutsch und Englisch, dunkel und hell.
- Übergabe: „Fertig“ sperrt die Ansicht und schreibt den Plan; erst dann wirkt „Plan anwenden“ in darktable. „Zurück zur Prüfung“ entsperrt wieder, und erneutes Anwenden ändert nur die Differenz.
- Export aus darktable in voller Auflösung, ohne vorhandenen Crop und ohne die XMP zu ändern.
- Knöpfe im darktable-Plugin: Review starten, Plan anwenden, Prüfung öffnen, Server stoppen, Crop & Farben zurücksetzen; eine Serveranzeige mit klickbarer URL.
- Der Server stoppt beim Schließen von darktable und nach 30 Minuten ohne Aktivität in der Web-Oberfläche.
- Ordnermodus ohne darktable (`python -m companion serve --folder …`).

#### Behoben
- Die Statusanzeige im Plugin traf den Undo-Knopf statt ihres eigenen Widgets.
- Keine Markup-Tags mehr in den Beschriftungen des Plugins (darktable stellt sie nicht dar).

#### Hinweis
- Der darktable-Teil ist gegen einen Stub der darktable-API getestet, noch nicht vollständig in echtem darktable und noch nicht mit echten RAWs in einer echten Bibliothek.
