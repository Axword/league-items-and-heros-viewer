import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
import io
import requests
import json

class YourAppClass:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("League of Legends - Champion Viewer")

        # Set the starting screen size and center it
        window_width = 800
        window_height = 1200
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.map_11_var = tk.BooleanVar(value=True)

        self.cache_dir = "cache"
        self.image_cache_dir = os.path.join(self.cache_dir, "images")
        self.champion_images = {}
        self.champions = {}

        # Initialize GUI elements
        self.init_gui()
        self.latest_version = self.get_latest_version()
        self.champions = self.fetch_data("pl_PL", "championFull")
        self.load_images_from_cache()
        self.update_champion_grid()

        self.root.mainloop()

    def init_gui(self):
        # Create a canvas to hold the image grid
        self.canvas = tk.Canvas(self.root)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create a vertical scrollbar
        self.scrollbar = tk.Scrollbar(self.root, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Create a frame to hold the champion images
        self.frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")

        # Bind the frame to update the scroll region
        self.frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Bind mouse wheel event for scrolling
        self.canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)

    def load_images_from_cache(self):
        """Load champion images from cache to avoid fetching each time."""
        if not os.path.exists(self.image_cache_dir):
            os.makedirs(self.image_cache_dir)
        for champion_id, champion in self.champions.items():
            image_path = os.path.join(self.image_cache_dir, f"{champion_id}.png")
            if os.path.exists(image_path):
                img = Image.open(image_path).resize((64, 64))  # Resize for display
                self.champion_images[champion["name"]] = ImageTk.PhotoImage(img)

    def update_champion_grid(self):
        """Update the grid of champions displayed as images."""
        for widget in self.frame.winfo_children():
            widget.destroy()  # Clear existing images

        # Create a grid of images
        for index, (champion_id, champion) in enumerate(self.champions.items()):
            img = self.fetch_image(f"https://ddragon.leagueoflegends.com/cdn/{self.latest_version}/img/champion/{champion_id}.png", f"{champion_id}.png")
            self.champion_images[champion["name"]] = ImageTk.PhotoImage(img)

            # Create a button for each image
            btn = tk.Button(self.frame, image=self.champion_images[champion["name"]], command=lambda champ=champion: self.show_champion_details(champ))
            btn.grid(row=index // 10, column=index % 10, padx=5, pady=5)  # Arrange in a grid of 10 per row

    def fetch_image(self, image_url, image_name):
        """Fetch an image from the URL and cache it locally."""
        image_path = os.path.join(self.image_cache_dir, image_name)

        if os.path.exists(image_path):
            return Image.open(image_path)  # Load from cache

        # If not cached, download it
        img_data = requests.get(image_url).content
        img = Image.open(io.BytesIO(img_data)).resize((64, 64))
        img.save(image_path)  # Save to cache
        return img

    def show_champion_details(self, champion_data):
        """Display champion details in a new window."""
        details_window = tk.Toplevel(self.root)
        details_window.title(champion_data["name"])
        details_label = tk.Label(details_window, text=f"Name: {champion_data['name']}\nDescription: {champion_data.get('description', 'No description')}")
        details_label.pack(padx=10, pady=10)

    def get_latest_version(self):
        """Fetch the latest version of the game."""
        url = "https://ddragon.leagueoflegends.com/api/versions.json"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()[0]  # Return the latest version
        else:
            messagebox.showerror("Error", "Failed to fetch the latest version!")
            return "12.6.1"  # Default value in case of error

    def fetch_data(self, language="pl_PL", data_type="championFull"):
        """Fetch data for champions or items."""
        url = f"https://ddragon.leagueoflegends.com/cdn/{self.latest_version}/data/{language}/{data_type}.json"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()["data"]
        else:
            messagebox.showerror("Error", "Failed to fetch data!")
            return {}

    def on_mouse_wheel(self, event):
        """Handle mouse wheel scrolling."""
        # Scroll the canvas based on the mouse wheel movement
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

# Run the application
if __name__ == "__main__":
    YourAppClass()
