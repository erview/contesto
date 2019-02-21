# coding: utf-8
import inspect
import logging
import sys

from contesto import config
from functools import reduce


LOG_FORMAT = "[%(asctime)s] %(process_c)s %(levelname)s %(session_id)s: %(message)s"


BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1m\033[38;5;%dm"
BOLD_SEQ = "\033[1m"

LEVEL_COLORS = {
    'WARNING': YELLOW,
    'INFO': WHITE,
    'DEBUG': BLUE,
    'CRITICAL': MAGENTA,
    'ERROR': RED
}

HIGHLIGHTS = range(20, 159)


class ColoredFormatter(logging.Formatter):

    def __init__(self, msg, use_color = True):
        logging.Formatter.__init__(self, msg)
        self.use_color = use_color

    def colorize(self, msg, color_id=WHITE):
        return COLOR_SEQ % color_id + str(msg) + RESET_SEQ

    def format(self, record):
        if self.use_color:
            levelname = record.levelname
            process = record.process

            hl_color_count = len(HIGHLIGHTS)
            if levelname in LEVEL_COLORS:
                levelname_color = self.colorize(levelname, LEVEL_COLORS[levelname])
                record.levelname = levelname_color

            if process:
                color_id = HIGHLIGHTS[int(process) % hl_color_count]
                record.process_c = self.colorize(process, color_id)

            if record.session_id:
                str_hash = reduce(lambda c, x: c + ord(x), record.session_id, 0)
                color_id = HIGHLIGHTS[str_hash % hl_color_count]
                record.session_id = self.colorize(record.session_id, color_id)

        return logging.Formatter.format(self, record)


class SessionStreamHandler(logging.StreamHandler):
    def emit(self, record):
        self.stream = sys.stderr
        super(SessionStreamHandler, self).emit(record)


class ContextFilter(logging.Filter):
    def filter(self, record):
        for frame in inspect.stack()[1:]:
            test = frame[0].f_locals.get("self")
            if hasattr(test, "driver") and hasattr(test.driver, "session_id") and test.driver.session_id:
                record.session_id = test.driver.session_id
                break
        else:
            record.session_id = "<no session id>"

        return True


def get_logger(name, level=None, format_=LOG_FORMAT):
    if not level:
        level = getattr(logging, config.logging["level"].upper())

    logger = logging.getLogger(name)
    logger.setLevel(level)
    context_filter = ContextFilter()

    stream_handler = SessionStreamHandler()
    formatter = ColoredFormatter(format_)
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(level)

    logger.addHandler(stream_handler)
    logger.addFilter(context_filter)
    return logger


log = get_logger(__name__)
