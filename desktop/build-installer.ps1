# يبني setup.exe — شغّله من PowerShell "كمسؤول" (Run as Administrator).
#
# السبب: electron-builder يفك ضغط أدوات التوقيع، وداخلها ارتباطات رمزية
# (symlinks) خاصة بنظام macOS. ويندوز يمنع إنشاء الارتباطات الرمزية إلا
# بصلاحية مدير أو بتفعيل "وضع المطوّر"، فيفشل البناء بلا صلاحية. الارتباطات
# نفسها لا تخصّ ويندوز إطلاقاً، لكن أداة البناء تتوقف عند الخطأ.

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

# بانر فوري: إن لم تظهر هذه السطور فالسكربت لم يبدأ أصلاً (غالباً منعته سياسة
# التنفيذ RemoteSigned، وهي تمنع بصمت). الحل: شغّل build-installer.bat بدلاً منه.
Write-Host ""
Write-Host "  بناء منصّب خط الجزيرة" -ForegroundColor Cyan
Write-Host "  ---------------------" -ForegroundColor Cyan

$isAdmin = ([Security.Principal.WindowsPrincipal] `
    [Security.Principal.WindowsIdentity]::GetCurrent()
).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host ""
    Write-Host "  لازم تشغّل هذا الملف بصلاحية مدير." -ForegroundColor Yellow
    Write-Host "  الأسهل: كليك يمين على build-installer.bat ← Run as administrator"
    Write-Host ""
    exit 1
}

# تفعيل وضع المطوّر يمنح صلاحية إنشاء الارتباطات الرمزية بشكل دائم،
# فلا تحتاج صلاحية مدير في المرات القادمة.
$key = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock'
if (-not (Test-Path $key)) { New-Item -Path $key -Force | Out-Null }
New-ItemProperty -Path $key -Name AllowDevelopmentWithoutDevLicense `
    -Value 1 -PropertyType DWord -Force | Out-Null
Write-Host "[1/3] وضع المطوّر مفعّل." -ForegroundColor Green

# بعض المحرّرات (VS Code مثلاً) تضبط هذا المتغيّر، وهو يجعل Electron يعمل
# كـNode عادي بلا واجهة — فيفشل التشغيل والبناء برسالة غامضة عن `app`.
Remove-Item Env:ELECTRON_RUN_AS_NODE -ErrorAction SilentlyContinue

if (-not (Test-Path 'node_modules')) {
    Write-Host "[2/3] تثبيت الحزم..." -ForegroundColor Cyan
    npm install --no-audit --no-fund
} else {
    Write-Host "[2/3] الحزم مثبّتة." -ForegroundColor Green
}

node build-icon.js

Write-Host "[3/3] بناء المنصّب..." -ForegroundColor Cyan
npx electron-builder --win --x64

$setup = Join-Path $PSScriptRoot 'release\setup.exe'
if (Test-Path $setup) {
    $mb = [math]::Round((Get-Item $setup).Length / 1MB, 1)
    Write-Host ""
    Write-Host "  تم بنجاح: $setup  ($mb ميجابايت)" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "  لم يُنتج المنصّب — راجع الرسائل بالأعلى." -ForegroundColor Red
    exit 1
}
