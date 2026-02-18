import tkinter as tk
from tkinter import ttk

class LoadingScreen:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the main window initially
        
        # Create loading window
        self.loading_window = tk.Toplevel(self.root)
        self.loading_window.title("Loading")
        
        # Remove window decorations
        self.loading_window.overrideredirect(True)
        
        # Calculate center position
        window_width = 300
        window_height = 100
        screen_width = self.loading_window.winfo_screenwidth()
        screen_height = self.loading_window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.loading_window.geometry(f'{window_width}x{window_height}+{x}+{y}')
        
        # Create a frame with a border
        self.frame = ttk.Frame(self.loading_window, padding="10")
        self.frame.grid(row=0, column=0, sticky="nsew")
        
        # Loading label
        self.status_label = ttk.Label(self.frame, text="Initializing...", font=('Helvetica', 10))
        self.status_label.grid(row=0, column=0, pady=(0, 10))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            self.frame,
            mode='determinate',
            length=200
        )
        self.progress_bar.grid(row=1, column=0)
        
        # Center the frame
        self.loading_window.grid_rowconfigure(0, weight=1)
        self.loading_window.grid_columnconfigure(0, weight=1)
        
        # Keep the window on top
        self.loading_window.lift()
        self.loading_window.attributes('-topmost', True)
        
        # Initialize progress value
        self.progress_value = 0
        self.progress_bar['value'] = 0
        
    def update_progress(self, value, text):
        """Update progress bar value and status text"""
        try:
            if self.loading_window.winfo_exists():
                self.progress_bar['value'] = value
                self.status_label['text'] = text
                self.loading_window.update()
        except tk.TclError as e:
            # Log the error or handle it as needed
            print(f"Error updating progress: {e}")
        
    def finish(self):
        """Close the loading screen"""
        try:
            if self.loading_window.winfo_exists():
                self.loading_window.destroy()
            if self.root.winfo_exists():
                self.root.destroy()
        except tk.TclError as e:
            # Log the error or handle it as needed
            print(f"Error closing loading screen: {e}")
