from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QPushButton, QWidget


class Toast(QFrame):
    def __init__(self, parent: QWidget, message: str, action_text: str = "", on_action=None):
        super().__init__(parent)
        self.setObjectName("toast")
        self.setStyleSheet("""
            #toast {
                background: #2c3e50;
                border-radius: 8px;
                padding: 12px 16px;
            }
            #toast QLabel {
                color: white;
                font-size: 13px;
            }
            #toast QPushButton {
                background: transparent;
                color: #3498db;
                border: none;
                font-weight: bold;
                font-size: 13px;
                padding: 4px 8px;
            }
            #toast QPushButton:hover {
                color: #5dade2;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        msg = QLabel(message)
        layout.addWidget(msg)

        if action_text and on_action:
            btn = QPushButton(action_text)
            btn.clicked.connect(on_action)
            layout.addWidget(btn)

        self._opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity)

    def _fade(self, start: float, end: float, duration_ms: int, on_finish=None):
        steps = 20
        interval = duration_ms // steps
        delta = (end - start) / steps
        self._cur_step = 0

        def tick():
            self._cur_step += 1
            val = start + delta * self._cur_step
            self._opacity.setOpacity(val)
            if self._cur_step >= steps:
                timer.stop()
                if on_finish:
                    on_finish()

        timer = QTimer(self)
        timer.timeout.connect(tick)
        timer.start(interval)

    def show(self):
        super().show()
        self.raise_()
        self._fade(0.0, 1.0, 200)
        QTimer.singleShot(3000, self._dismiss)

    def _dismiss(self):
        self._fade(1.0, 0.0, 300, self.deleteLater)


class ToastManager:
    _instance = None

    def __init__(self):
        self._container: QWidget | None = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def install(self, parent: QWidget):
        self._parent = parent

    def show(self, message: str, action_text: str = "", on_action=None):
        if not self._parent:
            return
        toast = Toast(self._parent, message, action_text, on_action)
        toast.setMinimumWidth(360)
        toast.adjustSize()
        pw = self._parent.width()
        tw = toast.minimumWidth()
        x = (pw - tw) // 2
        y = 16
        toast.move(x, y)
        toast.show()
