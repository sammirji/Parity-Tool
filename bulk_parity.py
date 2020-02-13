from curl_generator import CurlGenerator
from parity_checker import ParityChecker
import sys
import csv

CSV_FILE_NAME = 'input_request_parameters.csv'

class BulkParity:
  '''
    Generates all the curl files and runs parity test against each of them.
  '''

  def __init__(self, is_arg):
    if is_arg:
      if len(sys.argv) != 3:
        print("Invalid Arguments provided!\nUsage:\n$ python bulk_parity.py <HOST_1> <HOST_2>")
        print("Example:")
        print("$ python bulk_parity.py 'localhost:8080' 'abc-non-site-facing.prod.domain.com'")
        print("$ python bulk_parity.py '10.1.10.10:8080' 'abc-non-site-facing.prod.domain.com'")
        sys.exit(1)
      self.host_1 = sys.argv[1]
      self.host_2 = sys.argv[2]

  def initialize_params(self, hostname_1, hostname_2):
    if hostname_1 is None or hostname_2 is None:
      print("Invalid Arguments provided! hostname_1 and hostname_2 should be provided!")
      sys.exit(1)
    self.host_1 = hostname_1
    self.host_2 = hostname_2

  def generate_all_curls(self):
    with open(CSV_FILE_NAME) as csv_file:
      csv_reader = csv.reader(csv_file, delimiter=',')
      for row in csv_reader:
        product_type = row[1]
        test_type = row[2]
        request_id = row[3]
        offer_id = row[4]
        postal_code = row[5]
        store_ids = row[6]
        abc_curl_gen = CurlGenerator(False)
        abc_curl_gen.initialize_params(product_type, test_type, request_id, offer_id, postal_code, store_ids)
        path_location = abc_curl_gen.generate_curls()
        print("Curl generation completed at folder: " + path_location)
        folder_index = path_location[:len(path_location)-1].rfind('/')
        folder_name = path_location[folder_index+1:len(path_location)-1] 

        parity_check = ParityChecker(False)
        parity_check.initialize_params(folder_name, self.host_1, self.host_2)
        parity_check.bulkProcessParity()

if __name__ == "__main__":
  bp = BulkParity(True)
  bp.generate_all_curls()
  print("Bulk parity run completed.")
