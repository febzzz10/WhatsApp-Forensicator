from pathlib import Path
from typing import Optional, Protocol, runtime_checkable


@runtime_checkable
class InspectionResult(Protocol):
    source_type: str
    is_valid: bool
    file_count: int
    warnings: list[str]
    schema_fingerprint: Optional[str]


@runtime_checkable
class ParseContext(Protocol):
    case_id: int
    evidence_item_id: int
    source_file_id: int
    working_copy_path: Path
    timezone: str


@runtime_checkable
class ParseResult(Protocol):
    message_count: int
    contact_count: int
    group_count: int
    call_count: int
    media_count: int
    warnings: list[str]
    parser_version: str
    adapter_id: str


@runtime_checkable
class ParserAdapter(Protocol):
    adapter_id: str
    adapter_version: str

    def inspect(self, source: Path) -> InspectionResult: ...

    def supports(self, inspection: InspectionResult) -> bool: ...

    def parse(self, source: Path, context: ParseContext) -> ParseResult: ...

    def capabilities(self) -> dict: ...


@runtime_checkable
class DecryptAdapter(Protocol):
    adapter_id: str
    adapter_version: str

    def identify(self, source: Path) -> float: ...

    def required_inputs(self, source: Path) -> list[str]: ...

    def validate_inputs(self, inputs: dict) -> dict: ...

    def decrypt(self, source: Path, destination: Path, inputs: dict) -> dict: ...

    def verify_output(self, destination: Path) -> dict: ...
