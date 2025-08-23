import json
import boto3
import os
import google.generativeai as genai
import traceback

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ClothingItems')

api_key = os.environ.get('GOOGLE_AI_API_KEY')
if not api_key:
    raise ValueError("Google AI API Key not found")
genai.configure(api_key=api_key)

def lambda_handler(event, context):
    try:
        selected_items = []
        # Check if the frontend sent a list of selected items
        if event.get('body'):
            # An empty list from the frontend becomes '[]', which is valid JSON
            body_content = json.loads(event['body'])
            if body_content: # Ensure the list is not empty
                 selected_items = body_content

        if selected_items:
            # If items were selected, fetch only those from DynamoDB
            items_to_process = []
            for item_data in selected_items:
                response = table.get_item(Key={'itemId': item_data['itemId']})
                if 'Item' in response:
                    items_to_process.append(response['Item'])
        else:
            # Otherwise, use all items in the wardrobe
            response = table.scan()
            items_to_process = response.get('Items', [])

        if not items_to_process:
            return {'statusCode': 200, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps([])}

        # This is the corrected, complete prompt
        prompt_parts = [
            "You are a virtual fashion stylist.",
            "Analyze the following clothing items from a user's wardrobe. Each item has a unique 'itemId' provided after the image.",
            "Create up to 3 best outfit combinations. An outfit must consist of one top and one bottom.",
            "Return your answer ONLY as a valid JSON array of objects. Each object must have three keys: 'top_item_id' (string), 'bottom_item_id' (string), and 'suggestion' (string).",
            "Do not include any other text, markdown, or explanations outside of the JSON array.",
            "Here are the items:"
        ]

        for item in items_to_process:
            s3_response = s3_client.get_object(Bucket='genstyle-wardrobe-images', Key=item['itemId'])
            image_bytes = s3_response['Body'].read()
            prompt_parts.append({'mime_type': 'image/jpeg', 'data': image_bytes})
            prompt_parts.append(f"itemId: {item['itemId']}")
            
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
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': { 'Access-Control-Allow-Origin': '*' },
            'body': json.dumps({'error': f"An error occurred: {str(e)}"})
        }
