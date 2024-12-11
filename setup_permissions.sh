#!/bin/bash
# setup_permissions.sh

STORAGE_BASE="/media/karti/lite_driver"
DIRS=("previews" "uploads")

# Create base directory
sudo mkdir -p "$STORAGE_BASE"

# Create subdirectories
for dir in "${DIRS[@]}"; do
    sudo mkdir -p "$STORAGE_BASE/$dir"
done

# Set ownership
sudo chown -R karti:karti "$STORAGE_BASE"

# Set directory permissions
sudo find "$STORAGE_BASE" -type d -exec chmod 755 {} \;

# Set file permissions
sudo find "$STORAGE_BASE" -type f -exec chmod 644 {} \;

# Set special permissions for upload and preview directories
sudo chmod 777 "$STORAGE_BASE/previews"
sudo chmod 777 "$STORAGE_BASE/uploads"

echo "Permissions set successfully!"