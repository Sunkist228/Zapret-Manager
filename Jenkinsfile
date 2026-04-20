// Multibranch delivery pipeline для zapret2
// GitHub Actions - PR validation и releases
// Jenkins - delivery для deploy-capable branches:
//   master -> prod artifacts (stable channel)

pipeline {
    agent { label 'windows' }

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20', artifactNumToKeepStr: '10'))
        timeout(time: 1, unit: 'HOURS')
    }

    environment {
        BRANCH_NAME_SAFE = "${env.BRANCH_NAME ?: 'master'}"
        DEPLOYS = "${env.BRANCH_NAME == 'master' ? 'true' : 'false'}"
        PYTHON_VERSION = '3.12'
    }

    stages {
        stage('Prepare Build Metadata') {
            steps {
                script {
                    // Читаем VERSION
                    if (fileExists('VERSION')) {
                        env.PRODUCT_VERSION = readFile('VERSION').trim()
                    } else {
                        env.PRODUCT_VERSION = '0.0.0'
                    }

                    env.GIT_SHA_FULL = bat(script: '@git rev-parse HEAD', returnStdout: true).trim()
                    env.GIT_SHA_SHORT = bat(script: '@git rev-parse --short=12 HEAD', returnStdout: true).trim()
                    env.GIT_COMMIT_TS = bat(script: '@git show -s --format=%cI HEAD', returnStdout: true).trim()

                    // Формируем BUILD_VERSION
                    if (env.BRANCH_NAME == 'master') {
                        env.BUILD_VERSION = "v${env.PRODUCT_VERSION}+build.${env.BUILD_NUMBER}.sha.${env.GIT_SHA_SHORT}"
                        env.ARTIFACT_CHANNEL = 'stable'
                    } else {
                        env.BUILD_VERSION = "v${env.PRODUCT_VERSION}-dev.${env.BUILD_NUMBER}+sha.${env.GIT_SHA_SHORT}"
                        env.ARTIFACT_CHANNEL = 'dev'
                    }

                    currentBuild.description = "${env.BUILD_VERSION}"

                    echo "Branch: ${env.BRANCH_NAME ?: '(not set)'}"
                    echo "Product version: ${env.PRODUCT_VERSION}"
                    echo "Build version: ${env.BUILD_VERSION}"
                    echo "Artifact channel: ${env.ARTIFACT_CHANNEL}"
                    echo "Deploy: ${env.DEPLOYS}"
                }
            }
        }

        stage('Validate') {
            steps {
                bat '''
                    @echo off
                    echo Checking Python version...
                    python --version

                    echo Installing dependencies...
                    python -m pip install --quiet --upgrade pip
                    python -m pip install --quiet -r requirements.txt
                    python -m pip install --quiet pytest pytest-cov flake8

                    echo Running tests...
                    mkdir reports 2>nul
                    python -m pytest tests/ --junitxml=reports/junit.xml --cov=src --cov-report=xml:reports/coverage.xml

                    if %ERRORLEVEL% neq 0 (
                        echo Tests failed!
                        exit /b 1
                    )

                    echo Running linter...
                    python -m flake8 src/ tests/ --max-line-length=100 --extend-ignore=E203,W503
                '''
            }
        }

        stage('Build Windows EXE') {
            when {
                expression { env.DEPLOYS == 'true' }
            }
            steps {
                bat '''
                    @echo off
                    echo Building Windows EXE...
                    cd build
                    call build.bat

                    if not exist "dist\\ZapretManager.exe" (
                        echo ERROR: EXE file not created!
                        exit /b 1
                    )

                    echo Build successful!
                    dir "dist\\ZapretManager.exe"
                '''

                archiveArtifacts artifacts: 'build/dist/ZapretManager.exe', fingerprint: true
            }
        }

        stage('Publish to Artifact Server') {
            when {
                expression { env.DEPLOYS == 'true' }
            }
            steps {
                script {
                    def artifactApiKeyCredentialId = env.BRANCH_NAME == 'master' ? 'ARTIFACT_SERVER_API_KEY_PROD' : 'ARTIFACT_SERVER_API_KEY_DEV'

                    withCredentials([
                        string(credentialsId: artifactApiKeyCredentialId, variable: 'ARTIFACT_API_KEY'),
                        string(credentialsId: 'ARTIFACT_SERVER_URL', variable: 'ARTIFACT_URL')
                    ]) {
                        bat """
                            @echo off
                            echo Publishing artifact to server...
                            python scripts/publish_artifact.py ^
                                --url "%ARTIFACT_URL%" ^
                                --api-key "%ARTIFACT_API_KEY%" ^
                                --version "${env.BUILD_VERSION}" ^
                                --product-version "${env.PRODUCT_VERSION}" ^
                                --channel "${env.ARTIFACT_CHANNEL}" ^
                                --file build/dist/ZapretManager.exe ^
                                --platform windows ^
                                --arch x64

                            if %ERRORLEVEL% neq 0 (
                                echo WARNING: Failed to publish artifact
                                exit /b 0
                            )

                            echo Artifact published successfully!
                        """
                    }
                }
            }
        }

        stage('Build Summary') {
            steps {
                script {
                    echo """
===========================================
Build Summary
===========================================
Build version: ${env.BUILD_VERSION}
Product version: ${env.PRODUCT_VERSION}
Branch: ${env.BRANCH_NAME}
Commit: ${env.GIT_SHA_SHORT}
Channel: ${env.ARTIFACT_CHANNEL}
Deploy: ${env.DEPLOYS}
===========================================
"""
                }
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'reports/junit.xml'

            script {
                if (fileExists('reports/coverage.xml')) {
                    archiveArtifacts artifacts: 'reports/coverage.xml', allowEmptyArchive: true
                }
            }
        }

        success {
            echo "Pipeline success. Build version: ${env.BUILD_VERSION}"
        }

        failure {
            echo "Pipeline failed for ${env.BUILD_VERSION}"
        }

        cleanup {
            cleanWs(
                deleteDirs: true,
                patterns: [
                    [pattern: 'dist/**', type: 'INCLUDE'],
                    [pattern: 'build/build/**', type: 'INCLUDE'],
                    [pattern: 'build/dist/**', type: 'INCLUDE'],
                    [pattern: 'reports/**', type: 'INCLUDE'],
                    [pattern: '**/__pycache__/**', type: 'INCLUDE'],
                    [pattern: '**/*.pyc', type: 'INCLUDE']
                ]
            )
        }
    }
}
