# Sales Note Android

Thin Android WebView wrapper for the production Sales Note CRM.

The APK loads:

```text
https://sales-note-frontend-production.up.railway.app/
```

Build:

```powershell
.\gradlew.bat :app:assembleDebug
```

The debug APK is generated at:

```text
app/build/outputs/apk/debug/app-debug.apk
```

This project does not change Django, React, API, database, or Railway runtime behavior.
