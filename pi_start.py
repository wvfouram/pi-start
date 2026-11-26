#!/usr/bin/python3
# Start menu for Raspberry Pi, styled after the Windows 11 Start menu (dark).
import os
import sys
import re
import json
import math
import time
import shutil
import signal
import threading
import subprocess

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf, Pango, Gio, GObject  # noqa: E402,F401
import cairo  # noqa: E402

HOME = os.path.expanduser("~")
C_ACCENT = "#4CC2FF"
def hexc(h, a=1.0):
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


def _rr(cr, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    cr.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    cr.close_path()


def _line(cr, *pts):
    cr.move_to(*pts[0])
    for p in pts[1:]:
        cr.line_to(*p)
    cr.stroke()


def draw_glyph(cr, name, s, col):
    """Monochrome line icons for buttons."""
    cr.save()
    cr.scale(s / 16.0, s / 16.0)
    cr.set_source_rgba(*col)
    cr.set_line_width(1.15)
    cr.set_line_cap(cairo.LINE_CAP_ROUND)
    cr.set_line_join(cairo.LINE_JOIN_ROUND)
    pi = math.pi
    L = lambda *p: _line(cr, *p)  # noqa: E731
    if name == "back":
        L((13.5, 8), (2.5, 8))
        L((7, 3.5), (2.5, 8), (7, 12.5))
    elif name == "forward":
        L((2.5, 8), (13.5, 8))
        L((9, 3.5), (13.5, 8), (9, 12.5))
    elif name == "up":
        L((8, 13.5), (8, 2.5))
        L((3.5, 7), (8, 2.5), (12.5, 7))
    elif name == "refresh":
        cr.arc(8, 8, 5.5, -pi * 0.35, pi * 1.55)
        cr.stroke()
        L((12.9, 1.8), (12.6, 4.9), (9.6, 4.6))
    elif name == "plus":
        L((8, 2.5), (8, 13.5))
        L((2.5, 8), (13.5, 8))
    elif name == "new":
        cr.set_source_rgba(*hexc(C_ACCENT))
        cr.arc(8, 8, 6.5, 0, 2 * pi)
        cr.stroke()
        L((8, 4.8), (8, 11.2))
        L((4.8, 8), (11.2, 8))
    elif name == "cut":
        cr.arc(4.5, 12, 2, 0, 2 * pi)
        cr.stroke()
        cr.arc(11.5, 12, 2, 0, 2 * pi)
        cr.stroke()
        L((5.8, 10.5), (11, 1.8))
        L((10.2, 10.5), (5, 1.8))
    elif name == "copy":
        _rr(cr, 5, 1.5, 9, 10.5, 1.5)
        cr.stroke()
        cr.move_to(3, 4.5)
        cr.line_to(3, 13)
        cr.arc_negative(4.5, 13, 1.5, pi, pi / 2)
        cr.line_to(11, 14.5)
        cr.stroke()
    elif name == "paste":
        _rr(cr, 2.5, 3, 11, 11.5, 1.5)
        cr.stroke()
        _rr(cr, 5.5, 1.5, 5, 3, 1)
        cr.stroke()
        L((5.5, 8), (10.5, 8))
        L((5.5, 11), (9, 11))
    elif name == "rename":
        _rr(cr, 1.5, 4.5, 13, 7, 1.3)
        cr.stroke()
        L((4, 8), (8, 8))
        L((10.5, 2.5), (10.5, 13.5))
        L((9, 2.5), (12, 2.5))
        L((9, 13.5), (12, 13.5))
    elif name == "delete" or name == "trash":
        L((2.5, 4), (13.5, 4))
        L((6, 4), (6.5, 2), (9.5, 2), (10, 4))
        cr.move_to(4, 4)
        cr.line_to(4.8, 14)
        cr.line_to(11.2, 14)
        cr.line_to(12, 4)
        cr.stroke()
        L((6.8, 6.8), (7, 11.5))
        L((9.2, 6.8), (9, 11.5))
    elif name == "sort":
        L((4.5, 2.5), (4.5, 13.5))
        L((2, 5), (4.5, 2.5), (7, 5))
        L((11.5, 2.5), (11.5, 13.5))
        L((9, 11), (11.5, 13.5), (14, 11))
    elif name == "view":
        for y in (3, 8, 13):
            L((2, y), (14, y))
    elif name == "more":
        for x in (3, 8, 13):
            cr.arc(x, 8, 1.1, 0, 2 * pi)
            cr.fill()
    elif name == "chevdown":
        L((4, 6), (8, 10), (12, 6))
    elif name == "chevright":
        L((6, 4), (10, 8), (6, 12))
    elif name == "close":
        L((3.5, 3.5), (12.5, 12.5))
        L((12.5, 3.5), (3.5, 12.5))
    elif name == "min":
        L((3, 8), (13, 8))
    elif name == "max":
        _rr(cr, 3, 3, 10, 10, 1.2)
        cr.stroke()
    elif name == "restore":
        _rr(cr, 3, 5, 8, 8, 1.2)
        cr.stroke()
        L((5, 3), (12, 3), (13, 4), (13, 11))
    elif name == "search":
        cr.arc(6.6, 6.6, 4.6, 0, 2 * pi)
        cr.stroke()
        L((10, 10), (14, 14))
    elif name == "pane":
        _rr(cr, 1.5, 2.5, 13, 11, 1.5)
        cr.stroke()
        L((10, 2.5), (10, 13.5))
    elif name == "terminal":
        _rr(cr, 1.5, 2.5, 13, 11, 1.5)
        cr.stroke()
        L((4, 6), (6.5, 8), (4, 10))
        L((8, 10.5), (11.5, 10.5))
    elif name == "properties":
        _rr(cr, 2.5, 1.5, 11, 13, 1.5)
        cr.stroke()
        for y in (5, 8, 11):
            cr.arc(5.2, y, 0.8, 0, 2 * pi)
            cr.fill()
            L((7.2, y), (11, y))
    elif name == "pin":
        cr.move_to(6, 2)
        cr.line_to(10, 2)
        cr.line_to(9.5, 6.5)
        cr.line_to(12, 9)
        cr.line_to(4, 9)
        cr.line_to(6.5, 6.5)
        cr.close_path()
        cr.stroke()
        L((8, 9), (8, 14))
    elif name == "pin-fill":
        cr.set_line_width(1.0)
        cr.translate(8, 8)
        cr.rotate(pi / 4)
        cr.translate(-8, -8)
        cr.move_to(6, 2)
        cr.line_to(10, 2)
        cr.line_to(9.5, 6.5)
        cr.line_to(12, 9)
        cr.line_to(4, 9)
        cr.line_to(6.5, 6.5)
        cr.close_path()
        cr.stroke()
        L((8, 9), (8, 14))
    elif name == "folder":
        cr.move_to(1.5, 4)
        cr.line_to(6, 4)
        cr.line_to(7.5, 5.5)
        cr.line_to(14.5, 5.5)
        cr.line_to(14.5, 13)
        cr.line_to(1.5, 13)
        cr.close_path()
        cr.stroke()
    elif name == "file":
        cr.move_to(3.5, 1.5)
        cr.line_to(9.5, 1.5)
        cr.line_to(12.5, 4.5)
        cr.line_to(12.5, 14.5)
        cr.line_to(3.5, 14.5)
        cr.close_path()
        cr.stroke()
        L((9.5, 1.5), (9.5, 4.5), (12.5, 4.5))
    elif name == "zip":
        _rr(cr, 2.5, 1.5, 11, 13, 1.5)
        cr.stroke()
        for y in (3, 5, 7):
            L((7, y), (9, y))
        _rr(cr, 6.5, 9, 3, 3.5, 0.6)
        cr.stroke()
    elif name == "extract":
        _rr(cr, 2.5, 6.5, 11, 8, 1.5)
        cr.stroke()
        L((8, 1.5), (8, 10))
        L((5.5, 7.5), (8, 10), (10.5, 7.5))
    elif name == "restoreitem":
        cr.arc(8.5, 8.5, 5, -pi * 0.9, pi * 0.6)
        cr.stroke()
        L((2, 3.5), (3.6, 6.6), (6.6, 5.4))
    elif name == "open":
        _rr(cr, 1.5, 1.5, 13, 13, 2)
        cr.stroke()
        L((7, 9), (12.5, 3.5))
        L((8.5, 3.5), (12.5, 3.5), (12.5, 7.5))
    elif name == "newtab":
        _rr(cr, 1.5, 3.5, 13, 10, 1.5)
        cr.stroke()
        L((1.5, 6), (8, 6))
        L((8, 3.5), (8, 6))
    elif name == "check":
        L((3, 8.5), (6.5, 12), (13, 4.5))
    elif name == "eject":
        cr.move_to(8, 3)
        cr.line_to(13, 9)
        cr.line_to(3, 9)
        cr.close_path()
        cr.stroke()
        L((3, 12.5), (13, 12.5))
    elif name == "details-view":
        for y in (3.5, 8, 12.5):
            _rr(cr, 1.5, y - 1.2, 2.4, 2.4, 0.5)
            cr.stroke()
            L((6, y), (14.5, y))
    elif name == "icons-view":
        for x in (2, 9):
            for y in (2, 9):
                _rr(cr, x, y, 5, 5, 1.2)
                cr.stroke()
    elif name == "selectall":
        _rr(cr, 2, 2, 12, 12, 1.5)
        cr.stroke()
        L((5, 8), (7.2, 10.2), (11, 6))
    elif name == "info":
        cr.arc(8, 8, 6, 0, 2 * pi)
        cr.stroke()
        L((8, 7), (8, 11.5))
        cr.arc(8, 4.8, 0.9, 0, 2 * pi)
        cr.fill()
    elif name == "share":
        cr.arc(4, 8, 1.8, 0, 2 * pi)
        cr.stroke()
        cr.arc(12, 3.8, 1.8, 0, 2 * pi)
        cr.stroke()
        cr.arc(12, 12.2, 1.8, 0, 2 * pi)
        cr.stroke()
        L((5.6, 7.1), (10.4, 4.7))
        L((5.6, 8.9), (10.4, 11.3))
    elif name == "network":
        _rr(cr, 5, 1.5, 6, 4.5, 1)
        cr.stroke()
        L((8, 6), (8, 9))
        L((3, 9), (13, 9))
        L((3, 9), (3, 11))
        L((13, 9), (13, 11))
        _rr(cr, 1, 11, 4, 3.5, 0.8)
        cr.stroke()
        _rr(cr, 11, 11, 4, 3.5, 0.8)
        cr.stroke()
    elif name == "link":
        cr.arc(5.5, 10.5, 3, pi * 0.25, pi * 1.75)
        cr.stroke()
        cr.arc(10.5, 5.5, 3, pi * 1.25, pi * 0.75)
        cr.stroke()
        L((6.5, 9.5), (9.5, 6.5))
    else:
        draw_glyph_extra(cr, name, L, pi)
    cr.restore()




# ----------------------------------------------------------------------------
# Shared Windows 11 dark style
# ----------------------------------------------------------------------------
BASE_CSS = """
* { font-family: "Segoe UI Variable Text", "Segoe UI", "Selawik", "Open Sans", "Noto Sans", sans-serif; }
window.fx, window.fx-dialog { background-color: #202020; color: #ffffff; font-size: 12px; }
.fx label { color: #ffffff; }
headerbar.fx-title { background: #202020; border: none; box-shadow: none; min-height: 40px; padding: 0; margin: 0; }
headerbar.fx-title:backdrop { background: #202020; }
.app-title { font-size: 12px; color: #ffffff; margin-left: 4px; }
.app-title:backdrop { color: rgba(255,255,255,0.55); }
button.wc { background: transparent; border: none; border-radius: 0; min-width: 46px; min-height: 32px; padding: 0; box-shadow: none; }
button.wc:hover { background-color: rgba(255,255,255,0.06); }
button.wc.close:hover { background-color: #C42B1C; }
.tabstrip { margin-top: 6px; margin-left: 6px; }
button.tab { outline-color: transparent; background: transparent; border: none; border-radius: 8px 8px 0 0; min-height: 34px;
   padding: 0 6px 0 12px; box-shadow: none; margin-right: 1px; }
button.tab:hover { background-color: rgba(255,255,255,0.04); }
button.tab.active { background-color: #2C2C2C; }
button.tab label { font-size: 12px; }
button.tab-x { background: transparent; border: none; border-radius: 4px; min-width: 24px; min-height: 24px; padding: 0; box-shadow: none; }
button.tab-x:hover { background-color: rgba(255,255,255,0.08); }
button.tab-new { background: transparent; border: none; border-radius: 4px; min-width: 32px; min-height: 28px; padding: 0;
   box-shadow: none; margin-top: 4px; margin-left: 2px; }
button.tab-new:hover { background-color: rgba(255,255,255,0.06); }
.bar { background-color: #2C2C2C; padding: 4px 8px; }
.bar-bottom { border-bottom: 1px solid rgba(255,255,255,0.06); }
button.tb, button.nb { background: transparent; border: none; border-radius: 4px; min-height: 32px; padding: 0 9px; box-shadow: none; color: #ffffff; }
button.nb { min-width: 34px; padding: 0; }
button.tb:hover, button.nb:hover { background-color: rgba(255,255,255,0.06); }
button.tb:active, button.nb:active { background-color: rgba(255,255,255,0.04); }
button.tb:disabled label { color: rgba(255,255,255,0.36); }
button.tb label { font-size: 12px; }
button.tb.on, button.nb.on { background-color: rgba(255,255,255,0.09); }
.vsep { background-color: rgba(255,255,255,0.08); min-width: 1px; margin: 6px 6px; }
.status { background-color: #202020; padding: 4px 12px; border-top: 1px solid rgba(255,255,255,0.06); }
.status label { font-size: 12px; color: rgba(255,255,255,0.786); }
.sec { color: rgba(255,255,255,0.786); }
.ter { color: rgba(255,255,255,0.545); }
.big-title { font-size: 20px; font-weight: 600; }
.sect-title { font-size: 14px; font-weight: 600; }
entry.field, entry.fx-search { background-color: rgba(255,255,255,0.06); color: #ffffff; border: 1px solid rgba(255,255,255,0.07);
   border-bottom: 1px solid rgba(255,255,255,0.54); border-radius: 4px; min-height: 30px; padding: 0 10px; box-shadow: none;
   font-size: 12px; caret-color: #ffffff; }
entry.field:focus, entry.fx-search:focus { background-color: #1c1c1c; border-bottom: 2px solid #4CC2FF; }
entry selection, textview text selection, entry selection:focus, textview text selection:focus { background-color: #0078D4; color: #ffffff; }
scrollbar { background: transparent; border: none; }
scrollbar slider { background-color: rgba(255,255,255,0.45); border-radius: 6px; min-width: 3px; min-height: 3px; border: none; }
scrollbar:hover slider { min-width: 6px; min-height: 6px; background-color: rgba(255,255,255,0.55); }
scrollbar trough { background: transparent; border: none; }
scale trough { background-color: rgba(255,255,255,0.3); border: none; border-radius: 2px; min-height: 4px; min-width: 4px; }
scale highlight { background-color: #4CC2FF; border: none; border-radius: 2px; min-height: 4px; min-width: 4px; }
scale slider { background-color: #4CC2FF; border: 5px solid #454545; border-radius: 50%; min-width: 12px; min-height: 12px; box-shadow: none; }
scale slider:hover { border-width: 4px; }
menu, .menu, .context-menu { background-color: #2C2C2C; color: #ffffff; border: 1px solid rgba(0,0,0,0.45); border-radius: 8px; padding: 4px; }
menu menuitem { padding: 6px 12px; border-radius: 4px; color: #ffffff; min-height: 18px; }
menu menuitem:hover { background-color: rgba(255,255,255,0.06); }
menu menuitem:disabled label { color: rgba(255,255,255,0.36); }
menu menuitem label { color: #ffffff; font-size: 12px; }
menu menuitem arrow { color: rgba(255,255,255,0.786); }
menu separator { background-color: rgba(255,255,255,0.08); margin: 4px 0; min-height: 1px; }
window.fx button, window.fx-dialog button { background-image: none; text-shadow: none; -gtk-icon-shadow: none; }
button.primary { background-color: #4CC2FF; color: #000000; border: none; border-radius: 4px; min-height: 30px; padding: 0 16px; box-shadow: none; }
button.primary label { color: #000000; }
button.primary:hover { background-color: #48B1E8; }
button.secondary { background-color: rgba(255,255,255,0.06); color: #ffffff; border: 1px solid rgba(255,255,255,0.09); border-radius: 4px; min-height: 30px; padding: 0 16px; box-shadow: none; }
button.secondary:hover { background-color: rgba(255,255,255,0.09); }
.dlg-body { background-color: #2B2B2B; padding: 24px; }
.dlg-foot { background-color: #202020; padding: 22px 24px; border-top: 1px solid rgba(0,0,0,0.3); }
.dlg-title { font-size: 20px; font-weight: 600; }
.fx-dialog label { color: #ffffff; }
.fx-dialog label.sec { color: rgba(255,255,255,0.786); }
.fx-dialog label.ter { color: rgba(255,255,255,0.545); }
checkbutton check { background-color: rgba(0,0,0,0.1); border: 1px solid rgba(255,255,255,0.6); border-radius: 4px; min-width: 18px; min-height: 18px; -gtk-icon-source: none; color: #000000; }
checkbutton check:checked { background-color: #4CC2FF; border-color: #4CC2FF; -gtk-icon-source: -gtk-icontheme("object-select-symbolic"); }
checkbutton label { color: #ffffff; font-size: 12px; margin-left: 6px; }
radiobutton radio { background-color: rgba(0,0,0,0.1); border: 1px solid rgba(255,255,255,0.6); border-radius: 50%; min-width: 18px; min-height: 18px; -gtk-icon-source: none; }
radiobutton radio:checked { background-color: #000000; border: 5px solid #4CC2FF; }
radiobutton label { color: #ffffff; font-size: 12px; margin-left: 6px; }
switch { background-color: transparent; border: 1px solid rgba(255,255,255,0.6); border-radius: 12px; min-width: 40px; min-height: 18px; }
switch:checked { background-color: #4CC2FF; border-color: #4CC2FF; }
switch slider { background-color: rgba(255,255,255,0.8); border-radius: 50%; min-width: 12px; min-height: 12px; margin: 3px; border: none; box-shadow: none; }
switch:checked slider { background-color: #000000; }
switch image { color: transparent; }
combobox button, combobox box { background-color: rgba(255,255,255,0.06); color: #ffffff; border: 1px solid rgba(255,255,255,0.07); border-radius: 4px; box-shadow: none; min-height: 30px; }
combobox button cellview, combobox button label, combobox arrow { color: #ffffff; }
spinbutton { background-color: rgba(255,255,255,0.06); color: #ffffff; border: 1px solid rgba(255,255,255,0.07); border-radius: 4px; box-shadow: none; }
spinbutton entry { background: transparent; border: none; box-shadow: none; color: #ffffff; }
spinbutton button { background: transparent; border: none; box-shadow: none; color: #ffffff; }
tooltip, tooltip.background { background-color: #2C2C2C; border: 1px solid rgba(0,0,0,0.4); border-radius: 4px; }
tooltip label { color: #ffffff; font-size: 12px; }
.set-group { background-color: rgba(255,255,255,0.05); border-radius: 4px; border: 1px solid rgba(0,0,0,0.2); padding: 12px 16px; }
.set-head { font-size: 13px; }
.set-desc { font-size: 12px; color: rgba(255,255,255,0.6); }
"""


def apply_css(extra=""):
    prov = Gtk.CssProvider()
    prov.load_from_data((BASE_CSS + extra).encode())
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov,
                                             Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 10)
    Gtk.Settings.get_default().set_property("gtk-application-prefer-dark-theme", True)


