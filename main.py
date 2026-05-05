import flet as ft
import math

# --- ПОВНА БАЗА ДАНИХ АРСЕНАЛУ ---
arsenal = {
    "ОГБ-1": {"m": 3.1, "cx": 0.32, "s": 0.0038},
    "MOA-120": {"m": 1.59, "cx": 0.25, "s": 0.00212},
    "MOA-400": {"m": 4.61, "cx": 0.28, "s": 0.00528},
    "MOA-900": {"m": 10.44, "cx": 0.3, "s": 0.01038},
    "БЦ-2500": {"m": 3.0, "cx": 0.42, "s": 0.00636},
    "БЦ-3500": {"m": 4.0, "cx": 0.45, "s": 0.00709},
    "БЦ-4500": {"m": 5.6, "cx": 0.48, "s": 0.00709}
}

cities = ["Kramatorsk,UA", "Kostiantynivka,UA", "Toretsk,UA", "Horlivka,UA", "Donetsk,UA"]

def main(page: ft.Page):
    page.title = "BALLISTIC PRO v3.5"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.padding = ft.padding.only(top=50, left=15, right=15, bottom=20)
    
    def show_critical_error(e):
        page.clean()
        page.add(ft.Text(f"Помилка при запуску:\n{e}", color="red", size=20))
        page.update()

    try:
        # === ВЕРХНІЙ БЛОК: ВХІДНІ ДАНІ ===
        ent_h = ft.TextField(label="Висота(м)", value="1500", expand=True, keyboard_type=ft.KeyboardType.NUMBER)
        ent_v = ft.TextField(label="БПЛА(м/с)", value="25", expand=True, keyboard_type=ft.KeyboardType.NUMBER)
        ent_w = ft.TextField(label="Вітер(м/с)", value="-10", expand=True, keyboard_type=ft.KeyboardType.NUMBER)

        # === БЛОК: АРСЕНАЛ ===
        lbl_m = ft.TextField(label="m (кг)", value="4.61", read_only=True, expand=True, text_size=12)
        lbl_cx = ft.TextField(label="Cx", value="0.28", read_only=True, expand=True, text_size=12)
        lbl_s = ft.TextField(label="S (м²)", value="0.00528", read_only=True, expand=True, text_size=12)

        def on_ammo_change(e):
            data = arsenal.get(ammo_dropdown.value, arsenal["MOA-400"])
            lbl_m.value = str(data['m'])
            lbl_cx.value = str(data['cx'])
            lbl_s.value = str(data['s'])
            page.update()

        ammo_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option(k) for k in arsenal.keys()],
            value="MOA-400",
            expand=True
        )
        
        if hasattr(ammo_dropdown, 'on_change'): ammo_dropdown.on_change = on_ammo_change
        elif hasattr(ammo_dropdown, 'on_select'): ammo_dropdown.on_select = on_ammo_change

        # --- ДІАЛОГ ДОДАВАННЯ БК ---
        dlg_name = ft.TextField(label="Назва")
        dlg_m = ft.TextField(label="Маса", keyboard_type=ft.KeyboardType.NUMBER)
        dlg_cx = ft.TextField(label="Cx", keyboard_type=ft.KeyboardType.NUMBER)
        dlg_s = ft.TextField(label="S", keyboard_type=ft.KeyboardType.NUMBER)

        def save_bk(e):
            if dlg_name.value:
                arsenal[dlg_name.value] = {
                    "m": float(dlg_m.value.replace(",", ".")), 
                    "cx": float(dlg_cx.value.replace(",", ".")), 
                    "s": float(dlg_s.value.replace(",", "."))
                }
                ammo_dropdown.options = [ft.dropdown.Option(k) for k in arsenal.keys()]
                ammo_dropdown.value = dlg_name.value
                on_ammo_change(None)
                add_bk_dialog.open = False
                page.update()

        add_bk_dialog = ft.AlertDialog(
            title=ft.Text("Новий БК"),
            content=ft.Column([dlg_name, dlg_m, dlg_cx, dlg_s], tight=True),
            actions=[ft.TextButton("Зберегти", on_click=save_bk)]
        )
        page.overlay.append(add_bk_dialog)

        # === БЛОК: МЕТЕО ===
        city_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option(c) for c in cities],
            value="Horlivka,UA",
            expand=True
        )
        # Нове поле для ручного вводу міста
        ent_custom_city = ft.TextField(label="Інше (напр. Dnipro)", expand=True)
        
        ent_temp = ft.TextField(label="t (°C)", value="6.95", expand=True, keyboard_type=ft.KeyboardType.NUMBER)
        ent_press = ft.TextField(label="P (гПа)", value="1016", expand=True, keyboard_type=ft.KeyboardType.NUMBER)
        lbl_rho = ft.Text("ρ: 1.26364", color="cyan", weight="bold")
        lbl_status = ft.Text("", size=11)

        def get_weather(e):
            try:
                import requests 
                target_city = ent_custom_city.value.strip()
                if not target_city:
                    target_city = city_dropdown.value
                
                url = f"https://api.openweathermap.org/data/2.5/weather?q={target_city}&appid=26419f7c6a93b4f4e515dcfcda96586b&units=metric"
                r = requests.get(url, timeout=5).json()
                if r.get("cod") == 200:
                    ent_temp.value = str(r['main']['temp'])
                    ent_press.value = str(r['main']['pressure'])
                    lbl_status.value = f"OK: {r['name']}"
                    lbl_status.color = "green"
                else: 
                    lbl_status.value = "Місто не знайдено"
                    lbl_status.color = "red"
            except: 
                lbl_status.value = "Немає мережі"
                lbl_status.color = "red"
            page.update()

        # === РЕЗУЛЬТАТИ ===
        res_time = ft.Text("--", size=22, weight="bold")
        res_dist = ft.Text("--", size=22, weight="bold", color="red")
        res_angle = ft.Text("--", size=20, color="blue")

        def calculate(e):
            try:
                m = float(lbl_m.value.replace(",", "."))
                cx = float(lbl_cx.value.replace(",", "."))
                s = float(lbl_s.value.replace(",", "."))
                h = float(ent_h.value.replace(",", "."))
                v = float(ent_v.value.replace(",", "."))
                w = float(ent_w.value.replace(",", "."))
                t = float(ent_temp.value.replace(",", "."))
                p = float(ent_press.value.replace(",", "."))
                
                rho = (p * 100) / (287.05 * (t + 273.15))
                lbl_rho.value = f"ρ: {round(rho, 5)}"
                g, k = 9.81, 0.5 * rho * cx * s
                
                if k < 0.000001:
                    t_fall = math.sqrt(2 * h / g)
                    dist_l = (v + w) * t_fall
                else:
                    t_fall = math.sqrt(m/(k*g)) * math.acosh(math.exp(k*h/m))
                    dist_l = (m/k) * math.log(1 + (k*(v+w)*t_fall)/m)
                
                res_time.value = f"{round(t_fall, 3)} с"
                res_dist.value = f"{round(dist_l, 2)} м"
                res_angle.value = f"{round(math.degrees(math.atan(h/dist_l)), 2)}°"
            except: 
                lbl_status.value = "Помилка даних!"
                lbl_status.color = "red"
            page.update()

        # === КОМПОНУВАННЯ ===
        page.add(
            ft.Column([
                # Секція Вхідних Даних (кольори замінені на HEX-коди або текстові назви)
                ft.Text("ВХІДНІ ДАНІ", weight="bold", size=18, color="#90CAF9"),
                ft.Row([ent_h, ent_v, ent_w]),
                
                ft.Divider(height=15, color="transparent"),
                
                # Секція Арсеналу
                ft.Text("АРСЕНАЛ", weight="bold", size=16, color="#90CAF9"),
                ft.Row([ammo_dropdown, ft.ElevatedButton("+ БК", on_click=lambda _: setattr(add_bk_dialog, "open", True) or page.update())]),
                ft.Row([lbl_m, lbl_cx, lbl_s]),
                
                ft.Divider(height=15, color="transparent"),
                
                # Секція Метео
                ft.Text("МЕТЕО", weight="bold", size=16, color="#90CAF9"),
                ft.Row([city_dropdown, ent_custom_city]), 
                ft.ElevatedButton("ОНОВИТИ ПОГОДУ", on_click=get_weather, width=400),
                ft.Row([ent_temp, ent_press]),
                ft.Row([lbl_rho, lbl_status]),
                
                ft.Divider(height=15, color="transparent"),
                
                # Кнопка Розрахувати (колір змінено на текстовий)
                ft.ElevatedButton("РОЗРАХУВАТИ", on_click=calculate, bgcolor="green", color="white", height=50, width=400),
                
                ft.Divider(height=10, color="transparent"),

                # Таблиця результатів
                ft.Container(
                    padding=10, border=ft.border.all(1, "grey"), border_radius=10,
                    content=ft.Column([
                        ft.Row([
                            ft.Column([ft.Text("ЧАС ПАДІННЯ", size=10), res_time], expand=True, horizontal_alignment="center"),
                            ft.Column([ft.Text("ВІДСТАНЬ", size=10), res_dist], expand=True, horizontal_alignment="center"),
                        ]),
                        ft.Divider(),
                        ft.Row([ft.Text("📷 КУТ КАМЕРИ:", size=12), res_angle], alignment="center")
                    ])
                )
            ], spacing=5)
        )
    except Exception as fatal_e:
        show_critical_error(fatal_e)

ft.app(target=main)
