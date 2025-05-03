import pika
import json
import os
import subprocess
import tempfile
import redis
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import torch
from dotenv import load_dotenv


load_dotenv()


def data_fetch(data_path):
    """Fetch and load data from a file."""
    try:
        if data_path.endswith('.csv'):
            return pd.read_csv(data_path)
        elif data_path.endswith('.npy'):
            return np.load(data_path)
        else:
            raise ValueError(f"Unsupported file format: {data_path}")
    except Exception as e:
        raise RuntimeError(f"Error fetching data: {str(e)}")


def data_preprocessing(data, target_column=None, test_size=0.2):
    """Preprocess the data for machine learning."""
    try:
        if target_column:
            X = data.drop(columns=[target_column])
            y = data[target_column]
        else:
            X = data
            y = None

        # Handle missing values
        X = X.fillna(X.mean())

        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        if y is not None:
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=test_size, random_state=42
            )
            return X_train, X_test, y_train, y_test, scaler
        return X_scaled, scaler
    except Exception as e:
        raise RuntimeError(f"Error in data preprocessing: {str(e)}")


def train(X_train, y_train, model_type='linear', **kwargs):
    """Train a machine learning model."""
    try:
        if model_type == 'linear':
            from sklearn.linear_model import LinearRegression
            model = LinearRegression(**kwargs)
        elif model_type == 'random_forest':
            from sklearn.ensemble import RandomForestRegressor
            model = RandomForestRegressor(**kwargs)
        elif model_type == 'neural_network':
            model = torch.nn.Sequential(
                torch.nn.Linear(X_train.shape[1], 64),
                torch.nn.ReLU(),
                torch.nn.Linear(64, 1)
            )
            criterion = torch.nn.MSELoss()
            optimizer = torch.optim.Adam(model.parameters())
            
            X_tensor = torch.FloatTensor(X_train)
            y_tensor = torch.FloatTensor(y_train.values)
            
            for epoch in range(100):
                optimizer.zero_grad()
                outputs = model(X_tensor)
                loss = criterion(outputs, y_tensor)
                loss.backward()
                optimizer.step()
            return model
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
        
        model.fit(X_train, y_train)
        return model
    except Exception as e:
        raise RuntimeError(f"Error in model training: {str(e)}")


def execute_code(code):
    """Execute the provided code with predefined ML functions."""
    # Create a temporary file to store the code
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as temp:
        # Add imports and function definitions
        temp.write(b"import numpy as np\nimport pandas as pd\n")
        temp.write(b"from sklearn.model_selection import train_test_split\n")
        temp.write(b"from sklearn.preprocessing import StandardScaler\n")
        temp.write(b"import torch\n\n")
        temp.write(code.encode())
        temp_path = temp.name
    
    try:
        # Execute the code and capture output
        result = subprocess.run(
            ['python', temp_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Clean up the temporary file
        os.unlink(temp_path)
        
        return {
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        os.unlink(temp_path)
        return {
            'stdout': '',
            'stderr': 'Execution timed out after 30 seconds',
            'returncode': 1
        }
    except Exception as e:
        os.unlink(temp_path)
        return {
            'stdout': '',
            'stderr': str(e),
            'returncode': 1
        }


def main():
    """Main function to run the worker."""
    # Connect to Redis for result storage
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379))
    )
    
    # Connect to RabbitMQ
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=os.getenv('RABBITMQ_HOST', 'localhost'))
    )
    channel = connection.channel()
    
    # Declare the queue
    channel.queue_declare(queue='code_execution')
    
    def callback(ch, method, properties, body):
        try:
            # Parse the message
            submission = json.loads(body)
            code = submission['code']
            
            # Execute the code
            result = execute_code(code)
            
            # Store the result in Redis
            redis_client.set(
                f"result:{submission['timestamp']}",
                json.dumps(result),
                ex=3600  # Expire after 1 hour
            )
            
            # Acknowledge the message
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            print(f"Error processing message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag)
    
    # Start consuming messages
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='code_execution', on_message_callback=callback)
    
    print('Worker started. Waiting for messages...')
    channel.start_consuming()


if __name__ == '__main__':
    main()
