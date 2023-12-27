from systems.commands.index import Agent


class Transmitter(Agent('portal.transmitter')):

    def exec(self):
        for package in self.listen('agent:portal:transmitter', state_key = 'portal_transmitter'):
            request = package.message
            portal = self.get_portal(request.get('portal', None))
            data_type = request['data_type']
            operation = request['operation']
            params = request['params']
            response = False

            self.data('Transmitter request received', request)
            try:
                if operation == 'list':
                    response = portal.list(data_type,
                        operation = params.get('operation', None),
                        **params.get('filters', {})
                    )
                elif operation == 'retrieve':
                    response = portal.retrieve(data_type, params['id'])
                elif operation == 'create':
                    response = portal.create(data_type, **params.get('fields', {}))
                elif operation == 'update':
                    response = portal.update(data_type, params['id'], **params.get('fields', {}))
                elif operation == 'delete':
                    response = portal.delete(data_type, params['id'])

                if response is False:
                    raise Exception("Request operations {} for {} failed".format(operation, data_type))

                self.send(package.sender, {
                    'status': 'success',
                    'response': response
                })

            except Exception as e:
                self.send(package.sender, {
                    'status': 'error',
                    'error': str(e),
                    'response': response
                })
