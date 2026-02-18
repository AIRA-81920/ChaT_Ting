
# ChaT_Ting! 命令行AI聊天客户端

一个简洁、流畅、可靠的终端AI聊天应用，支持流式输出、Markdown实时渲染和多轮对话管理。

## 功能特性

- **流式输出**：实时逐字显示AI回复，模拟自然的打字效果
- **Markdown渲染**：支持代码高亮、标题、列表、表格等多种Markdown语法
- **思考动画**：等待响应时显示精美动画，即时反馈用户体验
- **多轮对话**：自动管理对话上下文，支持上下文延续
- **丰富命令**：多种便捷命令，满足不同使用场景
- **多行输入**：支持粘贴代码和长文本
- **文件导入**：直接从本地文件读取内容
- **对话保存**：自动保存对话记录为Markdown文件

## 环境要求

- Python 3.8+

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/AIRA-81920/ChaT_Ting.git
cd chaT_Ting
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置API密钥

复制环境配置示例文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入您的DeepSeek API密钥：

```
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
```

### 4. 运行程序

```bash
python chaT_Ting!.py
```
or:直接点击chaT_Ting!.bat

## 使用指南

### 基本对话

程序启动后，直接输入消息即可与AI对话：

```
> 你好，请介绍一下自己
```

### 命令系统

| 命令 | 功能 |
|------|------|
| `/help` | 显示所有命令和功能介绍 |
| `/history` | 显示当前对话统计信息 |
| `/save` | 立即保存对话历史到文件 |
| `/clear` | 清空对话历史（需确认） |
| `/model` | 切换AI模型或查看当前模型 |
| `/quit` | 退出程序 |

### 特殊输入模式

#### 多行输入

输入 `:ml` 进入多行模式：

```
> :ml
  1 | def hello():
  2 |     print("Hello, World!")
  3 | :end
```

#### 文件导入

输入 `:file 文件名` 从本地文件读取内容：

```
> :file myquestion.txt
```

#### 剪贴板导入

输入 `:clip` 从系统剪贴板导入内容（需安装pyperclip）：

```
> :clip
```

### 退出程序

输入 `q` 或 `/quit` 退出，系统会询问是否保存当前对话：

```
> q
对话历史包含 3 轮对话
是否保存对话？[y/N]: y
✓ 对话已保存至: chat_20250217_143022.md
感谢使用 ChaT_Ting! 再见~
```

## 配置说明

### 环境变量

在 `.env` 文件中可以配置以下选项：

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `DEEPSEEK_API_KEY` | 是 | - | DeepSeek API 密钥 |
| `API_BASE` | 否 | `https://api.deepseek.com` | API 地址 |
| `DEFAULT_MODEL` | 否 | `deepseek-chat` | 默认使用模型 |

### 支持的模型

- `deepseek-chat`：通用对话模型
- `deepseek-reasoner`：推理模型

## 项目结构

```
chat_ting/
├── chat_ting.py       # 主程序
├── .env.example       # 环境配置示例
├── requirements.txt   # Python依赖
└── README.md          # 说明文档
```

## 常见问题

### 1. 提示"未找到 API 密钥"

确保已正确创建 `.env` 文件并填入有效的API密钥。可访问 [DeepSeek平台](https://platform.deepseek.com) 获取密钥。

### 2. 网络连接失败

检查网络连接，或尝试使用代理。某些地区可能需要配置代理才能访问API。

### 3. 剪贴板功能不可用

安装 `pyperclip` 库即可启用剪贴板功能：

```bash
pip install pyperclip
```

## 依赖列表

- `requests`：HTTP请求库
- `rich`：终端美化库
- `python-dotenv`：环境变量管理
- `pyperclip`（可选）：剪贴板支持

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！
