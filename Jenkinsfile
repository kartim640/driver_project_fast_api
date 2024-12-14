pipeline {
    agent any
    
    environment {
        PYTHON_VERSION = '3.12'
        PATH = "/usr/local/bin:/usr/bin:/bin:$PATH"
        SUDO_PASS = credentials('SUDO_PASSWORD')
    }

    stages {
        stage('Checkout') {
            steps {
                // Explicitly specify your Git repository
                git branch: 'master',
                    url: 'https://github.com/kartim640/driver_project_fast_api.git'
            }
        }
        
        stage('Setup Environment') {
            steps {
                script {
                    try {
                        sh '''
                            # Install required packages
                            echo $SUDO_PASS | sudo -S apt-get update
                            echo $SUDO_PASS | sudo -S apt-get install -y python3-venv python3-pip
                            
                            # Print Python version
                            echo "Python version:"
                            python3 --version
                            
                            # Create virtual environment
                            echo "Creating virtual environment..."
                            python3 -m venv venv
                            
                            # Activate virtual environment
                            echo "Activating virtual environment..."
                            . venv/bin/activate
                            
                            # Upgrade pip
                            echo "Upgrading pip..."
                            python3 -m pip install --upgrade pip
                            
                            # Install requirements
                            echo "Installing requirements..."
                            if [ -f "requirements.txt" ]; then
                                pip install -r requirements.txt
                            else
                                echo "requirements.txt not found. Installing basic packages..."
                                pip install fastapi uvicorn pytest
                            fi
                            
                            # List installed packages
                            echo "Installed packages:"
                            pip list
                        '''
                    } catch (Exception e) {
                        echo "Setup failed: ${e.message}"
                        error("Environment setup failed")
                    }
                }
            }
        }
        
        stage('Run Tests') {
            steps {
                script {
                    try {
                        sh '''
                            # Activate virtual environment
                            . venv/bin/activate
                            
                            # Run tests if tests directory exists
                            if [ -d "tests" ]; then
                                echo "Running tests..."
                                pytest tests/ -v
                            else
                                echo "No tests directory found. Skipping tests."
                            fi
                        '''
                    } catch (Exception e) {
                        echo "Tests failed: ${e.message}"
                        error("Test stage failed")
                    }
                }
            }
        }
        
        stage('Deploy') {
            steps {
                script {
                    try {
                        sh '''
                            # Activate virtual environment
                            . venv/bin/activate
                            
                            # Check if port 8000 is in use
                            echo "Checking for existing process on port 8000..."
                            if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
                                echo "Port 8000 is in use. Stopping existing process..."
                                echo $SUDO_PASS | sudo -S kill -9 $(lsof -Pi :8000 -sTCP:LISTEN -t)
                            fi
                            
                            # Start the FastAPI application
                            echo "Starting FastAPI application..."
                            nohup uvicorn main:app --host 0.0.0.0 --port 8000 --reload > app.log 2>&1 &
                            
                            # Wait for application to start
                            echo "Waiting for application to start..."
                            sleep 10
                            
                            # Health check
                            echo "Performing health check..."
                            curl -f http://localhost:8000/health || {
                                echo "Health check failed"
                                exit 1
                            }
                            
                            echo "Application deployed successfully!"
                        '''
                    } catch (Exception e) {
                        echo "Deployment failed: ${e.message}"
                        error("Deployment stage failed")
                    }
                }
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
}
