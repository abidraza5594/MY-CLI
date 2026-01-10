import asyncio
import os
from pathlib import Path
import sys
import tempfile
import click

from agent.agent import Agent
from agent.events import AgentEventType
from agent.persistence import PersistenceManager, SessionSnapshot
from agent.session import Session
from config.config import ApprovalPolicy, Config, Provider, PROVIDER_CONFIG
from config.loader import load_config
from ui.tui import TUI, get_console

console = get_console()


def get_clipboard_image() -> str | None:
    """Get image from clipboard and save to temp file. Returns path or None."""
    try:
        import sys
        if sys.platform == 'win32':
            import win32clipboard
            from PIL import Image
            import io
            
            win32clipboard.OpenClipboard()
            try:
                # Try to get image from clipboard
                if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
                    data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
                    # Convert DIB to image
                    import struct
                    # Skip BITMAPINFOHEADER
                    offset = 40  # Size of BITMAPINFOHEADER
                    header = data[:offset]
                    width = struct.unpack('<i', header[4:8])[0]
                    height = struct.unpack('<i', header[8:12])[0]
                    
                    # Create BMP file in memory
                    bmp_header = b'BM' + struct.pack('<I', len(data) + 14) + b'\x00\x00\x00\x00' + struct.pack('<I', 54)
                    bmp_data = bmp_header + data
                    
                    img = Image.open(io.BytesIO(bmp_data))
                    
                    # Save to temp file
                    temp_path = Path(tempfile.gettempdir()) / "abid_clipboard_image.png"
                    img.save(str(temp_path), "PNG")
                    return str(temp_path)
            finally:
                win32clipboard.CloseClipboard()
        else:
            # For Linux/Mac, try using PIL's ImageGrab
            from PIL import ImageGrab
            img = ImageGrab.grabclipboard()
            if img:
                temp_path = Path(tempfile.gettempdir()) / "abid_clipboard_image.png"
                img.save(str(temp_path), "PNG")
                return str(temp_path)
    except ImportError:
        return None
    except Exception:
        return None
    return None


