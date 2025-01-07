from cursestools import *
import cursestools as c
from cursestools.utils import PadType
import curses
from typing import Callable
from atexit import register
from collections import deque

from rich.traceback import install
install()

BUTTON_HEIGHT = 3
BUTTON_WIDTH = 22

class Driver:
    instance = None
    def __init__(self):
        Driver.instance = self
        self.stdscr = curses.initscr()
        self.stdscr.noutrefresh() # will prevent unwanted refreshes later
        self.stdscr.keypad(True) # allows listening for arrow keys
        # curses.mousemask(curses.ALL_MOUSE_EVENTS) # allows listening for mouse events
        curses.noecho() # typed keys will not be displayed on the window
        curses.cbreak() # program will not wait for the enter key to be pressed to react to input
        curses.curs_set(0) # make cursor invisible
        if curses.has_colors:
            curses.start_color()
            self.init_colors()

        self.running = False

        self.title = ""
        self.menu_buttons = []
        self.menu_onpress = []
    
        self.context = ""
        self.last_context: deque[str] = deque()

        self.onpress: dict[str, Callable] = {}
        self.buttons: dict[str, list[str]] = {}
        self.overlay: dict[str, ] = {}
        self.pointer_start: dict[str, ] = {}
    
    def init_colors(self):
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLUE)

    def set_title(self, title: str):
        self.title = title
    
    def set_buttons(self, buttons: list[str]):
        self.menu_buttons = buttons

    def set_onpress(self, lmbdas: list[Callable[[], None]]):
        self.menu_onpress = lmbdas

    def make_header(self):
        '''shows game title and any extra information'''
        header = curses.newwin(1, curses.COLS, 0, 0)
        offset_x = (curses.COLS - len(self.title)) // 2
        header.addstr(0, offset_x, self.title)
        return header

    def make_options(self):
        '''shows controls and any extra information'''
        footer = Panel(1, curses.COLS, curses.LINES - 1, 0)
        text = "| Press Q to Quit | Press R to Return to Main Menu | Press B to Back |"
        offset_x = (curses.COLS - len(text)) // 2
        footer.addstr(0, offset_x, text)
        for label in ["Quit", "Return", "Back"]:
            footer.chgat(0, offset_x + text.find(label) - 5, 1, curses.color_pair(1))
        return footer

    def build(self):
        '''places windows and refreshes the terminal'''
        self.header = self.make_header()
        self.main_screen = Canvas(curses.LINES - 2, curses.COLS, 1, 0, outline=True)
        # self.prompt_box = Panel(1, curses.COLS - 2, curses.LINES - 5, 1)
        # self.text_box = TextBox(3, curses.COLS // 2, curses.LINES - 4, curses.COLS // 4)
        self.options = self.make_options()

        self.new_context("main-menu", self.menu_buttons, self.menu_onpress)
        self.refresh_all()
        self.set_context("main-menu")
        self.options.hide()
        curses.doupdate()

    def refresh_all(self):
        for window in [self.header, self.main_screen, self.options]:
            window.noutrefresh()

    def new_context(self, name: str, buttons: list[str], functions: list[Callable[[], None]], overlay: PadType = None):
        if overlay is None:
            overlay = curses.newpad(*self.main_screen.getmaxyx())
        self.pointer_start[name] = self.setup_buttons(overlay, buttons)
        self.onpress[name] = functions
        self.overlay[name] = overlay
        self.buttons[name] = buttons

    def set_last_context(self):
        num_prev_contexts = len(self.last_context)
        if num_prev_contexts == 0:
            self.set_context(self.context)
        else:
            self.set_context(self.last_context.pop())
            self.last_context.pop()

    def set_context(self, context: str):
        if context != self.context and self.context != "":
            self.last_context.append(self.context)
        self.context = context
        overlay = self.overlay[context]
        self.reset_pointer()
        self.main_screen.set_overlay(overlay)
        self.main_screen.show()

    def setup_buttons(self, overlay: Page, buttons: list[str]):
        pointer_start = (0, 0)
        if buttons:
            num_buttons = len(buttons)
            max_y, max_x = self.main_screen.getmaxyx()
            offset_x = (max_x - BUTTON_WIDTH) // 2
            offset_y = (max_y - BUTTON_HEIGHT * num_buttons + num_buttons - 1) // 2 - 1
            draw_button(overlay, BUTTON_HEIGHT, BUTTON_WIDTH, offset_y, offset_x, buttons[0])
            pointer_start = (offset_y + 1, offset_x - 2)
            for index in range(1, num_buttons):
                offset_y = (max_y - BUTTON_HEIGHT * num_buttons + num_buttons - 1) // 2 - 1 + (index * BUTTON_HEIGHT)
                draw_button(overlay, BUTTON_HEIGHT, BUTTON_WIDTH, offset_y, offset_x, buttons[index])
        return pointer_start

    def reset_pointer(self):
        num_buttons = len(self.buttons[self.context])
        start_y, start_x = self.pointer_start[self.context]
        for num_button in range(num_buttons):
            self.overlay[self.context].addch(start_y + BUTTON_HEIGHT * num_button, start_x, " ")
        if num_buttons != 0:
            self.overlay[self.context].addch(start_y, start_x, ">")
        self.pointer_y = start_y

    def move_pointer(self, dir: Dir):
        if (num_buttons := len(self.buttons[self.context])) == 0:
            return
        start_y, start_x = self.pointer_start[self.context] # highest
        overlay = self.overlay[self.context]
        overlay.addch(self.pointer_y, start_x, ' ') # erasing pointer
        lowest = start_y + BUTTON_HEIGHT * (num_buttons - 1)
        if dir is Dir.UP:
            self.pointer_y = self.pointer_y - BUTTON_HEIGHT if start_y < self.pointer_y else lowest
        elif dir is Dir.DOWN:
            self.pointer_y = self.pointer_y + BUTTON_HEIGHT if self.pointer_y < lowest else start_y
        overlay.addch(self.pointer_y, start_x, '>') # adding pointer
        self.main_screen.refresh()

    def get_pointed(self):
        return (self.pointer_y - self.pointer_start[self.context][0]) // BUTTON_HEIGHT

    def event_loop(self):
        self.running = True
        while self.running:
            key = self.stdscr.getkey()
            curses.flushinp()
            if key == ESC:
                self.options.toggle()
                if self.options.visible:
                    self.main_screen.hide()
                    # self.prompt_box.hide()
                else:
                    self.main_screen.show()
                    # self.prompt_box.show()
            elif self.options.visible:
                self.options_handler(key)
            else:
                self.menu_handler(key)
            # else:
            #     self.text_box.proc_key(key)

    def menu_handler(self, key: str):
        match (key):
            case "KEY_UP" | ('w'):
                self.move_pointer(Dir.UP)
            case "KEY_DOWN" | 's':
                self.move_pointer(Dir.DOWN)
            case c.ENTER | ' ':
                if self.buttons[self.context]:
                    try:
                        self.onpress[self.context][self.get_pointed()]()
                    except IndexError:
                        self.running = False
                        print(">>> ERROR: NOT IMPLEMENTED")

    def options_handler(self, key: str):
        match(key.upper()):
            case 'Q':
                self.close()
            case 'R':
                self.options.hide()
                self.set_context("main-menu")
                self.last_context.clear()
            case 'B':
                self.options.hide()
                self.set_last_context()

    def close(self):
        self.running = False
        self.stdscr.keypad(0)
        curses.echo() # reverses curses.noecho()
        curses.nocbreak() # reverses curses.cbreak()
        curses.endwin() # (uninitializes curses)

def shutdown():
    if Driver.instance == None:
        return
    Driver.instance.close()

register(shutdown)
    
if __name__ == "__main__":
    screen = Driver()
    screen.set_title("Title")
    screen.set_buttons(buttons=["SCRN1 BTN1",
                                "SCRN1 BTN2",
                                "SCRN1 BTN3"])
    ## ADDS TO MAIN MENU
    screen.set_onpress([lambda: screen.set_context("main-menu"),
                        lambda: screen.set_context("0"),
                        lambda: screen.set_context("1")])

    ### MUST BUILD BEFORE ADDING CONTEXTS
    screen.build()
    
    screen.new_context("0", 
                       ["SCRN2 BTN1",
                        "SCRN2 BTN2",
                        "SCRN2 BTN3",
                        "SCRN2 BTN4"],
                       [lambda: screen.set_context("main-menu"),
                        lambda: screen.set_context("1"),
                        lambda: screen.set_context("1"),
                        lambda: screen.set_context("1")])
    
    screen.new_context("1", 
                       ["SCRN3 BTN1",
                        "SCRN3 BTN2"], 
                       [lambda: screen.set_context("main-menu"),
                        lambda: screen.set_context("0")])
    

    screen.event_loop()
