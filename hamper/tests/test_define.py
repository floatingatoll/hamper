from unittest import TestCase

from hamper.plugins.define import Define


class MockBot(object):
    last_msg = None

    def reply(self, comm, msg):
        self.last_msg = msg


class TestDefine(TestCase):
    """
    The Command class provides some basic structure for regex-powered
    commands.
    """

    def setUp(self):
        self.bot = MockBot()

    def test_define_blame(self):
        d = Define()
        d.setup(None)
        d.message(self.bot, {
            'directed': True,
            'message': "define event '!blame ' <anything+>:a -> blame(a)"
        })
        d.message(self.bot, {
            'directed': True,
            'message': "define action blame(something) -> `my_name` blames `random_nick` for `something`"  # noqa
        })
        d.message(self.bot, {
            'directed': True,
            'message': "!blame a random  string <-->"  # noqa
        })
        self.assertTrue("a random  string <-->" in self.bot.last_msg)

    def test_define_url(self):
        d = Define()
        d.setup(None)
        d.message(self.bot, {
            'directed': True,
            'message': "define event '!lmgtfy ' <anything+>:a -> lmgtfy(a)"
        })
        d.message(self.bot, {
            'directed': True,
            'message': "define action lmgtfy(term) -> http://lmgtfy.com/?q=`term`"  # noqa
        })
        d.message(self.bot, {
            'directed': True,
            'message': "!lmgtfy a random  string <-->"  # noqa
        })
        self.assertEqual(
            "http://lmgtfy.com/?q=a random  string <-->", self.bot.last_msg
        )
