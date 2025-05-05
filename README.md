# ByteMe - ML Pipeline Development Platform

ByteMe is a web-based platform that allows users to develop and test machine learning pipelines in a streamlined environment. It provides a code editor with ML templates, real-time execution, and model deployment capabilities.

## Features

- Web-based code editor with Monaco (VS Code's editor)
- Predefined ML functions for common tasks:
  - `data_fetch`: Load data from CSV or NPY files
  - `data_preprocessing`: Handle data preprocessing with scaling and train-test split
  - `train`: Train ML models (Linear Regression, Random Forest, Neural Network)
- Real-time code execution status updates
- Distributed execution using Kubernetes
- Task queue management with RabbitMQ
- Result storage with Redis

## Prerequisites

- Python 3.9-3.12 (PyTorch compatibility)
- Docker
- Kubernetes cluster
- RabbitMQ
- Redis

## Architecture and Data Flow

### High-Level Architecture

![High Level Architecture](docs/high_level_arch.png)

This architecture represents the core components of the ByteMe platform:

1. **Web Interface Layer**
   - Frontend Framework: React.js with TypeScript
   - Code Editor: Monaco Editor (VS Code's editor)
   - UI Components: Material-UI (MUI)
   - State Management: Redux Toolkit
   - Build Tool: Vite
   - Testing: Jest and React Testing Library
   - Provides the user interface for code editing and file uploads
   - Handles real-time output display and model downloads
   - Communicates with the backend via WebSocket

2. **WebSocket Server**
   - Framework: Flask-SocketIO
   - Protocol: WebSocket with Socket.IO
   - Authentication: JWT (JSON Web Tokens)
   - Rate Limiting: Flask-Limiter
   - Acts as the communication bridge between frontend and backend
   - Handles real-time bidirectional communication
   - Manages code execution status updates
   - Streams output and error messages

3. **Python Backend**
   - Framework: Flask
   - ML Libraries: PyTorch, scikit-learn, pandas
   - Code Execution: Python's subprocess with resource limits
   - File Handling: Python's tempfile and shutil
   - Database: SQLite (for development), PostgreSQL (for production)
   - ORM: SQLAlchemy
   - Executes ML code in an isolated environment
   - Processes file uploads and data handling
   - Manages ML pipeline execution
   - Handles model training and evaluation

4. **Data Flow**
   - User interactions flow from browser to WebSocket server
   - Code execution requests are processed by the Python backend
   - Results and status updates flow back through WebSocket
   - File uploads are handled separately for better performance

### AWS Architecture

![AWS Architecture](docs/aws_arch.png)

This architecture represents the production deployment of ByteMe on AWS:

1. **Client Layer**
   - Users access the application through their web browsers
   - Static assets are served through CloudFront CDN
   - WebSocket connections are established through ALB

2. **DNS and CDN Layer**
   - Route 53 manages DNS routing and health checks
   - CloudFront provides global content delivery
   - ACM handles SSL/TLS certificate management

3. **Load Balancing Layer**
   - ALB distributes traffic across EC2 instances
   - Handles WebSocket connections
   - Provides SSL termination
   - Manages health checks

4. **Compute Layer**
   - EC2 instances run the application in Docker containers
   - Auto Scaling Group manages instance count
   - ECR stores and distributes Docker images

5. **Monitoring Layer**
   - CloudWatch monitors application metrics
   - Collects logs and performance data
   - Triggers alerts based on defined thresholds

## Installation and Setup

### Local Development Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Build Docker images:
```bash
docker build -t code-execution-platform:latest .
docker build -t code-execution-worker:latest -f Dockerfile.worker .
```

4. Deploy to Kubernetes:
```bash
kubectl apply -f k8s/deployment.yaml
```

### Configuration

Create a `.env` file in the root directory with the following variables:
```env
RABBITMQ_HOST=localhost
REDIS_HOST=localhost
REDIS_PORT=6379
```

## Usage

1. Start the FastAPI server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

2. In a separate terminal, start the worker process:
```bash
python app/worker.py
```

3. Open your browser and navigate to `http://localhost:8000`

4. Select a template or write custom code:
   - Basic ML Pipeline: Predefined template for common ML tasks
   - Custom Code: Write your own code using the available ML functions

5. Click "Run Code" to execute your code

Note: Both the FastAPI server and worker process must be running simultaneously for the code execution to work properly. The worker process is responsible for executing the code and storing results in Redis, while the FastAPI server handles the web interface and WebSocket communication.

## Available ML Functions

### data_fetch
```python
data = data_fetch('path/to/your/data.csv')
```
Loads data from CSV or NPY files.

### data_preprocessing
```python
X_train, X_test, y_train, y_test, scaler = data_preprocessing(
    data=data,
    target_column='target',
    test_size=0.2
)
```
Preprocesses data with scaling and train-test split.

### train
```python
model = train(
    X_train=X_train,
    y_train=y_train,
    model_type='linear'  # Options: 'linear', 'random_forest', 'neural_network'
)
```
Trains ML models with different algorithms.

## Data Requirements

Your CSV file must contain a column named 'target' that will be used as the target variable for prediction. If your data uses a different column name, you'll need to modify the code template to use your column name.

To check the available columns in your CSV:
1. Upload your CSV file
2. Use the custom template
3. Run this code:
```python
data = data_fetch('your_file.csv')
print("Available columns:", data.columns.tolist())
```

## Security Considerations

1. **Network Security**
   - Use VPC with private subnets
   - Implement security groups
   - Enable SSL/TLS encryption

2. **Application Security**
   - Input validation
   - Code execution sandboxing
   - Secure file handling

3. **Data Security**
   - Temporary file storage
   - Secure model transfer
   - Regular cleanup

## Troubleshooting

1. **Common Issues**
   - WebSocket connection failures
   - File upload errors
   - Model serialization issues

2. **Logs and Monitoring**
   - Check CloudWatch logs
   - Monitor EC2 instance metrics
   - Review application logs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Monaco Editor for the code editor
- FastAPI for the web framework
- RabbitMQ for message queuing
- Redis for result storage
- Kubernetes for container orchestration