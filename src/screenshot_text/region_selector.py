"""Interactive region selection overlay."""

from __future__ import annotations

from dataclasses import dataclass

from .config import RegionConfig


class RegionSelectionError(RuntimeError):
    """Raised when the screen region picker cannot start."""


def select_region() -> RegionConfig | None:
    """Open a fullscreen overlay and return the selected screen region."""

    try:
        import tkinter as tk
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on system package.
        raise RegionSelectionError(
            "Tkinter is unavailable. Install `python3-tk` and run from a desktop session."
        ) from exc

    try:
        overlay = _SelectionOverlay(tk)
    except tk.TclError as exc:  # pragma: no cover - depends on live desktop access.
        raise RegionSelectionError(
            "Could not open the region selector. Run this from an Ubuntu X11 desktop session."
        ) from exc

    return overlay.run()


@dataclass(slots=True)
class _SelectionOverlay:
    tk: object

    def __post_init__(self) -> None:
        tk = self.tk
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-alpha", 0.25)
        self.root.attributes("-topmost", True)
        self.root.configure(background="black")
        self.root.title("Select OCR Region")

        self.canvas = tk.Canvas(
            self.root,
            bg="black",
            cursor="crosshair",
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_text(
            24,
            24,
            anchor="nw",
            fill="white",
            text="Click and drag to select a region. Press Esc to cancel.",
            font=("TkDefaultFont", 16),
        )

        self.start_x = 0
        self.start_y = 0
        self.rectangle_id: int | None = None
        self.selection: RegionConfig | None = None

        self.canvas.bind("<ButtonPress-1>", self._on_button_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_button_release)
        self.root.bind("<Escape>", self._on_cancel)

    def run(self) -> RegionConfig | None:
        self.root.focus_force()
        self.root.mainloop()
        self.root.destroy()
        return self.selection

    def _on_button_press(self, event) -> None:
        self.start_x = event.x
        self.start_y = event.y

        if self.rectangle_id is not None:
            self.canvas.delete(self.rectangle_id)

        self.rectangle_id = self.canvas.create_rectangle(
            self.start_x,
            self.start_y,
            self.start_x,
            self.start_y,
            outline="#ffcc00",
            width=2,
        )

    def _on_drag(self, event) -> None:
        if self.rectangle_id is None:
            return

        self.canvas.coords(
            self.rectangle_id,
            self.start_x,
            self.start_y,
            event.x,
            event.y,
        )

    def _on_button_release(self, event) -> None:
        left = min(self.start_x, event.x)
        top = min(self.start_y, event.y)
        width = abs(event.x - self.start_x)
        height = abs(event.y - self.start_y)

        if width < 2 or height < 2:
            if self.rectangle_id is not None:
                self.canvas.delete(self.rectangle_id)
                self.rectangle_id = None
            return

        self.selection = RegionConfig(x=left, y=top, width=width, height=height)
        self.root.quit()

    def _on_cancel(self, _event) -> None:
        self.selection = None
        self.root.quit()