class CLI:
    def __init__(self, config: Config):
        self.agent: Agent | None = None
        self.config = config
        self.tui = TUI(config, console)

    async def run_single(self, message: str) -> str | None:
        async with Agent(self.config) as agent:
            self.agent = agent
            return await self._process_message(message)

    async def run_interactive(self) -> str | None:
        self.tui.print_welcome(
            "AI Agent",
            lines=[
                f"provider: {self.config.provider.value}",
                f"model: {self.config.model_name}",
                f"cwd: {self.config.cwd}",
                "commands: /help /config /provider /model /exit",
            ],
        )

        async with Agent(
            self.config,
            confirmation_callback=self.tui.handle_confirmation,
        ) as agent:
            self.agent = agent

            while True:
                try:
                    user_input = console.input("\n[user]>[/user] ").strip()
                    if not user_input:
                        continue

                    if user_input.startswith("/"):
                        should_continue = await self._handle_command(user_input)
                        if not should_continue:
                            break
                        continue

                    await self._process_message(user_input)
                except KeyboardInterrupt:
                    console.print("\n[dim]Use /exit to quit[/dim]")
                except EOFError:
                    break

        console.print("\n[dim]Goodbye![/dim]")

    def _get_tool_kind(self, tool_name: str) -> str | None:
        tool_kind = None
        tool = self.agent.session.tool_registry.get(tool_name)
        if not tool:
            tool_kind = None

        tool_kind = tool.kind.value

        return tool_kind

    async def _process_message(self, message: str) -> str | None:
        if not self.agent:
            return None

        assistant_streaming = False
        final_response: str | None = None

        async for event in self.agent.run(message):
            if event.type == AgentEventType.TEXT_DELTA:
                content = event.data.get("content", "")
                if not assistant_streaming:
                    self.tui.begin_assistant()
                    assistant_streaming = True
                self.tui.stream_assistant_delta(content)
            elif event.type == AgentEventType.TEXT_COMPLETE:
                final_response = event.data.get("content")
                if assistant_streaming:
                    self.tui.end_assistant()
                    assistant_streaming = False
            elif event.type == AgentEventType.AGENT_ERROR:
                error = event.data.get("error", "Unknown error")
                console.print(f"\n[error]Error: {error}[/error]")
            elif event.type == AgentEventType.TOOL_CALL_START:
                tool_name = event.data.get("name", "unknown")
                tool_kind = self._get_tool_kind(tool_name)
                self.tui.tool_call_start(
                    event.data.get("call_id", ""),
                    tool_name,
                    tool_kind,
                    event.data.get("arguments", {}),
                )
            elif event.type == AgentEventType.TOOL_CALL_COMPLETE:
                tool_name = event.data.get("name", "unknown")
                tool_kind = self._get_tool_kind(tool_name)
                self.tui.tool_call_complete(
                    event.data.get("call_id", ""),
                    tool_name,
                    tool_kind,
                    event.data.get("success", False),
                    event.data.get("output", ""),
                    event.data.get("error"),
                    event.data.get("metadata"),
                    event.data.get("diff"),
                    event.data.get("truncated", False),
                    event.data.get("exit_code"),
                )

        return final_response

    async def _handle_command(self, command: str) -> bool:
        cmd = command.lower().strip()
        parts = cmd.split(maxsplit=1)
        cmd_name = parts[0]
        cmd_args = parts[1] if len(parts) > 1 else ""
        if cmd_name == "/exit" or cmd_name == "/quit":
            return False
        elif command == "/help":
            self.tui.show_help()
        elif command == "/clear":
            self.agent.session.context_manager.clear()
            self.agent.session.loop_detector.clear()
            console.print("[success]Conversation cleared [/success]")
        elif command == "/config":
            console.print("\n[bold]Current Configuration[/bold]")
            console.print(f"  Provider: {self.config.provider.value}")
            console.print(f"  Model: {self.config.model_name}")
            console.print(f"  Vision Model: {self.config.vision_model_name}")
            console.print(f"  Temperature: {self.config.temperature}")
            console.print(f"  Approval: {self.config.approval.value}")
            console.print(f"  Working Dir: {self.config.cwd}")
            console.print(f"  Max Turns: {self.config.max_turns}")
        elif cmd_name == "/provider":
            if cmd_args:
                # Check if it's a provider name
                try:
                    provider = Provider(cmd_args.lower())
                    self.config.set_provider(provider)
                    console.print(f"[success]Provider changed to: {provider.value}[/success]")
                    console.print(f"[dim]Model: {self.config.model_name}[/dim]")
                    console.print(f"[dim]Vision: {self.config.vision_model_name}[/dim]")
                    
                    # Check if API key is set
                    if not self.config.api_key:
                        provider_config = PROVIDER_CONFIG.get(provider, {})
                        env_key = provider_config.get("env_key", "API_KEY")
                        console.print(f"[warning]Set {env_key} environment variable for this provider[/warning]")
                except ValueError:
                    console.print(f"[error]Unknown provider: {cmd_args}[/error]")
                    console.print(f"[dim]Available: {', '.join(p.value for p in Provider)}[/dim]")
            else:
                # Show provider selection menu
                console.print("\n[bold]╔═══════════════════════════════════════════════════════╗[/bold]")
                console.print("[bold]║              Choose AI Provider                       ║[/bold]")
                console.print("[bold]╚═══════════════════════════════════════════════════════╝[/bold]\n")
                
                providers = list(Provider)
                provider_info = {
                    Provider.OLLAMA: ("Local, Free, Unlimited", "🖥️"),
                    Provider.GEMINI: ("Google, Free Tier", "🌐"),
                    Provider.MISTRAL: ("Fast, Best for Coding", "⚡"),
                    Provider.OPENAI: ("Best Quality, Paid", "🤖"),
                    Provider.GROQ: ("Ultra Fast, Free Tier", "🚀"),
                }
                
                for i, p in enumerate(providers, 1):
                    info, emoji = provider_info.get(p, ("", ""))
                    marker = " [green]◄ current[/green]" if p == self.config.provider else ""
                    console.print(f"  [cyan]{i}[/cyan]. {emoji} {p.value.upper()} - {info}{marker}")
                
                console.print(f"\n  [dim]0. Cancel[/dim]")
                
                try:
                    choice = console.input("\nSelect provider: ").strip()
                    if choice and choice != "0":
                        choice_num = int(choice)
                        if 1 <= choice_num <= len(providers):
                            selected = providers[choice_num - 1]
                            pconfig = PROVIDER_CONFIG.get(selected, {})
                            
                            # Show models for this provider
                            console.print(f"\n[bold]Models for {selected.value.upper()}:[/bold]\n")
                            
                            models = pconfig.get("models", [])
                            coding_models = [m for m in models if m.get("type") == "coding"]
                            general_models = [m for m in models if m.get("type") == "general"]
                            vision_models = [m for m in models if m.get("type") == "vision"]
                            
                            all_models = []
                            
                            if coding_models:
                                console.print("  [yellow]── Coding ──[/yellow]")
                                for m in coding_models:
                                    all_models.append(m)
                                    idx = len(all_models)
                                    console.print(f"  [cyan]{idx}[/cyan]. {m['name']} [dim]({m['desc']})[/dim]")
                            
                            if general_models:
                                console.print("  [yellow]── General ──[/yellow]")
                                for m in general_models:
                                    all_models.append(m)
                                    idx = len(all_models)
                                    console.print(f"  [cyan]{idx}[/cyan]. {m['name']} [dim]({m['desc']})[/dim]")
                            
                            if vision_models:
                                console.print("  [yellow]── Vision ──[/yellow]")
                                for m in vision_models:
                                    all_models.append(m)
                                    idx = len(all_models)
                                    console.print(f"  [cyan]{idx}[/cyan]. {m['name']} [dim]({m['desc']})[/dim]")
                            
                            console.print(f"\n  [dim]0. Use default ({pconfig.get('default_model', 'N/A')})[/dim]")
                            
                            model_choice = console.input("\nSelect model: ").strip()
                            
                            selected_model = pconfig.get("default_model")
                            if model_choice and model_choice != "0":
                                model_idx = int(model_choice)
                                if 1 <= model_idx <= len(all_models):
                                    selected_model = all_models[model_idx - 1]["name"]
                            
                            # Ask for API key if not Ollama and not set
                            if selected != Provider.OLLAMA:
                                env_key = pconfig.get("env_key", "API_KEY")
                                existing_key = os.environ.get(env_key)
                                
                                if not existing_key:
                                    key_urls = {
                                        Provider.GEMINI: "https://makersuite.google.com/app/apikey",
                                        Provider.MISTRAL: "https://console.mistral.ai/",
                                        Provider.OPENAI: "https://platform.openai.com/api-keys",
                                        Provider.GROQ: "https://console.groq.com/",
                                    }
                                    url = key_urls.get(selected, "")
                                    console.print(f"\n[bold]Enter API Key[/bold]")
                                    if url:
                                        console.print(f"[dim]Get key from: {url}[/dim]")
                                    
                                    api_key = console.input(f"{env_key}: ").strip()
                                    if api_key:
                                        self.config.set_provider(selected, api_key)
                                        self.config.model.name = selected_model
                                    else:
                                        console.print("[error]API key required![/error]")
                                        return True
                                else:
                                    self.config.set_provider(selected)
                                    self.config.model.name = selected_model
                            else:
                                self.config.set_provider(selected)
                                self.config.model.name = selected_model
                            
                            console.print(f"\n[success]Provider: {selected.value}[/success]")
                            console.print(f"[success]Model: {selected_model}[/success]")
                        else:
                            console.print("[error]Invalid selection[/error]")
                except ValueError:
                    console.print("[error]Please enter a valid number[/error]")
                except KeyboardInterrupt:
                    console.print("\n[dim]Cancelled[/dim]")
        elif cmd_name == "/model":
            if cmd_args:
                self.config.model_name = cmd_args
                console.print(f"[success]Model changed to: {cmd_args} [/success]")
            else:
                console.print(f"Current model: {self.config.model_name}")
        elif cmd_name == "/vision":
            if cmd_args:
                self.config.model.vision_model = cmd_args
                console.print(f"[success]Vision model changed to: {cmd_args} [/success]")
            else:
                console.print(f"Current vision model: {self.config.vision_model_name}")
        elif cmd_name == "/paste":
            # Paste image from clipboard
            image_path = get_clipboard_image()
            if image_path:
                self.config.image_path = image_path
                console.print(f"[success]Image pasted from clipboard![/success]")
                console.print(f"[dim]Saved to: {image_path}[/dim]")
                console.print(f"[dim]Now type your question about the image.[/dim]")
            else:
                console.print("[error]No image found in clipboard![/error]")
                console.print("[dim]Copy an image (Ctrl+C) first, then use /paste[/dim]")
        elif cmd_name == "/models":
            import subprocess
            try:
                result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    models = []
                    for line in lines[1:]:
                        if line.strip():
                            model_name = line.split()[0]
                            models.append(model_name)
                    
                    if not models:
                        console.print("[error]No models found.[/error]")
                    else:
                        console.print("\n[bold]Available Ollama Models:[/bold]")
                        for i, m in enumerate(models, 1):
                            marker = " [green]◄ current[/green]" if m == self.config.model_name else ""
                            console.print(f"  [cyan]{i}[/cyan]. {m}{marker}")
                        
                        console.print(f"\n  [dim]0. Cancel[/dim]")
                        console.print("\n[bold]Select model to switch (or 0 to cancel):[/bold]")
                        
                        try:
                            choice = console.input("> ").strip()
                            if choice and choice != "0":
                                choice_num = int(choice)
                                if 1 <= choice_num <= len(models):
                                    selected = models[choice_num - 1]
                                    self.config.model_name = selected
                                    console.print(f"[success]Model changed to: {selected}[/success]")
                                else:
                                    console.print("[error]Invalid selection[/error]")
                        except ValueError:
                            console.print("[error]Please enter a valid number[/error]")
                        except KeyboardInterrupt:
                            console.print("\n[dim]Cancelled[/dim]")
                else:
                    console.print("[error]Failed to list models. Is Ollama running?[/error]")
            except FileNotFoundError:
                console.print("[error]Ollama not found.[/error]")
        elif cmd_name == "/approval":
            if cmd_args:
                try:
                    approval = ApprovalPolicy(cmd_args)
                    self.config.approval = approval
                    console.print(
                        f"[success]Approval policy changed to: {cmd_args} [/success]"
                    )
                except:
                    console.print(
                        f"[error]Incorrect approval policy: {cmd_args} [/error]"
                    )
                    console.print(
                        f"Valid options: {', '.join(p for p in ApprovalPolicy)}"
                    )
            else:
                console.print(f"Current approval policy: {self.config.approval.value}")
        elif cmd_name == "/stats":
            stats = self.agent.session.get_stats()
            console.print("\n[bold]Session Statistics [/bold]")
            for key, value in stats.items():
                console.print(f"   {key}: {value}")
        elif cmd_name == "/tools":
            tools = self.agent.session.tool_registry.get_tools()
            console.print(f"\n[bold]Available tools ({len(tools)}) [/bold]")
            for tool in tools:
                console.print(f"  • {tool.name}")
        elif cmd_name == "/mcp":
            mcp_servers = self.agent.session.mcp_manager.get_all_servers()
            console.print(f"\n[bold]MCP Servers ({len(mcp_servers)}) [/bold]")
            for server in mcp_servers:
                status = server["status"]
                status_color = "green" if status == "connected" else "red"
                console.print(
                    f"  • {server['name']}: [{status_color}]{status}[/{status_color}] ({server['tools']} tools)"
                )
        elif cmd_name == "/save":
            persistence_manager = PersistenceManager()
            session_snapshot = SessionSnapshot(
                session_id=self.agent.session.session_id,
                created_at=self.agent.session.created_at,
                updated_at=self.agent.session.updated_at,
                turn_count=self.agent.session.turn_count,
                messages=self.agent.session.context_manager.get_messages(),
                total_usage=self.agent.session.context_manager.total_usage,
            )
            persistence_manager.save_session(session_snapshot)
            console.print(
                f"[success]Session saved: {self.agent.session.session_id}[/success]"
            )
        elif cmd_name == "/sessions":
            persistence_manager = PersistenceManager()
            sessions = persistence_manager.list_sessions()
            console.print("\n[bold]Saved Sessions[/bold]")
            for s in sessions:
                console.print(
                    f"  • {s['session_id']} (turns: {s['turn_count']}, updated: {s['updated_at']})"
                )
        elif cmd_name == "/resume":
            if not cmd_args:
                console.print(f"[error]Usage: /resume <session_id> [/error]")
            else:
                persistence_manager = PersistenceManager()
                snapshot = persistence_manager.load_session(cmd_args)
                if not snapshot:
                    console.print(f"[error]Session does not exist [/error]")
                else:
                    session = Session(
                        config=self.config,
                    )
                    await session.initialize()
                    session.session_id = snapshot.session_id
                    session.created_at = snapshot.created_at
                    session.updated_at = snapshot.updated_at
                    session.turn_count = snapshot.turn_count
                    session.context_manager.total_usage = snapshot.total_usage

                    for msg in snapshot.messages:
                        if msg.get("role") == "system":
                            continue
                        elif msg["role"] == "user":
                            session.context_manager.add_user_message(
                                msg.get("content", "")
                            )
                        elif msg["role"] == "assistant":
                            session.context_manager.add_assistant_message(
                                msg.get("content", ""), msg.get("tool_calls")
                            )
                        elif msg["role"] == "tool":
                            session.context_manager.add_tool_result(
                                msg.get("tool_call_id", ""), msg.get("content", "")
                            )

                    await self.agent.session.client.close()
                    await self.agent.session.mcp_manager.shutdown()

                    self.agent.session = session
                    console.print(
                        f"[success]Resumed session: {session.session_id}[/success]"
                    )
        elif cmd_name == "/checkpoint":
            persistence_manager = PersistenceManager()
            session_snapshot = SessionSnapshot(
                session_id=self.agent.session.session_id,
                created_at=self.agent.session.created_at,
                updated_at=self.agent.session.updated_at,
                turn_count=self.agent.session.turn_count,
                messages=self.agent.session.context_manager.get_messages(),
                total_usage=self.agent.session.context_manager.total_usage,
            )
            checkpoint_id = persistence_manager.save_checkpoint(session_snapshot)
            console.print(f"[success]Checkpoint created: {checkpoint_id}[/success]")
        elif cmd_name == "/restore":
            if not cmd_args:
                console.print(f"[error]Usage: /restire <checkpoint_id> [/error]")
            else:
                persistence_manager = PersistenceManager()
                snapshot = persistence_manager.load_checkpoint(cmd_args)
                if not snapshot:
                    console.print(f"[error]Checkpoint does not exist [/error]")
                else:
                    session = Session(
                        config=self.config,
                    )
                    await session.initialize()
                    session.session_id = snapshot.session_id
                    session.created_at = snapshot.created_at
                    session.updated_at = snapshot.updated_at
                    session.turn_count = snapshot.turn_count
                    session.context_manager.total_usage = snapshot.total_usage

                    for msg in snapshot.messages:
                        if msg.get("role") == "system":
                            continue
                        elif msg["role"] == "user":
                            session.context_manager.add_user_message(
                                msg.get("content", "")
                            )
                        elif msg["role"] == "assistant":
                            session.context_manager.add_assistant_message(
                                msg.get("content", ""), msg.get("tool_calls")
                            )
                        elif msg["role"] == "tool":
                            session.context_manager.add_tool_result(
                                msg.get("tool_call_id", ""), msg.get("content", "")
                            )

                    await self.agent.session.client.close()
                    await self.agent.session.mcp_manager.shutdown()

                    self.agent.session = session
                    console.print(
                        f"[success]Resumed session: {session.session_id}, checkpoint: {checkpoint_id}[/success]"
                    )
        else:
            console.print(f"[error]Unknown command: {cmd_name}[/error]")

        return True


