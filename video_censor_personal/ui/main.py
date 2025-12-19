"""Bootstrap desktop application using CustomTkinter.

Provides a cross-platform graphical interface for Video Censor Personal.
"""

import customtkinter as ctk
from typing import Optional


class DesktopApp:
    """Desktop application window for Video Censor Personal.

    Uses CustomTkinter for modern, cross-platform UI appearance.
    Initializes a minimal window with empty frame content as a
    foundation for future feature expansion.

    Attributes:
        root: The CTk root window instance.
    """

    def __init__(self, title: str = "Video Censor Personal") -> None:
        """Initialize the desktop application.

        Args:
            title: Window title. Defaults to "Video Censor Personal".
        """
        self.root: ctk.CTk = ctk.CTk()
        self.root.title(title)
        self._setup_window()

    def _setup_window(self) -> None:
        """Configure window geometry and layout."""
        # Set default window size and position
        window_width = 800
        window_height = 600
        self.root.geometry(f"{window_width}x{window_height}")

        # Center window on screen
        self._center_window()

        # Configure grid layout for content
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Create empty content frame as placeholder
        content_frame = ctk.CTkFrame(self.root)
        content_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    def _center_window(self) -> None:
        """Center the window on the primary display."""
        self.root.update_idletasks()

        # Get window dimensions
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()

        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Calculate position
        x_position = (screen_width - window_width) // 2
        y_position = (screen_height - window_height) // 2

        self.root.geometry(
            f"{window_width}x{window_height}+{x_position}+{y_position}"
        )

    def run(self) -> None:
        """Start the application event loop.

        This method blocks until the window is closed.
        """
        self.root.mainloop()


def launch_app() -> None:
    """Entry point for launching the desktop application."""
    app = DesktopApp()
    app.run()


if __name__ == "__main__":
    launch_app()
