from systems.commands.index import Agent
from utility.display import print_exception_info


class Receiver(Agent('portal.receiver')):

    processes = (
        'receiver_check',
        'receiver_retry'
    )


    def receiver_check(self):
        self.run_exclusive('portal_receiver', self._request_events,
            timeout = self.get_config('portal_receiver_lock_timeout', 10)
        )
        self.sleep(1)

    def _request_events(self):
        try:
            for portal in self.get_portals(events = True):
                for event in self.portal_list(portal.name, 'event', 'follow'):
                    self._process_event(portal.name, event['id'], event['type'], event['data'])
        except Exception:
            pass

    def receiver_retry(self):
        try:
            for package in self.listen('agent:portal:receiver:retry', state_key = 'portal_receiver'):
                event = package.message
                self._process_event(event['portal'], event['id'], event['type'], event['data'])
        except Exception:
            pass


    def _process_event(self, portal_name, event_id, event_type, event_data):
        if not getattr(self, 'event_index', None):
            self.event_index = {}

        if event_id not in self.event_index:
            self.data("Portal {} event received".format(event_type), event_data)
            try:
                self.exec_local("portal event {}".format(event_type),
                    options = {
                        'portal': portal_name,
                        'event_id': event_id,
                        'event_fields': event_data,
                        'async_exec': True,
                        'task_priority': 1,
                        'verbosity': self.verbosity
                    }
                )
            except Exception as e:
                self.send('agent:portal:receiver:retry', {
                    'portal': portal_name,
                    'id': event_id,
                    'type': event_type,
                    'data': event_data
                })
                self.warning("Retrying portal event failed with error: {}".format(e))
                print_exception_info(True)
                raise e

            self.send('agent:portal:receiver:event', {
                'portal': portal_name,
                'id': event_id,
                'type': event_type,
                'data': event_data
            })
            self.event_index[event_id] = True
