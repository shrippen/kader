# Demo (internal)

Internal tool for automated screenshots, not part of any release. Uses the shared demo world of all shrippen projects (shrippen.github.io/demo).

```bash
demo/start.sh                    # gezeichnete Demo-Rollen anlegen und öffnen
```

Legt zwei Rollen mit gezeichneten Kamerascans an (Elbstrand Övelgönne, Fahrradwerkstatt; aus der gemeinsamen
Demowelt „Studio Weber“ aller shrippen-Projekte, `demo/world.json`) und öffnet sie mit `kader open`.
Ein paar Bilder sind absichtlich unterbelichtet, damit Grün, Gelb und Rot vorkommen. Standardordner ist
`KADER_CACHE/demo-rollen`, ein anderer geht mit `demo/start.sh ORDNER`. `demo/shots.json` beschreibt die
Screenshots, die `shrippen.github.io/demo/tools/screenshots.py` davon macht.
