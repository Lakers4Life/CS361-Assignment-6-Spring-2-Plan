# CS361-Assignment-6-Spring-2-Plan
A repository for the microservice - Exporting CSV Files from File

The microservice specifically is designed to export the data from our Main Programs as a CSV file that will be used for various different uses, depending on the user. 

Any main programs that will use this microservice will programmatically request data through a file-based communication pipeline by reading and writing a shared CSV file that the UI will update with request rows and will be responded with a response row. The main program will have a request row - status: "request", request_id = "unique per request", client = "Subway_Times, "Study_Tracker" or "AMC_Movies", Action - "Get_Arrival_Times", "Log_Hours", Params (Request Parameters for the data that will be exported depending on the Main Program), and Created_At = "TimeStamp." The Microservice will then check the CSV file over and over again and act when it sees a request that it hasn't handled yet. The microservice will then write a response back to the same file. 

Communication between Angela and Ranson is through Discord. 

