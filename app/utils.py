import pandas as pd
from io import StringIO
from html import unescape
import openai
import json
import os
import dotenv
dotenv.load_dotenv()


def parse_as_table(text_data):

    '''
    Parses the txt file as a pandas dataframe
    
    '''
    file_like = StringIO(text_data)
    # Load into a DataFrame, skipping metadata lines
    df = pd.read_csv(
        file_like,
        index_col=False,
        sep='\t',
        header=None,
        comment='#',
        names=['English', 'Spanish']
    )

    # Decode HTML entities like &nbsp;
    df = df.applymap(lambda x: unescape(str(x)) if pd.notnull(x) else x)

    # Drop empty rows if both columns are missing
    df.dropna(how='all', inplace=True)

    return df


class OpenAIService:

    def __init__(self, model = 'gpt-4o-mini'):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.model = model
        self.base_url = "https://api.openai.com/v1"
        

    async def __call__(self, messages, schema):

        client = openai.AsyncOpenAI(api_key = self.api_key, base_url=self.base_url)
        response = await client.chat.completions.parse(
            model = self.model,
            messages = messages,
            temperature=0,
            max_tokens=3500,
            top_p=1,
            frequency_penalty=0, 
            presence_penalty =0,
            response_format = schema # Pydantic model
        )

        return json.loads(response.choices[0].message.content)

    async def __str_call__(self, messages) -> str:

        client = openai.AsyncOpenAI(api_key = self.api_key, base_url=self.base_url)
        response = await client.chat.completions.create(
            model = self.model,
            messages = messages,
            temperature=0,
            max_tokens=3500,
            top_p=1,
            frequency_penalty=0, 
            presence_penalty =0,
            response_format = None
        )

        return response.choices[0].message.parsed
    
from typing import Dict

from pydantic import BaseModel, Field
from typing import List

async def generate_sentences(input : Dict) -> Dict:


    english_word = input['original_line'][0]
    spanish_meanings = input['original_line'][1]



    class SentenceItem(BaseModel):
        significado: str = Field(description="The Spanish meaning of the word")
        oracion_en_ingles: str = Field(description="English sentence using the word")
        oracion_en_espanol: str = Field(description="Exact translation of the sentence in spanish + the english word inside parentheses as it appears in the generated english sentence")

    class SentencesResponse(BaseModel):
        oraciones: List[SentenceItem] = Field(
            description="List of sentences in english with their Spanish meanings",
            min_items=0
        )

    schema = SentencesResponse

    messages = [
        {
            'role': 'system',
            'content': "You are a helpful English and Spanish teacher teacher that help his students with any questions or tasks they might have"
        },
        {
            "role": "user",
                        "content": f"""Make me an American English sentence with the following word '{english_word}', one for each of its Spanish meanings that will be provided below and that will be separated by commas or slashes:
              
             ### Spanish meanings ###
             '{spanish_meanings}'

                           If the english word has more Spanish meanings that are not included above, make me a sentence with ALL the meanings that this word has in Spanish from Spain. The sentences cannot contain more than 80 characters
              
              For each English sentence you create, provide its exact Spanish translation. 
              You must put at the end of each Spanish translation the English word in parentheses exactly as it appears in the English sentence (with the same conjugation/tense).
        
              Example:
              - English: "I run every morning"
              - Spanish: "Corro cada mañana (run)"
             
             """
        }
    ]
    res = await OpenAIService(model = 'gpt-4o-mini').__call__(messages, schema)
    return res