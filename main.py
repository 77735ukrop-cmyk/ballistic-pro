import flet as ft
import math
import os
import json

# --- НАДІЙНА ПАМ'ЯТЬ ДЛЯ ANDROID ---
APP_DIR = os.path.dirname(__file__)
ARSENAL_FILE = os.path.join(APP_DIR, "arsenal.json")
CITIES_FILE = os.path.join(APP_DIR, "cities.json")

# Стандартні бази
BASE_ARSENAL = {
    "ОГБ-1": {"m": 3.1, "cx": 0.32, "s": 0.0038},
    "MOA-120": {"m": 1.59, "cx": 0.25, "s": 0.00212},
    "MOA-400": {"m": 4.61, "cx": 0.28, "s": 0.00528},
    "MOA-900": {"m": 10.44, "cx": 0.3, "s": 0.01038},
    "БЦ-2500": {"m": 3.0, "cx": 0.42, "s": 0.00636},
    "БЦ-3500": {"m": 4.0, "cx": 0.45, "s": 0.00709},
    "БЦ-4500": {"m": 5.6, "cx": 0.48, "s": 0.00709}
}

BASE_CITIES = ["Kramatorsk,UA", "Kostiantynivka,UA", "Toretsk,UA", "Horlivka,UA", "Donetsk,UA"]

def load_data(file_path, default_data):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return default_data.copy()

def save_data(file_path, data):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except: pass

arsenal = load_data(ARSENAL_FILE, BASE_ARSENAL)
cities_list = load_data(CITIES_FILE, BASE_CITIES)

