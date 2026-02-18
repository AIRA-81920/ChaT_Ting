"""
ChaT_Ting! - 命令行AI聊天客户端

一个基于终端的智能聊天应用，支持流式输出、Markdown渲染和多轮对话管理。
"""

import os
import sys
import time
import json
import datetime
import platform
from typing import Optional, List, Dict, Tuple

import requests
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.status import Status
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box
from dotenv import load_dotenv

# 尝试导入剪贴板库（可选）
try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False


class ChaTing:
    """ChaT_Ting! 主应用类"""

    # API配置
    DEFAULT_API_BASE = "https://api.deepseek.com"
    DEFAULT_MODEL = "deepseek-chat"
    MAX_HISTORY_LENGTH = 10  # 最大历史轮次

    # 颜色配置
    COLOR_USER = "green"
    COLOR_AI = "cyan"
    COLOR_SYSTEM = "yellow"
    COLOR_ERROR = "red"

    # 支持的模型列表
    SUPPORTED_MODELS = {
        "deepseek-chat": "DeepSeek Chat (通用对话)",
        "deepseek-reasoner": "DeepSeek Reasoner (推理模型)",
    }

    def __init__(self):
        """初始化应用"""
        self.console = Console()
        self.history: List[Dict[str, str]] = []
        self.current_model = self.DEFAULT_MODEL
        self.conversation_count = 0
        self.api_key: Optional[str] = None
        self.api_base: Optional[str] = None

        # 加载配置
        self._load_config()

    def _load_config(self) -> None:
        """加载环境变量配置"""
        load_dotenv()

        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            self.console.print(
                f"[{self.COLOR_ERROR}]错误：未找到 API 密钥！[/]",
                style=f"bold {self.COLOR_ERROR}"
            )
            self.console.print("\n请在项目根目录创建 .env 文件，内容如下：")
            self.console.print("[cyan]DEEPSEEK_API_KEY=sk-xxxxxx[/]")
            self.console.print("\n或复制 .env.example 为 .env 并填入您的API密钥。\n")
            sys.exit(1)

        # 允许自定义API地址
        self.api_base = os.getenv("API_BASE", self.DEFAULT_API_BASE)

        # 允许自定义默认模型
        custom_model = os.getenv("DEFAULT_MODEL")
        if custom_model:
            self.current_model = custom_model

    def _get_headers(self) -> Dict[str, str]:
        """获取API请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _build_messages(self) -> List[Dict[str, str]]:
        """构建API消息列表"""
        messages = []

        # 添加系统提示（可选）
        messages.append({
            "role": "system",
            "content": "你是一个有帮助的AI助手。请用清晰、准确的中文回答用户的问题。"
        })

        # 添加历史记录（限制长度）
        if len(self.history) > self.MAX_HISTORY_LENGTH * 2:
            # 保留最近N轮对话
            self.history = self.history[-self.MAX_HISTORY_LENGTH * 2:]

        messages.extend(self.history)
        return messages

    def _call_api(self, messages: List[Dict[str, str]], stream: bool = True):
        """调用API"""
        url = f"{self.api_base}/chat/completions"
        data = {
            "model": self.current_model,
            "messages": messages,
            "stream": stream
        }

        try:
            response = requests.post(
                url,
                json=data,
                headers=self._get_headers(),
                stream=stream,
                timeout=60
            )

            if response.status_code == 401:
                raise Exception("API密钥无效，请检查配置")
            elif response.status_code == 429:
                raise Exception("请求过于频繁，请稍后再试")
            elif response.status_code >= 500:
                raise Exception(f"服务器错误：{response.status_code}")
            elif response.status_code != 200:
                raise Exception(f"请求失败：{response.status_code}")

            return response

        except requests.exceptions.Timeout:
            raise Exception("请求超时，请检查网络连接")
        except requests.exceptions.ConnectionError:
            raise Exception("网络连接失败，请检查网络")
        except Exception as e:
            raise Exception(f"API调用失败：{str(e)}")

    def _parse_stream_chunk(self, line: bytes) -> Optional[str]:
        """解析流式响应块"""
        # 跳过空行
        if not line:
            return None

        # 解码为字符串
        try:
            line_str = line.decode('utf-8').strip()
        except UnicodeDecodeError:
            return None

        # 跳过不包含 data: 的行
        if not line_str.startswith("data: "):
            return None

        # 提取 data 部分
        data = line_str[6:]
        if data.strip() == "[DONE]":
            return None

        try:
            json_data = json.loads(data)
            if "choices" in json_data and len(json_data["choices"]) > 0:
                delta = json_data["choices"][0].get("delta", {})
                content = delta.get("content", "")
                if content:
                    return content
        except json.JSONDecodeError:
            pass

        return None

    def _stream_response(self, messages: List[Dict[str, str]]) -> str:
        """流式输出响应，支持动态Markdown渲染"""
        response_text = ""
        buffer = ""

        try:
            response = self._call_api(messages, stream=True)

            # 用于跟踪是否收到任何内容
            received_content = False

            # 使用Live进行流式显示
            with Live(console=self.console, refresh_per_second=20, transient=False) as live:
                for line in response.iter_lines():
                    # 跳过空行
                    if not line:
                        continue

                    content = self._parse_stream_chunk(line)
                    if content:
                        received_content = True
                        response_text += content
                        buffer += content

                        # 尝试渲染Markdown
                        self._update_live_display(live, buffer)

                        # 控制输出速度（可选）
                        time.sleep(0.015)

            # 如果没有收到任何内容，抛出错误
            if not received_content:
                raise Exception("未收到AI响应，请检查API配置或网络连接")

            return response_text

        except Exception as e:
            raise e

    def _update_live_display(self, live, buffer: str) -> None:
        """动态更新Markdown显示"""
        try:
            # 检测是否为Markdown格式
            if any(char in buffer for char in ['#', '`', '*', '-', '|', '_', '>', '[']):
                try:
                    md = Markdown(buffer, code_theme="monokai")
                    live.update(md)
                    return
                except Exception:
                    pass

            # 非Markdown，直接显示文本
            live.update(Text(buffer, style=self.COLOR_AI))
        except Exception:
            # 如果渲染失败，直接显示原始文本
            live.update(Text(buffer, style=self.COLOR_AI))

    def _render_markdown(self, text: str) -> None:
        """渲染Markdown文本"""
        # 检测是否为Markdown格式
        if any(char in text for char in ['#', '`', '*', '-', '|', '_']):
            try:
                md = Markdown(text, code_theme="monokai")
                self.console.print(md)
                return
            except Exception:
                pass

        # 非Markdown或渲染失败，直接输出
        self.console.print(text, style=self.COLOR_AI)

    def _save_conversation(self) -> Optional[str]:
        """保存对话历史"""
        if not self.history:
            self.console.print("[yellow]没有对话记录可保存[/]")
            return None

        # 生成文件名
        now = datetime.datetime.now()
        filename = f"chat_{now.strftime('%Y%m%d_%H%M%S')}.md"
        filepath = os.path.join(os.getcwd(), filename)

        # 构建Markdown内容
        content_lines = [
            f"# ChaT_Ting! 对话记录",
            "",
            f"**日期**: {now.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**模型**: {self.current_model}",
            f"**对话轮次**: {self.conversation_count}",
            "",
            "---",
            ""
        ]

        # 添加历史消息
        for msg in self.history:
            role = "用户" if msg["role"] == "user" else "AI"
            content_lines.append(f"### {role}")
            content_lines.append("")
            content_lines.append(msg["content"])
            content_lines.append("")
            content_lines.append("---")
            content_lines.append("")

        # 写入文件
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content_lines))

            self.console.print(f"[green]✓[/] 对话已保存至: [cyan]{filepath}[/]")
            return filepath
        except Exception as e:
            self.console.print(f"[red]保存失败: {str(e)}[/]")
            return None

    def _show_help(self) -> None:
        """显示帮助信息"""
        table = Table(title="ChaT_Ting! 命令帮助", box=box.ROUNDED)
        table.add_column("命令", style="cyan", no_wrap=True)
        table.add_column("功能", style="white")

        commands = [
            ("/help", "显示所有命令和功能介绍"),
            ("/history", "显示当前对话统计信息"),
            ("/save", "立即保存对话历史到文件"),
            ("/clear", "清空对话历史（需确认）"),
            ("/model", "切换AI模型或查看当前模型"),
            ("/quit", "退出程序"),
            (":ml", "进入多行输入模式"),
            (":file <文件>", "从文件导入内容"),
            (":clip", "从剪贴板导入内容（需pyperclip）"),
        ]

        for cmd, desc in commands:
            table.add_row(cmd, desc)

        self.console.print(table)

    def _show_history(self) -> None:
        """显示对话统计"""
        table = Table(title="对话统计", box=box.ROUNDED)
        table.add_column("项目", style="cyan")
        table.add_column("值", style="white")

        table.add_row("当前模型", self.current_model)
        table.add_row("对话轮次", str(self.conversation_count))
        table.add_row("消息总数", str(len(self.history)))
        table.add_row("最大历史轮次", str(self.MAX_HISTORY_LENGTH))

        self.console.print(table)

    def _switch_model(self, args: str = "") -> None:
        """切换AI模型"""
        if not args:
            # 显示当前模型和可用模型
            table = Table(title="模型信息", box=box.ROUNDED)
            table.add_column("模型ID", style="cyan")
            table.add_column("描述", style="white")

            for model_id, desc in self.SUPPORTED_MODELS.items():
                current = " ✓" if model_id == self.current_model else ""
                table.add_row(model_id, desc + current)

            self.console.print(table)
            self.console.print(f"\n当前使用: [cyan]{self.current_model}[/]")
            self.console.print("输入 /model <模型ID> 切换模型")
            return

        # 切换模型
        model_id = args.strip()
        if model_id in self.SUPPORTED_MODELS:
            self.current_model = model_id
            self.console.print(f"[green]✓[/] 已切换到模型: [cyan]{model_id}[/]")
        else:
            self.console.print(f"[red]不支持的模型: {model_id}[/]")
            self.console.print("支持的模型:")
            for mid in self.SUPPORTED_MODELS:
                self.console.print(f"  - {mid}")

    def _clear_history(self) -> bool:
        """清空对话历史"""
        if not self.history:
            self.console.print("[yellow]对话历史已经是空的[/]")
            return False

        self.console.print(f"确定要清空 {self.conversation_count} 轮对话吗？[y/N]: ", end="")
        confirm = input().strip().lower()

        if confirm == 'y':
            self.history = []
            self.conversation_count = 0
            self.console.print("[green]✓[/] 对话历史已清空")
            return True
        else:
            self.console.print("[yellow]已取消[/]")
            return False

    def _handle_multiline_input(self) -> Optional[str]:
        """处理多行输入"""
        self.console.print("[cyan]多行输入模式（输入 :end 或空行结束）：[/]")
        lines = []
        line_num = 0

        while True:
            line_num += 1
            line = input(f"  {line_num:2d} | ")
            if line.strip() in (':end', ':e', ''):
                break
            lines.append(line)

        if not lines:
            self.console.print("[yellow]未输入内容[/]")
            return None

        return '\n'.join(lines)

    def _handle_file_input(self, filepath: str) -> Optional[str]:
        """处理文件导入"""
        if not filepath:
            self.console.print("[red]请指定文件路径[/]")
            return None

        # 处理相对路径和绝对路径
        if not os.path.isabs(filepath):
            filepath = os.path.join(os.getcwd(), filepath)

        if not os.path.exists(filepath):
            self.console.print(f"[red]文件不存在: {filepath}[/]")
            return None

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            self.console.print(f"[green]✓[/] 已从文件导入内容 ({len(content)} 字符)")
            return content
        except Exception as e:
            self.console.print(f"[red]读取文件失败: {str(e)}[/]")
            return None

    def _handle_clipboard_input(self) -> Optional[str]:
        """处理剪贴板导入"""
        if not CLIPBOARD_AVAILABLE:
            self.console.print("[red]剪贴板功能不可用，请安装 pyperclip 库[/]")
            return None

        try:
            content = pyperclip.paste()
            if not content:
                self.console.print("[yellow]剪贴板为空[/]")
                return None
            self.console.print(f"[green]✓[/] 已从剪贴板导入内容 ({len(content)} 字符)")
            return content
        except Exception as e:
            self.console.print(f"[red]读取剪贴板失败: {str(e)}[/]")
            return None

    def _handle_quit(self) -> bool:
        """处理退出"""
        if not self.history:
            return True

        self.console.print(f"对话历史包含 {self.conversation_count} 轮对话")
        self.console.print("是否保存对话？[y/N]: ", end="")
        confirm = input().strip().lower()

        if confirm == 'y':
            self._save_conversation()

        return True

    def _process_input(self, user_input: str) -> Tuple[bool, Optional[str]]:
        """
        处理用户输入
        返回: (是否退出, 要发送的消息)
        """
        user_input = user_input.strip()

        if not user_input:
            return False, None

        # 退出命令
        if user_input.lower() in ('q', 'exit', '/quit'):
            if self._handle_quit():
                return True, None

        # 命令处理
        if user_input.startswith('/'):
            parts = user_input.split(maxsplit=1)
            cmd = parts[0]
            args = parts[1] if len(parts) > 1 else ""

            if cmd == '/help':
                self._show_help()
            elif cmd == '/history':
                self._show_history()
            elif cmd == '/save':
                self._save_conversation()
            elif cmd == '/clear':
                self._clear_history()
            elif cmd == '/model':
                self._switch_model(args)
            elif cmd == '/quit':
                if self._handle_quit():
                    return True, None
            else:
                self.console.print(f"[red]未知命令: {cmd}[/]")
                self.console.print("输入 /help 查看可用命令")

            return False, None

        # 特殊输入模式
        if user_input.startswith(':'):
            # 多行输入
            if user_input.startswith(':ml'):
                content = self._handle_multiline_input()
                if content:
                    return False, content
                return False, None

            # 文件导入
            if user_input.startswith(':file '):
                filepath = user_input[6:].strip()
                content = self._handle_file_input(filepath)
                if content:
                    return False, content
                return False, None

            # 剪贴板导入
            if user_input == ':clip':
                content = self._handle_clipboard_input()
                if content:
                    return False, content
                return False, None

        # 普通消息
        return False, user_input

    def _display_welcome(self) -> None:
        """显示欢迎信息"""
        # 标题
        title = Text()
        title.append("╔═══════════════════════════════════════╗\n", style="bold cyan")
        title.append("║         ChaT_Ting! 命令行AI聊天        ║\n", style="bold cyan")
        title.append("╚═══════════════════════════════════════╝", style="bold cyan")

        self.console.print(title)
        self.console.print()

        # 简短提示
        self.console.print("[dim]输入 [cyan]/help[/] 查看命令 · 输入 [cyan]q[/] 退出[/]")
        self.console.print()

    def run(self) -> None:
        """运行主循环"""
        self._display_welcome()

        while True:
            try:
                # 获取用户输入
                user_input = input("> ").strip()

                # 处理输入
                should_exit, message = self._process_input(user_input)

                if should_exit:
                    break

                if not message:
                    continue

                # 显示用户消息
                self.conversation_count += 1
                self.console.print()
                self.console.print(f"─── 对话 #{self.conversation_count} ───")

                # 用户消息（绿色）
                user_display = Text()
                user_display.append("用户: ", style=f"bold {self.COLOR_USER}")
                user_display.append(message, style=self.COLOR_USER)
                self.console.print(user_display)
                self.console.print()

                # 添加到历史
                self.history.append({
                    "role": "user",
                    "content": message
                })

                # 构建消息
                messages = self._build_messages()

                # 获取AI响应
                try:
                    ai_response = self._stream_response(messages)

                    # 添加AI响应到历史
                    self.history.append({
                        "role": "assistant",
                        "content": ai_response
                    })

                    self.console.print()
                    self.console.print(f"[green]✓[/] 完成", style="dim")

                except Exception as e:
                    # 移除用户消息（API调用失败）
                    if self.history and self.history[-1]["role"] == "user":
                        self.history.pop()

                    self.console.print()
                    self.console.print(f"[red]错误: {str(e)}[/]", style="bold red")
                    self.console.print()

                self.console.print()
                self.console.print("─" * 40)
                self.console.print()

            except KeyboardInterrupt:
                # Ctrl+C 处理
                self.console.print()
                self.console.print("[yellow]检测到中断信号[/]")
                if self._handle_quit():
                    break
            except EOFError:
                # Ctrl+D 处理
                break

        # 退出
        self.console.print()
        self.console.print("[cyan]感谢使用 ChaT_Ting! 再见~[/]")


def main():
    """主函数"""
    app = ChaTing()
    app.run()


if __name__ == "__main__":
    main()