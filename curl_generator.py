import sys
import csv

"""
  Generates curl_req_*.txt files for parity testing.
  Usage:
  $ python curl_generator.py <REQUEST_ID> <OFFER_ID> <POSTAL_CODE> <STORE_IDS>
"""
if len(sys.argv) not in [4, 5]:
  print("Invalid arguments!\nUsage:\n$ python curl_generator.py <REQUEST_ID> <OFFER_ID> <POSTAL_CODE> <STORE_IDS>")
  print('-- <REQUEST_ID>: can be specified with label PRODUCT_ID="sampleProductId" or US_ITEM_ID="sampleUSItemId". ' +  
        'If no label is provided REQUEST_ID is considered to be US_ITEM_ID by default.')
  print("-- <STORE_IDS>: can be optionally specified. Use comma separated values if more than one store_id needs to be specified.")
  print("Example:")
  print('$ python curl_generator.py 55107666 "D3409E9E783F4F29B9EEE2B3B8801492" "90001"')
  print('$ python curl_generator.py "PRODUCT_ID=3HD11CXDBNLK" "D3409E9E783F4F29B9EEE2B3B8801492" "90001" 2280')
  print('$ python curl_generator.py "US_ITEM_ID=55107666" "D3409E9E783F4F29B9EEE2B3B8801492" "90001" 2280,1122,2239')
  exit(1)

file_name = 'curl_template.txt'

RESPONSE_GROUPS = '$RESPONSE_GROUPS'
CONSUMER_ID = '$CONSUMER_ID'
REQUEST_INPUT = '$REQUEST_INPUT'
POSTAL_CODE = '$POSTAL_CODE'
VERTICAL_ID = '$VERTICAL_ID'
STORE_IDS = '$STORE_IDS'

request_id = sys.argv[1]
request_label = '"USItemId"'
if '=' in request_id:
  req_list = request_id.split('=')
  if req_list[0] == 'PRODUCT_ID':
    request_label = '"productId"'
  elif req_list[0] == 'US_ITEM_ID':
    request_label = '"USItemId"'
  request_id = '"' + req_list[1] + '"' if req_list[0] == 'PRODUCT_ID' else req_list[1] 

product_context = '"productContexts": [{"productId": {' + request_label + ': '
offer_context = '"offerContexts": [{"offerId": {"offerId": "'
product_ids = '"productIds": [{' + request_label + ': '

with open(file_name, 'r') as file:
  hw_data = file.readline()
  lw_data = file.readline()
  whoAmI_data = file.readline()
  print("hw_data: " + hw_data)
  print("lw_data: " + lw_data)
  print("whoAmI_data: " + whoAmI_data)

offer_id = sys.argv[2]
postalCode = sys.argv[3]
us_store_ids = sys.argv[4] if len(sys.argv) == 5 else None

with open('request_types.csv') as csv_file:
  csv_reader = csv.reader(csv_file, delimiter=',')
  count = 1
  for row in csv_reader:
    consumerId = row[1]
    curl_type = row[2]
    request_type = row[3]
    if curl_type == 'HW' and request_type == 'ProductContext':
      request_input = product_context + request_id + '}}]'
      data = hw_data.replace(REQUEST_INPUT, request_input)
    elif curl_type == 'HW' and request_type == 'OfferContext':
      request_input = offer_context + offer_id + '"}}]'
      data = hw_data.replace(REQUEST_INPUT, request_input)
    elif curl_type == 'LW' and request_type == 'ProductIds':
      request_input = product_ids + request_id + '}]'
      data = lw_data.replace(REQUEST_INPUT, request_input)
    elif curl_type == 'WhoAmI' and request_type == 'ProductIds':
      request_input = product_ids + request_id + '}]'
      data = whoAmI_data.replace(REQUEST_INPUT, request_input)

    responseGroups = row[4]
    verticalId = row[5]
    store_front_ids = ', "storeFrontIds": ['
    if row[6] and us_store_ids:
      if ',' in us_store_ids:
        us_store_ids_list = us_store_ids.split(',')
        store_ids_list = ['{"USStoreId": ' + usStoreId + '}' for usStoreId in us_store_ids_list]
        storeIds = ','.join(store_ids_list)
        store_front_ids += storeIds + ']'
      else:
        store_front_ids += '{"USStoreId": ' + us_store_ids + '}]'
    elif row[6] and us_store_ids is None:
      ## Skip rows which require storeIds, if not provided in input.
      continue
    else:
      store_front_ids = ''
    curl_request = (data.replace(RESPONSE_GROUPS, responseGroups).replace(CONSUMER_ID, consumerId).replace(VERTICAL_ID, verticalId)
      .replace(POSTAL_CODE, postalCode).replace(STORE_IDS, store_front_ids))
    #print(curl_request+"\n")
    f = open('curl_req_'+str(count)+'.txt','w')
    f.write(curl_request)
    f.close()
    count += 1
print("Curl generation completed.")
