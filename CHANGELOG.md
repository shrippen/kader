# Changelog

## [Unreleased]

### Oberfläche auf Kante 1.7
- Die Companion-UI nutzt Kante 1.7 (vendort, `companion/static/vendor/`) statt des alten Design-Bundles; eigene
  Bausteine (Badges, Chips, Kennzahlenlisten, Fortschrittszeilen) sind durch Kante-Klassen ersetzt, `app.css`
  enthält nur noch Layout. Kennzahlen und Analysefortschritt zählen hoch, Drag-and-drop zwischen den Bändern
  nutzt Kantes Lücke/Zielzelle/Einrasten.
- Tk-Review-GUI, Statusfenster und TUI beziehen ihre Farben aus `companion/kante_tokens.py` (aus Kantes
  `palette.json` erzeugt, `tools/gen_kante_tokens.py`). Geschnittene Ecken gibt es in Tk nicht.

- Kante 1.5/1.6 nachgezogen: Aktionsleiste als `.bulk-bar`, Kennzahlen mit `.fact[data-tier]`, Kandidaten als
  `.chip`, Einstellungen als `.setting`-Zeilen, Meldungen im `.toast-stack`, Abschnittstitel als `.h-label`;
  die zugehörigen eigenen Regeln in `app.css` entfallen.
  Kopfzeile mit `.nav-inner.is-wrap`/`.nav-tools`, Aktionsleiste als `.bulk-bar.is-fixed` (Meldungen und Seitenrand
  folgen `--bar-h`), Editor auf Handys mit voller Bildfläche; kein seitliches Scrollen mehr bei 390 px. `tools/sync-kante.sh` liest die Version aus `palette.json`.

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
