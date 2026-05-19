#!/bin/bash

# Testing file upload
echo "Testing file upload..."
curl -X POST \
  'http://localhost:8000/uploadfile/' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@/usercode/obama.txt;type=text/plain'
echo ""
echo ""

# Testing the root endpoint
echo "Testing the root endpoint..."
curl -X GET 'http://localhost:8000/' -H 'accept: application/json'
echo ""
echo ""

# Wait for 30 seconds for background chunking and embedding
echo "Waiting for 30 seconds before testing question answering..."
sleep 30

# Testing question answering
echo "Testing question answering..."
curl -X POST \
  'http://localhost:8000/ask/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "question": "When was Obama president?",
    "file_id": 1
  }'
echo ""
echo ""

# Testing find similar chunks
echo "Testing find similar chunks..."
curl -X GET \
  'http://localhost:8000/find-similar-chunks/1?query=Obama+president' \
  -H 'accept: application/json'
echo ""
echo "All tests done!"