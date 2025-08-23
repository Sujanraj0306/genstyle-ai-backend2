import json
import os
import google.generativeai as genai
import traceback

# Configure the Gemini client from the environment variable
api_key = os.environ.get('GOOGLE_AI_API_KEY')
if not api_key:
    raise ValueError("Google AI API Key not found in environment variables")
genai.configure(api_key=api_key)

def lambda_handler(event, context):
    try:
        print("--- LISTING AVAILABLE MODELS ---")

        # Find all models that support the 'generateContent' method
        models_list = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                models_list.append(m.name)

        # Print the list of available models to the log
        print("Successfully found available models:")
        print(models_list)

        # Return this list to the frontend
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps(models_list)
        }

    except Exception as e:
        print(f"[ERROR] Function failed while listing models: {str(e)}")
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': { 'Access-Control-Allow-Origin': '*' },
            'body': json.dumps({'error': f"An error occurred: {str(e)}"})
        }
