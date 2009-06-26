
def take_snapshot():
    """
    Take a snapshot of all configured EBS volumes.
    """
    # Read the configurations to create a boto ec2 connection

    # Build boto ec2 volumes for each ebs vol in the config

    # Connect to the database using a django cursor

    # For each volume
        # Flush the tables and grab a READ LOCK

        # Freeze the xfs file system

        # Call create_snapshot

        # Unfreeze the xfs file system

        # Unlock the table

    # Log all fo the snapshot info

    pass
