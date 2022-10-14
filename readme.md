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
usage: python console.py [-h] [-d] [-f] [-o] eml_files [eml_files ...]

Convert EML to PDF.

positional arguments:
  eml_files     EML filenames

options:
  -h, --help    show this help message and exit
  -d, --delete  Keep the EML files after conversion (default: NO)
  -f, --force   Overwrite existing PDF files (default: NO)
  -o, --open    Open the PDF files after conversion (default: NO)
```

Setup Folder Action in Automator 
====================================
1. Open Automator. Select "New Document".
2. Choose "Folder Action" as type. Folder Actions are workflows that are attached to a folder in the Finder. Items added to the folder cause the workflow to run and are used as input to the workflow
3. In the workflow editor, select the folder the will receive EML files. 
4. Add a "Run Shell Script" action to the workflow. 
5. In the Run Shell Script action the we added, enter the script below. Here '$@' is a way that we pass multiple filename to the python scripts. We should change `<PATH TO EML_PDF FOLDER>` with the actual path to the project. 
```
#!/bin/sh
cd <PATH TO EML_PDF FOLDER>
source .venv/bin/activate
python3 console.py $@ -f -o -d
```

6. In the Run Shell Script action the we added, in the "Pass Input" select box, change to value from `To Stdin` to `As arguments`.
7. Save the workflow. Normally the work flow will be saved to `~/Library/Workflows/Applications/Folder Actions`