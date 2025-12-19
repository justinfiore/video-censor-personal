#!/bin/bash
# Create a macOS app bundle for Video Censor Personal

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="Video Censor Personal"
APP_BUNDLE_DIR="$SCRIPT_DIR/$APP_NAME.app"
CONTENTS_DIR="$APP_BUNDLE_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"

# Remove old bundle if it exists
rm -rf "$APP_BUNDLE_DIR"

# Create directory structure
mkdir -p "$MACOS_DIR"
mkdir -p "$RESOURCES_DIR"

# Create the executable wrapper script
cat > "$MACOS_DIR/$APP_NAME" << 'WRAPPER'
#!/bin/bash
# Executable wrapper for Video Censor Personal

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")"

# Activate virtual environment if it exists
if [ -d "$APP_ROOT/venv" ]; then
    source "$APP_ROOT/venv/bin/activate"
elif [ -d "$APP_ROOT/.venv" ]; then
    source "$APP_ROOT/.venv/bin/activate"
fi

# Launch the Python application
cd "$APP_ROOT"
exec python3 -m video_censor_personal.ui.main
WRAPPER

chmod +x "$MACOS_DIR/$APP_NAME"

# Create Info.plist
cat > "$CONTENTS_DIR/Info.plist" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>en</string>
    <key>CFBundleExecutable</key>
    <string>Video Censor Personal</string>
    <key>CFBundleIdentifier</key>
    <string>com.videocensor.personal</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>Video Censor Personal</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSRequiresIPhoneOS</key>
    <false/>
</dict>
</plist>
PLIST

echo "macOS app bundle created successfully at: $APP_BUNDLE_DIR"
echo ""
echo "You can now:"
echo "  1. Launch directly: open '$APP_BUNDLE_DIR'"
echo "  2. Create a desktop shortcut in your Applications folder:"
echo "     cp -r '$APP_BUNDLE_DIR' ~/Applications/"
