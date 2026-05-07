import flet as ft
import math
import os
import json

# --- ПАМ'ЯТЬ ---
APP_DIR = os.path.dirname(__file__)
ARSENAL_FILE = os.path.join(APP_DIR, "arsenal.json")
CITIES_FILE = os.path.join(APP_DIR, "cities.json")

# СТАНДАРТНІ БАЗИ
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
        except: 
            pass
    return default_data.copy()

def save_data(file_path, data):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except: 
        pass

arsenal = load_data(ARSENAL_FILE, BASE_ARSENAL)
cities_list = load_data(CITIES_FILE, BASE_CITIES)

def main(page: ft.Page):
    page.title = "BALLISTIC PRO v4.1"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.padding = ft.padding.only(top=50, left=15, right=15, bottom=20)

    try:
        # === ВЕРХНІЙ БЛОК: ВХІДНІ ДАНІ ===
        ent_h = ft.TextField(label="Висота(м)", value="1500", expand=True, keyboard_type=ft.KeyboardType.NUMBER)
        ent_v = ft.TextField(label="БПЛА(м/с)", value="28", expand=True, keyboard_type=ft.KeyboardType.NUMBER)
        ent_w_drone = ft.TextField(label="Вітер Висота", value="-10", expand=True, keyboard_type=ft.KeyboardType.NUMBER)

        # === БЛОК: АРСЕНАЛ ===
        lbl_m = ft.TextField(label="m (кг)", value="", read_only=True, expand=True, text_size=12)
        lbl_cx = ft.TextField(label="Cx", value="", read_only=True, expand=True, text_size=12)
        lbl_s = ft.TextField(label="S (м²)", value="", read_only=True, expand=True, text_size=12)

        ammo_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option(k) for k in arsenal.keys()],
            value=list(arsenal.keys())[0], expand=True
        )

        def on_ammo_change(e):
            safe_val = ammo_dropdown.value if ammo_dropdown.value in arsenal else list(arsenal.keys())[0]
            d = arsenal[safe_val]
            lbl_m.value = str(d['m'])
            lbl_cx.value = str(d['cx'])
            lbl_s.value = str(d['s'])
            page.update()

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
            add_bk_dialog.title.value = "Новий БК"
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
        city_dropdown = ft.Dropdown(options=[ft.dropdown.Option(c) for c in cities_list], value=cities_list[0] if cities_list else "", expand=True)
        ent_temp = ft.TextField(label="t (°C)", value="20", expand=True, keyboard_type=ft.KeyboardType.NUMBER)
        ent_press = ft.TextField(label="P (гПа)", value="1013", expand=True, keyboard_type=ft.KeyboardType.NUMBER)
        ent_w_ground = ft.TextField(label="Вітер Земля", value="-2", expand=True, keyboard_type=ft.KeyboardType.NUMBER)
        lbl_rho = ft.Text("ρ: ---", color="#90CAF9", weight="bold")
        lbl_status = ft.Text("", size=11)

        # --- ДІАЛОГ МІСТ ---
        current_editing_city = [None]
        dlg_city_name = ft.TextField(label="Місто (напр. Dnipro,UA)")

        def open_new_city(e):
            current_editing_city[0] = None
            dlg_city_name.value = ""
            city_dialog.title.value = "Нове місто"
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
                url = f"https://api.openweathermap.org/data/2.5/weather?q={city_dropdown.value}&appid=26419f7c6a93b4f4e515dcfcda96586b&units=metric"
                r = requests.get(url, timeout=5).json()
                if r.get("cod") == 200:
                    ent_temp.value = str(r['main']['temp'])
                    ent_press.value = str(r['main']['pressure'])
                    
                    # ВИПРАВЛЕНО: Автоматична підстановка мінуса для зустрічного вітру
                    wind_speed = float(r['wind']['speed'])
                    ent_w_ground.value = f"-{wind_speed}" if wind_speed != 0 else "0"
                    
                    lbl_status.value = f"OK: {r['name']}"
                    lbl_status.color = "green"
                else:
                    lbl_status.value = "Помилка API"
                    lbl_status.color = "red"
            except:
                lbl_status.value = "Немає мережі"
                lbl_status.color = "red"
            page.update()

        # === РЕЗУЛЬТАТИ ===
        res_time = ft.Text("--", size=24, weight="bold")
        res_dist = ft.Text("--", size=24, weight="bold", color="red")
        res_angle = ft.Text("--", size=20, color="blue")

        def calculate(e):
            try:
                m = float(lbl_m.value.replace(",", "."))
                cx = float(lbl_cx.value.replace(",", "."))
                s = float(lbl_s.value.replace(",", "."))
                h = float(ent_h.value.replace(",", "."))
                v_drone = float(ent_v.value.replace(",", "."))
                w_high = float(ent_w_drone.value.replace(",", "."))
                w_low = float(ent_w_ground.value.replace(",", "."))
                temp = float(ent_temp.value.replace(",", "."))
                press = float(ent_press.value.replace(",", "."))

                rho = (press * 100) / (287.05 * (temp + 273.15))
                lbl_rho.value = f"ρ: {round(rho, 5)}"
                g = 9.81
                k = 0.5 * rho * cx * s

                dt = 0.01
                x, y, vx, vy
