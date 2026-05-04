import flet as ft
import math
import requests
import json
import os

# --- РОБОТА З ДАНИМИ (Android-сумісність) ---
def get_data_path():
    if os.environ.get("FLET_PLATFORM") == "android":
        return os.path.join(os.environ.get("HOME"), "arsenal_data.json")
    return "arsenal_data.json"

DATA_FILE = get_data_path()

DEFAULT_ARSENAL = {
    "ОГБ-1": {"m": 3.1, "cx": 0.32, "s": 0.0038},
    "MOA-400": {"m": 4.61, "cx": 0.28, "s": 0.00528}
}

def load_arsenal():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            return DEFAULT_ARSENAL
    return DEFAULT_ARSENAL

def save_arsenal(data):
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f)
    except:
        pass

arsenal = load_arsenal()
cities = ["Kramatorsk,UA", "Toretsk,UA", "Kostiantynivka,UA", "Donetsk,UA"]

def main(page: ft.Page):
    page.title = "BALLISTIC PRO"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.padding = 20

    # Поля введення
    ent_h = ft.TextField(label="Висота (м)", value="1000", keyboard_type=ft.KeyboardType.NUMBER)
    ent_v = ft.TextField(label="V БПЛА (м/с)", value="5", keyboard_type=ft.KeyboardType.NUMBER)
    ent_w = ft.TextField(label="V вітру (м/с, + попутний)", value="0", keyboard_type=ft.KeyboardType.NUMBER)
    
    ent_m = ft.TextField(label="Маса (кг)", value="3.1")
    ent_cx = ft.TextField(label="Cx (опір)", value="0.32")
    ent_s = ft.TextField(label="S (площа м2)", value="0.0038")
    
    ent_temp = ft.TextField(label="Темп. (°C)", value="15")
    ent_press = ft.TextField(label="Тиск (гПа)", value="1013")

    new_name = ft.TextField(label="Назва БК")
    new_m = ft.TextField(label="Маса (кг)")
    new_cx = ft.TextField(label="Cx")
    new_s = ft.TextField(label="S (площа)")

    def on_ammo_change(e):
        data = arsenal[ammo_dropdown.value]
        ent_m.value = str(data['m'])
        ent_cx.value = str(data['cx'])
        ent_s.value = str(data['s'])
        page.update()

    ammo_dropdown = ft.Dropdown(
        label="Оберіть БК",
        options=[ft.dropdown.Option(k) for k in arsenal.keys()],
        value="ОГБ-1",
        on_change=on_ammo_change
    )
    
    city_dropdown = ft.Dropdown(
        label="Локація",
        options=[ft.dropdown.Option(c) for c in cities],
        value=cities[0]
    )

    res_l = ft.Text("0.0 м", size=35, weight="bold", color="red")
    res_angle = ft.Text("0.0°", size=25, color="blue")
    lbl_status = ft.Text("", color="yellow")

    def get_weather(e):
        city = city_dropdown.value
        api_key = "26419f7c6a93b4f4e515dcfcda96586b"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        try:
            r = requests.get(url, timeout=5).json()
            if r.get("cod") == 200:
                ent_temp.value = str(r['main']['temp'])
                ent_press.value = str(r['main']['pressure'])
                lbl_status.value = f"Погода: {city} оновлена"
            else:
                lbl_status.value = "Помилка погоди"
        except:
            lbl_status.value = "Немає мережі"
        page.update()

    def calculate(e):
        try:
            m, cx, s = float(ent_m.value), float(ent_cx.value), float(ent_s.value)
            h, v, w = float(ent_h.value), float(ent_v.value), float(ent_w.value)
            t, p = float(ent_temp.value), float(ent_press.value)
            rho = (p * 100) / (287.05 * (t + 273.15))
            g = 9.81
            k = 0.5 * rho * cx * s
            
            # Уникнення ділення на нуль, якщо k = 0
            if k == 0:
                t_fall = math.sqrt(2 * h / g)
                dist_l = (v + w) * t_fall
            else:
                t_fall = math.sqrt(m/(k*g)) * math.acosh(math.exp(k*h/m))
                dist_l = (m/k) * math.log(1 + (k*(v+w)*t_fall)/m)
                
            angle_deg = math.degrees(math.atan(h / dist_l)) if dist_l > 0 else 90
            res_l.value = f"{round(dist_l, 2)} м"
            res_angle.value = f"{round(angle_deg, 2)}°"
            lbl_status.value = "Розраховано успішно"
            page.update()
        except Exception as ex:
            lbl_status.value = f"Помилка: {ex}"
            page.update()

    page.add(
        ft.Column([
            ft.Text("BALLISTIC PRO v2.2", size=24, weight="bold", color="green"),
            ent_h, ent_v, ent_w,
            ft.Divider(),
            ammo_dropdown,
            ft.Row([ent_m, ent_cx, ent_s], wrap=True),
            ft.Divider(),
            city_dropdown,
            ft.ElevatedButton("ОНОВИТИ ПОГОДУ", on_click=get_weather),
            ft.Row([ent_temp, ent_press], wrap=True),
            ft.Divider(),
            ft.ElevatedButton("РОЗРАХУВАТИ", on_click=calculate, bgcolor="green", color="white", height=60, width=400),
            ft.Text("ДИСТАНЦІЯ СКИДУ:"), res_l,
            ft.Text("КУТ КАМЕРИ:"), res_angle,
            lbl_status
        ], spacing=10)
    )

ft.app(target=main)
