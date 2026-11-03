// Génère build/icon.png (256 px) et build/icon.ico à partir de build/icon.svg : npm run icon
const { app, BrowserWindow } = require("electron");
const fs = require("fs");
const path = require("path");

app.disableHardwareAcceleration();
app.whenReady().then(async () => {
  const dir = path.join(__dirname, "build");
  const svg = fs.readFileSync(path.join(dir, "icon.svg"), "utf8");
  const win = new BrowserWindow({ width: 256, height: 256, show: false, frame: false, transparent: true,
    webPreferences: { offscreen: true } });
  const html = "<body style='margin:0;background:transparent'>" + svg.replace(/width="\d+" height="\d+"/, 'width="256" height="256"') + "</body>";
  await win.loadURL("data:text/html;charset=utf-8," + encodeURIComponent(html));
  await new Promise((r) => setTimeout(r, 300));
  const png = (await win.webContents.capturePage({ x: 0, y: 0, width: 256, height: 256 })).resize({ width: 256, height: 256 }).toPNG();
  fs.writeFileSync(path.join(dir, "icon.png"), png);

  // ICO d'une seule image 256 px au format PNG (accepté par Windows Vista et plus).
  const head = Buffer.alloc(22);
  head.writeUInt16LE(0, 0); head.writeUInt16LE(1, 2); head.writeUInt16LE(1, 4);
  head.writeUInt8(0, 6); head.writeUInt8(0, 7); head.writeUInt8(0, 8); head.writeUInt8(0, 9);
  head.writeUInt16LE(1, 10); head.writeUInt16LE(32, 12); head.writeUInt32LE(png.length, 14); head.writeUInt32LE(22, 18);
  fs.writeFileSync(path.join(dir, "icon.ico"), Buffer.concat([head, png]));
  app.quit();
});
