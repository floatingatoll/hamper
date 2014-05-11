import re
import parsley
import ometa

#from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

from hamper.interfaces import ChatPlugin
#from hamper.utils import ude


SQLAlchemyBase = declarative_base()


class BadKeyWord(Exception):
    """doc string. TODO"""


class Define(ChatPlugin):
    """Define events and how to process those events"""
    name = 'define'
    priority = 1

    def setup(self, loader):
        if loader:
            super(Define, self).setup(loader)
            self.db = loader.db
            SQLAlchemyBase.metadata.create_all(self.db.engine)

        self.definitions = {
            'events': [],
            'rules': [],
            'actions': [],
        }
        self.grammar = """
        """

        self.action_definition = (
            '(?P<adescriptor>[a-zA-Z0-9_]*)\((?P<aargs>[^)]*)\)'
        )

    @property
    def events(self):
        return self.definitions['events']

    @property
    def rules(self):
        return self.definitions['rules']

    @property
    def actions(self):
        return self.definitions['actions']

    def message(self, bot, comm):
        if not comm['directed']:
            return
        msg = comm['message'].strip()
        match = re.match(r'define (?P<dtype>event|action) (?P<stuff>.*)', msg)
        if not match:
            self.attempt(bot, comm, msg)
            return
        m = match.groupdict()
        if m['dtype'] == 'event':
            return self.define_event(bot, comm, m['stuff'])
        elif m['dtype'] == 'action':
            return self.define_action(bot, comm, m['stuff'])

    def attempt(self, bot, comm, msg):
        for event, event_grammar, _, adescriptor, aargs in self.events:
            g = parsley.makeGrammar(event_grammar, {})
            aargs = g(msg).event()
            for i_adescriptor, aarg_names, action in self.actions:
                if (i_adescriptor != adescriptor and
                        len(aarg_names) != len(aargs)):
                    continue
                ret = self.acompile(action, dict(zip(aarg_names, aargs)))
                bot.reply(comm, ret)

    def define_event(self, bot, comm, event):
        """
        The user will define an event like:
            <parsley> -> <adescriptor>(<aargs>)
        We will cheat and rip off <adescriptor> to ensure that the <parsley>
        expression will parse and return a tuple. Eventually, that parsed tuple
        will be used as the <adescriptor> *aargs signature.
        """
        if '->' not in event:
            bot.reply(comm, "Your event didn't have an '->' operator")
            return
        splits = event.split('->')
        # event is <parsley>
        event, raw_action = '->'.join(splits[:-1]), splits[-1]

        # make sure the action is valid notation
        match = re.match(self.action_definition, raw_action.strip())
        # raw_action is <adescriptor>(<aargs>)

        if not match:
            bot.reply(comm, "Your action descriptor is not in valid format.")
            return
        m = match.groupdict()
        aargs = tuple(map(lambda s: s.strip(), m['aargs'].split(',')))

        event_grammar = "{base_grammar}\nevent = {event} -> {ret}".format(
            base_grammar=self.grammar,
            event=event,
            ret=repr(aargs).replace("'", "")
        )

        # run the event_grammar with the empty string to verify it doesn't use
        # undefined rules.
        g = parsley.makeGrammar(event_grammar, {})
        try:
            # TODO, implement some magic to determine if undefined rules are
            # being used
            g('').event()
        except AttributeError, e:
            bot.reply(
                comm, "The event you defined uses an undefined rule: {0}", e
            )
            return
        except (ometa.runtime.EOFError, ometa.runtime.ParseError), e:
            # meh, this isn't doing as much as I expected it would do
            pass

        self.events.append(
            (event, event_grammar, self.grammar, m['adescriptor'], aargs)
        )

    def define_action(self, bot, comm, action):
        if '->' not in action:
            bot.reply(comm, "Your event didn't have an '->' operator")
            return
        splits = action.split('->')
        raw_adescriptor, action = splits[0], '->'.join(splits[1:])
        match = re.match(self.action_definition, raw_adescriptor.strip())

        if not match:
            bot.reply(comm, "Your action descriptor is not in valid format.")
            return
        m = match.groupdict()

        aargs = tuple(map(lambda s: s.strip(), m['aargs'].split(',')))

        # Do a dry run of the action using the default aargs.
        try:
            self.acompile(action.strip(), dict(((pa, pa) for pa in aargs)))
        except BadKeyWord, e:
            bot.reply(comm, e.message)
            return

        self.actions.append(
            (m['adescriptor'], aargs, action.strip())
        )

    def resolve_keyword(self, actx):
        global_ctx = {
            'my_name': 'wesley',
            'random_nick': 'uberj188',
        }

        def resolve(keyword):
            if keyword in actx:
                return actx[keyword]
            elif keyword in global_ctx:
                return global_ctx[keyword]
            else:
                raise BadKeyWord(
                    "The keyword {0} isn't a thing".format(keyword)
                )
        return resolve

    def acompile(self, action, ctx):
        g = parsley.makeGrammar("""
        keyword = '`' <(letterOrDigit | '_')+>:kw '`' <ws>:w -> resolve(kw) + w
        anychar = <anything>:a ?(not a.isspace() and a != '`') -> a
        word = <anychar+>:word <ws>:w -> word + w
        action = (keyword | word)+
        """, {'resolve': self.resolve_keyword(ctx)})
        return ''.join(g(action).action())


"""
class Factoid(SQLAlchemyBase):

    __tablename__ = 'factoids'

    id = Column(Integer, primary_key=True)
    type = Column(String)
    trigger = Column(String)
    action = Column(String)
    response = Column(String)

    def __init__(self, trigger, type, action, response):
        self.type = type
        self.trigger = trigger
        self.action = action
        self.response = response
"""


define = Define()
