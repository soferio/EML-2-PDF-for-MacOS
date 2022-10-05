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