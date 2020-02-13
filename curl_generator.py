import sys
import csv
import os

RESPONSE_GROUPS = '$RESPONSE_GROUPS'
CONSUMER_ID = '$CONSUMER_ID'
REQUEST_INPUT = '$REQUEST_INPUT'
POSTAL_CODE = '$POSTAL_CODE'
VERTICAL_ID = '$VERTICAL_ID'
ENV = '$ENV'
STORE_IDS = '$STORE_IDS'

FILE_NAME = 'curl_template.txt'
CSV_FILE_NAME = 'request_types.csv'

class CurlGenerator:
  '''
    Generates curl_req_*.txt files for parity testing.
    Usage:
    $ python curl_generator.py <REQUEST_TYPE> <SCENARIO_TYPE> <REQUEST_ID> <OFFER_ID> <POSTAL_CODE> <STORE_IDS>
  '''
    
  def __init__(self, is_arg):
    if is_arg:  
      if len(sys.argv) not in [6, 7]:
        print("Invalid arguments!\nUsage:\n$ python curl_generator.py <REQUEST_TYPE> <SCENARIO_TYPE> <REQUEST_ID> <OFFER_ID> <POSTAL_CODE> <STORE_IDS>")
        print('-- <REQUEST_TYPE>: enumerator of "Regular", "Variant", "Bundle" or "BVShell".')
        print('-- <SCENARIO_TYPE>: enumerator of "Positive", "Negative" or "Store".')
        print('-- <REQUEST_ID>: can be specified with label PRODUCT_ID="sampleProductId" or US_ITEM_ID="sampleUSItemId". ' +  
              'If no label is provided REQUEST_ID is considered to be US_ITEM_ID by default.')
        print("-- <STORE_IDS>: can be optionally specified. Use comma separated values if more than one store_id needs to be specified.")
        print("Example:")
        print('$ python curl_generator.py Regular Negative 48319962 "06DEDE4C806C4B33B15CB348ACC6AFF6" "90001"')
        print('$ python curl_generator.py BVShell Store "PRODUCT_ID=3HD11CXDBNLK" "D3409E9E783F4F29B9EEE2B3B8801492" "90001" 2280')
        print('$ python curl_generator.py Variant Store "US_ITEM_ID=768746060" "91ED8E89C32442B696C9398671844D9C" "90001" 2280,1122,2239')
        sys.exit(1)
    
      self.product_type = sys.argv[1]
      self.test_type = sys.argv[2]
      self.request_id = sys.argv[3]
      self.offer_id = sys.argv[4]
      self.postalCode = sys.argv[5]
      self.us_store_ids = sys.argv[6] if len(sys.argv) == 7 else None
      self.initialize()

  def initialize_params(self, product_type, test_type, request_id, offer_id, postal_code, store_ids=None):
    if product_type is None or test_type is None or request_id is None or offer_id is None or postal_code is None:
      print("Invalid arguments!\nArguments:\n<REQUEST_TYPE> <SCENARIO_TYPE> <REQUEST_ID> <OFFER_ID> <POSTAL_CODE> <STORE_IDS>")
      print('-- <REQUEST_TYPE>: enumerator of "Regular", "Variant", "Bundle" or "BVShell".')
      print('-- <SCENARIO_TYPE>: enumerator of "Positive", "Negative" or "Store".')
      print('-- <REQUEST_ID>: can be specified with label PRODUCT_ID="sampleProductId" or US_ITEM_ID="sampleUSItemId". ' +  
            'If no label is provided REQUEST_ID is considered to be US_ITEM_ID by default.')
      print("-- <STORE_IDS>: can be optionally specified. Use comma separated values if more than one store_id needs to be specified.")
      sys.exit(1)
    
    self.product_type = product_type
    self.test_type = test_type
    self.request_id = request_id
    self.offer_id = offer_id
    self.postalCode = postal_code
    self.us_store_ids = store_ids
    self.initialize()

  def initialize(self):    
    request_label = '"USItemId"'
    if '=' in self.request_id:
      req_list = self.request_id.split('=')
      if req_list[0] == 'PRODUCT_ID':
        request_label = '"productId"'
      elif req_list[0] == 'US_ITEM_ID':
        request_label = '"USItemId"'
      self.request_id = '"' + req_list[1] + '"' if req_list[0] == 'PRODUCT_ID' else req_list[1] 
        
    self.product_context = '"productContexts": [{"productId": {' + request_label + ': '
    self.offer_context = '"offerContexts": [{"offerId": {"offerId": "'
    self.product_ids = '"productIds": [{' + request_label + ': '

  def generate_curls(self):
    """
     Generates curl requests for the provided arguments.
    """
    self.get_curl_request_from_template()
    import datetime
    now = datetime.datetime.today().strftime("%Y%m%d-%H%M%S")
    path = os.getcwd() + "/" + self.product_type + "-" + self.test_type + "-" + now + "/"
    self.create_new_curl_files(path)
    return path

  def get_curl_request_from_template(self):
    with open(FILE_NAME, 'r') as file:
      self.hw_data = file.readline()
      self.lw_data = file.readline()
      self.whoAmI_data = file.readline()
      print("hw_data: " + self.hw_data)
      print("lw_data: " + self.lw_data)
      print("whoAmI_data: " + self.whoAmI_data)

  def create_new_curl_files(self, path):
    try:
        os.mkdir(path)
    except OSError:
        print("Creation of the directory %s failed" % path)

    with open(CSV_FILE_NAME) as csv_file:
      csv_reader = csv.reader(csv_file, delimiter=',')
      count = 1
      for row in csv_reader:
        consumerId = row[1]
        curl_type = row[2]
        request_type = row[3]
        if curl_type == 'HW' and request_type == 'ProductContext':
          request_input = self.product_context + self.request_id + '}}]'
          data = self.hw_data.replace(REQUEST_INPUT, request_input)
        elif curl_type == 'HW' and request_type == 'OfferContext':
          request_input = self.offer_context + self.offer_id + '"}}]'
          data = self.hw_data.replace(REQUEST_INPUT, request_input)
        elif curl_type == 'LW' and request_type == 'ProductIds':
          request_input = self.product_ids + self.request_id + '}]'
          data = self.lw_data.replace(REQUEST_INPUT, request_input)
        elif curl_type == 'WhoAmI' and request_type == 'ProductIds':
          request_input = self.product_ids + self.request_id + '}]'
          data = self.whoAmI_data.replace(REQUEST_INPUT, request_input)

        responseGroups = row[4]
        verticalId = row[5]
        env = row[6]
        store_front_ids = ', "storeFrontIds": ['
        if row[7] and self.us_store_ids:
          if ',' in self.us_store_ids:
            us_store_ids_list = self.us_store_ids.split(',')
            store_ids_list = ['{"USStoreId": ' + usStoreId + '}' for usStoreId in us_store_ids_list]
            storeIds = ','.join(store_ids_list)
            store_front_ids += storeIds + ']'
          else:
            store_front_ids += '{"USStoreId": ' + self.us_store_ids + '}]'
        elif row[7] and self.us_store_ids is None:
          ## Skip rows which require storeIds, if not provided in input.
          continue
        else:
          store_front_ids = ''
        curl_request = (data.replace(RESPONSE_GROUPS, responseGroups).replace(CONSUMER_ID, consumerId).replace(VERTICAL_ID, verticalId)
          .replace(POSTAL_CODE, self.postalCode).replace(ENV, env).replace(STORE_IDS, store_front_ids))
        #print(curl_request+"\n")
        file_path = path + 'curl_req_'+str(count)+'.txt'
        f = open(file_path,'w')
        f.write(curl_request)
        f.close()
        count += 1

if __name__ == "__main__":
  icg = CurlGenerator(True)
  path_loc = icg.generate_curls()
  print("Curl generation completed at folder: " + path_loc)
