from pickle import dump, load

PATH = "groups.txt"


class Group:
    def __init__(self, title: str):
        self.title = title
        self.terms: list[list[str]] = []

    def new_term(self, term: str, definition: str):
        self.terms.append([term, definition])

def sort_groups():
    pass

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

if __name__ == "__main__":
    from random import randrange

    groups = []
    for group_num in    range(50):
        group = Group(f"Group {group_num} Title")
        for term_num in range(randrange(3, 11)):
            group.new_term(f"Group {group_num} - Term {term_num}", f"Group {group_num} - Definition {term_num}")
        groups.append(group)
    restore_groups(groups)