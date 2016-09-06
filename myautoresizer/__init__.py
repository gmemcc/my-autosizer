import ConfigParser
import gtk
import logging
import os
import re
import shutil
from os.path import expanduser, exists

EXCLUDE_WIN_TITLES = ['Desktop', 'XdndCollectionWindowImp', 'unity-launcher', 'unity-panel', 'unity-dash', 'Hud']


def config_logging_default():
    fmt = '[%(levelname)-7s] %(asctime)s %(module)s.%(funcName)s:%(lineno)d  %(message)s'
    logging.basicConfig(format=fmt, datefmt='%Y-%m-%d %I:%M:%S', level=logging.DEBUG)


def get_win_name_or_empty(win):
    try:
        return win.property_get('WM_NAME')[2]
    except TypeError:
        return ''


def get_win_list():
    win_list = []
    root = gtk.gdk.get_default_root_window()
    for wid in root.property_get('_NET_CLIENT_LIST')[2]:
        win = gtk.gdk.window_foreign_new(wid)
        if win:
            win_list.append(win)
    return win_list


def forfirst_window(callback):
    root = gtk.gdk.get_default_root_window()
    for win in get_win_list():
        title = get_win_name_or_empty(win)
        if title not in EXCLUDE_WIN_TITLES:
            callback(win)
            break


def foreach_window(callback):
    root = gtk.gdk.get_default_root_window()
    for win in get_win_list():
        title = get_win_name_or_empty(win)
        if title not in EXCLUDE_WIN_TITLES:
            callback(win)


def print_rect():
    def cb(win):
        wm_name = get_win_name_or_empty(win)
        wm_cls = win.property_get('WM_CLASS')[2]
        rect = 'x: %i  y: %i  width: %i  height: %i depth: %i' % win.get_geometry()
        logging.debug("\nWindow Name: %s\nWindow Class: %s\nRectangle: %s\n", wm_name, wm_cls, rect)

    foreach_window(cb)


def read_cfg():
    cfg = ConfigParser.ConfigParser()
    ini_dir = expanduser('~') + "/.local/etc/"
    ini_name = 'my-autoresizer.ini'
    ini_path = ini_dir + ini_name
    if not exists(ini_path):
        os.makedirs(ini_dir)
        smpl_ini_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ini_name)
        logging.debug("Copy sample configuration file %s to %s" % (smpl_ini_path, ini_dir))
        shutil.copy(smpl_ini_path, ini_path)
    logging.debug("Read configuration from %s" % ini_path)
    cfg.read(ini_path)
    return cfg


def get_scr_size():
    tmp_win = gtk.Window()
    scr = tmp_win.get_screen()
    cur_mon_id = scr.get_monitor_at_window(scr.get_active_window())
    cur_mon_geo = scr.get_monitor_geometry(cur_mon_id)
    return cur_mon_geo[2], cur_mon_geo[3]


def auto_resize():
    cfg = read_cfg()

    def cb(win):
        title = get_win_name_or_empty(win)
        cls = win.property_get('WM_CLASS')[2]
        for section in cfg.sections():
            try:
                title_regex = cfg.get(section, 'title_regex')
                class_regex = cfg.get(section, 'class_regex')
                if re.search(title_regex, title) and re.search(class_regex, cls):
                    g = win.get_geometry()
                    x = g[0]
                    y = g[1]
                    w = g[2]
                    h = g[3]
                    size = cfg.get(section, 'size')
                    if size == 'static':
                        win.unmaximize()
                        w = cfg.getint(section, 'width')
                        h = cfg.getint(section, 'height')
                    position = cfg.get(section, 'position')
                    if position == 'static':
                        x = cfg.getint(section, 'x')
                        y = cfg.getint(section, 'y')
                    elif position == 'center':
                        (sw, sh) = get_scr_size()
                        x = (sw - w + 60) / 2
                        y = (sh - h + 20) / 2
                    win.move_resize(x, y, w, h)
                    logging.info("Move_resizing [x, y, w, h] to: %s , title: %s" % ([x, y, w, h], title))
                    break
            except ConfigParser.NoOptionError as e:
                logging.error("Error in configuration: %s" % e.message)

    foreach_window(cb)
    # The LAST move_resize() invocation has no effect, just a workaround:
    forfirst_window(cb)
