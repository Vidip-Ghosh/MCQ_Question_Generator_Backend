from flask import Flask, request, jsonify
from flask_cors import CORS
from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import resources_pb2, service_pb2, service_pb2_grpc
from clarifai_grpc.grpc.api.status import status_code_pb2
import os
from dotenv import load_dotenv
import requests
import re
import json

load_dotenv()

app = Flask(__name__)
CORS(app)

PAT = os.environ["PAT"]
USER_ID = os.environ["USER_ID"]
APP_ID = os.environ['APP_ID']
MODEL_ID = os.environ['MODEL_ID']
MODEL_VERSION_ID = os.environ['MODEL_VERSION_ID']

print(PAT, USER_ID, APP_ID, MODEL_ID, MODEL_VERSION_ID)

channel = ClarifaiChannel.get_grpc_channel()
stub = service_pb2_grpc.V2Stub(channel)

metadata = (('authorization', 'Key ' + PAT),)

userDataObject = resources_pb2.UserAppIDSet(user_id=USER_ID, app_id=APP_ID)

@app.route('/',methods=['GET'])
def render(): 
    return "Hello from Home page"

@app.route('/complete',methods=['POST'])
def complete():
    try:
        raw_text = request.json['query']  
    except KeyError:
        return jsonify({'error': 'Invalid request, "query" field missing'}), 400

    userDataObject = resources_pb2.UserAppIDSet(user_id=USER_ID, app_id=APP_ID)

    post_model_outputs_response = stub.PostModelOutputs(
        service_pb2.PostModelOutputsRequest(
            user_app_id=userDataObject,
            model_id=MODEL_ID,
            version_id=MODEL_VERSION_ID,
            inputs=[
                resources_pb2.Input(
                    data=resources_pb2.Data(
                        text=resources_pb2.Text(
                            raw=raw_text
                        )
                    )
                )
            ]
        ),
        metadata=metadata
    )
    
    if post_model_outputs_response.status.code != status_code_pb2.SUCCESS:
        return jsonify({'error': f"Post model outputs failed, status: {post_model_outputs_response.status.description}"}), 500

    output = post_model_outputs_response.outputs[0]
    completion = output.data.text.raw

    completion = completion.replace("\n", " ")
    
    sentences = re.split(r'(?<=[.!?])\s+', completion)

    # Extracting questions and options
    questions = []
    options = []
    for sentence in sentences:
        if sentence.endswith('?'):
            questions.append(sentence)
        elif re.search(r'\b[A-D]\)', sentence):
            options.append(sentence)
    regex = r"([a-zA-Z]+) (\d+)"
    match = re.search(r"Answers:", completion)
    # print("Answers: ",match)
    answers_section = match.groups()
    keyword = 'Answers:'
    before_keyword, keyword, after_keyword = completion.partition(keyword)

    answers_array = after_keyword.split('\n')
    print(answers_array)

    print("Questions:")
    data = []
    for i, q in enumerate(questions, 1):
        data.append({
            "Question": q,
            "Options": options[i-1],
            # "Answer": answers_array
        })
    json_data = json.dumps(data, indent=4)
    return json_data

@app.route('/summarize', methods=['POST'])
def summarize():
    data = request.json
    text = data.get('text')

    def query(data):
        API_URL = "https://api-inference.huggingface.co/models/philschmid/bart-large-cnn-samsum"
        headers = {"Authorization": "Bearer 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"}
        response = requests.post(API_URL, headers=headers, json={"inputs": data})
        result = response.json()
        print(result)
        return result

    summarised_text = query(text)

    return jsonify(summarised_text)

if __name__ == '__main__':
    app.run(debug=True)
