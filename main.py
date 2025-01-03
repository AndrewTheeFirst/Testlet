from driver import Driver
from interface import Group,\
    retrieve_groups, restore_groups, store_group
from cursestools import FreeWindow, Panel, Dir
from cursestools import consts as c
import curses
from curses import window

# def create():
#     ... # creating group
#     restore_groups()

# def edit(title: str):
#     groups = retrieve_groups()

#     group = pop_group(title, groups)
#     ... # editing group
#     groups.append(group)
#     restore_groups(groups)
  
# def study(title: str):
#     make_selection()
#     get_group(title)

def delete(self: Driver):
    groups = retrieve_groups()
    index = 0
    while (index := make_selection(self)) != -1:
        groups.pop(index)
        restore_groups(groups)
    self.main_screen.refresh()

def make_selection(self: Driver):
    groups = retrieve_groups()
    num_groups = len(groups)
    start_y, start_x = self.main_screen.getbegyx()
    height, width = self.main_screen.getmaxyx()
    selection_width = 30
    selection_window: window = curses.newwin(\
        height, selection_width, start_y, start_x + (width - selection_width) // 2)

    selection_height = height
    if num_groups > height:
        selection_height = num_groups

    page = FreeWindow(selection_window, height=selection_height)
    for index in range(num_groups):
        group = groups[index]
        desc = f"{index + 1}.) {group.title} - {len(group.terms)} Terms"
        page.addstr(index, 0, desc)
    index = browse_selection(page, selection_height, selection_width, height, width)
    return index

def browse_selection(selection: FreeWindow, sel_height: int, sel_width: int, w_height: int, w_width):
    shift = 1
    y, v_shift = 0, 0
    while True:
        selection.chgat(y, 0, sel_width, curses.A_STANDOUT)
        selection.refresh()
        selection.chgat(y, 0, sel_width, curses.A_NORMAL)
        key = selection.getkey()
        match(key):
            case 'w':
                if y - shift >= 0:
                    y -= shift
                    if y < v_shift:
                        selection.shift(Dir.DOWN, shift)
                        v_shift -= shift
            case 's':
                if y + shift < sel_height:
                    y += shift
                    if y >= v_shift + w_height:
                        selection.shift(Dir.UP, shift)
                        v_shift += shift
            case c.ENTER:
                return y
            case c.ESC:
                return -1
        selection.refresh()

def confirm():
    pass

if __name__ == "__main__":
    screen = Driver()
    screen.set_title("Testlet")
    screen.set_buttons(buttons=["Create new Group", "Study Group", "Edit Group", "Delete Group"])
    screen.set_onpress([lambda: ...,
                        lambda: screen.set_context("choose-mode"),
                        lambda: make_selection(screen),
                        lambda: delete(screen)])
    
    screen.build()
    
    screen.new_context("choose-mode", 
                     [ "Review", "Test", "Back"],
                     [lambda: make_selection(screen),
                      lambda: make_selection(screen),
                      lambda: screen.set_context("main-menu")])

    screen.event_loop()
