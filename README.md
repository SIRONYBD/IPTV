# IPTV

How It Works
Option 1: Check IPTV Availability
Checks each channel from the provided M3U source and reports the working versus non-working channels. Only working channels are saved to the output file.

Option 2: Combine Multiple M3U Files
Combines channels from multiple sources and removes duplicates (based on the stream URL).

Option 3: Categorize Channels (Delete Unavailable Channels)

By Time Latency:
Measures the latency of each channel and includes only the channels that respond. The available channels are sorted from fastest to slowest before saving.
Alphabetical Order (A-Z):
Checks each channel for availability and includes only those that work. The available channels are then sorted alphabetically by the channel name (extracted from the info line) before saving.
