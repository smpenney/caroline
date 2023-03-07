# Caroline's ACCIO server

## Requirements
* Simplified ACCIO server: [1.pdf](1.pdf)
* ACCIO server: [2.pdf](2.pdf)

## Test Cases
* Server handles incorrect port
* Server gracefully handles SIGINT signal
* Server accepts a connection
* Server accepts a connection and sends accio\r\n command
* Server starts receiving data
* Server accepts another connection after the first connection finished
* When server receives and process 10 connections simultaneously
* **Server aborts connection and write ERROR into corresponding file (resetting any received content) when it does not receive new data from client for more than 10 seconds.**
* Server accepts another connection after the first connection timed out
* Server successfully receives a small file (~500 bytes) using the submitted version of the client
    * Server correctly saves the file from the previous test
* Server successfully receives a small file (~500 bytes) using the instructor’s version of the client
    * Server correctly saves the file from the previous test
* Server successfully receives sequentially 10 large files (~10 MiBytes) using the submitted version of the client and saves all the files from the previous test in 1.file, 2.file, … 10.file
    * Same as previous but in parallel
* Server successfully receives sequentially 10 large files (~10 MiBytes) using the instructor’s version of the client and saves all the files from the previous test in 1.file, 2.file, … 10.file
    * Same as previous but in parallel
* Server successfully receives sequentially 10 large files (~10 MiBytes) using the instructor’s version of the client and saves all the files from the previous test in 1.file, 2.file, … 10.file (with emulated delays and/or transmission errors)
    * Same as previous but in parallel