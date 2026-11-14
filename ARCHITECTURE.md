# Architecture

How this repository is meant to be built. Where the code differs today is listed under
"Known deviations". Change this file in the PR that changes the structure.

## What it does

Kader crops photographed film negatives to the frame on the film. The detection finds
the frame in every picture of a roll and rates how sure it is; in a local web interface
the user checks and corrects the proposals; "done" hands the crops to a target: cropped
copies, a list, sidecars for darktable, RawTherapee or Lightroom, or darktable itself
through the Lua plug-in.

## Building blocks

| Path | Its one task |
|---|---|
| `kader.py`, `frame_edges.py`, `film_scale.py` | The detection: finding the frame (frame edges per roll for 35 mm, the older search for other formats), skew, the vote over a whole roll, the scale from the perforation; the command line and the run over a batch. In the target one file per step. |
| `kader_wrapper.py` | Starts the detection or the companion with the Python of the virtual environment; what the Lua plug-in calls. |
| `kader.lua` | The darktable plug-in: starts detection or companion for the selected pictures and writes crop and rotation into darktable. |
| `companion/session.py` | The state of one review: pictures, crops, decisions, colours. |
| `companion/detect.py`, `rawdetect.py` | Running the detection for a session in the background; the density image from a RAW file the detection measures on. |
| `companion/programs.py`, `export.py`, `converters.py`, `pp3.py` | The outside programs: finding them; turning RAW files into JPEG with darktable-cli, RawTherapee or rawpy. |
| `companion/sources.py`, `thumbs.py`, `orientation.py` | What a folder contains; thumbnails and image sizes; how a file is stored rotated. |
| `companion/targets/` | One file per output (copies, list, darktable, darktable sidecar, RawTherapee, XMP, reviews). |
| `companion/server.py`, `companion/static/` | The local HTTP API and the web interface in the browser (`api.js` is its one way to the server). `static/vendor/` is synced, never edited here. |
| `companion/__main__.py`, `launcher.py`, `window.py`, `tui.py` | Start of the companion: command line, the small start window, the terminal front. |
| `companion/dtplugin.py`, `dtconfig.py` | Installing the Lua plug-in into darktable; reading darktable's configuration. |
| `tests/` | Tests of detection, companion and Lua (through `lua_harness.lua`). |
| `tools/` | Measuring the detection against the owner's hand crops (`eval.py`, `calibrate.py` and others; they need local test photos), Kante sync, the structure check (synced copy). |
| `packaging/`, `install.sh`, `scripts/`, `demo/`, `docs/` | AppImage and Windows build; installing; release notes; the demo rolls for screenshots; landing page. |

## Layers

```
 darktable ─► kader.lua                 browser: companion/static/ (through api.js)
                 │ starts                          │ HTTP
                 ▼                                 ▼
        kader_wrapper.py ─────────────► companion: server.py
                 │                          │              │
                 │                          ▼              ▼
                 │                    detect.py ──► session.py ──► targets/ ─► files,
                 │                    rawdetect.py  (state)        darktable, sidecars
                 │                          │
                 │                          ├──► programs, export, converters ─► darktable-cli,
                 ▼                          ▼                                    RawTherapee
        the detection: kader.py, frame_edges.py, film_scale.py   (pictures in, crops out)
```

- The detection knows nothing of the companion, the plug-in or an output. It takes
  pictures and returns crops with their confidence. The companion uses its named
  public functions only.
- A rule stands once, in Python: when a crop counts as a hit, the colour of a picture
  and its thresholds, the list of film formats, the RAW file endings. The plug-in and
  the web interface get the result; they do not compute it again.
- What must exist in Lua and in Python (how darktable stores crop and rotation) is
  held equal by a test.
- An outside program is found and run at one place, in `companion/`; the detection
  gets pictures that are already converted.
- `server.py` translates HTTP and decides nothing; the browser reaches it through
  `api.js` only.
- A target needs the crop arithmetic and the file helpers, not the session: these
  live in small files of their own, and nothing imports in a circle.
- The session holds state only.
- One way of working exists. A script nobody runs any more is deleted.
- `tools/` measures; the program imports nothing from it.
- The demo is in no release.

## Where new things go

| Change | Touch |
|---|---|
| A change to how the frame is found | The file of its step in the detection, a test in `tests/`; then `tools/eval.py` on the test photos |
| A new film format | The list of formats in the detection; nothing else keeps a list |
| A new output | A file in `companion/targets/`, its entry in `companion/targets/__init__.py`, a test |
| A new way to convert RAW files | `companion/converters.py`, the program in `companion/programs.py` |
| A new call of the web interface | `companion/server.py`, `companion/static/api.js`, the page's file in `static/` |
| A new threshold or rating | Once in Python; `tools/calibrate.py` finds its value |
| Something in darktable | `kader.lua`, with a test through `tests/lua_harness.lua` |
| A design element that is missing | Kante, then `tools/sync-kante.sh` |
| A release | The steps in `RELEASE.md` |

## Known deviations

- The hit rule stands three times and differs: measuring tool, web interface,
  feedback report (`AUDIT.md`, finding 1).
- An older way of working lies beside the real one: batch script, film analysis, Tk
  interface, two analysis scripts, their data (`AUDIT.md`, finding 2).
- Converting RAW files with darktable-cli is built twice, in the detection and in
  the companion, with two lists of endings (`AUDIT.md`, finding 3).
- `companion/session.py` holds state, crop arithmetic and file helpers; the targets
  import it and it imports them (`AUDIT.md`, finding 4).
- `kader.py` holds nearly the whole detection in 2425 lines; the companion calls its
  private helpers, the server through a private helper of `detect.py`
  (`AUDIT.md`, finding 5).
- How darktable stores crop and rotation stands in Lua and in Python without a test;
  the version numbers differ (`AUDIT.md`, finding 6).
- Colours and thresholds are computed in three places (`AUDIT.md`, finding 7).
