from systems.commands.index import Agent


class Receiver(Agent('portal.receiver')):

    processes = (
        'receiver_check',
        'receiver_retry'
    )


    def receiver_check(self):
        self.run_exclusive('portal_receiver', self._request_events,
            timeout = self.get_config('portal_receiver_lock_timeout', 10)
        )

    def _request_events(self):
        for portal_name in self.get_portals():
            for event in self.portal_list(portal_name, 'event', 'follow'):
                self._process_event(portal_name, event['type'], event['data'])

    def receiver_retry(self):
        for package in self.listen('agent:portal:receiver:retry', state_key = 'portal_receiver'):
            event = package.message
            self._process_event(event['portal'], event['type'], event['data'])


    def _process_event(self, portal_name, event_type, event_data):
        self.data("Portal {} event received".format(event_type), event_data)
        self.exec_local("portal event {}".format(event_type),
            options = {
                'portal': portal_name,
                'event_fields': event_data,
                'async_exec': True
            }
        )
        self.send('agent:portal:receiver:event', {
            'portal': portal_name,
            'type': event_type,
            'data': event_data
        })
