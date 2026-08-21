import os
import json
import ftplib
import sqlite3
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
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.utils import platform as kivy_platform
from kivy.resources import resource_find
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line

try:
    from android.storage import app_storage_path
    BASE_DIR = app_storage_path()
except Exception:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_FILE = os.path.join(BASE_DIR, "contacts.db")
CONFIG_FILE = os.path.join(BASE_DIR, "ftp_config.json")

AR = "Sans"
try:
    fr = resource_find("NotoSansArabic.ttf")
    fb = resource_find("NotoSansArabicBold.ttf")
    if fr and os.path.exists(fr):
        LabelBase.register(name="Arabic", fn_regular=fr, fn_bold=(fb if fb and os.path.exists(fb) else fr))
        AR = "Arabic"
except Exception:
    pass

Window.softinput_mode = "resize"

IS_ANDROID = (kivy_platform == "android")

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
    "الرياض", "جدة", "مكة المكرمة", "المدينة المنورة", "الدمام",
    "القاهرة", "الإسكندرية", "الجيزة", "الأقصر", "أسوان",
    "أبو ظبي", "دبي", "الشارقة", "عمّان", "بغداد", "دمشق", "بيروت",
    "الدار البيضاء", "الرباط", "مراكش", "إسطنبول", "لندن", "باريس",
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
    t = "%" + q + "%"
    rows = conn.execute(
        """SELECT * FROM contacts WHERE name LIKE ? OR phone LIKE ?
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
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def open_url(url):
    try:
        if IS_ANDROID:
            from jnius import autoclass
            Intent = autoclass("android.content.Intent")
            Uri = autoclass("android.net.Uri")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
            PythonActivity.mActivity.startActivity(intent)
        else:
            import webbrowser
            webbrowser.open(url)
    except Exception:
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception:
            pass


def call_phone(phone):
    if not phone:
        return
    try:
        if IS_ANDROID:
            from jnius import autoclass
            Intent = autoclass("android.content.Intent")
            Uri = autoclass("android.net.Uri")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            intent = Intent(Intent.ACTION_DIAL, Uri.parse("tel:" + phone))
            PythonActivity.mActivity.startActivity(intent)
        else:
            import webbrowser
            webbrowser.open("tel:" + phone)
    except Exception:
        try:
            import webbrowser
            webbrowser.open("tel:" + phone)
        except Exception:
            pass


def ar_btn(text, color, cmd, width_hint=0.2, height=None):
    b = Button(text=text, font_name=AR, font_size=dp(12), bold=True,
               background_color=color, size_hint_x=width_hint)
    if height:
        b.size_hint_y = None
        b.height = height
    b.bind(on_press=cmd)
    return b


def ar_label(text, size=None, color=(0, 0, 0, 1), bold=False, halign="right"):
    lbl = Label(text=text, font_name=AR,
                font_size=size if size else dp(14),
                color=color, bold=bold, halign=halign, valign="middle")
    lbl.bind(size=lambda inst, val: setattr(inst, "text_size", val))
    return lbl


def ar_input(hint, height=None):
    ti = TextInput(hint_text=hint, hint_font_name=AR,
                   font_name=AR, font_size=dp(14),
                   multiline=False, size_hint_y=None,
                   height=height if height else dp(42),
                   padding=[dp(10), dp(8)])
    return ti


class MainScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.selected_id = None
        root = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(6))

        header = BoxLayout(size_hint_y=None, height=dp(56), padding=[dp(12), dp(8)])
        with header.canvas.before:
            Color(0.10, 0.45, 0.91, 1)
            header.bg_rect = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=lambda i, v: setattr(header.bg_rect, "pos", v),
                    size=lambda i, v: setattr(header.bg_rect, "size", v))
        title = ar_label("مدير جهات الاتصال", size=dp(20), bold=True,
                         color=(1, 1, 1, 1), halign="center")
        header.add_widget(title)
        root.add_widget(header)

        search = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(5))
        self.search_input = ar_input("بحث...")
        self.search_input.bind(text=self.on_search)
        search.add_widget(self.search_input)
        search.add_widget(ar_btn("مسح", (0.45, 0.45, 0.45, 1), self.clear_search, 0.18))
        root.add_widget(search)

        self.contact_list = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None)
        self.contact_list.bind(minimum_height=self.contact_list.setter("height"))
        scroll = ScrollView(bar_width=dp(4))
        scroll.add_widget(self.contact_list)
        root.add_widget(scroll)

        btns = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(3))
        btns.add_widget(ar_btn("+ اضافة", (0.10, 0.45, 0.91, 1), self.add_new, 0.24))
        btns.add_widget(ar_btn("تعديل", (0.35, 0.35, 0.35, 1), self.edit_sel, 0.19))
        btns.add_widget(ar_btn("حذف", (0.85, 0.19, 0.15, 1), self.delete_sel, 0.19))
        btns.add_widget(ar_btn("اتصال", (0.0, 0.55, 0.15, 1), self.call_contact, 0.19))
        btns.add_widget(ar_btn("واتساب", (0.15, 0.70, 0.30, 1), self.open_wa, 0.19))
        root.add_widget(btns)

        nav = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(5))
        nav.add_widget(ar_btn("نسخ احتياطي FTP", (0.10, 0.45, 0.91, 1), self.go_ftp, 0.55))
        nav.add_widget(ar_btn("تصدير CSV", (0.35, 0.35, 0.35, 1), self.export_csv, 0.45))
        root.add_widget(nav)

        self.add_widget(root)

    def go_ftp(self, *a):
        self.manager.current = "ftp"

    def on_enter(self):
        Clock.schedule_once(lambda dt: self.load_list(), 0.05)

    def load_list(self, contacts=None):
        self.contact_list.clear_widgets()
        try:
            if contacts is None:
                contacts = get_all()
        except Exception:
            contacts = []
        if not contacts:
            empty = ar_label("لا توجد جهات اتصال\nاضغط + اضافة لبدء التسجيل",
                             size=dp(15), color=(0.5, 0.5, 0.5, 1), halign="center")
            empty.size_hint_y = None
            empty.height = dp(120)
            self.contact_list.add_widget(empty)
            return
        for c in contacts:
            self.contact_list.add_widget(self._make_row(c))

    def _make_row(self, c):
        is_sel = (self.selected_id == c["id"])
        bg_color = (0.87, 0.92, 1.0, 1) if is_sel else (1, 1, 1, 1)
        border_color = (0.10, 0.45, 0.91, 1) if is_sel else (0.85, 0.85, 0.85, 1)

        box = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(74),
                        padding=[dp(10), dp(6)], spacing=dp(8))

        with box.canvas.before:
            bc = Color(*bg_color)
            rr = RoundedRectangle(pos=box.pos, size=box.size, radius=[dp(10)])
            lc = Color(*border_color)
            ln = Line(rounded_rectangle=(box.x, box.y, box.width, box.height, dp(10)), width=dp(1))

        def upd_pos(inst, val):
            rr.pos = val
            ln.rounded_rectangle = (val[0], val[1], inst.width, inst.height, dp(10))

        def upd_size(inst, val):
            rr.size = val
            ln.rounded_rectangle = (inst.x, inst.y, val[0], val[1], dp(10))

        box.bind(pos=upd_pos, size=upd_size)

        info = BoxLayout(orientation="vertical", spacing=dp(2))
        phone = c.get("phone") or ""
        addr = c.get("address") or ""
        cat = c.get("category") or ""

        name_lbl = ar_label(str(c.get("name") or ""), size=dp(15), bold=True)
        name_lbl.size_hint_x = 1
        info.add_widget(name_lbl)

        detail = phone
        if cat:
            detail += "  |  " + cat
        if addr:
            detail += "  |  " + addr
        det_lbl = ar_label(detail, size=dp(11), color=(0.42, 0.42, 0.42, 1))
        det_lbl.size_hint_x = 1
        info.add_widget(det_lbl)
        box.add_widget(info)

        call_btn = Button(text="اتصال", font_name=AR, font_size=dp(11), bold=True,
                          background_color=(0.0, 0.55, 0.15, 1),
                          size_hint_x=None, width=dp(72))
        call_btn.bind(on_press=lambda inst, ph=phone: call_phone(ph))
        box.add_widget(call_btn)

        def on_touch(instance, touch, cid=c["id"]):
            if instance.collide_point(*touch.pos):
                self.selected_id = cid
                Clock.schedule_once(lambda dt: self.load_list(), 0)
                return True
            return False

        box.bind(on_touch_down=on_touch)
        return box

    def on_search(self, inst, text):
        if len(text.strip()) >= 1:
            try:
                results = search_db(text.strip())
            except Exception:
                results = []
            self.contact_list.clear_widgets()
            for c in results:
                self.contact_list.add_widget(self._make_row(c))
        elif text == "":
            Clock.schedule_once(lambda dt: self.load_list(), 0)

    def do_search(self, *a):
        t = self.search_input.text.strip()
        if t:
            self.load_list(search_db(t))

    def clear_search(self, *a):
        self.search_input.text = ""
        Clock.schedule_once(lambda dt: self.load_list(), 0)

    def add_new(self, *a):
        scr = self.manager.get_screen("add")
        scr.editing_id = None
        scr.clear_form()
        self.manager.current = "add"

    def edit_sel(self, *a):
        if not self.selected_id:
            return
        scr = self.manager.get_screen("add")
        scr.editing_id = self.selected_id
        self.manager.current = "add"

    def delete_sel(self, *a):
        if not self.selected_id:
            return
        try:
            delete_contact(self.selected_id)
        except Exception:
            pass
        self.selected_id = None
        Clock.schedule_once(lambda dt: self.load_list(), 0)

    def _get_selected_contact(self):
        if not self.selected_id:
            return None
        try:
            for c in get_all():
                if c["id"] == self.selected_id:
                    return c
        except Exception:
            pass
        return None

    def call_contact(self, *a):
        c = self._get_selected_contact()
        if c:
            call_phone((c.get("phone") or "").strip())

    def open_wa(self, *a):
        c = self._get_selected_contact()
        if c:
            phone = (c.get("phone") or "").replace("+", "").replace(" ", "")
            if phone:
                open_url("https://wa.me/" + phone)

    def export_csv(self, *a):
        try:
            path = os.path.join(BASE_DIR, "contacts_export.csv")
            contacts = get_all()
            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                f.write("name,phone,email,address,category,notes\n")
                for c in contacts:
                    f.write('"%s","%s","%s","%s","%s","%s"\n' % (
                        c.get("name") or "", c.get("phone") or "",
                        c.get("email") or "", c.get("address") or "",
                        c.get("category") or "", c.get("notes") or ""))
        except Exception:
            pass


class AddScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.editing_id = None
        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(6))

        top = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(5))
        top.add_widget(ar_btn("رجوع", (0.45, 0.45, 0.45, 1), self.go_back, 0.25))
        ttl = ar_label("بيانات جهة الاتصال", size=dp(17), bold=True, halign="center")
        top.add_widget(ttl)
        root.add_widget(top)

        inner = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        inner.bind(minimum_height=inner.setter("height"))

        self.name_in = ar_input("اسم المورد / التاجر", dp(46))
        inner.add_widget(self.name_in)

        code_box = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(5))
        code_values = [c[0] + " " + c[1] for c in COUNTRY_CODES]
        self.code_spinner = Spinner(text="+967 اليمن", values=code_values,
                                    font_name=AR, font_size=dp(13),
                                    background_color=(0.10, 0.45, 0.91, 1))
        code_box.add_widget(self.code_spinner)
        inner.add_widget(code_box)

        self.phone_in = ar_input("رقم الهاتف (بدون مفتاح الدولة)", dp(46))
        inner.add_widget(self.phone_in)

        self.email_in = ar_input("البريد الإلكتروني (اختياري)", dp(46))
        inner.add_widget(self.email_in)

        self.address_in = ar_input("العنوان / المدينة", dp(46))
        inner.add_widget(self.address_in)

        self.category_in = ar_input("التصنيف (مثال: إلكترونيات)", dp(46))
        inner.add_widget(self.category_in)

        self.notes_in = ar_input("ملاحظات (اختياري)", dp(46))
        inner.add_widget(self.notes_in)

        save_btn = Button(text="حفظ", font_name=AR, font_size=dp(18), bold=True,
                          size_hint_y=None, height=dp(56),
                          background_color=(0.10, 0.45, 0.91, 1))
        save_btn.bind(on_press=self.save_it)
        inner.add_widget(save_btn)

        sv = ScrollView(bar_width=dp(4))
        sv.add_widget(inner)
        root.add_widget(sv)
        self.add_widget(root)

    def go_back(self, *a):
        self.manager.current = "main"

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
        code = "+967"
        try:
            parts = self.code_spinner.text.split(" ", 1)
            if parts:
                code = parts[0].strip()
        except Exception:
            pass
        phone = self.phone_in.text.strip().replace(" ", "").replace("-", "")
        full_phone = (code + phone) if phone else ""
        email = self.email_in.text.strip()
        address = self.address_in.text.strip()
        category = self.category_in.text.strip()
        notes = self.notes_in.text.strip()

        try:
            if self.editing_id:
                update_contact(self.editing_id, name, full_phone, email, address, category, notes)
            else:
                add_contact(name, full_phone, email, address, category, notes)
        except Exception:
            pass
        self.editing_id = None
        self.manager.current = "main"

    def on_enter(self):
        if self.editing_id:
            try:
                for c in get_all():
                    if c["id"] == self.editing_id:
                        self.name_in.text = c.get("name") or ""
                        self.email_in.text = c.get("email") or ""
                        self.address_in.text = c.get("address") or ""
                        self.category_in.text = c.get("category") or ""
                        self.notes_in.text = c.get("notes") or ""
                        phone = c.get("phone") or ""
                        matched = False
                        for code, cname in COUNTRY_CODES:
                            if phone.startswith(code):
                                self.code_spinner.text = code + " " + cname
                                self.phone_in.text = phone[len(code):]
                                matched = True
                                break
                        if not matched:
                            self.phone_in.text = phone
                        break
            except Exception:
                pass


class FTPScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(6))

        top = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(5))
        top.add_widget(ar_btn("رجوع", (0.45, 0.45, 0.45, 1), self.go_back, 0.25))
        ttl = ar_label("النسخ الاحتياطي FTP", size=dp(17), bold=True, halign="center")
        top.add_widget(ttl)
        root.add_widget(top)

        cfg = load_config()
        self.host_in = ar_input("عنوان الخادم Host", dp(44))
        self.host_in.text = cfg.get("host", "")
        root.add_widget(self.host_in)

        self.port_in = ar_input("المنفذ Port (افتراضي 21)", dp(44))
        self.port_in.text = str(cfg.get("port", "21"))
        root.add_widget(self.port_in)

        self.user_in = ar_input("اسم المستخدم", dp(44))
        self.user_in.text = cfg.get("username", "")
        root.add_widget(self.user_in)

        self.pass_in = ar_input("كلمة المرور", dp(44))
        self.pass_in.password = True
        self.pass_in.text = cfg.get("password", "")
        root.add_widget(self.pass_in)

        self.dir_in = ar_input("المجلد البعيد (مثال: /backup)", dp(44))
        self.dir_in.text = cfg.get("remote_dir", "/")
        root.add_widget(self.dir_in)

        btns = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(4))
        btns.add_widget(ar_btn("اختبار", (0.45, 0.45, 0.45, 1), self.test_conn, 0.25))
        btns.add_widget(ar_btn("نسخ احتياطي", (0.10, 0.45, 0.91, 1), self.do_backup, 0.25))
        btns.add_widget(ar_btn("استعادة", (0.85, 0.19, 0.15, 1), self.do_restore, 0.25))
        btns.add_widget(ar_btn("حفظ", (0.0, 0.55, 0.15, 1), self.save_cfg, 0.25))
        root.add_widget(btns)

        self.status = ar_label("", size=dp(12), color=(0.25, 0.25, 0.25, 1), halign="center")
        self.status.size_hint_y = None
        self.status.height = dp(36)
        root.add_widget(self.status)

        self.add_widget(root)

    def go_back(self, *a):
        self.manager.current = "main"

    def _cfg(self):
        port = "21"
        try:
            pv = self.port_in.text.strip()
            if pv:
                int(pv)
                port = pv
        except Exception:
            pass
        return {
            "host": self.host_in.text.strip(),
            "port": port,
            "username": self.user_in.text.strip(),
            "password": self.pass_in.text.strip(),
            "remote_dir": self.dir_in.text.strip() or "/",
        }

    def save_cfg(self, *a):
        save_config(self._cfg())
        self.status.text = "تم حفظ الإعدادات"

    def test_conn(self, *a):
        cfg = self._cfg()
        if not cfg["host"]:
            self.status.text = "أدخل عنوان الخادم أولاً"
            return
        try:
            ftp = ftplib.FTP()
            ftp.connect(cfg["host"], int(cfg["port"]), timeout=15)
            ftp.login(cfg["username"], cfg["password"])
            ftp.quit()
            self.status.text = "تم الاتصال بنجاح"
        except Exception as e:
            self.status.text = "خطأ: " + str(e)[:80]

    def do_backup(self, *a):
        cfg = self._cfg()
        if not cfg["host"]:
            self.status.text = "أدخل عنوان الخادم أولاً"
            return
        try:
            ftp = ftplib.FTP()
            ftp.connect(cfg["host"], int(cfg["port"]), timeout=15)
            ftp.login(cfg["username"], cfg["password"])
            try:
                ftp.cwd(cfg["remote_dir"])
            except Exception:
                try:
                    ftp.mkd(cfg["remote_dir"])
                    ftp.cwd(cfg["remote_dir"])
                except Exception:
                    pass
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            fn = "contacts_backup_" + ts + ".db"
            with open(DB_FILE, "rb") as f:
                ftp.storbinary("STOR " + fn, f)
            ftp.quit()
            self.status.text = "تم النسخ الاحتياطي بنجاح"
        except Exception as e:
            self.status.text = "خطأ: " + str(e)[:80]

    def do_restore(self, *a):
        cfg = self._cfg()
        if not cfg["host"]:
            self.status.text = "أدخل عنوان الخادم أولاً"
            return
        try:
            ftp = ftplib.FTP()
            ftp.connect(cfg["host"], int(cfg["port"]), timeout=15)
            ftp.login(cfg["username"], cfg["password"])
            try:
                ftp.cwd(cfg["remote_dir"])
            except Exception:
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
                try:
                    ftp.quit()
                except Exception:
                    pass
                return
            latest = sorted(backups)[-1]
            temp = DB_FILE + ".tmp"
            with open(temp, "wb") as f:
                ftp.retrbinary("RETR " + latest, f.write)
            try:
                ftp.quit()
            except Exception:
                pass
            import shutil
            shutil.copy2(temp, DB_FILE)
            try:
                os.remove(temp)
            except Exception:
                pass
            self.status.text = "تمت الاستعادة بنجاح"
        except Exception as e:
            self.status.text = "خطأ: " + str(e)[:80]


def _save_crash(err_text):
    try:
        with open(os.path.join(BASE_DIR, "crash_log.txt"), "w", encoding="utf-8") as f:
            f.write(err_text)
    except Exception:
        pass


class ContactManagerApp(App):
    def build(self):
        self.title = "مدير جهات الاتصال"
        try:
            init_db()
        except Exception:
            pass
        try:
            sm = ScreenManager()
            sm.add_widget(MainScreen(name="main"))
            sm.add_widget(AddScreen(name="add"))
            sm.add_widget(FTPScreen(name="ftp"))
        except Exception:
            import traceback
            err = traceback.format_exc()
            _save_crash(err)
            from kivy.uix.label import Label as _L
            from kivy.uix.scrollview import ScrollView as _SV
            box = BoxLayout()
            sv = _SV()
            lbl = _L(text=err[-2000:], color=(1, 0.2, 0.2, 1), font_name=AR, font_size="12sp")
            sv.add_widget(lbl)
            box.add_widget(sv)
            return box

        Window.bind(on_keyboard=self.on_key)
        self.sm = sm
        return sm

    def on_key(self, window, key, *args):
        if key == 27:
            if self.sm.current != "main":
                self.sm.current = "main"
                return True
        return False


if __name__ == "__main__":
    try:
        ContactManagerApp().run()
    except Exception:
        import traceback
        from kivy.base import runTouchApp
        from kivy.uix.label import Label as _L
        err = traceback.format_exc()
        _save_crash(err)
        runTouchApp(_L(text=err[-2000:], color=(1, 0.2, 0.2, 1), font_name=AR, font_size="12sp"))
