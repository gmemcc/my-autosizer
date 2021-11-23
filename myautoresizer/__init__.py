import ConfigParser
import gtk
import logging
import os
import re
import shutil
import time
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


def foractive_window(callback):
    active_window = gtk.gdk.get_default_root_window().get_screen().get_active_window()
    callback(active_window)


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


def auto_resize(active_win_only):
    cfg = read_cfg()

    def cb(win):
        title = get_win_name_or_empty(win)
        cls = win.property_get('WM_CLASS')[2]
        for section in cfg.sections():
            try:
                title_regex = cfg.get(section, 'title_regex')
                class_regex = cfg.get(section, 'class_regex')
                if re.search(title_regex, title) and re.search(class_regex, cls):
                    scr = win.get_screen()
                    n_monitors = scr.get_n_monitors()
                    idx_primary_monitor = scr.get_primary_monitor()
                    cur_mon_id = scr.get_monitor_at_window(win)
                    g = win.get_geometry()
                    x = g[0]
                    y = g[1]
                    w = g[2]
                    h = g[3]
                    cur_mon_geo = scr.get_monitor_geometry(cur_mon_id)
                    (sx, sy, sw, sh) = cur_mon_geo[0], cur_mon_geo[1], cur_mon_geo[2], cur_mon_geo[3]
                    # hack
                    scale_factor = 1
                    if sw == 3840 and sh == 2160:
                        scale_factor = 2
                    size = cfg.get(section, 'size')
                    if size == 'static':
                        win.unmaximize()
                        w = cfg.getint(section, 'width') * scale_factor
                        h = cfg.getint(section, 'height') * scale_factor
                    elif size == 'keep':
                        pass
                    position = cfg.get(section, 'position')
                    is_primary = idx_primary_monitor == cur_mon_id
                    x_offset = 0
                    y_offset = 0
                    if is_primary:
                        x_offset = 36 * scale_factor
                    if position == 'static':
                        relative_to = 'left_top'
                        try:
                            relative_to = cfg.get(section, 'relative_to')
                        except:
                            pass
                        if relative_to.find('left') > -1:
                            x = cfg.getint(section, 'x') * scale_factor + x_offset
                        else:
                            x = sw - w - cfg.getint(section, 'x') * scale_factor
                        if relative_to.find('top') > -1:
                            y = cfg.getint(section, 'y') * scale_factor + y_offset
                        else:
                            y = sh - h - cfg.getint(section, 'y') * scale_factor
                        x += sx
                        y += sy
                    elif position == 'center' or position == 'maximize':
                        y_offset = 22 * scale_factor
                        x = (sw - w + x_offset) / 2 + sx
                        y = (sh - h + y_offset) / 2 + sy
                    win.move_resize(x, y, w, h)
                    if position == 'maximize':
                        win.maximize()
                    logging.info("Move and resize [x, y, w, h] to: %s , title: %s, mon: %d" % ([x, y, w, h], title, cur_mon_id))
                    break
            except ConfigParser.NoOptionError as e:
                logging.error("Error in configuration: %s" % e.message)

    time.sleep(5)
    if active_win_only:
        foractive_window(cb)
        # The LAST move_resize() invocation has no effect, just a workaround:
        foractive_window(cb)
    else:
        foreach_window(cb)
        # The LAST move_resize() invocation has no effect, just a workaround:
        forfirst_window(cb)
