"""
Created on Aug 2, 2015
From: https://github.com/izderadicka/xmpp-tester/blob/master/commander.py
@author: ivan
"""

from collections import deque
import inspect
import re
import threading
import urwid

import elkm1.message


def parse_range(rng, max):
    # e.g. rng = "<3, 45, 46, 48-51, 77"
    if rng.strip() == '*':
        return range(0, max)
    ids = []
    for x in map(str.strip,rng.split(',')):
        if x.isdigit():
            ids.append(int(x))
        elif x[0] == '<':
            ids.extend(range(0,int(x[1:])))
        elif '-' in x:
            xr = [s.strip() for s in x.split('-')]
            ids.extend(range(int(xr[0]),int(xr[1])+1))
        else:
            raise ValueError('Unknown range type: "%s"'%x)
    return ids

class UnknownCommand(Exception):
    def __init__(self,cmd):
        Exception.__init__(self,'Uknown command: %s'%cmd)

class Command(object):
    """Base class to manage commands."""

    def __init__(self):
        self._quit_cmd = ['q', 'quit', 'exit']
        self._help_cmd = ['?', 'help', 'h']

        self.encoders = {}
        for fn_name, fn in inspect.getmembers(elkm1.message, inspect.isfunction):
            if not fn_name.endswith('_encode'):
                continue
            self.encoders[fn_name[0:2]] = fn

    def __call__(self,line):
        tokens=line.split()
        cmd=tokens[0].lower()
        args=tokens[1:]

        if cmd in self._quit_cmd:
            return Commander.Exit

        if cmd in self._help_cmd:
            return self.help(args[0] if args else None)

        if hasattr(self, 'do_'+cmd):
            print("#blue#{:s} {:s}".format(cmd, ' '.join(args)))
            return getattr(self, 'do_'+cmd)(*args)

        if cmd in self.encoders:
            converted = []
            for arg in args:
                try:
                    i = int(arg)
                    converted.append(i)
                except ValueError:
                    converted.append(arg)
            print("#blue#{:s} {:s}".format(cmd, ' '.join(args)))
            self.encoder(self.encoders[cmd], *converted)
        else:
            raise UnknownCommand(cmd)

    def help(self,cmd=None):
        def std_help():
            qc='|'.join(self._quit_cmd)
            hc ='|'.join(self._help_cmd)

            res='#green#Type [%s] to get more help about particular command\n' % hc
            res+='Type [%s] to quit program\n' % qc

            cl = [name[3:] for name in dir(self) if name.startswith('do_')]
            cl += [fnname for fnname in self.encoders]
            res += 'Available commands: %s' %(' '.join(sorted(cl)))
            return res

        if not cmd:
            return std_help()
        else:
            if cmd in self.encoders:
                params = [p for p in inspect.signature(self.encoders[cmd]).parameters]
                doc = "#green#{:s} {:s}\n".format(cmd, " ".join(params))
                doc += self.encoders[cmd].__doc__
                return doc
            else:
                try:
                    fn=getattr(self,'do_'+cmd)
                    doc=fn.__doc__
                    return doc or '#red#No documentation available for %s'%cmd
                except AttributeError:
                    return std_help()
 
class ElkCommands(Command):
    def set_elk(self, elk):
        self.elk = elk

    def do_raw(self, *args):
        """raw - send bytes typed to Elk"""
        self.elk.send(elkm1.message.MessageEncode(args[0], None))

    def display_objects(self, object_list, *args):
        for i in parse_range(" ".join(args), object_list.max_elements):
            print(object_list[i])

    def do_zone(self, *args):
        self.display_objects(self.elk.zones, *args)
    def do_light(self, *args):
        self.display_objects(self.elk.lights, *args)
    def do_area(self, *args):
        self.display_objects(self.elk.areas, *args)
    def do_keypad(self, *args):
        self.display_objects(self.elk.keypads, *args)
    def do_user(self, *args):
        self.display_objects(self.elk.users, *args)
    def do_task(self, *args):
        self.display_objects(self.elk.tasks, *args)
    def do_output(self, *args):
        self.display_objects(self.elk.outputs, *args)
    def do_setting(self, *args):
        self.display_objects(self.elk.settings, *args)
    def do_counter(self, *args):
        self.display_objects(self.elk.counters, *args)
    def do_thermostat(self, *args):
        self.display_objects(self.elk.thermostats, *args)
    def do_panel(self, *args):
        print(self.elk.panel)
    def encoder(self, fn, *args):
        self.elk.send(fn(*args))

class FocusMixin(object):
    def mouse_event(self, size, event, button, x, y, focus):
        if focus and hasattr(self, '_got_focus') and self._got_focus:
            self._got_focus()
        return super(FocusMixin,self).mouse_event(size, event, button, x, y, focus)

