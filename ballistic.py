import flet as ft
import math

def main(page: ft.Page):
    # Головний обробник помилок, щоб не було чорного екрана
    try:
        page.title = "BALLISTIC PRO"
        page.theme_mode = ft.ThemeMode.DARK
        page.padding = 10
        page.scroll = ft.ScrollMode.ADAPTIVE

        # --- БАЗОВІ ДАНІ ---
        DEFAULT_ARSENAL = {
            "ОГБ-1": {"m": 3.1, "cx": 0.32, "s": 0.0038},
            "MOA-400": {"m": 4.61, "cx": 0.28, "s": 0.00528},
            "БЦ-2500": {"m": 3.0, "cx": 0.42, "s": 0.00636}
        }

        # --- ЕЛЕМЕНТИ ІНТЕРФЕЙСУ ---
        ent_h = ft.TextField(label="H (м)", value="1000", expand=1, keyboard_type=ft.KeyboardType.NUMBER)
        ent_v = ft.TextField(label="V (м/с)", value="5", expand=1, keyboard_type=ft.KeyboardType.NUMBER)
        ent_w = ft.TextField(label="W (вітер)", value="0", expand=1, keyboard_type=ft.KeyboardType.NUMBER)

        ent_m = ft.TextField(label="m (кг)", value="0", expand=1)
        ent_cx = ft.TextField(label="Cx", value="0", expand=1)
        ent_s = ft.TextField(label="S (м²)", value="0", expand=1)

        ammo_dd = ft.Dropdown(label="Боєприпас", expand=True)
        city_dd = ft.Dropdown(
            label="Місто",
            options=[ft.dropdown.Option(c) for c in ["Kramatorsk,UA", "Toretsk,UA", "Donetsk,UA", "Horlivka,UA"]],
            value="Kramatorsk,UA",
            expand=True
        )

        ent_temp = ft.TextField(label="T (°C)", value="15", expand=1)
        ent_press = ft.TextField(label="P (гПа)", value="1013", expand=1)
        lbl_rho = ft.Text("ρ (густина): ---", size=14, color="orange")

        res_angle = ft.Text("0.0°", size=22, weight="bold", color="blue")
        res_time = ft.Text("0.0 с", size=22, weight="bold", color="green")
        res_dist = ft.Text("0.0 м", size=22, weight="bold", color="red")
        lbl_status = ft.Text("Система готова", size=12, color="white60")

        # --- ЛОГІКА ---
        def get_arsenal():
            data = page.client_storage.get("arsenal_data")
            return data if data else DEFAULT_ARSENAL

        def update_fields(e=None):
            arsenal = get_arsenal()
            if ammo_dd.value in arsenal:
                d = arsenal[ammo_dd.value]
                ent_m.value = str(d["m"])
                ent_cx.value = str(d["cx"])
                ent_s.value = str(d["s"])
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
                lbl_status.value = "Розраховано успішно"
                lbl_status.color = "green"
            except:
                lbl_status.value = "Помилка в числах"
                lbl_status.color = "red"
            page.update()

        def get_weather(e):
            import requests # Імпорт всередині
            try:
                url = f"http://api.openweathermap.org/data/2.5/weather?q={city_dd.value}&appid=26419f7c6a93b4f4e515dcfcda96586b&units=metric"
                r = requests.get(url, timeout=5).json()
                ent_temp.value = str(r["main"]["temp"])
                ent_press.value = str(r["main"]["pressure"])
                lbl_status.value = "Погода оновлена"
                calculate(None)
            except:
                lbl_status.value = "Помилка погоди (перевірте інтернет)"
            page.update()

        # --- ДІАЛОГ НАЛАШТУВАНЬ ---
        edit_name = ft.TextField(label="Назва")
        edit_m = ft.TextField(label="Маса")
        edit_cx = ft.TextField(label="Cx")
        edit_s = ft.TextField(label="S")

        def save_bk(e):
            if edit_name.value:
                current_arsenal = get_arsenal()
                current_arsenal[edit_name.value] = {
                    "m": float(edit_m.value or 0),
                    "cx": float(edit_cx.value or 0),
                    "s": float(edit_s.value or 0)
                }
                page.client_storage.set("arsenal_data", current_arsenal)
                refresh_dd()
                dlg.open = False
                page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Редагувати БК"),
            content=ft.Column([edit_name, edit_m, edit_cx, edit_s], tight=True),
            actions=[ft.TextButton("Зберегти", on_click=save_bk)]
        )

        def open_settings(e):
            arsenal = get_arsenal()
            if ammo_dd.value in arsenal:
                d = arsenal[ammo_dd.value]
                edit_name.value = ammo_dd.value
                edit_m.value = str(d["m"])
                edit_cx.value = str(d["cx"])
                edit_s.value = str(d["s"])
            page.dialog = dlg
            dlg.open = True
            page.update()

        def refresh_dd():
            arsenal = get_arsenal()
            ammo_dd.options = [ft.dropdown.Option(k) for k in arsenal.keys()]
            if not ammo_dd.value: ammo_dd.value = list(arsenal.keys())[0]

        # --- ЗБІРКА ІНТЕРФЕЙСУ ---
        page.add(
            ft.Text("BALLISTIC PRO v2.1", size=22, weight="bold"),
            ft.Row([ent_h, ent_v, ent_w]),
            ft.Divider(height=5),
            ft.Row([ammo_dd, ft.IconButton(ft.icons.SETTINGS, on_click=open_settings)]),
            ft.Row([ent_m, ent_cx, ent_s]),
            ft.Divider(height=5),
            city_dd,
            ft.Row([ent_temp, ent_press]),
            ft.ElevatedButton("ОНОВИТИ МЕТЕО", icon=ft.icons.CLOUD, on_click=get_weather, width=400),
            lbl_rho,
            ft.Divider(height=10),
            ft.ElevatedButton("РОЗРАХУВАТИ", bgcolor="green", color="white", height=60, width=400, on_click=calculate),
            ft.Container(
                padding=10,
                border=ft.border.all(1, "white24"),
                border_radius=10,
                content=ft.Row([
                    ft.Column([ft.Text("КУТ", size=10), res_angle], expand=1, horizontal_alignment="center"),
                    ft.Column([ft.Text("ЧАС", size=10), res_time], expand=1, horizontal_alignment="center"),
                    ft.Column([ft.Text("ВІДСТАНЬ", size=10), res_dist], expand=1, horizontal_alignment="center"),
                ])
            ),
            lbl_status
        )

        # Фінальна ініціалізація після page.add()
        refresh_dd()
        update_fields()

    except Exception as e:
        # Це врятує від чорного екрана, показавши помилку
        page.add(ft.Text(f"Критична помилка: {e}", color="red"))

ft.app(target=main)
