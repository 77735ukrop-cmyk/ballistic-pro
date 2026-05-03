import flet as ft
import math
import requests

# База даних БК
arsenal = {
    "ОГБ-1": {"m": 3.1, "cx": 0.32, "s": 0.0038},
    "MOA-120": {"m": 1.59, "cx": 0.25, "s": 0.00212},
    "MOA-400": {"m": 4.61, "cx": 0.28, "s": 0.00528},
    "MOA-900": {"m": 10.44, "cx": 0.3, "s": 0.01038},
    "БЦ-2500": {"m": 3.0, "cx": 0.42, "s": 0.00636},
    "БЦ-3500": {"m": 4.0, "cx": 0.45, "s": 0.00709},
    "БЦ-4500": {"m": 5.6, "cx": 0.48, "s": 0.00709}
}

cities = ["Kramatorsk,UA", "Toretsk,UA", "Kostiantynivka,UA", "Donetsk,UA"]

def main(page: ft.Page):
    page.title = "BALLISTIC PRO"
    page.scroll = ft.ScrollMode.ADAPTIVE # Це важливо: дозволяє гортати, якщо не влізе
    page.padding = 20 # Відступи по краях екрана
    
    # Створюємо вертикальний список елементів
    layout = ft.Column(
        controls=[
            ft.Text("BALLISTIC PRO v2.0", size=24, weight="bold"),
            
            # Поля вводу йдуть одне за одним
            ft.TextField(label="Висота (м)", keyboard_type=ft.KeyboardType.NUMBER),
            ft.TextField(label="V БПЛА (м/с)", keyboard_type=ft.KeyboardType.NUMBER),
            
            # Випадаючий список
            ft.Dropdown(
                label="Оберіть Арсенал (БК)",
                options=[
                    ft.dropdown.Option("MOA-400"),
                    ft.dropdown.Option("Інший варіант"),
                ],
            ),
            
            # Поля Маси та Cx можна зробити в ряд, якщо вони короткі
            ft.Row([
                ft.TextField(label="Маса (кг)", expand=True),
                ft.TextField(label="Cx", expand=True),
            ]),
            
            ft.TextField(label="Локація"),
            
            # Кнопка
            ft.ElevatedButton(text="РОЗРАХУВАТИ", on_click=lambda _: print("Рахуємо...")),
            
            # Результати
            ft.Text("ДИСТАНЦІЯ СКИДУ:", weight="bold"),
            ft.Text("489.68 м", color="red", size=30),
        ],
        spacing=15, # Відстань між елементами (по 15 пікселів)
    )

    page.add(layout)

    # Поля введення
    ent_h = ft.TextField(label="Висота (м)", value="1000")
    ent_v = ft.TextField(label="V БПЛА (м/с)", value="5")
    ent_w = ft.TextField(label="V вітру (м/с)", value="0")
    
    # Поля характеристик (тепер вони будуть заповнюватися при розрахунку)
    ent_m = ft.TextField(label="Маса (кг)", value="0", read_only=False)
    ent_cx = ft.TextField(label="Cx", value="0", read_only=False)
    ent_s = ft.TextField(label="S (площа)", value="0", read_only=False)
    
    ent_temp = ft.TextField(label="Температура (°C)", value="15")
    ent_press = ft.TextField(label="Тиск (гПа)", value="1013")

    res_l = ft.Text("0.0 м", size=35, weight="bold", color="red")
    res_angle = ft.Text("0.0°", size=25, color="blue")
    lbl_status = ft.Text("", color="yellow")

    # --- Функція погоди ---
    def get_weather(e):
        city = city_dropdown.value
        api_key = "26419f7c6a93b4f4e515dcfcda96586b"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        try:
            r = requests.get(url, timeout=5).json()
            if r.get("cod") == 200:
                ent_temp.value = str(r['main']['temp'])
                ent_press.value = str(r['main']['pressure'])
                lbl_status.value = f"Погода оновлена для {city}"
            else:
                lbl_status.value = "Помилка отримання погоди"
        except:
            lbl_status.value = "Немає зв'язку з метео-сервером"
        page.update()

    # --- Функція розрахунку (тут тепер і вибір БК) ---
    def calculate(e):
        try:
            # 1. Беремо дані з обраного БК прямо зараз
            selected_bk = ammo_dropdown.value
            if selected_bk in arsenal:
                data = arsenal[selected_bk]
                ent_m.value = str(data['m'])
                ent_cx.value = str(data['cx'])
                ent_s.value = str(data['s'])
            
            # 2. Читаємо значення з полів
            m = float(ent_m.value)
            cx = float(ent_cx.value)
            s = float(ent_s.value)
            h = float(ent_h.value)
            v = float(ent_v.value)
            w = float(ent_w.value)
            t = float(ent_temp.value)
            p = float(ent_press.value)

            if m <= 0 or cx <= 0 or s <= 0:
                lbl_status.value = "Помилка: Оберіть БК зі списку!"
                page.update()
                return

            # 3. Фізика
            rho = (p * 100) / (287.05 * (t + 273.15))
            g = 9.81
            
            # Математика
            t_fall = math.sqrt(2*m/(rho*cx*s*g)) * math.acosh(math.exp(rho*cx*s*h/(2*m)))
            dist_l = (2*m/(rho*cx*s)) * math.log(1 + (rho*cx*s*(v+w)*t_fall)/(2*m))
            angle_deg = math.degrees(math.atan(h / dist_l)) if dist_l > 0 else 90
            
            res_l.value = f"{round(dist_l, 2)} м"
            res_angle.value = f"{round(angle_deg, 2)}°"
            lbl_status.value = f"Розраховано для {selected_bk}"
            page.update()
            
        except Exception as ex:
            lbl_status.value = f"Помилка: {ex}"
            page.update()

    # Створюємо випадаючі списки БЕЗ on_change (щоб не було помилок)
    ammo_dropdown = ft.Dropdown(
        label="Оберіть Арсенал (БК)",
        options=[ft.dropdown.Option(k) for k in arsenal.keys()],
        value="ОГБ-1"
    )
    
    city_dropdown = ft.Dropdown(
        label="Локація",
        options=[ft.dropdown.Option(c) for c in cities],
        value=cities[0]
    )

    page.add(
        ft.Text("BALLISTIC PRO v2.0", size=30, weight="bold"),
        ft.Row([ent_h, ent_v, ent_w]),
        ft.Divider(),
        ammo_dropdown,
        ft.Row([ent_m, ent_cx, ent_s]),
        ft.Divider(),
        ft.Row([city_dropdown, ft.ElevatedButton("ОНОВИТИ ПОГОДУ", on_click=get_weather)]),
        ft.Row([ent_temp, ent_press]),
        ft.Divider(),
        ft.ElevatedButton(
            "РОЗРАХУВАТИ", 
            on_click=calculate, 
            bgcolor="green", 
            color="white", 
            height=60, 
            width=400
        ),
        ft.Text("ДИСТАНЦІЯ СКИДУ:"),
        res_l,
        ft.Text("КУТ НАХИЛУ:"),
        res_angle,
        lbl_status
    )

ft.app(target=main)
