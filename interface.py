from pickle import dump, load
from dataclasses import dataclass

PATH = "groups.txt"

@dataclass
class Group:
    title: str
    terms: dict[str, str]
    def new_term(self, term: str, definition: str):
        self.terms[term] = definition

def restore_groups(groups: list[Group]):
    with open(PATH, 'wb') as file:
        for group in groups:
            dump(group, file)

def store_group(group: Group):
    with open(PATH, 'ab') as file:
        dump(group, file)

def retrieve_groups() -> list[Group]:
    groups = []
    with open(PATH, 'rb') as file:
        while True:
            try:
                group = load(file)
                groups.append(group)
            except EOFError:
                break
    return groups

# groups = []
# for group_num in range(30):
#     dict = {}
#     title = f"Group {group_num}"
#     group = Group(title, dict)
#     for term_num in range(5):
#         group.new_term(f"Term {term_num}", f"Definition {term_num}")
#     groups.append(group)
# restore_groups(groups)