def draw_glyph_extra(cr, name, L, pi):
    if name == "save":
        _rr(cr, 2, 2, 12, 12, 1.5)
        cr.stroke()
        _rr(cr, 4.5, 2, 6, 4, 0.5)
        cr.stroke()
        _rr(cr, 4.5, 9, 7, 5, 0.5)
        cr.stroke()
    elif name == "undo":
        cr.move_to(3, 7)
        cr.curve_to(6, 3.5, 13, 4.5, 13, 10)
        cr.stroke()
        L((3, 3), (3, 7), (7, 7))
    elif name == "redo":
        cr.move_to(13, 7)
        cr.curve_to(10, 3.5, 3, 4.5, 3, 10)
        cr.stroke()
        L((13, 3), (13, 7), (9, 7))
    elif name == "replace":
        L((2, 5), (10, 5))
        L((7.5, 2.5), (10, 5), (7.5, 7.5))
        L((14, 11), (6, 11))
        L((8.5, 8.5), (6, 11), (8.5, 13.5))
    elif name == "zoomin":
        cr.arc(6.6, 6.6, 4.6, 0, 2 * pi)
        cr.stroke()
        L((10, 10), (14, 14))
        L((4.6, 6.6), (8.6, 6.6))
        L((6.6, 4.6), (6.6, 8.6))
    elif name == "zoomout":
        cr.arc(6.6, 6.6, 4.6, 0, 2 * pi)
        cr.stroke()
        L((10, 10), (14, 14))
        L((4.6, 6.6), (8.6, 6.6))
    elif name == "fit":
        L((2, 5.5), (2, 2), (5.5, 2))
        L((10.5, 2), (14, 2), (14, 5.5))
        L((14, 10.5), (14, 14), (10.5, 14))
        L((5.5, 14), (2, 14), (2, 10.5))
    elif name == "wrap":
        L((2, 3), (14, 3))
        cr.move_to(2, 8)
        cr.line_to(11.5, 8)
        cr.curve_to(15, 8, 15, 13, 11.5, 13)
        cr.line_to(8, 13)
        cr.stroke()
        L((9.5, 11.3), (8, 13), (9.5, 14.7))
        L((2, 13), (5, 13))
    elif name == "play":
        cr.move_to(4.5, 2.5)
        cr.line_to(13, 8)
        cr.line_to(4.5, 13.5)
        cr.close_path()
        cr.fill()
    elif name == "pause":
        _rr(cr, 3.5, 2.5, 3, 11, 0.8)
        cr.fill()
        _rr(cr, 9.5, 2.5, 3, 11, 0.8)
        cr.fill()
    elif name in ("next", "prev"):
        if name == "prev":
            cr.translate(16, 0)
            cr.scale(-1, 1)
        cr.move_to(3, 3)
        cr.line_to(10.5, 8)
        cr.line_to(3, 13)
        cr.close_path()
        cr.fill()
        _rr(cr, 11, 3, 2, 10, 0.6)
        cr.fill()
    elif name == "shuffle":
        L((2, 4), (5, 4), (11, 12), (14, 12))
        L((2, 12), (5, 12), (11, 4), (14, 4))
        L((12, 2), (14, 4), (12, 6))
        L((12, 10), (14, 12), (12, 14))
    elif name in ("repeat", "repeat1"):
        cr.move_to(3, 9)
        cr.line_to(3, 6)
        cr.arc(5, 6, 2, pi, 1.5 * pi)
        cr.line_to(13, 4)
        cr.stroke()
        L((11, 2), (13, 4), (11, 6))
        cr.move_to(13, 7)
        cr.line_to(13, 10)
        cr.arc(11, 10, 2, 0, 0.5 * pi)
        cr.line_to(3, 12)
        cr.stroke()
        L((5, 10), (3, 12), (5, 14))
        if name == "repeat1":
            cr.set_font_size(5)
            cr.move_to(6.8, 9.8)
            cr.show_text("1")
    elif name in ("volume", "mute"):
        cr.move_to(1.5, 6)
        cr.line_to(4.5, 6)
        cr.line_to(8, 2.5)
        cr.line_to(8, 13.5)
        cr.line_to(4.5, 10)
        cr.line_to(1.5, 10)
        cr.close_path()
        cr.stroke()
        if name == "mute":
            L((10.5, 6), (14.5, 10))
            L((14.5, 6), (10.5, 10))
        else:
            cr.arc(8, 8, 3.5, -pi / 3.5, pi / 3.5)
            cr.stroke()
            cr.arc(8, 8, 6.2, -pi / 3.5, pi / 3.5)
            cr.stroke()
    elif name == "fullscreen":
        L((2, 6), (2, 2), (6, 2))
        L((10, 2), (14, 2), (14, 6))
        L((14, 10), (14, 14), (10, 14))
        L((6, 14), (2, 14), (2, 10))
        L((2, 2), (6, 6))
        L((14, 14), (10, 10))
    elif name == "unfullscreen":
        L((6, 2), (6, 6), (2, 6))
        L((10, 2), (10, 6), (14, 6))
        L((10, 14), (10, 10), (14, 10))
        L((6, 14), (6, 10), (2, 10))
    elif name == "rotate":
        cr.arc(8, 9, 5, pi * 1.15, pi * 2.85)
        cr.stroke()
        L((2.5, 2.5), (3.4, 6.4), (7.2, 5.4))
    elif name == "heart":
        cr.move_to(8, 13.5)
        cr.curve_to(1, 8, 1.5, 2.5, 5, 2.5)
        cr.curve_to(6.5, 2.5, 7.5, 3.5, 8, 4.5)
        cr.curve_to(8.5, 3.5, 9.5, 2.5, 11, 2.5)
        cr.curve_to(14.5, 2.5, 15, 8, 8, 13.5)
        cr.stroke()
    elif name == "pen":
        L((2.5, 13.5), (3.2, 10.5), (11, 2.7), (13.3, 5), (5.5, 12.8), (2.5, 13.5))
        L((9.5, 4.2), (11.8, 6.5))
    elif name == "highlighter":
        L((3, 13.5), (13, 13.5))
        cr.move_to(5, 11)
        cr.line_to(11, 3)
        cr.line_to(13.5, 5)
        cr.line_to(7.5, 12.5)
        cr.line_to(5, 12.5)
        cr.close_path()
        cr.stroke()
    elif name == "eraser":
        cr.move_to(2.5, 10)
        cr.line_to(9, 3.5)
        cr.line_to(13.5, 8)
        cr.line_to(8, 13.5)
        cr.line_to(5.5, 13.5)
        cr.close_path()
        cr.stroke()
        L((6, 6.5), (10.5, 11))
        L((8, 13.5), (14, 13.5))
    elif name == "crop":
        L((4.5, 1.5), (4.5, 11.5), (14.5, 11.5))
        L((1.5, 4.5), (11.5, 4.5), (11.5, 14.5))
    elif name == "camera":
        _rr(cr, 1.5, 4, 13, 9.5, 1.6)
        cr.stroke()
        L((5, 4), (6, 2.5), (10, 2.5), (11, 4))
        cr.arc(8, 8.8, 2.6, 0, 2 * pi)
        cr.stroke()
    elif name == "timer":
        cr.arc(8, 9, 5.5, 0, 2 * pi)
        cr.stroke()
        L((8, 9), (8, 5.8))
        L((6.3, 1.8), (9.7, 1.8))
    elif name == "settings":
        n = 8
        cr.new_path()
        for i in range(n * 2):
            a = i * pi / n
            r = 6.6 if i % 2 == 0 else 5.0
            a1, a2 = a - pi / (n * 2.4), a + pi / (n * 2.4)
            cr.line_to(8 + r * math.cos(a1), 8 + r * math.sin(a1))
            cr.line_to(8 + r * math.cos(a2), 8 + r * math.sin(a2))
        cr.close_path()
        cr.stroke()
        cr.arc(8, 8, 2.2, 0, 2 * pi)
        cr.stroke()
    elif name == "history":
        cr.arc(8, 8, 6, pi * 1.05, pi * 2.85)
        cr.stroke()
        L((1.2, 6.2), (2.3, 8.6), (4.6, 7.3))
        L((8, 4.6), (8, 8.2), (10.5, 9.7))
    elif name == "image":
        _rr(cr, 1.5, 2.5, 13, 11, 1.5)
        cr.stroke()
        L((1.5, 11), (5.5, 7), (9, 10.5), (11, 8.5), (14.5, 12))
        cr.arc(10.5, 5.5, 1.2, 0, 2 * pi)
        cr.stroke()
    elif name == "music":
        cr.arc(4.5, 12, 2, 0, 2 * pi)
        cr.stroke()
        cr.arc(12, 10.5, 2, 0, 2 * pi)
        cr.stroke()
        L((6.5, 12), (6.5, 3.5), (14, 2), (14, 10.5))
    elif name == "video":
        _rr(cr, 1.5, 3.5, 9.5, 9, 1.5)
        cr.stroke()
        L((11, 6.5), (14.5, 4.5), (14.5, 11.5), (11, 9.5))
    elif name == "queue":
        for y in (3, 7):
            L((2, y), (14, y))
        L((2, 11), (8, 11))
        cr.move_to(10.5, 9)
        cr.line_to(14, 11.5)
        cr.line_to(10.5, 14)
        cr.close_path()
        cr.fill()
    elif name == "edit":
        L((2.5, 13.5), (3.2, 10.5), (11, 2.7), (13.3, 5), (5.5, 12.8), (2.5, 13.5))
    elif name == "slideshow":
        _rr(cr, 1.5, 2.5, 13, 9, 1.5)
        cr.stroke()
        cr.move_to(6.5, 5)
        cr.line_to(10, 7)
        cr.line_to(6.5, 9)
        cr.close_path()
        cr.fill()
        L((5, 14), (11, 14))
    elif name == "print":
        _rr(cr, 1.5, 6, 13, 6, 1.2)
        cr.stroke()
        L((4.5, 6), (4.5, 1.5), (11.5, 1.5), (11.5, 6))
        _rr(cr, 4.5, 9.5, 7, 5, 0.5)
        cr.stroke()
    elif name == "wallpaper":
        _rr(cr, 1.5, 2.5, 13, 9, 1.2)
        cr.stroke()
        L((1.5, 9.5), (5, 6), (8, 9), (10, 7), (14.5, 10.5))
        L((5.5, 14), (10.5, 14))
        L((8, 11.5), (8, 14))
    elif name == "list":
        for y in (3.5, 8, 12.5):
            cr.arc(2.5, y, 0.9, 0, 2 * pi)
            cr.fill()
            L((5.5, y), (14, y))
    elif name == "add":
        L((8, 2.5), (8, 13.5))
        L((2.5, 8), (13.5, 8))
    elif name == "split":
        _rr(cr, 1.5, 2.5, 13, 11, 1.5)
        cr.stroke()
        L((8, 2.5), (8, 13.5))
    elif name == "keyboard":
        _rr(cr, 1, 3.5, 14, 9, 1.5)
        cr.stroke()
        for x in (4, 6.7, 9.3, 12):
            cr.rectangle(x - 0.5, 6, 1, 1)
        cr.fill()
        L((4.5, 10), (11.5, 10))


