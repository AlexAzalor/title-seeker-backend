from enum import Enum
from config import config

CFG = config()


class Language(Enum):
    UK = CFG.UK
    EN = CFG.EN
