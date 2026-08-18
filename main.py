import os
import json
import ftplib
import sqlite3
import difflib
from datetime import datetime

from kivy.app import App
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.utils import platform as kivy_platform
from kivy.resources import resource_find
try:
    from android.storage import app_storage_path
    BASE_DIR = app_storage_path()
except Exception:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_FILE = os.path.join(BASE_DIR, "contacts.db")
CONFIG_FILE = os.path.join(BASE_DIR, "ftp_config.json")

AR = "Sans"
try:
    font_regular = resource_find("NotoSansArabic.ttf")
    font_bold = resource_find("NotoSansArabicBold.ttf")
    if font_regular and os.path.exists(font_regular):
        LabelBase.register(name="Arabic", fn_regular=font_regular, fn_bold=font_bold or font_regular)
        AR = "Arabic"
except Exception:
    pass

Window.softinput_mode = "resize"

COUNTRY_CODES = [
    ("+967", "Yemen", "Yemen"),
    ("+966", "Saudi Arabia", "Saudi Arabia"),
    ("+971", "UAE", "UAE"),
    ("+973", "Bahrain", "Bahrain"),
    ("+974", "Qatar", "Qatar"),
    ("+968", "Oman", "Oman"),
    ("+965", "Kuwait", "Kuwait"),
    ("+20", "Egypt", "Egypt"),
    ("+962", "Jordan", "Jordan"),
    ("+963", "Syria", "Syria"),
    ("+961", "Lebanon", "Lebanon"),
    ("+970", "Palestine", "Palestine"),
    ("+212", "Morocco", "Morocco"),
    ("+213", "Algeria", "Algeria"),
    ("+216", "Tunisia", "Tunisia"),
    ("+1", "USA", "USA"),
    ("+44", "UK", "UK"),
    ("+33", "France", "France"),
    ("+49", "Germany", "Germany"),
    ("+90", "Turkey", "Turkey"),
    ("+92", "Pakistan", "Pakistan"),
    ("+91", "India", "India"),
    ("+86", "China", "China"),
    ("+81", "Japan", "Japan"),
]

COUNTRY_LABELS = {
    "Yemen": "اليمن",
    "Saudi Arabia": "السعودية",
    "UAE": "الإمارات",
    "Bahrain": "البحرين",
    "Qatar": "قطر",
    "Oman": "عمان",
    "Kuwait": "الكويت",
    "Egypt": "مصر",
    "Jordan": "الأردن",
    "Syria": "سوريا",
    "Lebanon": "لبنان",
    "Palestine": "فلسطين",
    "Morocco": "المغرب",
    "Algeria": "الجزائر",
    "Tunisia": "تونس",
    "USA": "أمريكا",
    "UK": "بريطانيا",
    "France": "فرنسا",
    "Germany": "ألمانيا",
    "Turkey": "تركيا",
    "Pakistan": "باكستان",
    "India": "الهند",
    "China": "الصين",
    "Japan": "اليابان",
}

CITIES = [
    "صنعاء", "عدن", "تعز", "الحديدة", "المكلا", "سيئون", "زنجبار",
    "تريم", "شبوة", "بيحان", "صعده", "الحجه", "عمران", "ذمار",
    "إب", "جبلة", "يافع", "لودر", "المحويه", "زبيد", "بيت الفقيه",
    "الرياض", "جدة", "مكة المكرمة", "المدينة المنورة", "الدمام",
    "القاهرة", "الإسكندرية", "الجيزة", "الأقصر", "أسوان",
    "أبو ظبي", "دبي", "الشارقة", "عمّان", "بغداد", "دمشق", "بيروت",
    "الدار البيضاء", "الرباط", "مراكش", "إسطنبول", "لندن", "باريس",
    "نيويورك", "طوكيو", "بكين",
]

CATEGORIES = [
    "إلكترونيات", "هواتف ذكية", "ملابس", "أغذية", "مشروبات",
    "مواد بناء", "أثاث", "سيارات", "قطع غيار", "مواد تجميل",
    "صحة", "زراعة", "تغليف", "طباعة", "مطاعم", "فنادق",
    "شحن", "توصيل", "استيراد", "تصدير", "تجزئة", "جملة",
    "خدمات", "تصميم", "تسويق", "عقارات", "مقاولات", "صيانة",
    "تنظيف", "ذهب", "مجوهرات",
]


