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

def parse_attachments(parsed_eml, ep, body):
  """
  Parse eml for attachments and replace images in the body with attached images 
  Arguments:
      parsed_eml: parsed result of the email
      ep: parser
      body: body content of he email
  Returns:
      attachments: list of Attachment object
      attachment_filenames: list of attachment filenames
      body: new content body
  """

  # Parse attachments
  attachments = []
  attachment_filenames = []
  if (parsed_eml.get('attachment') != None):
    # parse nested emails for content_id of nested attachments
    # so that we knows which attachments are for nested emails, then we don't include those attachments in the main email
    nested_content_ids = []
    for attachment in parsed_eml.get('attachment'):
      content_type = attachment.get('content_header').get('content-type')[0]
      if content_type.lower().startswith('message/rfc822'):
        nested_raw_email = base64.b64decode(attachment.get('raw'))
        nested_parsed_eml = ep.decode_email_bytes(nested_raw_email)
        for nested_attachment in nested_parsed_eml.get('attachment'):
          if (nested_attachment.get('content_header').get('content-id') 
              and len(nested_attachment.get('content_header').get('content-id')) > 0):
            nested_content_ids = nested_content_ids + nested_attachment.get('content_header').get('content-id')

    for attachment in parsed_eml.get('attachment'):
      # attachment['raw'] is not actually raw. They are base64 encoded by eml_parser before returning to us.
      if (
        attachment.get('content_header') != None 
        and attachment.get('raw') != None
      ):
        found_and_replaced = False
        if (attachment.get('content_header').get('content-id') != None 
            and attachment.get('content_header').get('content-id')[0] != None):
          if (attachment.get('content_header').get('content-id')[0] in nested_content_ids):
            found_and_replaced = True
          else:
            # find the content ID in the form cid:CONTENT_ID and replace it with base64 representation of the images
            content_id = attachment.get('content_header').get('content-id')[0][1:-1] 
            find = 'cid:' + content_id
            
            # content type is like: image/png; name="image001.png"
            # we don't need the name after ;
            content_type = attachment.get('content_header').get('content-type')[0]
            if (';' in  content_type): 
              content_type = content_type[:content_type.index(';')] 
            
            # find and replace 
            if (content_id != None and find in body and content_type):
              repl = 'data:' + content_type + ';base64,' + attachment.get('raw').decode()
              body = body.replace(find, repl)
              found_and_replaced = True

        # Only attach file if it was not placed somewhere in html or in nested emails
        if not found_and_replaced:
          attachment_filename = attachment.get('filename')
          content_type = attachment.get('content_header').get('content-type')[0]
          # when the attachment is an email but the filename does not contain an extension
          if content_type.lower().startswith('message/rfc822') and '.' not in attachment_filename:
            attachment_filename = 'Mail Attachment.eml'

          file = NamedBytesIO(base64.b64decode(attachment.get('raw')), name=attachment_filename)
          attachments.append(Attachment(file_obj=file))
          attachment_filenames.append(attachment_filename)
  return [attachments, attachment_filenames, body]

def generate_header(parsed_eml, attachment_filenames):
  """
  Generate the header section contain to/from/cc/bcc/subject/attachments
  Arguments:
      parsed_eml: parsed result of the email
      attachment_filenames: list of attachment filenames
  Returns:
      HTML string of the header 
  """

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
  return header

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
      if (bodies.get(body.get('content_type')) == None): # only accept the first of each content_type if there are multiple
        bodies[body.get('content_type')] = body.get('content')
    else:
      any_content = body.get('content')
  content_string = bodies.get(TEXT_PLAIN) if bodies.get(TEXT_HTML) == None else bodies.get(TEXT_HTML)
  if (content_string == None): 
    content_string = any_content

  attachments, attachment_filenames, content_string = parse_attachments(parsed_eml, ep, content_string)
  header = generate_header(parsed_eml, attachment_filenames)

  elements = html5lib.parse(content_string, namespaceHTMLElements=False)
  if len(attachments) > 0: 
    # the ID attribute in the img tag cause attachments failed to be attached, so we need to delete it
    # See https://github.com/Kozea/WeasyPrint/issues/1733 
    # parse HTML to find any element with ID attributes and delete the id attribute
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

  # insert header to first child body element if possible
  # we don't insert to body element because in some emails the first element is a page. 
  # so anything we put before the first element will push the first element to the 2nd page. 
  header_inserted = False
  body_element = elements.find('body') or elements.find('*//body')
  if (body_element != None):
    header_elements = html5lib.parse(header, namespaceHTMLElements=False)
    for child in body_element:
      child.insert(0, header_elements)
      # if there is text in child, we want the header element to stay before the text
      header_elements.tail, child.text = child.text, None
      header_inserted = True
      break

  # produce the new HTML string after removing IDs attributes
  s = html5lib.serializer.HTMLSerializer()
  walker = html5lib.getTreeWalker("etree")
  stream = walker(elements)
  output = s.serialize(stream)
  if not header_inserted:
    content_string = header
  else:
    content_string = ''
  for item in output:
    content_string = content_string + item

  # log the html for debug purpose
  with open("html.log", "w") as file:
    file.write(content_string)
  pdf_filename = filename.replace(".eml", ".pdf")
  with recursionlimit(RECURSION_LIMIT):
    HTML(string=content_string).write_pdf(target=pdf_filename, attachments=attachments, stylesheets=[CSS('stylesheets.css')])

if __name__ == '__main__':
  main()
