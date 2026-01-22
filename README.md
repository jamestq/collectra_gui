# Collectra GUI

A desktop application for viewing and editing annotation data with an interactive visual interface.

## Installation

### Option 1: Download Pre-built Binary

Download the latest release for your platform from the [Releases page](https://github.com/jamestq/collectra_gui/releases):

| Platform | File |
|----------|------|
| Windows | `collectra_gui-windows-x86_64.exe` |
| macOS (Intel) | `collectra_gui-macos-x86_64` |
| macOS (Apple Silicon) | `collectra_gui-macos-arm64` |
| Linux | `collectra_gui-linux-x86_64` |

After downloading, make the binary executable (macOS/Linux):
```bash
chmod +x collectra_gui-*
```

### Option 2: Install via Python/Poetry

For development or if you prefer installing from source:

```bash
# Clone the repository
git clone https://github.com/jamestq/collectra_gui.git
cd collectra_gui

# Install dependencies
poetry install

# Run the application
poetry run collectra_gui start
```

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

### Running in Debug Mode

```bash
poetry run collectra_gui start --debug
```

### Building from Source

To create a standalone executable:

```bash
# Install dev dependencies
poetry install --with dev

# Build executable
poetry run pyinstaller collectra_gui.spec --clean
```

The built executable will be in the `dist/` directory.
