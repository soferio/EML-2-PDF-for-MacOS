import eml_parser
import easygui
from weasyprint import HTML, Attachment, CSS
from io import BytesIO
import base64
import logging
from send2trash import send2trash
import traceback
import json
import datetime
import sys
import html5lib
import tinycss2
from pathlib import Path
import os.path
import html

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

# check if object has attribute <name> with value <value>
def check_attribute(obj, name, value):
  return hasattr(obj, name) and getattr(obj, name) == value

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
  filename = easygui.fileopenbox(msg="Please select input file", filetypes=["*.eml"], default=current_path + '/*.eml')

  # If user does not select any file, just stop here
  if filename == None:
    return

  # Save current path for next use
  with open(setting_filename, 'w') as file:
    file.write(str(Path(filename).parent))

  # output filename is the same, only extension is different
  pdf_filename = filename.replace(".eml", ".pdf")
  if os.path.isfile(pdf_filename):
    if easygui.boolbox("A PDF file with this name already exists, do you want to replace existing file?", 
      choices=("[Y]es", "[N]o (Esc)"),):
      perform_conversion(filename, pdf_filename)
  else:
    perform_conversion(filename, pdf_filename)

def perform_conversion(filename, pdf_filename):
  try:
    pdf_filename = convert(filename, pdf_filename)
    if easygui.boolbox("""
    PDF file was generated successfully at: 
    %s

    Do you want to delete the EML file?
    """ % pdf_filename, choices=("[D]elete", "[K]eep (Esc)"),):
      print("EML file is in Trash bin now")
      send2trash(filename)
  except Exception as e:
    traceback.print_exc()

def convert(filename, pdf_filename):
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
  
  # Parse attachments
  attachments = []
  attachment_filenames = []
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
          if (';' in  content_type): 
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
          attachment_filenames.append(attachment.get('filename'))
  
  # create a header section to contain to, from, subject and date
  with open("header.html", "r") as file:
    header = file.read()
  
  # From section
  from_email = parsed_eml.get('header').get('from')
  # if there is header, use header because there is name of email address there
  if (parsed_eml.get('header').get('header') != None 
      and parsed_eml.get('header').get('header').get('from') 
      and len(parsed_eml.get('header').get('header').get('from')) > 0):
    from_email = html.escape(parsed_eml.get('header').get('header').get('from')[0])

  subject = html.escape(parsed_eml.get('header').get('subject'))

  # Date section
  if (parsed_eml.get('header').get('received') != None 
    and len(parsed_eml.get('header').get('received')) > 0):
    # received date in local time
    date = parsed_eml.get('header').get('received')[0].get('date').astimezone().strftime('%-d %B %Y at %-I:%M:%S %p')
  elif parsed_eml.get('header').get('date') != None:
    # if received date is not available, use sent date
    date = parsed_eml.get('header').get('date').astimezone().strftime('%-d %B %Y at %-I:%M:%S %p')
  else:
    date = 'Unknown'

  # To section
  to_emails = ', '.join(parsed_eml.get('header').get('to'))
  if (parsed_eml.get('header').get('header') != None 
      and parsed_eml.get('header').get('header').get('to') 
      and len(parsed_eml.get('header').get('header').get('to')) > 0):
    to_emails = html.escape(parsed_eml.get('header').get('header').get('to')[0])

  # CC section
  display_cc = parsed_eml.get('header').get('cc') != None and len(parsed_eml.get('header').get('cc')) > 0
  cc_row_display = 'table-row' if display_cc else 'none'
  cc_emails = ''
  if (display_cc):
    cc_emails = ', '.join(parsed_eml.get('header').get('cc'))
    # if there is header, use header because there is name of email address there
    if (parsed_eml.get('header').get('header') != None 
        and parsed_eml.get('header').get('header').get('cc') 
        and len(parsed_eml.get('header').get('header').get('cc')) > 0):
      cc_emails = html.escape(parsed_eml.get('header').get('header').get('cc')[0])

  # BCC section
  display_bcc = parsed_eml.get('header').get('header').get('bcc') != None and len(parsed_eml.get('header').get('header').get('bcc')) > 0
  bcc_row_display = 'table-row' if display_bcc else 'none'
  bcc_emails = ''
  if (parsed_eml.get('header').get('header') != None 
      and parsed_eml.get('header').get('header').get('bcc') 
      and len(parsed_eml.get('header').get('header').get('bcc')) > 0):
    bcc_emails = html.escape(parsed_eml.get('header').get('header').get('bcc')[0])

  attachment_row_display = 'table-row' if len(attachment_filenames) > 0 else 'none'
  attachment_filenames = ', '.join(attachment_filenames)
  header = header % (from_email, subject, date, to_emails, cc_row_display, cc_emails, bcc_row_display, bcc_emails, attachment_row_display, attachment_filenames)

  elements = html5lib.parse(string, namespaceHTMLElements=False)
  if len(attachments) > 0: 
    # the ID attribute in the img tag cause attachments failed to be attached, so we need to delete it
    # See https://github.com/Kozea/WeasyPrint/issues/1733 
    # parse HTML  
    # find any element with ID attributes and delete the id attribute
    elements_with_ids = elements.findall('*//*[@id]')
    for element in elements_with_ids:
      del element.attrib['id']

  # element with display:inline-block and width:100% can create truncate issue in rendering PDF
  # here if any element has both of those styles, we remove display:inline-block
  elements_with_styles = elements.findall('*//*[@style]')
  for element in elements_with_styles:
    declarations = tinycss2.parse_declaration_list(element.attrib['style'])
    found_width_100_percent = False
    found_display_inline_block = False
    for d in declarations:
      if check_attribute(d, 'name', 'display') and hasattr(d, 'value') and len(d.value) > 0 and check_attribute(d.value[0], 'lower_value', 'inline-block'):
        found_display_inline_block = True
      if check_attribute(d, 'name', 'width') and hasattr(d, 'value') and len(d.value) > 0 and check_attribute(d.value[0], 'type', 'percentage') and check_attribute(d.value[0], 'value', 100):
        found_width_100_percent = True
      
    if found_width_100_percent and found_display_inline_block:
      new_styles = []
      for d in declarations:
        if not (hasattr(d, 'name') and d.name == 'display' and len(d.value) > 0 and d.value[0].lower_value == 'inline-block'):
          new_styles.append(d.serialize())
      element.attrib['style'] = ';'.join(new_styles)

  # insert header to body element
  body_element = elements.find('body') or elements.find('*//body')
  if (body_element != None):
    header_elements = html5lib.parse(header, namespaceHTMLElements=False)
    body_element.insert(0, header_elements)

  # produce the new HTML string after removing IDs attributes
  s = html5lib.serializer.HTMLSerializer()
  walker = html5lib.getTreeWalker("etree")
  stream = walker(elements)
  output = s.serialize(stream)
  if (body_element == None):
    string = header
  else:
    string = ''
  for item in output:
    string = string + item

  # log the html for debug purpose
  with open("html.log", "w") as file:
    file.write(string)
  
  with recursionlimit(RECURSION_LIMIT):
    HTML(string=string).write_pdf(target=pdf_filename, attachments=attachments, stylesheets=[CSS('stylesheets.css')])

if __name__ == '__main__':
  main()
