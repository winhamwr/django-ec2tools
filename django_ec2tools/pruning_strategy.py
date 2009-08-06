import datetime

def parse_ts(ts):
    return datetime.datetime.strptime(ts, '%Y-%m-%dT%H:%M:%S.000Z')

class PruneStrategyBase(object):
    """
    Base class for making pruning strategies. Subclass and write a
    _should_prune() method to create a strategy.
    """
    def __call__(self, snapshot, pruning_vol_id):
        return self._should_prune(snapshot, pruning_vol_id)

    def _should_prune(self, snapshot, pruning_vol_id):
        raise NotImplementedError("Classes extending PruneStrategyBase should implement their own _should_prune()")

class PruneByAge(PruneStrategyBase):
    """
    Class for aged-based snapshot pruning strategies. Give __init__ a
    timedelta object, and all snapshots older than that will be pruned.
    """
    def __init__(self, max_age):
        self.max_age = max_age

    def _should_prune(self, snapshot, pruning_vol_id):
        if snapshot.volume_id == pruning_vol_id:
            now = datetime.datetime.now()

            age = now - parse_ts(snapshot.start_time)
            if age > self.max_age:
                return True
        return False

oneday_rolling = PruneByAge(datetime.timedelta(1))
twoday_rolling = PruneByAge(datetime.timedelta(2))
oneweek_rolling = PruneByAge(datetime.timedelta(7))