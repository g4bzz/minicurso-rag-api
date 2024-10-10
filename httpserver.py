from rag_gemini import pdf_response as rag_gemini
import asyncio
from quart_cors import cors
from quart import Quart, request, make_response
import warnings

warnings.filterwarnings("ignore")
app = Quart(__name__)
cors(app, allow_origin="http://localhost:4200") 


def setHeaders(response):
    response.headers['Access-Control-Allow-Origin'] = 'http://localhost:4200'
    response.headers['Access-Control-Allow-Methods'] = 'POST'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'


@app.route('/gemini', methods=['POST'])
async def get_response_atlas():
    data = await request.get_json()
    prompt = data.get('prompt')
    asyncResp = False
    try:
        asyncResp = data.get('stream')
    except Exception as error:
        print(error)

    response = await make_response(rag_gemini(prompt, asyncResp))
    response.content_type = 'application/json' 
    return response


@app.route("/", methods=['GET'])
async def get_home():
    response = await make_response("Servidor no ar!")
    return response
    
if __name__ == '__main__':
    asyncio.run(app.run(port=8000))

