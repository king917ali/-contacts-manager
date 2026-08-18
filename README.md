# بناء تطبيق الأندرويد (APK)

## الطريقة السهلة: GitHub Actions

### الخطوة 1: إنشاء مستودع على GitHub

1. افتح https://github.com/new
2. أنشئ مستودع جديد (مثلاً: `contacts-manager`)
3. ارفع الملفات:

```bash
cd "C:\Users\KING\Documents\برنامج جهات اتصال\android_app"
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### الخطوة 2: بناء APK تلقائياً

1. افتح المستودع على GitHub
2. اضغط على تبويب **Actions**
3. اختر **Build Android APK**
4. اضغط **Run workflow**
5. انتظر 15-20 دقيقة
6. حمّل ملف APK من **Artifacts**

### الخطوة 3: تثبيت على الهاتف

1. حمّل ملف APK من GitHub
2. فعّل **مصادر غير معروفة** في إعدادات الهاتف
3. ثبّت التطبيق

## مزامنة البيانات

- التطبيق يستخدم نفس ملف `contacts.db`
- النسخ الاحتياطي عبر FTP
- لنقل البيانات: استخدم FTP بين الكمبيوتر والهاتف

## ملاحظات

- **أول بناء** يستغرق 15-20 دقيقة
- **الAPK** يعمل بدون إنترنت
- **البيانات** تُخزّن محلياً على الهاتف
