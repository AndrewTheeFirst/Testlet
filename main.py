from driver import Driver
from interface import \
    restore_groups, retrieve_groups,\
    store_group, pop_group, get_group

def create():
    ... # creating group
    store_group()

def edit(title: str):
    groups = retrieve_groups()
    group = pop_group(title, groups)
    ... # editing group
    groups.append(group)
    restore_groups(groups)
  
def study(title: str):
    get_group(title)

def delete(title: str):
    groups = retrieve_groups()
    pop_group(title, groups)
    restore_groups(groups)

if __name__ == "__main__":
    screen = Driver()
    screen.set_title("Testlet")
    screen.set_buttons(buttons=["Create new Group", "Study Group", "Edit Group", "Delete Group"])
    screen.set_onpress([lambda: ...,
                        lambda: screen.set_context("choose-mode"),
                        lambda: ...,
                        lambda: ...])
    
    screen.build()
    
    screen.new_context("choose-mode", 
                     [ "Review", "Test", "Back"],
                     [lambda: ...,
                      lambda: ...,
                      lambda: screen.set_context("main-menu")])

    screen.event_loop()