class Icon(Gtk.DrawingArea):
    """Monochrome glyph icon."""

    def __init__(self, name, size=16, color=None):
        super().__init__()
        self.name = name
        self.size = size
        self.color = color
        self.set_size_request(size, size)
        self.set_valign(Gtk.Align.CENTER)
        self.connect("draw", self._draw)

    def set_icon(self, name):
        self.name = name
        self.queue_draw()

    def _draw(self, w, cr):
        col = self.color or (1, 1, 1, 1)
        p = self.get_parent()
        if not self.is_sensitive() or (p and not p.is_sensitive()):
            col = (1, 1, 1, 0.36)
        draw_glyph(cr, self.name, self.size, col)


class WinTitlebar(Gtk.HeaderBar):
    """Title bar with Windows 11 caption buttons. Pack your own widgets with pack_start()."""

    def __init__(self, window):
        super().__init__()
        self.win = window
        self.get_style_context().add_class("fx-title")
        self.set_show_close_button(False)
        self.set_custom_title(Gtk.Box())
        wc = Gtk.Box(spacing=0)
        wc.set_valign(Gtk.Align.START)
        for name, cb, extra in (("min", lambda *_: window.iconify(), ""),
                                ("max", lambda *_: self.toggle_max(), ""),
                                ("close", lambda *_: window.close(), "close")):
            b = Gtk.Button()
            b.get_style_context().add_class("wc")
            if extra:
                b.get_style_context().add_class(extra)
            ic = Icon(name, 10)
            b.add(ic)
            b.connect("clicked", cb)
            if name == "max":
                self.max_icon = ic
            wc.pack_start(b, False, False, 0)
        self.pack_end(wc)
        window.connect("window-state-event", self._wstate)
        window.set_titlebar(self)

    def toggle_max(self):
        if self.win.is_maximized():
            self.win.unmaximize()
        else:
            self.win.maximize()

    def _wstate(self, w, ev):
        maxed = bool(ev.new_window_state & Gdk.WindowState.MAXIMIZED)
        self.max_icon.set_icon("restore" if maxed else "max")
        return False


def app_title(text, logo_draw):
    """Little logo + app name for the left of the title bar."""
    box = Gtk.Box(spacing=8)
    box.set_margin_start(14)
    da = Gtk.DrawingArea()
    da.set_size_request(16, 16)
    da.set_valign(Gtk.Align.CENTER)
    da.connect("draw", lambda w, cr: logo_draw(cr, 16))
    box.pack_start(da, False, False, 0)
    lb = Gtk.Label(label=text)
    lb.get_style_context().add_class("app-title")
    box.pack_start(lb, False, False, 0)
    return box, lb


class JsonSettings(dict):
    def __init__(self, app_dir, defaults):
        super().__init__(defaults)
        self.dir = os.path.join(HOME, ".config", app_dir)
        self.file = os.path.join(self.dir, "settings.json")
        try:
            with open(self.file) as f:
                self.update(json.load(f))
        except (OSError, ValueError):
            pass

    def save(self):
        try:
            os.makedirs(self.dir, exist_ok=True)
            tmp = self.file + ".tmp"
            with open(tmp, "w") as f:
                json.dump(self, f, indent=1)
            os.replace(tmp, self.file)
        except OSError:
            pass


def vsep():
    s = Gtk.Box()
    s.get_style_context().add_class("vsep")
    return s


def logo_pixbuf(draw, size):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
    draw(cairo.Context(surf), size)
    return Gdk.pixbuf_get_from_surface(surf, 0, 0, size, size)
def label(text="", cls=None, xalign=0.0, ellipsize=False, wrap=False, markup=False):
    lb = Gtk.Label()
    if markup:
        lb.set_markup(text)
    else:
        lb.set_text(text)
    lb.set_xalign(xalign)
    if cls:
        for c in cls.split():
            lb.get_style_context().add_class(c)
    if ellipsize:
        lb.set_ellipsize(Pango.EllipsizeMode.END)
    if wrap:
        lb.set_line_wrap(True)
        lb.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
    return lb


