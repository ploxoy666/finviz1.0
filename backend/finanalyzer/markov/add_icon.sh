#!/bin/bash
# Automated Icon Setup Script for Stock Predictor App

echo "🎨 Stock Predictor App Icon Setup"
echo "=================================="
echo ""

# Check if icon.png exists on Desktop
ICON_PATH="$HOME/Desktop/icon.png"

if [ ! -f "$ICON_PATH" ]; then
    echo "❌ Error: icon.png not found on Desktop"
    echo ""
    echo "Please save your icon as 'icon.png' on your Desktop first, then run this script again."
    echo ""
    echo "Steps:"
    echo "1. Save the icon image to Desktop as 'icon.png'"
    echo "2. Run: bash add_icon.sh"
    exit 1
fi

echo "✓ Found icon.png on Desktop"
echo ""

# Navigate to Desktop
cd "$HOME/Desktop" || exit

# Create iconset directory
echo "📁 Creating icon set..."
mkdir -p icon.iconset

# Generate all required icon sizes for macOS
echo "🔄 Generating icon sizes..."
sips -z 16 16     icon.png --out icon.iconset/icon_16x16.png 2>/dev/null
sips -z 32 32     icon.png --out icon.iconset/icon_16x16@2x.png 2>/dev/null
sips -z 32 32     icon.png --out icon.iconset/icon_32x32.png 2>/dev/null
sips -z 64 64     icon.png --out icon.iconset/icon_32x32@2x.png 2>/dev/null
sips -z 128 128   icon.png --out icon.iconset/icon_128x128.png 2>/dev/null
sips -z 256 256   icon.png --out icon.iconset/icon_128x128@2x.png 2>/dev/null
sips -z 256 256   icon.png --out icon.iconset/icon_256x256.png 2>/dev/null
sips -z 512 512   icon.png --out icon.iconset/icon_256x256@2x.png 2>/dev/null
sips -z 512 512   icon.png --out icon.iconset/icon_512x512.png 2>/dev/null
sips -z 1024 1024 icon.png --out icon.iconset/icon_512x512@2x.png 2>/dev/null

echo "✓ All sizes generated"
echo ""

# Convert to .icns format
echo "🔧 Converting to .icns format..."
iconutil -c icns icon.iconset

if [ ! -f "icon.icns" ]; then
    echo "❌ Error: Failed to create icon.icns"
    rm -rf icon.iconset
    exit 1
fi

echo "✓ Icon converted successfully"
echo ""

# Move to app Resources
APP_PATH="$HOME/Desktop/markov chains app/Stock Predictor.app/Contents/Resources"
echo "📦 Installing icon to app..."

if [ ! -d "$APP_PATH" ]; then
    echo "❌ Error: App Resources directory not found"
    echo "Expected: $APP_PATH"
    rm -rf icon.iconset icon.icns
    exit 1
fi

mv icon.icns "$APP_PATH/"
echo "✓ Icon installed to app"
echo ""

# Clean up
echo "🧹 Cleaning up..."
rm -rf icon.iconset
echo "✓ Cleanup complete"
echo ""

# Refresh Finder to show new icon
echo "🔄 Refreshing Finder..."
touch "$HOME/Desktop/markov chains app/Stock Predictor.app"
killall Finder 2>/dev/null

echo ""
echo "════════════════════════════════════════"
echo "✅ ICON INSTALLATION COMPLETE!"
echo "════════════════════════════════════════"
echo ""
echo "The icon has been successfully added to your Stock Predictor app!"
echo ""
echo "You should now see the new icon in Finder."
echo "If not, try:"
echo "  1. Restart Finder: killall Finder"
echo "  2. Log out and log back in"
echo "  3. Restart your Mac"
echo ""
echo "🎉 Enjoy your newly branded app!"
