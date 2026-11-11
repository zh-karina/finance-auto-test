// Jenkins 声明式流水线（finance-auto-test：FastAPI 财务系统 + pytest 合规测试）
// 流程：拉代码 → 装依赖 → 启动被测 FastAPI 应用 → 跑 pytest(生成 allure-results)
//       → Allure 生成 HTML 报告 → 推送到 GitHub gh-pages 分支（Pages 在线访问）
//
// 前提：Jenkins 凭据中存在 Secret text 类型凭据，ID 为 github-pat（GitHub PAT，勾选 repo 权限）

pipeline {
    agent any

    environment {
        // 仓库信息（Pages 推送用）
        GITHUB_OWNER          = 'zh-karina'
        GITHUB_REPO           = 'finance-auto-test'
        GITHUB_CREDENTIALS_ID = 'github-pat'

        // 对本构建的所有 git 命令关闭证书吊销检查（修复 SYSTEM 账号下
        // "SSL peer certificate or SSH remote key was not OK" 的问题，与运行账号无关）
        GIT_CONFIG_COUNT  = '1'
        GIT_CONFIG_KEY_0  = 'http.schannelCheckRevoke'
        GIT_CONFIG_VALUE_0 = 'false'

        // 被测系统地址（tests/test_finance.py 读取该环境变量）
        BASE_URL = 'http://127.0.0.1:8000'

        // Windows 专用路径（Linux Agent 忽略）
        PYTHON_BIN  = 'D:/anaconda/python.exe'
        ALLURE_HOME = 'D:\\allure\\allure-2.27.0'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup Python') {
            steps {
                script {
                    if (isUnix()) {
                        sh '''
                          python3 -m venv .venv
                          . .venv/bin/activate
                          python -m pip install -r requirements.txt
                        '''
                    } else {
                        bat '''
                          if not exist ".venv\\Scripts\\python.exe" "%PYTHON_BIN%" -m venv .venv
                          call .venv\\Scripts\\activate.bat
                          python -c "import fastapi, uvicorn, pytest, requests, allure" 2>nul || python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
                          python --version
                        '''
                    }
                }
            }
        }

        stage('Start App') {
            steps {
                script {
                    if (isUnix()) {
                        sh '''
                          . .venv/bin/activate
                          nohup python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > uvicorn.log 2>&1 &
                          echo $! > app.pid
                          sleep 5
                        '''
                    } else {
                        bat '''
                          call .venv\\Scripts\\activate.bat
                          powershell -Command "$p = Start-Process python -ArgumentList '-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000' -PassThru -WindowStyle Hidden; $p.Id | Out-File -Encoding ascii app.pid"
                          timeout /t 6 /nobreak >nul
                          powershell -Command "try { (Invoke-WebRequest -UseBasicParsing -TimeoutSec 5 '%BASE_URL%/docs').StatusCode } catch { $_.Exception.Response.StatusCode.value__ }"
                        '''
                    }
                }
            }
        }

        stage('Run Tests') {
            steps {
                catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                    script {
                        if (isUnix()) {
                            sh '''
                              . .venv/bin/activate
                              pytest tests/ --alluredir=allure-results --clean-alluredir
                            '''
                        } else {
                            bat '''
                              call .venv\\Scripts\\activate.bat
                              pytest tests/ --alluredir=allure-results --clean-alluredir
                            '''
                        }
                    }
                }
            }
        }

        stage('Generate Allure Report') {
            steps {
                script {
                    if (isUnix()) {
                        sh '''
                          if [ ! -x allure-cli/bin/allure ]; then
                            curl -sL "https://github.com/allure-framework/allure2/releases/download/2.29.0/allure-2.29.0.tgz" -o allure.tgz
                            tar -xzf allure.tgz
                            mv allure-2.29.0 allure-cli
                          fi
                          rm -rf /tmp/allure-report
                          ./allure-cli/bin/allure generate allure-results -o /tmp/allure-report --clean
                        '''
                    } else {
                        bat '''
                          set "ALLURE="
                          if exist "%ALLURE_HOME%\\bin\\allure.bat" set "ALLURE=%ALLURE_HOME%\\bin\\allure.bat"
                          if not defined ALLURE if exist "allure-cli\\bin\\allure.bat" set "ALLURE=allure-cli\\bin\\allure.bat"
                          if not defined ALLURE (
                            echo 未找到 Allure，开始下载...
                            curl -sL -o allure.tgz "https://github.com/allure-framework/allure2/releases/download/2.29.0/allure-2.29.0.tgz"
                            tar -xzf allure.tgz
                            move allure-2.29.0 allure-cli
                            set "ALLURE=allure-cli\\bin\\allure.bat"
                          )
                          if exist "%TEMP%\\allure-report" rmdir /s /q "%TEMP%\\allure-report"
                          call "%ALLURE%" generate allure-results -o "%TEMP%\\allure-report" --clean
                        '''
                    }
                }
            }
            post {
                always {
                    script {
                        if (isUnix()) {
                            sh 'tar -czf allure-results.tgz allure-results || true'
                        } else {
                            bat 'if exist allure-results powershell -Command "Compress-Archive -Path allure-results -DestinationPath allure-results.zip -Force"'
                        }
                    }
                    archiveArtifacts artifacts: 'allure-results.*', allowEmptyArchive: true
                }
            }
        }

        stage('Publish to GitHub Pages') {
            steps {
                withCredentials([string(credentialsId: env.GITHUB_CREDENTIALS_ID, variable: 'GITHUB_TOKEN')]) {
                    script {
                        if (isUnix()) {
                            sh '''
                              git config user.name "jenkins-bot"
                              git config user.email "jenkins-bot@ci.local"
                              git checkout --orphan pages-tmp 2>/dev/null || git checkout -B pages-tmp
                              find . -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
                              cp -r /tmp/allure-report/. .
                              touch .nojekyll
                              echo "${GITHUB_OWNER}/${GITHUB_REPO} - build #${BUILD_NUMBER}" > BUILD_INFO.txt
                              git add -A
                              git commit -m "chore: publish Allure report from build #${BUILD_NUMBER} [ci skip]" || echo "Nothing to commit"
                              git push --force "https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_OWNER}/${GITHUB_REPO}.git" HEAD:${PAGES_BRANCH:-gh-pages}
                            '''
                        } else {
                            bat '''
                              git config user.name "jenkins-bot"
                              git config user.email "jenkins-bot@ci.local"

                              git checkout --orphan pages-tmp 2>nul
                              if errorlevel 1 git checkout -B pages-tmp

                              for /d %%d in (*) do if /i not "%%d"==".git" rmdir /s /q "%%d"
                              for %%f in (*) do del /q "%%f"

                              xcopy "%TEMP%\\allure-report" . /E /Y /Q >nul
                              type nul > .nojekyll
                              echo %GITHUB_OWNER%/%GITHUB_REPO% - build #%BUILD_NUMBER% > BUILD_INFO.txt

                              git add -A
                              git commit -m "chore: publish Allure report from build #%BUILD_NUMBER% [ci skip]" || echo Nothing to commit
                              git push --force "https://x-access-token:%GITHUB_TOKEN%@github.com/%GITHUB_OWNER%/%GITHUB_REPO%.git" HEAD:gh-pages
                            '''
                        }
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                if (isUnix()) {
                    sh 'if [ -f app.pid ]; then kill $(cat app.pid) 2>/dev/null || true; fi; pkill -f "uvicorn app.main" 2>/dev/null || true'
                } else {
                    bat 'if exist app.pid for /f %%i in (app.pid) do taskkill /f /pid %%i 2>nul'
                }
            }
            cleanWs(deleteDirs: true, notFailBuild: true)
        }
    }
}
