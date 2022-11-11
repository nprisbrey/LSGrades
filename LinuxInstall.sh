#!/bin/bash

# Check that Python 3 is installed
if [ $(command -v python3) ]; then
	echo "python3 is installed."
else
	echo "python3 not installed. Now attempting to install..."
	{ #Try
		sudo apt update &&
		sudo apt install python3 -y &&
		echo "python3 installed successfully."
	} || { #Catch
		echo "Couldn't install python3 automatically. Please install and then run this script again." &&
		exit
	}
fi

# Check that pip is installed
if [ $(command -v pip) ]; then
	echo "pip is installed."
else
	echo "pip not installed. Now attempting to install..."
	{ #Try
		sudo apt update &&
		sudo apt install python3-pip -y &&
		echo "pip installed successfully."
	} || { #Catch
		echo "Couldn't install pip automatically. Please install and then run this script again." &&
		exit
	}
fi

# Install Python dependencies
pip install -r requirements.txt
