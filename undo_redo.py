import cv2
import copy

class UndoRedoManager:
    def __init__(self, max_history=20):
        self.history = []
        self.current_index = -1
        self.max_history = max_history
    
    def add_state(self, image):
        """Add image state to history"""
        if image is None:
            return
        
        # Remove any redo states if user makes a new action
        if self.current_index < len(self.history) - 1:
            self.history = self.history[:self.current_index + 1]
        
        # Add new state
        self.history.append(image.copy())
        self.current_index += 1
        
        # Limit history size
        if len(self.history) > self.max_history:
            self.history.pop(0)
            self.current_index -= 1
    
    def undo(self):
        """Undo to previous state"""
        if self.current_index > 0:
            self.current_index -= 1
            return self.history[self.current_index].copy()
        return None
    
    def redo(self):
        """Redo to next state"""
        if self.current_index < len(self.history) - 1:
            self.current_index += 1
            return self.history[self.current_index].copy()
        return None
    
    def can_undo(self):
        """Check if undo is possible"""
        return self.current_index > 0
    
    def can_redo(self):
        """Check if redo is possible"""
        return self.current_index < len(self.history) - 1
    
    def get_current_state(self):
        """Get current state"""
        if 0 <= self.current_index < len(self.history):
            return self.history[self.current_index].copy()
        return None
    
    def clear(self):
        """Clear history"""
        self.history = []
        self.current_index = -1
