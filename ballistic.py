import flet as ft
import math
import requests

def main(page: ft.Page):
    page.title = "BALLISTIC PRO"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.padding = 15

    # --- ЛОГІКА ЗБЕРЕЖЕННЯ (ЗАМІСТЬ JSON) ---
    DEFAULT_ARSENAL = {
        "ОГБ-1": {"m": 3.1, "cx": 0.32, "s": 0.0038},
        "MOA-400": {"m": 4.61, "cx": 0.28, "s": 0.00528}
    }

    # Отримуємо дані з пам'яті телефону
    arsenal = page.client_storage.get("arsenal_db")
    if not arsenal:
        arsenal = DEFAULT_ARSENAL
        page.client_storage.set("arsenal_db", arsenal)

    # --- ЕЛЕМЕНТИ ВВОДУ ---
    ent_h = ft.TextField(label="ВИСОТА (м)", value="1000", expand=1, keyboard_type="number")
    ent_v = ft.TextField(label="БПЛА (м/с)", value="5", expand=1, keyboard_type="number")
    ent_w = ft.TextField(label="ВІТЕР (м/с)", value="0", expand=1, keyboard_type="number")

    ent_m = ft.TextField(label="Маса (кг)", value="0", expand=1)
    ent_cx = ft.TextField(label="Cx", value="0", expand=1)
    ent_s = ft.TextField(label="S (площа)", value="0", expand=1)

    # Поля для додавання нового БК
    new_name = ft.TextField(label="Назва БК")
    new_m = ft.TextField(label="Маса", keyboard_type="number")
    new_cx = ft.TextField(label="Cx", keyboard_type="number")
    new_s = ft.TextField(label="S", keyboard_type="number")

    # Результати
    res_l = ft.Text("0.0 м", size=30, weight="bold", color="red")
    res_angle = ft.Text("0.0°", size=25, color="blue")
    res_time = ft.Text("0.0 с", size=25, color="green")
    lbl_status = ft.Text("", color="yellow")

    # --- ФУНКЦІЇ ---
    def on_ammo_change(e):
        if ammo_dropdown.value in arsenal:
            data = arsenal[ammo_dropdown.value]
            ent_m.value = str(data['m'])
            ent_cx.value = str(data['cx'])
            ent_s.value = str(data['s'])
            page.update()

    def save_bk(e):
        if new_name.value:
            try:
                arsenal[new_name.value] = {
                    "m": float(new_m.value),
                    "cx": float(new_cx.value),
                    "s": float(new_s.value)
                }
                page.client_storage.set("arsenal_db", arsenal)
                ammo_dropdown.options = [ft.dropdown.Option(k) for k in arsenal.keys()]
                ammo_dropdown.value = new_name.value
                on_ammo_change(None)
                exp_tile.expanded = False
                lbl_status.value = f"Збережено: {new_name.value}"
            except:
                lbl_status.value = "Помилка вводу даних!"
            page.update()

    def get_weather(e):
        city = city_dropdown.value
        api_key = "26419f7c6a93b4f4e515dcfcda96586b"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        try:
            r = requests.get(url, timeout=5).json()
            if r.get("cod") == 200:
                ent_temp.value = str(r['main']['temp'])
                ent_press.value = str(r['main']['pressure'])
                lbl_status.value = "Погода оновлена"
            else:
                lbl_status.value = "Помилка API"
        except:
            lbl_status.value = "Немає інтернету"
        page.update()

    def calculate(e):
        try:
            m, cx, s = float(ent_m.value), float(ent_cx.value), float(ent_s.value)
            h, v, w = float(ent_h.value), float(ent_v.value), float(ent_w.value)
            t, p = float(ent_temp.value), float(ent_press.value)

            # Розрахунок густини повітря
            rho = (p * 100) / (287.05 * (t + 273.15))
            g = 9.81
            
            # Формули з урахуванням опору
            t_fall = math.sqrt(2*m/(rho*cx*s*g)) * math.acosh(math.exp(rho*cx*s*h/(2*m)))
            dist_l = (2*m/(rho*cx*s)) * math.log(1 + (rho*cx*s*(v+w)*t_fall)/(2*m))
            angle = math.degrees(math.atan(h / dist_l)) if dist_l > 0 else 90
            
            res_l.value = f"{round(dist_l, 2)} м"
            res_angle.value = f"{round(angle, 2)}°"
            res_time.value = f"{round(t_fall, 2)} с"
            lbl_status.value = "Розраховано успішно"
        except Exception as ex:
            lbl_status.value = "Помилка в розрахунках"
        page.update()

    # --- ЕЛЕМЕНТИ UI ---
    ammo_dropdown = ft.Dropdown(
        label="Оберіть БК",
        options=[ft.dropdown.Option(k) for k in arsenal.keys()],
        value=list(arsenal.keys())[0],
        on_change=on_ammo_change,
        expand=True
    )

    city_dropdown = ft.Dropdown(
        label="Локація",
        options=[ft.dropdown.Option(c) for c in ["Horlivka,UA", "Donetsk,UA", "Kramatorsk,UA"]],
        value="Horlivka,UA",
        expand=True
    )

    ent_temp = ft.TextField(label="T (°C)", value="15", expand=1)
    ent_press = ft.TextField(label="P (гПа)", value="1013", expand=1)

    exp_tile = ft.ExpansionTile(
        title=ft.Text("Керування Арсеналом (Додати/Змінити)"),
        controls=[
            ft.Column([new_name, new_m, new_cx, new_s, 
            ft.ElevatedButton("ЗБЕРЕГТИ БК", on_click=save_bk, width=400)], spacing=10)
        ]
    )

    # Побудова екрану
    page.add(
        ft.Text("BALLISTIC PRO v2.5", size=22, weight="bold"),
        ft.Row([ent_h, ent_v, ent_w]),
        ft.Divider(),
        ft.Row([ammo_dropdown, ft.IconButton(ft.icons.SETTINGS, on_click=lambda _: setattr(exp_tile, "expanded", not exp_tile.expanded))]),
        ft.Row([ent_m, ent_cx, ent_s]),
        exp_tile,
        ft.Divider(),
        ft.Row([city_dropdown]),
        ft.ElevatedButton("ОНОВИТИ ПОГОДУ", on_click=get_weather, icon=ft.icons.CLOUD_SYNC, width=400),
        ft.Row([ent_temp, ent_press]),
        ft.Divider(),
        ft.ElevatedButton("РОЗРАХУВАТИ", on_click=calculate, bgcolor="green", color="white", height=60, width=400),
        ft.Column([
            ft.Row([ft.Text("ДИСТАНЦІЯ:"), res_l], alignment="spaceBetween"),
            ft.Row([ft.Text("КУТ:"), res_angle], alignment="spaceBetween"),
            ft.Row([ft.Text("ЧАС ПАДІННЯ:"), res_time], alignment="spaceBetween"),
        ]),
        lbl_status
    )
    
    # Стартова ініціалізація полів
    on_ammo_change(None)

ft.app(target=main)
