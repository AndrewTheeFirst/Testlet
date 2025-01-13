from driver import Driver
from interface import Group,\
    retrieve_groups, restore_groups, store_group
from cursestools import Page, Panel, Canvas, Terminal, Dir, TextBox, Align, \
    draw_box, draw_button, cover
from cursestools import consts as c
import curses
from curses import window
from time import sleep
from pygame.time import Clock

clock = Clock()
binds = {'a': Dir.RIGHT, 'w': Dir.DOWN, 's': Dir.UP, 'd': Dir.LEFT}

def copy_window(screen: window):
    return curses.newwin(*screen.getmaxyx(), *screen.getbegyx())

def prompt_window(window: window | Page, prompt: str, timeout = 1):
    prompt_len = len(prompt)
    height = window.getmaxyx()[0]
    offset_y, offset_x = 0, 0
    if isinstance(window, Page):
        height = window.get_parent_window().getmaxyx()[0]
        offset_y, offset_x = window.get_offset()
    window.addstr(offset_y + height - 1, offset_x + 0, prompt)
    window.refresh()
    window.addstr(offset_y + height - 1, offset_x + 0, ' ' * prompt_len)
    sleep(timeout)
    window.refresh()

def create():
    ...

def delete(self: Driver, container: window):
    groups = retrieve_groups()
    index = group_select(container, groups, confirm=True)
    while index != -1:
        groups.pop(index)
        restore_groups(groups)
        index = group_select(container, groups, confirm=True)
    self.set_last_context()

