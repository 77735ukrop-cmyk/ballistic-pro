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
        except: 
            pass
    return default_data.copy()

def save_data(file_path, data):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except: 
        pass

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
            lbl_m.value = str(d['m'])
            lbl_cx.value = str(d['cx'])
            lbl_s.value = str(d['s'])
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
                    lbl_status.value = f"OK: {r['name']}"
                    lbl_status.color = "green"
                else: 
                    lbl_status.value = "Помилка API"
                    lbl_status.color = "red"
            except: 
                lbl_status.value = "Немає мережі"
                lbl_status.color = "red"
            page.update()

        # === РЕЗУЛЬТАТИ ===
        res_time = ft.Text("--")
        res_dist = ft.Text("--", color="red")
        res_angle = ft.Text("--", color="blue")

        def calculate(e):
            try:
                m = float(lbl_m.value.replace(",", "."))
                cx = float(lbl_cx.value.replace(",", "."))
                s = float(lbl_s.value.replace(",", "."))
                h = float(ent_h.value.replace(",", "."))
                v_drone = float(ent_v.value.replace(",", "."))
                w_high = float(ent_w_drone.value.replace(",", "."))
                w_low = float(ent_w_ground.value.replace(",", "."))
                temp = float(ent_temp.value.replace(",", "."))
                press = float(ent_press.value.replace(",", "."))
                
                rho = (press * 100) / (287.05 * (temp + 273.15))
                lbl_rho.value = f"ρ: {round(rho, 5)}"
                g = 9.81
                k = 0.5 * rho * cx * s
                
                # --- СИМУЛЯЦІЯ З ГРАДІЄНТОМ ВІТРУ ---
                dt = 0.01
                x = 0.0
                y = 0.0
                vx = v_drone
                vy = 0.0
                t_fall = 0.0
                
                while y < h:
                    curr_w = w_high + (w_low - w_high) * (y / h)
                    
                    v_air_x = vx - curr_w
                    v_air_y = vy
                    V_total = math.sqrt(v_air_x**2 + v_air_y**2)
                    
                    ax = -(k / m) * V_total * v_air_x
                    ay = g - (k / m) * V_total * v_air_y
                    
                    vx += ax * dt
                    vy += ay * dt
                    x += vx * dt
                    y += vy * dt
                    t_fall += dt
                    
                    if t_fall > 120: 
                        break
                
                res_time.value = f"{round(t_fall, 3)} с"
                res_dist.value = f"{round(x, 2)} м"
                res_angle.value = f"{round(math.degrees(math.atan(h/x)), 2)}°" if x > 0 else "90°"
            except: 
                lbl_status.value = "Помилка даних!"
                lbl_status.color = "red"
            page.update()

        # === КОМПОНУВАННЯ ===
        page.add(ft.Column([
            ft.Text("ВХІДНІ ДАНІ", weight="bold", size=18, color="#90CAF9"),
            ft.Row([ent_h, ent_v, ent_w_drone]),
            ft.Divider(height=15, color="transparent"),
            
            ft.Text("АРСЕНАЛ", weight="bold", size=16, color="#90CAF9"),
            ft.Row([ammo_dropdown, ft.ElevatedButton("➕", width=50), ft.ElevatedButton("⚙️", width=50)]),
            ft.Row([lbl_m, lbl_cx, lbl_s]),
            ft.Divider(height=15, color="transparent"),
            
            ft.Text("МЕТЕО", weight="bold", size=16, color="#90CAF9"),
            ft.Row([city_dropdown, ft.ElevatedButton("➕", width=50), ft.ElevatedButton("⚙️", width=50)]),
            ft.ElevatedButton("ОНОВИТИ ПОГОДУ", on_click=get_weather, width=400),
            ft.Row([ent_temp, ent_press, ent_w_ground]),
            ft.Row([lbl_rho, lbl_status]),
            ft.Divider(height=15, color="transparent"),
            
            ft.ElevatedButton("РОЗРАХУВАТИ", on_click=calculate, bgcolor="green", color="white", height=50, width=400),
            ft.Container(padding=10, border=ft.border.all(1, "grey"), border_radius=10, content=ft.Column([
                ft.Row([
                    ft.Column([ft.Text("ЧАС ПАДІННЯ", size=10), res_time], expand=True, horizontal_alignment="center"),
                    ft.Column([ft.Text("ВІДСТАНЬ", size=10), res_dist], expand=True, horizontal_alignment="center")
                ]),
                ft.Divider(),
                ft.Row([ft.Text("📷 КУТ КАМЕРИ:", size=12), res_angle], alignment="center")
            ]))
        ], spacing=5))
        
        on_ammo_change(None)
        
    except Exception as fatal_e: 
        page.add(ft.Text(f"Fatal: {fatal_e}", color="red"))

ft.app(target=main)
