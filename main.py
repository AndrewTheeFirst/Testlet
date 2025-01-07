from driver import Driver
from interface import Group,\
    retrieve_groups, restore_groups, store_group
from cursestools import Page, Dir, TextBox, Align, \
    draw_box, draw_button, cover
from cursestools import consts as c
import curses
from time import sleep
from pygame.time import Clock

clock = Clock()

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
    self.set_context(self.context)

def delete(self: Driver):
    groups = retrieve_groups()
    index = make_selection(self, groups, confirm=True)
    while index != -1:
        groups.pop(index)
        restore_groups(groups)
        index = make_selection(self, groups, confirm=True)
    self.set_last_context()

def view_group(self: Driver, group: Group):
    start_y, start_x, height, width = self.main_screen.getbegyx() + self.main_screen.getmaxyx()
    container = curses.newwin(height, width, start_y, start_x)
    FRAME_WIDTH = 2 * width // 3
    FRAME_HEIGHT = height - 4
    frame_offset_x = (width - FRAME_WIDTH) // 2
    draw_box(container, FRAME_HEIGHT + 2, FRAME_WIDTH + 2, 1, frame_offset_x - 1)
    view_window = curses.newwin(FRAME_HEIGHT, FRAME_WIDTH, start_y + 2, start_x + frame_offset_x)
    container.refresh()
    view = Page(view_window, height=FRAME_HEIGHT * 2, width=FRAME_WIDTH * len(group.terms))

    BOX_HEIGHT, BOX_WIDTH = 8, 50
    box_offset_x = (FRAME_WIDTH - BOX_WIDTH) // 2
    box_offset_y = (FRAME_HEIGHT - BOX_HEIGHT) // 2
    textbox = TextBox(BOX_HEIGHT - 2, BOX_WIDTH - 2, alignment=Align.CENTER, v_centered=True)
    index = 0
    for term, defn in group.terms.items():
        index_offset = index * FRAME_WIDTH
        draw_box(view, BOX_HEIGHT, BOX_WIDTH, box_offset_y, box_offset_x + index_offset)
        textbox.set_text(term)
        textbox.print_textbox(view, box_offset_y + 1, box_offset_x + 1 + index_offset)

        draw_box(view, BOX_HEIGHT, BOX_WIDTH, box_offset_y + FRAME_HEIGHT, box_offset_x + index_offset)
        textbox.set_text(defn)
        textbox.print_textbox(view, box_offset_y + 1 + FRAME_HEIGHT, box_offset_x + 1 + index_offset)
        index += 1

    binds = {'w': c.Dir.DOWN, 'a': c.Dir.RIGHT, 's': c.Dir.UP, 'd': c.Dir.LEFT}
    view.refresh()
    while True:
        key = view.getkey()
        curses.flushinp()
        if key in ['a', 'd']:
            for _ in range(FRAME_WIDTH):
                view.shift(binds[key], 1)
                view.refresh()
                clock.tick(240)
        if key in ['w', 's']:
            for _ in range(FRAME_HEIGHT):
                view.shift(binds[key], 1)
                view.refresh()
                clock.tick(60)
        if key == c.ESC:
            break

def make_selection(self: Driver, groups: list[Group], *, confirm: bool = False) -> int:
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
        desc = f"{group.title} - {len(group.terms)} Terms"
        selection.addstr(index, 0, desc)

    index, v_shift = browse_selection(selection, SEL_WIN_H, num_groups)
    if confirm:
        while index != -1 and not get_confirm(self):
            draw_box(container, SEL_WIN_H + 2, SEL_WIN_W + 2, 2, center_offset_x - 1,)
            container.noutrefresh()
            index, v_shift = browse_selection(selection, SEL_WIN_H, num_groups, index, v_shift)
    return index

def browse_selection(page: Page, sel_win_h: int, num_groups: int, index = 0, v_shift = 0) -> int:
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
        match(key):
            case 'w':
                if selected_y >= shift_unit:
                    selected_y -= shift_unit
                    if selected_y < v_shift:
                        page.shift(Dir.DOWN, shift_unit)
                        v_shift -= shift_unit
            case 's':
                if selected_y < min(page_height - shift_unit, num_groups - 1):
                    selected_y += shift_unit
                    if selected_y >= v_shift + sel_win_h:
                        page.shift(Dir.UP, shift_unit)
                        v_shift += shift_unit
            case c.ENTER:
                break
            case c.ESC:
                selected_y = -1
                break
    return selected_y, v_shift

def get_confirm(self: Driver, prompt: str = "Are you sure? y/n"):
    height, width, beg_y, beg_x = self.main_screen.getmaxyx() + self.main_screen.getbegyx()
    container_h = 5
    container_w = width - 2
    container = curses.newwin(container_h, container_w,
                              beg_y + (height - container_h) // 2, beg_x + 2)
    draw_button(container, container_h - 2, container_w - 2, 1, 1, prompt)
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
                        lambda: ...,
                        lambda: delete(screen)])
    
    screen.build()
    
    screen.new_context("choose-mode", CM_BUTTONS,
                     [lambda: study(screen),
                      lambda: ...,
                      lambda: screen.set_last_context()])

    screen.event_loop()
