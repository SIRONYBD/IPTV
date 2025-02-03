import requests
import time

def fetch_content_from_url(url):
    """Fetch content from a URL."""
    try:
        print(f"Fetching content from URL: {url}")
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching URL '{url}': {e}")
        return None

def read_content_from_file(file_path):
    """Read file content from a local file."""
    try:
        print(f"Reading content from file: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file '{file_path}': {e}")
        return None

def get_m3u_content(source):
    """
    Determines if source is a URL or file.
    If it starts with http:// or https://, treat as URL; otherwise, as a file path.
    """
    source = source.strip()
    if source.lower().startswith("http://") or source.lower().startswith("https://"):
        return fetch_content_from_url(source)
    else:
        return read_content_from_file(source)

def parse_m3u(content):
    """
    Parses M3U content into a list of (info_line, stream_url) tuples.
    Expects the standard M3U format where each channel is defined by:
    #EXTINF:...
    stream_url
    """
    lines = content.splitlines()
    channels = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF"):
            info_line = line
            if i + 1 < len(lines):
                url_line = lines[i + 1].strip()
                channels.append((info_line, url_line))
                i += 2
            else:
                i += 1
        else:
            i += 1
    return channels

def check_stream(url, timeout=5):
    """
    Checks whether the stream URL is available.
    Uses a GET request with streaming enabled and a timeout.
    Returns True if a valid response is received.
    """
    try:
        response = requests.get(url, stream=True, timeout=timeout)
        if 200 <= response.status_code < 400:
            return True
    except Exception:
        pass
    return False

def measure_latency(url, timeout=5):
    """
    Measures the latency of a stream URL by timing the GET request.
    Returns the elapsed time in seconds if available; otherwise, returns None.
    """
    try:
        start_time = time.perf_counter()
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        elapsed = time.perf_counter() - start_time
        return elapsed
    except Exception:
        return None

def option_check_availability():
    """Option 1: Check IPTV availability."""
    source = input("Enter the source for the M3U playlist (URL or local file path): ").strip()
    content = get_m3u_content(source)
    if content is None:
        print("Could not retrieve the M3U content. Exiting option.")
        return

    channels = parse_m3u(content)
    if not channels:
        print("No channels found in the M3U content.")
        return

    total = len(channels)
    working_channels = []
    not_working = 0

    print(f"\nFound {total} channels. Checking availability...\n")
    for idx, (info, url) in enumerate(channels, start=1):
        print(f"[{idx}/{total}] Checking: {url}")
        if check_stream(url):
            print("   -> Available!")
            working_channels.append((info, url))
        else:
            print("   -> Not available.")
            not_working += 1

    print("\n--- Summary ---")
    print(f"Working channels: {len(working_channels)}")
    print(f"Not working channels: {not_working}")

    if working_channels:
        output_file = input("Enter the filename to save the available channels (e.g., available_channels.m3u): ").strip()
        if not output_file:
            output_file = "available_channels.m3u"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for info, url in working_channels:
                f.write(f"{info}\n{url}\n")
        print(f"\nSaved {len(working_channels)} available channels to '{output_file}'.")
    else:
        print("No available channels to save.")

def option_combine_m3u():
    """Option 2: Combine multiple M3U files (removing duplicates based on the stream URL)."""
    combined_channels = []
    seen_urls = set()

    try:
        n = int(input("How many M3U sources do you want to combine? Enter a number: "))
    except ValueError:
        print("Invalid number. Exiting option.")
        return

    for i in range(1, n + 1):
        source = input(f"Enter source #{i} (URL or local file path): ").strip()
        content = get_m3u_content(source)
        if content:
            channels = parse_m3u(content)
            print(f"Found {len(channels)} channels in source #{i}.")
            for info, url in channels:
                if url not in seen_urls:
                    combined_channels.append((info, url))
                    seen_urls.add(url)
                else:
                    print(f"Duplicate found and skipped: {url}")
        else:
            print(f"Skipping source #{i} due to retrieval issues.")

    if not combined_channels:
        print("No channels found from the provided sources.")
        return

    output_file = input("Enter the filename to save the combined M3U (e.g., combined_playlist.m3u): ").strip()
    if not output_file:
        output_file = "combined_playlist.m3u"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for info, url in combined_channels:
            f.write(f"{info}\n{url}\n")
    print(f"\nCombined {len(combined_channels)} channels saved to '{output_file}'.")

