import flet as ft
import math
import requests

arsenal = {
    "ОГБ-1": {"m": 3.1, "cx": 0.32, "s": 0.0038},
    "MOA-120": {"m": 1.59, "cx": 0.25, "s": 0.00212},
    "MOA-400": {"m": 4.61, "cx": 0.28, "s": 0.00528},
    "MOA-900": {"m": 10.44, "cx": 0.3, "s": 0.01038},
    "БЦ-2500": {"m": 3.0, "cx": 0.42, "s": 0.00636},
    "БЦ-3500": {"m": 4.0, "cx": 0.45, "s": 0.00709},
    "БЦ-4500": {"m": 5.6, "cx": 0.48, "s": 0.00709}
}

cities = ["Kramatorsk,UA", "Toretsk,UA", "Kostiantynivka,UA", "Donetsk,UA"]

def main(page: ft.Page):
    page.title = "BALLISTIC PRO"
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.padding = 20

    # 1. Поля введення (ініціалізація)
    ent_h = ft.TextField(label="Висота (м)", value="1000", keyboard_type=ft.KeyboardType.NUMBER)
    ent_v = ft.TextField(label="V БПЛА (м/с)", value="5", keyboard_type=ft.KeyboardType.NUMBER)
    ent_w = ft.TextField(label="V вітру (м/с)", value="0", keyboard_type=ft.KeyboardType.NUMBER)
    
    ent_m = ft.TextField(label="Маса (кг)", value="0")
    ent_cx = ft.TextField(label="Cx", value="0")
    ent_s = ft.TextField(label="S (площа)", value="0")
    
    ent_temp = ft.TextField(label="Температура (°C)", value="15")
    ent_press = ft.TextField(label="Тиск (гПа)", value="1013")

    ammo_dropdown = ft.Dropdown(
        label="Оберіть Арсенал (БК)",
        options=[ft.dropdown.Option(k) for k in arsenal.keys()],
        value="ОГБ-1"
    )
    
    city_dropdown = ft.Dropdown(
        label="Локація",
        options=[ft.dropdown.Option(c) for c in cities],
        value=cities[0]
    )

    res_l = ft.Text("0.0 м", size=35, weight="bold", color="red")
    res_angle = ft.Text("0.0°", size=25, color="blue")
    lbl_status = ft.Text("", color="yellow")

    # Функції
    def get_weather(e):
        city = city_dropdown.value
        api_key = "26419f7c6a93b4f4e515dcfcda96586b"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        try:
            r = requests.get(url, timeout=5).json()
            if r.get("cod") == 200:
                ent_temp.value = str(r['main']['temp'])
                ent_press.value = str(r['main']['pressure'])
                lbl_status.value = f"Погода оновлена"
            else:
                lbl_status.value = "Помилка погоди"
        except:
            lbl_status.value = "Немає зв'язку"
        page.update()

    def calculate(e):
        try:
            selected_bk = ammo_dropdown.value
            if selected_bk in arsenal:
                data = arsenal[selected_bk]
                ent_m.value = str(data['m'])
                ent_cx.value = str(data['cx'])
                ent_s.value = str(data['s'])
            
            m = float(ent_m.value)
            cx = float(ent_cx.value)
            s = float(ent_s.value)
            h = float(ent_h.value)
            v = float(ent_v.value)
            w = float(ent_w.value)
            t = float(ent_temp.value)
            p = float(ent_press.value)

            rho = (p * 100) / (287.05 * (t + 273.15))
            g = 9.81
            
            t_fall = math.sqrt(2*m/(rho*cx*s*g)) * math.acosh(math.exp(rho*cx*s*h/(2*m)))
            dist_l = (2*m/(rho*cx*s)) * math.log(1 + (rho*cx*s*(v+w)*t_fall)/(2*m))
            angle_deg = math.degrees(math.atan(h / dist_l)) if dist_l > 0 else 90
            
            res_l.value = f"{round(dist_l, 2)} м"
            res_angle.value = f"{round(angle_deg, 2)}°"
            lbl_status.value = f"Розраховано для {selected_bk}"
            page.update()
        except Exception as ex:
            lbl_status.value = f"Помилка: {ex}"
            page.update()

    # ЄДИНИЙ інтерфейс
    page.add(
        ft.Column([
            ft.Text("BALLISTIC PRO v2.0", size=24, weight="bold"),
            ent_h, ent_v, ent_w,
            ft.Divider(),
            ammo_dropdown,
            ft.Row([ent_m, ent_cx, ent_s], wrap=True), # wrap=True запобігає вильоту за екран
            ft.Divider(),
            city_dropdown,
            ft.ElevatedButton("ОНОВИТИ ПОГОДУ", on_click=get_weather),
            ft.Row([ent_temp, ent_press], wrap=True),
            ft.Divider(),
            ft.ElevatedButton("РОЗРАХУВАТИ", on_click=calculate, bgcolor="green", color="white", height=60, width=400),
            ft.Text("ДИСТАНЦІЯ СКИДУ:"), res_l,
            ft.Text("КУТ НАХИЛУ:"), res_angle,
            lbl_status
        ], spacing=10)
    )

ft.app(target=main)
