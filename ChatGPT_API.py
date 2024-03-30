from flask import Flask, request, jsonify
from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import resources_pb2, service_pb2, service_pb2_grpc
from clarifai_grpc.grpc.api.status import status_code_pb2

app = Flask(__name__)

PAT = '65bf3f1ed0ce4d7f83412c32847d91d2'
USER_ID = 'openai'
APP_ID = 'chat-completion'
MODEL_ID = 'gpt-4-turbo'
MODEL_VERSION_ID = '182136408b4b4002a920fd500839f2c8'

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

    return jsonify({'completion': completion})

if __name__ == '__main__':
    app.run(debug=True)