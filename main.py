import easygui

from send2trash import send2trash
import traceback
from pathlib import Path
import os
from common import convert

def main():
  # read settings file for recent open path
  setting_filename = 'settings.txt'
  current_path = '.'
  if os.path.isfile(setting_filename):
    with open(setting_filename, 'r') as file:
      path = file.readline()
      if (path == ''):
        current_path = '.'
      else:
        current_path = path

  # User chooses input file 
  filenames = easygui.fileopenbox(msg="Please select input file", filetypes=["*.eml"], default=current_path + '/*.eml', multiple=True)

  # If user does not select any file, just stop here
  if filenames == None:
    return

  # Save current path for next use
  with open(setting_filename, 'w') as file:
    file.write(str(Path(filenames[0]).parent))

  # output filename is the same, only extension is different
  exists = False
  for filename in filenames:
    pdf_filename = filename.replace(".eml", ".pdf")
    if os.path.isfile(pdf_filename):
      exists = True
      break
  
  if exists:
    if easygui.boolbox("Some PDF files exist, do you want to replace existing files?", 
        choices=("[Y]es", "[N]o (Esc)"),):
        perform_conversion(filenames)
  else:
    perform_conversion(filenames)

def perform_conversion(filenames):
  failed_filenames = []
  for filename in filenames:
    try:
      convert(filename)    
    except Exception as e:
      failed_filenames.append(filename)
      traceback.print_exc()
  message = 'All files were converted successfully!'
  if len(failed_filenames) > 0:
    message = 'These files have issues during conversion to PDF:\n\n\t%s' % ('\n\t'.join(failed_filenames))

  if (easygui.boolbox("""
    %s\n
    Do you want to delete the EML files?
  """ % message, choices=("[D]elete", "[K]eep (Esc)"),)):
      print("EML file is in Trash bin now")
      for filename in filenames:
        if filename not in failed_filenames:
          send2trash(filename)

if __name__ == '__main__':
  main()
