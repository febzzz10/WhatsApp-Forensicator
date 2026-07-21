from collections.abc import Collection
from PySide6.QtWidgets import QWidget


def refresh_style(widget: QWidget) -> None:
    style = widget.style()
    if style is not None:
        style.unpolish(widget)
        style.polish(widget)
    widget.update()


def set_dynamic_property(
    widget: QWidget,
    name: str,
    value: object,
    *,
    allowed_values: Collection[object] | None = None,
    default_value: object | None = None,
) -> object:
    if allowed_values is not None and value not in allowed_values:
        value = default_value
    if widget.property(name) == value:
        return value
    widget.setProperty(name, value)
    refresh_style(widget)
    return value
