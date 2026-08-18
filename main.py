import os
import json
import ftplib
import sqlite3
import difflib
from datetime import datetime

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window

Window.softinput_mode = "resize"

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "contacts.db")
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ftp_config.json")

COUNTRY_CODES = [
    ("+967", "اليمن"), ("+966", "السعودية"), ("+971", "الإمارات"),
    ("+973", "البحرين"), ("+974", "قطر"), ("+968", "عمان"),
    ("+965", "الكويت"), ("+20", "مصر"), ("+962", "الأردن"),
    ("+963", "سوريا"), ("+961", "لبنان"), ("+970", "فلسطين"),
    ("+212", "المغرب"), ("+213", "الجزائر"), ("+216", "تونس"),
    ("+1", "أمريكا"), ("+44", "بريطانيا"), ("+33", "فرنسا"),
    ("+49", "ألمانيا"), ("+90", "تركيا"), ("+92", "باكستان"),
    ("+91", "الهند"), ("+86", "الصين"), ("+81", "اليابان"),
]

CITIES = [
    "صنعاء", "عدن", "تعز", "الحديدة", "المكلا", "سيئون", "زنجبار",
    "تريم", "شبوة", "بيحان", "صعده", "الحجه", "عمران", "ذمار",
    "إب", "جبلة", "يافع", "لودر", "المحويه", "زبيد", "بيت الفقيه",
    "الرياض", "جدة", "مكة المكرمة", "المدينة المنورة", "الدمام", "الظهران", "الخبر",
    "القاهرة", "الإسكندرية", "الجيزة", "الأقصر", "أسوان",
    "أبو ظبي", "دبي", "الشارقة", "عجمان", "الدوحة", "المنامة", "مسقط",
    "عمّان", "بغداد", "دمشق", "بيروت", "القدس", "رام الله",
    "الدار البيضاء", "الرباط", "مراكش", "فاس", "طنجة",
    "إسطنبول", "لندن", "باريس", "برلين", "روما", "مدريد",
    "نيويورك", "طوكيو", "بكين", "كوالالمبور", "بانكوك",
]

