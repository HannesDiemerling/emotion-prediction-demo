import tkinter as tk
import vlc
import pandas as pd
import os
import random
from PIL import Image, ImageTk

class ScienceNightApp:
    def __init__(self, root):

        # ===============================
        # Konfiguration, easy maintanance
        # ===============================

        self.config = {
            "csv_folder": "Daten",
            "csv_filename": "Data_Lables.csv",
            "video_folder": os.path.join("Daten", "RAVDESS"),
            "mask_folder": os.path.join("Daten", "MaskeRAVDESS"),
            "leaderboard_file": os.path.join("Daten", "Leaderboard.csv"),
            "video_ext": ".mp4",
            "mask_ext": ".png",
            "window_title": "Lange Nacht der Wissenschaft",
            "window_size": "800x600",
            "top_frame_bg": "black",
            "bottom_frame_bg": "gray",
            "header_bg": "lightgray",
            "leaderboard_text": "Leaderboard",
            "next_text": "Weiter",
            "emotions": ["Freude", "Wut", "Trauer", "Angst",  "Überraschung", "Ekel", "Neutral"],
            "button_padx": 10,
            "button_pady": 10,
            "font": ("Arial", 16),
            "bottom_frame_height": 300,
            "answers_frame_height": 80,
            "answer_fg": "#FFFFFF",
            "answer_font": ("Helvetica", 18, "bold"),
            "active_user_bg": "#FFFF99"  # hellgelb
        }
        
        # ===============================
        # Basic elements
        # ===============================

        self.root = root
        self.root.title(self.config["window_title"])
        self.root.geometry(self.config["window_size"])
        
        # CSV-Data loading
        self.csv_data = self.load_csv()
        self.video_info = self.build_video_info(self.csv_data)
        
        # Leaderboard loading (Or initialisation)
        self.load_leaderboard_csv()
        
        # VLC-Player instance
        self.vlc_instance = vlc.Instance()
        self.player = self.vlc_instance.media_player_new()
        
        # ===============================
        # User managment
        # ===============================

        self.active_user = None
        self.user_correct = 0
        self.user_wrong = 0
        
        # UI build
        self.build_ui()
        
        # start first loop
        self.start_new_cycle()
    
    # ===============================
    # CSV- and Data func
    # ===============================

    def load_csv(self):
        """Lädt die CSV-Datei und gibt ein pandas DataFrame zurück."""
        csv_path = os.path.join(self.config["csv_folder"], self.config["csv_filename"])
        try:
            data = pd.read_csv(csv_path)
            return data
        except Exception as e:
            print("Fehler beim Laden der CSV-Datei:", e)
            return pd.DataFrame()
    
    def build_video_info(self, csv_data):
        """Erstellt ein Dictionary, das jedem Videodateinamen die zugehörigen Antworten zuordnet."""
        info = {}
        for _, row in csv_data.iterrows():
            video_filename = row["Name"]
            info[video_filename] = {
                "richtige": row["Real"],
                "modell": row["Model"]
            }
        return info
    
    def load_leaderboard_csv(self):
        """Lädt die Leaderboard-Daten aus einer CSV-Datei oder erstellt sie, falls nicht vorhanden."""
        leaderboard_file = self.config["leaderboard_file"]
        if os.path.exists(leaderboard_file):
            try:
                self.leaderboard_data = pd.read_csv(leaderboard_file)
            except Exception as e:
                print("Fehler beim Laden der Leaderboard CSV:", e)
                self.leaderboard_data = pd.DataFrame(columns=["Name", "Richtig", "Falsch", "Anzahl", "Prozent"])
        else:
            # Erstelle initiale Leaderboard-Daten mit dem KI-Eintrag
            self.leaderboard_data = pd.DataFrame([{
                "Name": "Die Emotions KI",
                "Richtig": 800,
                "Falsch": 200,
                "Anzahl": 1000,
                "Prozent": "80%"
            }])
            self.leaderboard_data.to_csv(leaderboard_file, index=False)
    
    def save_leaderboard_csv(self):
        """Speichert die aktuellen Leaderboard-Daten in die CSV-Datei."""
        leaderboard_file = self.config["leaderboard_file"]
        self.leaderboard_data.to_csv(leaderboard_file, index=False)
    
    # ===============================
    # UI-Aufbau
    # ===============================

    def build_ui(self):
        """Erstellt alle UI-Elemente in modularen Abschnitten, inklusive Header für Nutzerverwaltung."""
        # --- Header Frame Login (Left) and Leaderboard-Info (Right)---
        self.header_frame = tk.Frame(self.root, bg=self.config["header_bg"], height=50)
        self.header_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Left: "Neuer Nutzer" and "Beenden"
        self.header_left = tk.Frame(self.header_frame, bg=self.config["header_bg"])
        self.header_left.pack(side=tk.LEFT, padx=10)
        self.new_user_button = tk.Button(self.header_left, text="Neuer Nutzer", command=self.show_new_user_window, relief="flat", font=self.config["font"])
        self.new_user_button.pack(side=tk.TOP, pady=2)
        self.logout_button = tk.Button(self.header_left, text="Beenden", command=self.user_logout, relief="flat", font=self.config["font"])
        self.logout_button.pack(side=tk.TOP, pady=2)
        
        # Right: stats
        self.header_right = tk.Frame(self.header_frame, bg=self.config["header_bg"])
        self.header_right.pack(side=tk.RIGHT, padx=10)
        self.username_label = tk.Label(self.header_right, text="Kein Nutzer", bg=self.config["header_bg"], font=self.config["font"])
        self.username_label.pack(side=tk.TOP)

        self.stats_frame = tk.Frame(self.header_right, bg=self.config["header_bg"])
        self.stats_frame.pack(side=tk.TOP)
        self.correct_label = tk.Label(self.stats_frame, text="R: 0", fg="green", bg=self.config["header_bg"], font=self.config["font"])
        self.correct_label.pack(side=tk.LEFT)
        self.separator_label = tk.Label(self.stats_frame, text=" | ", bg=self.config["header_bg"], font=self.config["font"])
        self.separator_label.pack(side=tk.LEFT)
        self.wrong_label = tk.Label(self.stats_frame, text="F: 0", fg="blue", bg=self.config["header_bg"], font=self.config["font"])
        self.wrong_label.pack(side=tk.LEFT)
        
        # --- Middle: Video ---
        self.top_frame = tk.Frame(self.root, bg=self.config["top_frame_bg"])
        self.top_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # --- Down area ---
        self.bottom_frame = tk.Frame(self.root, bg=self.config["bottom_frame_bg"],
                                     height=self.config["bottom_frame_height"])
        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Down: Frame
        self.answers_frame = tk.Frame(self.bottom_frame, bg=self.config["bottom_frame_bg"],
                                      height=self.config["answers_frame_height"])
        self.answers_frame.pack(side=tk.TOP, fill=tk.X)
        
        self.buttons_frame = tk.Frame(self.bottom_frame, bg=self.config["bottom_frame_bg"])
        self.buttons_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        
        # Down Left: Leaderboard
        self.left_frame = tk.Frame(self.buttons_frame, bg=self.config["bottom_frame_bg"], width=100)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.leaderboard_button = tk.Button(self.left_frame, text=self.config["leaderboard_text"],
                                            command=self.show_leaderboard, relief="flat", font=self.config["font"])
        self.leaderboard_button.pack(padx=self.config["button_padx"], pady=self.config["button_pady"])
        
        # Down Middle: Emotion Buttons
        self.center_frame = tk.Frame(self.buttons_frame, bg=self.config["bottom_frame_bg"])
        self.center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.emotion_buttons = {}  # Wird beim Aktivieren der Buttons befüllt
        
        # Down Right: Next Button
        self.right_frame = tk.Frame(self.buttons_frame, bg=self.config["bottom_frame_bg"], width=100)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.next_button = tk.Button(self.right_frame, text=self.config["next_text"],
                                     state=tk.DISABLED, command=self.next_cycle,
                                     relief="flat", font=self.config["font"])
        self.next_button.pack(padx=self.config["button_padx"], pady=self.config["button_pady"])
        
        # Updating
        self.top_frame.update()
        self.player.set_hwnd(self.top_frame.winfo_id())
        
        # Cache answer
        self.answer_label = None
        self.model_label = None
        self.mask_label = None
    
    # ===============================
    # User Methods
    # ===============================

    def show_new_user_window(self):
        """Öffnet ein kleines Fenster zur Eingabe eines neuen Nutzernamens."""
        self.new_user_window = tk.Toplevel(self.root)
        self.new_user_window.title("Neuer Nutzer")
        self.new_user_window.geometry("300x150")
        
        tk.Label(self.new_user_window, text="Nutzername:").pack(pady=10)
        self.username_entry = tk.Entry(self.new_user_window, font=self.config["font"])
        self.username_entry.pack(pady=5)
        
        button_frame = tk.Frame(self.new_user_window)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Zurück", command=self.new_user_window.destroy, font=self.config["font"]).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Erstellen", command=self.create_user, font=self.config["font"]).pack(side=tk.LEFT, padx=10)
    
    def create_user(self):
        """Erstellt einen neuen Nutzer basierend auf der Eingabe."""
        name = self.username_entry.get().strip()
        if name:
            if self.active_user:
                self.archive_current_user()
            self.active_user = name
            self.user_correct = 0
            self.user_wrong = 0
            self.update_user_info_display()
        self.new_user_window.destroy()
    
    def user_logout(self):
        """Beendet den aktuellen Nutzer, archiviert dessen Daten."""
        if self.active_user:
            self.archive_current_user()
            self.active_user = None
            self.user_correct = 0
            self.user_wrong = 0
            self.update_user_info_display()
    
    def update_user_info_display(self):
        """Aktualisiert die Anzeige des aktiven Nutzers und der Statistiken."""
        if self.active_user:
            self.username_label.config(text=self.active_user)
            self.correct_label.config(text=f"R: {self.user_correct}")
            self.wrong_label.config(text=f"F: {self.user_wrong}")
        else:
            self.username_label.config(text="Kein Nutzer")
            self.correct_label.config(text="R: 0")
            self.wrong_label.config(text="F: 0")
    
    def archive_current_user(self):
        """Archiviert den aktuellen Nutzer in der Leaderboard CSV."""
        if not self.active_user:
            return
        name = self.active_user
        if name in self.leaderboard_data["Name"].values:
            idx = self.leaderboard_data[self.leaderboard_data["Name"] == name].index[0]
            self.leaderboard_data.at[idx, "Richtig"] += self.user_correct
            self.leaderboard_data.at[idx, "Falsch"] += self.user_wrong
        else:
            new_entry = {
                "Name": name,
                "Richtig": self.user_correct,
                "Falsch": self.user_wrong
            }
            new_df = pd.DataFrame([new_entry])
            self.leaderboard_data = pd.concat([self.leaderboard_data, new_df], ignore_index=True)
        self.leaderboard_data["Anzahl"] = self.leaderboard_data["Richtig"] + self.leaderboard_data["Falsch"]
        self.leaderboard_data["Prozent"] = (self.leaderboard_data["Richtig"] / self.leaderboard_data["Anzahl"] * 100).round().astype(int).astype(str) + "%"
        self.save_leaderboard_csv()
    
    def show_leaderboard(self):
        """Öffnet ein Fenster mit einem scrollbaren, spaltenbasierten Leaderboard.
        Es wird eine Kopfzeile angezeigt. Der aktuelle Nutzer wird hervorgehoben."""
        self.leaderboard_window = tk.Toplevel(self.root)
        self.leaderboard_window.title("Leaderboard")
        self.leaderboard_window.geometry("800x600")
        
        # copy leaderboard data
        temp_data = self.leaderboard_data.copy()
        
        # add activ user
        if self.active_user:
            if self.active_user in temp_data["Name"].values:
                idx = temp_data[temp_data["Name"] == self.active_user].index[0]
                temp_data.at[idx, "Richtig"] += self.user_correct
                temp_data.at[idx, "Falsch"] += self.user_wrong
            else:
                new_entry = {"Name": self.active_user, "Richtig": self.user_correct, "Falsch": self.user_wrong}
                new_df = pd.DataFrame([new_entry])
                temp_data = pd.concat([temp_data, new_df], ignore_index=True)
        
        # Update stats
        temp_data["Anzahl"] = temp_data["Richtig"] + temp_data["Falsch"]
        temp_data["Prozent"] = (temp_data["Richtig"] / temp_data["Anzahl"] * 100).round().astype(int).astype(str) + "%"
        # calc ratio
        temp_data["ratio"] = temp_data.apply(lambda row: row["Richtig"] / row["Anzahl"] if row["Anzahl"] > 0 else 0, axis=1)
        # relativ to "AI"
        ki_row = temp_data[temp_data["Name"] == "Die Emotions KI"]
        ki_ratio = ki_row.iloc[0]["ratio"] if not ki_row.empty else 0.8
        
        # Sort by Ratio
        sorted_data = temp_data.sort_values(by="ratio", ascending=False)
        
        # activate scrolling
        canvas = tk.Canvas(self.leaderboard_window)
        scrollbar = tk.Scrollbar(self.leaderboard_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Header for leaderboard
        header_frame = tk.Frame(scrollable_frame, padx=5, pady=5, bg="lightblue")
        header_frame.grid(row=0, column=0, sticky="ew")
        tk.Label(header_frame, text="Name", font=self.config["font"], width=12, bg="lightblue").grid(row=0, column=0, padx=5)
        tk.Label(header_frame, text="Richtig", font=self.config["font"], width=8, bg="lightblue").grid(row=0, column=1, padx=5)
        tk.Label(header_frame, text="Falsch", font=self.config["font"], width=8, bg="lightblue").grid(row=0, column=2, padx=5)
        tk.Label(header_frame, text="Anzahl", font=self.config["font"], width=8, bg="lightblue").grid(row=0, column=3, padx=5)
        tk.Label(header_frame, text="Prozent", font=self.config["font"], width=8, bg="lightblue").grid(row=0, column=4, padx=5)
        
        # generate rows
        row_idx = 1
        for _, row in sorted_data.iterrows():
            # Colour of bourder: gray one for "AI", green for Ratio >= "AI", blue otherwise.
            if row["Name"] == "Die Emotions KI":
                border_color = "gray"
            elif row["ratio"] >= ki_ratio:
                border_color = "green"
            else:
                border_color = "blue"
            # Highlight active user
            bg_color = self.config["active_user_bg"] if self.active_user == row["Name"] else "white"
            entry_frame = tk.Frame(scrollable_frame, padx=5, pady=5, bg=bg_color, highlightthickness=2, highlightbackground=border_color)
            entry_frame.grid(row=row_idx, column=0, sticky="ew", padx=5, pady=2)
            tk.Label(entry_frame, text=row["Name"], font=self.config["font"], width=12, bg=bg_color).grid(row=0, column=0, padx=5)
            tk.Label(entry_frame, text=f'{row["Richtig"]}', fg="green", font=self.config["font"], width=8, bg=bg_color).grid(row=0, column=1, padx=5)
            tk.Label(entry_frame, text=f'{row["Falsch"]}', fg="blue", font=self.config["font"], width=8, bg=bg_color).grid(row=0, column=2, padx=5)
            tk.Label(entry_frame, text=f'{row["Anzahl"]}', font=self.config["font"], width=8, bg=bg_color).grid(row=0, column=3, padx=5)
            tk.Label(entry_frame, text=row["Prozent"], font=self.config["font"], width=8, bg=bg_color).grid(row=0, column=4, padx=5)
            row_idx += 1
        
        # "Zurück"-Button
        tk.Button(self.leaderboard_window, text="Zurück", command=self.leaderboard_window.destroy, font=self.config["font"]).pack(pady=10, anchor="se")
    
    # ===============================
    # Zyklussteuerung und UI-Updates
    # ===============================

    def clear_video_area(self):
        """Bereinigt den oberen Bereich und stoppt die Videowiedergabe."""
        self.player.stop()
        if self.answer_label:
            self.answer_label.destroy()
            self.answer_label = None
        if self.model_label:
            self.model_label.destroy()
            self.model_label = None
        if self.mask_label:
            self.mask_label.destroy()
            self.mask_label = None
    
    def clear_emotion_buttons(self):
        """Entfernt alle Emotionstasten aus dem zentralen Bereich."""
        for btn in self.emotion_buttons.values():
            btn.destroy()
        self.emotion_buttons = {}
    
    def start_new_cycle(self):
        """Startet einen neuen Zyklus: Video auswählen, abspielen und Emotionstasten aktivieren."""
        self.clear_video_area()
        self.clear_emotion_buttons()
        self.next_button.config(state=tk.DISABLED)
        
        # delete old text
        for widget in self.answers_frame.winfo_children():
            widget.destroy()
        
        # pick video by random
        video_folder = self.config["video_folder"]
        video_files = [f for f in os.listdir(video_folder) if f.lower().endswith(self.config["video_ext"])]
        if not video_files:
            print("Keine Videodateien gefunden im Ordner:", video_folder)
            return
        self.current_video = random.choice(video_files)
        video_path = os.path.join(video_folder, self.current_video)
        
        # load video in vlc
        media = self.vlc_instance.media_new(video_path)
        self.player.set_media(media)
        self.player.play()
        
        # wait for 1 sek for lable buttons, preventing random clicking
        self.root.after(1000, self.enable_emotion_buttons)
    
    def enable_emotion_buttons(self):
        """Erstellt und zeigt die Emotionstasten im zentralen Bereich an."""
        for emotion in self.config["emotions"]:
            btn = tk.Button(self.center_frame, text=emotion,
                            command=lambda em=emotion: self.emotion_selected(em),
                            relief="flat", font=self.config["font"], bg="#F0F0F0", fg="black")
            btn.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5, pady=5)
            self.emotion_buttons[emotion] = btn
    
    def emotion_selected(self, selected_emotion):
        """
        Wird aufgerufen, wenn eine Emotion ausgewählt wurde.
        - Hebt den gewählten Button hervor (grün, wenn korrekt; blau, wenn falsch) und entfernt die übrigen.
        - Deaktiviert weitere Klicks.
        - Stoppt die Videowiedergabe.
        - Zeigt modern formatierte Antworttexte im unteren Bereich an.
        - Lädt das Maskenbild (im oberen Bereich) und aktiviert den "Weiter"-Button.
        """

        if all(btn["state"] == "disabled" for btn in self.emotion_buttons.values()):
            return
        
        # Deactivate buttons
        for btn in self.emotion_buttons.values():
            btn.config(state=tk.DISABLED)
        
        # check answer
        info = self.video_info.get(self.current_video, {"richtige": "N/A", "modell": "N/A"})
        is_correct = (selected_emotion == info["richtige"])
        
        # update stats
        if self.active_user:
            if is_correct:
                self.user_correct += 1
            else:
                self.user_wrong += 1
            self.update_user_info_display()
        
        # highlight button in colour, green (Right) or blue (wrong)
        for emotion, btn in self.emotion_buttons.items():
            if emotion == selected_emotion:
                btn.config(bg="green" if is_correct else "blue")
            else:
                btn.destroy()
        
        self.player.stop()
        
        # Grid for lables
        self.answer_label = tk.Label(self.answers_frame,
                                     text=f"Richtige Antwort: {info['richtige']}",
                                     fg=self.config["answer_fg"],
                                     bg=self.config["bottom_frame_bg"],
                                     font=self.config["answer_font"])
        self.answer_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        self.model_label = tk.Label(self.answers_frame,
                                    text=f"Modell-Antwort: {info['modell']}",
                                    fg=self.config["answer_fg"],
                                    bg=self.config["bottom_frame_bg"],
                                    font=self.config["answer_font"])
        self.model_label.grid(row=0, column=1, padx=20, pady=10, sticky="w")
        
        # showing masks
        # TODO: Hier statt der verwendeten dummy daten XAI für den jeweiligen clip zeigen.
        mask_folder = self.config["mask_folder"]
        mask_filename = os.path.splitext(self.current_video)[0] + self.config["mask_ext"]
        mask_path = os.path.join(mask_folder, mask_filename)
        if os.path.exists(mask_path):
            try:
                image = Image.open(mask_path)
                top_width = self.top_frame.winfo_width()
                top_height = self.top_frame.winfo_height()
                if top_width > 0 and top_height > 0:
                    image = image.resize((top_width, top_height), Image.Resampling.LANCZOS)
                self.mask_image = ImageTk.PhotoImage(image)
                self.mask_label = tk.Label(self.top_frame, image=self.mask_image)
                self.mask_label.place(x=0, y=0, relwidth=1, relheight=1)
            except Exception as e:
                print("Fehler beim Laden des Maskenbildes:", e)
        else:
            print("Maskenbild nicht gefunden:", mask_path)
        
        # "Weiter"-Button activate
        self.next_button.config(state=tk.NORMAL)
    
    def next_cycle(self):
        """Wird beim Klick auf 'Weiter' aufgerufen und startet den nächsten Zyklus."""
        self.clear_video_area()
        self.clear_emotion_buttons()
        self.next_button.config(state=tk.DISABLED)
        self.start_new_cycle()

# ===============================
# Hauptprogramm starten
# ===============================

if __name__ == "__main__":
    root = tk.Tk()
    app = ScienceNightApp(root)
    root.mainloop()