import dataclasses
from typing import Any, Dict, List, Optional

from cubox_to_notion.notionfier.api.common_objects import ExternalFile, RichText, TextColor
from cubox_to_notion.notionfier.api.consts import CodeLanguage
from cubox_to_notion.notionfier.api.utils import NotionObject


@dataclasses.dataclass
class BlockObject(NotionObject):
    pass


@dataclasses.dataclass
class Paragraph(BlockObject):
    @dataclasses.dataclass
    class Content:
        rich_text: List[RichText]
        children: Optional[List["BlockObject"]] = None
        color: TextColor = TextColor.default

    paragraph: Content


@dataclasses.dataclass
class Heading1(BlockObject):
    @dataclasses.dataclass
    class Content:
        rich_text: List[RichText]
        color: TextColor = TextColor.default

    heading_1: Content


@dataclasses.dataclass
class Heading2(BlockObject):
    @dataclasses.dataclass
    class Content:
        rich_text: List[RichText]
        color: TextColor = TextColor.default

    heading_2: Content


@dataclasses.dataclass
class Heading3(BlockObject):
    @dataclasses.dataclass
    class Content:
        rich_text: List[RichText]
        color: TextColor = TextColor.default

    heading_3: Content


# todo: Callout blocks


@dataclasses.dataclass
class Quote(BlockObject):
    @dataclasses.dataclass
    class Content:
        rich_text: List[RichText]
        color: TextColor = TextColor.default
        children: Optional[List["BlockObject"]] = None

    quote: Content


@dataclasses.dataclass
class BulletedListItem(BlockObject):
    @dataclasses.dataclass
    class Content:
        rich_text: List[RichText]
        children: Optional[List["BlockObject"]] = None
        color: TextColor = TextColor.default

    bulleted_list_item: Content


@dataclasses.dataclass
class NumberedListItem(BlockObject):
    @dataclasses.dataclass
    class Content:
        rich_text: List[RichText]
        children: Optional[List["BlockObject"]] = None
        color: TextColor = TextColor.default

    numbered_list_item: Content


@dataclasses.dataclass
class Todo(BlockObject):
    @dataclasses.dataclass
    class Content:
        rich_text: List[RichText]
        checked: bool
        children: Optional[List["BlockObject"]] = None
        color: TextColor = TextColor.default

    to_do: Content


@dataclasses.dataclass
class Code(BlockObject):
    @dataclasses.dataclass
    class Content:
        rich_text: List[RichText]
        caption: Optional[List[RichText]] = None
        language: CodeLanguage = CodeLanguage.plain_text

    code: Content


@dataclasses.dataclass
class Image(BlockObject):
    @dataclasses.dataclass
    class Content:
        external: ExternalFile
        caption: List[RichText] = dataclasses.field(default_factory=lambda: [])

    image: Content


@dataclasses.dataclass
class Equation(BlockObject):
    @dataclasses.dataclass
    class Content:
        expression: str

    equation: Content


@dataclasses.dataclass
class Divider(BlockObject):
    divider: Dict[str, Any] = dataclasses.field(default_factory=lambda: {})


@dataclasses.dataclass
class TableRow(NotionObject):
    @dataclasses.dataclass
    class Content:
        cells: List[List[RichText]]

    table_row: Content


@dataclasses.dataclass
class Table(BlockObject):
    @dataclasses.dataclass
    class Content:
        table_width: int
        has_column_header: bool
        has_row_header: bool
        children: List[TableRow]

    table: Content
