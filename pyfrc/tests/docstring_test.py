import inspect
import os
import re
import sys

# if you want to be really pedantic, enforce sphinx docstrings. Ha.
pedantic_docstrings = True

# regex to use to detect the sphinx docstrings
param_re = re.compile(r"^:param (\S+?):\s*(.+)$")
type_re = re.compile(r"^:type (\S+?):\s*(.+)$")
both_re = re.compile(r"^:param (\S+?) (\S+?):\s*(.+)$")


def ignore_object(o, robot_path):
    """Returns true if the object can be ignored"""

    if inspect.isbuiltin(o):
        return True

    try:
        src = inspect.getsourcefile(o)
    except TypeError:
        return True

    return src is None or not os.path.abspath(src).startswith(robot_path)


def print_fn_err(msg, parent, fn, errors):
    if inspect.isclass(parent):
        name = "%s.%s" % (parent.__name__, fn.__name__)
    else:
        name = "%s" % fn.__name__
    name = "%s.%s" % (parent.__name__, fn.__name__)

    err = "ERROR: %s '%s()'\n-> See %s:%s" % (
        msg,
        name,
        inspect.getsourcefile(fn),
        inspect.getsourcelines(fn)[1],
    )

    if err not in errors:
        print(err, file=sys.stderr)
        errors.append(err)


def check_function(parent, fn, errors):
    doc = inspect.getdoc(fn)

    if doc is None:
        print_fn_err("No docstring for", parent, fn, errors)

    elif pedantic_docstrings:
        # find the list of parameters
        args, varargs, keywords, defaults, _, _, annotations = inspect.getfullargspec(
            fn
        )
        if len(args) > 0 and args[0] == "self":
            del args[0]

        if varargs is not None:
            args.append(varargs)

        if keywords is not None:
            args.append(keywords)

        params = []

        for line in doc.splitlines():
            # :param arg: stuff
            match = param_re.match(line)
            if match:

                arg = match.group(1)
                if arg not in args:
                    print_fn_err(
                        "Param '%s' is documented but isn't a parameter for" % arg,
                        parent,
                        fn,
                        errors,
                    )

                if arg in annotations.keys() and isinstance(annotations.get(arg), str):
                    print_fn_err(
                        "Do not document %s in both the docstring and annotations"
                        % arg,
                        parent,
                        fn,
                        errors,
                    )

                params.append(arg)

            # :type arg: type
            match = type_re.match(line)
            if match:
                arg = match.group(1)
                if arg in annotations.keys() and isinstance(annotations.get(arg), type):
                    print_fn_err(
                        "Do not document %s in both the docstring and annotations"
                        % arg,
                        parent,
                        fn,
                        errors,
                    )

            # :param type arg: stuff
            match = both_re.match(line)
            if match:
                arg = match.group(2)
                if arg not in args:
                    print_fn_err(
                        "Param '%s' is documented but isn't a parameter for" % arg,
                        parent,
                        fn,
                        errors,
                    )

                if arg in annotations.keys() and isinstance(
                    annotations.get(arg), (str, type)
                ):
                    print_fn_err(
                        "Do not document %s in both the docstring and annotations"
                        % arg,
                        parent,
                        fn,
                        errors,
                    )

                params.append(arg)

        for param, annotation in annotations.items():
            if param not in params and isinstance(annotation, str):
                params.insert(args.index(param), param)

        if len(params) != len(args):

            diff = set(args).difference(params)

            if len(diff) == 1:
                print_fn_err(
                    "Param '%s' is not documented in docstring for" % diff.pop(),
                    parent,
                    fn,
                    errors,
                )
            elif len(diff) > 1:
                print_fn_err(
                    "Params '%s' are not documented in docstring for"
                    % "','".join(diff),
                    parent,
                    fn,
                    errors,
                )

        else:
            for param, arg in zip(params, args):
                if param != arg:
                    print_fn_err(
                        "Param '%s' is out of order, does not match param '%s' in docstring for"
                        % (param, arg),
                        parent,
                        fn,
                        errors,
                    )


def check_object(o, robot_path, errors):
    if inspect.isclass(o) and inspect.getdoc(o) is None:
        err = "ERROR: Class '%s' has no docstring!\n-> See %s:%s" % (
            o.__name__,
            inspect.getsourcefile(o),
            inspect.getsourcelines(o)[1],
        )
        print(err)
        errors.append(err)

    for name, value in inspect.getmembers(o):

        if ignore_object(value, robot_path):
            continue

        check_thing(o, value, robot_path, errors)


def check_thing(parent, thing, robot_path, errors):
    if inspect.isclass(thing):
        check_object(thing, robot_path, errors)

    elif inspect.isfunction(thing):
        check_function(parent, thing, errors)


def test_docstrings(robot, robot_path):
    """
    The purpose of this test is to ensure that all of your robot code
    has docstrings. Properly using docstrings will make your code
    more maintainable and look more professional.
    """

    # this allows abspath() to work correctly
    os.chdir(robot_path)

    errors = []

    for module in sys.modules.values():

        if ignore_object(module, robot_path):
            continue

        check_object(module, robot_path, errors)

    # if you get an error here, look at stdout for the error message
    assert len(errors) == 0
