#!/usr/bin/python3
# Puts the Start menu in place of the raspberry menu, or puts the raspberry menu back with --remove.
#  - taskbar: swaps the "smenu" widget in wf-panel-pi for a pi-start launcher
#  - keyboard: binds the Super key to pi-start (labwc), saving any old Super binding
#  - autostart: preloads pi-start at login so it opens instantly
import os
import re
import sys
import time
import shutil
import subprocess
import xml.dom.minidom


from gi.repository import GLib

HOME = os.path.expanduser("~")
STATE = os.path.join(HOME, ".config", "pi-start")
PANEL_INI = os.path.join(HOME, ".config", "wf-panel-pi", "wf-panel-pi.ini")
PANEL_SYS = "/etc/xdg/wf-panel-pi/wf-panel-pi.ini"
DEF_LEFT = "smenu spacing0 spacing4 launchers spacing8 window-list"
RC = os.path.join(HOME, ".config", "labwc", "rc.xml")
RC_SYS = "/etc/xdg/labwc/rc.xml"
AUTOSTART = os.path.join(HOME, ".config", "autostart", "pi-start.desktop")
BIND = '<keybind key="Super_L" onRelease="yes"><action name="Execute" command="pi-start" /></keybind>'
SUPER_RE = re.compile(r'[ \t]*<keybind\s+key="Super_L"[^>]*?(?:/>|>.*?</keybind>)[ \t]*\n?', re.S)


def panel_get(key, default):
    for path in (PANEL_INI, PANEL_SYS):
        kf = GLib.KeyFile()
        try:
            kf.load_from_file(path, GLib.KeyFileFlags.KEEP_COMMENTS)
            return kf.get_string("panel", key)
        except GLib.Error:
            continue
    return default


def panel_set(values):
    kf = GLib.KeyFile()
    try:
        kf.load_from_file(PANEL_INI, GLib.KeyFileFlags.KEEP_COMMENTS)
    except GLib.Error:
        pass
    for k, v in values.items():
        kf.set_string("panel", k, v)
    os.makedirs(os.path.dirname(PANEL_INI), exist_ok=True)
    kf.save_to_file(PANEL_INI)


def panel(remove):
    if not shutil.which("wf-panel-pi") and not os.path.exists(PANEL_SYS) and not os.path.exists(PANEL_INI):
        print("  Taskbar: wf-panel-pi not found, skipped")
        return
    left = panel_get("widgets_left", DEF_LEFT).split()
    lch = panel_get("launchers", "").split()
    if remove:
        if "smenu" not in left:
            left.insert(0, "smenu")
        lch = [x for x in lch if x != "pi-start"]
        panel_set({"widgets_left": " ".join(left), "launchers": " ".join(lch)})
        print("  Taskbar: raspberry menu button put back")
        return
    if os.path.exists(PANEL_INI):
        shutil.copy(PANEL_INI, os.path.join(STATE, f"wf-panel-pi.ini.bak-{int(time.time())}"))
    left = [x for x in left if x != "smenu"]
    if "launchers" not in left:
        left.insert(0, "launchers")
    lch = ["pi-start"] + [x for x in lch if x != "pi-start"]
    panel_set({"widgets_left": " ".join(left), "launchers": " ".join(lch)})
    print("  Taskbar: raspberry menu button replaced with Start")


def keyboard(remove):
    if not (shutil.which("labwc") or os.path.exists(os.path.dirname(RC))):
        print("  Super key: labwc not found, skipped")
        return
    saved = os.path.join(STATE, "superkey-orig.xml")
    if not os.path.exists(RC):
        if remove:
            return
        os.makedirs(os.path.dirname(RC), exist_ok=True)
        if os.path.exists(RC_SYS):
            shutil.copy(RC_SYS, RC)
        else:
            with open(RC, "w") as f:
                f.write('<?xml version="1.0"?>\n<labwc_config>\n  <keyboard>\n    <default />\n  </keyboard>\n</labwc_config>\n')
    with open(RC) as f:
        txt = f.read()
    if remove:
        new = txt.replace(BIND, "")
        old = ""
        if os.path.exists(saved):
            with open(saved) as f:
                old = f.read().strip()
            os.remove(saved)
        if old:
            new = re.sub(r"(<keyboard\s*>(\s*<default\s*/>)?)", lambda m: m.group(1) + "\n    " + old, new, count=1)
        new = re.sub(r"\n[ \t]*\n[ \t]*\n", "\n\n", new)
    else:
        if BIND in txt:
            print("  Super key: already opens Start")
            return
        shutil.copy(RC, os.path.join(STATE, f"rc.xml.bak-{int(time.time())}"))
        olds = [m.group(0).strip() for m in SUPER_RE.finditer(txt)]
        if olds and not os.path.exists(saved):
            with open(saved, "w") as f:
                f.write("\n    ".join(olds))
        new = SUPER_RE.sub("", txt)
        if re.search(r"<keyboard\s*>\s*<default\s*/>", new):
            new = re.sub(r"(<keyboard\s*>\s*<default\s*/>)", lambda m: m.group(1) + "\n    " + BIND, new, count=1)
        elif re.search(r"<keyboard\s*>", new):
            new = re.sub(r"(<keyboard\s*>)", lambda m: m.group(1) + "\n    " + BIND, new, count=1)
        elif re.search(r"<keyboard\s*/>", new):
            new = re.sub(r"<keyboard\s*/>", "<keyboard>\n    <default />\n    " + BIND + "\n  </keyboard>", new, count=1)
        else:
            new = new.replace("</labwc_config>", "  <keyboard>\n    <default />\n    " + BIND + "\n  </keyboard>\n</labwc_config>")
    try:
        xml.dom.minidom.parseString(new)
    except Exception as e:
        print(f"  Super key: could not change rc.xml safely ({e}); left unchanged")
        return
    with open(RC, "w") as f:
        f.write(new)
    if shutil.which("labwc") and os.environ.get("LABWC_PID"):
        subprocess.run(["labwc", "--reconfigure"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.run(["pkill", "-HUP", "-x", "labwc"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("  Super key: " + ("put back to how it was" if remove else "now opens Start"))


def autostart(remove):
    if remove:
        if os.path.exists(AUTOSTART):
            os.remove(AUTOSTART)
        return
    os.makedirs(os.path.dirname(AUTOSTART), exist_ok=True)
    with open(AUTOSTART, "w") as f:
        f.write("[Desktop Entry]\nType=Application\nName=Start menu\nExec=pi-start --background\n"
                "NoDisplay=true\nX-GNOME-Autostart-enabled=true\n")
    print("  Login: Start menu loads in the background so it opens instantly")


def main():
    remove = "--remove" in sys.argv
    os.makedirs(STATE, exist_ok=True)
    for step in (panel, keyboard, autostart):
        try:
            step(remove)
        except Exception as e:
            print(f"  {step.__name__}: {e}")


if __name__ == "__main__":
    main()