def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, phone TEXT, email TEXT, address TEXT,
        category TEXT DEFAULT '', notes TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit()
    conn.close()


def get_all():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM contacts ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_db(q):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    t = f"%{q}%"
    rows = conn.execute("""SELECT * FROM contacts WHERE name LIKE ? OR phone LIKE ?
        OR email LIKE ? OR address LIKE ? OR category LIKE ? OR notes LIKE ?
        ORDER BY name""", (t, t, t, t, t, t)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_contact(name, phone, email, address, category, notes):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT INTO contacts (name,phone,email,address,category,notes) VALUES (?,?,?,?,?,?)",
                 (name, phone, email, address, category, notes))
    conn.commit()
    conn.close()


def update_contact(cid, name, phone, email, address, category, notes):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("UPDATE contacts SET name=?,phone=?,email=?,address=?,category=?,notes=? WHERE id=?",
                 (name, phone, email, address, category, notes, cid))
    conn.commit()
    conn.close()


def delete_contact(cid):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("DELETE FROM contacts WHERE id=?", (cid,))
    conn.commit()
    conn.close()


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def ar_btn(text, color, cmd, width_hint=0.2):
    return Button(
        text=text, font_name=AR, font_size=dp(12), bold=True,
        background_color=color, size_hint_x=width_hint, on_press=cmd
    )


def ar_label(text, size=dp(14), color=(0, 0, 0, 1), bold=False, halign="right"):
    return Label(
        text=text, font_name=AR, font_size=size,
        color=color, bold=bold, halign=halign,
        text_size=(None, None), valign="middle"
    )


def ar_input(hint, height=dp(42)):
    return TextInput(
        hint_text=hint, hint_font_name=AR,
        font_name=AR, font_size=dp(14),
        multiline=False, size_hint_y=None, height=height,
        padding=[dp(10), dp(8)]
    )


class MainScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.selected_id = None
        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(6))

        bg = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(60),
                       padding=[dp(10), dp(5)])
        bg.add_widget(ar_label("مدير جهات الاتصال", size=dp(22), bold=True, color=(1,1,1,1), halign="center"))
        root.add_widget(bg)

        search = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(5))
        self.search_input = ar_input("بحث بالاسم أو الرقم أو العنوان...")
        self.search_input.bind(text=self.on_search)
        search.add_widget(self.search_input)
        search.add_widget(ar_btn("بحث", (0.1, 0.45, 0.91, 1), lambda x: self.do_search(), 0.2))
        search.add_widget(ar_btn("مسح", (0.5, 0.5, 0.5, 1), self.clear_search, 0.15))
        root.add_widget(search)

        self.contact_list = BoxLayout(orientation="vertical", spacing=dp(3), size_hint_y=None)
        self.contact_list.bind(minimum_height=self.contact_list.setter("height"))
        scroll = ScrollView()
        scroll.add_widget(self.contact_list)
        root.add_widget(scroll)

        btns = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(3))
        btns.add_widget(ar_btn("+ اضافة", (0.1, 0.45, 0.91, 1), self.add_new, 0.2))
        btns.add_widget(ar_btn("تعديل", (0.3, 0.3, 0.3, 1), self.edit_sel, 0.2))
        btns.add_widget(ar_btn("حذف", (0.85, 0.19, 0.15, 1), self.delete_sel, 0.2))
        btns.add_widget(ar_btn("اتصال", (0.0, 0.55, 0.0, 1), self.call_contact, 0.2))
        btns.add_widget(ar_btn("واتساب", (0.15, 0.83, 0.4, 1), self.open_wa, 0.2))
        root.add_widget(btns)

        nav = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(5))
        nav.add_widget(ar_btn("النسخ الاحتياطي", (0.1, 0.45, 0.91, 1),
                              lambda x: setattr(self.manager, "current", "ftp"), 0.5))
        nav.add_widget(ar_btn("تصدير CSV", (0.3, 0.3, 0.3, 1), self.export_csv, 0.5))
        root.add_widget(nav)

        self.add_widget(root)

    def on_enter(self):
        Clock.schedule_once(lambda dt: self.load_list(), 0.1)

    def load_list(self, contacts=None):
        self.contact_list.clear_widgets()
        if contacts is None:
            contacts = get_all()
        if not contacts:
            self.contact_list.add_widget(ar_label("لا توجد جهات اتصال", size=dp(16), color=(0.5,0.5,0.5,1)))
            return
        for c in contacts:
            self.contact_list.add_widget(self._make_row(c))

    def _make_row(self, c):
        is_sel = self.selected_id == c["id"]
        bg_color = (0.88, 0.92, 1, 1) if is_sel else (1, 1, 1, 1)
        border_color = (0.1, 0.45, 0.91, 1) if is_sel else (0.85, 0.85, 0.85, 1)

        box = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(72),
                        padding=[dp(8), dp(6)], spacing=dp(8))
        box.canvas.before.clear()
        with box.canvas.before:
            from kivy.graphics import Color, RoundedRectangle, Line
            Color(*bg_color)
            RoundedRectangle(pos=box.pos, size=box.size, radius=[dp(10)])
            Color(*border_color)
            Line(rounded_rectangle=(box.x, box.y, box.width, box.height, dp(10)), width=dp(1))

        info = BoxLayout(orientation="vertical", spacing=dp(2))
        phone = c["phone"] or ""
        addr = c["address"] or ""
        cat = c["category"] or ""
        name_lbl = ar_label(c["name"], size=dp(15), bold=True, halign="right")
        name_lbl.size_hint_x = 1
        info.add_widget(name_lbl)

        detail_text = f"{phone}"
        if cat:
            detail_text += f"  |  {cat}"
        if addr:
            detail_text += f"  |  {addr}"
        det = ar_label(detail_text, size=dp(11), color=(0.4, 0.4, 0.4, 1), halign="right")
        det.size_hint_x = 1
        info.add_widget(det)
        box.add_widget(info)

        call_btn = Button(text=" اتصال ", font_name=AR, font_size=dp(11),
                          background_color=(0.0, 0.6, 0.0, 1), size_hint_x=None, width=dp(70))
        call_btn.bind(on_press=lambda inst, ph=phone: self._call(ph))
        box.add_widget(call_btn)

        def on_touch(instance, touch, cid=c["id"]):
            if instance.collide_point(*touch.pos):
                self.selected_id = cid
                self.load_list()
                return True
        box.bind(on_touch_down=on_touch)
        return box

    def _call(self, phone):
        if phone:
            import webbrowser
            webbrowser.open(f"tel:{phone}")

    def on_search(self, inst, text):
        if len(text) >= 1:
            self.load_list(search_db(text))

    def do_search(self):
        t = self.search_input.text.strip()
        if t:
            self.load_list(search_db(t))

    def clear_search(self, *a):
        self.search_input.text = ""
        self.load_list()

    def add_new(self, *a):
        self.manager.get_screen("add").editing_id = None
        self.manager.get_screen("add").clear_form()
        self.manager.current = "add"

    def edit_sel(self, *a):
        if not self.selected_id:
            return
        self.manager.get_screen("add").editing_id = self.selected_id
        self.manager.current = "add"

    def delete_sel(self, *a):
        if not self.selected_id:
            return
        delete_contact(self.selected_id)
        self.selected_id = None
        self.load_list()

    def call_contact(self, *a):
        if not self.selected_id:
            return
        for c in get_all():
            if c["id"] == self.selected_id:
                phone = (c["phone"] or "").strip()
                if phone:
                    import webbrowser
                    webbrowser.open(f"tel:{phone}")
                break

    def open_wa(self, *a):
        if not self.selected_id:
            return
        for c in get_all():
            if c["id"] == self.selected_id:
                phone = (c["phone"] or "").replace("+", "").replace(" ", "")
                if phone:
                    import webbrowser
                    webbrowser.open(f"https://wa.me/{phone}")
                break

    def export_csv(self, *a):
        path = os.path.join(BASE_DIR, "contacts_export.csv")
        contacts = get_all()
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            f.write("الاسم,رقم الهاتف,البريد,العنوان,التصنيف,ملاحظات\n")
            for c in contacts:
                f.write(f'"{c["name"]}","{c["phone"]}","{c["email"]}","{c["address"]}","{c["category"]}","{c["notes"]}"\n')


class AddScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.editing_id = None
        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(6))

        top = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(5))
        top.add_widget(ar_btn("رجوع", (0.5, 0.5, 0.5, 1),
                              lambda x: setattr(self.manager, "current", "main"), 0.3))
        top.add_widget(ar_label("بيانات جهة الاتصال", size=dp(18), bold=True, halign="center"))
        root.add_widget(top)

        scroll_inner = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        scroll_inner.bind(minimum_height=scroll_inner.setter("height"))

        self.name_in = ar_input("اسم المورد / التاجر")
        self.name_in.size_hint_y = None
        self.name_in.height = dp(45)
        scroll_inner.add_widget(self.name_in)

        code_box = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(5))
        code_values = [f"{c[0]} - {COUNTRY_LABELS[c[1]]}" for c in COUNTRY_CODES]
        self.code_spinner = Spinner(
            text="+967 - اليمن", values=code_values,
            font_name=AR, font_size=dp(12),
            background_color=(0.1, 0.45, 0.91, 1)
        )
        code_box.add_widget(ar_label("مفتاح الدولة:", size=dp(12)))
        code_box.add_widget(self.code_spinner)
        scroll_inner.add_widget(code_box)

        self.phone_in = ar_input("رقم الهاتف (بدون المفتاح)")
        self.phone_in.size_hint_y = None
        self.phone_in.height = dp(45)
        scroll_inner.add_widget(self.phone_in)

        self.email_in = ar_input("البريد الإلكتروني")
        self.email_in.size_hint_y = None
        self.email_in.height = dp(45)
        scroll_inner.add_widget(self.email_in)

        self.address_in = ar_input("العنوان")
        self.address_in.size_hint_y = None
        self.address_in.height = dp(45)
        scroll_inner.add_widget(self.address_in)

        self.category_in = ar_input("التصنيف")
        self.category_in.size_hint_y = None
        self.category_in.height = dp(45)
        scroll_inner.add_widget(self.category_in)

        self.notes_in = ar_input("ملاحظات")
        self.notes_in.size_hint_y = None
        self.notes_in.height = dp(45)
        scroll_inner.add_widget(self.notes_in)

        save_btn = Button(
            text="حفظ", font_name=AR, font_size=dp(18), bold=True,
            size_hint_y=None, height=dp(55),
            background_color=(0.1, 0.45, 0.91, 1), on_press=self.save_it
        )
        scroll_inner.add_widget(save_btn)

        sv = ScrollView()
        sv.add_widget(scroll_inner)
        root.add_widget(sv)
        self.add_widget(root)

    def clear_form(self):
        self.name_in.text = ""
        self.phone_in.text = ""
        self.email_in.text = ""
        self.address_in.text = ""
        self.category_in.text = ""
        self.notes_in.text = ""
        self.code_spinner.text = "+967 - اليمن"

    def save_it(self, *a):
        name = self.name_in.text.strip()
        if not name:
            return
        code = self.code_spinner.text.split(" - ")[0].strip()
        phone = self.phone_in.text.strip().replace(" ", "")
        full_phone = f"{code}{phone}" if phone else ""

        if self.editing_id:
            update_contact(self.editing_id, name, full_phone,
                           self.email_in.text.strip(), self.address_in.text.strip(),
                           self.category_in.text.strip(), self.notes_in.text.strip())
        else:
            add_contact(name, full_phone, self.email_in.text.strip(),
                        self.address_in.text.strip(), self.category_in.text.strip(),
                        self.notes_in.text.strip())
        self.manager.current = "main"

    def on_enter(self):
        if self.editing_id:
            for c in get_all():
                if c["id"] == self.editing_id:
                    self.name_in.text = c["name"]
                    self.email_in.text = c["email"] or ""
                    self.address_in.text = c["address"] or ""
                    self.category_in.text = c["category"] or ""
                    self.notes_in.text = c["notes"] or ""
                    phone = c["phone"] or ""
                    for code, eng, _ in COUNTRY_CODES:
                        if phone.startswith(code):
                            self.code_spinner.text = f"{code} - {COUNTRY_LABELS[eng]}"
                            self.phone_in.text = phone[len(code):]
                            break
                    else:
                        self.phone_in.text = phone
                    break


class FTPScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(6))

        top = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(5))
        top.add_widget(ar_btn("رجوع", (0.5, 0.5, 0.5, 1),
                              lambda x: setattr(self.manager, "current", "main"), 0.3))
        top.add_widget(ar_label("النسخ الاحتياطي", size=dp(18), bold=True, halign="center"))
        root.add_widget(top)

        cfg = load_config()
        self.host_in = ar_input("عنوان الخادم (Host)")
        self.host_in.text = cfg.get("host", "")
        root.add_widget(self.host_in)

        self.port_in = ar_input("المنفذ (Port)")
        self.port_in.text = cfg.get("port", "21")
        root.add_widget(self.port_in)

        self.user_in = ar_input("اسم المستخدم")
        self.user_in.text = cfg.get("username", "")
        root.add_widget(self.user_in)

        self.pass_in = ar_input("كلمة المرور")
        self.pass_in.password = True
        self.pass_in.text = cfg.get("password", "")
        root.add_widget(self.pass_in)

        self.dir_in = ar_input("المجلد البعيد")
        self.dir_in.text = cfg.get("remote_dir", "/")
        root.add_widget(self.dir_in)

        btns = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(4))
        btns.add_widget(ar_btn("اختبار", (0.5, 0.5, 0.5, 1), self.test_conn, 0.25))
        btns.add_widget(ar_btn("نسخ احتياطي", (0.1, 0.45, 0.91, 1), self.do_backup, 0.25))
        btns.add_widget(ar_btn("استعادة", (0.85, 0.19, 0.15, 1), self.do_restore, 0.25))
        btns.add_widget(ar_btn("حفظ", (0.0, 0.6, 0.0, 1), self.save_cfg, 0.25))
        root.add_widget(btns)

        self.status = ar_label("", size=dp(12), color=(0.3, 0.3, 0.3, 1))
        self.status.size_hint_y = None
        self.status.height = dp(30)
        root.add_widget(self.status)

        self.add_widget(root)

    def _cfg(self):
        return {
            "host": self.host_in.text.strip(),
            "port": self.port_in.text.strip() or "21",
            "username": self.user_in.text.strip(),
            "password": self.pass_in.text.strip(),
            "remote_dir": self.dir_in.text.strip() or "/",
        }

    def save_cfg(self, *a):
        save_config(self._cfg())
        self.status.text = "تم حفظ الإعدادات"

    def test_conn(self, *a):
        cfg = self._cfg()
        try:
            ftp = ftplib.FTP()
            ftp.connect(cfg["host"], int(cfg["port"]), timeout=10)
            ftp.login(cfg["username"], cfg["password"])
            ftp.quit()
            self.status.text = "تم الاتصال بنجاح"
        except Exception as e:
            self.status.text = f"خطأ: {str(e)}"

    def do_backup(self, *a):
        cfg = self._cfg()
        try:
            ftp = ftplib.FTP()
            ftp.connect(cfg["host"], int(cfg["port"]), timeout=10)
            ftp.login(cfg["username"], cfg["password"])
            try:
                ftp.cwd(cfg["remote_dir"])
            except:
                ftp.mkd(cfg["remote_dir"])
                ftp.cwd(cfg["remote_dir"])
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            fn = f"contacts_backup_{ts}.db"
            with open(DB_FILE, "rb") as f:
                ftp.storbinary(f"STOR {fn}", f)
            ftp.quit()
            self.status.text = f"تم النسخ: {fn}"
        except Exception as e:
            self.status.text = f"خطأ: {str(e)}"

    def do_restore(self, *a):
        cfg = self._cfg()
        try:
            ftp = ftplib.FTP()
            ftp.connect(cfg["host"], int(cfg["port"]), timeout=10)
            ftp.login(cfg["username"], cfg["password"])
            try:
                ftp.cwd(cfg["remote_dir"])
            except:
                self.status.text = "المجلد غير موجود"
                return
            files = []
            ftp.retrlines("LIST", files.append)
            backups = []
            for line in files:
                parts = line.split()
                if len(parts) >= 9:
                    fn = " ".join(parts[8:])
                    if fn.endswith(".db"):
                        backups.append(fn)
            if not backups:
                self.status.text = "لا توجد نسخ احتياطية"
                ftp.quit()
                return
            latest = sorted(backups)[-1]
            temp = DB_FILE + ".restore_tmp"
            with open(temp, "wb") as f:
                ftp.retrbinary(f"RETR {latest}", f.write)
            ftp.quit()
            import shutil
            shutil.copy2(temp, DB_FILE)
            os.remove(temp)
            self.status.text = f"تمت الاستعادة: {latest}"
        except Exception as e:
            self.status.text = f"خطأ: {str(e)}"


class ContactManagerApp(App):
    def build(self):
        self.title = "مدير جهات الاتصال"
        init_db()
        sm = ScreenManager()
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(AddScreen(name="add"))
        sm.add_widget(FTPScreen(name="ftp"))
        return sm


if __name__ == "__main__":
    ContactManagerApp().run()
