Requirements
===============================================
This project use 3rd party libraries:

- `easygui`: let users select the input file from a dialog
- `eml-parser`: parse the EML file for HTML and attachments files
- `weasyprint`: Convert HTML files and create PDF files with attachments
- `html5lib`: for editing HTML elements
- `tinycss2`: for editing CSS styles
- `Send2Trash`: For moving EML file to trash bin. 


On MacOs, please run this command to install dependencies for `weasyprint`
```
brew install python pango libffi
```

Please run this command to install `python-tk`, a dependency of `easygui`
```
brew install python-tk
```

Then from the base directory of the project, please run this to create a virtual env:
```
python3 -m venv .venv
```

Activate the virtual env so we can start working in:
```
source .venv/bin/activate
```


Install dependencies libraries to the virtual env:
```
python3 -m pip install -r requirements.txt
```

Running
===============================================
Please run the following command from the base directory of the project:
```
python3 main.py
```

Create a shortcut in Desktop 
===============================================
To create a shortcut to run the script in MacOs, first we need to grant the execute permission to the file `start.command` by running:
```
chmod +x ./start.command
```

Then in Finder, please right click on `start.command` file and select `Make Alias`. Then we can copy the alias file anywhere (such as Desktop) or rename it to anything. 
Double click on the alias file or the `start.command` file will run the script in virtual environment.

The script will run inside a terminal windows. After finish running, if the terminal windows is not closed, then we can configure the terminal to close. To configure the terminal to close after finish running, we need to:
- Open Terminal 
- Go to Menu Terminal -> Preferences...
- Then in tab Shell, in "When the shell exists:", we select "Close if the shell exited cleanly". 