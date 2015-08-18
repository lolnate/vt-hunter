#!/usr/bin/env python3
import curses
import email
import os
import lib.hunting as hunting

from lib.vtmis.scoring import *
from lib.constants import VT_HUNTER_VERSION, VT_HOME

from configparser import ConfigParser

try:
    config = ConfigParser()
    config.read(os.path.join(VT_HOME, "etc", "vt.ini"))
except ImportError:
    raise SystemExit('vt.ini was not found or was not accessible.')

raw_msgs = config.get("locations", "raw_msgs")

def display_normal(stdscr, dl):
    # Get the rule 'tags'
    hits = hunting.sess.query(hunting.Hit).filter(hunting.Hit.download == dl).all()
    rtags = []
    ctags = []
    file_type = ""
    first_country = ""
    for hit in hits:
        rtags.extend(hit.rule.split("_"))
        file_type = hit.file_type
        first_country = hit.first_country
        ctags.append(get_rule_campaign(hit.rule))
    campaigns = set(ctags)
    rule_tags = set(rtags)

    # Display them
    stdscr.addstr(3,1,"Rule hits: {0}".format(",".join(rule_tags)))
    stdscr.addstr(4,1,"Score: {0}".format(dl.score))
    stdscr.addstr(5,1,"Campaign Matches: {0}".format(" - ".join(campaigns)))
    stdscr.addstr(6,1,"File Type: {0}".format(file_type))
    stdscr.addstr(7,1,"First Country: {0}".format(first_country))

def display_raw(stdscr, dl):
    # Display more information about the email
    # TODO: Allow for more than just the first raw email hit (allow cycling)
    first_hit = hunting.sess.query(hunting.Hit).filter(hunting.Hit.download == dl).first()
    # Figure out how many lines we have available to display this text
    lines_available = stdscr.getmaxyx()[0] - 8
    if lines_available < 0:
        return

    fin = open(raw_msgs + first_hit.raw_email_html, "r")
    text = fin.read().split('<br />')
    fin.close()
    line_num = 1
    for line in text:
        line = line.replace("<br />", "")
        if line_num > lines_available:
            continue
        # Start printing on line 3 (line_num + 2)
        stdscr.addstr(line_num + 2,2,line)
        line_num += 1

def process_grab(command, current_dl):
    # Get the rules for this current md5
    hits = hunting.sess.query(hunting.Hit).filter(hunting.Hit.md5 == current_dl.md5).all()
    rules = []
    for hit in hits:
        rules.extend(hit.rule)


def process_download(current_dl):
    # 1 = Download
    current_dl.process_state = 1
    hunting.sess.commit()


def process_nodownload(current_dl):
    # 5 = Do Not Download
    current_dl.process_state = 5
    hunting.sess.commit()

def main():
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(1)

    curses.start_color()
    scrsize = stdscr.getmaxyx()

    # Init some fancy colors
    curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)

    dl_queue = hunting.sess.query(hunting.Download).filter(hunting.Download.process_state == 0).all()
    dl_iter = iter(dl_queue)
    current_dl = next(dl_iter)
    current_num = 0
    max_num = len(dl_queue)

    running = True
    toggle_raw = False
    toggle_grab = False
    while running:
        stdscr.clear()
        stdscr.addstr(1,1,"VT HUNTER V{0}".format(VT_HUNTER_VERSION), curses.A_BOLD)

        if current_dl is None:
            stdscr.addstr(3,1,"No alerts are available for review!", curses.A_BOLD)
        else:
            current_num += 1
            if toggle_raw:
                display_raw(stdscr, current_dl)
            else:
                display_normal(stdscr, current_dl)

        # Display Help
        stdscr.addstr(scrsize[0] - 4, 1, "COMMANDS", curses.color_pair(1))
        if not toggle_grab:
            stdscr.addstr(scrsize[0] - 3, 1, "q - quit    r - raw email          d - download", curses.color_pair(1))
        else:
            stdscr.addstr(scrsize[0] - 3, 1, "q - quit    d - download", curses.color_pair(1))
        if not toggle_grab:
            stdscr.addstr(scrsize[0] - 2, 1, "s - skip    n - do not download    g - grab tags", curses.color_pair(1))
        else:
            stdscr.addstr(scrsize[0] - 2, 1, "s - skip    n - do not download    g - cancel grab", curses.color_pair(1))

        # Display the number of alerts left
        stdscr.addstr(scrsize[0] - 6, 1, "{0} / {1} Alerts".format(current_num, len(dl_queue)), curses.color_pair(1))

        c = stdscr.getch()
        # Toggle commands
        commands = []
        if c == ord('q'):
            commands.extend('q')
        if current_dl is not None:
            if c == ord('s'):
                commands.extend('s')
            if c == ord('r'):
                if not toggle_grab:
                    commands.extend('r')
            if c == ord('d'):
                commands.extend('d')
                commands.extend('s')
            if c == ord('n'):
                commands.extend('n')
                commands.extend('s')
            if c == ord('g'):
                if toggle_grab:
                    toggle_grab = False
                else:
                    toggle_grab = True

        # Process commands
        if 'q' in commands:
            running = False
            break
        if 'd' in commands:
            if toggle_grab:
                process_grab('d', current_dl)
            else:
                process_download(current_dl)
        if 'n' in commands:
            if toggle_grab:
                process_grab('n', current_dl)
            else:
                process_nodownload(current_dl)
        if 's' in commands:
            toggle_raw = False
            # TODO: Do we want to allow skipping a grabbed set of tags?
            toggle_grab = False
            try:
                current_dl = next(dl_iter)
            except StopIteration:
                dl_queue = hunting.sess.query(hunting.Download).filter(hunting.Download.process_state == 0).all()
                if len(dl_queue) < 1:
                    current_dl = None
                else:
                    dl_iter = iter(dl_queue)
                    current_dl = next(dl_iter)
        if 'r' in commands:
            if toggle_raw:
                toggle_raw = False
            else:
                toggle_raw = True

    # Wrap it up and return the console to normal.
    curses.nocbreak(); stdscr.keypad(0); curses.echo()
    curses.endwin()

if __name__ == "__main__":
    main()
