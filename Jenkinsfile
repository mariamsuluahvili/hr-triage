pipeline {
  agent { label 'ai-lab' }

  options {
    timestamps()
    timeout(time: 30, unit: 'MINUTES')
  }

  environment {
    IMAGE = "hr-triage:${env.BUILD_NUMBER}"
    PYTHONDONTWRITEBYTECODE = '1'
  }

  stages {
    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Install') {
      steps {
        sh '''
          python3 -m venv .venv
          . .venv/bin/activate
          python -m pip install -r requirements-dev.txt
          python -m pip install --no-deps -e .
        '''
      }
    }

    stage('Lint') {
      steps {
        sh '''
          . .venv/bin/activate
          ruff check src tests ui
        '''
      }
    }

    stage('Test') {
      steps {
        sh '''
          . .venv/bin/activate
          mkdir -p reports
          python -m pytest --junitxml=reports/junit.xml
        '''
      }
      post {
        always {
          junit allowEmptyResults: true, testResults: 'reports/junit.xml'
          archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
        }
      }
    }

    stage('IaC validate') {
      steps {
        sh '''
          terraform -chdir=infra fmt -check
          terraform -chdir=infra init -backend=false -input=false
          terraform -chdir=infra validate
        '''
      }
    }

    stage('Build image') {
      steps {
        sh 'docker build -t "$IMAGE" .'
      }
    }

    stage('Smoke test') {
      steps {
        sh 'python3 scripts/container_smoke.py "$IMAGE"'
      }
    }
  }

  post {
    always {
      sh 'docker rmi -f "$IMAGE" || true'
    }
  }
}