def extract_channel_name(info_line):
    """
    Extracts the channel name from an info line.
    Assumes the channel name comes after the last comma.
    """
    parts = info_line.split(',')
    if len(parts) > 1:
        return parts[-1].strip()
    return info_line.strip()

def option_categorize_channels():
    """Option 3: Categorize channels (delete unavailable channels)."""
    source = input("Enter the source for the M3U playlist (URL or local file path): ").strip()
    content = get_m3u_content(source)
    if content is None:
        print("Could not retrieve the M3U content. Exiting option.")
        return

    channels = parse_m3u(content)
    if not channels:
        print("No channels found in the M3U content.")
        return

    print("\nHow do you want to categorize the channels?")
    print("1. By Time Latency")
    print("2. Alphabetical Order (A-Z)")
    cat_choice = input("Select an option (1 or 2): ").strip()

    if cat_choice == "1":
        # Measure latency for each channel and only include channels that are available.
        print("\nMeasuring latency for each channel (this may take some time)...")
        available_channels = []
        total = len(channels)
        for idx, (info, url) in enumerate(channels, start=1):
            print(f"[{idx}/{total}] Checking latency for: {url}")
            latency = measure_latency(url)
            if latency is not None:
                available_channels.append((info, url, latency))
                print(f"   -> Available with latency: {latency:.2f} sec")
            else:
                print("   -> Not available. Skipping.")
        if not available_channels:
            print("No available channels found.")
            return

        # Sort available channels by latency (lowest first)
        available_channels.sort(key=lambda x: x[2])
        output_file = input("Enter the filename to save the latency-sorted playlist (e.g., latency_sorted.m3u): ").strip()
        if not output_file:
            output_file = "latency_sorted.m3u"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for info, url, latency in available_channels:
                f.write(f"{info}\n{url}\n")
        print(f"\nSaved {len(available_channels)} channels (sorted by latency) to '{output_file}'.")

    elif cat_choice == "2":
        # For alphabetical order, first check availability of each channel.
        print("\nChecking availability for each channel (this may take some time)...")
        available_channels = []
        total = len(channels)
        for idx, (info, url) in enumerate(channels, start=1):
            print(f"[{idx}/{total}] Checking: {url}")
            if check_stream(url):
                available_channels.append((info, url))
                print("   -> Available!")
            else:
                print("   -> Not available. Skipping.")
        if not available_channels:
            print("No available channels found.")
            return

        # Sort channels alphabetically by channel name extracted from the info line.
        sorted_channels = sorted(available_channels, key=lambda x: extract_channel_name(x[0]).lower())
        output_file = input("Enter the filename to save the alphabetically-sorted playlist (e.g., sorted_playlist.m3u): ").strip()
        if not output_file:
            output_file = "sorted_playlist.m3u"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for info, url in sorted_channels:
                f.write(f"{info}\n{url}\n")
        print(f"\nSaved {len(sorted_channels)} channels (sorted A-Z) to '{output_file}'.")
    else:
        print("Invalid option. Returning to the main menu.")

def main():
    """Main menu for the IPTV tool."""
    while True:
        print("\n===== IPTV Tool Menu =====")
        print("1. Check IPTV Availability")
        print("2. Combine Multiple M3U Files")
        print("3. Categorize Channels (Delete Unavailable Channels)")
        print("0. Exit")
        choice = input("Select an option (0-3): ").strip()

        if choice == "1":
            option_check_availability()
        elif choice == "2":
            option_combine_m3u()
        elif choice == "3":
            option_categorize_channels()
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please choose 0, 1, 2, or 3.")

if __name__ == "__main__":
    main()
