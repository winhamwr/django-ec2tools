import datetime

def parse_ts(ts):
    """
    Parses an ec2 date string (eg. snapshot.start_time) as a datetime object.
    """
    return datetime.datetime.strptime(ts, '%Y-%m-%dT%H:%M:%S.000Z')

class PruneStrategyBase(object):
    """
    Base class for making pruning strategies. Subclass and write a
    _should_prune() method to create a strategy.
    """
    def __call__(self, ec2_conn, snapshot, pruning_vol_id):
        return self._should_prune(ec2_conn, snapshot, pruning_vol_id)

    def _should_prune(self, ec2_conn, snapshot, pruning_vol_id):
        raise NotImplementedError("Classes extending PruneStrategyBase should implement their own _should_prune()")

class PruneByAge(PruneStrategyBase):
    """
    Class for aged-based snapshot pruning strategies. Give __init__ a
    timedelta object, and all snapshots older than that will be pruned.
    """
    def __init__(self, max_age):
        self.max_age = max_age

    def _should_prune(self, ec2_conn, snapshot, pruning_vol_id):
        if snapshot.volume_id == pruning_vol_id:
            now = datetime.datetime.now()

            age = now - parse_ts(snapshot.start_time)
            if age > self.max_age:
                return True
        return False

oneday_rolling = PruneByAge(datetime.timedelta(1))
twoday_rolling = PruneByAge(datetime.timedelta(2))
oneweek_rolling = PruneByAge(datetime.timedelta(7))

class PruneByAgeWithParent(PruneByAge):
    """
    Class for aged-based snapshot pruning strategies. Give __init__ a
    timedelta object, and all snapshots older than that will be pruned along
    with the snapshots of any parent volume (volumes which created the
    snapshot that spawned this volume). This does NOT prune the snapshot if the
    parent was a new volume (not created from a snapshot).
    """
    def _should_prune(self, ec2_conn, snapshot, pruning_vol_id):
        should_prune = super(PruneByAgeWithParent, self)._should_prune(
            ec2_conn, snapshot, pruning_vol_id)
        if should_prune:
            # If we already should prune it, don't worry about parents
            return True

        # If the snapshots is from a parent vol, maybe we should prune it
        parent = self._get_parent(ec2_conn, pruning_vol_id)
        if parent and parent.snapshot_id:
                # Only delete parents who have parents themselves
                return super(PruneByAgeWithParent, self)._should_prune(
                    ec2_conn, snapshot, parent.id)

    def _get_parent(self, ec2_conn, volume_id):
        volume = ec2_conn.get_all_volumes([volume_id])[0]

        if volume.snapshot_id:
            # We have a parent
            snapshot = ec2_conn.get_all_snapshots([volume.snapshot_id])[0]
            parent_id = snapshot.volume_id
            if parent_id:
                parent = ec2_conn.get_all_volumes([parent_id])[0]
                return parent

twoday_rolling_parent = PruneByAgeWithParent(datetime.timedelta(2))