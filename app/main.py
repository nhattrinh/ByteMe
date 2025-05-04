from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import json
import pika
import os
import redis
import asyncio
from dotenv import load_dotenv


load_dotenv()


app = FastAPI(title="ByteMe")


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


# Redis connection
def get_redis_client():
    return redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379))
    )


# RabbitMQ connection
def get_rabbitmq_connection():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=os.getenv("RABBITMQ_HOST", "localhost"))
    )
    return connection


@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/index.html") as f:
        return f.read()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    redis_client = get_redis_client()
    
    try:
        while True:
            data = await websocket.receive_text()
            # Parse the code submission
            submission = json.loads(data)
            
            # Send to RabbitMQ queue
            connection = get_rabbitmq_connection()
            channel = connection.channel()
            channel.queue_declare(queue='code_execution')
            
            channel.basic_publish(
                exchange='',
                routing_key='code_execution',
                body=json.dumps(submission)
            )
            
            # Send acknowledgment back to client
            await websocket.send_text(json.dumps({
                "status": "received",
                "message": "Code submitted for execution"
            }))
            
            connection.close()
            
            # Poll for results
            while True:
                result = redis_client.get(f"result:{submission['timestamp']}")
                if result:
                    result_data = json.loads(result)
                    await websocket.send_text(json.dumps({
                        "status": "completed",
                        "message": "Execution completed",
                        "result": result_data['stdout'] + result_data['stderr']
                    }))
                    break
                await asyncio.sleep(1)
            
    except Exception as e:
        await websocket.close()
        print(f"WebSocket error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