def add_cls(w, *cls):
    ctx = w.get_style_context()
    for c in cls:
        ctx.add_class(c)
    return w


def tb_button(icon, text, cb=None, chev=False, tip=None):
    b = Gtk.Button()
    add_cls(b, "tb")
    box = Gtk.Box(spacing=7)
    if icon:
        box.pack_start(Icon(icon), False, False, 0)
    if text:
        box.pack_start(Gtk.Label(label=text), False, False, 0)
    if chev:
        box.pack_start(Icon("chevdown", 10), False, False, 0)
    b.add(box)
    b.set_relief(Gtk.ReliefStyle.NONE)
    b.set_tooltip_text(tip or text or None)
    if cb:
        b.connect("clicked", lambda w: cb(w))
    return b


def icon_button(icon, cb, cls="nb", tip=None, size=16):
    b = Gtk.Button()
    add_cls(b, cls)
    b.add(Icon(icon, size))
    b.set_relief(Gtk.ReliefStyle.NONE)
    if tip:
        b.set_tooltip_text(tip)
    b.connect("clicked", lambda w: cb(w))
    return b


def build_menu(spec):
    """spec: list of None (separator) or dicts: label, cb, icon, place, accel, sensitive, checked, sub."""
    menu = Gtk.Menu()
    add_cls(menu, "context-menu")
    for it in spec:
        if it is None:
            menu.append(Gtk.SeparatorMenuItem())
            continue
        mi = Gtk.MenuItem()
        box = Gtk.Box(spacing=12)
        ic = None
        if it.get("checked"):
            ic = Icon("check", 16)
        elif it.get("pixbuf") is not None:
            ic = Gtk.Image.new_from_pixbuf(it["pixbuf"])
        elif it.get("icon"):
            ic = Icon(it["icon"], 16)
        if ic is None:
            ic = Gtk.Box()
            ic.set_size_request(16, 16)
        box.pack_start(ic, False, False, 0)
        lb = Gtk.Label(label=it["label"])
        lb.set_xalign(0)
        box.pack_start(lb, True, True, 0)
        if it.get("accel"):
            al = Gtk.Label(label=it["accel"])
            al.get_style_context().add_class("dim-label")
            al.set_opacity(0.55)
            al.set_margin_start(24)
            box.pack_end(al, False, False, 0)
        mi.add(box)
        mi.set_sensitive(it.get("sensitive", True))
        if it.get("sub") is not None:
            mi.set_submenu(build_menu(it["sub"]))
        elif it.get("cb"):
            cb = it["cb"]
            mi.connect("activate", lambda w, cb=cb: GLib.idle_add(cb))
        menu.append(mi)
    menu.show_all()
    return menu


def popup_menu(menu, widget, event=None):
    menu.attach_to_widget(widget, None)
    if event is not None:
        menu.popup_at_pointer(event)
    else:
        menu.popup_at_widget(widget, Gdk.Gravity.SOUTH_WEST, Gdk.Gravity.NORTH_WEST, None)


# ----------------------------------------------------------------------------
# Windows 11 style dialogs
# ----------------------------------------------------------------------------
class WinDialog(Gtk.Window):
    def __init__(self, parent, title, body=None, primary="OK", secondary="Cancel", width=440, extra=None,
                 markup=False):
        super().__init__(transient_for=parent, modal=True)
        add_cls(self, "fx-dialog")
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_default_size(width, -1)
        self.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        self.set_title(title)
        self.cb = None
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        add_cls(self.body, "dlg-body")
        self.body.pack_start(label(title, "dlg-title"), False, False, 0)
        if body:
            lb = label(body, wrap=True, markup=markup)
            lb.set_max_width_chars(60)
            self.body.pack_start(lb, False, False, 0)
        if extra:
            self.body.pack_start(extra, False, False, 0)
        outer.pack_start(self.body, True, True, 0)
        self.foot = Gtk.Box(spacing=8, homogeneous=True)
        add_cls(self.foot, "dlg-foot")
        self.primary_btn = None
        if primary:
            pb = Gtk.Button(label=primary)
            add_cls(pb, "primary")
            pb.connect("clicked", lambda *_: self.done(True))
            self.foot.pack_start(pb, True, True, 0)
            pb.set_can_default(True)
            self.set_default(pb)
            self.primary_btn = pb
        if secondary:
            sb = Gtk.Button(label=secondary)
            add_cls(sb, "secondary")
            sb.connect("clicked", lambda *_: self.done(False))
            self.foot.pack_start(sb, True, True, 0)
        if primary or secondary:
            outer.pack_start(self.foot, False, False, 0)
        self.add(outer)
        self.connect("key-press-event", self._key)

    def _key(self, w, ev):
        if ev.keyval == Gdk.KEY_Escape:
            self.done(False)
            return True
        return False

    def done(self, ok):
        cb = self.cb
        self.cb = None
        self.hide()
        if cb:
            cb(ok)
        self.destroy()

    def ask(self, cb=None):
        self.cb = cb
        self.show_all()
        if self.primary_btn:
            self.primary_btn.grab_focus()


def info_dialog(parent, title, body):
    WinDialog(parent, title, body, primary="OK", secondary=None).ask()


def confirm(parent, title, body, yes, cb, no="Cancel"):
    WinDialog(parent, title, body, primary=yes, secondary=no).ask(cb)


def error_list_dialog(parent, title, errors):
    lines = []
    for p, msg in errors[:12]:
        lines.append(f"{os.path.basename(p) or p}: {msg}" if p else msg)
    if len(errors) > 12:
        lines.append(f"...and {len(errors) - 12} more")
    info_dialog(parent, title, "\n".join(lines))




# ----------------------------------------------------------------------------
# Start menu
# ----------------------------------------------------------------------------
import pwd  # noqa: E402
import datetime  # noqa: E402

gi.require_version("PangoCairo", "1.0")
from gi.repository import PangoCairo  # noqa: E402

try:
    gi.require_version("GtkLayerShell", "0.1")
    from gi.repository import GtkLayerShell  # noqa: E402
except (ValueError, ImportError):
    GtkLayerShell = None

APP_ID = "io.github.pistart"
DEFAULTS = {"pins": None, "align": "left", "show_recent": True}
PANEL_INI = os.path.join(HOME, ".config", "wf-panel-pi", "wf-panel-pi.ini")
PANEL_SYS_INI = "/etc/xdg/wf-panel-pi/wf-panel-pi.ini"
MENU_W = 640
MENU_H = 720
COLS = 6
ROWS = 3

# first installed id of each group becomes a default pin
DEFAULT_PINS = [
    ["pi-explorer.desktop", "pcmanfm.desktop"],
    ["chromium.desktop", "chromium-browser.desktop", "firefox.desktop", "firefox-esr.desktop"],
    ["pi-notepad.desktop", "mousepad.desktop", "org.xfce.mousepad.desktop", "geany.desktop"],
    ["pi-calculator.desktop", "galculator.desktop"],
    ["pi-photos.desktop", "eom.desktop", "gpicview.desktop"],
    ["pi-mediaplayer.desktop", "vlc.desktop"],
    ["pi-terminal.desktop", "lxterminal.desktop"],
    ["pi-snip.desktop"],
    ["pi-taskmgr.desktop"],
    ["rpcc.desktop", "rc_gui.desktop"],
    ["org.thonny.Thonny.desktop", "thonny.desktop"],
    ["geany.desktop", "org.geany.Geany.desktop"],
    ["code.desktop"],
    ["libreoffice-writer.desktop"],
    ["libreoffice-calc.desktop"],
    ["vlc.desktop"],
]

CSS = """
window.start-bg { background-color: transparent; }
.start button, .flyout button { background-image: none; text-shadow: none; -gtk-icon-shadow: none; color: #ffffff; }
.start-ph { color: rgba(255,255,255,0.55); font-size: 13px; margin-left: 5px; }
.start { background-color: rgba(36,36,36,0.985); border: 1px solid rgba(255,255,255,0.09); border-radius: 8px;
   box-shadow: 0 8px 24px rgba(0,0,0,0.5); }
.start label { color: #ffffff; }
.start-foot { background-color: rgba(27,27,27,0.99); border-top: 1px solid rgba(255,255,255,0.06);
   border-radius: 0 0 8px 8px; padding: 0 40px; min-height: 63px; }
.search-pill { background-color: #1D1D1D; border: 1px solid rgba(255,255,255,0.09); border-bottom: 1px solid rgba(255,255,255,0.3);
   border-radius: 17px; min-height: 34px; padding: 0 14px; }
.search-pill.focus { border-bottom: 2px solid #4CC2FF; }
entry.start-search { background: transparent; border: none; box-shadow: none; min-height: 32px; padding: 0 4px;
   color: #ffffff; font-size: 13px; caret-color: #ffffff; }
.sec-head { font-size: 14px; font-weight: 600; }
button.pill { background-color: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.05); border-radius: 4px;
   min-height: 24px; padding: 0 8px; box-shadow: none; }
button.pill:hover { background-color: rgba(255,255,255,0.09); }
button.pill label { font-size: 12px; }
button.tile { background: transparent; border: none; border-radius: 4px; padding: 10px 2px 6px 2px; box-shadow: none;
   min-width: 92px; min-height: 80px; outline-color: transparent; }
button.tile:hover, button.tile:focus { background-color: rgba(255,255,255,0.06); }
button.tile:active { background-color: rgba(255,255,255,0.04); }
button.tile label { font-size: 11.5px; }
button.rec { background: transparent; border: none; border-radius: 4px; padding: 8px 10px; box-shadow: none; outline-color: transparent; }
button.rec:hover, button.rec:focus { background-color: rgba(255,255,255,0.06); }
button.rec label.nm { font-size: 12px; }
button.rec label.tm { font-size: 11px; color: rgba(255,255,255,0.6); }
button.row { background: transparent; border: none; border-radius: 4px; padding: 5px 10px; box-shadow: none; outline-color: transparent; }
button.row:hover, button.row:focus { background-color: rgba(255,255,255,0.06); }
button.row label { font-size: 12px; }
button.letter { background: transparent; border: none; border-radius: 4px; padding: 4px 10px; box-shadow: none; }
button.letter:hover { background-color: rgba(255,255,255,0.06); }
button.letter label { font-size: 12px; font-weight: 600; }
button.jump { background-color: rgba(255,255,255,0.04); border: none; border-radius: 4px; min-width: 52px; min-height: 52px;
   box-shadow: none; }
button.jump:hover { background-color: rgba(255,255,255,0.09); }
button.jump label { font-size: 18px; font-weight: 600; }
button.jump:disabled label { color: rgba(255,255,255,0.25); }
button.user { background: transparent; border: none; border-radius: 4px; padding: 4px 12px 4px 8px; box-shadow: none; }
button.user:hover { background-color: rgba(255,255,255,0.06); }
button.user label { font-size: 12px; }
button.foot { background: transparent; border: none; border-radius: 4px; min-width: 40px; min-height: 40px; padding: 0; box-shadow: none; }
button.foot:hover { background-color: rgba(255,255,255,0.06); }
.dot { background-color: rgba(255,255,255,0.35); border-radius: 3px; min-width: 6px; min-height: 6px; }
.dot.on { background-color: #ffffff; min-height: 14px; }
.flyout { background-color: #2C2C2C; border: 1px solid rgba(0,0,0,0.5); border-radius: 8px; padding: 4px;
   box-shadow: 0 6px 16px rgba(0,0,0,0.45); }
button.fly { background: transparent; border: none; border-radius: 4px; padding: 0 12px; min-height: 34px; box-shadow: none; }
button.fly:hover { background-color: rgba(255,255,255,0.06); }
button.fly label { font-size: 12px; }
.fly-sep { background-color: rgba(255,255,255,0.08); min-height: 1px; margin: 4px 2px; }
list.results, list.results row { background: transparent; }
list.results row { border-radius: 4px; padding: 0; outline-color: transparent; }
list.results row:hover { background-color: rgba(255,255,255,0.05); }
list.results row:selected { background-color: rgba(255,255,255,0.09); }
.res-head { font-size: 12px; font-weight: 600; margin: 10px 10px 4px 10px; }
.res-name { font-size: 12px; }
.res-best { font-size: 14px; font-weight: 600; }
.res-type { font-size: 11px; color: rgba(255,255,255,0.6); }
.detail { background-color: rgba(255,255,255,0.04); border-radius: 8px; padding: 20px 8px 8px 8px; }
.detail-name { font-size: 16px; font-weight: 600; }
.detail-sep { background-color: rgba(255,255,255,0.08); min-height: 1px; margin: 14px 4px 8px 4px; }
.empty-note { font-size: 12px; color: rgba(255,255,255,0.6); }
"""


