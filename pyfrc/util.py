import sys


def print_err(*args):
    print(*args, file=sys.stderr)


def yesno(prompt):
    """Returns True if user answers 'y'"""
    prompt += " [y/n]"
    a = ""
    while a not in ["y", "n"]:
        a = input(prompt).lower()

    return a == "y"
