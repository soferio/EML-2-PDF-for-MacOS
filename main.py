import eml_parser
import easygui
from weasyprint import HTML, Attachment
from io import BytesIO
import base64
import logging
from send2trash import send2trash
logger = logging.getLogger('weasyprint')
logger.addHandler(logging.FileHandler('weasyprint.log'))

TEXT_PLAIN = 'text/plain'
TEXT_HTML = 'text/html'

class NamedBytesIO(BytesIO):
  def __init__(self,*args,**kwargs):
    BytesIO.__init__(self, *args)
    self.name = kwargs.get('name')

def main():
  # User chooses input file 
  filename = easygui.fileopenbox(msg="Please select input file", filetypes=["*.eml"])

  # If user does not select any file, just stop here
  if filename == None:
    return

  try:
    convert(filename)
    send2trash(filename)
  except:
    print("Something went wrong")

def convert(filename):
  # Decode input file
  with open(filename, 'rb') as file:
    raw_email = file.read()
  
  ep = eml_parser.EmlParser(include_raw_body=True, include_attachment_data=True)
  parsed_eml = ep.decode_email_bytes(raw_email)

  # Parse body
  bodies = {}
  for body in parsed_eml['body']:
    bodies[body['content_type']] = body['content']
  string = bodies[TEXT_PLAIN] if bodies[TEXT_HTML] == None else bodies[TEXT_HTML]
  # the ID attribute in the img tag cause attachments failed to be attached, so we need to replace it with something else.
  string = string.replace(' id=', ' did=')
  
  # Parse attachments
  attachments = []
  for attachment in parsed_eml['attachment']:
    # attachment['raw'] is not actually raw. They are base64 encoded by eml_parser before returning to us.
    if (
      attachment['content_header'] != None 
      and attachment['content_header']['content-id'] != None 
      and attachment['content_header']['content-id'][0] != None
    ):
      # find the content ID in the form cid:CONTENT_ID and replace it with base64 representation of the images
      content_id = attachment['content_header']['content-id'][0][1:-1] 
      find = 'cid:' + content_id
      
      # content type is like: image/png; name="image001.png"
      # we don't need the name after ;
      content_type = attachment['content_header']['content-type'][0]
      content_type = content_type[:content_type.index(';')] 
      
      # find and replace 
      if (find in string and content_type):
        repl = 'data:' + content_type + ';base64,' + attachment['raw'].decode()
        string = string.replace(find, repl)
      else:
        # if the image was replace, then we don't need to attach it. 
        file = NamedBytesIO(base64.b64decode(attachment['raw']), name=attachment['filename'])
        attachments.append(Attachment(file_obj=file))

  # output filename is the same, only extension is different
  pdf_filename = filename.replace(".eml", ".pdf")
  HTML(string=string).write_pdf(target=pdf_filename, attachments=attachments)
  print('Output file: ' + pdf_filename)

if __name__ == '__main__':
  main()
