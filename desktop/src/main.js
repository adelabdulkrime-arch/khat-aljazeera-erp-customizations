'use strict';

const { app, BrowserWindow, shell, Menu, dialog, ipcMain, session } = require('electron');
const path = require('path');
const fs = require('fs');
const { readServer, writeServer, normalizeServer } = require('./config');

// مثيل واحد فقط — الضغط على الأيقونة مرة ثانية يُظهر النافذة المفتوحة
if (!app.requestSingleInstanceLock()) {
  app.quit();
  return;
}

let mainWindow = null;
let serverOrigin = null;

/** هل هذا العنوان داخل السيرفر الخاص بنا؟ */
function isInternal(targetUrl) {
  try {
    return new URL(targetUrl).origin === serverOrigin;
  } catch {
    return false;
  }
}

// ── التنقّل ────────────────────────────────────────────────────────────────
// نافذة Electron بلا أزرار المتصفح، فالمستخدم يفقد الرجوع والأمام تماماً —
// وهو ما يتوقعه أي شخص اعتاد الويب. هذه الدوال تُربط بثلاثة مداخل: قائمة
// «تنقّل»، واختصارات لوحة المفاتيح (Alt+سهم)، وأزرار الفأرة الجانبية.
//
// في Electron 30+ تنتقل واجهة التاريخ إلى webContents.navigationHistory؛
// نستخدمها حين تتوفر ونعود للواجهة القديمة إن لم تكن — فالملف يعمل على
// الإصدارين دون تعديل.
function nav() {
  return mainWindow && mainWindow.webContents;
}

function canGoBack() {
  const wc = nav();
  if (!wc) return false;
  return wc.navigationHistory ? wc.navigationHistory.canGoBack() : wc.canGoBack();
}

function canGoForward() {
  const wc = nav();
  if (!wc) return false;
  return wc.navigationHistory ? wc.navigationHistory.canGoForward() : wc.canGoForward();
}

function goBack() {
  const wc = nav();
  if (!wc || !canGoBack()) return;
  wc.navigationHistory ? wc.navigationHistory.goBack() : wc.goBack();
}

function goForward() {
  const wc = nav();
  if (!wc || !canGoForward()) return;
  wc.navigationHistory ? wc.navigationHistory.goForward() : wc.goForward();
}

/** يُبلّغ الصفحة بحالة التاريخ لتعطيل الزر الذي لا وجهة له. */
function syncNavState() {
  const wc = nav();
  if (!wc || wc.isDestroyed()) return;
  wc.executeJavaScript(
    `window.__khatNavState && window.__khatNavState(${canGoBack()}, ${canGoForward()})`,
    true
  ).catch(() => {});
}

function loadServer() {
  if (!mainWindow) return;
  mainWindow.loadURL(`${serverOrigin}/desk/home`);
}

