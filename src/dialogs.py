from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
                             QPushButton)
from PyQt6.QtCore import Qt, pyqtSignal

class FilterSliderDialog(QDialog):
    """A dialog with a slider to get a filter parameter, with preview signal."""
    # Signal emitted when the slider value changes, sending the correctly scaled value
    valueChangedPreview = pyqtSignal(float)
    # Signal emitted when the dialog is closed (accepted or rejected)
    previewFinished = pyqtSignal()

    def __init__(self, title, label_text, min_val, max_val, initial_val, step=1, decimals=0, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.decimals = decimals
        self.step = step # Store step for potential float conversion

        # Determine slider range based on decimals
        self.slider_min = int(min_val * (10**decimals))
        self.slider_max = int(max_val * (10**decimals))
        self.slider_initial = int(initial_val * (10**decimals))
        self.slider_step = int(step * (10**decimals)) # Slider step is always integer

        layout = QVBoxLayout(self)

        self.label = QLabel(f"{label_text}: {self._format_value(self.slider_initial)}")
        layout.addWidget(self.label)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(self.slider_min, self.slider_max)
        self.slider.setValue(self.slider_initial)
        self.slider.setSingleStep(self.slider_step)
        self.slider.setTickInterval(self.slider_step * 10) # Example tick interval
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider.valueChanged.connect(self._update_label_and_emit) # Connect to new method
        layout.addWidget(self.slider)

        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("Tamam")
        self.cancel_button = QPushButton("İptal")
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        # Emit previewFinished when the dialog closes
        self.finished.connect(self.previewFinished.emit) # Connect built-in finished signal

    def _update_label_and_emit(self, value):
        """Updates the label and emits the valueChangedPreview signal."""
        formatted_value = self._format_value(value)
        self.label.setText(f"{self.label.text().split(':')[0]}: {formatted_value}")
        # Emit the correctly scaled value
        if self.decimals == 0:
            self.valueChangedPreview.emit(float(value))
        else:
            self.valueChangedPreview.emit(value / (10**self.decimals))

    def _format_value(self, value):
        """Formats the integer slider value back to the original scale."""
        float_value = value / (10**self.decimals)
        return f"{float_value:.{self.decimals}f}"

    def get_value(self):
        """Returns the selected value in the original scale (float or int)."""
        slider_value = self.slider.value()
        if self.decimals == 0:
            return slider_value # Return as integer
        else:
            return slider_value / (10**self.decimals) # Return as float
