import flet as ft
import math
import traceback

# Базовий арсенал (зберігається в оперативній пам'яті)
arsenal = {
    "ОГБ-1": {"m": 3.1, "cx": 0.32, "s": 0.0038},
    "MOA-400": {"m": 4.61, "cx": 0.28, "s": 0.00528}
}
cities = ["Kramatorsk,UA", "Toretsk,UA", "Kostiantynivka,UA", "Donetsk,UA"]

def main(page: ft.Page):
    page.title = "BALLISTIC PRO v2.9"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.padding = 20
    
    def show_critical_error(e):
        page.clean()
        page.add(ft.Text(f"Помилка при запуску:\n{e}", color="red", size=20))
        page.update()

    try:
        # Поля введення
        ent_h = ft.TextField(label="Висота (м)", value="1000", keyboard_type=ft.KeyboardType.NUMBER)
        ent_v = ft.TextField(label="V БПЛА (м/с)", value="5", keyboard_type=ft.KeyboardType.NUMBER)
        ent_w = ft.TextField(label="V вітру (+ попутний)", value="0", keyboard_type=ft.KeyboardType.NUMBER)
        
        ent_m = ft.TextField(label="Маса (кг)", value="3.1", keyboard_type=ft.KeyboardType.NUMBER)
        ent_cx = ft.TextField(label="Cx (опір)", value="0.32", keyboard_type=ft.KeyboardType.NUMBER)
        ent_s = ft.TextField(label="S (площа м2)", value="0.0038", keyboard_type=ft.KeyboardType.NUMBER)
        
        ent_temp = ft.TextField(label="Темп. (°C)", value="15", keyboard_type=ft.KeyboardType.NUMBER)
        ent_press = ft.TextField(label="Тиск (гПа)", value="1013", keyboard_type=ft.KeyboardType.NUMBER)

        # Поля для додавання БК
        new_name = ft.TextField(label="Назва БК")
        new_m = ft.TextField(label="Маса (кг)", keyboard_type=ft.KeyboardType.NUMBER)
        new_cx = ft.TextField(label="Cx", keyboard_type=ft.KeyboardType.NUMBER)
        new_s = ft.TextField(label="S (площа)", keyboard_type=ft.KeyboardType.NUMBER)

        res_l = ft.Text("0.0 м", size=35, weight="bold", color="red")
        res_angle = ft.Text("0.0°", size=25, color="blue")
        lbl_status = ft.Text("Готовий", color="yellow")

        def refresh_dropdown():
            ammo_dropdown.options = [ft.dropdown.Option(k) for k in arsenal.keys()]
            page.update()

        def save_bk(e):
            name = new_name.value
            if name:
                # Захист від введення з комою замість крапки
                arsenal[name] = {
                    "m": float(new_m.value.replace(",", ".")), 
                    "cx": float(new_cx.value.replace(",", ".")), 
                    "s": float(new_s.value.replace(",", "."))
                }
                refresh_dropdown()
                lbl_status.value = f"БК '{name}' додано на час сесії!"
                page.update()

        def on_ammo_change(e):
            data = arsenal.get(ammo_dropdown.value, arsenal["ОГБ-1"])
            ent_m.value = str(data['m'])
            ent_cx.value = str(data['cx'])
            ent_s.value = str(data['s'])
            page.update()

        # Створюємо меню БЕЗ параметра on_change
        ammo_dropdown = ft.Dropdown(
            label="Оберіть БК",
            options=[ft.dropdown.Option(k) for k in arsenal.keys()],
            value="ОГБ-1"
        )
        
        # Безпечне призначення події (працюватиме на будь-якій версії Flet)
        if hasattr(ammo_dropdown, 'on_change'):
            ammo_dropdown.on_change = on_ammo_change
        if hasattr(ammo_dropdown, 'on_select'):
            ammo_dropdown.on_select = on_ammo_change
        if hasattr(ammo_dropdown, 'on_text_change'):
            ammo_dropdown.on_text_change = on_ammo_change
        
        city_dropdown = ft.Dropdown(
            label="Локація",
            options=[ft.dropdown.Option(c) for c in cities],
            value=cities[0]
        )

        def get_weather(e):
            try:
                import requests 
                city = city_dropdown.value
                api_key = "26419f7c6a93b4f4e515dcfcda96586b"
                url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
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
                # Читаємо значення, автоматично замінюючи кому на крапку (якщо користувач помилився)
                m = float(ent_m.value.replace(",", "."))
                cx = float(ent_cx.value.replace(",", "."))
                s = float(ent_s.value.replace(",", "."))
                h = float(ent_h.value.replace(",", "."))
                v = float(ent_v.value.replace(",", "."))
                w = float(ent_w.value.replace(",", "."))
                t = float(ent_temp.value.replace(",", "."))
                p = float(ent_press.value.replace(",", "."))
                
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
                lbl_status.value = "Успіх"
            except Exception as ex:
                lbl_status.value = f"Помилка даних: {ex}"
            page.update()

        page.add(
            ft.Column([
                ft.Text("BALLISTIC PRO v2.9", size=24, weight="bold", color="green"),
                ent_h, ent_v, ent_w,
                ft.Divider(),
                ammo_dropdown,
                ft.Row([ent_m, ent_cx, ent_s], wrap=True),
                ft.ExpansionTile(
                    title=ft.Text("Додати БК (тимчасово)"),
                    controls=[
                        new_name, new_m, new_cx, new_s,
                        ft.ElevatedButton("ДОДАТИ", on_click=save_bk)
                    ]
                ),
                ft.Divider(),
                city_dropdown,
                ft.ElevatedButton("ОТРИМАТИ ПОГОДУ", on_click=get_weather),
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
