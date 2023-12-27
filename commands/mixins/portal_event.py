from systems.commands.index import CommandMixin
from utility.data import Collection


class PortalEventCommandMixin(CommandMixin('portal_event')):

    def get_event(self):
        return Collection(**self.event_fields)


    def event_wrapper(self, callback):
        try:
            return callback(self.get_event())

        except Exception as e:
            self.send('agent:portal:listener:retry', {
                'portal': self.portal,
                'type': self.name,
                'data': self.event_fields
            })
            raise e
