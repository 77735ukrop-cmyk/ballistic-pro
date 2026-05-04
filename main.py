import flet as ft
import math
import traceback

def main(page: ft.Page):
    page.title = "BALLISTIC PRO v2.7"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.ADAPTIVE
    
    def show_critical_error(e):
        page.clean()
        page.add(ft.Text(f"Критична помилка при запуску:\n{e}", color="red", size=20))
        page.update()

    try:
        # Стандартні дані
        DEFAULT_ARSENAL = {
            "ОГБ-1": {"m": 3.1, "cx": 0.32, "s": 0.0038},
            "MOA-400": {"m": 4.61, "cx": 0.28, "s": 0.00528}
        }

        if not page.client_storage.contains_key("arsenal"):
            page.client_storage.set("arsenal", DEFAULT_ARSENAL)
        
        arsenal = page.client_storage.get("arsenal")
        cities = ["Kramatorsk,UA", "Toretsk,UA", "Kostiantynivka,UA", "Donetsk,UA"]

        ent_h = ft.TextField(label="Висота (м)", value="1000", keyboard_type=ft.KeyboardType.NUMBER)
        ent_v = ft.TextField(label="V БПЛА (м/с)", value="5", keyboard_type=ft.KeyboardType.NUMBER)
        ent_w = ft.TextField(label="V вітру (+ попутний)", value="0", keyboard_type=ft.KeyboardType.NUMBER)
        
        ent_m = ft.TextField(label="Маса (кг)", value="3.1")
        ent_cx = ft.TextField(label="Cx (опір)", value="0.32")
        ent_s = ft.TextField(label="S (площа м2)", value="0.0038")
        
        ent_temp = ft.TextField(label="Темп. (°C)", value="15")
        ent_press = ft.TextField(label="Тиск (гПа)", value="1013")

        res_l = ft.Text("0.0 м", size=35, weight="bold", color="red")
        res_angle = ft.Text("0.0°", size=25, color="blue")
        lbl_status = ft.Text("Готовий до роботи", color="yellow")

        def get_weather(e):
            # Безпечний імпорт: викликається тільки при натисканні
            import requests 
            city = city_dropdown.value
            api_key = "26419f7c6a93b4f4e515dcfcda96586b"
            # ОБОВ'ЯЗКОВО HTTPS для Android
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
            try:
                r = requests.get(url, timeout=5).json()
                if r.get("cod") == 200:
                    ent_temp.value = str(r['main']['temp'])
                    ent_press.value = str(r['main']['pressure'])
                    lbl_status.value = f"Погода оновлена: {city}"
                else:
                    lbl_status.value = "Помилка API"
            except Exception as ex:
                lbl_status.value = f"Помилка мережі: {ex}"
            page.update()

        def calculate(e):
            try:
                m, cx, s = float(ent_m.value), float(ent_cx.value), float(ent_s.value)
                h, v, w = float(ent_h.value), float(ent_v.value), float(ent_w.value)
                t, p = float(ent_temp.value), float(ent_press.value)
                
                rho = (p * 100) / (287.05 * (t + 273.15))
                g = 9.81
                k = 0.5 * rho * cx * s
                
                if k < 0.000001:
                    t_fall = math.sqrt(2 * h / g)
                    dist_l = (v + w) * t_fall
                else:
                    t_fall = math.sqrt(m/(k*g)) * math.acosh(math.exp(k*h/m))
                    dist_l = (m/k) * math.log(1 + (k*(v+w)*t_fall)/m)
                    
                angle_deg = math.degrees(math.atan(h / dist_l)) if dist_l > 0 else 90
                res_l.value = f"{round(dist_l, 2)} м"
                res_angle.value = f"{round(angle_deg, 2)}°"
                lbl_status.value = "Розрахунок завершено"
            except Exception as ex:
                lbl_status.value = f"Помилка розрахунку: {ex}"
            page.update()

        city_dropdown = ft.Dropdown(
            label="Локація",
            options=[ft.dropdown.Option(c) for c in cities],
            value=cities[0]
        )

        page.add(
            ft.Column([
                ft.Text("BALLISTIC PRO v2.7", size=24, weight="bold", color="green"),
                ent_h, ent_v, ent_w,
                ft.Divider(),
                ft.Row([ent_m, ent_cx, ent_s], wrap=True),
                ft.Divider(),
                city_dropdown,
                ft.ElevatedButton("ОНОВИТИ ПОГОДУ", on_click=get_weather),
                ft.Row([ent_temp, ent_press], wrap=True),
                ft.Divider(),
                ft.ElevatedButton("РОЗРАХУВАТИ", on_click=calculate, bgcolor="green", color="white", height=60, width=400),
                ft.Text("ДИСТАНЦІЯ ВИНОСУ:"), res_l,
                ft.Text("КУТ КАМЕРИ:"), res_angle,
                lbl_status
            ], spacing=10)
        )
    except Exception as fatal_e:
        show_critical_error(fatal_e)

ft.app(target=main)
