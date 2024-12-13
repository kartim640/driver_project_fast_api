pipeline {
    agent any
    
    environment {
        PYTHON_VERSION = '3.12'
        PATH = "/usr/local/bin:/usr/bin:/bin:$PATH"
    }

    stages {
        stage('Checkout') {
            steps {
                // Checkout code from GitHub
                checkout scm
                
                // Print information about the commit
                sh '''
                    echo "Branch: ${GIT_BRANCH}"
                    echo "Commit: ${GIT_COMMIT}"
                '''
            }
        }
        
        stage('Setup Environment') {
            steps {
                script {
                    try {
                        sh '''
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
                            pip install -r requirements.txt
                            
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
                                lsof -Pi :8000 -sTCP:LISTEN -t | xargs kill -9 || true
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
            // Clean workspace
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
