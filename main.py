from driver import Driver
from interface import Group,\
    retrieve_groups, restore_groups, store_group
from cursestools import Page, Panel, Canvas, Terminal, Dir, TextBox, Align, \
    draw_box, draw_button, cover
from cursestools import consts as c
import curses
from time import sleep
from pygame.time import Clock

def copy_window(screen: curses.window):
    return curses.newwin(*screen.getmaxyx(), *screen.getbegyx())

class LineEdit():
    def __init__(self, terminal: Terminal):
        self.terminal = terminal
        self.editing = False
        self.binds = {c.TAB: self.toggle()}
    
    def proc_key(self, key):
        self.binds.get(key, lambda: self.terminal.proc_key(key))()
    
    def toggle(self):
        self.editing = not self.editing

clock = Clock()

# def create():
#     ... # creating group
#     restore_groups()

def edit(self: Driver):
    groups = retrieve_groups()
    index = group_select(self, groups)
    while index != -1:
        view = render_editing_view(self.main_screen, groups[index])
        index = group_select(self, groups)
    self.set_context(self.context)
    # groups.append(group)
    # restore_groups(groups)

def render_editing_view(main_screen: curses.window, group: Group):
    start_y, start_x, height, width = main_screen.getbegyx() + main_screen.getmaxyx()
    view_win_w = 2 * width // 3
    view_win_h = height - 4 - 2
    win_offset_x = start_x + (width - view_win_w) // 2

    container = copy_window(main_screen)
    container.addstr(1,  (width - len(group.title)) // 2, group.title)
    container.refresh()

    view_window = Canvas(view_win_h, view_win_w, start_y + 2, win_offset_x, outline=True)
    view_window.refresh()
    terminal = Terminal(4, view_win_w, height - 2, win_offset_x)
    terminal.refresh()
    view = Page(view_window, width=view_win_w * len(group.terms))
    
    term_index = 0
    line_edit = LineEdit(terminal)
    while True:
        key = view_window.getkey()
        if key == c.ESC:
            break
        elif line_edit.editing:
            pass
        else:
            if key in ['a']:
                term_index -= 1 
                if term_index >= 0:
                    pass
            elif key in ['d']:
                term_index += 1
                num_terms = len(group.terms)
                if term_index < num_terms:
                    view
                else: 
                    term_index = num_terms - 1
                
  
def study(self: Driver):
    groups = retrieve_groups()
    
    index = group_select(self, groups)
    while index != -1:
        view = render_view(self.main_screen, groups[index])
        browse_view(view)
        index = group_select(self, groups)
    self.set_context(self.context)

def delete(self: Driver):
    groups = retrieve_groups()
    index = group_select(self, groups, confirm=True)
    while index != -1:
        groups.pop(index)
        restore_groups(groups)
        index = group_select(self, groups, confirm=True)
    self.set_last_context()

def render_view(main_screen: curses.window, group: Group):
    start_y, start_x, height, width = main_screen.getbegyx() + main_screen.getmaxyx()
    container = curses.newwin(height, width, start_y, start_x)
    view_win_w = 2 * width // 3
    view_win_h = height - 4
    frame_offset_x = (width - view_win_w) // 2
    view_window = curses.newwin(view_win_h, view_win_w, start_y + 2, start_x + frame_offset_x)

    draw_box(container, view_win_h + 2, view_win_w + 2, 1, frame_offset_x - 1)
    container.noutrefresh()
    view = Page(view_window, height=view_win_h * 2, width=view_win_w * len(group.terms))

    BOX_HEIGHT, BOX_WIDTH = 8, 50
    box_offset_x = (view_win_w - BOX_WIDTH) // 2
    box_offset_y = (view_win_h - BOX_HEIGHT) // 2
    textbox = TextBox(BOX_HEIGHT - 2, BOX_WIDTH - 2, alignment=Align.CENTER, v_centered=True)
    index = 0
    for term, defn in group.terms.items():
        index_offset = index * view_win_w
        draw_box(view, BOX_HEIGHT, BOX_WIDTH, box_offset_y, box_offset_x + index_offset)
        textbox.set_text(term)
        textbox.print_textbox(view, box_offset_y + 1, box_offset_x + 1 + index_offset)

        draw_box(view, BOX_HEIGHT, BOX_WIDTH, box_offset_y + view_win_h, box_offset_x + index_offset)
        textbox.set_text(defn)
        textbox.print_textbox(view, box_offset_y + 1 + view_win_h, box_offset_x + 1 + index_offset)
        index += 1
    return view

def browse_view(view: Page):
    frame_h, frame_w = view.get_parent_window().getmaxyx()
    binds = {'w': c.Dir.DOWN, 'a': c.Dir.RIGHT, 's': c.Dir.UP, 'd': c.Dir.LEFT}
    view.refresh()
    while True:
        key = view.getkey()
        curses.flushinp()
        if key in ['a', 'd']:
            for _ in range(frame_w):
                view.shift(binds[key], 1)
                view.refresh()
                clock.tick(240)
        if key in ['w', 's']:
            for _ in range(frame_h):
                view.shift(binds[key], 1)
                view.refresh()
                clock.tick(60)
        if key == c.ESC:
            break

def _render_selection(sel_win_h: int, sel_win_w: int,
                     start_y: int, start_x: int, \
                     groups: list[Group]):
    
    num_groups = len(groups)
    sel_page_h = sel_win_h
    if num_groups > sel_win_h:
        sel_page_h = num_groups
    selection_window = curses.newwin(sel_win_h, sel_win_w, start_y, start_x)
    selection = Page(selection_window, height=sel_page_h)

    for index in range(num_groups):
        group = groups[index]
        desc = f"{group.title} - {len(group.terms)} Terms"
        selection.addstr(index, 0, desc)
    return selection

def _browse_selection(page: Page, num_groups: int, index = 0, v_shift = 0) -> int:
    sel_win_h = page.get_parent_window().getmaxyx()[0]
    page_height, page_width = page.getmaxyx()
    shift_unit = 1
    selected_y, v_shift = index, v_shift
    page.set_offset(v_shift=v_shift)
    while True:
        page.chgat(selected_y, 0, page_width, curses.A_STANDOUT)
        page.refresh()
        page.chgat(selected_y, 0, page_width, curses.A_NORMAL)
        key = page.getkey()
        curses.flushinp()
        if key in ['w', "KEY_UP"] and selected_y >= shift_unit:
            selected_y -= shift_unit
            if selected_y < v_shift:
                page.shift(Dir.DOWN, shift_unit)
                v_shift -= shift_unit
        elif key in ['s', "KEY_DOWN"] and selected_y < min(page_height - shift_unit, num_groups - 1):
            selected_y += shift_unit
            if selected_y >= v_shift + sel_win_h:
                page.shift(Dir.UP, shift_unit)
                v_shift += shift_unit
        elif key in [c.ENTER, c.ESC]:
            if key == c.ESC:
                selected_y = -1
            break
    return selected_y, v_shift

def group_select(self: Driver, groups: list[Group], confirm: bool = False):
    num_groups = len(groups)
    self.main_screen.remove_overlay()
    height, width = self.main_screen.getmaxyx()
    beg_y, beg_x = self.main_screen.getbegyx()

    sel_win_h = height - 5
    sel_win_w = 36 + (width % 2)
    frame_offset_y = 2
    frame_offset_x = (width - sel_win_w) // 2 - 1 # relative to the self.main_screen
    sel_offset_y = beg_y + frame_offset_y + 1 # relative to self.stdscr
    sel_offset_x = beg_x + frame_offset_x + 1

    container = curses.newwin(height, width, beg_y, beg_x)
    selection: Page = _render_selection(sel_win_h, sel_win_w,
                                       sel_offset_y, sel_offset_x,
                                       groups)
    
    header = "GROUP SELECT:"
    container.addstr(1, (width - len(header)) // 2, header)
    draw_box(container, sel_win_h + 2, sel_win_w + 2, frame_offset_y, frame_offset_x)
    container.noutrefresh()
    index, v_shift = _browse_selection(selection, num_groups)
    
    
    if confirm:
        while index != -1 and not get_confirm(self):
            draw_box(container, sel_win_h + 2, sel_win_w + 2, frame_offset_y, frame_offset_x)
            container.noutrefresh()
            index, v_shift = _browse_selection(selection, num_groups, index, v_shift)
    return index

def get_confirm(self: Driver):
    height, width, beg_y, beg_x = self.main_screen.getmaxyx() + self.main_screen.getbegyx()
    container_h = 5
    container_w = width - 2
    container = curses.newwin(container_h, container_w,
                              beg_y + (height - container_h) // 2, beg_x + 2)
    draw_button(container, container_h - 2, container_w - 2, 1, 1,
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
    screen.set_onpress([lambda: ...,
                        lambda: screen.set_context("choose-mode"),
                        lambda: edit(screen),
                        lambda: delete(screen)])
    
    screen.build()
    
    screen.new_context("choose-mode", CM_BUTTONS,
                     [lambda: study(screen),
                      lambda: ...,
                      lambda: screen.set_last_context()])

    screen.event_loop()
