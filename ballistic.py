import flet as ft
import math

def main(page: ft.Page):
    page.title = "BALLISTIC PRO"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 10
    page.scroll = ft.ScrollMode.ADAPTIVE

    # --- СТАН ПРОГРАМИ (БАЗА ДАНИХ) ---
    def get_initial_arsenal():
        return {
            "ОГБ-1": {"m": 3.1, "cx": 0.32, "s": 0.0038},
            "MOA-400": {"m": 4.61, "cx": 0.28, "s": 0.00528},
            "БЦ-2500": {"m": 3.0, "cx": 0.42, "s": 0.00636}
        }

    # Завантаження даних
    arsenal = page.client_storage.get("arsenal_data")
    if not arsenal:
        arsenal = get_initial_arsenal()
        page.client_storage.set("arsenal_data", arsenal)

    # --- ЕЛЕМЕНТИ ВВОДУ (ПОЛІТ) ---
    ent_h = ft.TextField(label="H (м)", value="1000", expand=1, keyboard_type="number")
    ent_v = ft.TextField(label="V (м/с)", value="5", expand=1, keyboard_type="number")
    ent_w = ft.TextField(label="W (вітер)", value="0", expand=1, keyboard_type="number")

    # --- ЕЛЕМЕНТИ ВВОДУ (БК) ---
    ent_m = ft.TextField(label="m (кг)", value="0", expand=1, text_size=12)
    ent_cx = ft.TextField(label="Cx", value="0", expand=1, text_size=12)
    ent_s = ft.TextField(label="S (м²)", value="0", expand=1, text_size=12)

    def update_bk_fields(e):
        if ammo_dd.value in arsenal:
            data = arsenal[ammo_dd.value]
            ent_m.value = str(data["m"])
            ent_cx.value = str(data["cx"])
            ent_s.value = str(data["s"])
            page.update()

    ammo_dd = ft.Dropdown(
        label="Боєприпас",
        options=[ft.dropdown.Option(k) for k in arsenal.keys()],
        value=list(arsenal.keys())[0],
        on_change=update_bk_fields,
        expand=True
    )

    # --- ЕЛЕМЕНТИ ВВОДУ (МЕТЕО) ---
    city_dd = ft.Dropdown(
        label="Місто",
        options=[ft.dropdown.Option(c) for c in ["Kramatorsk,UA", "Toretsk,UA", "Donetsk,UA", "Horlivka,UA"]],
        value="Kramatorsk,UA",
        expand=True
    )
    ent_temp = ft.TextField(label="T (°C)", value="15", expand=1)
    ent_press = ft.TextField(label="P (гПа)", value="1013", expand=1)
    lbl_rho = ft.Text("ρ (густина): 1.225", size=12, color="orange")

    # --- РЕЗУЛЬТАТИ ---
    res_angle = ft.Text("0.0°", size=22, weight="bold", color="blue")
    res_time = ft.Text("0.0 с", size=22, weight="bold", color="green")
    res_dist = ft.Text("0.0 м", size=22, weight="bold", color="red")
    lbl_status = ft.Text("", size=12)

    # --- ВІКНО НАЛАШТУВАНЬ (ШЕСТЕРНЯ) ---
    edit_name = ft.TextField(label="Назва БК")
    edit_m = ft.TextField(label="Маса")
    edit_cx = ft.TextField(label="Cx")
    edit_s = ft.TextField(label="S")

    def save_settings(e):
        name = edit_name.value
        if name:
            arsenal[name] = {
                "m": float(edit_m.value or 0),
                "cx": float(edit_cx.value or 0),
                "s": float(edit_s.value or 0)
            }
            page.client_storage.set("arsenal_data", arsenal)
            ammo_dd.options = [ft.dropdown.Option(k) for k in arsenal.keys()]
            ammo_dd.value = name
            update_bk_fields(None)
            settings_dialog.open = False
            page.update()

    settings_dialog = ft.AlertDialog(
        title=ft.Text("Налаштування БК"),
        content=ft.Column([edit_name, edit_m, edit_cx, edit_s], tight=True),
        actions=[ft.TextButton("Зберегти", on_click=save_settings)]
    )

    def open_settings(e):
        if ammo_dd.value in arsenal:
            data = arsenal[ammo_dd.value]
            edit_name.value = ammo_dd.value
            edit_m.value = str(data["m"])
            edit_cx.value = str(data["cx"])
            edit_s.value = str(data["s"])
            page.dialog = settings_dialog
            settings_dialog.open = True
            page.update()

    # --- ЛОГІКА ОБЧИСЛЕНЬ ---
    def get_weather(e):
        import requests
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city_dd.value}&appid=26419f7c6a93b4f4e515dcfcda96586b&units=metric"
            r = requests.get(url, timeout=5).json()
            ent_temp.value = str(r["main"]["temp"])
            ent_press.value = str(r["main"]["pressure"])
            lbl_status.value = "Погода оновлена ✅"
            calculate(None)
        except:
            lbl_status.value = "Помилка зв'язку ❌"
        page.update()

    def calculate(e):
        try:
            m, cx, s = float(ent_m.value), float(ent_cx.value), float(ent_s.value)
            h, v, w = float(ent_h.value), float(ent_v.value), float(ent_w.value)
            t, p = float(ent_temp.value), float(ent_press.value)

            rho = (p * 100) / (287.05 * (t + 273.15))
            lbl_rho.value = f"ρ (густина): {round(rho, 4)}"
            
            g = 9.81
            k = (rho * cx * s) / 2
            
            t_fall = math.sqrt(m/(k*g)) * math.acosh(math.exp(k*h/m))
            dist = (m/k) * math.log(1 + (k*(v+w)*t_fall)/m)
            angle = math.degrees(math.atan(h / dist)) if dist > 0 else 90

            res_dist.value = f"{round(dist, 1)} м"
            res_angle.value = f"{round(angle, 1)}°"
            res_time.value = f"{round(t_fall, 2)} с"
            lbl_status.value = "Розрахунок успішний"
        except Exception as err:
            lbl_status.value = f"Помилка даних"
        page.update()

    # --- ПОБУДОВА ЕКРАНУ ---
    page.add(
        ft.Text("BALLISTIC PRO", size=24, weight="bold"),
        ft.Row([ent_h, ent_v, ent_w]),
        ft.Divider(),
        
        ft.Row([
            ammo_dd, 
            ft.IconButton(icon=ft.icons.SETTINGS, on_click=open_settings)
        ]),
        ft.Row([ent_m, ent_cx, ent_s]),
        ft.Divider(),
        
        ft.Row([city_dd]),
        ft.Row([ent_temp, ent_press]),
        ft.ElevatedButton("ОНОВИТИ ПОГОДУ", on_click=get_weather, icon=ft.icons.CLOUD),
        lbl_rho,
        
        ft.Divider(),
        ft.ElevatedButton("РОЗРАХУВАТИ", on_click=calculate, bgcolor="green", color="white", height=50, width=500),
        
        # Таблиця як на малюнку
        ft.Container(
            content=ft.Row([
                ft.Column([ft.Text("КУТ", size=12), res_angle], expand=1, horizontal_alignment="center"),
                ft.Column([ft.Text("ЧАС", size=12), res_time], expand=1, horizontal_alignment="center"),
                ft.Column([ft.Text("ВІДСТАНЬ", size=12), res_dist], expand=1, horizontal_alignment="center"),
            ]),
            padding=15,
            border=ft.border.all(1, "white24"),
            border_radius=10
        ),
        lbl_status
    )
    
    # Заповнюємо поля БК при старті
    update_bk_fields(None)

ft.app(target=main)
