import os
import logging
from flask import Flask, request, jsonify, render_template
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.efficientnet import preprocess_input
import numpy as np
import cv2
# Optional IoT integration (commented out for now)
# import paho.mqtt.client as mqtt
import boto3
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging and ensure logs directory exists
LOG_DIR = 'logs'
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOG_DIR, 'app.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Initialize Flask app
app = Flask(__name__)

# Load pre-trained model
MODEL_PATH = os.getenv('MODEL_PATH', 'models/waste_classification_model.h5')
try:
    model = load_model(MODEL_PATH)
    class_names = ['Plastic', 'Paper', 'Metal', 'Glass', 'Organic', 'E-Waste', 'Hazardous']
    logging.info(f"Model loaded successfully from {MODEL_PATH}.")
except Exception as e:
    logging.error(f"Failed to load model from {MODEL_PATH}: {e}")
    raise RuntimeError("Model loading failed. Check logs for details.")

# Optional IoT client setup (commented out for now)
# MQTT_BROKER = os.getenv('MQTT_BROKER', "broker.hivemq.com")
# MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
# mqtt_client = mqtt.Client()
#
# def on_mqtt_connect(client, userdata, flags, rc):
#     if rc == 0:
#         logging.info(f"Connected to MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
#     else:
#         logging.error(f"Failed to connect to MQTT Broker, return code {rc}")
#
# mqtt_client.on_connect = on_mqtt_connect
# try:
#     mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
#     mqtt_client.loop_start()
# except Exception as e:
#     logging.error(f"MQTT connection error: {e}")

# AWS S3 client setup
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
S3_BUCKET = os.getenv('S3_BUCKET')

if not all([AWS_ACCESS_KEY, AWS_SECRET_KEY, S3_BUCKET]):
    logging.warning("AWS credentials or bucket name not fully set in environment variables.")
    s3 = None
else:
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY
    )

# Preprocess image for model inference
def preprocess_image(image):
    """
    Preprocess input image for model inference.
    Args:
        image (numpy.ndarray): Input image.
    Returns:
        numpy.ndarray: Preprocessed image ready for model prediction.
    """
    resized_image = cv2.resize(image, (224, 224))  # Resize to match model input size
    normalized_image = preprocess_input(resized_image)  # Normalize pixel values
    return np.expand_dims(normalized_image, axis=0)  # Add batch dimension

# Disposal instructions mapping
DISPOSAL_INSTRUCTIONS = {
    'Plastic': "Dispose of plastic in the recycling bin.",
    'Paper': "Dispose of paper in the recycling bin.",
    'Metal': "Dispose of metal in the recycling bin.",
    'Glass': "Dispose of glass in the recycling bin.",
    'Organic': "Compost organic waste.",
    'E-Waste': "Take e-waste to an authorized recycling center.",
    'Hazardous': "Dispose of hazardous waste at a designated facility."
}

# Route for the main page
@app.route('/')
def index():
    """
    Render the main page of the application.
    """
    return render_template('index.html')

# Route for predicting waste type
@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Validate file upload
        if 'file' not in request.files:
            logging.warning("No file uploaded.")
            return jsonify({'error': 'No file uploaded.'}), 400
        
        file = request.files['file']
        if file.filename == '':
            logging.warning("Empty filename provided.")
            return jsonify({'error': 'Empty filename.'}), 400
        
        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'bmp'}
        if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            logging.warning(f"Unsupported file type uploaded: {file.filename}")
            return jsonify({'error': 'Unsupported file type. Allowed types: png, jpg, jpeg, bmp.'}), 400
        
        # Read and preprocess image
        file_content = file.read()
        if not file_content:
            logging.warning(f"Uploaded file is empty: {file.filename}")
            return jsonify({'error': 'Empty file uploaded.'}), 400
        
        image = cv2.imdecode(np.frombuffer(file_content, np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            logging.warning(f"Failed to decode image: {file.filename}")
            return jsonify({'error': 'Invalid image file.'}), 400
        
        processed_image = preprocess_image(image)
        
        # Make prediction
        predictions = model.predict(processed_image)
        predicted_class = class_names[np.argmax(predictions)]
        
        # Optional IoT integration (commented out for now)
        # try:
        #     if mqtt_client.is_connected():
        #         mqtt_client.publish("waste/sort", predicted_class)
        #         logging.info(f"Prediction published to IoT: {predicted_class}")
        #     else:
        #         logging.warning("MQTT client is not connected. Skipping IoT publish.")
        # except Exception as e:
        #     logging.error(f"Failed to publish MQTT message: {e}")
        
        # Upload image to cloud storage
        if s3:
            try:
                from io import BytesIO
                s3.upload_fileobj(BytesIO(file_content), S3_BUCKET, f"uploads/{file.filename}")
                logging.info(f"Image uploaded to S3: {file.filename}")
            except Exception as e:
                logging.error(f"Failed to upload image to S3: {e}")
        else:
            logging.warning("S3 client not configured. Skipping image upload.")
        
        # Return response with disposal instructions
        return jsonify({
            'prediction': predicted_class,
            'disposal_instructions': DISPOSAL_INSTRUCTIONS.get(predicted_class, "No specific instructions available.")
        })
    
    except Exception as e:
        logging.error(f"Error during prediction: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred.'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
