import json
import boto3
import os
import google.generativeai as genai
import traceback

# Initialize AWS and Google AI clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ClothingItems')

# Configure the Gemini client from the environment variable
api_key = os.environ.get('GOOGLE_AI_API_KEY')
if not api_key:
    raise ValueError("Google AI API Key not found in environment variables")
genai.configure(api_key=api_key)

def lambda_handler(event, context):
    try:
        response = table.scan()
        items = response.get('Items', [])

        if not items:
            return {'statusCode': 200, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps([])}

        prompt_parts = [
            "You are a virtual fashion stylist.",
            "Analyze the following clothing items from a user's wardrobe. Each item has a unique 'itemId' provided after the image.",
            "Create up to 3 best outfit combinations. An outfit must consist of one top and one bottom.",
            "Return your answer ONLY as a valid JSON array of objects. Each object must have three keys: 'top_item_id' (string), 'bottom_item_id' (string), and 'suggestion' (string).",
            "Do not include any other text, markdown, or explanations outside of the JSON array.",
            "Here are the items:"
        ]

        for item in items:
            s3_response = s3_client.get_object(Bucket='genstyle-wardrobe-images', Key=item['itemId'])
            image_bytes = s3_response['Body'].read()
            
            prompt_parts.append({'mime_type': 'image/jpeg', 'data': image_bytes})
            prompt_parts.append(f"itemId: {item['itemId']}")
            
        # Use the correct model name from the list you provided
        model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
        response = model.generate_content(prompt_parts)
        
        json_response_text = response.text.replace("```json", "").replace("```", "").strip()
        outfits = json.loads(json_response_text)
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps(outfits)
        }

    except Exception as e:
        print(f"[ERROR] Function failed: {str(e)}")
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': { 'Access-Control-Allow-Origin': '*' },
            'body': json.dumps({'error': f"An error occurred: {str(e)}"})
        }
