# screenshot-text

`screenshot-text` is a small Ubuntu/X11 utility that lets you select a screen region, capture it on a loop, run OCR with Tesseract, and hook your own action logic onto accepted text updates.

It is designed for pragmatic local use, especially for reading terminal text shared through Teams where OCR can be noisy and debuggability matters.

## What It Does

- `select`: draw and save a screen rectangle
- `test`: capture once, preprocess once, OCR once, and print the result
- `watch`: keep polling the saved region and emit accepted text changes

## Requirements

- Ubuntu desktop session
- X11 session
- Python 3.11+
- `python3-tk`
- `tesseract-ocr`

Install the system packages first:

```bash
sudo apt install python3-tk tesseract-ocr
```

Then install the Python dependencies:

```bash
uv sync
```

## Config

The runtime config lives at:

```text
~/.config/screenshot-text/config.toml
```

You can create it from the sample file:

```bash
mkdir -p ~/.config/screenshot-text
cp config.sample.toml ~/.config/screenshot-text/config.toml
```

Every command also accepts `--config /path/to/config.toml`.

## Usage

Select a region:

```bash
uv run screenshot-text select
```

Capture once and print raw OCR output:

```bash
uv run screenshot-text test
```

Also print normalized text:

```bash
uv run screenshot-text test --print-normalized
```

Save debug images from the `test` run:

```bash
uv run screenshot-text test --debug-dir ~/.cache/screenshot-text/debug
```

Watch the region continuously:

```bash
uv run screenshot-text watch
```

## Config Fields

```toml
interval_seconds = 2.0

[region]
x = 100
y = 200
width = 800
height = 300

[ocr]
lang = "eng"
psm = 6

[preprocess]
grayscale = true
upscale = 2
threshold = 180
invert = false

[detection]
require_stable_reads = 1

[debug]
save_dir = "/home/you/.cache/screenshot-text/debug"
```

Notes:

- `psm = 6`, `7`, and `11` are the main modes worth trying first.
- `invert = true` is often helpful for white-on-black terminal themes.
- `require_stable_reads = 2` can reduce noisy flicker if OCR is unstable.

## Debugging Workflow

If OCR quality is poor:

1. Run `test --debug-dir ...` to save the raw and preprocessed images.
2. Inspect whether the selected region is tight enough.
3. Try raising `upscale`.
4. Try toggling `invert`.
5. Try different `psm` values.
6. Adjust `threshold`.

## Custom Actions

The placeholder hook lives in `src/screenshot_text/actions.py`.

When `watch` accepts new text, it:

1. prints the accepted normalized text
2. calls `handle_accepted_text(...)`

That is the intended place to add your own regex matching, keyword triggers, command execution, or other local automation logic.

## Notes

- This first version is intentionally X11-first. Wayland desktops may block or alter screenshot/overlay behavior.
- If Tesseract is missing, the CLI will fail with a direct install-oriented error instead of silently doing nothing.
