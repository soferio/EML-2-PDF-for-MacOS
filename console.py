import argparse
import os
from common import convert
from send2trash import send2trash
import traceback
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import logging
import sys

logger = logging.getLogger('console.py')
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)
logger.addHandler(handler)
handler = logging.FileHandler('log/console.txt')
handler.setFormatter(formatter)
logger.addHandler(handler)

def dir_path(path):
  if os.path.isdir(path):
    return path
  else:
    raise argparse.ArgumentTypeError(f"{path} is not a valid directory")

def process_files(filenames):
  """Convert list of EML files to PDF"""
  exists = False
  for filename in filenames:
    pdf_filename = filename.replace(".eml", ".pdf")
    if pdf_filename != filename and os.path.isfile(pdf_filename):
      exists = True
      break

  if exists and not args.forceWrite:
    logger.info("Do nothing because there are PDF existing files. If you want to overwrite existing PDF files, please use -f flag")
    return

  failed_filenames = []
  converted_filenames = []
  success_filenames = []
  for filename in filenames:
    file_extension = os.path.splitext(filename)[-1]
    if file_extension.lower() == ".eml":
      try:
        if os.path.exists(filename):
          pdf_filename = convert(filename)  
          converted_filenames.append(filename)  
          success_filenames.append('"' + pdf_filename + '"')
        else: 
          logger.info("File " + filename + ' does not exist')
      except Exception as e:
        failed_filenames.append(filename)
        traceback.print_exc()
        
  message = None
  if len(filenames) == len(success_filenames) and len(success_filenames) > 0:
    message = 'All files were converted successfully!'
  if len(failed_filenames) > 0:
    message = 'These files have issues during conversion to PDF:\n\n\t%s' % ('\n\t'.join(failed_filenames))

  if args.delete:
    for filename in converted_filenames:
      send2trash(filename)
  
  if args.openPdf and len(success_filenames) > 0:
    os.system("open " + " ".join(success_filenames))
  if message != None:
    logger.info(message)
  
    
class EmlPdfEventHandler(FileSystemEventHandler):
  """Convert EML file to PDF"""

  def __init__(self, logger=None):
    super().__init__()

  def on_moved(self, event):
    super().on_moved(event)
    if not event.is_directory:
      logger.info("Move " + event.dest_path)
      process_files([event.dest_path]) 

  def on_created(self, event):
    super().on_created(event)

    if not event.is_directory:
      logger.info("Create " + event.src_path)
      process_files([event.src_path]) 

  def on_deleted(self, event):
    super().on_deleted(event)

  def on_modified(self, event):
    super().on_modified(event)

    if not event.is_directory:
      logger.info("Modify " + event.src_path)
      process_files([event.src_path]) 

parser = argparse.ArgumentParser(description='Convert EML to PDF.', prog='python console.py')
parser.add_argument('filenames', metavar='eml_files', type=str, nargs='*',
                    help='EML filenames')
parser.add_argument('-d', '--delete', dest='delete', action='store_true',
                    help='Keep the EML files after conversion (default: NO)')
parser.add_argument('-f', '--force', dest='forceWrite', action='store_true',
                    help='Overwrite existing PDF files (default: NO)')
parser.add_argument('-o', '--open', dest='openPdf', action='store_true',
                    help='Open the PDF files after conversion (default: NO)')
parser.add_argument('-w', '--watch', dest='watch', type=dir_path, default=None, metavar='directory',
                    help='Watch a directory and all subdirectories of it for EML files')
args = parser.parse_args()

if len(args.filenames) == 0 and args.watch == None:
  parser.error('Please specify filenames to convert or a directory to watch')

if len(args.filenames) > 0:
  process_files(args.filenames)
  
if args.watch != None:
  event_handler = EmlPdfEventHandler()
  observer = Observer()
  observer.schedule(event_handler, args.watch, recursive=True)
  observer.start()
  try:
    while observer.is_alive():
      observer.join(1)
  finally:
    observer.stop()
    observer.join()
