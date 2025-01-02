from driver import Driver
from typing import Callable
from driver import *
from pickle import dump, load
from dataclasses import dataclass

PATH = "groups.txt"

@dataclass
class Group:
    title: str
    terms: dict[str, str]
    def new_term(self, term: str, definition: str):
        self.terms[term] = definition

def store_group(groups: list[Group]):
    with open(PATH, 'wb') as file:
        for group in groups:
            dump(group, file)

def restore_groups(group: Group):
    with open(PATH, 'ab') as file:
        dump(group, file)

def retrieve_groups():
    groups = []
    with open(PATH, 'rb') as file:
        while True:
            try:
                group = load(file)
                groups.append(group)
            except EOFError:
                break
    return groups

def pop_group(title: str, groups: list[Group]):
    for index in range(len(groups)):
        if groups[index].title == title:
            return groups.pop(index)
    raise Exception("Group could not be Found")

def get_group(title: str, groups: list[Group]):
    for group in groups:
        if group.title == title:
            return group
    raise Exception("Group could not be Found")

# screen = Driver(title="Testlet", 
#                 buttons=["New Study Group",
#                          "Edit a Group",
#                          "Study a Group"])
# screen.add_onpress()
# screen.build()
# screen.event_loop()