import dataclasses
from typing import Optional

from cubox_to_notion.notionfier.api.consts import TextColor
from cubox_to_notion.notionfier.api.utils import NotionObject


# Rich text objects
@dataclasses.dataclass
class Annotation(NotionObject):
    bold: Optional[bool] = False
    italic: Optional[bool] = False
    strikethrough: Optional[bool] = False
    underline: Optional[bool] = False
    code: Optional[bool] = False
    color: Optional[TextColor] = None


@dataclasses.dataclass
class RichText(NotionObject):
    annotations: Optional[Annotation] = None


@dataclasses.dataclass
class LinkObject(NotionObject):
    url: str


@dataclasses.dataclass
class Text(RichText):
    @dataclasses.dataclass
    class Content:
        content: str
        link: Optional[LinkObject] = None

    text: Content = Content(content="")


@dataclasses.dataclass
class ExternalFile(NotionObject):
    url: str


# todo: Mention object
# todo: Equation object
# todo: Link preview mention object
