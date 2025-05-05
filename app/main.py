from fastapi import FastAPI, WebSocket, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
import json
import pika
import os
import redis
import asyncio
from dotenv import load_dotenv
import shutil
from pathlib import Path


load_dotenv()


# Configure CORS middleware
middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
]


app = FastAPI(title="ByteMe", middleware=middleware)


# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# Redis connection
def get_redis_client():
    try:
        client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            socket_timeout=5,  # 5 seconds timeout
            socket_connect_timeout=5,  # 5 seconds connection timeout
            retry_on_timeout=True,
            decode_responses=True
        )
        # Test the connection
        client.ping()
        return client
    except redis.ConnectionError as e:
        print(f"Redis connection error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected Redis error: {e}")
        raise


# RabbitMQ connection
def get_rabbitmq_connection():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=os.getenv("RABBITMQ_HOST", "localhost"))
    )
    return connection


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Save the file
        file_path = UPLOAD_DIR / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {"filename": file.filename, "status": "success"}
    except Exception as e:
        return {"error": str(e), "status": "error"}


@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/index.html") as f:
        return f.read()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print("New WebSocket connection attempt")
    try:
        await websocket.accept()
        print("WebSocket connection accepted")
        
        try:
            redis_client = get_redis_client()
            print("Redis connection established")
        except Exception as e:
            print(f"Failed to connect to Redis: {e}")
            await websocket.send_text(json.dumps({
                "status": "error",
                "message": "Failed to connect to Redis server",
                "type": "status"
            }))
            return
        
        while True:
            try:
                data = await websocket.receive_text()
                print(f"Received data from client: {data}")
                
                # Parse the code submission
                try:
                    submission = json.loads(data)
                    print(f"Parsed submission: {submission}")
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    await websocket.send_text(json.dumps({
                        "status": "error",
                        "message": f"Invalid JSON format: {str(e)}",
                        "type": "status"
                    }))
                    continue
                
                # Validate submission
                if 'code' not in submission or 'timestamp' not in submission:
                    print("Missing required fields in submission")
                    await websocket.send_text(json.dumps({
                        "status": "error",
                        "message": "Missing required fields in submission",
                        "type": "status"
                    }))
                    continue
                
                # Send to RabbitMQ queue
                try:
                    connection = get_rabbitmq_connection()
                    channel = connection.channel()
                    channel.queue_declare(queue='code_execution')
                    
                    # Send initial status
                    await websocket.send_text(json.dumps({
                        "status": "received",
                        "message": "Code submitted for execution",
                        "type": "status"
                    }))
                    
                    channel.basic_publish(
                        exchange='',
                        routing_key='code_execution',
                        body=json.dumps(submission)
                    )
                    print("Message published to RabbitMQ")
                    
                    connection.close()
                except Exception as e:
                    print(f"RabbitMQ error: {e}")
                    await websocket.send_text(json.dumps({
                        "status": "error",
                        "message": f"Failed to publish to queue: {str(e)}",
                        "type": "status"
                    }))
                    continue
                
                # Poll for results
                max_attempts = 60  # 1 minute timeout
                attempts = 0
                while attempts < max_attempts:
                    try:
                        result = redis_client.get(f"result:{submission['timestamp']}")
                        if result:
                            result_data = json.loads(result)
                            # Send execution output
                            await websocket.send_text(json.dumps({
                                "status": "completed",
                                "message": "Execution completed",
                                "result": result_data['stdout'] + result_data['stderr'],
                                "type": "output"
                            }))
                            print("Execution completed, results sent")
                            break
                        # Send progress update
                        await websocket.send_text(json.dumps({
                            "status": "running",
                            "message": "Executing code...",
                            "type": "status"
                        }))
                        attempts += 1
                        await asyncio.sleep(1)
                    except redis.ConnectionError as e:
                        print(f"Redis connection error during polling: {e}")
                        await websocket.send_text(json.dumps({
                            "status": "error",
                            "message": "Lost connection to Redis server",
                            "type": "status"
                        }))
                        break
                    except Exception as e:
                        print(f"Error during result polling: {e}")
                        await websocket.send_text(json.dumps({
                            "status": "error",
                            "message": f"Error during execution: {str(e)}",
                            "type": "status"
                        }))
                        break
                
                if attempts >= max_attempts:
                    await websocket.send_text(json.dumps({
                        "status": "error",
                        "message": "Execution timed out",
                        "type": "status"
                    }))
                
            except Exception as e:
                print(f"Error processing message: {str(e)}")
                print(f"Error type: {type(e)}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                await websocket.send_text(json.dumps({
                    "status": "error",
                    "message": f"Error processing message: {str(e)}",
                    "type": "status"
                }))
            
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        try:
            await websocket.send_text(json.dumps({
                "status": "error",
                "message": f"Error: {str(e)}",
                "type": "status"
            }))
        except:
            pass
        try:
            await websocket.close()
        except:
            pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