@click.command()
@click.argument("prompt", required=False)
@click.option(
    "--cwd",
    "-c",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Current working directory",
)
@click.option(
    "--image",
    "-i",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Image file to analyze (uses vision model)",
)
@click.option(
    "--model",
    "-m",
    type=str,
    help="Specify Ollama model to use (e.g., llama3, codellama, mistral)",
)
@click.option(
    "--vision-model",
    "-v",
    type=str,
    help="Specify vision model for image tasks (e.g., llava, bakllava)",
)
@click.option(
    "--list-models",
    "-l",
    is_flag=True,
    help="List all available Ollama models",
)
@click.option(
    "--paste",
    "-p",
    is_flag=True,
    help="Use image from clipboard (copy image first with Ctrl+C)",
)
@click.option(
    "--provider",
    type=click.Choice(["ollama", "gemini", "mistral", "openai", "groq"], case_sensitive=False),
    help="AI provider to use (default: ollama)",
)
@click.option(
    "--api-key",
    "-k",
    type=str,
    help="API key for the selected provider",
)
@click.option(
    "--setup",
    "-s",
    is_flag=True,
    help="Interactive setup - choose provider, model, and enter API key",
)
def main(
    prompt: str | None,
    cwd: Path | None,
    image: Path | None,
    model: str | None,
    vision_model: str | None,
    list_models: bool,
    paste: bool,
    provider: str | None,
    api_key: str | None,
    setup: bool,
):
    # List available models if requested
    if list_models:
        import subprocess
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
            if result.returncode == 0:
                # Parse models from output
                lines = result.stdout.strip().split('\n')
                models = []
                for line in lines[1:]:  # Skip header
                    if line.strip():
                        model_name = line.split()[0]
                        models.append(model_name)
                
                if not models:
                    console.print("[error]No models found. Pull a model first: ollama pull llama3[/error]")
                    return
                
                # Show interactive menu
                console.print("\n[bold]╔═══════════════════════════════════════╗[/bold]")
                console.print("[bold]║     Available Ollama Models           ║[/bold]")
                console.print("[bold]╚═══════════════════════════════════════╝[/bold]\n")
                
                for i, m in enumerate(models, 1):
                    console.print(f"  [cyan]{i}[/cyan]. {m}")
                
                console.print(f"\n  [dim]0. Exit without selecting[/dim]")
                console.print("\n[bold]Select model number (or press Enter to skip):[/bold]")
                
                try:
                    choice = input("> ").strip()
                    
                    if not choice or choice == "0":
                        console.print("[dim]No model selected. Exiting.[/dim]")
                        return
                    
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(models):
                        selected_model = models[choice_num - 1]
                        console.print(f"\n[success]Selected: {selected_model}[/success]")
                        console.print(f"\n[bold]Usage:[/bold]")
                        console.print(f"  abid -m {selected_model} \"your prompt here\"")
                        console.print(f"  abid --model {selected_model} \"your prompt here\"")
                        console.print(f"\n[dim]Or in interactive mode: /model {selected_model}[/dim]")
                    else:
                        console.print("[error]Invalid selection[/error]")
                except ValueError:
                    console.print("[error]Please enter a valid number[/error]")
                except KeyboardInterrupt:
                    console.print("\n[dim]Cancelled[/dim]")
            else:
                console.print("[error]Failed to list models. Is Ollama running?[/error]")
        except FileNotFoundError:
            console.print("[error]Ollama not found. Please install Ollama first.[/error]")
        return

    # Interactive setup mode
    if setup:
        console.print("\n[bold]╔═══════════════════════════════════════════════════════╗[/bold]")
        console.print("[bold]║           ABID - AI Provider Setup                    ║[/bold]")
        console.print("[bold]╚═══════════════════════════════════════════════════════╝[/bold]\n")
        
        # Step 1: Choose Provider
        console.print("[bold]Step 1: Choose AI Provider[/bold]\n")
        providers = list(Provider)
        provider_info = {
            Provider.OLLAMA: ("Local, Free, Unlimited", "🖥️"),
            Provider.GEMINI: ("Google, Free Tier Available", "🌐"),
            Provider.MISTRAL: ("Fast, Best for Coding", "⚡"),
            Provider.OPENAI: ("Best Quality, Paid", "🤖"),
            Provider.GROQ: ("Ultra Fast, Free Tier", "🚀"),
        }
        
        for i, p in enumerate(providers, 1):
            info, emoji = provider_info.get(p, ("", ""))
            console.print(f"  [cyan]{i}[/cyan]. {emoji} {p.value.upper()} - {info}")
        
        console.print(f"\n  [dim]0. Cancel[/dim]")
        
        try:
            choice = input("\nSelect provider (1-5): ").strip()
            if not choice or choice == "0":
                console.print("[dim]Setup cancelled.[/dim]")
                return
            
            choice_num = int(choice)
            if not (1 <= choice_num <= len(providers)):
                console.print("[error]Invalid selection[/error]")
                return
            
            selected_provider = providers[choice_num - 1]
            pconfig = PROVIDER_CONFIG.get(selected_provider, {})
            
            # Step 2: Show available models for this provider
            console.print(f"\n[bold]Step 2: Choose Model for {selected_provider.value.upper()}[/bold]\n")
            
            models = pconfig.get("models", [])
            
            # Group by type
            coding_models = [m for m in models if m.get("type") == "coding"]
            general_models = [m for m in models if m.get("type") == "general"]
            vision_models = [m for m in models if m.get("type") == "vision"]
            
            all_models = []
            
            if coding_models:
                console.print("  [yellow]── Coding Models ──[/yellow]")
                for m in coding_models:
                    all_models.append(m)
                    idx = len(all_models)
                    console.print(f"  [cyan]{idx}[/cyan]. {m['name']} [dim]({m['desc']})[/dim]")
            
            if general_models:
                console.print("\n  [yellow]── General Models ──[/yellow]")
                for m in general_models:
                    all_models.append(m)
                    idx = len(all_models)
                    console.print(f"  [cyan]{idx}[/cyan]. {m['name']} [dim]({m['desc']})[/dim]")
            
            if vision_models:
                console.print("\n  [yellow]── Vision Models ──[/yellow]")
                for m in vision_models:
                    all_models.append(m)
                    idx = len(all_models)
                    console.print(f"  [cyan]{idx}[/cyan]. {m['name']} [dim]({m['desc']})[/dim]")
            
            console.print(f"\n  [dim]0. Use default ({pconfig.get('default_model', 'N/A')})[/dim]")
            
            model_choice = input("\nSelect model: ").strip()
            
            selected_model = pconfig.get("default_model")
            if model_choice and model_choice != "0":
                model_idx = int(model_choice)
                if 1 <= model_idx <= len(all_models):
                    selected_model = all_models[model_idx - 1]["name"]
            
            # Step 3: API Key (if not Ollama)
            selected_api_key = None
            if selected_provider != Provider.OLLAMA:
                env_key = pconfig.get("env_key", "API_KEY")
                existing_key = os.environ.get(env_key)
                
                console.print(f"\n[bold]Step 3: Enter API Key[/bold]")
                
                if existing_key:
                    console.print(f"[dim]Found existing {env_key} in environment[/dim]")
                    use_existing = input("Use existing key? (Y/n): ").strip().lower()
                    if use_existing != 'n':
                        selected_api_key = existing_key
                
                if not selected_api_key:
                    # Show where to get API key
                    key_urls = {
                        Provider.GEMINI: "https://makersuite.google.com/app/apikey",
                        Provider.MISTRAL: "https://console.mistral.ai/",
                        Provider.OPENAI: "https://platform.openai.com/api-keys",
                        Provider.GROQ: "https://console.groq.com/",
                    }
                    url = key_urls.get(selected_provider, "")
                    if url:
                        console.print(f"[dim]Get your API key from: {url}[/dim]")
                    
                    selected_api_key = input(f"Enter {env_key}: ").strip()
                    
                    if not selected_api_key:
                        console.print("[error]API key is required for this provider![/error]")
                        return
            
            # Setup complete - show summary
            console.print("\n[bold]╔═══════════════════════════════════════════════════════╗[/bold]")
            console.print("[bold]║                  Setup Complete!                      ║[/bold]")
            console.print("[bold]╚═══════════════════════════════════════════════════════╝[/bold]\n")
            
            console.print(f"  Provider: [green]{selected_provider.value}[/green]")
            console.print(f"  Model: [green]{selected_model}[/green]")
            if selected_api_key:
                console.print(f"  API Key: [green]{'*' * 20}...{selected_api_key[-4:]}[/green]")
            
            # Ask to start
            start_now = input("\nStart ABID now? (Y/n): ").strip().lower()
            if start_now == 'n':
                # Show usage command
                console.print("\n[bold]To use later:[/bold]")
                if selected_provider == Provider.OLLAMA:
                    console.print(f"  abid -m {selected_model} \"your prompt\"")
                else:
                    console.print(f"  abid --provider {selected_provider.value} -k YOUR_KEY -m {selected_model} \"your prompt\"")
                return
            
            # Set config and continue
            try:
                config = load_config(cwd=cwd)
            except Exception as e:
                console.print(f"[error]Configuration Error: {e}[/error]")
                sys.exit(1)
            
            config.set_provider(selected_provider, selected_api_key)
            config.model.name = selected_model
            
            # Continue to interactive mode
            cli = CLI(config)
            asyncio.run(cli.run_interactive())
            return
            
        except ValueError:
            console.print("[error]Please enter a valid number[/error]")
            return
        except KeyboardInterrupt:
            console.print("\n[dim]Setup cancelled.[/dim]")
            return

    try:
        config = load_config(cwd=cwd)
    except Exception as e:
        console.print(f"[error]Configuration Error: {e}[/error]")
        sys.exit(1)

    # Set provider if specified
    if provider:
        try:
            p = Provider(provider.lower())
            config.set_provider(p, api_key)
            console.print(f"[dim]Using provider: {p.value}[/dim]")
        except ValueError:
            console.print(f"[error]Unknown provider: {provider}[/error]")
            sys.exit(1)
    elif api_key:
        # If only API key provided, set it for current provider
        config.set_provider(config.provider, api_key)

    # Override model if specified via CLI
    if model:
        config.model.name = model
        console.print(f"[dim]Using model: {model}[/dim]")
    
    # Override vision model if specified via CLI
    if vision_model:
        config.model.vision_model = vision_model
        console.print(f"[dim]Using vision model: {vision_model}[/dim]")

    # Store image path in config for later use
    if image:
        config.image_path = str(image)
    elif paste:
        # Try to get image from clipboard
        clipboard_image = get_clipboard_image()
        if clipboard_image:
            config.image_path = clipboard_image
            console.print(f"[success]Using image from clipboard[/success]")
        else:
            console.print("[error]No image found in clipboard![/error]")
            console.print("[dim]Copy an image first (Ctrl+C on image), then run again with --paste[/dim]")
            sys.exit(1)
    else:
        config.image_path = None

    errors = config.validate()

    if errors:
        for error in errors:
            console.print(f"[error]{error}[/error]")

        sys.exit(1)

    cli = CLI(config)

    # messages = [{"role": "user", "content": prompt}]
    if prompt:
        result = asyncio.run(cli.run_single(prompt))
        if result is None:
            sys.exit(1)
    else:
        asyncio.run(cli.run_interactive())


main()
