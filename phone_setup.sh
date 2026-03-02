#!/bin/sh
# SolarPunk Phone Setup — runs in a-Shell on iOS
# Connects your phone to your running GitHub system
# Run: curl -fsSL https://raw.githubusercontent.com/meekotharaccoon-cell/meeko-nerve-center/main/phone_setup.sh | sh

echo ""
echo "🌸 SolarPunk Phone Setup"
echo "======================"
echo ""

# Check for a-Shell
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ Python3 not found."
  echo "Install a-Shell from the App Store: https://apps.apple.com/app/a-shell/id1473805438"
  exit 1
fi

echo "✅ a-Shell detected"
echo ""

# Install dependencies available in a-Shell
pip install requests 2>/dev/null || true

# Create phone config directory
mkdir -p ~/solarpunk
cd ~/solarpunk

# Download the phone controller
curl -fsSL https://raw.githubusercontent.com/meekotharaccoon-cell/meeko-nerve-center/main/phone_controller.py -o phone_controller.py

echo "✅ Phone controller downloaded"
echo ""
echo "Setup your GitHub token to connect to your system:"
echo "  1. Go to: https://github.com/settings/tokens"
echo "  2. Create a token with 'repo' and 'actions' scopes"
echo "  3. Run: python3 ~/solarpunk/phone_controller.py --setup"
echo ""
echo "After setup, run any of these from your phone:"
echo "  python3 ~/solarpunk/phone_controller.py --status"
echo "  python3 ~/solarpunk/phone_controller.py --trigger"
echo "  python3 ~/solarpunk/phone_controller.py --directive \"focus on grants today\""
echo "  python3 ~/solarpunk/phone_controller.py --revenue"
echo "  python3 ~/solarpunk/phone_controller.py --jobs"
echo ""
echo "🌸 Done. Your phone is now a control panel for your system."