def draw_logo(cr, s):
    """Start button: four soft rounded tiles."""
    cr.save()
    cr.scale(s / 16.0, s / 16.0)
    g = cairo.LinearGradient(1, 1, 15, 15)
    g.add_color_stop_rgb(0, 0.33, 0.80, 1.0)
    g.add_color_stop_rgb(1, 0.0, 0.42, 0.85)
    for x, y in ((1.2, 1.2), (8.6, 1.2), (1.2, 8.6), (8.6, 8.6)):
        _rr(cr, x, y, 6.2, 6.2, 1.9)
    cr.set_source(g)
    cr.fill()
    cr.restore()


_orig_extra = draw_glyph_extra


def draw_glyph_extra(cr, name, L, pi):  # noqa: F811
    if name == "power":
        cr.arc(8, 8.6, 5.2, -pi / 2 + 0.75, -pi / 2 - 0.75 + 2 * pi)
        cr.stroke()
        L((8, 1.8), (8, 7.6))
    elif name == "gear":
        cr.arc(8, 8, 2.2, 0, 2 * pi)
        cr.stroke()
        for i in range(8):
            a = i * pi / 4
            L((8 + 4.4 * math.cos(a), 8 + 4.4 * math.sin(a)), (8 + 6.2 * math.cos(a), 8 + 6.2 * math.sin(a)))
        cr.arc(8, 8, 4.6, 0, 2 * pi)
        cr.stroke()
    elif name == "lock":
        _rr(cr, 3, 7, 10, 7, 1.5)
        cr.stroke()
        cr.arc(8, 6.5, 3, pi, 0)
        L((5, 6.5), (5, 7))
        cr.new_path()
        cr.arc(8, 6.5, 3, pi, 2 * pi)
        cr.stroke()
        L((11, 6.5), (11, 7))
        L((8, 9.8), (8, 11.2))
    elif name == "signout":
        L((9.5, 2.5), (3, 2.5), (3, 13.5), (9.5, 13.5))
        L((6.5, 8), (14, 8))
        L((11.5, 5.5), (14, 8), (11.5, 10.5))
    elif name == "restart":
        cr.arc(8, 8, 5.2, -pi / 2 + 0.2, 1.5 * pi - 0.5)
        cr.stroke()
        L((7.4, 0.9), (8.6, 2.8), (6.6, 4.0))
    elif name == "chevleft":
        L((10, 3), (5, 8), (10, 13))
    elif name == "user":
        cr.arc(8, 5.5, 3, 0, 2 * pi)
        cr.stroke()
        cr.arc(8, 15, 6, pi + 0.35, 2 * pi - 0.35)
        cr.stroke()
    else:
        _orig_extra(cr, name, L, pi)


