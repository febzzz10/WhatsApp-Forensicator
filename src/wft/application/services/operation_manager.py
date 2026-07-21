from typing import Optional
from PySide6.QtCore import QObject, Signal


class Operation(QObject):
    status_changed = Signal(str)

    def __init__(self, op_id: str, name: str, page: str = "") -> None:
        super().__init__()
        self.op_id = op_id
        self.name = name
        self.page = page
        self._running = False

    @property
    def running(self) -> bool:
        return self._running

    def start(self) -> None:
        self._running = True
        self.status_changed.emit("started")

    def complete(self) -> None:
        self._running = False
        self.status_changed.emit("completed")

    def fail(self) -> None:
        self._running = False
        self.status_changed.emit("failed")


class OperationManager(QObject):
    def __init__(self) -> None:
        super().__init__()
        self._operations: dict[str, Operation] = {}

    def start(self, op_id: str, name: str, page: str = "") -> Operation:
        if op_id in self._operations and self._operations[op_id].running:
            return self._operations[op_id]
        op = Operation(op_id, name, page)
        op.start()
        self._operations[op_id] = op
        return op

    def complete(self, op_id: str) -> None:
        op = self._operations.get(op_id)
        if op:
            op.complete()

    def fail(self, op_id: str) -> None:
        op = self._operations.get(op_id)
        if op:
            op.fail()

    @property
    def active_count(self) -> int:
        return sum(1 for op in self._operations.values() if op.running)

    @property
    def active_operations(self) -> list[Operation]:
        return [op for op in self._operations.values() if op.running]

    def is_running(self, op_id: str) -> bool:
        op = self._operations.get(op_id)
        return op is not None and op.running

    def clear_completed(self) -> None:
        self._operations = {
            k: v for k, v in self._operations.items() if v.running
        }
