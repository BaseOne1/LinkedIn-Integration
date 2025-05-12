import os
import requests
import pandas as pd
import fal_client
from openpyxl import load_workbook
 
# Set API key
api_key = '23dbd33e-402d-4a25-b609-25835fd0fae7:a41fea96ba25054c52b3e9b43b7a321a'
finetune_id = '7580067a-4326-454c-a66d-ac2cc2a7dde4'
os.environ['FAL_KEY'] = api_key
 
# Prompt for image generation
prompt = prompt
 
def on_queue_update(update):
    if isinstance(update, fal_client.InProgress):
        for log in update.logs:
            print(log["message"])
 
result = fal_client.subscribe(
    "fal-ai/flux-pro/v1.1-ultra-finetuned",
#    "fal-ai/flux/dev",
    arguments={
        "prompt": prompt,                   # Your descriptive text prompt for image generation
       #"control_image_url": "URL HERE",    # Referance image for input to image generation
        "guidance_scale": 10,                # How close you want the model to stick to your prompt - 1 to 40
        "seed": 0,                          # Seed for reproducibility; change as needed
        "sync_mode": False,                 # Wait for image generation before returning the response
        "num_images": 3,                    # Number of images to generate
        "enable_safety_checker": False,     # Enable or disable the safety checker
        "safety_tolerance": 6,              # Safety tolerance level, choose from 1 to 6
        "output_format": "jpeg",            # Choose 'jpeg' or 'png' for the output format
        "aspect_ratio": "21:9",              # Possible enum values: 21:9, 16:9, 4:3, 3:2, 1:1, 2:3, 3:4, 9:16, 9:21
#       "raw": False,                       # Generate less processed, more natural-looking images, NA with finetunes
        "finetune_id": finetune_id,         # ID of your specific finetuned model
        "finetune_strength": 0.7          # Adjust the influence of finetuning - 0 to 2  
        #Amara FT setting works best between 0.6 - 0.8
    },
    with_logs=True,
    on_queue_update=on_queue_update,
)
 
# Print API raw response
print("API Response:", result)
 
# Directory setup
image_dir = 'F:/Images/AriaEllison'
if not os.path.exists(image_dir):
    os.makedirs(image_dir)
 
# Path to the Excel file
file_path = 'F:/generated_images_info-AR1A.xlsx'
 
# Load existing Excel data while preserving formatting
if os.path.exists(file_path):
    try:
        old_df = pd.read_excel(file_path, engine='openpyxl')
    except Exception as e:
        print(f"Failed to read existing file: {e}")
        old_df = pd.DataFrame()
else:
    old_df = pd.DataFrame()
 
# Process multiple images and save metadata
if result and 'images' in result:
    new_entries = []
    for image_info in result['images']:
        image_url = image_info['url']
        print(f"Image URL: {image_url}")
 
        # Generate unique file name
        url_part = image_url.split('/')[-1].split('.')[0]
        file_name = f"Aria_{result['seed']}_{url_part}.jpeg"
        file_path_img = os.path.join(image_dir, file_name)
 
        # Download the image
        response = requests.get(image_url)
        if response.status_code == 200:
            with open(file_path_img, 'wb') as f:
                f.write(response.content)
            print(f"Image saved to {file_path_img}")
        else:
            print(f"Failed to download image, status code: {response.status_code}")
 
        # Collect metadata for Excel
        new_entries.append({
            'IMAGE': f'=IMAGE("{image_url}")',
            'URL': image_url,
            'File Name': file_name,
            'Width': image_info['width'],
            'Height': image_info['height'],
            'Content Type': image_info['content_type'],
            'Timings': result.get('timings', ''),
            'Seed': result['seed'],
            'NSFW Content': 'Yes' if result['has_nsfw_concepts'][0] else 'No',
            'Prompt': result['prompt']
        })
 
    # Convert new data to DataFrame
    new_df = pd.DataFrame(new_entries)
 
    # Append data to Excel without overwriting formatting
    with pd.ExcelWriter(file_path, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
        new_df.to_excel(writer, index=False, header=False, startrow=writer.sheets['Sheet1'].max_row)
 
    print(f"Data appended to {file_path}")
 
else:
    print("No images found in the result or error occurred.")