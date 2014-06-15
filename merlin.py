""" This module allows you to analyse OCaml source code, autocomplete and infer types while writing """

import subprocess
import functools
import sublime
import sublime_plugin
import re

from .process import MerlinProcess, merlin_bin
from .helpers import merlin_pos, only_ocaml


merlin_processes = {}


def merlin_process(name):
    global merlin_processes
    if name is None:
        name = ''

    if name not in merlin_processes:
        merlin_processes[name] = MerlinProcess()
        merlin_processes[name].project_find(name)
        merlin_processes[name].reset(name=name)

    return merlin_processes[name]


class MerlinLoadProject(sublime_plugin.WindowCommand):
    """
    Command to reload .merlin file from current project.
    """
    def run(self):
        """ Load the project from the view of the active window. """
        view = self.window.active_view()
        merlin_process(view.file_name()).project_load(view.file_name())


class MerlinLoadModule(sublime_plugin.WindowCommand):
    """
    Command to find modules and load them into the current view.
    """

    def run(self):
        view = self.window.active_view()
        self.process = merlin_process(view.file_name())

        self.modules = self.process.find_list()
        self.window.show_quick_panel(self.modules, self.on_complete)

    def on_complete(self, index):
        self.process.find_use(self.modules[index])


class Autocomplete(sublime_plugin.EventListener):
    """
    Sublime Text autocompletion integration
    """

    completions = []
    cplns_ready = None

    @only_ocaml
    def on_query_completions(self, view, prefix, locations):
        """ Sublime autocomplete event handler. """

        # Expand the prefix with dots
        l = locations[0]
        line = view.substr(sublime.Region(view.line(l).a, l))
        prefix = re.findall(r"(([\w.]|->)+)", line)[-1][0]

        process = merlin_process(view.file_name())
        process.sync_buffer_to_cursor(view)

        default_return = ([], sublime.INHIBIT_WORD_COMPLETIONS)

        if self.cplns_ready:
            self.cplns_ready = None
            if self.completions:
                cplns, self.completions = self.completions, []
                return cplns

            return default_return

        if self.cplns_ready is None:
            self.cplns_ready = False
            line, col = view.rowcol(locations[0])
            result = process.complete_cursor(prefix, line + 1, col)
            self.cplns = [(r['name'] + '\t' + r['desc'], r['name']) for r in result]

            self.show_completions(view, self.cplns)

        return default_return

    @only_ocaml
    def show_completions(self, view, completions):
        self.cplns_ready = True
        if completions:
            self.completions = completions
            view.run_command("hide_auto_complete")
            sublime.set_timeout(functools.partial(self.show, view), 0)

    @only_ocaml
    def show(self, view):
        view.run_command("auto_complete", {
            'disable_auto_insert': True,
            'api_completions_only': True,
            'next_completion_if_showing': False,
            'auto_complete_commit_on_tab': True,
        })


class MerlinBuffer(sublime_plugin.EventListener):
    """
    Synchronize the current buffer with Merlin and:
     - autocomplete words with type informations;
     - display errors in the gutter.
    """

    _process = None
    error_messages = []

    def process(self, view):
        if not self._process:
            self._process = merlin_process(view.file_name())
        return self._process

    @only_ocaml
    def on_activated(self, view):
        """
        Create a Merlin process if necessary and load imported modules.
        """

        self.show_errors(view)

    @only_ocaml
    def on_post_save(self, view):
        """
        Sync the buffer with Merlin on each text edit.
        """

        self.process(view).sync_buffer(view)  # Dummy sync with the whole file
        self.display_to_status_bar(view)
        self.show_errors(view)

    @only_ocaml
    def on_modified(self, view):
        view.erase_regions('ocaml-underlines-errors')

    def show_errors(self, view):
        """
        Show a simple gutter icon for each parsing error.
        """

        view.erase_regions('ocaml-underlines-errors')

        errors = self.process(view).report_errors()

        error_messages = []
        underlines = []

        for e in errors:
            pos_start = e['start']
            pos_stop = e['end']
            pnt_start = merlin_pos(view, pos_start)
            pnt_stop = merlin_pos(view, pos_stop)
            r = sublime.Region(pnt_start, pnt_stop)
            line_r = view.full_line(r)
            line_r.a -= 1
            underlines.append(r)

            # Remove line and character number
            message = e['message']

            error_messages.append((line_r, message))

        self.error_messages = error_messages
        flag = sublime.DRAW_OUTLINED
        view.add_regions('ocaml-underlines-errors', underlines, scope='ocaml-underlines-errors', icon='dot', flags=flag)

    @only_ocaml
    def on_selection_modified(self, view):
        self.display_to_status_bar(view)

    def display_to_status_bar(self, view):
        """
        Display error message to the status bar when the selection intersects
        with errors in the current view.
        """

        caret_region = view.sel()[0]

        for message_region, message_text in self.error_messages:
            if message_region.intersects(caret_region):
                sublime.status_message(message_text)
                return
            else:
                sublime.status_message('')
