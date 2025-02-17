import os
import pandas as pd

folder_path = "Daten\RAVDESS" 

# Mapping für die Emotionen nach RAVDESS Schema
emotion_map = {
    "01": "Neutral",
    "02": "Neutral",
    "03": "Freude",
    "04": "Trauer",
    "05": "Wut",
    "06": "Angst",
    "07": "Ekel",
    "08": "Überraschung"
}

# get all names
file_list = [f for f in os.listdir(folder_path) if f.endswith('.mp4')]

# Liste zum Speichern der Daten
data = []

for file in file_list:

    base_name = os.path.splitext(file)[0]
    parts = base_name.split('-')
    
    # Der 3. Teil entspricht der Emotion
    emotion_code = parts[2]
    emotion = emotion_map.get(emotion_code, "Unknown")
    
    data.append({
        "Name": file,
        "Real": emotion,
        "Model": emotion  # TODO: Hier noch die funktion hinzufügen, die die model ergebnisse matcht
    })

df = pd.DataFrame(data)

print(df)
df.to_csv('Daten\Data_Lables.csv', index=False, header=True)