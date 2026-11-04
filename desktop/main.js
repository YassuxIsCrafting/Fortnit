// Île Éclair pour Windows : une fenêtre plein écran qui charge le jeu en ligne.
// Le jeu n'est pas embarqué, donc chaque mise à jour du site arrive toute seule au lancement.
const { app, BrowserWindow, shell, Menu } = require("electron");
const path = require("path");

const HOST = "fortnit-jeu.yasser-mobiarchitects.workers.dev";
const GAME_URL = "https://" + HOST + "/";

// Une seule fenêtre du jeu à la fois : relancer l'exe remet la fenêtre existante devant.
if (!app.requestSingleInstanceLock()) app.quit();

// Musique du lobby sans attendre un clic.
app.commandLine.appendSwitch("autoplay-policy", "no-user-gesture-required");

let win;

function create() {
  Menu.setApplicationMenu(null);
  win = new BrowserWindow({
    width: 1600,
    height: 900,
    backgroundColor: "#14123a",
    title: "Île Éclair",
    icon: path.join(__dirname, "build", "icon.png"),
    autoHideMenuBar: true,
    show: false,
    webPreferences: { contextIsolation: true, sandbox: true, backgroundThrottling: false },
  });
  win.once("ready-to-show", () => { win.maximize(); win.setFullScreen(true); win.show(); });

  const wc = win.webContents;
  // Le jeu reste dans la fenêtre, les autres liens s'ouvrent dans le navigateur.
  wc.setWindowOpenHandler(({ url }) => { shell.openExternal(url); return { action: "deny" }; });
  wc.on("will-navigate", (e, url) => {
    if (url.startsWith("file:")) return;
    if (new URL(url).host !== HOST) { e.preventDefault(); shell.openExternal(url); }
  });
  wc.on("did-fail-load", (e, code, desc, url, isMain) => {
    if (isMain && code !== -3) win.loadFile(path.join(__dirname, "offline.html"), { query: { u: GAME_URL } });
  });
  // F11 plein écran, F5 recharger, Ctrl+Maj+I outils de développement.
  wc.on("before-input-event", (e, input) => {
    if (input.type !== "keyDown") return;
    if (input.key === "F11") { win.setFullScreen(!win.isFullScreen()); e.preventDefault(); }
    else if (input.key === "F5") { wc.reloadIgnoringCache(); e.preventDefault(); }
    else if (input.control && input.shift && input.key.toLowerCase() === "i") wc.toggleDevTools();
  });

  win.loadURL(GAME_URL);
}

app.on("second-instance", () => { if (win) { if (win.isMinimized()) win.restore(); win.focus(); } });
app.whenReady().then(create);
app.on("window-all-closed", () => app.quit());