# ---------------------------------------------------------------- helpers
def _sh(cmd):
    try:
        subprocess.Popen(cmd, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except OSError:
        return False


def app_image(gicon, size):
    if gicon is None:
        gicon = Gio.ThemedIcon.new("application-x-executable")
    img = Gtk.Image.new_from_gicon(gicon, Gtk.IconSize.DIALOG)
    img.set_pixel_size(size)
    return img


def time_ago(ts):
    now = time.time()
    d = now - ts
    if d < 60:
        return "Just now"
    if d < 3600:
        return f"{int(d // 60)}m ago"
    if d < 86400:
        return f"{int(d // 3600)}h ago"
    dt = datetime.datetime.fromtimestamp(ts)
    if d < 2 * 86400:
        return "Yesterday at " + dt.strftime("%I:%M %p").lstrip("0")
    if d < 7 * 86400:
        return dt.strftime("%A")
    return dt.strftime("%b %d").replace(" 0", " ")


def user_names():
    if os.environ.get("PI_START_DEMO_NAME"):
        return os.environ["PI_START_DEMO_NAME"], "pi"
    user = os.environ.get("USER") or ""
    try:
        pw = pwd.getpwuid(os.getuid())
        user = pw.pw_name
        full = (pw.pw_gecos or "").split(",")[0].strip()
    except KeyError:
        full = ""
    return full or user or "User", user


def panel_position():
    for path in (PANEL_INI, PANEL_SYS_INI):
        kf = GLib.KeyFile()
        try:
            kf.load_from_file(path, GLib.KeyFileFlags.NONE)
            return kf.get_string("panel", "position").strip()
        except GLib.Error:
            continue
    return "top"


def _launcher_list():
    for path in (PANEL_INI, PANEL_SYS_INI):
        kf = GLib.KeyFile()
        try:
            kf.load_from_file(path, GLib.KeyFileFlags.KEEP_COMMENTS)
            return kf.get_string("panel", "launchers").split()
        except GLib.Error:
            continue
    return []


def taskbar_pinned(app_id):
    return (app_id[:-8] if app_id.endswith(".desktop") else app_id) in _launcher_list()


def taskbar_set(app_id, pinned):
    """Add or remove an app on the wf-panel-pi taskbar. The panel reloads its file on its own."""
    lid = app_id[:-8] if app_id.endswith(".desktop") else app_id
    cur = _launcher_list()
    if pinned and lid not in cur:
        cur.append(lid)
    elif not pinned and lid in cur:
        cur.remove(lid)
    else:
        return
    kf = GLib.KeyFile()
    try:
        kf.load_from_file(PANEL_INI, GLib.KeyFileFlags.KEEP_COMMENTS)
    except GLib.Error:
        pass
    kf.set_string("panel", "launchers", " ".join(cur))
    try:
        os.makedirs(os.path.dirname(PANEL_INI), exist_ok=True)
        kf.save_to_file(PANEL_INI)
    except GLib.Error:
        pass


# ---------------------------------------------------------------- data
class AppItem:
    def __init__(self, info):
        self.info = info
        self.id = info.get_id() or ""
        self.name = info.get_display_name() or info.get_name() or self.id
        self.gicon = info.get_icon()
        parts = [info.get_description() or ""]
        if isinstance(info, Gio.DesktopAppInfo):
            parts.append(info.get_generic_name() or "")
            parts += list(info.get_keywords() or [])
            parts.append(info.get_categories() or "")
        parts.append(os.path.basename(info.get_executable() or ""))
        self.extra = " ".join(parts).lower()
        self.key = self.name.lower()

    def is_settings(self):
        return "settings" in self.extra


class AppDB:
    def __init__(self):
        self.items = []
        self.by_id = {}
        self.reload()

    def reload(self):
        seen = {}
        for info in Gio.AppInfo.get_all():
            try:
                if not info.should_show():
                    continue
            except Exception:
                continue
            aid = info.get_id() or ""
            if aid == "pi-start.desktop":
                continue
            it = AppItem(info)
            exe = os.path.basename((info.get_executable() or "").split()[0] if info.get_executable() else "")
            k = (it.key, exe)
            if k in seen:
                # keep our own pi-* entry when two entries are the same app
                if aid.startswith("pi-") and not seen[k].id.startswith("pi-"):
                    seen[k] = it
                continue
            seen[k] = it
        self.items = sorted(seen.values(), key=lambda a: a.key)
        self.by_id = {a.id: a for a in self.items}

    def get(self, aid):
        it = self.by_id.get(aid)
        if it:
            return it
        try:
            info = Gio.DesktopAppInfo.new(aid)
        except TypeError:
            info = None
        if info is None:
            return None
        return AppItem(info)

    def find_exe(self, names):
        for n in names:
            for a in self.items:
                exe = a.info.get_executable() or ""
                if os.path.basename(exe.split()[0] if exe else "") == n:
                    return a
        return None


class FileIndex:
    """Small background index of file names in the home folder for search."""
    SKIP = {"node_modules", "__pycache__", "venv", ".venv", "site-packages", "snap"}

    def __init__(self):
        self.files = []
        self.built = 0
        self.busy = False

    def refresh(self):
        if self.busy or time.time() - self.built < 120:
            return
        self.busy = True
        threading.Thread(target=self._build, daemon=True).start()

    def _build(self):
        out = []
        stack = [(HOME, 0)]
        while stack and len(out) < 40000:
            d, depth = stack.pop()
            try:
                with os.scandir(d) as it:
                    for e in it:
                        if e.name.startswith("."):
                            continue
                        try:
                            if e.is_dir(follow_symlinks=False):
                                if depth < 5 and e.name not in self.SKIP:
                                    stack.append((e.path, depth + 1))
                                out.append((e.name.lower(), e.path, True))
                            elif e.is_file(follow_symlinks=False):
                                out.append((e.name.lower(), e.path, False))
                        except OSError:
                            pass
            except OSError:
                pass
        self.files = out
        self.built = time.time()
        self.busy = False

    def search(self, q, limit=6):
        hits = []
        for low, path, isdir in self.files:
            if q in low:
                score = 3 if low.startswith(q) else (2 if re.search(r"[\s_\-.]" + re.escape(q), low) else 1)
                hits.append((-score, len(low), path, isdir))
        hits.sort()
        return [(p, d) for _, _, p, d in hits[:limit]]


def recent_files(limit):
    out = []
    try:
        items = Gtk.RecentManager.get_default().get_items()
    except Exception:
        items = []
    for r in items:
        uri = r.get_uri()
        if not uri.startswith("file://"):
            continue
        path = GLib.filename_from_uri(uri)[0]
        if not os.path.exists(path):
            continue
        try:
            ts = r.get_modified().to_unix()
        except AttributeError:
            ts = r.get_modified()
        out.append((ts, path, r.get_mime_type() or ""))
    out.sort(reverse=True)
    return out[:limit]


def file_gicon(path, mime=None):
    if os.path.isdir(path):
        return Gio.ThemedIcon.new("folder")
    if not mime:
        mime, _ = Gio.content_type_guess(path, None)
    return Gio.content_type_get_icon(mime or "application/octet-stream")


def open_path(path):
    try:
        Gio.AppInfo.launch_default_for_uri(GLib.filename_to_uri(path, None), None)
    except GLib.Error:
        _sh(["xdg-open", path])


# ---------------------------------------------------------------- window
class StartWindow(Gtk.Window):
    def __init__(self, app):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.app = app
        self.st = app.settings
        self.db = AppDB()
        self.files = FileIndex()
        self.page = 0
        self.fly = None
        self.results = []
        self.shown_at = 0
        self.set_title("Start")
        self.set_application(app)
        add_cls(self, "start-bg")
        self.set_app_paintable(True)
        vis = self.get_screen().get_rgba_visual()
        if vis:
            self.set_visual(vis)
        self.demo_bg = None
        if os.environ.get("PI_START_DEMO_BG"):
            try:
                self.demo_bg = GdkPixbuf.Pixbuf.new_from_file(os.environ["PI_START_DEMO_BG"])
            except GLib.Error:
                pass
        self.connect("draw", self._draw_bg)
        self.layer = bool(GtkLayerShell and os.environ.get("WAYLAND_DISPLAY") and GtkLayerShell.is_supported())
        self.at_bottom = panel_position() == "bottom"
        if self.layer:
            GtkLayerShell.init_for_window(self)
            GtkLayerShell.set_namespace(self, "pi-start")
            GtkLayerShell.set_layer(self, GtkLayerShell.Layer.TOP)
            for e in (GtkLayerShell.Edge.TOP, GtkLayerShell.Edge.BOTTOM, GtkLayerShell.Edge.LEFT, GtkLayerShell.Edge.RIGHT):
                GtkLayerShell.set_anchor(self, e, True)
            try:
                GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.EXCLUSIVE)
            except AttributeError:
                GtkLayerShell.set_keyboard_interactivity(self, True)
        else:
            self.set_decorated(False)
            self.set_skip_taskbar_hint(True)
            self.set_skip_pager_hint(True)
            self.set_keep_above(True)
            self.set_type_hint(Gdk.WindowTypeHint.UTILITY)
            self.connect("focus-out-event", self._focus_out)
        self.connect("key-press-event", self._key)
        self.connect("delete-event", lambda *a: (self.hide_menu(), True)[1])

        self.overlay = Gtk.Overlay()
        self.add(self.overlay)
        self.sink = Gtk.EventBox()
        self.sink.set_visible_window(False)
        self.sink.connect("button-press-event", self._sink_press)
        self.overlay.add(self.sink)

        self.menu = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        add_cls(self.menu, "start")
        self.menu.set_margin_start(12)
        self.menu.set_margin_end(12)
        self.menu.set_margin_top(12)
        self.menu.set_margin_bottom(12)
        self.sink.add(self.menu)
        self._place()
        self._build()
        self.overlay.show_all()
        Gio.AppInfoMonitor.get().connect("changed", lambda *a: self._apps_changed())

    # ---- layout
    def _place(self):
        disp = Gdk.Display.get_default()
        mon = disp.get_primary_monitor() or disp.get_monitor(0)
        geo = mon.get_workarea() if not self.layer else mon.get_geometry()
        avail = geo.height - (0 if not self.layer else 40)
        h = max(420, min(MENU_H, avail - 24))
        self.menu.set_size_request(MENU_W, h)
        self.menu.set_halign(Gtk.Align.CENTER if self.st["align"] == "center" else Gtk.Align.START)
        self.menu.set_valign(Gtk.Align.END if self.at_bottom else Gtk.Align.START)
        if not self.layer:
            self.move(geo.x, geo.y)
            self.set_default_size(geo.width, geo.height)
            self.resize(geo.width, geo.height)

    def _draw_bg(self, w, cr):
        if self.demo_bg is not None:
            a = w.get_allocation()
            pb = self.demo_bg.scale_simple(a.width, a.height, GdkPixbuf.InterpType.BILINEAR)
            Gdk.cairo_set_source_pixbuf(cr, pb, 0, 0)
            cr.paint()
            return False
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)
        return False

    def _build(self):
        m = self.menu
        top = Gtk.Box()
        top.set_margin_start(32)
        top.set_margin_end(32)
        top.set_margin_top(32)
        top.set_margin_bottom(20)
        pill = Gtk.Box(spacing=6)
        add_cls(pill, "search-pill")
        self.pill = pill
        pill.pack_start(Icon("search", 14, color=(1, 1, 1, 0.75)), False, False, 0)
        self.search = Gtk.Entry()
        add_cls(self.search, "start-search")
        self.search.connect("changed", self._search_changed)
        self.search.connect("key-press-event", self._search_key)
        self.search.connect("activate", lambda e: self._activate_selected())
        self.search.connect("focus-in-event", lambda *a: pill.get_style_context().add_class("focus"))
        self.search.connect("focus-out-event", lambda *a: pill.get_style_context().remove_class("focus"))
        # GTK hides placeholder text while the box has focus, so draw our own
        ov = Gtk.Overlay()
        ov.add(self.search)
        self.ph = label("Search for apps, settings, and documents", "start-ph")
        self.ph.set_halign(Gtk.Align.START)
        self.ph.set_no_show_all(False)
        ov.add_overlay(self.ph)
        ov.set_overlay_pass_through(self.ph, True)
        pill.pack_start(ov, True, True, 0)
        top.pack_start(pill, True, True, 0)
        m.pack_start(top, False, False, 0)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(110)
        self.stack.add_named(self._build_home(), "home")
        self.stack.add_named(self._build_all(), "all")
        self.stack.add_named(self._build_letters(), "letters")
        self.stack.add_named(self._build_more(), "more")
        self.stack.add_named(self._build_search(), "search")
        m.pack_start(self.stack, True, True, 0)
        m.pack_end(self._build_foot(), False, False, 0)

    def _head(self, text, btn_text, cb, back=False):
        row = Gtk.Box()
        row.set_margin_start(32 + 18)
        row.set_margin_end(32 + 18)
        row.set_margin_bottom(6)
        row.pack_start(label(text, "sec-head"), False, False, 0)
        b = Gtk.Button()
        add_cls(b, "pill")
        bx = Gtk.Box(spacing=8)
        if back:
            bx.pack_start(Icon("chevleft", 10), False, False, 0)
            bx.pack_start(Gtk.Label(label=btn_text), False, False, 0)
        else:
            bx.pack_start(Gtk.Label(label=btn_text), False, False, 0)
            bx.pack_start(Icon("chevright", 10), False, False, 0)
        b.add(bx)
        b.connect("clicked", lambda w: cb())
        row.pack_end(b, False, False, 0)
        return row

    # ---- home page
    def _build_home(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.pack_start(self._head("Pinned", "All", lambda: self.show_page("all")), False, False, 0)
        prow = Gtk.Box()
        prow.set_margin_start(32)
        prow.set_margin_end(14)
        self.pin_grid = Gtk.Grid()
        self.pin_grid.set_column_homogeneous(True)
        self.pin_grid.set_row_spacing(2)
        pe = Gtk.EventBox()
        pe.set_visible_window(False)
        pe.add_events(Gdk.EventMask.SCROLL_MASK | Gdk.EventMask.SMOOTH_SCROLL_MASK)
        pe.connect("scroll-event", self._pin_scroll)
        pe.add(self.pin_grid)
        prow.pack_start(pe, True, True, 0)
        self.dots = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.dots.set_valign(Gtk.Align.CENTER)
        self.dots.set_size_request(18, -1)
        prow.pack_end(self.dots, False, False, 0)
        box.pack_start(prow, False, False, 0)

        self.rec_head = self._head("Recommended", "More", lambda: self.show_page("more"))
        self.rec_head.set_margin_top(22)
        box.pack_start(self.rec_head, False, False, 0)
        self.rec_grid = Gtk.Grid()
        self.rec_grid.set_column_homogeneous(True)
        self.rec_grid.set_column_spacing(8)
        self.rec_grid.set_row_spacing(2)
        self.rec_grid.set_margin_start(32)
        self.rec_grid.set_margin_end(32)
        box.pack_start(self.rec_grid, False, False, 0)
        self.fill_pins()
        return box

    def pins(self):
        if self.st.get("pins") is None:
            out = []
            for group in DEFAULT_PINS:
                for aid in group:
                    if aid in out:
                        break
                    if self.db.get(aid):
                        out.append(aid)
                        break
            self.st["pins"] = out
            self.st.save()
        return [p for p in self.st["pins"] if self.db.get(p)]

    def fill_pins(self):
        for c in self.pin_grid.get_children():
            self.pin_grid.remove(c)
        pins = self.pins()
        per = COLS * ROWS
        pages = max(1, (len(pins) + per - 1) // per)
        self.page = min(self.page, pages - 1)
        shown = pins[self.page * per:(self.page + 1) * per]
        for i, aid in enumerate(shown):
            it = self.db.get(aid)
            b = Gtk.Button()
            add_cls(b, "tile")
            v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=7)
            v.pack_start(app_image(it.gicon, 32), False, False, 0)
            lb = label(it.name, xalign=0.5)
            lb.set_ellipsize(Pango.EllipsizeMode.END)
            lb.set_max_width_chars(11)
            lb.set_width_chars(11)
            v.pack_start(lb, False, False, 0)
            b.add(v)
            b.set_tooltip_text(it.name)
            b.connect("clicked", lambda w, a=it: self.launch(a))
            b.connect("button-press-event", lambda w, e, a=it: self._app_press(w, e, a, pinned=True))
            self.pin_grid.attach(b, i % COLS, i // COLS, 1, 1)
        # keep the grid the same height on every page
        for i in range(len(shown), COLS):
            sp = Gtk.Box()
            sp.set_size_request(92, 80)
            self.pin_grid.attach(sp, i, 0, 1, 1)
        for r in range(max(1, (len(shown) + COLS - 1) // COLS), ROWS):
            sp = Gtk.Box()
            sp.set_size_request(92, 80)
            self.pin_grid.attach(sp, 0, r, 1, 1)
        if not shown:
            note = label("Right-click an app in All apps and choose Pin to Start.", "empty-note", xalign=0.5)
            self.pin_grid.attach(note, 0, 0, COLS, 1)
        for c in self.dots.get_children():
            self.dots.remove(c)
        if pages > 1:
            for p in range(pages):
                d = Gtk.EventBox()
                inner = Gtk.Box()
                add_cls(inner, "dot")
                if p == self.page:
                    add_cls(inner, "on")
                inner.set_halign(Gtk.Align.CENTER)
                d.add(inner)
                d.connect("button-press-event", lambda w, e, p=p: self._set_page(p))
                self.dots.pack_start(d, False, False, 0)
        self.pin_grid.show_all()
        self.dots.show_all()

    def _set_page(self, p):
        self.page = p
        self.fill_pins()

    def _pin_scroll(self, w, ev):
        per = COLS * ROWS
        pages = max(1, (len(self.pins()) + per - 1) // per)
        dy = 0
        if ev.direction == Gdk.ScrollDirection.UP:
            dy = -1
        elif ev.direction == Gdk.ScrollDirection.DOWN:
            dy = 1
        elif ev.direction == Gdk.ScrollDirection.SMOOTH:
            ok, dx, ddy = ev.get_scroll_deltas()
            dy = 1 if ddy > 0.3 else (-1 if ddy < -0.3 else 0)
        n = max(0, min(pages - 1, self.page + dy))
        if n != self.page:
            self._set_page(n)
        return True

    def fill_recent(self):
        for c in self.rec_grid.get_children():
            self.rec_grid.remove(c)
        items = recent_files(6) if self.st["show_recent"] else []
        if not items:
            note = label("Files you open recently will show up here.", "empty-note", xalign=0.5)
            note.set_margin_top(18)
            self.rec_grid.attach(note, 0, 0, 2, 1)
        for i, (ts, path, mime) in enumerate(items):
            self.rec_grid.attach(self._rec_button(path, mime, ts), i % 2, i // 2, 1, 1)
        self.rec_grid.show_all()

    def _rec_button(self, path, mime, ts):
        b = Gtk.Button()
        add_cls(b, "rec")
        h = Gtk.Box(spacing=12)
        h.pack_start(app_image(file_gicon(path, mime), 32), False, False, 0)
        v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        v.set_valign(Gtk.Align.CENTER)
        v.pack_start(label(os.path.basename(path), "nm", ellipsize=True), False, False, 0)
        v.pack_start(label(time_ago(ts), "tm"), False, False, 0)
        h.pack_start(v, True, True, 0)
        b.add(h)
        b.set_tooltip_text(path)
        b.connect("clicked", lambda w: (self.hide_menu(), open_path(path)))
        b.connect("button-press-event", lambda w, e: self._file_press(w, e, path))
        return b

    # ---- all apps
    def _build_all(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.pack_start(self._head("All apps", "Back", lambda: self.show_page("home"), back=True), False, False, 0)
        self.all_sw = Gtk.ScrolledWindow()
        self.all_sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.all_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.all_list.set_margin_start(32 + 8)
        self.all_list.set_margin_end(32 + 8)
        self.all_list.set_margin_bottom(12)
        self.all_sw.add(self.all_list)
        box.pack_start(self.all_sw, True, True, 0)
        self.letter_rows = {}
        self.fill_all()
        return box

    @staticmethod
    def _letter(name):
        c = name[:1].upper()
        if c.isalpha():
            return c
        return "#" if c.isdigit() else "&"

    def fill_all(self):
        for c in self.all_list.get_children():
            self.all_list.remove(c)
        self.letter_rows = {}
        groups = {}
        for a in self.db.items:
            groups.setdefault(self._letter(a.name), []).append(a)
        order = [k for k in ("&", "#") if k in groups] + sorted(k for k in groups if k.isalpha())
        for k in order:
            lb = Gtk.Button()
            add_cls(lb, "letter")
            lb.add(label(k))
            lb.set_halign(Gtk.Align.START)
            lb.set_margin_top(6)
            lb.connect("clicked", lambda w: self.show_page("letters"))
            self.all_list.pack_start(lb, False, False, 0)
            self.letter_rows[k] = lb
            for a in groups[k]:
                b = Gtk.Button()
                add_cls(b, "row")
                h = Gtk.Box(spacing=14)
                h.pack_start(app_image(a.gicon, 24), False, False, 0)
                h.pack_start(label(a.name, ellipsize=True), True, True, 0)
                b.add(h)
                b.connect("clicked", lambda w, a=a: self.launch(a))
                b.connect("button-press-event", lambda w, e, a=a: self._app_press(w, e, a))
                self.all_list.pack_start(b, False, False, 0)
        self.all_list.show_all()
        if hasattr(self, "jump_btns"):
            for k, b in self.jump_btns.items():
                b.set_sensitive(k in self.letter_rows)

    def _build_letters(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.pack_start(self._head("All apps", "Back", lambda: self.show_page("all"), back=True), False, False, 0)
        grid = Gtk.Grid()
        grid.set_row_spacing(6)
        grid.set_column_spacing(6)
        grid.set_halign(Gtk.Align.CENTER)
        grid.set_margin_top(20)
        self.jump_btns = {}
        keys = ["&", "#"] + [chr(c) for c in range(ord("A"), ord("Z") + 1)]
        for i, k in enumerate(keys):
            b = Gtk.Button()
            add_cls(b, "jump")
            b.add(label(k, xalign=0.5))
            b.set_sensitive(k in self.letter_rows)
            b.connect("clicked", lambda w, k=k: self._jump(k))
            grid.attach(b, i % 7, i // 7, 1, 1)
            self.jump_btns[k] = b
        box.pack_start(grid, False, False, 0)
        return box

    def _jump(self, k):
        self.show_page("all")
        row = self.letter_rows.get(k)
        if row is None:
            return

        def go():
            a = row.get_allocation()
            adj = self.all_sw.get_vadjustment()
            adj.set_value(min(a.y, adj.get_upper() - adj.get_page_size()))
            return False
        GLib.idle_add(go)

    # ---- more (all recent files)
    def _build_more(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.pack_start(self._head("Recommended", "Back", lambda: self.show_page("home"), back=True), False, False, 0)
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.more_grid = Gtk.Grid()
        self.more_grid.set_column_homogeneous(True)
        self.more_grid.set_column_spacing(8)
        self.more_grid.set_margin_start(32)
        self.more_grid.set_margin_end(32)
        sw.add(self.more_grid)
        box.pack_start(sw, True, True, 0)
        return box

    def fill_more(self):
        for c in self.more_grid.get_children():
            self.more_grid.remove(c)
        items = recent_files(40) if self.st["show_recent"] else []
        if not items:
            self.more_grid.attach(label("Files you open recently will show up here.", "empty-note", xalign=0.5), 0, 0, 2, 1)
        for i, (ts, path, mime) in enumerate(items):
            self.more_grid.attach(self._rec_button(path, mime, ts), i % 2, i // 2, 1, 1)
        self.more_grid.show_all()

    # ---- search
    def _build_search(self):
        box = Gtk.Box(spacing=12)
        box.set_margin_start(24)
        box.set_margin_end(24)
        box.set_margin_bottom(16)
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sw.set_size_request(300, -1)
        self.res_list = Gtk.ListBox()
        add_cls(self.res_list, "results")
        self.res_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.res_list.connect("row-selected", lambda lb, row: self._show_detail(row))
        self.res_list.connect("row-activated", lambda lb, row: self._open_result(row))
        sw.add(self.res_list)
        box.pack_start(sw, True, True, 0)
        self.detail = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        add_cls(self.detail, "detail")
        self.detail.set_size_request(250, -1)
        box.pack_start(self.detail, False, False, 0)
        return box

    def _search_changed(self, e):
        self.ph.set_visible(not e.get_text())
        q = e.get_text().strip().lower()
        if not q:
            self.show_page("home")
            return
        self.files.refresh()
        apps = []
        for a in self.db.items:
            if a.key.startswith(q):
                s = 100
            elif re.search(r"(^|[\s\-_.])" + re.escape(q), a.key):
                s = 80
            elif q in a.key:
                s = 60
            elif q in a.extra:
                s = 30
            else:
                continue
            apps.append((-s, a.key, a))
        apps.sort(key=lambda t: (t[0], t[1]))
        apps = [a for _, _, a in apps[:8]]
        settings = [a for a in apps if a.is_settings()]
        apps = [a for a in apps if not a.is_settings()]
        docs = []
        seen = set()
        for ts, path, mime in recent_files(60):
            if q in os.path.basename(path).lower():
                docs.append((path, False))
                seen.add(path)
        for path, isdir in self.files.search(q, 8):
            if path not in seen:
                docs.append((path, isdir))
        docs = docs[:6]
        res = []
        first = apps or settings
        if first:
            res.append(("best", "app", first[0]))
            rest_apps = apps[1:] if apps else []
            rest_set = settings[1:] if not apps else settings
        elif docs:
            res.append(("best", "file", docs[0]))
            docs = docs[1:]
            rest_apps, rest_set = [], []
        else:
            rest_apps, rest_set = [], []
        if rest_apps:
            res.append(("head", "Apps", None))
            res += [("item", "app", a) for a in rest_apps]
        if rest_set:
            res.append(("head", "Settings", None))
            res += [("item", "app", a) for a in rest_set]
        if docs:
            res.append(("head", "Documents", None))
            res += [("item", "file", d) for d in docs]
        self._fill_results(res, q)
        if self.stack.get_visible_child_name() != "search":
            self.show_page("search", keep_search=True)

    def _fill_results(self, res, q):
        for c in self.res_list.get_children():
            self.res_list.remove(c)
        first_sel = None
        for kind, typ, obj in res:
            row = Gtk.ListBoxRow()
            row.res = (typ, obj)
            if kind == "head":
                row.set_selectable(False)
                row.set_activatable(False)
                row.add(label(typ, "res-head"))
                row.res = None
            else:
                best = kind == "best"
                h = Gtk.Box(spacing=12)
                h.set_margin_start(10)
                h.set_margin_end(10)
                h.set_margin_top(8 if best else 5)
                h.set_margin_bottom(8 if best else 5)
                if typ == "app":
                    icon, name, sub = obj.gicon, obj.name, "App"
                else:
                    path, isdir = obj
                    icon, name = file_gicon(path), os.path.basename(path)
                    sub = "Folder" if isdir else self._short(os.path.dirname(path))
                h.pack_start(app_image(icon, 32 if best else 24), False, False, 0)
                v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
                v.set_valign(Gtk.Align.CENTER)
                v.pack_start(label(name, "res-best" if best else "res-name", ellipsize=True), False, False, 0)
                if best or typ == "file":
                    v.pack_start(label(sub, "res-type", ellipsize=True), False, False, 0)
                h.pack_start(v, True, True, 0)
                row.add(h)
                if best:
                    hd = Gtk.ListBoxRow()
                    hd.res = None
                    hd.set_selectable(False)
                    hd.set_activatable(False)
                    hd.add(label("Best match", "res-head"))
                    self.res_list.add(hd)
                if first_sel is None:
                    first_sel = row
            self.res_list.add(row)
        if not res:
            row = Gtk.ListBoxRow()
            row.res = None
            row.set_selectable(False)
            nl = label(f'No results for "{q}"', "empty-note", xalign=0.5)
            nl.set_margin_top(30)
            row.add(nl)
            self.res_list.add(row)
        self.res_list.show_all()
        if first_sel:
            self.res_list.select_row(first_sel)
        else:
            self._show_detail(None)

    @staticmethod
    def _short(p):
        return "~" + p[len(HOME):] if p.startswith(HOME) else p

    def _show_detail(self, row):
        for c in self.detail.get_children():
            self.detail.remove(c)
        if row is None or not getattr(row, "res", None):
            self.detail.hide()
            return
        typ, obj = row.res
        if typ == "app":
            icon, name, sub = obj.gicon, obj.name, "App"
        else:
            path, isdir = obj
            icon, name = file_gicon(path), os.path.basename(path)
            sub = ("Folder" if isdir else "File") + "\n" + self._short(path)
        img = app_image(icon, 64)
        img.set_halign(Gtk.Align.CENTER)
        self.detail.pack_start(img, False, False, 0)
        nm = label(name, "detail-name", xalign=0.5, wrap=True)
        nm.set_justify(Gtk.Justification.CENTER)
        nm.set_margin_top(10)
        self.detail.pack_start(nm, False, False, 0)
        sb = label(sub, "res-type", xalign=0.5, wrap=True)
        sb.set_justify(Gtk.Justification.CENTER)
        self.detail.pack_start(sb, False, False, 0)
        sep = Gtk.Box()
        add_cls(sep, "detail-sep")
        self.detail.pack_start(sep, False, False, 0)
        if typ == "app":
            acts = [("open", "Open", lambda: self.launch(obj))]
            pinned = obj.id in (self.st["pins"] or [])
            acts.append(("pin", "Unpin from Start" if pinned else "Pin to Start",
                         lambda: (self.toggle_pin(obj), self._show_detail(row))))
            on_bar = taskbar_pinned(obj.id)
            acts.append(("pin", "Unpin from taskbar" if on_bar else "Pin to taskbar",
                         lambda: (taskbar_set(obj.id, not on_bar), self._show_detail(row))))
        else:
            acts = [("open", "Open", lambda: (self.hide_menu(), open_path(path))),
                    ("folder", "Open file location", lambda: (self.hide_menu(), open_path(os.path.dirname(path)))),
                    ("copy", "Copy path", lambda: self._copy(path))]
        for ic, text, cb in acts:
            b = tb_button(ic, text, lambda w, cb=cb: cb())
            b.get_child().set_halign(Gtk.Align.START)
            self.detail.pack_start(b, False, False, 0)
        self.detail.show_all()

    def _copy(self, text):
        Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).set_text(text, -1)
        if shutil.which("wl-copy") and os.environ.get("WAYLAND_DISPLAY"):
            try:
                subprocess.run(["wl-copy", text], timeout=3)
            except (OSError, subprocess.SubprocessError):
                pass

    def _open_result(self, row):
        if not getattr(row, "res", None):
            return
        typ, obj = row.res
        if typ == "app":
            self.launch(obj)
        else:
            self.hide_menu()
            open_path(obj[0])

    def _activate_selected(self):
        row = self.res_list.get_selected_row()
        if self.stack.get_visible_child_name() == "search" and row:
            self._open_result(row)

    def _search_key(self, w, ev):
        if self.stack.get_visible_child_name() != "search":
            return False
        if ev.keyval in (Gdk.KEY_Down, Gdk.KEY_Up):
            rows = [r for r in self.res_list.get_children() if getattr(r, "res", None)]
            if not rows:
                return True
            cur = self.res_list.get_selected_row()
            i = rows.index(cur) if cur in rows else -1
            i = min(len(rows) - 1, i + 1) if ev.keyval == Gdk.KEY_Down else max(0, i - 1)
            self.res_list.select_row(rows[i])
            return True
        return False

    # ---- footer
    def _build_foot(self):
        foot = Gtk.Box(spacing=4)
        add_cls(foot, "start-foot")
        full, user = user_names()
        ub = Gtk.Button()
        add_cls(ub, "user")
        h = Gtk.Box(spacing=12)
        av = Gtk.DrawingArea()
        av.set_size_request(32, 32)
        av.connect("draw", lambda w, cr: self._draw_avatar(cr, full))
        h.pack_start(av, False, False, 0)
        h.pack_start(label(full), False, False, 0)
        ub.add(h)
        ub.set_valign(Gtk.Align.CENTER)
        ub.set_tooltip_text(user)
        ub.connect("clicked", lambda w: self.open_fly(w, [("lock", "Lock", self.do_lock),
                                                         ("signout", "Sign out", self.do_signout)]))
        foot.pack_start(ub, False, False, 0)
        pw = self._foot_btn("power", "Power", lambda w: self.open_fly(w, [
            ("lock", "Lock", self.do_lock), ("signout", "Sign out", self.do_signout), None,
            ("restart", "Restart", self.do_restart), ("power", "Shut down", self.do_shutdown)]))
        foot.pack_end(pw, False, False, 0)
        foot.pack_end(self._foot_btn("folder", "File Explorer", lambda w: self.open_explorer()), False, False, 0)
        foot.pack_end(self._foot_btn("gear", "Settings", lambda w: self.open_settings()), False, False, 0)
        return foot

    def _foot_btn(self, icon, tip, cb):
        b = Gtk.Button()
        add_cls(b, "foot")
        b.add(Icon(icon, 16))
        b.set_tooltip_text(tip)
        b.set_valign(Gtk.Align.CENTER)
        b.connect("clicked", cb)
        return b

    def _draw_avatar(self, cr, name):
        g = cairo.LinearGradient(0, 0, 32, 32)
        g.add_color_stop_rgb(0, 0.30, 0.76, 1.0)
        g.add_color_stop_rgb(1, 0.0, 0.47, 0.83)
        cr.arc(16, 16, 16, 0, 2 * math.pi)
        cr.set_source(g)
        cr.fill()
        initials = "".join(p[:1] for p in name.split()[:2]).upper() or "U"
        cr.set_source_rgb(1, 1, 1)
        lay = PangoCairo.create_layout(cr)
        lay.set_font_description(Pango.FontDescription("Sans Semi-Bold 11"))
        lay.set_text(initials, -1)
        w, h = lay.get_pixel_size()
        cr.move_to(16 - w / 2, 16 - h / 2)
        PangoCairo.show_layout(cr, lay)

    # ---- flyouts (drawn inside the menu, so they work on every desktop)
    def open_fly(self, widget, items):
        self.close_fly()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        add_cls(box, "flyout")
        box.set_size_request(200, -1)
        for it in items:
            if it is None:
                s = Gtk.Box()
                add_cls(s, "fly-sep")
                box.pack_start(s, False, False, 0)
                continue
            ic, text, cb = it
            b = Gtk.Button()
            add_cls(b, "fly")
            h = Gtk.Box(spacing=12)
            if ic:
                h.pack_start(Icon(ic, 16), False, False, 0)
            h.pack_start(label(text), True, True, 0)
            b.add(h)
            b.connect("clicked", lambda w, cb=cb: (self.close_fly(), cb()))
            box.pack_start(b, False, False, 0)
        box.set_halign(Gtk.Align.START)
        box.set_valign(Gtk.Align.START)
        self.overlay.add_overlay(box)
        box.show_all()
        _, nat = box.get_preferred_size()
        x, y = widget.translate_coordinates(self.overlay, 0, 0)
        a = widget.get_allocation()
        ma = self.menu.get_allocation()
        fx = x + a.width - nat.width if x + a.width / 2 > ma.x + ma.width / 2 else x
        fy = y - nat.height - 6
        if fy < 0:
            fy = y + a.height + 6
        box.set_margin_start(max(0, fx))
        box.set_margin_top(max(0, fy))
        self.fly = box

    def close_fly(self):
        if self.fly is not None:
            self.fly.destroy()
            self.fly = None
            return True
        return False

    def _app_press(self, w, ev, a, pinned=False):
        if ev.button != 3:
            return False
        pins = self.st["pins"] or []
        items = []
        if pinned:
            items.append(("pin", "Unpin from Start", lambda: self.toggle_pin(a)))
            if pins and pins[0] != a.id:
                items.append(("up", "Move to front", lambda: self.move_front(a)))
        else:
            items.append(("pin", "Unpin from Start" if a.id in pins else "Pin to Start", lambda: self.toggle_pin(a)))
        on_bar = taskbar_pinned(a.id)
        items.append(("pin", "Unpin from taskbar" if on_bar else "Pin to taskbar", lambda: taskbar_set(a.id, not on_bar)))
        self._fly_at(ev, w, items)
        return True

    def _file_press(self, w, ev, path):
        if ev.button != 3:
            return False
        self._fly_at(ev, w, [("open", "Open", lambda: (self.hide_menu(), open_path(path))),
                             ("folder", "Open file location", lambda: (self.hide_menu(), open_path(os.path.dirname(path)))),
                             ("copy", "Copy path", lambda: self._copy(path))])
        return True

    def _fly_at(self, ev, w, items):
        self.open_fly(w, items)
        if self.fly is None:
            return
        x, y = w.translate_coordinates(self.overlay, int(ev.x), int(ev.y))
        _, nat = self.fly.get_preferred_size()
        ow = self.overlay.get_allocated_width()
        oh = self.overlay.get_allocated_height()
        self.fly.set_margin_start(max(0, min(x, ow - nat.width - 4)))
        self.fly.set_margin_top(max(0, min(y, oh - nat.height - 4)))

    # ---- actions
    def toggle_pin(self, a):
        pins = list(self.st["pins"] or [])
        if a.id in pins:
            pins.remove(a.id)
        else:
            pins.append(a.id)
        self.st["pins"] = pins
        self.st.save()
        self.fill_pins()

    def move_front(self, a):
        pins = [p for p in (self.st["pins"] or []) if p != a.id]
        self.st["pins"] = [a.id] + pins
        self.st.save()
        self.page = 0
        self.fill_pins()

    def launch(self, a):
        self.hide_menu()
        try:
            ctx = Gdk.Display.get_default().get_app_launch_context()
            a.info.launch([], ctx)
        except GLib.Error:
            exe = a.info.get_executable()
            if exe:
                _sh([exe])

    def open_settings(self):
        a = self.db.find_exe(["rpcc", "rc_gui", "pipanel", "lxappearance"])
        if a:
            self.launch(a)

    def open_explorer(self):
        self.hide_menu()
        for exe in ("pi-explorer", "pcmanfm", "xdg-open"):
            if shutil.which(exe):
                _sh([exe, HOME])
                return

    def do_lock(self):
        self.hide_menu()
        if os.environ.get("WAYLAND_DISPLAY") and shutil.which("swaylock"):
            _sh(["swaylock", "-f", "-c", "202020"])
            return
        for cmd in (["xdg-screensaver", "lock"], ["light-locker-command", "-l"], ["dm-tool", "lock"],
                    ["loginctl", "lock-session"]):
            if shutil.which(cmd[0]):
                _sh(cmd)
                return

    def do_signout(self):
        self.hide_menu()
        if os.environ.get("LABWC_PID") and shutil.which("labwc"):
            _sh(["labwc", "--exit"])
            return
        sid = os.environ.get("XDG_SESSION_ID")
        if sid:
            _sh(["loginctl", "terminate-session", sid])
        else:
            _sh(["loginctl", "terminate-user", user_names()[1]])

    def do_restart(self):
        self.hide_menu()
        _sh(["systemctl", "reboot"])

    def do_shutdown(self):
        self.hide_menu()
        _sh(["systemctl", "poweroff"])

    # ---- pages, show / hide
    def show_page(self, name, keep_search=False):
        self.close_fly()
        if name != "search" and not keep_search and self.search.get_text():
            self.search.handler_block_by_func(self._search_changed)
            self.search.set_text("")
            self.search.handler_unblock_by_func(self._search_changed)
        if name == "more":
            self.fill_more()
        if name == "all" and self.stack.get_visible_child_name() == "home":
            self.all_sw.get_vadjustment().set_value(0)
        self.stack.set_visible_child_name(name)

    def _apps_changed(self):
        self.db.reload()
        self.fill_all()
        self.fill_pins()

    def show_menu(self):
        self.close_fly()
        self.at_bottom = panel_position() == "bottom"
        self._place()
        self.page = 0
        self.search.set_text("")
        self.stack.set_visible_child_name("home")
        self.fill_pins()
        self.fill_recent()
        self.files.refresh()
        self.shown_at = time.time()
        self.show()
        self.present()
        self.search.grab_focus()

    def hide_menu(self):
        self.close_fly()
        self.hide()

    def toggle(self):
        if self.get_visible():
            self.hide_menu()
        else:
            self.show_menu()

    def _focus_out(self, *a):
        if time.time() - self.shown_at > 0.4 and not os.environ.get("PI_START_DEMO_BG"):
            self.hide_menu()
        return False

    def _sink_press(self, w, ev):
        if self.close_fly():
            return True
        a = self.menu.get_allocation()
        if not (a.x <= ev.x <= a.x + a.width and a.y <= ev.y <= a.y + a.height):
            self.hide_menu()
            return True
        return False

    def _key(self, w, ev):
        if ev.keyval == Gdk.KEY_Escape:
            if self.close_fly():
                return True
            if self.search.get_text():
                self.search.set_text("")
            elif self.stack.get_visible_child_name() == "letters":
                self.show_page("all")
            elif self.stack.get_visible_child_name() != "home":
                self.show_page("home")
            else:
                self.hide_menu()
            return True
        # typing anywhere goes to the search box, like Windows
        if not self.search.has_focus() and ev.string and ev.string.isprintable() \
                and not (ev.state & (Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.MOD1_MASK)):
            self.search.grab_focus_without_selecting()
            self.search.set_position(-1)
            return self.search.event(ev)
        return False


# ---------------------------------------------------------------- app
class StartApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.win = None

    def do_startup(self):
        Gtk.Application.do_startup(self)
        self.settings = JsonSettings("pi-start", DEFAULTS)
        apply_css(CSS)
        self.hold()

    def do_command_line(self, cmd):
        args = cmd.get_arguments()[1:]
        if "--quit" in args:
            self.quit()
            return 0
        if self.win is None:
            self.win = StartWindow(self)
        if "--background" in args:
            return 0
        if "--show" in args:
            self.win.show_menu()
        elif "--hide" in args:
            self.win.hide_menu()
        else:
            self.win.toggle()
        return 0


def main():
    GLib.set_prgname("pi-start")
    GLib.set_application_name("Start")
    app = StartApp()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
