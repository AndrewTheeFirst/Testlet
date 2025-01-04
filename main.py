from driver import Driver
from interface import Group,\
    retrieve_groups, restore_groups, store_group
from cursestools import Page, Dir
from cursestools.utils import draw_box
from cursestools import consts as c
import curses
from time import sleep

# def create():
#     ... # creating group
#     restore_groups()

# def edit(title: str):
#     groups = retrieve_groups()

#     group = pop_group(title, groups)
#     ... # editing group
#     groups.append(group)
#     restore_groups(groups)
  
def study(self: Driver):
    index = 0
    groups = retrieve_groups()
    while (index := make_selection(self, groups) != -1):
        view_group(self, groups[index])
    self.set_last_context()

def delete(self: Driver):
    index = 0
    groups = retrieve_groups()
    while (index := make_selection(self, groups)) != -1:
        # confirm() -> Are you sure?
        groups.pop(index)
        restore_groups(groups)
    self.set_last_context()

def view_group(self: Driver, group: Group):
    start_y, start_x, height, width = self.main_screen.getbegyx() + self.main_screen.getmaxyx()
    container = curses.newwin(height, width, start_y, start_x)
    FRAME_WIDTH = 2 * width // 3
    FRAME_HEIGHT = height - 4
    offset_x = (width - FRAME_WIDTH) // 2
    draw_box(container, FRAME_HEIGHT + 2, FRAME_WIDTH + 2, 1, offset_x - 1)
    view_window = curses.newwin(FRAME_HEIGHT, FRAME_WIDTH, start_y + 2, start_x + offset_x)
    container.refresh()
    view = Page(view_window, height=FRAME_HEIGHT * 2, width=FRAME_WIDTH * len(group.terms))
    index = 0
    for term, defn in group.terms.items():
        view.addstr(1, 1 + index * FRAME_WIDTH, f"term: {term}")
        view.addstr(1 + FRAME_HEIGHT, 1 + index * FRAME_WIDTH, f"def: {defn}")
        index += 1

    binds = {'w': c.Dir.DOWN, 'a': c.Dir.RIGHT, 's': c.Dir.UP, 'd': c.Dir.LEFT}
    timeout = 0.001
    view.refresh()
    while True:
        key = view.getkey()
        if key in ['a', 'd']:
            for _ in range(FRAME_WIDTH):
                view.shift(binds[key], 1)
                view.refresh()
                sleep(timeout * FRAME_HEIGHT / 2)
                
        if key in ['w', 's']:
            for _ in range(FRAME_HEIGHT):
                view.shift(binds[key], 1)
                view.refresh()
                sleep(timeout * FRAME_WIDTH / 2)
        if key == c.ESC:
            break

def make_selection(self: Driver, groups: list[Group]):
    num_groups = len(groups)
    height, width, start_y, start_x = self.main_screen.getmaxyx() + self.main_screen.getbegyx()
    container = curses.newwin(height, width, start_y, start_x)
    header = "GROUP SELECT:"
    container.addstr(1, (width - len(header)) // 2, header)

    SEL_WIN_W = 36 + (width % 2)
    SEL_WIN_H = height - 5
    center_offset_x = (width - SEL_WIN_W) // 2
    self.main_screen.remove_overlay()
    selection_window = curses.newwin(SEL_WIN_H, SEL_WIN_W, start_y + 3, start_x + center_offset_x)
    draw_box(container, SEL_WIN_H + 2, SEL_WIN_W + 2, 2, center_offset_x - 1,)
    container.refresh()

    page_height = SEL_WIN_H
    if num_groups > SEL_WIN_H:
        page_height = num_groups
    selection = Page(selection_window, height=page_height)

    for index in range(num_groups): # adding content
        group = groups[index]
        desc = f"{index + 1}.) {group.title} - {len(group.terms)} Terms"
        selection.addstr(index, 0, desc)

    return browse_selection(selection, SEL_WIN_H, num_groups)

def browse_selection(page: Page, sel_win_h: int, num_groups: int):
    page_height, page_width = page.getmaxyx()
    shift = 1
    selected_y, v_shift = 0, 0
    while True:
        page.chgat(selected_y, 0, page_width, curses.A_STANDOUT)
        page.refresh()
        page.chgat(selected_y, 0, page_width, curses.A_NORMAL)
        key = page.getkey()
        match(key):
            case 'w':
                if selected_y >= shift:
                    selected_y -= shift
                    if selected_y < v_shift:
                        page.shift(Dir.DOWN, shift)
                        v_shift -= shift
            case 's':
                if selected_y < min(page_height - shift, num_groups - 1):
                    selected_y += shift
                    if selected_y >= v_shift + sel_win_h:
                        page.shift(Dir.UP, shift)
                        v_shift += shift
            case c.ENTER:
                break
            case c.ESC:
                selected_y = -1
                break
    return selected_y

def confirm():
    pass

MM_BUTTONS = "(TESTING)\0CREATE NEW GROUP\0STUDY GROUP\0EDIT GROUP\0DELETE GROUP".split('\0')
CM_BUTTONS = "REVIEW TEST BACK".split(' ')

if __name__ == "__main__":
    screen = Driver()
    screen.set_title("TESTLET")
    screen.set_buttons(MM_BUTTONS)
    screen.set_onpress([lambda: study(screen),
                        lambda: ...,
                        lambda: screen.set_context("choose-mode"),
                        lambda: ...,
                        lambda: delete(screen)])
    
    screen.build()
    
    screen.new_context("choose-mode", CM_BUTTONS,
                     [lambda: ...,
                      lambda: ...,
                      lambda: screen.set_last_context()])

    screen.event_loop()
