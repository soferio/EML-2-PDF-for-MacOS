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

Running the command line interface
====================================
The `console.py` is the command line version of `main.py`. For a list of argument to run it, please type:
```
python console.py -h
```

A help message will appear like this:
```
usage: python console.py [-h] [-d] [-f] [-o] [-w directory] [eml_files ...]

Convert EML to PDF.

positional arguments:
  eml_files             EML filenames

options:
  -h, --help            show this help message and exit
  -d, --delete          Keep the EML files after conversion (default: NO)
  -f, --force           Overwrite existing PDF files (default: NO)
  -o, --open            Open the PDF files after conversion (default: NO)
  -w directory, --watch directory
                        Watch a directory and all subdirectories of it for EML files
```

Setup Watcher on Login
====================================
1. First we need to edit `watch.command` file to specify the directory we need to watch.
 Just replace `EML_DIRECTORY` with the path of your EML directory.
Then we grant the execution permission on the file `watch.command` by running:
```
chmod +x ./watch.command
```
2. Go to System Preferences -> "Users & Groups".
3. Click on the Lock button on lower corner to change settings.
4. Then click on the the Current User on the left panel. On the right panel, we click on `Login Items` tab. 
4. In `Login Items` tab, click on the '+' button to add a new item to run when login. 
5. Navigate to and select `watch.command` file. 
