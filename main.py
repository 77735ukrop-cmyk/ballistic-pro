import flet as ft
import math
import os
import json

# --- ПАМ'ЯТЬ ---
APP_DIR = os.path.dirname(__file__)
ARSENAL_FILE = os.path.join(APP_DIR, "arsenal.json")
CITIES_FILE = os.path.join(APP_DIR, "cities.json")

def load_data(file_path, default_data):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return default_data.copy()

def save_data(file_path, data):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except: pass

arsenal = load_data(ARSENAL_FILE, {"ОГБ-1": {"m": 3.1, "cx": 0.32, "s": 0.0038}})
cities_list = load_data(CITIES_FILE, ["Kramatorsk,UA"])

def main(page: ft.Page):
    page.title = "BALLISTIC PRO v3.9"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.padding = ft.padding.only(top=50, left=15, right=15, bottom=20)
    
    try:
        # === ВЕРХНІЙ БЛОК: ВХІДНІ ДАНІ ===
        ent_h = ft.TextField(label="Висота(м)", value="1500", expand=True, keyboard_type=ft.KeyboardType.NUMBER)
        ent_v = ft.TextField(label="БПЛА(м/с)", value="28", expand=True, keyboard_type=ft.KeyboardType.NUMBER)
        ent_w_drone = ft.TextField(label="Вітер Висота", value="-10", expand=True, keyboard_type=ft.KeyboardType.NUMBER)

        # === БЛОК: АРСЕНАЛ ===
        lbl_m = ft.TextField(label="m (кг)", value="3.1", read_only=True, expand=True, text_size=12)
        lbl_cx = ft.TextField(label="Cx", value="0.32", read_only=True, expand=True, text_size=12)
        lbl_s = ft.TextField(label="S (м²)", value="0.0038", read_only=True, expand=True, text_size=12)

        ammo_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option(k) for k in arsenal.keys()],
            value=list(arsenal.keys())[0], expand=True
        )
        
        def on_ammo_change(e):
            d = arsenal.get(ammo_dropdown.value, list(arsenal.values())[0])
            lbl_m.value, lbl_cx.value, lbl_s.value = str(d['m']), str(d['cx']), str(d['s'])
            page.update()
        ammo_dropdown.on_change = on_ammo_change

        # === БЛОК: МЕТЕО ===
        city_dropdown = ft.Dropdown(options=[ft.dropdown.Option(c) for c in cities_list], value=cities_list[0], expand=True)
        ent_temp = ft.TextField(label="t (°C)", value="20", expand=True, keyboard_type=ft.KeyboardType.NUMBER)
        ent_press = ft.TextField(label="P (гПа)", value="1013", expand=True, keyboard_type=ft.KeyboardType.NUMBER)
        ent_w_ground = ft.TextField(label="Вітер Земля", value="-2", expand=True, keyboard_type=ft.KeyboardType.NUMBER)
        lbl_rho = ft.Text("ρ: ---", color="#90CAF9", weight="bold")
        lbl_status = ft.Text("", size=11)

        def get_weather(e):
            try:
                import requests 
                url = f"https://api.openweathermap.org/data/2.5/weather?q={city_dropdown.value}&appid=26419f7c6a93b4f4e515dcfcda96586b&units=metric"
                r = requests.get(url, timeout=5).json()
                if r.get("cod") == 200:
                    ent_temp.value = str(r['main']['temp'])
                    ent_press.value = str(r['main']['pressure'])
                    ent_w_ground.value = str(r['wind']['speed']) # Підтягуємо вітер біля землі
                    lbl_status.value = f"OK: {r['name']}"; lbl_status.color = "green"
                else: lbl_status.value = "Помилка API"; lbl_status.color = "red"
            except: lbl_status.value = "Немає мережі"; lbl_status.color =
