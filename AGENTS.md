# AGENTS.md

## Working style

You are contributing to a small local Ubuntu utility written in Python.

Optimize for:
- correctness
- clarity
- straightforward implementation
- easy local debugging

Do not optimize for:
- framework cleverness
- excessive abstraction
- premature extensibility
- packaging/distribution complexity

## Project objective

Build a tool that:
1. lets the user select a rectangle on screen
2. periodically screenshots that region
3. runs OCR on the captured image
4. exposes a clean hook for later user-defined logic

The likely source text is a terminal visible in a Teams meeting, so OCR quality and pragmatic debugging matter a lot.

## Key design priorities

1. Make the first version work locally on Ubuntu.
2. Keep modules small and responsibilities obvious.
3. Make OCR behavior tunable by config rather than hardcoded.
4. Make it easy to inspect what the tool is doing.
5. Prefer a simple architecture that the user can edit later.

## Preferred implementation choices

Unless there is a concrete reason not to, prefer:
- Python
- `tkinter` for region selection
- `mss` for screenshot capture
- `Pillow` for image conversion
- `opencv-python` only where it clearly helps preprocessing
- `pytesseract` for OCR
- TOML for config

## Architecture guidance

A good module split is:

- `main.py` or package CLI entrypoint: CLI wiring
- `region_selector.py`: overlay and rectangle capture
- `screen_capture.py`: screenshot logic
- `preprocess.py`: OCR-oriented image cleanup
- `ocr.py`: wrapper around pytesseract
- `detector.py`: stateful text acceptance / debounce
- `actions.py`: placeholder hook for user-defined actions
- `config.py`: config loading/saving and model(s)

You may adjust names, but preserve separation of concerns.

## Behavior guidance

### Region selection
- Fullscreen translucent overlay is fine
- Click-drag-release rectangle selection is enough
- Support cancel if practical
- Save coordinates explicitly as `x`, `y`, `width`, `height`

### Monitoring loop
- Poll at a configurable interval
- Capture only the selected region
- Preprocess, OCR, normalize
- Avoid spamming identical text repeatedly
- Print/log accepted text changes
- Call a clearly marked placeholder hook

### OCR
- Expose Tesseract language and PSM in config
- Do not assume OCR will be perfect
- Build for debuggability
- Consider that white-on-black content may need inversion

### Preprocessing
Start simple:
- grayscale
- configurable upscale
- configurable threshold
- optional inversion

Only add more image processing if it clearly improves reliability.

## Code quality expectations

- Use descriptive names
- Add type hints where they improve clarity
- Add docstrings for public functions and modules where useful
- Keep functions reasonably small
- Handle obvious runtime errors cleanly
- Avoid giant classes when simple functions or small dataclasses will do

## Debuggability

Make it easy for the user to see what is happening.

Helpful features include:
- a `test` command
- logging OCR output
- optional debug image save paths
- explicit error messages if Tesseract is missing or config is incomplete

## What to avoid

Do not:
- invent an elaborate plugin framework
- add unnecessary dependencies
- hide behavior behind too much indirection
- overfit the code to one exact terminal theme
- silently swallow OCR/capture failures
- add speculative features not needed for v1

## Deliverables expected from you

When implementing, include:
- source code
- `README.md`
- sample config
- practical Ubuntu setup instructions

## Decision rule

When multiple approaches are possible, choose the one that:
- is easier to understand
- is easier to run locally
- is easier for the user to modify later
- is good enough for a first working version

## Final note

This is a pragmatic local automation tool, not a platform. Build the smallest clean thing that works.