function showOffline() {
  if (!mainWindow) return;
  mainWindow.loadFile(path.join(__dirname, 'offline.html'), {
    query: { server: serverOrigin },
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    show: false,
    backgroundColor: '#1a2b4a',
    icon: path.join(__dirname, '..', 'build', 'icon.ico'),
    title: 'خط الجزيرة',
    // الشريط مخفي لا معطّل: Alt يُظهره عند الحاجة، ولا يأكل مساحة رأسية من
    // شاشة يُفترض أن تعرض جداول. أزرار التنقّل الفعلية تُحقن داخل الصفحة
    // (nav_overlay.js) فتكون مرئية دائماً دون شريط قوائم دائم.
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      spellcheck: false,
    },
  });

  mainWindow.once('ready-to-show', () => mainWindow.show());
  mainWindow.on('closed', () => { mainWindow = null; });

  // أزرار الفأرة الجانبية (رجوع/أمام) — يتوقعها المستخدم من أي متصفح، ولا
  // تعمل في نافذة Electron ما لم تُربط يدوياً.
  mainWindow.on('app-command', (event, cmd) => {
    if (cmd === 'browser-backward') goBack();
    else if (cmd === 'browser-forward') goForward();
  });

  // اختصارات المتصفح المعتادة. قائمة «تنقّل» تغطي Alt+سهم، وهذه تضيف
  // Backspace وAlt+سهم بالاتجاه اللاتيني لمن اعتاده — مع تجاهلها أثناء
  // الكتابة في حقل، وإلا حذف المستخدم حرفاً فخرج من الصفحة.
  mainWindow.webContents.on('before-input-event', (event, input) => {
    if (input.type !== 'keyDown') return;
    const back =
      (input.key === 'Backspace' && !input.control && !input.alt && !input.meta) ||
      (input.alt && (input.key === 'ArrowLeft' || input.key === 'ArrowRight'));
    if (!back) return;

    // لا نتدخّل إن كان المؤشر داخل حقل إدخال.
    mainWindow.webContents
      .executeJavaScript(
        `(() => { const e = document.activeElement;
            return !!e && (e.tagName === 'INPUT' || e.tagName === 'TEXTAREA' || e.isContentEditable); })()`,
        true
      )
      .then((typing) => {
        if (typing) return;
        if (input.key === 'Backspace' || input.key === 'ArrowRight') goBack();
        else goForward();
      })
      .catch(() => {});
  });

  // عنوان النافذة يبقى ثابتاً بدل ما يتغيّر مع كل صفحة
  mainWindow.on('page-title-updated', (event) => event.preventDefault());

  // الروابط الخارجية تُفتح بالمتصفح (واتساب، مواقع خارجية)، والداخلية داخل التطبيق
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (isInternal(url)) {
      return {
        action: 'allow',
        overrideBrowserWindowOptions: {
          backgroundColor: '#1a2b4a',
          autoHideMenuBar: true,
          webPreferences: { contextIsolation: true, nodeIntegration: false, sandbox: true },
        },
      };
    }
    if (/^https?:|^mailto:|^tel:/i.test(url)) shell.openExternal(url);
    return { action: 'deny' };
  });

  // منع التطبيق من الإبحار خارج السيرفر — يُفتح بالمتصفح بدلاً من ذلك
  mainWindow.webContents.on('will-navigate', (event, url) => {
    if (url.startsWith('file://')) return;   // صفحة «لا يوجد اتصال» المحلية
    if (isInternal(url)) return;
    event.preventDefault();
    if (/^https?:/i.test(url)) shell.openExternal(url);
  });

  // حقن أزرار التنقّل في كل صفحة. القائمة والاختصارات موجودة، لكن القائمة
  // مخفية خلف Alt والاختصارات لا يعرفها من يفتح التطبيق أول مرة — فيبقى بلا
  // وسيلة ظاهرة للرجوع، وهي أول ما يبحث عنه.
  const NAV_OVERLAY = fs.readFileSync(path.join(__dirname, 'nav_overlay.js'), 'utf8');

  // يُحقن مبكراً (dom-ready) ومرة أخرى بعد اكتمال التحميل: صفحة النظام تبني
  // واجهتها بجافاسكربت بعد did-finish-load، وقد تمسح ما أُضيف قبلها. الملف
  // نفسه يتجاهل الحقن المكرر (علامة __khatNavReady) ويعيد بناء الشريط إن
  // اختفى، فالتكرار آمن.
  const injectNav = () => {
    const wc = nav();
    if (!wc || wc.isDestroyed()) return;
    wc.executeJavaScript(NAV_OVERLAY, true).then(syncNavState).catch(() => {});
  };

  mainWindow.webContents.on('dom-ready', injectNav);
  mainWindow.webContents.on('did-finish-load', () => {
    injectNav();
    // النظام يُكمل بناء واجهته بعد التحميل بقليل؛ حقنة متأخرة واحدة تكفي
    // لتثبيت الشريط دون استطلاع دوري.
    setTimeout(injectNav, 1500);
  });

  // تحديث حالة الزرّين بعد كل تنقّل، ليُعطَّل ما لا تاريخ له.
  ['did-navigate', 'did-navigate-in-page'].forEach((evt) => {
    mainWindow.webContents.on(evt, () => syncNavState());
  });

  // الصفحة معزولة عن Node، فتُبلّغ عن النقر بتغيير عنوان الصفحة إلى وسم
  // متفق عليه — حدث واحد يصل مباشرة، بدل استطلاع دوري كان يراكم مستمعين على
  // webContents حتى حذّر Electron من تسرّب (MaxListenersExceededWarning).
  // يُطلق على webContents لا على النافذة: المستمع على النافذة أعلاه يمنع
  // تغيير العنوان المعروض (preventDefault) لكن الحدث يصل هنا على أي حال.
  mainWindow.webContents.on('page-title-updated', (_event, title) => {
    if (title === '__khat_nav_back__') goBack();
    else if (title === '__khat_nav_forward__') goForward();
  });

  // فشل تحميل الصفحة الرئيسية ⇒ اعرض شاشة «لا يوجد اتصال»
  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription, validatedURL, isMainFrame) => {
    // -3 = ABORTED، يحدث طبيعياً عند إلغاء تنقّل، وليس خطأ حقيقي
    if (!isMainFrame || errorCode === -3) return;
    if (validatedURL && validatedURL.startsWith('file://')) return;
    showOffline();
  });

  loadServer();
}

function promptForServer() {
  if (!mainWindow) return;
  mainWindow.loadFile(path.join(__dirname, 'settings.html'), {
    query: { server: serverOrigin },
  });
}

