# Parity Test Tool - Python

Run parity test between 2 environments (or hosts) for multiple number of curls, with a single command line statement. 

**Tool usage details:**

We can use single command to generate `curl_*.txt` files and a single command to run parity for all the generated curls.

* As a **pre-requisite**, run the below command: 

```
$ sudo pip install -r requirements.txt
```
  
* To generate the `curl_*.txt` files, run the below command:

```
$ python iro_curl_generator.py <REQUEST_ID> <OFFER_ID> <POSTAL_CODE> <STORE_IDS>
-- <REQUEST_ID>: can be specified with label PRODUCT_ID="sampleProductId" or US_ITEM_ID="sampleUSItemId". If no label is provided REQUEST_ID is considered to be US_ITEM_ID by default.
-- <STORE_IDS>: can be optionally specified. Use comma separated values if more than one store_id needs to be specified.
Example: 
$ python iro_curl_generator.py 55107666 "D3409E9E783F4F29B9EEE2B3B8801492" "90001"
$ python iro_curl_generator.py "PRODUCT_ID=3HD11CXDBNLK" "D3409E9E783F4F29B9EEE2B3B8801492" "90001" 2280
$ python iro_curl_generator.py "US_ITEM_ID=55107666" "D3409E9E783F4F29B9EEE2B3B8801492" "90001" 2280,1122,2239
```
Additionally, you can add-on your own curl files. Just create the filename with the pattern: `curl_req_*.txt` and add `$HOST` keyword for the hostname in the curl, so that the hostname gets dynamically picked up for parity.

* Once the `curl_*.txt` files are generated, use the below command to run the parity for all curls:

```
$ python parity_checker.py 'iro-non-site-facing.prod-non-site-facing.iro.services.glb.prod.walmart.com' 'localhost:8080'
```
You should find HTML reports generated in the same (current) folder with filename syntax: `parity_results-curl_req*.html`

* We can also specifically run parity for single `curl_*.txt` file. Use the below command:

```
$ python parity_checker.py 'curl_req_1.txt' 'iro-non-site-facing.prod-non-site-facing.iro.services.glb.prod.walmart.com' 'localhost:8080'
```

** Sample HTML report: **

![Sample Report](parity_results.png)