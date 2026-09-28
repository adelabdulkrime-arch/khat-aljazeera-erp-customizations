'use strict';

const { app, BrowserWindow, shell, Menu, dialog, ipcMain, session } = require('electron');
const path = require('path');
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
        { label: 'تحديث الصفحة', accelerator: 'F5', click: () => loadServer() },
        { label: 'الصفحة الرئيسية', accelerator: 'Alt+Home', click: () => loadServer() },
        { type: 'separator' },
        { label: 'إعدادات الاتصال…', click: () => promptForServer() },
        { type: 'separator' },
        { label: 'خروج', role: 'quit' },
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
