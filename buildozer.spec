[app]
title = Contacts Manager
package.name = contactsmanager
package.domain = org.contactsmanager
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0.0
requirements = python3,kivy
orientation = portrait
fullscreen = 0
android.permissions = INTERNET
android.api = 31
android.minapi = 21
android.ndk = 25
android.arch = arm64-v8a
android.release_artifact = apk
android.allow_backup = 1

[buildozer]
log_level = 2
warn_on_root = 0
