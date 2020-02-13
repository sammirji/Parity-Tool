import json
import sys
import subprocess
import glob
import traceback

HOST_NAME = "$HOST"

class ParityChecker:
  '''
   Class expects arguments: folder-path, filename <optional>, url1, url2
   Example: parity_checker.py "Regular-Negative-20200127-175720" "curl_1.txt" "localhost:8080" "abc-non-site-facing.prod.domain.com"
    ~or~    parity_checker.py "Regular-Negative-20200127-175720" "localhost:8080" "abc-non-site-facing.prod.domain.com"
  '''

  def __init__(self, is_arg):
    """
     Initialize all class level variables and validate arguments
    """
    if is_arg:
      arguments = len(sys.argv) - 1
      if arguments not in [3, 4]:
        print("Please use format:\n python parity_checker.py 'Regular-Negative-20200127-175720' 'curl_1.txt' 'localhost:8080' 'abc-non-site-facing.prod.domain.com'")
        print("\n~ OR ~ please use below format for bulk parity testing:")
        print("python parity_checker.py 'Regular-Negative-20200127-175720' 'localhost:8080' 'abc-non-site-facing.prod.domain.com'")
        sys.exit(1)
      self.folder_path = sys.argv[1]
      self.file_name = self.folder_path + "/" + sys.argv[2] if len(sys.argv) - 1 == 4 else ''
      self.actual_file_name = sys.argv[2] if len(sys.argv) - 1 == 4 else ''
      self.url_1 = sys.argv[3] if len(sys.argv) - 1 == 4 else sys.argv[2]
      self.url_2 = sys.argv[4] if len(sys.argv) - 1 == 4 else sys.argv[3]
    self.url_context = None
    self.unmatched_tags = {}
    self.counter = 1

  def initialize_params(self, folder_name, host_1, host_2):
    if folder_name is None or host_1 is None or host_2 is None:
      print("Invalid arguments! Please provide folder_name, host_1 and host_2 parameters.")
      sys.exit(1)
    self.folder_path = folder_name
    self.url_1 = host_1
    self.url_2 = host_2

  def bulkProcessParity(self):
    """
     Picks up all files starting with 'curl_req_' as curl text files
     and runs parity test.
    """
    import os
    path = os.path.join(os.getcwd(), self.folder_path, 'curl_req_*')
    for name in glob.glob(path):
      self.file_name = name
      self.actual_file_name = name[name.rfind('/')+1:]
      self.processParityCheck()
      self.counter += 1

  def sortedDeep(self, d):
    if isinstance(d,list):
      return sorted(self.sortedDeep(v) for v in d)
    if isinstance(d,dict):
      return {k: self.sortedDeep(d[k]) for k in sorted(d)}
    return d

  def processParityCheck(self):
    import uncurl
    try:
      with open(self.file_name, 'r') as file:
        data = file.read()
        curl_request_1 = data.replace(HOST_NAME, self.url_1).replace('\n', '')
        print("curl1: "+curl_request_1+"\n")
        self.url_context = uncurl.parse_context(curl_request_1)
        proc_1 = subprocess.Popen(curl_request_1, shell=True, stdout=subprocess.PIPE)
        (output_1, error_1) = proc_1.communicate()
        if error_1:
          print("error_1: " + str(error_1))
        
        curl_request_2 = data.replace(HOST_NAME, self.url_2).replace('\n', '')
        print("\ncurl2: "+curl_request_2+"\n")
        proc_2 = subprocess.Popen(curl_request_2, shell=True, stdout=subprocess.PIPE)
        (output_2, error_2) = proc_2.communicate()
        if error_2:
          print("error_2: " + str(error_2))
    except Exception as err:
      print("Exception encountered!")
      print(err)
      exit(1)

    #print("output_2:"+output_2+"\noutput_1:"+output_1)
    if output_2 and output_1:
      try:
        jsonObject_a = json.loads(output_1)
        jsonObject_b = json.loads(output_2)
        #print("\njsonObject_a: " + json.dumps(jsonObject_a, indent=4))
        self.unmatched_tags[self.url_1] = {}
        self.compare_object(self.url_1, '', self.sortedDeep(jsonObject_a), self.sortedDeep(jsonObject_b))
        self.unmatched_tags[self.url_2] = {}
        self.compare_object(self.url_2, '', self.sortedDeep(jsonObject_b), self.sortedDeep(jsonObject_a))

        json_data = json.dumps(self.unmatched_tags, indent=4, sort_keys=True)
        #print("\nParity discrepancy in:\n" + json_data)
        
        result = self.combine_results(json.loads(json_data))
        #print("\nresult: " + json.dumps(result))
        
        self.publish_results(result)
      except Exception as err:
        print(err)
        traceback.print_exc()

  def combine_results(self, unmatched_json):
    import copy
    result = copy.deepcopy(unmatched_json[self.url_1])
    for key, val in unmatched_json[self.url_2].iteritems():
      if val in unmatched_json[self.url_1].keys():
        if key != unmatched_json[self.url_1][val]:
          result[val].append(key)
      else:
        if val not in result:
          result[val] = list()
        result[val].append(key) 
    return result

  def compare_object(self, url_x, json_path, a, b):
    if type(a) != type(b):
      self.unmatched_tags[url_x][json_path + '=' + (json.dumps(a) if type(a) is dict else unicode(a))] = json_path + '=' + (json.dumps(b) if type(b) is dict else unicode(b))
    elif type(a) is dict:
      self.compare_dict(url_x, json_path, self.sortedDeep(a), self.sortedDeep(b))
    elif type(a) is list:
      self.compare_list(url_x, json_path, self.sortedDeep(a), self.sortedDeep(b))
    else:
      if a != b:
        self.unmatched_tags[url_x][json_path + '=' + (json.dumps(a) if type(a) is dict else unicode(a))] = json_path + '=' + (json.dumps(b) if type(b) is dict else unicode(b))

  def compare_dict(self, url_x, json_path_dict, a, b):
    for key,val in a.items():
      if not key in b:
        self.unmatched_tags[url_x][json_path_dict + '=' + (json.dumps(key) if type(key) is dict else unicode(key))] = json_path_dict + '=' + (json.dumps(b) if type(b) is dict else unicode(b))
      else:
        self.compare_object(url_x, (json_path_dict + ('.' if json_path_dict else '') + (json.dumps(key) if type(key) is dict else unicode(key) if key else key)), val, b[key])

  def compare_list(self, url_x, json_path_list, a, b):
    import itertools
    for (a_index, b_index) in itertools.izip_longest(a, b): 
      idx = unicode(a.index(a_index)) if a_index in a else unicode(b.index(b_index))
      self.compare_object(url_x, json_path_list + '[' + idx + ']', a_index, b_index)

  def publish_results(self, parity_data):
    try:
      table_body = "<table id='hosts'><tr><th colspan=2>Request:</th></tr>"
      table_body += "<tr><td><b>URL:</b></td><td>" + unicode(self.url_context.url) + "</td></tr>"
      table_body += "<tr><td><b>Headers:</b></td><td>" + json.dumps(self.url_context.headers) + "</td></tr>"
      table_body += "<tr><td><b>Request Body:</b></td><td>" + unicode(self.url_context.data) + "</td></tr></table><br/>"
      table_body += "<h4>Differences:</h4><br/><table id='hosts'><tr>"
      #for ky in self.unmatched_tags.keys():
      table_body += "<th colspan='2'>" + self.url_1 + "</th>" + "<th colspan='2'>" + self.url_2 + "</th>"
      table_body += "</tr><tr><td><b>Attribute</b></td><td><b>Value</b></td><td><b>Attribute</b></td><td><b>Value</b></td></tr>"
      for key, val in parity_data.iteritems():
        keys = key.split("=")
        if type(val) is list:
          for v in val:
            vals = v.split("=")
            table_body += "<tr><td>" + keys[0] + "</td><td>" + keys[1] + "</td><td>" + vals[0] + "</td><td>" + vals[1] + "</td></tr>"
        else:
          vals = val.split("=")
          table_body += "<tr><td>" + keys[0] + "</td><td>" + keys[1] + "</td><td>" + vals[0] + "</td><td>" + vals[1] + "</td></tr>"
      table_body += "</table>"
      self.wrapStringInHTMLMac(table_body)
    except Exception as err:
      print("Error while publishing results!")
      print(err)
      traceback.print_exc()

  def wrapStringInHTMLMac(self, body):
    import datetime
    import os

    now = datetime.datetime.today().strftime("%Y%m%d-%H%M%S")
    fn = self.actual_file_name.split('.txt')[0]+'-' if self.actual_file_name else ''
    filename = os.path.join(os.getcwd(), self.folder_path, 'parity_results-'+fn+now+'.html')
    f = open(filename,'w')

    html_string = """<html>
    <head>
    <style>
    #hosts {
      font-family: 'Trebuchet MS', Arial, Helvetica, sans-serif;
      border-collapse: collapse;
      width: 100%;
      font-size: 12px;
    }

    #hosts td, #hosts th {
      border: 1px solid #ddd;
      padding: 8px;
    }

    #hosts tr:nth-child(even){background-color: #f2f2f2;}

    #hosts tr:hover {background-color: #ddd;}

    #hosts th {
      padding-top: 12px;
      padding-bottom: 12px;
      text-align: left;
      background-color: #009dff;
      color: white;
    }
    </style>"""
    wrapper = """<title>Parity Test Results - %s</title>
    </head>
    <body><p>%s</p></body>
    </html>"""

    whole = html_string + wrapper % (now, body)
    f.write(whole)
    f.close()

    print('filename:' + filename)

if __name__ == "__main__":
  pc = ParityChecker(True)
  if len(sys.argv) - 1 == 3:
    pc.bulkProcessParity()
  else:
    pc.processParityCheck()
