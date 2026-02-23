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

    params = {"input_file": str(input_json), "columns": ["title", "date", "format"]}
    request_id = append_request_row(client="AMC_Movies", params=params)

## How to Recieve Data:

To programmatically recieve data (reading the response fields), the Microservice will update the same row(matching the request_id) in request.csv:
    setting status as "processing" then "done" on success or "error" on failure. 
    The data will be exported from the JSON file and be sent as a CSV File for in its respective download folder. 
  
An example call in this code will be: 
    row = wait_for_response(request_id=request_id, timeout_seconds=30, poll_seconds=0.5)
    output_file = row.get("output_file", "").strip()
  
## UML Sequence Diagram
<img width="810" height="401" alt="image" src="https://github.com/user-attachments/assets/3efc57e1-d82e-444b-867b-d635e2ac7ae4" />


Communication between Angela and Ranson is through Discord. 

