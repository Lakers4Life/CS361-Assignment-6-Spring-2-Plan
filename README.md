# CS361-Exporting-Microservice
A repository for the microservice - Exporting CSV Files from File

## Overview:

The microservice specifically is designed to export the data from our Main Programs as a CSV file that will be used for various different uses, depending on the user. The microservice listens for export requests written to a shared request.csv file. When it finds a new rquest,it reads that input data from a JSON file specified in the request (for my AMC A-List project, it would be the amc_profiles.json file), and writes the exported CSV to an output file path. The Microservice is designed to be used for different client programs using the same request/response contract. 

## How to Request Data: 

Requesting Data is done by when the client will append a row to the request.csv with:
  status: "request"
  request_id: "unique string"
  client: "AMC_Movies", "Study_Tracker", "Subway_Times"
  action: "export_csv" 
  params: "the JSON String"
  created_at: "time_stamp"
  output file: ""
  error: ""

The params must be a JSON object string with the input_file string which is the path to a JSON file containing the data to be exported. It could be different depending on which main program is using the Microservvice. 

An example call in code would be:

  REQUEST_FILE = Path("request.csv")
  FIELDS = ["status","request_id","client","action","params","created_at","output_file","error"]
  
  request_id = str(uuid.uuid4())
  
  params = {"input_file": "amc_export_data.json", "columns": ["title"]}
  
  row = {
      "status": "request",
      "request_id": request_id,
      "client": "AMC_Movies",
      "action": "export_csv",
      "params": json.dumps(params),
      "created_at": datetime.now().isoformat(timespec="seconds"),
      "output_file": "",
      "error": ""
  }
  
  with REQUEST_FILE.open("a", newline="", encoding="utf-8") as f:
      csv.DictWriter(f, fieldnames=FIELDS).writerow(row)
  
  print("Sent request_id:", request_id)

## How to Recieve Data:

To programmatically recieve data (reading the response fields), the Microservice will update the same row(matching the request_id) in request.csv:
  setting status as "processing" then "done" on success or "error" on failure. 
  The data will be exported from the JSON file and be sent as a CSV File for in its respective download folder. 
  
An example call in this code will be: 

  REQUEST_FILE = Path("request.csv")
  
  def wait_for_result(request_id: str, timeout=30):
      start = time.time()
      while time.time() - start < timeout:
          with REQUEST_FILE.open("r", newline="", encoding="utf-8") as f:
              for row in csv.DictReader(f):
                  if row["request_id"] == request_id and row["status"] in ("done", "error"):
                      return row
          time.sleep(0.5)
      raise TimeoutError("No response yet")
  
  resp = wait_for_result("PUT_REQUEST_ID_HERE")
  
  if resp["status"] == "done":
      print("CSV created at:", resp["output_file"])
  else:
      print("Error:", resp["error"])

The UML Sequence Diagram is attached below:
<img width="810" height="401" alt="image" src="https://github.com/user-attachments/assets/3efc57e1-d82e-444b-867b-d635e2ac7ae4" />


Communication between Angela and Ranson is through Discord. 

