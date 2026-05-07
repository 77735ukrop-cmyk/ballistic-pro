import flet as ft
import math, os, json

APP_DIR = os.path.dirname(__file__)
ARS_F, CIT_F = os.path.join(APP_DIR, "ars.json"), os.path.join(APP_DIR, "cit.json")

# ПОВНИЙ СПИСОК БК
BASE_ARS = {
    "ОГБ-1": {"m": 3.1, "cx": 0.32, "s": 0.0038},
    "MOA-120": {"m": 1.59, "cx": 0.25, "s": 0.00212},
    "MOA-400": {"m": 4.61, "cx": 0.28, "s": 0.00528},
    "MOA-900": {"m": 10.44, "cx": 0.3, "s": 0.01038},
    "БЦ-2500": {"m": 3.0, "cx": 0.42, "s": 0.00636},
    "БЦ-3500": {"m": 4.0, "cx": 0.45, "s": 0.00709},
    "БЦ-4500": {"m": 5.6, "cx": 0.48, "s": 0.00709}
}
BASE_CIT = ["Kramatorsk,UA", "Toretsk,UA", "Horlivka,UA"]

def load_d(f, d):
    if os.path.exists(f):
        try:
            with open(f, "r", encoding="utf-8") as file: return json.load(file)
        except: pass
    return d.copy()

def save_d(f, data):
    try:
        with open(f, "w", encoding="utf-8") as file: json.dump(data, file)
    except: pass

ars, cit = load_d(ARS_F, BASE_ARS), load_d(CIT_F, BASE_CIT)

def main(page: ft.Page):
    page.title = "BALLISTIC PRO v4.2"
    page.theme_mode = "dark"
    page.scroll = "adaptive"
    page.padding = ft.padding.only(top=40, left=15, right=15, bottom=20)

    eh = ft.TextField(label="Висота(м)", value="1500", expand=1)
    ev = ft.TextField(label="БПЛА(м/с)", value="28", expand=1)
    ew_h = ft.TextField(label="Вітер Висота", value="-10", expand=1)
    
    lm = ft.TextField(label="m(кг)", read_only=True, expand=1)
    lcx = ft.TextField(label="Cx", read_only=True, expand=1)
    ls = ft.TextField(label="S(м²)", read_only=True, expand=1)

    add_dd = ft.Dropdown(options=[ft.dropdown.Option(k) for k in ars.keys()], value=list(ars.keys())[0], expand=True)
    c_dd = ft.Dropdown(options=[ft.dropdown.Option(c) for c in cit], value=cit[0], expand=True)

    def up_a(e):
        d = ars.get(add_dd.value, list(ars.values())[0])
        lm.value, lcx.value, ls.value = str(d['m']), str(d['cx']), str(d['s'])
        page.update()
    add_dd.on_change = up_a

    d_n, d_m, d_cx, d_s = ft.TextField(label="Назва"), ft.TextField(label="m"), ft.TextField(label="Cx"), ft.TextField(label="S")
    cur_bk = [None]

    def bk_save(e):
        n = d_n.value.strip()
        if n:
            if cur_bk[0] and cur_bk[0] != n: ars.pop(cur_bk[0], None)
            ars[n] = {"m":float(d_m.value), "cx":float(d_cx.value), "s":float(d_s.value)}
            save_d(ARS_F, ars)
            add_dd.options = [ft.dropdown.Option(k) for k in ars.keys()]
            add_dd.value = n
            up_a(None); bk_dlg.open = False; page.update()

    bk_dlg = ft.AlertDialog(content=ft.Column([d_n, d_m, d_cx, d_s], tight=True), actions=[ft.TextButton("Зберегти", on_click=bk_save)])
    page.overlay.append(bk_dlg)

    def open_bk_add(e):
        cur_bk[0]=None; d_n.value=d_m.value=d_cx.value=d_s.value=""; bk_dlg.open=True; page.update()
    def open_bk_ed(e):
        cur_bk[0]=add_dd.value; b=ars[add_dd.value]
        d_n.value, d_m.value, d_cx.value, d_s.value = cur_bk[0], str(b['m']), str(b['cx']), str(b['s'])
        bk_dlg.open=True; page.update()

    et, ep, ew_g = ft.TextField(label="t°C", value="20", expand=1), ft.TextField(label="P", value="1013", expand=1), ft.TextField(label="Вітер Земля", value="-2", expand=1)
    l_rho = ft.Text("ρ: ---", color="blue", weight="bold")

    def get_w(e):
        try:
            import requests
            r = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={c_dd.value}&appid=26419f7c6a93b4f4e515dcfcda96586b&units=metric").json()
            if r.get("cod") == 200:
                et.value, ep.value = str(r['main']['temp']), str(r['main']['pressure'])
                ws = float(r['wind']['speed'])
                ew_g.value = f"-{ws}" if ws != 0 else "0"
            page.update()
        except: pass

    rt, rd, ra = ft.Text("--", size=22, weight="bold"), ft.Text("--", size=22, weight="bold", color="red"), ft.Text("--", color="blue")

    def calc(e):
        try:
            m, cx, s = float(lm.value), float(lcx.value), float(ls.value)
            h, vd, wh, wl = float(eh.value), float(ev.value), float(ew_h.value), float(ew_g.value)
            rho = (float(ep.value)*100)/(287.05*(float(et.value)+273.15))
            l_rho.value = f"ρ: {round(rho,4)}"
            k, dt, x, y, vx, vy, t = 0.5*rho*cx*s, 0.01, 0.0, 0.0, vd, 0.0, 0.0
            while y < h:
                cw = wh + (wl - wh) * (y / h)
                vax, vay = vx - cw, vy
                vt = math.sqrt(vax**2 + vay**2)
                vx += (-(k/m)*vt*vax)*dt
                vy += (9.81-(k/m)*vt*vay)*dt
                x, y, t = x+vx*dt, y+vy*dt, t+dt
                if t > 100: break
            rt.value, rd.value, ra.value = f"{round(t,2)} с", f"{round(x,2)} м", f"{round(math.degrees(math.atan(h/x)),2)}°"
            page.update()
        except: pass

    page.add(ft.Column([
        ft.Text("ВХІДНІ ДАНІ", weight="bold", color="blue"), ft.Row([eh, ev, ew_h]),
        ft.Text("АРСЕНАЛ", weight="bold"),
        ft.Row([add_dd, ft.IconButton("add", on_click=open_bk_add), ft.IconButton("settings", on_click=open_bk_ed)]),
        ft.Row([lm, lcx, ls]),
        ft.Text("МЕТЕО", weight="bold"),
        ft.Row([c_dd, ft.ElevatedButton("ОНОВИТИ", on_click=get_w)]),
        ft.Row([et, ep, ew_g]), l_rho,
        ft.ElevatedButton("РОЗРАХУВАТИ", on_click=calc, bgcolor="green", color="white", width=400, height=50),
        ft.Container(padding=10, border=ft.border.all(1, "grey"), border_radius=10, content=ft.Column([
            ft.Row([ft.Column([ft.Text("ЧАС"), rt], expand=1), ft.Column([ft.Text("ВІДСТАНЬ"), rd], expand=1)]),
            ft.Row([ft.Text("📷 КУТ:"), ra], alignment="center")
        ]))
    ], spacing=7))
    up_a(None)

ft.app(target=main)
