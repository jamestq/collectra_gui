# Collectra GUI

A desktop application for viewing and editing annotation data with an interactive visual interface.

## Installation

### One-line Install (No Python Required)

**macOS / Linux:**
```bash
curl -fsSL https://raw.githubusercontent.com/jamestq/collectra_gui/main/install.sh | bash
```

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/jamestq/collectra_gui/main/install.ps1 | iex
```

### Manual Download

Download the latest release for your platform from the [Releases page](https://github.com/jamestq/collectra_gui/releases):

| Platform | File |
|----------|------|
| Windows | `collectra_gui-windows-x86_64.exe` |
| macOS (Intel) | `collectra_gui-macos-x86_64` |
| macOS (Apple Silicon) | `collectra_gui-macos-arm64` |
| Linux | `collectra_gui-linux-x86_64` |

## Usage

After installation, run:

```bash
collectra_gui start
```

This opens the GUI window where you can:
1. Select a folder containing YAML annotation data and images
2. View and edit annotations
3. Create new annotations by drawing bounding boxes
4. Save changes back to the YAML file

## Development

### Prerequisites

- Python 3.12+
- Poetry

### Setup

```bash
# Clone the repository
git clone https://github.com/jamestq/collectra_gui.git
cd collectra_gui

# Install dependencies
poetry install

# Run in development mode
poetry run collectra_gui start --debug
```

### Building from Source

```bash
# Install dev dependencies
poetry install --with dev

# Build executable
poetry run pyinstaller collectra_gui.spec --clean
```

The built executable will be in the `dist/` directory.

## Uninstall

**macOS / Linux:**
```bash
curl -fsSL https://raw.githubusercontent.com/jamestq/collectra_gui/main/install.sh | bash -s -- uninstall
```

**Windows (PowerShell):**
```powershell
& { irm https://raw.githubusercontent.com/jamestq/collectra_gui/main/install.ps1 } -Action uninstall
```

Or manually delete the binary from:
- macOS/Linux: `~/.local/bin/collectra_gui`
- Windows: `%LOCALAPPDATA%\collectra_gui\collectra_gui.exe`
