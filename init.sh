#!/bin/bash

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3 to continue."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed. Please install pip3 to continue."
    exit 1
fi

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "Error: requirements.txt not found in current directory."
    exit 1
fi

echo "Checking dependencies from requirements.txt..."

# Read requirements.txt and check each package
while IFS= read -r line; do
    # Skip empty lines and comments
    if [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]]; then
        continue
    fi
    
    # Extract package name (before >= or == or other operators)
    package=$(echo "$line" | sed 's/[><=!].*//' | tr -d '[:space:]')
    
    if [ -n "$package" ]; then
        echo "Checking $package..."
        if ! python3 -c "import $package" 2>/dev/null; then
            echo "Error: $package is not installed."
            echo "Would you like to install dependencies? (y/n)"
            read -p "Answer: " answer
            if [ "$answer" = "y" ]; then
                echo "Installing $package..."
                pip3 install $package
            else
                echo "Please install $package manually and run this script again."
            exit 1
        fi
    fi
done < requirements.txt

echo "All dependencies are installed successfully!"
