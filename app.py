import customtkinter as ctk
from tkinter import messagebox, filedialog
from bs4 import BeautifulSoup
from os import listdir, path, makedirs
from urllib.request import urlretrieve
from vdf import load, binary_load, binary_dump

class SteamCustomizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Steam Shortcut Customizer")
        self.root.iconbitmap(r"C:\Users\Silun\Documents\GitHub\steam\assets\batman.ico")  # Ensure the path is correct

        # Set the theme to Dark mode
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Use CTkFont for CustomTkinter
        self.font = ctk.CTkFont(family="Poppins", size=12)  # Updated to CTkFont

        # Steam Path Input
        self.steam_path_label = ctk.CTkLabel(root, text="Steam Path:", font=self.font)
        self.steam_path_label.pack(pady=5)
        self.steam_path_entry = ctk.CTkEntry(root, width=300, font=self.font)
        self.steam_path_entry.pack(pady=5)

        # Profile Selection
        self.profile_label = ctk.CTkLabel(root, text="Select Profile:", font=self.font)
        self.profile_label.pack(pady=5)
        self.profile_listbox = ctk.CTkTextbox(root, width=300, height=100, font=self.font)
        self.profile_listbox.pack(pady=5)

        # Game Selection
        self.game_label = ctk.CTkLabel(root, text="Select Game:", font=self.font)
        self.game_label.pack(pady=5)
        self.game_listbox = ctk.CTkTextbox(root, width=300, height=100, font=self.font)
        self.game_listbox.pack(pady=5)

        # SteamDB HTML File Input
        self.steamdb_file_label = ctk.CTkLabel(root, text="Path to steamdb.info HTML file:", font=self.font)
        self.steamdb_file_label.pack(pady=5)
        self.steamdb_file_entry = ctk.CTkEntry(root, width=300, font=self.font)
        self.steamdb_file_entry.pack(pady=5)

        # File Dialog Button
        self.file_dialog_button = ctk.CTkButton(root, text="Browse", command=self.browse_file, font=self.font)
        self.file_dialog_button.pack(pady=5)

        # Start Button
        self.start_button = ctk.CTkButton(root, text="Customize Shortcut", command=self.customize_shortcut, font=self.font)
        self.start_button.pack(pady=20)

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("HTML files", "*.html")])
        if file_path:
            self.steamdb_file_entry.delete(0, ctk.END)
            self.steamdb_file_entry.insert(0, file_path)

    def rungameid_to_appid(self, rungameid: int):
        return round(rungameid * 2.32830643653e-10)

    def customize_shortcut(self):
        steam_path = self.steam_path_entry.get()
        userdata_path = path.join(steam_path, "userdata")
        
        # Clear previous selections
        self.profile_listbox.delete("1.0", ctk.END)
        self.game_listbox.delete("1.0", ctk.END)
        
        # Fetch profiles
        profile_ids = self.fetch_profiles(userdata_path)
        if not profile_ids:
            messagebox.showerror("Error", "No profiles found in the specified Steam path.")
            return

        selected_profile_id = self.select_profile(profile_ids)
        if not selected_profile_id:
            return
        profile_path = path.join(userdata_path, selected_profile_id)

        # Fetch games
        games_dict = self.fetch_games(profile_path)
        if not games_dict:
            messagebox.showerror("Error", "No games found for the selected profile.")
            return

        selected_game = self.select_game(games_dict)
        if not selected_game:
            return

        steamdb_html_path = self.steamdb_file_entry.get()
        success = self.update_shortcut(profile_path, selected_game, steamdb_html_path)
        if success:
            messagebox.showinfo("Success", "Your game has been styled successfully! Please restart Steam to see the changes.")

    def fetch_profiles(self, userdata_path):
        profile_ids = []
        for index, profile_id in enumerate(listdir(userdata_path)):
            localconfig_path = path.join(userdata_path, profile_id, "config\\localconfig.vdf")
            username = load(open(localconfig_path))["UserLocalConfigStore"]["friends"]["PersonaName"]
            self.profile_listbox.insert(ctk.END, f"[{index}] {username} ({profile_id})\n")
            profile_ids.append(profile_id)
        return profile_ids

    def select_profile(self, profile_ids):
        while True:
            input_index = input("Select profile index: ")
            try:
                input_index = int(input_index)
                if input_index >= len(profile_ids) or input_index < 0:
                    print("Invalid input, try again!")
                else:
                    return profile_ids[input_index]
            except ValueError:
                print("Invalid input, try again!")

    def fetch_games(self, profile_path):
        screenshots_vdf_path = path.join(profile_path, "760\\screenshots.vdf")
        games_dict = load(open(screenshots_vdf_path))["screenshots"]["shortcutnames"]
        return games_dict

    def select_game(self, games_dict):
        for index, (id, name) in enumerate(games_dict.items()):
            self.game_listbox.insert(ctk.END, f"[{index}] {name} ({id})\n")

        while True:
            input_index = input("Select game index: ")
            try:
                input_index = int(input_index)
                if input_index >= len(games_dict) or input_index < 0:
                    print("Invalid input, try again!")
                else:
                    return list(games_dict.items())[input_index]
            except ValueError:
                print("Invalid input, try again!")

    def update_shortcut(self, profile_path, selected_game, steamdb_html_path):
        game_id, game_name = selected_game
        steamdb_html = BeautifulSoup(open(steamdb_html_path, encoding="utf-8"), "html.parser")

        # Extract data from SteamDB
        name = steamdb_html.select_one("#main > div > div.header-wrapper > div > div.pagehead > div.d-flex.flex-grow > h1").text
        appid = steamdb_html.select_one("#main > div > div.header-wrapper > div > div.row.app-row > div.span8 > table > tbody > tr:nth-child(1) > td:nth-child(2)").text

        # Additional SteamDB data extraction
        clienticon = steamdb_html.find("td", string="clienticon").find_next_sibling("td").find("a")["href"]
        icons_dir = path.join(profile_path, "config\\grid\\icons")
        makedirs(icons_dir, exist_ok=True)

        # Download the required icons and save them
        urlretrieve(clienticon, path.join(icons_dir, f"{game_id}.ico"))
        
        # Update the shortcut data
        shortcuts_vdf_path = path.join(profile_path, "config\\shortcuts.vdf")
        shortcuts_list = list(binary_load(open(shortcuts_vdf_path, "rb"))["shortcuts"].values())

        for shortcut in shortcuts_list:
            if shortcut["AppName"] == game_name:
                shortcut["AppName"] = name
                shortcut["icon"] = path.join(icons_dir, f"{game_id}.ico")
                break

        shortcuts_dict = {str(index): shortcut for index, shortcut in enumerate(shortcuts_list)}
        binary_dump({"shortcuts": shortcuts_dict}, open(shortcuts_vdf_path, "wb"))

        return True

# Main loop
if __name__ == "__main__":
    root = ctk.CTk()
    app = SteamCustomizerApp(root)
    root.mainloop()
