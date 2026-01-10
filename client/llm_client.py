import asyncio
import base64
from pathlib import Path
from typing import Any, AsyncGenerator
from openai import APIConnectionError, APIError, AsyncOpenAI, RateLimitError

from client.response import (
    StreamEventType,
    StreamEvent,
    TextDelta,
    TokenUsage,
    ToolCall,
    ToolCallDelta,
    parse_tool_call_arguments,
)
from config.config import Config, Provider


class LLMClient:
    def __init__(self, config: Config) -> None:
        self._client: AsyncOpenAI | None = None
        self._max_retries: int = 3
        self.config = config

    def get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None

    def _build_tools(self, tools: list[dict[str, Any]]):
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get(
                        "parameters",
                        {
                            "type": "object",
                            "properties": {},
                        },
                    ),
                },
            }
            for tool in tools
        ]

    def _has_image_in_messages(self, messages: list[dict[str, Any]]) -> bool:
        """Check if any message contains an image."""
        for msg in messages:
            content = msg.get("content")
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "image_url":
                        return True
        return False

    def _encode_image_to_base64(self, image_path: str) -> str:
        """Encode an image file to base64."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _get_image_mime_type(self, image_path: str) -> str:
        """Get MIME type from image path."""
        ext = Path(image_path).suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        return mime_types.get(ext, "image/jpeg")

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        stream: bool = True,
        image_path: str | None = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        # Route to appropriate provider
        provider = self.config.provider
        
        if provider == Provider.MISTRAL:
            async for event in self._mistral_chat(messages, tools, image_path):
                yield event
            return
        elif provider == Provider.GEMINI:
            async for event in self._gemini_chat(messages, tools, image_path):
                yield event
            return
        
        # Default: Use OpenAI-compatible client (Ollama, OpenAI, Groq)
        async for event in self._openai_chat(messages, tools, stream, image_path):
            yield event

    async def _mistral_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        image_path: str | None = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Chat using Mistral's native SDK with tool support"""
        try:
            import httpx
            import json
            
            model = self.config.model_name
            api_key = self.config.api_key
            
            # Convert messages to Mistral format
            mistral_messages = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                tool_calls = msg.get("tool_calls")
                
                if isinstance(content, list):
                    content = " ".join(
                        item.get("text", "") for item in content 
                        if isinstance(item, dict) and item.get("type") == "text"
                    )
                
                msg_dict = {"role": role, "content": content or ""}
                
                if tool_calls and role == "assistant":
                    msg_dict["tool_calls"] = tool_calls
                
                if role == "tool":
                    msg_dict = {
                        "role": "tool",
                        "content": content,
                        "tool_call_id": msg.get("tool_call_id", ""),
                    }
                
                mistral_messages.append(msg_dict)
            
            # Build tools for Mistral format
            mistral_tools = None
            if tools:
                mistral_tools = [
                    {
                        "type": "function",
                        "function": {
                            "name": tool["name"],
                            "description": tool.get("description", ""),
                            "parameters": tool.get("parameters", {"type": "object", "properties": {}}),
                        }
                    }
                    for tool in tools
                ]
            
            # Build request payload
            payload = {
                "model": model,
                "messages": mistral_messages,
            }
            if mistral_tools:
                payload["tools"] = mistral_tools
                payload["tool_choice"] = "auto"
            
            # Make HTTP request to Mistral API
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "https://api.mistral.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                
                if response.status_code != 200:
                    error_data = response.json() if response.text else {}
                    error_msg = error_data.get("error", {}).get("message", response.text)
                    yield StreamEvent(
                        type=StreamEventType.ERROR,
                        error=f"Mistral API error ({response.status_code}): {error_msg}",
                    )
                    return
                
                data = response.json()
            
            if data and data.get("choices"):
                choice = data["choices"][0]
                message = choice.get("message", {})
                content = message.get("content", "")
                
                # Check for tool calls
                if message.get("tool_calls"):
                    for tc in message["tool_calls"]:
                        tc_id = tc.get("id", "")
                        func = tc.get("function", {})
                        func_name = func.get("name", "")
                        func_args = func.get("arguments", "{}")
                        
                        yield StreamEvent(
                            type=StreamEventType.TOOL_CALL_START,
                            tool_call_delta=ToolCallDelta(
                                call_id=tc_id,
                                name=func_name,
                            ),
                        )
                        
                        yield StreamEvent(
                            type=StreamEventType.TOOL_CALL_COMPLETE,
                            tool_call=ToolCall(
                                call_id=tc_id,
                                name=func_name,
                                arguments=parse_tool_call_arguments(func_args),
                            ),
                        )
                
                if content:
                    yield StreamEvent(
                        type=StreamEventType.TEXT_DELTA,
                        text_delta=TextDelta(content),
                    )
                
                usage_data = data.get("usage", {})
                yield StreamEvent(
                    type=StreamEventType.MESSAGE_COMPLETE,
                    finish_reason=choice.get("finish_reason", "stop"),
                    usage=TokenUsage(
                        prompt_tokens=usage_data.get("prompt_tokens", 0),
                        completion_tokens=usage_data.get("completion_tokens", 0),
                        total_tokens=usage_data.get("total_tokens", 0),
                        cached_tokens=0,
                    ) if usage_data else None,
                )
            else:
                yield StreamEvent(
                    type=StreamEventType.ERROR,
                    error="No response from Mistral API",
                )
                
        except Exception as e:
            yield StreamEvent(
                type=StreamEventType.ERROR,
                error=f"Mistral API error: {e}",
            )

    async def _gemini_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        image_path: str | None = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Chat using Google's Gemini API with tool support"""
        try:
            import httpx
            import json
            
            model = self.config.model_name
            api_key = self.config.api_key
            
            # Convert messages to Gemini format
            gemini_contents = []
            system_instruction = None
            
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if isinstance(content, list):
                    content = " ".join(
                        item.get("text", "") for item in content 
                        if isinstance(item, dict) and item.get("type") == "text"
                    )
                
                if role == "system":
                    system_instruction = content
                elif role == "user":
                    gemini_contents.append({
                        "role": "user",
                        "parts": [{"text": content}]
                    })
                elif role == "assistant":
                    gemini_contents.append({
                        "role": "model",
                        "parts": [{"text": content}]
                    })
                elif role == "tool":
                    # Tool result
                    tool_call_id = msg.get("tool_call_id", "unknown")
                    gemini_contents.append({
                        "role": "function",
                        "parts": [{
                            "functionResponse": {
                                "name": tool_call_id,
                                "response": {"result": content}
                            }
                        }]
                    })
            
            # Build Gemini tools
            gemini_tools = None
            if tools:
                function_declarations = []
                for tool in tools:
                    params = tool.get("parameters", {"type": "object", "properties": {}})
                    # Gemini requires specific format
                    func_decl = {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": params,
                    }
                    function_declarations.append(func_decl)
                gemini_tools = [{"functionDeclarations": function_declarations}]
            
            # Build request payload
            payload = {
                "contents": gemini_contents,
            }
            
            if system_instruction:
                payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
            
            if gemini_tools:
                payload["tools"] = gemini_tools
            
            # Make HTTP request to Gemini API
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                )
                
                if response.status_code != 200:
                    error_data = response.json() if response.text else {}
                    error_msg = error_data.get("error", {}).get("message", response.text)
                    yield StreamEvent(
                        type=StreamEventType.ERROR,
                        error=f"Gemini API error ({response.status_code}): {error_msg}",
                    )
                    return
                
                data = response.json()
            
            if data and data.get("candidates"):
                candidate = data["candidates"][0]
                content_parts = candidate.get("content", {}).get("parts", [])
                
                for part in content_parts:
                    # Check for function call
                    if "functionCall" in part:
                        fc = part["functionCall"]
                        func_name = fc.get("name", "")
                        func_args = fc.get("args", {})
                        
                        yield StreamEvent(
                            type=StreamEventType.TOOL_CALL_START,
                            tool_call_delta=ToolCallDelta(
                                call_id=func_name,
                                name=func_name,
                            ),
                        )
                        
                        yield StreamEvent(
                            type=StreamEventType.TOOL_CALL_COMPLETE,
                            tool_call=ToolCall(
                                call_id=func_name,
                                name=func_name,
                                arguments=func_args if isinstance(func_args, dict) else {},
                            ),
                        )
                    
                    # Check for text
                    if "text" in part:
                        yield StreamEvent(
                            type=StreamEventType.TEXT_DELTA,
                            text_delta=TextDelta(part["text"]),
                        )
                
                # Usage info
                usage_data = data.get("usageMetadata", {})
                yield StreamEvent(
                    type=StreamEventType.MESSAGE_COMPLETE,
                    finish_reason="stop",
                    usage=TokenUsage(
                        prompt_tokens=usage_data.get("promptTokenCount", 0),
                        completion_tokens=usage_data.get("candidatesTokenCount", 0),
                        total_tokens=usage_data.get("totalTokenCount", 0),
                        cached_tokens=0,
                    ) if usage_data else None,
                )
            else:
                yield StreamEvent(
                    type=StreamEventType.ERROR,
                    error="No response from Gemini API",
                )
                
        except Exception as e:
            yield StreamEvent(
                type=StreamEventType.ERROR,
                error=f"Gemini API error: {e}",
            )

    async def _openai_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        stream: bool = True,
        image_path: str | None = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Chat using OpenAI-compatible API (Ollama, OpenAI, Groq)"""
        client = self.get_client()

        # Check if we need to use vision model
        has_image = self._has_image_in_messages(messages) or image_path is not None
        model_to_use = self.config.vision_model_name if has_image else self.config.model_name

        # If image_path provided, add it to the last user message
        if image_path and Path(image_path).exists():
            messages = self._add_image_to_messages(messages, image_path)

        kwargs = {
            "model": model_to_use,
            "messages": messages,
            "stream": stream,
        }

        # Vision models typically don't support tools well
        if tools and not has_image:
            kwargs["tools"] = self._build_tools(tools)
            kwargs["tool_choice"] = "auto"

        for attempt in range(self._max_retries + 1):
            try:
                if stream:
                    async for event in self._stream_response(client, kwargs):
                        yield event
                else:
                    event = await self._non_stream_response(client, kwargs)
                    yield event
                return
            except RateLimitError as e:
                if attempt < self._max_retries:
                    wait_time = 2**attempt
                    await asyncio.sleep(wait_time)
                else:
                    yield StreamEvent(
                        type=StreamEventType.ERROR,
                        error=f"Rate limit exceeded: {e}",
                    )
                    return
            except APIConnectionError as e:
                if attempt < self._max_retries:
                    wait_time = 2**attempt
                    await asyncio.sleep(wait_time)
                else:
                    yield StreamEvent(
                        type=StreamEventType.ERROR,
                        error=f"Connection error: {e}",
                    )
                    return
            except APIError as e:
                yield StreamEvent(
                    type=StreamEventType.ERROR,
                    error=f"API error: {e}",
                )
                return

    def _add_image_to_messages(
        self, messages: list[dict[str, Any]], image_path: str
    ) -> list[dict[str, Any]]:
        """Add image to the last user message."""
        messages = messages.copy()
        
        # Find last user message
        for i in range(len(messages) - 1, -1, -1):
            if messages[i].get("role") == "user":
                content = messages[i].get("content", "")
                
                # Convert to multimodal format
                base64_image = self._encode_image_to_base64(image_path)
                mime_type = self._get_image_mime_type(image_path)
                
                messages[i]["content"] = [
                    {"type": "text", "text": content if isinstance(content, str) else str(content)},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_image}"
                        }
                    }
                ]
                break
        
        return messages

    async def _stream_response(
        self,
        client: AsyncOpenAI,
        kwargs: dict[str, Any],
    ) -> AsyncGenerator[StreamEvent, None]:
        response = await client.chat.completions.create(**kwargs)

        finish_reason: str | None = None
        usage: TokenUsage | None = None
        tool_calls: dict[int, dict[str, Any]] = {}

        async for chunk in response:
            if hasattr(chunk, "usage") and chunk.usage:
                usage = TokenUsage(
                    prompt_tokens=chunk.usage.prompt_tokens,
                    completion_tokens=chunk.usage.completion_tokens,
                    total_tokens=chunk.usage.total_tokens,
                    cached_tokens=getattr(getattr(chunk.usage, 'prompt_tokens_details', None), 'cached_tokens', 0) or 0,
                )

            if not chunk.choices:
                continue

            choice = chunk.choices[0]
            delta = choice.delta

            if choice.finish_reason:
                finish_reason = choice.finish_reason

            if delta.content:
                yield StreamEvent(
                    type=StreamEventType.TEXT_DELTA,
                    text_delta=TextDelta(delta.content),
                )

            if delta.tool_calls:
                for tool_call_delta in delta.tool_calls:
                    idx = tool_call_delta.index

                    if idx not in tool_calls:
                        tool_calls[idx] = {
                            "id": tool_call_delta.id or "",
                            "name": "",
                            "arguments": "",
                        }

                        if tool_call_delta.function:
                            if tool_call_delta.function.name:
                                tool_calls[idx]["name"] = tool_call_delta.function.name
                                yield StreamEvent(
                                    type=StreamEventType.TOOL_CALL_START,
                                    tool_call_delta=ToolCallDelta(
                                        call_id=tool_calls[idx]["id"],
                                        name=tool_call_delta.function.name,
                                    ),
                                )

                        if tool_call_delta.function.arguments:
                            tool_calls[idx][
                                "arguments"
                            ] += tool_call_delta.function.arguments

                            yield StreamEvent(
                                type=StreamEventType.TOOL_CALL_DELTA,
                                tool_call_delta=ToolCallDelta(
                                    call_id=tool_calls[idx]["id"],
                                    name=tool_call_delta.function.name,
                                    arguments_delta=tool_call_delta.function.arguments,
                                ),
                            )

        for idx, tc in tool_calls.items():
            yield StreamEvent(
                type=StreamEventType.TOOL_CALL_COMPLETE,
                tool_call=ToolCall(
                    call_id=tc["id"],
                    name=tc["name"],
                    arguments=parse_tool_call_arguments(tc["arguments"]),
                ),
            )

        yield StreamEvent(
            type=StreamEventType.MESSAGE_COMPLETE,
            finish_reason=finish_reason,
            usage=usage,
        )

    async def _non_stream_response(
        self,
        client: AsyncOpenAI,
        kwargs: dict[str, Any],
    ) -> StreamEvent:
        response = await client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        message = choice.message

        text_delta = None
        if message.content:
            text_delta = TextDelta(content=message.content)

        tool_calls: list[ToolCall] = []
        if message.tool_calls:
            for tc in message.tool_calls:
                tool_calls.append(
                    ToolCall(
                        call_id=tc.id,
                        name=tc.function.name,
                        arguments=parse_tool_call_arguments(tc.function.arguments),
                    )
                )

        usage = None
        if response.usage:
            usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                cached_tokens=getattr(getattr(response.usage, 'prompt_tokens_details', None), 'cached_tokens', 0) or 0,
            )

        return StreamEvent(
            type=StreamEventType.MESSAGE_COMPLETE,
            text_delta=text_delta,
            finish_reason=choice.finish_reason,
            usage=usage,
        )
