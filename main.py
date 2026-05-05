import flet as ft
import math

# --- ПОВНА БАЗА ДАНИХ АРСЕНАЛУ З EXCEL ---
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
    page.title = "BALLISTIC PRO v3.0"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.padding = 15
    
    # === ВЕРХНІЙ БЛОК: ВХІДНІ ДАНІ ===
    ent_h = ft.TextField(label="Висота(м)", value="1500", keyboard_type=ft.KeyboardType.NUMBER)
    ent_v = ft.TextField(label="БПЛА(м/с)", value="25", keyboard_type=ft.KeyboardType.NUMBER)
    ent_w = ft.TextField(label="Вітер(м/с)", value="-10", keyboard_type=ft.KeyboardType.NUMBER, tooltip="- зустрічний, + попутний")

    # === БЛОК: АРСЕНАЛ ===
    lbl_m = ft.TextField(label="m (кг)", value="4.61", read_only=True, text_size=13)
    lbl_cx = ft.TextField(label="Cx", value="0.28", read_only=True, text_size=13)
    lbl_s = ft.TextField(label="S (м²)", value="0.00528", read_only=True, text_size=13)

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
    # Безпечне підключення події
    if hasattr(ammo_dropdown, 'on_change'): ammo_dropdown.on_change = on_ammo_change
    elif hasattr(ammo_dropdown, 'on_select'): ammo_dropdown.on_select = on_ammo_change

    # --- ДІАЛОГ ДОДАВАННЯ НОВОГО БК (Шестерня) ---
    dlg_name = ft.TextField(label="Назва БК (напр. САМ-1)")
    dlg_m = ft.TextField(label="Маса (кг)", keyboard_type=ft.KeyboardType.NUMBER)
    dlg_cx = ft.TextField(label="Cx (опір)", keyboard_type=ft.KeyboardType.NUMBER)
    dlg_s = ft.TextField(label="S (площа)", keyboard_type=ft.KeyboardType.NUMBER)

    def close_dlg(e):
        add_bk_dialog.open = False
        page.update()

    def save_bk(e):
        name = dlg_name.value
        if name:
            try:
                arsenal[name] = {
                    "m": float(dlg_m.value.replace(",", ".")), 
                    "cx": float(dlg_cx.value.replace(",", ".")), 
                    "s": float(dlg_s.value.replace(",", "."))
                }
                ammo_dropdown.options = [ft.dropdown.Option(k) for k in arsenal.keys()]
                ammo_dropdown.value = name
                on_ammo_change(None)
                close_dlg(None)
            except Exception as ex:
                dlg_name.label = "Помилка цифр!"
                page.update()

    add_bk_dialog = ft.AlertDialog(
        title=ft.Text("Додати БК"),
        content=ft.Column([dlg_name, dlg_m, dlg_cx, dlg_s], tight=True),
        actions=[
            ft.TextButton("Скасувати", on_click=close_dlg),
            ft.TextButton("Зберегти", on_click=save_bk)
        ]
    )
    page.overlay.append(add_bk_dialog)

    def open_settings(e):
        add_bk_dialog.open = True
        page.update()

    btn_settings = ft.IconButton(icon=ft.icons.SETTINGS, on_click=open_settings, icon_size=30)

    # === БЛОК: МЕТЕО ===
    city_dropdown = ft.Dropdown(
        options=[ft.dropdown.Option(c) for c in cities],
        value="Horlivka,UA",
        expand=True
    )
    ent_temp = ft.TextField(label="t (°C)", value="6.95", keyboard_type=ft.KeyboardType.NUMBER)
    ent_press = ft.TextField(label="P (гПа)", value="1016", keyboard_type=ft.KeyboardType.NUMBER)
    lbl_rho = ft.Text("ρ: 1.26364", color=ft.colors.CYAN_300, weight="bold")
    lbl_status = ft.Text("", size=12)

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
                lbl_status.value = "Погода оновлена"
                lbl_status.color = "green"
            else:
                lbl_status.value = "Помилка API"
                lbl_status.color = "red"
        except Exception as ex:
            lbl_status.value = f"Помилка мережі"
            lbl_status.color = "red"
        page.update()

    # === БЛОК: РЕЗУЛЬТАТИ ===
    res_time = ft.Text("--", size=24, weight="bold")
    res_dist = ft.Text("--", size=24, weight="bold", color="red")
    res_angle = ft.Text("--", size=20, color="blue")

    def calculate(e):
        try:
            # Заміна ком на крапки на льоту
            m = float(lbl_m.value.replace(",", "."))
            cx = float(lbl_cx.value.replace(",", "."))
            s = float(lbl_s.value.replace(",", "."))
            h = float(ent_h.value.replace(",", "."))
            v = float(ent_v.value.replace(",", "."))
            w = float(ent_w.value.replace(",", "."))
            t = float(ent_temp.value.replace(",", "."))
            p = float(ent_press.value.replace(",", "."))
            
            # 1. Густина повітря
            rho = (p * 100) / (287.05 * (t + 273.15))
            lbl_rho.value = f"ρ: {round(rho, 5)}"
            
            g = 9.81
            k = 0.5 * rho * cx * s
            
            # 2. Балістика (точна фізична формула)
            if k < 0.000001:
                t_fall = math.sqrt(2 * h / g)
                dist_l = (v + w) * t_fall
            else:
                t_fall = math.sqrt(m/(k*g)) * math.acosh(math.exp(k*h/m))
                dist_l = (m/k) * math.log(1 + (k*(v+w)*t_fall)/m)
                
            angle_deg = math.degrees(math.atan(h / dist_l)) if dist_l > 0 else 90
            
            # Вивід результатів
            res_time.value = f"{round(t_fall, 3)} с"
            res_dist.value = f"{round(dist_l, 2)} м"
            res_angle.value = f"{round(angle_deg, 2)}°"
            
            lbl_status.value = ""
        except Exception as ex:
            lbl_status.value = "Помилка: перевірте цифри!"
            lbl_status.color = "red"
        page.update()

    # === КОМПОНУВАННЯ ІНТЕРФЕЙСУ ===
    page.add(
        ft.Column([
            # Шапка
            ft.Row([
                ent_h, ent_v, ent_w
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            ft.Divider(height=2, color=ft.colors.BLUE_GREY_800),
            
            # Арсенал
            ft.Text("АРСЕНАЛ", weight="bold", size=16),
            ft.Row([ammo_dropdown, btn_settings]),
            ft.Row([lbl_m, lbl_cx, lbl_s], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            ft.Divider(height=2, color=ft.colors.BLUE_GREY_800),
            
            # Метео
            ft.Text("МЕТЕО", weight="bold", size=16),
            ft.Row([city_dropdown]),
            ft.ElevatedButton("ОНОВИТИ ПОГОДУ", on_click=get_weather, icon=ft.icons.CLOUD_DOWNLOAD),
            ft.Row([ent_temp, ent_press], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Row([lbl_rho, lbl_status], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            ft.Divider(height=2, color=ft.colors.BLUE_GREY_800),
            
            # Кнопка Розрахувати
            ft.ElevatedButton("РОЗРАХУВАТИ", on_click=calculate, bgcolor=ft.colors.GREEN_700, color="white", height=55, width=400),
            
            # Результати (Таблиця)
            ft.Container(
                padding=10,
                border=ft.border.all(1, ft.colors.BLUE_GREY_500),
                border_radius=10,
                content=ft.Column([
                    ft.Row([
                        ft.Column([ft.Text("ЧАС ПАДІННЯ", size=12), res_time], expand=True, alignment=ft.MainAxisAlignment.CENTER),
                        ft.Column([ft.Text("ВІДСТАНЬ ДО ЦІЛІ", size=12), res_dist], expand=True, alignment=ft.MainAxisAlignment.CENTER),
                    ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
                    ft.Divider(height=1),
                    ft.Row([
                        ft.Icon(ft.icons.CAMERA_ALT_OUTLINED, size=20),
                        ft.Text("КУТ КАМЕРИ:", size=14), 
                        res_angle
                    ], alignment=ft.MainAxisAlignment.CENTER)
                ])
            )
        ], spacing=8)
    )

ft.app(target=main)
