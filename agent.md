# Working rules for this repository

The rules for all shrippen repositories are in `RULES.md` (writing, code, commits, bug
fixes, repository, GUI). It is a synced copy from the rules repository; do not edit it
here. This file holds only what is particular to this repository. A Claude Code session on
the owner's machine has the rules through the global `CLAUDE.md` already and reads
`RULES.md` only for its GUI rule, before work on a user interface.

## Auto-Crop-Negative – Projekt-Wissen

## Zweck
Automatisches Zuschneiden von fotoabfotografierten Filmnegativen. Das Skript erkennt den
Bildbereich innerhalb des Filmstreifens (ohne Sprossenlöcher, Filmrand, Halter) und liefert
die Crop-Koordinaten als JSON.

## Workflow
1. **Vollautomatisch** – das finale Skript läuft ohne menschliches Eingreifen.
2. Unsichere Kandidaten werden automatisch als `needs_review` markiert.
3. Manuelle Korrekturen im Review-GUI dienen **nur zum Trainieren/Validieren** des Algorithmus.
   Sie sind **nicht pixelgenau**, sondern geben Anhaltspunkte für die Richtung der Korrektur.
   Im Zweifel: groben Bias korrigieren, nicht einzelne Bilder optimieren.
4. Validierung per Delta-Kriterien: ΔHeight <100px, ΔWidth <50px = OK

## Pipeline
- `kader.py` – Stage 1 (Filmstreifen-Erkennung) + Stage 2 (Bildinhalt)
- `film_analysis.py` – Filmweites Seitenverhältnis + Bildgröße aus Pass-1-Daten
- `batch_test.py` – `--two-pass`: Pass 1 → Film-Analyse → Pass 2 (mit Film-Metadaten)
- `start_review_gui.sh` – interaktive Analyseauswahl + GUI-Start
- `review_gui.py` – Bild-Review, Crop-Editor, Export

## Bekannte Fehlerklassen (Stand: 98 manuelle Korrekturen, 92/98 OK = 94%)
- **Geloest: Film-Aspect-Erkennung** via Pass A (measure_image_aspect):
  Polaritaets-adaptiv (Bild kann heller ODER dunkler als Filmrand sein –
  Negativ-Polaritaet!), Dark-Span (Halter <100) + Span mit Threshold bei
  Rand + 25% des Kontrasts.
- **Geloest: Kontrast-Konsens statt Median:** Die bestkontrasteste Messung
  (klarste Bildgrenzen) fuehrt; alle Messungen innerhalb +/-10% davon werden
  gemittelt. Grund: schwaechere Messungen erwischt oft den Filmstreifen
  statt das Bild (Film 31: Kontrast 67 -> 1.03 korrekt vs. Kontrast 13-28
  -> 1.1-1.6 gestreut).
- **Geloest: 1:1-Filme (Film 29: 11/13, Film 31: 11/12).**
- **Rest-MISS (6):** Alles Grenzfaelle (Delta 57-85px, Schwelle 50/100).
  Kein systematischer Fehler mehr.

## Architektur: Drei-Phasen-Pipeline
1. **Pass A** (`--measure-aspect`): Misst Bild-Aspect pro Bild OHNE
   Ziel-Vorurteil. Polaritaets-adaptive Span-Suche, ~1s/Bild.
2. **Film-Aspect-Bestimmung** (`determine_film_aspects`): Portrait-
   Normalisierung, bestkontrasteste Messung + Konsens (+/-10%),
   Fallback 1.5 bei <3 validen.
3. **Pass B** (volle Erkennung): Stage 1 + Stage 2 mit `--aspect-ratio`
   aus Schritt 2. Geometry-Fallback + Expand-Height nutzen das echte Format.

## Wichtige Erkenntnisse
- Aspect-Strafe in Stage 1 wuerde das Format-Erkennen verhindern
  (Chicken-and-Egg). Daher: Pass A ohne jeden Aspect-Bias.
- Negative haben BEIDE Polaritaeten: Bild heller ODER dunkler als Rand
  (je nach Belichtung). Immer beide pruefen.
- Bright-Span-Threshold bei (border+content)/2 zerbricht bei dunkleren
  Bildmitteilen; 25%-Regel behebt das.
- Full-Image-Dark-Span in Stage 2 war ein Fehlschlag (Out-of-Bounds-Crops
  bei Portrait-Bildern) – entfernt.
- Nutzer-Definition "sauberer Crop": moeglichst wenig Filmrand, Aspect
  ist Richtwert kein Dogma. Geometry-Fallback nur bei starker Abweichung
  (>15%) und nur wenn er den Crop tatsaechlich verbessert.

## Architektur: Drei-Phasen-Pipeline
1. **Pass A** (`--measure-aspect`): Misst Bild-Aspect pro Bild OHNE
   Ziel-Vorurteil. Nur Dark-Span + Bright-Span, kein Scoring/Merge. ~1s/Bild.
2. **Film-Aspect-Bestimmung** (`determine_film_aspects`): Portrait-
   Normalisierung (a<1 -> 1/a), Median pro Film, Fallback 1.5 bei <3 validen.
3. **Pass B** (volle Erkennung): Stage 1 + Stage 2 mit `--aspect-ratio`
   aus Schritt 2. Geometry-Fallback + Expand-Height nutzen das echte Format.

## Wichtige Erkenntnisse
- Aspect-Strafe in Stage 1 wuerde das Format-Erkennen verhindern
  (Chicken-and-Egg). Daher: Pass A ohne jeden Aspect-Bias.
- Bright-Span-Threshold bei (border+content)/2 zerbricht bei dunkleren
  Bildmitteilen; 25%-Regel behebt das.
- Full-Image-Dark-Span in Stage 2 war ein Fehlschlag (produzierte
  Out-of-Bounds-Crops bei Portrait-Bildern) – entfernt.
- Konsistenz-Korrektur orientation-blind: funktioniert, weil Pass B mit
  korrektem Film-Aspect laeuft und die Medians dann stimmen.

## Gelernte Bugs
- Konsistenz-Call stand in main() statt _run_two_pass (Muster
  "elapsed + results.sort" existiert doppelt – Edit traf falsches Vorkommen).
  Bei doppelten Code-Mustern immer eindeutigen Kontext verwenden!
- Film-Konsistenz nur anwenden wenn Film-Aspect verlässlich
  (matching >= 3 Bilder nahe am Film-Aspect).

## GUI (this project)

- Here: the companion web UI vendors `companion/static/vendor/` (`tools/sync-kante.sh`,
  `VERSION` names the Kante commit); Tk and the TUI take `companion/kante_tokens.py`, generated
  by `tools/gen_kante_tokens.py` from Kante's `tokens/`. Never edit either by hand. The landing
  page links `https://shrippen.github.io/v1/`.

## Release

Release steps: `RELEASE.md`. Before a release, load the skill `release-changelog`. A release
is published, so the owner confirms it in words.

## Repository (this project)

- CI runs on the GitHub mirror (`.github/workflows/ci.yml`, since 16.10.2026) and reports back to Gitea as the commit status `github / test`.
- The merge waits for: CI is green on the PR's latest commit: the newest `github / test` status there (`.github/workflows/ci.yml` on the GitHub mirror: the tests in `tests/` and the demo rolls, on every push, no path filter) is success. The browser smoke test (`tests/ui_smoke.py`) is not in CI; run it locally when the PR changes the review UI.
- The owner also confirms: a PR that changes `packaging/`.
- Everything else: `RULES.md` (Repository) and the skill `pr-review`.
