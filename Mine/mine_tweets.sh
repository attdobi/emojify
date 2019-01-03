# Launch emmoji analyze on 4 cores simultaniusly.
# Launch these on a screen to view the output and debug.

# This will show the output of the last task
# Trap will ensure that all tasks are killed with the last one.
trap 'kill %1; kill %2; kill %3' SIGINT
python emoji_analyze_SQL.py 1 4 &
python emoji_analyze_SQL.py 2 4 &
python emoji_analyze_SQL.py 3 4 &
python emoji_analyze_SQL.py 4 4