class ListView(FocusMixin, urwid.ListBox):
    def __init__(self, model, got_focus, max_size=None):
        urwid.ListBox.__init__(self,model)
        self._got_focus=got_focus
        self.max_size=max_size
        self._lock=threading.Lock()

    def mouse_event(self, size, event, button, x, y, focus):
        direction = 'up' if button == 4 else 'down'
        return super(ListView,self).keypress(size, direction)

    def add(self,line):
        with self._lock:
            was_on_end=self.get_focus()[1] == len(self.body)-1
            if self.max_size and len(self.body)>self.max_size:
                del self.body[0]
            self.body.append(urwid.Text(line))
            last=len(self.body)-1
            if was_on_end:
                self.set_focus(last,'above')

class Input(FocusMixin, urwid.Edit):
    signals=['line_entered']
    def __init__(self, got_focus=None):
        urwid.Edit.__init__(self)
        self.history=deque(maxlen=1000)
        self._history_index=-1
        self._got_focus=got_focus

    def keypress(self, size, key):
        if key=='enter':
            line=self.edit_text.strip()
            if line:
                urwid.emit_signal(self,'line_entered', line)
                self.history.append(line)
            self._history_index=len(self.history)
            self.edit_text=u''
        if key=='up':
            self._history_index-=1
            if self._history_index< 0:
                self._history_index= 0
            else:
                self.edit_text=self.history[self._history_index]
        if key=='down':
            self._history_index+=1
            if self._history_index>=len(self.history):
                self._history_index=len(self.history) 
                self.edit_text=u''
            else:
                self.edit_text=self.history[self._history_index]
        else:
            urwid.Edit.keypress(self, size, key)

class Commander(urwid.Frame):
    """Simple terminal UI with command input on bottom line and display
       frame above similar to chat client etc. Initialize with your
       Command instance to execute commands and the start main loop
       Commander.loop(). You can also asynchronously output messages
       with Commander.output('message') """

    class Exit(object):
        pass

    PALLETE=[('reversed', urwid.BLACK, urwid.LIGHT_GRAY),
              ('normal', urwid.LIGHT_GRAY, urwid.BLACK),
              ('error', urwid.LIGHT_RED, urwid.BLACK),
              ('green', urwid.DARK_GREEN, urwid.BLACK),
              ('blue', urwid.LIGHT_BLUE, urwid.BLACK),
              ('magenta', urwid.DARK_MAGENTA, urwid.BLACK), ]

    def __init__(self, title, command_caption='Command:  (Tab to switch focus to upper frame, where you can scroll text)', cmd_cb=None, max_size=1000):
        self.header=urwid.Text(title)
        self.model=urwid.SimpleListWalker([])
        self.body=ListView(self.model, lambda: self._update_focus(False),
                           max_size=max_size )
        self.input=Input(lambda: self._update_focus(True))
        foot=urwid.Pile([urwid.AttrMap(urwid.Text(command_caption), 'reversed'),
                        urwid.AttrMap(self.input,'normal')])
        urwid.Frame.__init__(self, 
                             urwid.AttrWrap(self.body, 'normal'),
                             urwid.AttrWrap(self.header, 'reversed'),
                             foot)
        self.set_focus_path(['footer',1])
        self._focus=True
        urwid.connect_signal(self.input,'line_entered',self.on_line_entered)
        self._cmd=cmd_cb
        self._output_styles=[s[0] for s in self.PALLETE]
        self.eloop=None

    def loop(self, handle_mouse=False):
        # self.eloop=urwid.MainLoop(self, self.PALLETE, handle_mouse=handle_mouse)
        # self._eloop_thread=threading.current_thread()
        # self.eloop.run()
        import asyncio
        evl = urwid.AsyncioEventLoop(loop=asyncio.get_event_loop())
        self.eloop = urwid.MainLoop(self, self.PALLETE, event_loop=evl, handle_mouse=True)
        self._eloop_thread=threading.current_thread()
        self.eloop.run()

    def on_line_entered(self,line):
        if self._cmd:
            try:
                res = self._cmd(line)
            except Exception as e:
                self.output('Error: %s'%e, 'error')
                return
            if res==Commander.Exit:
                raise urwid.ExitMainLoop()
            elif res:
                self.output(str(res))
        else:
            if line in ('q','quit','exit'):
                raise urwid.ExitMainLoop()
            else:
                self.output(line)

    def output(self, line, style=None):
        match = re.search(r'^#(\w+)#(.*)', line, re.DOTALL)
        if match and match.group(1) in self._output_styles:
            line = (match.group(1), match.group(2))
        elif style and style in self._output_styles:
            line=(style,line) 
        self.body.add(line)

        # since output could be called asynchronously form other threads 
        # we need to refresh screen in these cases
        if self.eloop and self._eloop_thread != threading.current_thread():
            self.eloop.draw_screen()

    def _update_focus(self, focus):
        self._focus=focus

    def switch_focus(self):
        if self._focus:
            self.set_focus('body')
            self._focus=False
        else:
            self.set_focus_path(['footer',1])
            self._focus=True

    def keypress(self, size, key):
        if key=='tab':
            self.switch_focus()
        return urwid.Frame.keypress(self, size, key)
