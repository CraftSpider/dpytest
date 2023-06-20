from .runner import get_message
from .verify import verify


def assert_easy_message_content(expected: str):
    mess = get_message(peek=True)  # peek doesnt remove the message from the queue
    assert verify().message().content(expected), "<%s> != <%s>" % (mess.content, expected)
