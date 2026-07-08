# Dispatcharr Group Channel Streams

[![GitHub Issues](https://img.shields.io/github/issues/kpirnie/dispatcharr-group-channel-streams?style=for-the-badge&logo=github&color=006400&logoColor=white&labelColor=000)](https://github.com/kpirnie/dispatcharr-group-channel-streamsissues)
[![Last Commit](https://img.shields.io/github/last-commit/kpirnie/dispatcharr-group-channel-streams?style=for-the-badge&labelColor=000)](https://github.com/kpirnie/dispatcharr-group-channel-streams/commits/main)
[![License: MIT](https://img.shields.io/badge/License-MIT-orange.svg?style=for-the-badge&logo=opensourceinitiative&logoColor=white&labelColor=000)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white&style=for-the-badge&labelColor=000)](https://python.org)
[![Kevin Pirnie](https://img.shields.io/badge/-KevinPirnie.com-000d2d?style=for-the-badge&labelColor=000&logoColor=white&logo=data:image/svg%2Bxml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIxLjgiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+CiAgPGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iMTAiLz4KICA8ZWxsaXBzZSBjeD0iMTIiIGN5PSIxMiIgcng9IjQuNSIgcnk9IjEwIi8+CiAgPGxpbmUgeDE9IjIiIHkxPSIxMiIgeDI9IjIyIiB5Mj0iMTIiLz4KICA8bGluZSB4MT0iNC41IiB5MT0iNi41IiB4Mj0iMTkuNSIgeTI9IjYuNSIvPgogIDxsaW5lIHgxPSI0LjUiIHkxPSIxNy41IiB4Mj0iMTkuNSIgeTI9IjE3LjUiLz4KPC9zdmc+Cg==)](https://kevinpirnie.com/)

A Python tool for automatically grouping and organizing streaming channels in your Dispatcharr instance. This tool fetches all available streams from your Dispatcharr API, intelligently groups them by channel name, and creates or updates channel entries with multiple stream sources for redundancy and quality options.

## What it Does

**Problem**: When you have multiple M3U sources in Dispatcharr, you often end up with duplicate channels (e.g., "ESPN HD", "ESPN SD", "ESPN") scattered across different providers. This makes channel management difficult and your channel list cluttered.

**Solution**: This tool automatically:
- Fetches all streams from your Dispatcharr instance
- Groups streams with similar names (using customizable regex normalization)
- Creates unified channel entries that include all stream variants
- Provides redundancy by linking multiple stream sources to each channel
- Keeps your channel list clean and organized

## Features

- **Intelligent Channel Grouping**: Automatically groups similar channels together
- **Stream Redundancy**: Each channel can have multiple stream sources for failover
- **Name Normalization**: Remove unwanted suffixes like "HD", "SD", etc. using regex
- **M3U Refresh**: Optionally refresh all M3U sources before processing
- **Stale Stream Pruning**: Optionally remove streams that no longer exist from your grouped channels
- **Configuration Management**: Save settings for easy reuse
- **Retry Logic**: Built-in retry mechanisms for API calls
- **Progress Tracking**: Clear feedback on operations being performed

## Requirements

- Python 3.6+
- A running Dispatcharr instance
- Valid Dispatcharr user account credentials

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://gitlab.com/kp-development/python/dispatcharr-group-channel-streams.git
   cd dispatcharr-group-channel-streams
   ```

2. **Install dependencies** (if any are added later):
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Run the tool**:
   ```bash
   python3 main.py
   ```

## Quick Start

### First Time Setup
When you run the tool for the first time, it will prompt you for configuration:

```bash
python3 main.py
```

You'll be asked for:
- **Dispatcharr URL**: Your Dispatcharr instance URL (e.g., `http://192.168.1.100:8080`)
- **Username**: Your Dispatcharr username
- **Password**: Your Dispatcharr password  
- **Normalizer**: Optional regex pattern to clean channel names

### Example Configuration Session
```
Please enter the following info...
Dispatcharr URL [http(s)://HOST:PORT]: http://192.168.1.100:8080
Username: admin
Password: ********
Channel Name Normalizer RegExp (optional): \s(HD|SD|FHD|4K)$
Configuration saved to /home/user/.config/.dgcs_conf
```

## Usage

### Basic Usage
```bash
# Run with saved configuration
python3 main.py

# Run with M3U refresh (slower but ensures latest data)
python3 main.py --refresh

# Run with stale stream pruning
python3 main.py --prune
```

### Command Line Arguments

#### Configuration Arguments
```bash
# Provide configuration via command line (will save to config file)
python3 main.py --endpoint http://localhost:8080 --username admin --password mypassword

# Add channel name normalizer
python3 main.py --endpoint http://localhost:8080 --username admin --password mypassword --normalizer "\s(HD|SD)$"
```

#### Operational Arguments
```bash
# Force M3U refresh before processing
python3 main.py --refresh

# Reconfigure the application (prompts for new settings)
python3 main.py --reconfigure

# Remove stale streams from grouped channels before processing
python3 main.py --prune
```

### All Available Arguments

| Argument | Type | Description |
|----------|------|-------------|
| `--endpoint` | Value | Dispatcharr instance URL (e.g., `http://127.0.0.1:8080`) |
| `--username` | Value | Dispatcharr username |
| `--password` | Value | Dispatcharr password |
| `--normalizer` | Value | Regex pattern to normalize channel names |
| `--refresh` | Flag | Refresh all M3U sources before processing |
| `--reconfigure` | Flag | Force reconfiguration of saved settings |
| `--prune` | Flag | Remove stale streams from grouped channels before processing |

## Channel Name Normalization

The normalizer helps clean up channel names by removing unwanted suffixes or prefixes. This ensures channels with slightly different names get grouped together.

### Common Normalizer Patterns

| Pattern | Removes | Example |
|---------|---------|---------|
| `\s(HD\|SD)$` | " HD" or " SD" at end | "ESPN HD" → "ESPN" |
| `\s(FHD\|4K\|UHD)$` | High-res suffixes | "CNN 4K" → "CNN" |
| `^\[.*?\]\s*` | Brackets at start | "[US] NBC" → "NBC" |
| `\s-\s.*$` | Everything after " - " | "ESPN - Sports" → "ESPN" |

### Complex Example
```bash
# Remove quality indicators and country prefixes
python3 main.py --normalizer "^\[.*?\]\s*|\s(HD|SD|FHD|4K|UHD)$"
```

## Configuration File

Settings are automatically saved to `~/.config/.dgcs_conf`:

```ini
[DEFAULT]
API_ENDPOINT = http://192.168.1.100:8080
API_USER = admin  
API_PASS = mypassword
NORMALIZER = \s(HD|SD)$
```

## How It Works

1. **Authentication**: Connects to your Dispatcharr API using provided credentials
2. **Stream Fetching**: Retrieves all available streams from all M3U sources
3. **M3U Refresh** (optional): Triggers refresh of M3U sources for latest data
4. **Name Normalization**: Applies regex pattern to clean channel names
5. **Stale Stream Pruning** (optional): Removes stream IDs that no longer exist from existing channels
6. **Grouping**: Groups streams with matching normalized names
7. **Channel Management**: Creates new channels or updates existing ones with grouped streams
8. **Redundancy**: Each channel gets all matching streams as backup sources

## Example Output

```
Starting channel creation...
Triggering M3U account refresh...
Waiting for M3U refresh to complete...
M3U refresh complete, fetching streams...
Fetching streams...
Found 1247 streams
Fetching channels...
Found 89 channels
Pruning stale streams...
Pruned channel: ESPN
2 Stale Streams Removed
Updated channel: ESPN
4 Streams
Created channel: Discovery Channel  
2 Streams
Updated channel: CNN
3 Streams
Successfully processed 156 channels
```

## Troubleshooting

### Common Issues

**Authentication Failed**
- Verify your Dispatcharr URL is correct and accessible
- Check username and password are correct
- Ensure Dispatcharr API is enabled

**No Streams Found**  
- Run with `--refresh` flag to update M3U sources
- Check that M3U sources are configured in Dispatcharr
- Verify M3U URLs are accessible

**Regex Errors**
- Test your normalizer pattern with an online regex tester
- Use double quotes around complex patterns
- Escape special characters properly

### Getting Help

1. Run with `--reconfigure` to reset configuration
2. Check Dispatcharr logs for API errors
3. Ensure all M3U sources are working in Dispatcharr first

## Contributing

Issues and pull requests are welcome. Please ensure any changes maintain backward compatibility with existing configurations.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