function buildMenu() {
  const template = [
    {
      label: 'ملف',
      submenu: [
        // تحديث الصفحة الحالية، لا العودة للرئيسية: كان F5 يُحمّل /desk/home
        // فيفقد المستخدم مكانه كلما أراد تحديث قائمة.
        {
          label: 'تحديث الصفحة',
          accelerator: 'F5',
          click: () => { const wc = nav(); if (wc) wc.reload(); },
        },
        { label: 'الصفحة الرئيسية', accelerator: 'Alt+Home', click: () => loadServer() },
        { type: 'separator' },
        { label: 'إعدادات الاتصال…', click: () => promptForServer() },
        { type: 'separator' },
        { label: 'خروج', role: 'quit' },
      ],
    },
    {
      // قائمة مستقلة للتنقّل: المستخدم يبحث عن الرجوع والأمام أولاً، فوضعها
      // داخل «عرض» أو «ملف» يُخفيها عمّن يحتاجها.
      label: 'تنقّل',
      submenu: [
        {
          label: 'رجوع',
          accelerator: 'Alt+Right',   // في RTL السهم الأيمن هو اتجاه الرجوع
          click: () => goBack(),
        },
        {
          label: 'أمام',
          accelerator: 'Alt+Left',
          click: () => goForward(),
        },
        { type: 'separator' },
        {
          label: 'الصفحة الرئيسية',
          accelerator: 'Alt+Home',
          click: () => loadServer(),
        },
      ],
    },
    {
      label: 'تحرير',
      submenu: [
        { label: 'تراجع', role: 'undo' },
        { label: 'إعادة', role: 'redo' },
        { type: 'separator' },
        { label: 'قص', role: 'cut' },
        { label: 'نسخ', role: 'copy' },
        { label: 'لصق', role: 'paste' },
        { label: 'تحديد الكل', role: 'selectAll' },
      ],
    },
    {
      label: 'عرض',
      submenu: [
        { label: 'تكبير', role: 'zoomIn', accelerator: 'CommandOrControl+Plus' },
        { label: 'تصغير', role: 'zoomOut' },
        { label: 'الحجم الطبيعي', role: 'resetZoom' },
        { type: 'separator' },
        { label: 'ملء الشاشة', role: 'togglefullscreen' },
        { label: 'أدوات المطوّر', role: 'toggleDevTools' },
      ],
    },
    {
      label: 'مساعدة',
      submenu: [
        {
          label: 'عن التطبيق',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'عن التطبيق',
              message: 'خط الجزيرة — إدارة الورشة',
              detail: `الإصدار ${app.getVersion()}\nالسيرفر: ${serverOrigin}\nElectron ${process.versions.electron}`,
              buttons: ['حسناً'],
            });
          },
        },
      ],
    },
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

app.on('second-instance', () => {
  if (!mainWindow) return;
  if (mainWindow.isMinimized()) mainWindow.restore();
  mainWindow.focus();
});

app.whenReady().then(() => {
  serverOrigin = readServer();

  // طلبات تنزيل PDF (الفواتير) تُحفظ بمجلد التنزيلات مع إظهار شريط الحفظ
  session.defaultSession.on('will-download', () => { /* سلوك Electron الافتراضي كافٍ */ });

  // أصول النظام (js/css/صور) تُطلب من الشبكة لا من الكاش.
  //
  // التطبيق كان يحتفظ بنسخ قديمة من desk.js والأيقونات بعد تحديث السيرفر،
  // فيظهر الشعار القديم واسم "ERPNext" في الشريط الجانبي بينما المتصفح على
  // الجهاز نفسه يعرض الصحيح — فرقٌ أربك التشخيص مرتين.
  //
  // مقصور على مسار /assets: صفحات النظام وبياناته تمرّ بسلوك الكاش المعتاد،
  // فلا يتباطأ التصفّح. والكوكيز والجلسة لا تتأثر، فيبقى الدخول محفوظاً.
  session.defaultSession.webRequest.onBeforeSendHeaders(
    { urls: ['*://*/assets/*'] },
    (details, callback) => {
      callback({
        requestHeaders: {
          ...details.requestHeaders,
          'Cache-Control': 'no-cache',
          Pragma: 'no-cache',
        },
      });
    }
  );

  ipcMain.handle('config:get-server', () => serverOrigin);

  ipcMain.handle('config:set-server', (_event, value) => {
    const saved = writeServer(value);
    if (!saved) return { ok: false, error: 'العنوان غير صالح' };
    serverOrigin = saved;
    loadServer();
    return { ok: true, server: saved };
  });

  ipcMain.handle('app:retry', () => { loadServer(); });
  ipcMain.handle('app:open-settings', () => { promptForServer(); });

  buildMenu();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