class GroupEditView:

    def __init__(self, container: window, group: Group):
        self.group = group
        start_y, start_x, height, width = container.getbegyx() + container.getmaxyx()
        cover(container)
        container.clear()
        container.addstr(1,  (width - len(group.title)) // 2, group.title)

        view_win_w = 2 * width // 3 # 2/3's of the container width
        view_win_h = height - 8 # height of container - 2 to be contained, - 4 for tb, - 2 for header
        tb_h = view_win_h // 2 # 1/2 the height of view_window
        tb_w = 2 * view_win_w // 3 # 2/3's the width of view_window

        win_offset_x = start_x + (width - (view_win_w + 2)) // 2 # Adding 2 adjusts for canvas/tb border

        self.view_window = Canvas(view_win_h + 2, view_win_w + 2, start_y + 2, win_offset_x, outline=True)
        self.line_edit = Terminal(4, view_win_w + 2, height - 2, win_offset_x)
        self.view = Page(self.view_window, multiplier=2, width=view_win_w * len(group.terms))
        self.textbox = TextBox(tb_h, tb_w, v_centered=True, alignment=Align.CENTER)
        
        container.noutrefresh()
        self.view_window.noutrefresh()
        self.line_edit.noutrefresh()
        curses.doupdate()
    
    def render(self):
        self.view.clear()
        terms = self.group.terms
        win_h, win_w = self.view_window.getmaxyx()
        tb_h, tb_w = self.textbox.get_size()
        tb_offset_y = (win_h - tb_h) // 2
        tb_offset_x = (win_w - tb_w) // 2
        for index in range(len(terms)):
            index_hz_offset = index * win_w
            for index_2, label in enumerate(["TERM:", "DEF:"]):
                index_vt_offset = index_2 * win_h
                self.view.addstr(index_vt_offset, 1 + index_hz_offset, label)
                self.textbox.set_text(terms[index][index_2])
                self.textbox.print_textbox(self.view, tb_offset_y + index_vt_offset, tb_offset_x + index_hz_offset)
        self.view.refresh()

    def event_loop(self):
        win_h, win_w = self.view_window.getmaxyx()
        while True:
            key = self.line_edit.getkey()
            if key == c.ESC:
                break
            elif (key := self.line_edit.proc_key(key)):
                if key in binds:
                    shift = win_w if key in ['a', 'd'] else win_h
                    self.view.shift(binds[key], shift)
                    self.view.refresh()
            if (text := self.line_edit.get_text()):
                self.proc_command(text)

    def proc_command(self, text: str):
        # GET THE COMMAND AND ARG
        requires_render = True
        text = text.lstrip()
        gap = text.find(' ')
        arg = text[gap + 1:]
        command = text[:gap]
        
        win_h, win_w = self.view_window.getmaxyx()
        offset_y, offset_x = self.view.get_offset()
        pair = offset_y // win_h
        pair_index =  offset_x // win_w
        
        if command == "/set" and arg:
            self.group.terms[pair_index][pair] = arg
        elif command == "/switch":
            self.group.terms[pair_index][0], self.group.terms[pair_index][1] = \
            self.group.terms[pair_index][1], self.group.terms[pair_index][0]
        else:
            prompt_window(self.view, "Syntax Error")
            requires_render = False
        if requires_render:
            self.render()

def edit(self: Driver, container: window):
    groups = retrieve_groups()
    index = group_select(container, groups)
    while index != -1:
        view = GroupEditView(container, groups[index])
        view.render()
        view.event_loop()
        index = group_select(container, groups)
    self.set_context(self.context)

class GroupStudyView:

    def __init__(self, container: window, group: Group):
        self.group = group
        start_y, start_x, height, width = container.getbegyx() + container.getmaxyx()
        cover(container)
        container.clear()
        container.addstr(1,  (width - len(group.title)) // 2, group.title)
        
        view_win_w = 2 * width // 3
        view_win_h = height - 4
        frame_offset_x = (width - view_win_w) // 2
        tb_h = view_win_h // 2 # 1/2 the height of view_window
        tb_w = 2 * view_win_w // 3 # 2/3's the width of view_window

        self.view_window = Canvas(view_win_h + 2, view_win_w + 2, start_y + 2, start_x + frame_offset_x, outline=True)
        self.view = Page(self.view_window, height=view_win_h * 2, width=view_win_w * len(group.terms))
        self.textbox = TextBox(tb_h, tb_w, alignment=Align.CENTER, v_centered=True)

        container.noutrefresh()
        self.view_window.noutrefresh()
        
    def render(self):
        win_h, win_w = self.view_window.getmaxyx()
        tb_h, tb_w = self.textbox.get_size()
        box_h, box_w = tb_h + 2, tb_w + 2
        tb_offset_y = (win_h - tb_h) // 2
        tb_offset_x = (win_w - tb_w) // 2
        box_offset_y = (win_h - box_h) // 2
        box_offset_x = (win_w - box_w) // 2

        for index, (term, defn) in enumerate(self.group.terms):
            index_hz_offset = index * win_w
            for index_2, text in enumerate([term, defn]):
                index_vt_offset = index_2 * win_h
                draw_box(self.view, box_h, box_w, box_offset_y + index_vt_offset, box_offset_x + index_hz_offset)
                self.textbox.set_text(text)
                self.textbox.print_textbox(self.view, tb_offset_y + index_vt_offset, tb_offset_x + index_hz_offset)

    def event_loop(self):
        win_h, win_w = self.view_window.getmaxyx()
        self.view.refresh()
        while True:
            key = self.view.getkey()
            curses.flushinp()
            if key in ['a', 'd']:
                for _ in range(win_w):
                    self.view.shift(binds[key], 1)
                    self.view.refresh()
                    clock.tick(240)
            if key in ['w', 's']:
                for _ in range(win_h):
                    self.view.shift(binds[key], 1)
                    self.view.refresh()
                    clock.tick(60)
            if key == c.ESC:
                break

def study(self: Driver, container: window):
    groups = retrieve_groups()  
    index = group_select(container, groups)
    while index != -1:
        view = GroupStudyView(container, groups[index])
        view.render()
        view.event_loop()
        index = group_select(container, groups)
    self.set_context(self.context)

class GroupView:
    
    def __init__(self, container: window, groups: list[Group]):
        self.groups = groups
        self.container = container
        num_groups = len(groups)
        height, width, start_y, start_x = self.container.getmaxyx() + self.container.getbegyx()
        win_h = height - 6 # height - 2 to be contained, - 2 for the head, - 2 for the foot
        win_w = width // 3 # will be a third of the width of the screen
        page_h = win_h
        if num_groups > win_h:
            page_h = num_groups
        self.view_window = Canvas(win_h + 2, win_w + 2,\
                                  start_y + 2, start_x + (width - (win_w + 2)) // 2, outline=True)
        self.view = Page(self.view_window, height=page_h)
        self.view_window.refresh()
        self.selected_y = 0
        self.v_shift = 0

    def render(self):
        header = "GROUP SELECT:"
        cover(self.container)
        self.container.clear()
        self.container.addstr(1,  (self.container.getmaxyx()[1] - len(header)) // 2, header)
        self.container.noutrefresh()
        self.view_window.noutrefresh()
        for index in range(len(self.groups)):
            group = self.groups[index]
            desc = f"{group.title} - {len(group.terms)} Terms"
            self.view.addstr(index, 0, desc)

    def event_loop(self) -> int:
        win_h = self.view_window.getmaxyx()[0]
        page_height, page_width = self.view.getmaxyx()
        num_groups = len(self.groups)
        SHIFT_UNIT = 1
        self.view.set_offset(v_shift=self.v_shift)
        while True:
            self.view.chgat(self.selected_y, 0, page_width, curses.A_STANDOUT)
            self.view.refresh()
            self.view.chgat(self.selected_y, 0, page_width, curses.A_NORMAL)
            key = self.view.getkey()
            curses.flushinp()
            if key in ['w', "KEY_UP"] and self.selected_y >= SHIFT_UNIT:
                self.selected_y -= SHIFT_UNIT
                if self.selected_y < self.v_shift:
                    self.view.shift(Dir.DOWN, SHIFT_UNIT)
                    self.v_shift -= SHIFT_UNIT
            elif key in ['s', "KEY_DOWN"] and self.selected_y < min(page_height - SHIFT_UNIT, num_groups - 1):
                self.selected_y += SHIFT_UNIT
                if self.selected_y >= self.v_shift + win_h:
                    self.view.shift(Dir.UP, SHIFT_UNIT)
                    self.v_shift += SHIFT_UNIT
            elif key in [c.ENTER, c.ESC]:
                if key == c.ESC:
                    self.selected_y = -1
                break

def group_select(container: window, groups: list[Group], confirm: bool = False):
    view = GroupView(container, groups)
    while True:
        view.render()
        view.event_loop()
        if confirm and view.selected_y != -1:
            if not get_confirm(container):
                continue
        break
    return view.selected_y

def get_confirm(container: window):
    win_h, win_w = container.getmaxyx()
    draw_button(container, 3, win_w - 2, (win_h - 3) // 2 , 1,
                "Are you sure? y/n")
    while True:
        key = container.getkey()
        if key in ['y', c.ENTER]:
            cover(container)
            return True
        if key in ['n', c.ESC]:
            cover(container)
            return False
    
MM_BUTTONS = "CREATE NEW GROUP,STUDY GROUP,EDIT GROUP,DELETE GROUP".split(',')
CM_BUTTONS = "REVIEW TEST BACK".split()

if __name__ == "__main__":
    input("SET SCREEN TO DESIRED SIZE THEN PRESS ENTER")
    screen = Driver()
    screen.set_title("TESTLET")
    screen.set_buttons(MM_BUTTONS)
    container = ...
    screen.set_onpress([lambda: create(),
                        lambda: screen.set_context("choose-mode"),
                        lambda: edit(screen, container),
                        lambda: delete(screen, container)])

    screen.build()
    container = copy_window(screen.main_screen)
    screen.new_context("choose-mode", CM_BUTTONS,
                     [lambda: study(screen, container),
                      lambda: ...,
                      screen.set_last_context])

    screen.event_loop()
