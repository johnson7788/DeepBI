# -*- coding: utf-8 -*-
"""
@ author:
@ info: claude to chatgpt
@ date: 2024/2/1 21:22

pip install boto3
pip install tiktoken
config  .aws/config
        .aws/credentials
"""

import json
import time
try:
    import tiktoken
    import boto3
except:
    raise Exception("Error, need: pip install boto3 tiktoken")
# define default model
Claude_AI_MODEL = 'anthropic.claude-v2:1'
# define default temperature
Claude_AI_temperature = 0.1
Claude_role_map = {
    "system": "Human",
    "user": "Human",
    "assistant": "Assistant",
}

Claude_stop_reason_map = {
    "stop_sequence": "stop",
    "max_tokens": "length",
}


class AWSClaudeClient:

    @classmethod
    def run(cls, apiKey, data, model_name=None, temperature=None):
        if "ApiKey" not in apiKey or "ApkSecret" not in apiKey:
            raise Exception("agent_llm llm api key empty use_model: ", model_name, " need apikey and ApkSecret")

        if model_name is None:
            model_name = Claude_AI_MODEL
        if temperature is None:
            temperature = Claude_AI_temperature

        prompt = cls.input_to_openai(data['messages'])
        client_obj = boto3.client(
            service_name='bedrock-runtime',
            region_name="us-east-1",
            aws_access_key_id=apiKey['ApiKey'],
            aws_secret_access_key=apiKey['ApkSecret']
        )
        body = json.dumps({
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens_to_sample": 100000,
            "top_p": 0.9,
        })
        modelId = model_name
        accept = 'application/json'
        contentType = 'application/json'
        response = client_obj.invoke_model(body=body, modelId=modelId, accept=accept, contentType=contentType)
        response_body = json.loads(response.get('body').read())
        return cls.output_to_openai(response_body)
        pass

    @classmethod
    def output_to_openai(cls, data):
        completion = data['completion']
        completion_tokens = cls.num_tokens_from_string(completion)
        openai_response = {
            "id": f"chatcmpl-{str(time.time())}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": Claude_AI_MODEL,
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": completion_tokens,
                "total_tokens": completion_tokens,
            },
            "choices": [
                {
                    "delta": {
                        "role": "assistant",
                        "content": completion,
                    },
                    "index": 0,
                    "finish_reason":  Claude_stop_reason_map[data.get("stop_reason")] if 'stop_reason' in data else None
                    if data.get("stop_reason")
                    else None,
                }
            ],
        }
        return openai_response
        pass

    @classmethod
    def input_to_openai(cls, messages):
        prompt = ""
        for message in messages:
            role = message["role"]
            content = message["content"]
            transformed_role = Claude_role_map[role]
            prompt += f"\n\n{transformed_role.capitalize()}: {content}"
        prompt += "\n\nAssistant: "
        return prompt

    @classmethod
    def num_tokens_from_string(cls, string: str, encoding_name: str = "cl100k_base") -> int:
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.get_encoding(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens

