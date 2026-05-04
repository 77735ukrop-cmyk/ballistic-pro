import flet as ft
import math
import requests

def main(page: ft.Page):
    page.title = "BALLISTIC PRO"
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.padding = 15
    page.theme_mode = ft.ThemeMode.DARK # Темна тема

    # --- ІНІЦІАЛІЗАЦІЯ БАЗИ ДАНИХ (БЕЗПЕЧНА ДЛЯ ANDROID) ---
    default_arsenal = {
        "ОГБ-1": {"m": 3.1, "cx": 0.32, "s": 0.0038},
        "MOA-400": {"m": 4.61, "cx": 0.28, "s": 0.00528}
    }
    
    # Читаємо з пам'яті телефону. Якщо порожньо - беремо стандартні
    arsenal = page.client_storage.get("arsenal_db")
    if not arsenal:
        arsenal = default_arsenal

    def save_arsenal_to_storage():
        page.client_storage.set("arsenal_db", arsenal)

    cities = ["Kramatorsk,UA", "Toretsk,UA", "Kostiantynivka,UA", "Donetsk,UA", "Horlivka,UA"]

    # --- ЕЛЕМЕНТИ ІНТЕРФЕЙСУ ---
    
    # Блок 1: Політ
    ent_h = ft.TextField(label="ВИСОТА (м)", value="1000", keyboard_type=ft.KeyboardType.NUMBER, expand=1)
    ent_v = ft.TextField(label="БПЛА (м/с)", value="5", keyboard_type=ft.KeyboardType.NUMBER, expand=1)
    ent_w = ft.TextField(label="ВІТЕР (м/с)", value="0", keyboard_type=ft.KeyboardType.NUMBER, expand=1)

    # Блок 2: Арсенал
    ent_m = ft.TextField(label="Маса (кг)", value="0", expand=1)
    ent_cx = ft.TextField(label="Cx", value="0", expand=1)
    ent_s = ft.TextField(label="S (площа)", value="0", expand=1)

    def on_ammo_change(e):
        data = arsenal[ammo_dropdown.value]
        ent_m.value = str(data['m'])
        ent_cx.value = str(data['cx'])
        ent_s.value = str(data['s'])
        page.update()

    ammo_dropdown = ft.Dropdown(
        options=[ft.dropdown.Option(k) for k in arsenal.keys()],
        value="MOA-400" if "MOA-400" in arsenal else list(arsenal.keys())[0],
        on_change=on_ammo_change,
        expand=1
    )

    # Блок 3: Метео
    city_dropdown = ft.Dropdown(options=[ft.dropdown.Option(c) for c in cities], value="Horlivka,UA", expand=1)
    ent_temp = ft.TextField(label="Температура (°C)", value="15", expand=1)
    ent_press = ft.TextField(label="Тиск (гПа)", value="1013", expand=1)
    lbl_rho = ft.Text("ρ (густина): ---", size=16, color=ft.colors.ORANGE)
    lbl_status = ft.Text("", color="yellow")

    # Блок 4: Результати
    res_angle = ft.Text("0.00°", size=20, weight="bold", color="blue")
    res_time = ft.Text("0.00 с", size=20, weight="bold", color="green")
    res_dist = ft.Text("0.00 м", size=20, weight="bold", color="red")

    # Викликаємо ручне заповнення полів БК при старті
    on_ammo_change(None)

    # --- ДІАЛОГОВЕ ВІКНО КЕРУВАННЯ БК (ШЕСТЕРНЯ) ---
    dlg_name = ft.TextField(label="Назва БК")
    dlg_m = ft.TextField(label="Маса (кг)")
    dlg_cx = ft.TextField(label="Cx")
    dlg_s = ft.TextField(label="S (площа)")

    def save_new_bk(e):
        name = dlg_name.value
        if name:
            arsenal[name] = {
                "m": float(dlg_m.value.replace(',', '.')),
                "cx": float(dlg_cx.value.replace(',', '.')),
                "s": float(dlg_s.value.replace(',', '.'))
            }
            save_arsenal_to_storage() # Зберігаємо в пам'ять телефону
            
            # Оновлюємо список
            ammo_dropdown.options = [ft.dropdown.Option(k) for k in arsenal.keys()]
            ammo_dropdown.value = name
            on_ammo_change(None)
            
            close_dlg(e)
            lbl_status.value = f"БК {name} збережено!"
            page.update()

    def close_dlg(e):
        dialog.open = False
        page.update()

    dialog = ft.AlertDialog(
        title=ft.Text("Додати / Змінити БК"),
        content=ft.Column([dlg_name, dlg_m, dlg_cx, dlg_s], tight=True),
        actions=[
            ft.TextButton("Скасувати", on_click=close_dlg),
            ft.TextButton("ЗБЕРЕГТИ", on_click=save_new_bk),
        ],
    )
    page.overlay.append(dialog)

    def open_settings_dialog(e):
        # Заповнюємо поточними даними
        dlg_name.value = ammo_dropdown.value
        dlg_m.value = ent_m.value
        dlg_cx.value = ent_cx.value
        dlg_s.value = ent_s.value
        dialog.open = True
        page.update()

    # --- ФУНКЦІЇ ЛОГІКИ ---
    def get_weather(e):
        city = city_dropdown.value
        api_key = "26419f7c6a93b4f4e515dcfcda96586b"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        try:
            r = requests.get(url, timeout=5).json()
            if r.get("cod") == 200:
                ent_temp.value = str(r['main']['temp'])
                ent_press.value = str(r['main']['pressure'])
                lbl_status.value = "Погоду оновлено"
                calculate(None) # Автоматично рахуємо нову густину
            else:
                lbl_status.value = "Помилка погоди"
        except:
            lbl_status.value = "Немає зв'язку з інтернетом"
        page.update()

    def calculate(e):
        try:
            m = float(ent_m.value)
            cx = float(ent_cx.value)
            s = float(ent_s.value)
            h = float(ent_h.value)
            v = float(ent_v.value)
            w = float(ent_w.value)
            t = float(ent_temp.value)
            p = float(ent_press.value)

            # Обчислення густини (rho)
            rho = (p * 100) / (287.05 * (t + 273.15))
            lbl_rho.value = f"ρ: {round(rho, 5)}"
            
            g = 9.81
            
            t_fall = math.sqrt(2*m/(rho*cx*s*g)) * math.acosh(math.exp(rho*cx*s*h/(2*m)))
            dist_l = (2*m/(rho*cx*s)) * math.log(1 + (rho*cx*s*(v+w)*t_fall)/(2*m))
            angle_deg = math.degrees(math.atan(h / dist_l)) if dist_l > 0 else 90
            
            res_dist.value = f"{round(dist_l, 2)} м"
            res_angle.value = f"{round(angle_deg, 2)}°"
            res_time.value = f"{round(t_fall, 3)} с"
            
            lbl_status.value = "Успішно розраховано"
            page.update()
        except Exception as ex:
            lbl_status.value = f"Помилка в даних"
            page.update()

    # --- ПОБУДОВА ІНТЕРФЕЙСУ (ЗГІДНО З ЕСКІЗОМ) ---
    page.add(
        ft.Row([ent_h, ent_v, ent_w]),
        ft.Divider(height=10, color="transparent"),
        
        ft.Text("АРСЕНАЛ", size=20, weight="bold"),
        ft.Row([
            ammo_dropdown,
            ft.IconButton(icon=ft.icons.SETTINGS, icon_size=30, on_click=open_settings_dialog)
        ]),
        ft.Row([ent_m, ent_cx, ent_s]),
        ft.Divider(height=10, color="transparent"),
        
        ft.Text("МЕТЕО", size=20, weight="bold"),
        ft.Row([city_dropdown]),
        ft.ElevatedButton("ОНОВИТИ ПОГОДУ", on_click=get_weather, icon=ft.icons.CLOUD_DOWNLOAD, width=200),
        ft.Row([ent_temp, ent_press]),
        lbl_rho,
        ft.Divider(height=10, color="transparent"),
        
        ft.ElevatedButton("РОЗРАХУВАТИ", on_click=calculate, bgcolor=ft.colors.GREEN_700, color="white", height=60, expand=1, width=float('inf')),
        ft.Divider(height=10, color="transparent"),
        
        # Таблиця результатів
        ft.Container(
            border=ft.border.all(1, ft.colors.OUTLINE),
            border_radius=10,
            padding=10,
            content=ft.Row([
                ft.Column([ft.Icon(ft.icons.ARCHITECTURE), res_angle], horizontal_alignment="center", expand=1),
                ft.Column([ft.Text("ЧАС", size=12), res_time], horizontal_alignment="center", expand=1),
                ft.Column([ft.Text("ВІДСТАНЬ", size=12), res_dist], horizontal_alignment="center", expand=1),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        ),
        
        lbl_status
    )

ft.app(target=main)