def main(page: ft.Page):
    page.title = "BALLISTIC PRO v3.8"
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
        ent_v = ft.TextField(label="БПЛА(м/с)", value="28", expand=True, keyboard_type=ft.KeyboardType.NUMBER)
        ent_w = ft.TextField(label="Вітер(м/с)", value="-10", expand=True, keyboard_type=ft.KeyboardType.NUMBER)

        # === БЛОК: АРСЕНАЛ ===
        lbl_m = ft.TextField(label="m (кг)", value="3.1", read_only=True, expand=True, text_size=12)
        lbl_cx = ft.TextField(label="Cx", value="0.32", read_only=True, expand=True, text_size=12)
        lbl_s = ft.TextField(label="S (м²)", value="0.0038", read_only=True, expand=True, text_size=12)

        def on_ammo_change(e):
            safe_val = ammo_dropdown.value if ammo_dropdown.value in arsenal else list(arsenal.keys())[0]
            data = arsenal[safe_val]
            lbl_m.value = str(data['m'])
            lbl_cx.value = str(data['cx'])
            lbl_s.value = str(data['s'])
            page.update()

        ammo_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option(k) for k in arsenal.keys()],
            value=list(arsenal.keys())[0],
            expand=True
        )
        
        if hasattr(ammo_dropdown, 'on_change'): ammo_dropdown.on_change = on_ammo_change
        elif hasattr(ammo_dropdown, 'on_select'): ammo_dropdown.on_select = on_ammo_change

        # --- ДІАЛОГ АРСЕНАЛУ ---
        current_editing_bk = [None]
        dlg_name = ft.TextField(label="Назва")
        dlg_m = ft.TextField(label="Маса", keyboard_type=ft.KeyboardType.NUMBER)
        dlg_cx = ft.TextField(label="Cx", keyboard_type=ft.KeyboardType.NUMBER)
        dlg_s = ft.TextField(label="S", keyboard_type=ft.KeyboardType.NUMBER)

        def open_new_bk(e):
            current_editing_bk[0] = None
            dlg_name.value = ""
            dlg_m.value = ""
            dlg_cx.value = ""
            dlg_s.value = ""
            add_bk_dialog.title.value = "Додати новий БК"
            add_bk_dialog.open = True
            page.update()

        def open_edit_bk(e):
            curr = ammo_dropdown.value
            if curr in arsenal:
                current_editing_bk[0] = curr
                dlg_name.value = curr
                dlg_m.value = str(arsenal[curr]['m'])
                dlg_cx.value = str(arsenal[curr]['cx'])
                dlg_s.value = str(arsenal[curr]['s'])
                add_bk_dialog.title.value = "Редагувати БК"
                add_bk_dialog.open = True
                page.update()

        def save_bk(e):
            new_name = dlg_name.value.strip()
            if new_name:
                old_name = current_editing_bk[0]
                if old_name and old_name != new_name and old_name in arsenal:
                    del arsenal[old_name]
                
                arsenal[new_name] = {
                    "m": float(dlg_m.value.replace(",", ".")), 
                    "cx": float(dlg_cx.value.replace(",", ".")), 
                    "s": float(dlg_s.value.replace(",", "."))
                }
                save_data(ARSENAL_FILE, arsenal)
                
                ammo_dropdown.options = [ft.dropdown.Option(k) for k in arsenal.keys()]
                ammo_dropdown.value = new_name
                on_ammo_change(None)
                add_bk_dialog.open = False
                page.update()

        def delete_bk(e):
            name = dlg_name.value.strip()
            if name in arsenal and len(arsenal) > 1:
                del arsenal[name]
                save_data(ARSENAL_FILE, arsenal)
                
                ammo_dropdown.options = [ft.dropdown.Option(k) for k in arsenal.keys()]
                ammo_dropdown.value = ammo_dropdown.options[0].key
                on_ammo_change(None)
            add_bk_dialog.open = False
            page.update()

        add_bk_dialog = ft.AlertDialog(
            title=ft.Text(""),
            content=ft.Column([dlg_name, dlg_m, dlg_cx, dlg_s], tight=True),
            actions=[
                ft.TextButton("❌ Видалити", on_click=delete_bk),
                ft.TextButton("✅ Зберегти", on_click=save_bk)
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
        page.overlay.append(add_bk_dialog)

        # === БЛОК: МЕТЕО ===
        city_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option(c) for c in cities_list],
            value=cities_list[0] if cities_list else "",
            expand=True
        )
        ent_temp = ft.TextField(label="t (°C)", value="22.59", expand=True, keyboard_type=ft.KeyboardType.NUMBER)
        ent_press = ft.TextField(label="P (гПа)", value="1017", expand=True, keyboard_type=ft.KeyboardType.NUMBER)
        lbl_rho = ft.Text("ρ: 1.19799", color="#90CAF9", weight="bold")
        lbl_status = ft.Text("", size=11)

        # --- ДІАЛОГ МІСТ ---
        current_editing_city = [None]
        dlg_city_name = ft.TextField(label="Місто (напр. Dnipro,UA)")

        def open_new_city(e):
            current_editing_city[0] = None
            dlg_city_name.value = ""
            city_dialog.title.value = "Додати місто"
            city_dialog.open = True
            page.update()

        def open_edit_city(e):
            curr = city_dropdown.value
            current_editing_city[0] = curr
            dlg_city_name.value = curr
            city_dialog.title.value = "Редагувати місто"
            city_dialog.open = True
            page.update()

        def save_city(e):
            new_city = dlg_city_name.value.strip()
            if new_city:
                old_city = current_editing_city[0]
                if old_city and old_city != new_city and old_city in cities_list:
                    cities_list.remove(old_city)
                
                if new_city not in cities_list:
                    cities_list.append(new_city)
                
                save_data(CITIES_FILE, cities_list)
                city_dropdown.options = [ft.dropdown.Option(c) for c in cities_list]
                city_dropdown.value = new_city
                city_dialog.open = False
                page.update()

        def delete_city(e):
            city = dlg_city_name.value.strip()
            if city in cities_list and len(cities_list) > 1:
                cities_list.remove(city)
                save_data(CITIES_FILE, cities_list)
                city_dropdown.options = [ft.dropdown.Option(c) for c in cities_list]
                city_dropdown.value = cities_list[0]
            city_dialog.open = False
            page.update()

        city_dialog = ft.AlertDialog(
            title=ft.Text(""),
            content=ft.Column([dlg_city_name], tight=True),
            actions=[
                ft.TextButton("❌ Видалити", on_click=delete_city),
                ft.TextButton("✅ Зберегти", on_click=save_city)
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
        page.overlay.append(city_dialog)

        def get_weather(e):
            try:
                import requests 
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
                v_drone = float(ent_v.value.replace(",", "."))
                w_wind = float(ent_w.value.replace(",", "."))
                t = float(ent_temp.value.replace(",", "."))
                p = float(ent_press.value.replace(",", "."))
                
                # Густина повітря
                rho = (p * 100) / (287.05 * (t + 273.15))
                lbl_rho.value = f"ρ: {round(rho, 5)}"
                g = 9.81
                k = 0.5 * rho * cx * s
                
                # --- ТОЧНА СИМУЛЯЦІЯ (ЧИСЕЛЬНЕ ІНТЕГРУВАННЯ) ---
                dt = 0.01  # Крок симуляції 10 мілісекунд
                x = 0.0    # Горизонтальна відстань
                y = 0.0    # Вертикальна відстань (падіння)
                vx = v_drone # Початкова горизонтальна швидкість (відносно землі)
                vy = 0.0     # Початкова вертикальна швидкість
                t_fall = 0.0
                
                # Симулюємо політ, поки БК не досягне землі
                while y < h:
                    # Швидкість вітру відносно БК
                    # w_wind: + попутний, - зустрічний
                    v_air_x = vx - w_wind
                    v_air_y = vy
                    
                    # Загальна повітряна швидкість БК
                    V_total = math.sqrt(v_air_x**2 + v_air_y**2)
                    
                    # Прискорення (опір + гравітація)
                    ax = -(k / m) * V_total * v_air_x
                    ay = g - (k / m) * V_total * v_air_y
                    
                    # Крок у майбутнє
                    vx += ax * dt
                    vy += ay * dt
                    x += vx * dt
                    y += vy * dt
                    t_fall += dt
                    
                    # Запобіжник
                    if t_fall > 120:
                        break
                
                dist_l = x
                angle_deg = math.degrees(math.atan(h / dist_l)) if dist_l > 0 else 90
                
                res_time.value = f"{round(t_fall, 3)} с"
                res_dist.value = f"{round(dist_l, 2)} м"
                res_angle.value = f"{round(angle_deg, 2)}°"
                lbl_status.value = ""
            except Exception as ex: 
                lbl_status.value = "Помилка даних!"
                lbl_status.color = "red"
            page.update()

        # === КОМПОНУВАННЯ ===
        page.add(
            ft.Column([
                ft.Text("ВХІДНІ ДАНІ", weight="bold", size=18, color="#90CAF9"),
                ft.Row([ent_h, ent_v, ent_w]),
                
                ft.Divider(height=15, color="transparent"),
                
                ft.Text("АРСЕНАЛ", weight="bold", size=16, color="#90CAF9"),
                ft.Row([
                    ammo_dropdown, 
                    ft.ElevatedButton("➕", on_click=open_new_bk, width=50),
                    ft.ElevatedButton("⚙️", on_click=open_edit_bk, width=50)
                ]),
                ft.Row([lbl_m, lbl_cx, lbl_s]),
                
                ft.Divider(height=15, color="transparent"),
                
                ft.Text("МЕТЕО", weight="bold", size=16, color="#90CAF9"),
                ft.Row([
                    city_dropdown, 
                    ft.ElevatedButton("➕", on_click=open_new_city, width=50),
                    ft.ElevatedButton("⚙️", on_click=open_edit_city, width=50)
                ]),
                ft.ElevatedButton("ОНОВИТИ ПОГОДУ", on_click=get_weather, width=400),
                ft.Row([ent_temp, ent_press]),
                ft.Row([lbl_rho, lbl_status]),
                
                ft.Divider(height=15, color="transparent"),
                
                ft.ElevatedButton("РОЗРАХУВАТИ", on_click=calculate, bgcolor="green", color="white", height=50, width=400),
                
                ft.Divider(height=10, color="transparent"),

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
        
        on_ammo_change(None)
        
    except Exception as fatal_e:
        show_critical_error(fatal_e)

ft.app(target=main)
