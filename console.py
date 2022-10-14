import argparse
import os
from common import convert
from send2trash import send2trash
import traceback

parser = argparse.ArgumentParser(description='Convert EML to PDF.', prog='python console.py')
parser.add_argument('filenames', metavar='eml_files', type=str, nargs='+',
                    help='EML filenames')
parser.add_argument('-d', '--delete', dest='delete', action='store_true',
                    help='Keep the EML files after conversion (default: NO)')
parser.add_argument('-f', '--force', dest='forceWrite', action='store_true',
                    help='Overwrite existing PDF files (default: NO)')
parser.add_argument('-o', '--open', dest='openPdf', action='store_true',
                    help='Open the PDF files after conversion (default: NO)')

args = parser.parse_args()

exists = False
for filename in args.filenames:
  pdf_filename = filename.replace(".eml", ".pdf")
  if os.path.isfile(pdf_filename):
    exists = True
    break

if not exists or args.forceWrite:
  failed_filenames = []
  success_filenames = []
  for filename in args.filenames:
    try:
      if os.path.exists(filename):
        file_extension = os.path.splitext(filename)[1]
        if file_extension.lower() == ".eml":
          pdf_filename = convert(filename)    
          success_filenames.append('"' + pdf_filename + '"')
      else: 
        print("File " + filename + ' does not exist')
    except Exception as e:
      failed_filenames.append(filename)
      traceback.print_exc()
  message = 'Some files are not converted!'
  if len(args.filenames) == len(success_filenames):
    message = 'All files were converted successfully!'
  if len(failed_filenames) > 0:
    message = 'These files have issues during conversion to PDF:\n\n\t%s' % ('\n\t'.join(failed_filenames))

  if args.delete:
    for filename in args.filenames:
      if filename not in failed_filenames:
        send2trash(filename)
  
  if args.openPdf:
    os.system("open " + " ".join(success_filenames))
  print(message)
else:
  print("Do nothing because there are PDF existing files. If you want to overwrite existing PDF files, please use -f flag")