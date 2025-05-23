# AI命理教练网站部署指南 (简单版)

## 项目简介
这是一个AI命理教练网站，用户只需输入生日信息，就能获得专业的八字命理分析报告。网站使用了Python的Flask框架和现代的前端技术。

## 已准备的部署文件
为了让您能轻松地把网站部署到云平台，我们已经准备好了以下文件：

- `Procfile`: 告诉云平台如何运行您的网站
- `requirements.txt`: 列出了网站需要的所有Python包
- `runtime.txt`: 指定了Python的版本
- `app.py`: 已经更新，可以自动适应不同的运行环境

## 部署到Heroku (最简单的方法)

### 1. 准备工作
- 创建[Heroku账户](https://signup.heroku.com/)
- 下载安装[Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)

### 2. 登录Heroku
打开命令行，输入:
```bash
heroku login
```

### 3. 创建应用
```bash
# 进入项目文件夹
cd /Users/feiwu4/Documents/weblearning/coaching

# 创建一个新的Heroku应用
heroku create ai-minging-coach

# 确认创建成功
heroku apps
```

### 4. 设置环境变量
为了保护API密钥，我们把它存在Heroku的环境变量中:
```bash
heroku config:set FLOWITH_KEY="flo_916327f7e9c65188cb23550a5d25cff77ce997dccc7d888f3aeee5c1cf263da6"
heroku config:set DEEPSEEK_KEY="sk-yiukvkodedbpotyhhhrdwwwfmbfdmogoolxpivqrzyqbytkw"
```

### 5. 部署代码
```bash
# 将代码推送到Heroku
git add .
git commit -m "准备部署到Heroku"
git push heroku master
```

### 6. 打开网站
```bash
heroku open
```

## 部署到其他平台

### 部署到PythonAnywhere

1. 注册[PythonAnywhere账号](https://www.pythonanywhere.com/)
2. 点击Dashboard中的"Web"选项卡
3. 选择"Add a new web app"
4. 选择"Flask"框架和Python 3.9
5. 设置源代码目录为您的项目路径
6. 将以下文件上传到该目录：
   - app.py
   - requirements.txt
   - 整个static和templates文件夹
7. 在"WSGI configuration file"中确保Flask应用配置正确
8. 点击"Reload"按钮启动您的网站

### 部署到腾讯云或阿里云

1. 创建一个云服务器实例(CentOS或Ubuntu)
2. 通过SSH连接到服务器
3. 安装必要的软件:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip nginx
   ```
4. 上传您的项目文件
5. 安装依赖:
   ```bash
   pip3 install -r requirements.txt
   ```
6. 使用Gunicorn启动应用:
   ```bash
   gunicorn -w 4 -b 127.0.0.1:8090 app:app &
   ```
7. 配置Nginx作为反向代理

## 可能遇到的问题及解决方法

### 1. 样式无法加载
这通常是因为静态文件路径配置问题。确保:
- static文件夹已正确上传
- app.py中的static_folder设置正确
- 如果使用Nginx，确保配置了静态文件的处理

### 2. API调用失败
- 检查网络连接是否正常
- 确认API密钥是否正确设置
- 查看服务器日志(app.log)了解详细错误信息

### 3. 网站打不开
- 检查云平台的防火墙设置
- 确认应用是否正在运行
- 检查日志文件查看具体错误

## 测试部署是否成功
成功部署后，访问您的网站地址，输入一个出生日期信息，如果能正常生成命理报告，说明部署成功了！

## 需要帮助？
如果您在部署过程中遇到任何问题，可以查看各云平台的官方文档，或者联系技术支持获取帮助。
