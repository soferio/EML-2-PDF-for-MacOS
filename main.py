import eml_parser
import easygui
from weasyprint import HTML, Attachment
from io import BytesIO
import base64
import logging
from send2trash import send2trash
import traceback
import json
import datetime
import sys
logger = logging.getLogger('weasyprint')
logger.addHandler(logging.FileHandler('weasyprint.log'))

TEXT_PLAIN = 'text/plain'
TEXT_HTML = 'text/html'
RECURSION_LIMIT = 5000

class NamedBytesIO(BytesIO):
  def __init__(self,*args,**kwargs):
    BytesIO.__init__(self, *args)
    self.name = kwargs.get('name')

# Some HTML has multiple nested element, so python catches "RecursionError: maximum recursion depth exceeded in comparison"
# We need this to increase the limit
class recursionlimit:
  def __init__(self, limit):
      self.limit = limit

  def __enter__(self):
      self.old_limit = sys.getrecursionlimit()
      sys.setrecursionlimit(self.limit)

  def __exit__(self, type, value, tb):
      sys.setrecursionlimit(self.old_limit)

def json_serial(obj):
  if isinstance(obj, datetime.datetime):
      serial = obj.isoformat()
      return serial

def main():
  # User chooses input file 
  filename = easygui.fileopenbox(msg="Please select input file", filetypes=["*.eml"])

  # If user does not select any file, just stop here
  if filename == None:
    return

  try:
    convert(filename)
    send2trash(filename)
  except Exception as e:
    traceback.print_exc()

def convert(filename):
  # Decode input file
  with open(filename, 'rb') as file:
    raw_email = file.read()
  
  ep = eml_parser.EmlParser(include_raw_body=True, include_attachment_data=True)
  parsed_eml = ep.decode_email_bytes(raw_email)

  # log the json for debug purpose
  with open("json.log", "w") as file:
    file.write(json.dumps(parsed_eml, default=json_serial))

  # Parse body
  bodies = {}
  any_content = None
  for body in parsed_eml['body']:
    if (body.get('content_type') != None):
      bodies[body.get('content_type')] = body.get('content')
    else:
      any_content = body.get('content')
  string = bodies.get(TEXT_PLAIN) if bodies.get(TEXT_HTML) == None else bodies.get(TEXT_HTML)
  if (string == None): 
    string = any_content
  
  # log the html for debug purpose
  with open("html.log", "w") as file:
    file.write(string)
  
  # Parse attachments
  attachments = []
  if (parsed_eml.get('attachment') != None):
    for attachment in parsed_eml.get('attachment'):
      # attachment['raw'] is not actually raw. They are base64 encoded by eml_parser before returning to us.
      if (
        attachment.get('content_header') != None 
        and attachment.get('raw') != None
      ):
        found_and_replaced = False
        if (attachment.get('content_header').get('content-id') != None 
            and attachment.get('content_header').get('content-id')[0] != None):
          # find the content ID in the form cid:CONTENT_ID and replace it with base64 representation of the images
          content_id = attachment.get('content_header').get('content-id')[0][1:-1] 
          find = 'cid:' + content_id
          
          # content type is like: image/png; name="image001.png"
          # we don't need the name after ;
          content_type = attachment.get('content_header').get('content-type')[0]
          content_type = content_type[:content_type.index(';')] 
          
          # find and replace 
          if (content_id != None and find in string and content_type):
            repl = 'data:' + content_type + ';base64,' + attachment.get('raw').decode()
            string = string.replace(find, repl)
            found_and_replaced = True

        # Only attach file if it was not placed somewhere in html
        if not found_and_replaced:
          file = NamedBytesIO(base64.b64decode(attachment.get('raw')), name=attachment.get('filename'))
          attachments.append(Attachment(file_obj=file))
  
  if len(attachments) > 0: 
    # the ID attribute in the img tag cause attachments failed to be attached, so we need to replace it with something else.
    string = string.replace(' id=', ' did=')
  
  # output filename is the same, only extension is different
  pdf_filename = filename.replace(".eml", ".pdf")
  with recursionlimit(RECURSION_LIMIT):
    HTML(string=string).write_pdf(target=pdf_filename, attachments=attachments)
  print('Output file: ' + pdf_filename)

if __name__ == '__main__':
  main()
