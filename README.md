# Distributed ML Code Execution Platform

A distributed machine learning code execution platform that allows users to write and execute ML code in a web-based environment. The platform supports parallel execution of ML tasks using Kubernetes, RabbitMQ, and Redis.

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

- Python 3.9+
- Docker
- Kubernetes cluster
- RabbitMQ
- Redis

## Installation

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

## Configuration

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

2. Open your browser and navigate to `http://localhost:8000`

3. Select a template or write custom code:
   - Basic ML Pipeline: Predefined template for common ML tasks
   - Custom Code: Write your own code using the available ML functions

4. Click "Run Code" to execute your code

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

## Architecture

- **Frontend**: FastAPI with WebSocket support
- **Code Editor**: Monaco Editor (VS Code's editor)
- **Task Queue**: RabbitMQ
- **Result Storage**: Redis
- **Container Orchestration**: Kubernetes
- **ML Libraries**: scikit-learn, PyTorch, pandas, numpy

## Security Considerations

- Code execution is sandboxed
- Timeout limits for code execution
- Input validation and sanitization
- Secure WebSocket connections

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Monaco Editor for the code editor
- FastAPI for the web framework
- RabbitMQ for message queuing
- Redis for result storage
- Kubernetes for container orchestration 