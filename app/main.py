# Imports


import os
import time 
import json
import logging
import requests
import random
import asyncio
from io import StringIO
from app.utils import *
from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse


import dotenv
dotenv.load_dotenv()


# Configure the logging module
logging.basicConfig(level=logging.INFO)

# App


app = FastAPI()



@app.post("/ingest_data")
async def ingest_data(file: UploadFile):

    '''
    
    This endpoint is used to ingest data from a file and return it contents without parsing it
    
    '''
    # Read the file contents
    contents = await file.read()
    
    # Decode the bytes to string (assuming it's a text file)
    text_content = contents.decode("utf-8")
    
    # Process the text content as needed
    # For now, just return the content
    return {"message": "File processed successfully", "content": text_content}


@app.post("/check_lines")
async def process_data(file: UploadFile = File(...)):
    '''
    This endpoint processes a file and returns its contents as a list of dictionaries
    '''
    # Read the file contents
    contents = await file.read()
    
    # Decode the bytes to string (assuming it's a text file)
    text_content = contents.decode("utf-8")
    
    # Separate by each line:
    lines = [ {"original_line":line.replace("&nbsp;", "").split('\t')} for line in text_content.split('\n')[3:]]


    # Eliminate &nbsp


    return lines



from pydantic import BaseModel
from typing import List

class Input(BaseModel):
    original_line: List[str]

@app.post("/generate_sentences")
async def generate_sentences_data(input: Input) -> Dict:
    '''
    Process the input and generate sentences
    '''
    
    # Convert Pydantic model to dictionary
    input_dict = input.model_dump()
    
    # Call the generate_sentences function
    result = await generate_sentences(input_dict)
    
    return result 


@app.post("/process_file")
async def process_file(file: UploadFile = File(...)):

    '''
    This endpoint processes a file and returns its contents as a list of dictionaries
    '''
    # Read the file contents
    contents = await file.read()
    
    # Decode the bytes to string (assuming it's a text file)
    text_content = contents.decode("utf-8")
    
    # Separate by each line:
    lines = [ {"original_line":line.replace("&nbsp;", "").split('\t')} for line in text_content.split('\n')[3:]]

    # Create a semaphore to limit concurrent requests to 10
    semaphore = asyncio.Semaphore(15)

    # Process all lines concurrently with random delays
    async def process_line(line):
        async with semaphore:
            try:
                # Add random sleep between 1 and 3 seconds to prevent simultaneous calls
                sleep_time = random.uniform(0, 1)
                await asyncio.sleep(sleep_time)
                
                _ = await generate_sentences(line)
                line['oraciones'] = _.get('oraciones', [])
            except Exception as e:
                print(f"Error processing line: {e}")
                line['oraciones'] = []
            return line
    
    # Create tasks for all lines and wait for all to complete
    tasks = [process_line(line) for line in lines]
    lines = await asyncio.gather(*tasks)

    return lines





