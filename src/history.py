from collections import deque

class Command:
    def __init__(self, do_func, undo_func, description):
        self.do_func = do_func
        self.undo_func = undo_func
        self.description = description
    def do(self):
        self.do_func()
    def undo(self):
        self.undo_func()

class History:
    def __init__(self, max_size=50):
        self.undo_stack = deque(maxlen=max_size)
        self.redo_stack = deque(maxlen=max_size)
    def push(self, command):
        self.undo_stack.append(command)
        self.redo_stack.clear()
    def undo(self):
        if self.undo_stack:
            cmd = self.undo_stack.pop()
            cmd.undo()
            self.redo_stack.append(cmd)
    def redo(self):
        if self.redo_stack:
            cmd = self.redo_stack.pop()
            cmd.do()
            self.undo_stack.append(cmd)
    def can_undo(self):
        return len(self.undo_stack) > 0
    def can_redo(self):
        return len(self.redo_stack) > 0
