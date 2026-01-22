#!/bin/bash
#
# Collectra GUI Installer for macOS and Linux
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/jamestq/collectra_gui/main/install.sh | bash
#
# Or download and run:
#   chmod +x install.sh && ./install.sh
#

set -e

REPO="jamestq/collectra_gui"
BINARY_NAME="collectra_gui"
INSTALL_DIR="${COLLECTRA_INSTALL_DIR:-$HOME/.local/bin}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Detect OS and architecture
detect_platform() {
    local os arch

    case "$(uname -s)" in
        Linux*)  os="linux";;
        Darwin*) os="macos";;
        *)       error "Unsupported operating system: $(uname -s)";;
    esac

    case "$(uname -m)" in
        x86_64|amd64)  arch="x86_64";;
        arm64|aarch64) arch="arm64";;
        *)             error "Unsupported architecture: $(uname -m)";;
    esac

    # Linux only supports x86_64 for now
    if [ "$os" = "linux" ] && [ "$arch" = "arm64" ]; then
        error "Linux ARM64 is not yet supported. Please build from source."
    fi

    echo "${os}-${arch}"
}

# Get latest release version
get_latest_version() {
    curl -sS "https://api.github.com/repos/${REPO}/releases/latest" | \
        grep '"tag_name":' | \
        sed -E 's/.*"([^"]+)".*/\1/'
}

# Download and install
install() {
    local platform version download_url tmp_dir

    platform=$(detect_platform)
    info "Detected platform: $platform"

    # Get version
    version="${COLLECTRA_VERSION:-$(get_latest_version)}"
    if [ -z "$version" ]; then
        error "Could not determine latest version. Set COLLECTRA_VERSION manually."
    fi
    info "Installing version: $version"

    # Construct download URL
    download_url="https://github.com/${REPO}/releases/download/${version}/${BINARY_NAME}-${platform}"
    info "Downloading from: $download_url"

    # Create temp directory
    tmp_dir=$(mktemp -d)
    trap "rm -rf $tmp_dir" EXIT

    # Download binary
    if ! curl -fSL "$download_url" -o "$tmp_dir/$BINARY_NAME"; then
        error "Failed to download binary. Check if release exists: $download_url"
    fi

    # Make executable
    chmod +x "$tmp_dir/$BINARY_NAME"

    # Create install directory if needed
    mkdir -p "$INSTALL_DIR"

    # Install binary
    mv "$tmp_dir/$BINARY_NAME" "$INSTALL_DIR/$BINARY_NAME"
    info "Installed to: $INSTALL_DIR/$BINARY_NAME"

    # Check if install dir is in PATH
    if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
        warn "$INSTALL_DIR is not in your PATH"
        echo ""
        echo "Add it to your shell profile:"
        echo ""
        echo "  For bash (~/.bashrc or ~/.bash_profile):"
        echo "    export PATH=\"\$PATH:$INSTALL_DIR\""
        echo ""
        echo "  For zsh (~/.zshrc):"
        echo "    export PATH=\"\$PATH:$INSTALL_DIR\""
        echo ""
        echo "  For fish (~/.config/fish/config.fish):"
        echo "    fish_add_path $INSTALL_DIR"
        echo ""
    fi

    echo ""
    info "Installation complete!"
    echo ""
    echo "Run 'collectra_gui start' to launch the application."
}

# Uninstall
uninstall() {
    if [ -f "$INSTALL_DIR/$BINARY_NAME" ]; then
        rm "$INSTALL_DIR/$BINARY_NAME"
        info "Uninstalled $BINARY_NAME from $INSTALL_DIR"
    else
        warn "$BINARY_NAME is not installed in $INSTALL_DIR"
    fi
}

# Main
case "${1:-install}" in
    install)   install;;
    uninstall) uninstall;;
    *)         echo "Usage: $0 [install|uninstall]"; exit 1;;
esac
