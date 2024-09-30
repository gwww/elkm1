"""
Created on Aug 2, 2015
From: https://github.com/izderadicka/xmpp-tester/blob/master/commander.py
@author: ivan
"""

import inspect
import re
import threading
import traceback
from collections import deque
from importlib import import_module

import attr
import urwid

import elkm1_lib.message


@attr.s
class Command:
    function = attr.ib()
    help = attr.ib()
    docs = attr.ib()


def parse_subcommand(line):
    tokens = line.split()
    if len(tokens) == 0:
        return (None, None)
    cmd = tokens[0].lower()
    args = tokens[1:]

    converted = []
    for arg in args:
        try:
            i = int(arg)
            converted.append(i)
        except ValueError:
            converted.append(arg)
    return (cmd, converted)


def parse_range(rng, max):
    # e.g. rng = "<3, 45, 46, 48-51, 77"
    if rng.strip() == "*":
        return range(0, max)
    ids = []
    for x in map(str.strip, rng.split(",")):
        if x.isdigit():
            ids.append(int(x))
        elif x[0] == "<":
            ids.extend(range(0, int(x[1:])))
        elif "-" in x:
            xr = [s.strip() for s in x.split("-")]
            ids.extend(range(int(xr[0]), int(xr[1]) + 1))
        else:
            raise ValueError(f'Unknown range type: "{x}"')
    return ids


def parse_element_command(cmd, line, max):
    match = re.match("([\\d,\\- <*]+)(\\w*.*)", line)
    if match:
        ids = parse_range(match.groups()[0], max)
        subcommand = parse_subcommand(match.groups()[1])
        return (ids, subcommand[0], subcommand[1])
    return None


def find_class(module, class_name):
    for class_ in inspect.getmembers(module, inspect.isclass):
        if class_[0] == class_name:
            return class_
    return None


def get_helpers(element, clas):
    helpers = {}
    class_ = find_class(import_module("elkm1_lib." + element), clas)
    if class_:
        for function_name, fn in inspect.getmembers(class_[1], inspect.isfunction):
            if fn.__doc__ and fn.__doc__.startswith("(Helper)"):
                params = [p for p in inspect.signature(fn).parameters]
                if params[0] == "self":
                    del params[0]
                params = " ".join(["<" + p + ">" for p in params])
                helpers[function_name] = (
                    fn,
                    f"{function_name} {params}",
                    fn.__doc__[8:],
                )
    return helpers


class Commands:
    def __init__(self, elk):
        self.elk = elk

        self._quit_cmd = ["q", "quit", "exit"]
        self._help_cmd = ["?", "help", "h"]

        self.encode_cmds = {}
        for fn_name, fn in inspect.getmembers(elkm1_lib.message, inspect.isfunction):
            if not fn_name.endswith("_encode"):
                continue
            cmd = fn_name[0:2]
            params = [p for p in inspect.signature(fn).parameters]
            params = " ".join(["<" + p + ">" for p in params])
            self.encode_cmds[cmd] = Command(fn, f"{cmd} {params}", fn.__doc__)

        self.element_cmds = {}
        self.subcommands = {}
        for element in elk.element_list:
            if element == "panel":
                fn = self.panel_print
                cmd = element
            else:
                fn = self.print_elements
                cmd = element[:-1]
            self.element_cmds[cmd] = (
                fn,
                f"{cmd} <range list> [subcommand]",
                f"Displays internal state of {element}",
                get_helpers(element, cmd.capitalize()),
            )

    def __call__(self, line):
        tokens = line.split()
        cmd = tokens[0].lower()
        args = tokens[1:]

        if cmd in self._quit_cmd:
            return Commander.Exit

        print(f"#blue#{line}")

        if cmd in self._help_cmd:
            return self.help(cmd, args)

        if cmd in self.encode_cmds:
            return self.encoder(cmd, args)

        if cmd == "recv":
            return self.elk._got_data(" ".join(args))

        if cmd in self.element_cmds:
            return self.element_cmds[cmd][0](cmd, args)

        return f"#error#Unknown command: {cmd}"

    def help(self, cmd, args):
        if len(args) == 0:
            res = '#green#Type "[?|h|help] <command>" to get more help\n'
            res += 'Type "[q|quit|exit]" to quit program\n'
            res += "Element display commands:\n  {}\n\n".format(
                " ".join(list(self.element_cmds.keys()))
            )
            cl = [fnname for fnname in self.encode_cmds]
            res += "Send message commands:\n  {}\n".format(" ".join(sorted(cl)))
        else:
            help_for = args[0]
            if help_for in self.encode_cmds:
                command = self.encode_cmds[help_for]
                res = f"#green#{command.help}\n{command.docs}"

            elif help_for in self.element_cmds:
                res = (
                    f"#green#{self.element_cmds[help_for][1]}\n"
                    f"{self.element_cmds[help_for][2]}"
                )
                for _k, v in self.element_cmds[help_for][3].items():
                    res += f"\nSubcommand: {v[1]}\n{v[2]}"
            else:
                res = f"#error#Unknown command: {help_for}"
        return res

    def print_elements(self, cmd, args):
        element_list = getattr(self.elk, cmd + "s", None)
        if element_list is None:
            print("Command not supported.")
            return

        args = parse_element_command(cmd, " ".join(args), element_list.max_elements)
        if args is None:
            print("Cannot parse command.")
            return

        if args[1]:
            if args[1] in self.element_cmds[cmd][3]:
                fn = self.element_cmds[cmd][3][args[1]][0]
            else:
                raise NotImplementedError
            for i in args[0]:
                print(fn)
                fn(element_list[i], *args[2])
        else:
            for i in args[0]:
                print(element_list[i])

    def panel_print(self, cmd, args):
        print(self.elk.panel)

    def encoder(self, cmd, args):
        converted = []
        for arg in args:
            try:
                i = int(arg)
                converted.append(i)
            except ValueError:
                converted.append(arg)
        self.elk.send(self.encode_cmds[cmd].function(*converted))


