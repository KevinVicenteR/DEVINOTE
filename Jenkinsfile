pipeline {
    agent any

    options {
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    environment {
        IMAGE = 'ghcr.io/kevinvicenter/devinote'
    }

    stages {
        stage('Preparar') {
            steps {
                script {
                    // Obtiene el SHA con git: no depende de que GIT_COMMIT exista
                    // ni de take(), que el sandbox de Jenkins puede bloquear.
                    def shortSha = sh(script: 'git rev-parse --short=7 HEAD', returnStdout: true).trim()
                    env.IMAGE_TAG = "${env.BUILD_NUMBER}-${shortSha}"
                }
            }
        }

        stage('Tests') {
            agent {
                docker {
                    image 'python:3.14-slim'
                    reuseNode true
                }
            }
            environment {
                // Dentro del contenedor el usuario de Jenkins no tiene HOME escribible;
                // sin esto pip/poetry fallan al crear ~/.config o ~/.cache.
                HOME             = "${WORKSPACE}"
                POETRY_CACHE_DIR = "${WORKSPACE}/.cache/pypoetry"
                PIP_CACHE_DIR    = "${WORKSPACE}/.cache/pip"
                DATABASE_URL     = 'sqlite://'
                JWT_SECRET       = 'ci-test-secret-with-at-least-32-characters'
            }
            steps {
                sh '''
                    python -m venv .ci-tools
                    . .ci-tools/bin/activate
                    pip install --quiet "poetry==2.5.2"
                    poetry install --no-root --no-interaction
                    poetry run pip install --quiet pytest pytest-cov
                    poetry run pytest tests --cov=app --cov=main --cov-report=xml --junitxml=test-results.xml
                '''
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'test-results.xml'
                }
            }
        }

        stage('SonarQube Cloud') {
            agent {
                docker {
                    image 'sonarsource/sonar-scanner-cli:latest'
                    args '--entrypoint='
                    reuseNode true
                }
            }
            environment {
                HOME            = "${WORKSPACE}"
                SONAR_USER_HOME = "${WORKSPACE}/.sonar"
            }
            steps {
                withCredentials([string(credentialsId: 'sonarcloud-token', variable: 'SONAR_TOKEN')]) {
                    sh 'sonar-scanner -Dsonar.qualitygate.wait=true'
                }
            }
        }

        stage('Imagen Docker') {
            when { branch 'Dev' }
            steps {
                withCredentials([usernamePassword(credentialsId: 'ghcr', usernameVariable: 'REG_USER', passwordVariable: 'REG_TOKEN')]) {
                    // -f dockerfile porque el archivo está en minúsculas.
                    sh '''
                        echo "$REG_TOKEN" | docker login ghcr.io -u "$REG_USER" --password-stdin
                        docker build -f dockerfile -t "$IMAGE:$IMAGE_TAG" -t "$IMAGE:latest" .
                        docker push "$IMAGE:$IMAGE_TAG"
                        docker push "$IMAGE:latest"
                    '''
                }
            }
            post {
                always {
                    sh 'docker logout ghcr.io || true'
                }
            }
        }

        stage('Desplegar en Kubernetes') {
            when { branch 'Dev' }
            steps {
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    sh '''
                        kubectl apply -k k8s/
                        kubectl -n devinote set image deployment/devinote app="$IMAGE:$IMAGE_TAG"
                        kubectl -n devinote rollout status deployment/devinote --timeout=180s
                    '''
                }
            }
        }
    }
}
