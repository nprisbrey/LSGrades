#!/bin/bash

# Check that Python 3 is installed
if [ $(command -v python3) ]; then
	echo "Python 3 is installed."
else
	echo "Python 3 not installed. Now attempting to install..."
	{ #Try
		sudo apt-get update &&
		sudo apt-get install python3 -y &&
		echo "Python 3 installed successfully."
	} || { #Catch
		echo "Couldn't install Python 3 automatically. Please install and then run this script again." &&
		exit
	}
fi