class FocusMixin:
    def mouse_event(self, size, event, button, x, y, focus):
        if focus and hasattr(self, "_got_focus") and self._got_focus:
            self._got_focus()
        return super().mouse_event(size, event, button, x, y, focus)


class ListView(FocusMixin, urwid.ListBox):
    def __init__(self, model, got_focus, max_size=None):
        urwid.ListBox.__init__(self, model)
        self._got_focus = got_focus
        self.max_size = max_size
        self._lock = threading.Lock()

    def mouse_event(self, size, event, button, x, y, focus):
        direction = "up" if button == 4 else "down"
        return super().keypress(size, direction)

    def add(self, line):
        with self._lock:
            was_on_end = self.get_focus()[1] == len(self.body) - 1
            if self.max_size and len(self.body) > self.max_size:
                del self.body[0]
            self.body.append(urwid.Text(line))
            last = len(self.body) - 1
            if was_on_end:
                self.set_focus(last, "above")


class Input(FocusMixin, urwid.Edit):
    signals = ["line_entered"]

    def __init__(self, got_focus=None):
        urwid.Edit.__init__(self)
        self.history = deque(maxlen=1000)
        self._history_index = -1
        self._got_focus = got_focus

    def keypress(self, size, key):
        if key == "enter":
            line = self.edit_text.strip()
            if line:
                urwid.emit_signal(self, "line_entered", line)
                self.history.append(line)
            self._history_index = len(self.history)
            self.edit_text = ""
        if key == "up":
            self._history_index -= 1
            if self._history_index < 0:
                self._history_index = 0
            else:
                self.edit_text = self.history[self._history_index]
        if key == "down":
            self._history_index += 1
            if self._history_index >= len(self.history):
                self._history_index = len(self.history)
                self.edit_text = ""
            else:
                self.edit_text = self.history[self._history_index]
        else:
            urwid.Edit.keypress(self, size, key)


class Commander(urwid.Frame):
    """Simple terminal UI with command input on bottom line and display
    frame above similar to chat client etc. Initialize with your
    Command instance to execute commands and the start main loop
    Commander.loop(). You can also asynchronously output messages
    with Commander.output('message')"""

    class Exit:
        pass

    PALLETE = [
        ("reversed", urwid.BLACK, urwid.LIGHT_GRAY),
        ("normal", urwid.LIGHT_GRAY, urwid.BLACK),
        ("error", urwid.LIGHT_RED, urwid.BLACK),
        ("green", urwid.DARK_GREEN, urwid.BLACK),
        ("blue", urwid.LIGHT_BLUE, urwid.BLACK),
        ("magenta", urwid.DARK_MAGENTA, urwid.BLACK),
    ]

    def __init__(
        self,
        title,
        command_caption="Command:  (Tab to switch focus to upper frame)",
        cmd_cb=None,
        max_size=1000,
    ):
        self.header = urwid.Text(title)
        self.model = urwid.SimpleListWalker([])
        self.body = ListView(
            self.model, lambda: self._update_focus(False), max_size=max_size
        )
        self.input = Input(lambda: self._update_focus(True))
        foot = urwid.Pile(
            [
                urwid.AttrMap(urwid.Text(command_caption), "reversed"),
                urwid.AttrMap(self.input, "normal"),
            ]
        )
        urwid.Frame.__init__(
            self,
            urwid.AttrWrap(self.body, "normal"),
            urwid.AttrWrap(self.header, "reversed"),
            foot,
        )
        self.set_focus_path(["footer", 1])
        self._focus = True
        urwid.connect_signal(self.input, "line_entered", self.on_line_entered)
        self._cmd = cmd_cb
        self._output_styles = [s[0] for s in self.PALLETE]
        self.eloop = None

    def loop(self, handle_mouse=False):
        # self.eloop=urwid.MainLoop(self, self.PALLETE, handle_mouse=handle_mouse)
        # self._eloop_thread=threading.current_thread()
        # self.eloop.run()
        import asyncio

        evl = urwid.AsyncioEventLoop(loop=asyncio.get_event_loop())
        self.eloop = urwid.MainLoop(
            self, self.PALLETE, event_loop=evl, handle_mouse=True
        )
        self._eloop_thread = threading.current_thread()
        self.eloop.run()

    def on_line_entered(self, line):
        if self._cmd:
            try:
                res = self._cmd(line)
            except Exception as e:
                traceback.print_exc()
                self.output(f"Error: {e}", "error")
                return
            if res == Commander.Exit:
                raise urwid.ExitMainLoop()
            elif res:
                self.output(str(res))
        else:
            if line in ("q", "quit", "exit"):
                raise urwid.ExitMainLoop()
            else:
                self.output(line)

    def output(self, line, style=None):
        match = re.search(r"^#(\w+)#(.*)", line, re.DOTALL)
        if match and match.group(1) in self._output_styles:
            line = (match.group(1), match.group(2))
        elif style and style in self._output_styles:
            line = (style, line)
        self.body.add(line)

        # since output could be called asynchronously form other threads
        # we need to refresh screen in these cases
        if self.eloop and self._eloop_thread != threading.current_thread():
            self.eloop.draw_screen()

    def _update_focus(self, focus):
        self._focus = focus

    def switch_focus(self):
        if self._focus:
            self.set_focus("body")
            self._focus = False
        else:
            self.set_focus_path(["footer", 1])
            self._focus = True

    def keypress(self, size, key):
        if key == "tab":
            self.switch_focus()
        return urwid.Frame.keypress(self, size, key)
