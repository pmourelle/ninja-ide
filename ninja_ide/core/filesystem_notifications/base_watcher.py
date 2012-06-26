# -*- coding: utf-8 -*-
#
# This file is part of NINJA-IDE (http://ninja-ide.org).
#
# NINJA-IDE is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# any later version.
#
# NINJA-IDE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NINJA-IDE; If not, see <http://www.gnu.org/licenses/>.
import os
from PyQt4.QtCore import QObject
from PyQt4.QtCore import SIGNAL, QThread
import time

ADDED = 1
MODIFIED = 2
DELETED = 3
RENAME = 4
REMOVE = 5


def do_stat(self, file_path):
    status = None
    try:
        status = os.stat(file_path)
    except OSError:
        pass
    return status


class SingleFileWatcher(QThread):
    def __init__(self, callback):
        self._watches = dict()
        self._do_run = True
        self._emit_call = callback

    def stop_running(self):
        self._do_run = False

    def add_watch(self, file_to_watch):
        status = do_stat(file_to_watch)
        #only add if the file still exists
        if (file_to_watch not in self._watches) and status:
            self._watches[file_to_watch] = do_stat(file_to_watch)

    def del_watch(self, file_to_unwatch):
        if file_to_unwatch in self._watches:
            self._watches.pop(file_to_unwatch)

    def tick(self):
        keys = self._watches.keys()
        for each_file in keys:
            status = do_stat(each_file)
            if not status:
                self._emit_call(DELETED, each_file)
                self.del_watch(each_file)
            if status.st_mtime > self._watches[each_file].st_mtime:
                self._emit_call(MODIFIED, each_file)

    def run(self):
        while self._do_run:
            self.tick()
            time.sleep(1)


class BaseWatcher(QObject):

###############################################################################
# SIGNALS
#
# fileChanged(int, QString)  [added, deleted, modified, rename, remove]
###############################################################################

    def __init__(self):
        self._file_watcher = SingleFileWatcher(self._emit_signal_on_change)
        super(BaseWatcher, self).__init__()
        self._file_watcher.start()

    def add_file_watch(self, file_path):
        self._file_watcher.add_watch(file_path)

    def remove_file_watch(self, file_path):
        self._file_watcher.remove_file_watch(file_path)

    def shutdown_notification(self):
        self._file_watcher.stop_running()
        self._file_watcher.quit()

    def _emit_signal_on_change(self, event, path):
        self.emit(SIGNAL("fileChanged(int, QString)"), event, path)
