class StatsData:
    def __init__(self, num_of_vms):
        self._num_of_vm = num_of_vms
        self._num_of_queries = 0
        self._average = 0.0

    @property
    def num_of_vm(self):
        return self._num_of_vm

    @num_of_vm.setter 
    def num_of_vm(self, val):
        self._num_of_vm = val

    @property
    def num_of_queries(self):
        return self._num_of_queries

    @num_of_queries.setter
    def num_of_queries(self, val):
        self._num_of_queries = val

    def add_query(self, time):
        new_avg = self._get_new_avg(self.num_of_queries, time)
        self._average = new_avg
        self.num_of_queries += 1

    def _get_new_avg(self, n, new_time):
        return ((n * self._average) + new_time) / (n + 1)

    def get_stats_as_dict(self):
        return {'vm_count': self.num_of_vm, 'request_count': self.num_of_queries,
                'average_request_time': self._average}