CATEGORIES = [
    "إلكترونيات", "هواتف ذكية", "ملابس", "أغذية", "مشروبات",
    "مواد بناء", "أثاث", "سيارات", "قطع غيار", "مواد تجميل",
    "صحة", "زراعة", "تغليف", "طباعة", "مطاعم", "فنادق",
    "شحن", "توصيل", "استيراد", "تصدير", "تجزئة", "جملة",
    "خدمات", "تصميم", "تسويق", "عقارات", "مقاولات", "صيانة",
    "تنظيف", "أمن", "ذهب", "مجوهرات", "ألعاب", "رياضة",
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
    rows = conn.execute("SELECT * FROM contacts ORDER BY name").fetchall()
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


def fuzzy_match(query, item):
    q = query.lower().strip()
    s = item.lower().strip()
    if not q:
        return 0
    if q in s:
        return 2.0
    score = difflib.SequenceMatcher(None, q, s).ratio()
    for part in s.split():
        score = max(score, difflib.SequenceMatcher(None, q, part).ratio() * 0.8)
    return score


class MainScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))

        header = BoxLayout(size_hint_y=None, height=dp(50))
        header.add_widget(Label(text="مدير جهات الاتصال", font_size=dp(20), bold=True,
                                 color=(1, 1, 1, 1), size_hint_x=0.6))
        header.add_widget(Button(text="FTP", size_hint_x=0.2, font_size=dp(11),
                                  background_color=(0.1, 0.45, 0.91, 1),
                                  on_press=lambda x: setattr(self.manager, "current", "ftp")))
        header.add_widget(Button(text="تصدير", size_hint_x=0.2, font_size=dp(11),
                                  background_color=(0.4, 0.4, 0.4, 1),
                                  on_press=self.export_csv))
        layout.add_widget(header)

        search_box = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(5))
        self.search_input = TextInput(hint_text="بحث...", multiline=False,
                                       font_size=dp(14), size_hint_x=0.6)
        self.search_input.bind(text=self.on_search)
        search_box.add_widget(self.search_input)
        search_box.add_widget(Button(text="بحث", font_size=dp(12),
                                      background_color=(0.1, 0.45, 0.91, 1),
                                      size_hint_x=0.2, on_press=lambda x: self.do_search()))
        search_box.add_widget(Button(text="مسح", font_size=dp(12),
                                      background_color=(0.4, 0.4, 0.4, 1),
                                      size_hint_x=0.2, on_press=self.clear_search))
        layout.add_widget(search_box)

        self.contact_list = BoxLayout(orientation="vertical", spacing=dp(4))
        scroll = ScrollView()
        scroll.add_widget(self.contact_list)
        layout.add_widget(scroll)

        btn_box = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(3))
        for text, color, cmd in [
            ("+ اضافة", (0.1, 0.45, 0.91, 1), self.add_new),
            ("تعديل", (0.4, 0.4, 0.4, 1), self.edit_selected),
            ("حذف", (0.85, 0.19, 0.15, 1), self.delete_sel),
            ("اتصال", (0.0, 0.6, 0.0, 1), self.call_contact),
            ("واتساب", (0.15, 0.83, 0.4, 1), self.open_wa),
        ]:
            btn_box.add_widget(Button(text=text, font_size=dp(11), bold=True,
                                       background_color=color, on_press=cmd))
        layout.add_widget(btn_box)
        self.add_widget(layout)
        self.selected_id = None

    def on_enter(self):
        Clock.schedule_once(lambda dt: self.load_list(), 0.1)

    def load_list(self, contacts=None):
        self.contact_list.clear_widgets()
        if contacts is None:
            contacts = get_all()
        for c in contacts:
            row = self._make_row(c)
            self.contact_list.add_widget(row)

    def _make_row(self, c):
        box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(70),
                        padding=[dp(8), dp(4)], spacing=dp(2))
        bg = [0.93, 0.95, 0.98, 1] if self.selected_id == c["id"] else [1, 1, 1, 1]
        box.canvas.before.clear()
        with box.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(*bg)
            RoundedRectangle(pos=box.pos, size=box.size, radius=[dp(8)])

        top = BoxLayout(orientation="horizontal")
        top.add_widget(Label(text=c["name"], font_size=dp(14), bold=True,
                              color=(0, 0, 0, 1), halign="right", text_size=(None, None),
                              size_hint_x=0.5))
        phone_txt = c["phone"] or ""
        top.add_widget(Label(text=phone_txt, font_size=dp(12),
                              color=(0.33, 0.33, 0.33, 1), halign="left",
                              size_hint_x=0.5))

        bot = BoxLayout(orientation="horizontal")
        addr = c["address"] or ""
        cat = c["category"] or ""
        bot.add_widget(Label(text=f"{cat}  |  {addr}", font_size=dp(10),
                              color=(0.5, 0.5, 0.5, 1), halign="right",
                              text_size=(None, None), size_hint_x=1))

        box.add_widget(top)
        box.add_widget(bot)

        def on_touch(instance, touch, cid=c["id"]):
            if instance.collide_point(*touch.pos):
                self.selected_id = cid
                self.load_list()
                return True
        box.bind(on_touch_down=on_touch)
        return box

    def on_search(self, instance, text):
        if len(text) >= 1:
            results = search_db(text)
            self.load_list(results)

    def do_search(self):
        text = self.search_input.text.strip()
        if text:
            self.load_list(search_db(text))

    def clear_search(self, *a):
        self.search_input.text = ""
        self.load_list()

    def add_new(self, *a):
        self.manager.get_screen("add").editing_id = None
        self.manager.get_screen("add").clear_form()
        self.manager.current = "add"

    def edit_selected(self, *a):
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

    def open_wa(self, *a):
        if not self.selected_id:
            return
        contacts = get_all()
        for c in contacts:
            if c["id"] == self.selected_id:
                phone = (c["phone"] or "").replace("+", "").replace(" ", "")
                if phone:
                    import webbrowser
                    webbrowser.open(f"https://wa.me/{phone}")
                break

    def call_contact(self, *a):
        if not self.selected_id:
            return
        contacts = get_all()
        for c in contacts:
            if c["id"] == self.selected_id:
                phone = (c["phone"] or "").strip()
                if phone:
                    import webbrowser
                    webbrowser.open(f"tel:{phone}")
                break

    def export_csv(self, *a):
        from kivy.utils import platform
        if platform == "android":
            from android.storage import app_storage_path
            path = os.path.join(app_storage_path(), "contacts_export.csv")
        else:
            path = "contacts_export.csv"
        contacts = get_all()
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            f.write("الاسم,رقم الهاتف,البريد,العنوان,التصنيف,ملاحظات\n")
            for c in contacts:
                f.write(f'"{c["name"]}","{c["phone"]}","{c["email"]}","{c["address"]}","{c["category"]}","{c["notes"]}"\n')


class AddScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.editing_id = None
        layout = BoxLayout(orientation="vertical", padding=dp(15), spacing=dp(8))

        top = BoxLayout(size_hint_y=None, height=dp(45))
        top.add_widget(Button(text="رجوع", font_size=dp(12),
                               background_color=(0.4, 0.4, 0.4, 1),
                               on_press=lambda x: setattr(self.manager, "current", "main")))
        top.add_widget(Label(text="بيانات جهة الاتصال", font_size=dp(16), bold=True,
                              color=(0, 0, 0, 1)))
        layout.add_widget(top)

        self.name_in = self._field(layout, "اسم المورد / التاجر")
        self.phone_in = self._field(layout, "رقم الهاتف (بدون مفتاح الدولة)")
        self.email_in = self._field(layout, "البريد الإلكتروني")
        self.address_in = self._field(layout, "العنوان (اقتراح تلقائي)")
        self.category_in = self._field(layout, "التصنيف (اقتراح تلقائي)")
        self.notes_in = self._field(layout, "ملاحظات")

        code_box = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(5))
        codes = [f"{c} {n}" for c, n in COUNTRY_CODES]
        self.code_spinner = Spinner(text="+967 اليمن", values=codes,
                                     size_hint_x=0.5, font_size=dp(12))
        code_box.add_widget(Label(text="مفتاح الدولة:", font_size=dp(12),
                                   color=(0, 0, 0, 1), size_hint_x=0.5))
        code_box.add_widget(self.code_spinner)
        layout.add_widget(code_box)

        save_btn = Button(text="  حفظ  ", font_size=dp(16), bold=True,
                           size_hint_y=None, height=dp(50),
                           background_color=(0.1, 0.45, 0.91, 1),
                           on_press=self.save_it)
        layout.add_widget(save_btn)

        scroll = ScrollView()
        inner = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(5))
        inner.bind(minimum_height=inner.setter("height"))
        for child in list(layout.children):
            pass
        self.add_widget(layout)

    def _field(self, parent, hint):
        ti = TextInput(hint_text=hint, multiline=False, font_size=dp(14),
                       size_hint_y=None, height=dp(42), padding=[dp(8), dp(8)])
        parent.add_widget(ti)
        return ti

    def clear_form(self):
        self.name_in.text = ""
        self.phone_in.text = ""
        self.email_in.text = ""
        self.address_in.text = ""
        self.category_in.text = ""
        self.notes_in.text = ""
        self.code_spinner.text = "+967 اليمن"

    def save_it(self, *a):
        name = self.name_in.text.strip()
        if not name:
            return
        code = self.code_spinner.text.split()[0]
        phone = self.phone_in.text.strip().replace(" ", "")
        full_phone = f"{code}{phone}" if phone else ""
        add_contact(name, full_phone, self.email_in.text.strip(),
                    self.address_in.text.strip(), self.category_in.text.strip(),
                    self.notes_in.text.strip())
        self.manager.current = "main"

    def on_enter(self):
        if self.editing_id:
            contacts = get_all()
            for c in contacts:
                if c["id"] == self.editing_id:
                    self.name_in.text = c["name"]
                    self.email_in.text = c["email"] or ""
                    self.address_in.text = c["address"] or ""
                    self.category_in.text = c["category"] or ""
                    self.notes_in.text = c["notes"] or ""
                    phone = c["phone"] or ""
                    for code, name in COUNTRY_CODES:
                        if phone.startswith(code):
                            self.code_spinner.text = f"{code} {name}"
                            self.phone_in.text = phone[len(code):]
                            break
                    else:
                        self.phone_in.text = phone
                    break


class FTPScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        layout = BoxLayout(orientation="vertical", padding=dp(15), spacing=dp(8))

        top = BoxLayout(size_hint_y=None, height=dp(45))
        top.add_widget(Button(text="رجوع", font_size=dp(12),
                               background_color=(0.4, 0.4, 0.4, 1),
                               on_press=lambda x: setattr(self.manager, "current", "main")))
        top.add_widget(Label(text="النسخ الاحتياطي FTP", font_size=dp(16), bold=True,
                              color=(0, 0, 0, 1)))
        layout.add_widget(top)

        cfg = load_config()
        self.host_in = self._field(layout, "عنوان الخادم (Host)")
        self.host_in.text = cfg.get("host", "")
        self.port_in = self._field(layout, "المنفذ (Port)")
        self.port_in.text = cfg.get("port", "21")
        self.user_in = self._field(layout, "اسم المستخدم")
        self.user_in.text = cfg.get("username", "")
        self.pass_in = self._field(layout, "كلمة المرور")
        self.pass_in.password = True
        self.pass_in.text = cfg.get("password", "")
        self.dir_in = self._field(layout, "المجلد البعيد")
        self.dir_in.text = cfg.get("remote_dir", "/")

        btn_box = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))
        btn_box.add_widget(Button(text="اختبار", font_size=dp(12),
                                   background_color=(0.4, 0.4, 0.4, 1),
                                   on_press=self.test_conn))
        btn_box.add_widget(Button(text="نسخ احتياطي", font_size=dp(12), bold=True,
                                   background_color=(0.1, 0.45, 0.91, 1),
                                   on_press=self.do_backup))
        btn_box.add_widget(Button(text="استعادة", font_size=dp(12),
                                   background_color=(0.85, 0.19, 0.15, 1),
                                   on_press=self.do_restore))
        btn_box.add_widget(Button(text="حفظ", font_size=dp(12),
                                   background_color=(0.15, 0.83, 0.4, 1),
                                   on_press=self.save_cfg))
        layout.add_widget(btn_box)

        self.status = Label(text="", font_size=dp(11), color=(0.3, 0.3, 0.3, 1),
                             size_hint_y=None, height=dp(30))
        layout.add_widget(self.status)

        self.backups_list = BoxLayout(orientation="vertical", spacing=dp(3))
        scroll = ScrollView()
        scroll.add_widget(self.backups_list)
        layout.add_widget(scroll)

        self.add_widget(layout)

    def _field(self, parent, hint):
        ti = TextInput(hint_text=hint, multiline=False, font_size=dp(13),
                       size_hint_y=None, height=dp(38), padding=[dp(8), dp(8)])
        parent.add_widget(ti)
        return ti

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
