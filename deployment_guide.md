# AI命理教练网站部署指南

## 项目概述
这是一个基于八字命理分析的AI教练网站，用户输入生日信息后，系统会自动计算八字并生成个性化的命理分析报告。

## 文件结构
- `app.py`：主程序文件，包含Flask应用和核心逻辑
- `static/`：存放CSS和JavaScript文件
- `templates/`：存放HTML模板文件
- `requirements.txt`：项目依赖列表

## 部署步骤

### 1. 服务器准备
确保服务器已安装Python 3.7或更高版本。

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 环境变量配置（可选）
为了安全起见，可以将Flowith API密钥设置为环境变量：
```bash
export FLOWITH_KEY="flo_916327f7e9c65188cb23550a5d25cff77ce997dccc7d888f3aeee5c1cf263da6"
```

如果使用环境变量，需要修改`app.py`中的相关代码来读取环境变量。

### 4. 启动应用
使用Gunicorn启动应用（生产环境推荐）：
```bash
gunicorn -w 4 -b 0.0.0.0:8090 app:app
```

或使用Flask内置服务器（仅用于测试）：
```bash
python app.py
```

### 5. 配置Nginx（推荐）
如果使用Nginx作为反向代理，可以参考以下配置：
```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://127.0.0.1:8090;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 注意事项
- 确保服务器防火墙允许8090端口（或您设定的其他端口）的访问
- 为了提高安全性，建议使用HTTPS
- 定期检查`app.log`日志文件，监控应用运行状态
- 如需更改端口，修改app.py文件最后一行的port参数

## 故障排除
- 如果遇到API调用问题，检查网络连接和API密钥是否正确
- 如果页面样式无法加载，确认静态文件路径配置正确
- 如遇到权限问题，检查文件和目录的读写权限
