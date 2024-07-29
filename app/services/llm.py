import logging
import re
import json
from typing import List
from loguru import logger
from openai import OpenAI
from openai import AzureOpenAI
from openai.types.chat import ChatCompletion

from app.config import config

_max_retries = 5


def _generate_response(prompt: str) -> str:
    content = ""
    llm_provider = config.app.get("llm_provider", "openai")
    logger.info(f"llm provider: {llm_provider}")
    if llm_provider == "g4f":
        model_name = config.app.get("g4f_model_name", "")
        if not model_name:
            model_name = "gpt-3.5-turbo-16k-0613"
        import g4f

        content = g4f.ChatCompletion.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
        )
    else:
        api_version = ""  # for azure
        if llm_provider == "moonshot":
            api_key = config.app.get("moonshot_api_key")
            model_name = config.app.get("moonshot_model_name")
            base_url = "https://api.moonshot.cn/v1"
        elif llm_provider == "ollama":
            # api_key = config.app.get("openai_api_key")
            api_key = "ollama"  # any string works but you are required to have one
            model_name = config.app.get("ollama_model_name")
            base_url = config.app.get("ollama_base_url", "")
            if not base_url:
                base_url = "http://localhost:11434/v1"
        elif llm_provider == "openai":
            api_key = config.app.get("openai_api_key")
            model_name = config.app.get("openai_model_name")
            base_url = config.app.get("openai_base_url", "")
            if not base_url:
                base_url = "https://api.openai.com/v1"
        elif llm_provider == "oneapi":
            api_key = config.app.get("oneapi_api_key")
            model_name = config.app.get("oneapi_model_name")
            base_url = config.app.get("oneapi_base_url", "")
        elif llm_provider == "azure":
            api_key = config.app.get("azure_api_key")
            model_name = config.app.get("azure_model_name")
            base_url = config.app.get("azure_base_url", "")
            api_version = config.app.get("azure_api_version", "2024-02-15-preview")
        elif llm_provider == "gemini":
            api_key = config.app.get("gemini_api_key")
            model_name = config.app.get("gemini_model_name")
            base_url = "***"
        elif llm_provider == "qwen":
            api_key = config.app.get("qwen_api_key")
            model_name = config.app.get("qwen_model_name")
            base_url = "***"
        elif llm_provider == "cloudflare":
            api_key = config.app.get("cloudflare_api_key")
            model_name = config.app.get("cloudflare_model_name")
            account_id = config.app.get("cloudflare_account_id")
            base_url = "***"
        elif llm_provider == "deepseek":
            api_key = config.app.get("deepseek_api_key")
            model_name = config.app.get("deepseek_model_name")
            base_url = config.app.get("deepseek_base_url")
            if not base_url:
                base_url = "https://api.deepseek.com"
        elif llm_provider == "ernie":
            api_key = config.app.get("ernie_api_key")
            secret_key = config.app.get("ernie_secret_key")
            base_url = config.app.get("ernie_base_url")
            model_name = "***"
            if not secret_key:
                raise ValueError(
                    f"{llm_provider}: secret_key is not set, please set it in the config.toml file."
                )
        else:
            raise ValueError(
                "llm_provider is not set, please set it in the config.toml file."
            )

        if not api_key:
            raise ValueError(
                f"{llm_provider}: api_key is not set, please set it in the config.toml file."
            )
        if not model_name:
            raise ValueError(
                f"{llm_provider}: model_name is not set, please set it in the config.toml file."
            )
        if not base_url:
            raise ValueError(
                f"{llm_provider}: base_url is not set, please set it in the config.toml file."
            )

        if llm_provider == "qwen":
            import dashscope
            from dashscope.api_entities.dashscope_response import GenerationResponse

            dashscope.api_key = api_key
            response = dashscope.Generation.call(
                model=model_name, messages=[{"role": "user", "content": prompt}]
            )
            if response:
                if isinstance(response, GenerationResponse):
                    status_code = response.status_code
                    if status_code != 200:
                        raise Exception(
                            f'[{llm_provider}] returned an error response: "{response}"'
                        )

                    content = response["output"]["text"]
                    return content.replace("\n", "")
                else:
                    raise Exception(
                        f'[{llm_provider}] returned an invalid response: "{response}"'
                    )
            else:
                raise Exception(f"[{llm_provider}] returned an empty response")

        if llm_provider == "gemini":
            import google.generativeai as genai

            genai.configure(api_key=api_key, transport="rest")

            generation_config = {
                "temperature": 0.5,
                "top_p": 1,
                "top_k": 1,
                "max_output_tokens": 2048,
            }

            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_ONLY_HIGH",
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_ONLY_HIGH",
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_ONLY_HIGH",
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_ONLY_HIGH",
                },
            ]

            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config,
                safety_settings=safety_settings,
            )

            try:
                response = model.generate_content(prompt)
                candidates = response.candidates
                generated_text = candidates[0].content.parts[0].text
            except (AttributeError, IndexError) as e:
                print("Gemini Error:", e)

            return generated_text

        if llm_provider == "cloudflare":
            import requests

            response = requests.post(
                f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model_name}",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "messages": [
                        {"role": "system", "content": "You are a friendly assistant"},
                        {"role": "user", "content": prompt},
                    ]
                },
            )
            result = response.json()
            logger.info(result)
            return result["result"]["response"]

        if llm_provider == "ernie":
            import requests

            params = {
                "grant_type": "client_credentials",
                "client_id": api_key,
                "client_secret": secret_key,
            }
            access_token = (
                requests.post("https://aip.baidubce.com/oauth/2.0/token", params=params)
                .json()
                .get("access_token")
            )
            url = f"{base_url}?access_token={access_token}"

            payload = json.dumps(
                {
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.5,
                    "top_p": 0.8,
                    "penalty_score": 1,
                    "disable_search": False,
                    "enable_citation": False,
                    "response_format": "text",
                }
            )
            headers = {"Content-Type": "application/json"}

            response = requests.request(
                "POST", url, headers=headers, data=payload
            ).json()
            return response.get("result")

        if llm_provider == "azure":
            client = AzureOpenAI(
                api_key=api_key,
                api_version=api_version,
                azure_endpoint=base_url,
            )
        else:
            client = OpenAI(
                api_key=api_key,
                base_url=base_url,
            )

        response = client.chat.completions.create(
            model=model_name, messages=[{"role": "user", "content": prompt}]
        )
        if response:
            if isinstance(response, ChatCompletion):
                content = response.choices[0].message.content
            else:
                raise Exception(
                    f'[{llm_provider}] returned an invalid response: "{response}", please check your network '
                    f"connection and try again."
                )
        else:
            raise Exception(
                f"[{llm_provider}] returned an empty response, please check your network connection and try again."
            )

    return content.replace("\n", "")


def generate_script(
    video_subject: str, language: str = "", paragraph_number: int = 1
) -> str:
    prompt = f"""
# 角色：视频文案本生成器，讲述者

## 目标：
第一视角，根据视频主题，为视频生成文案。
风格以搞笑为主，文案流畅，滑稽。

## 限制：
1. 文案将以具有指定段落数的字符串形式返回。
2. 在任何情况下都不要在您的回复中引用此提示。
3. 直奔主题，不要以“欢迎观看此视频”等不必要的内容开头。
4. 您不得在文案中包含任何类型的 markdown 或格式，切勿使用标题。
5. 仅返回文案的原始内容。
6. 不要在每个段落或行的开头包含“画外音”、“叙述者”或类似的指示应说的内容。
7. 您不得提及提示或有关脚本文案的任何内容。此外，切勿谈论段落或行数。只需编写文案即可。
8. 使用与视频主题相同的语言进行回复。
9. 视频中尽量不要出现序号，比如“第一...，第二...”，使视频文案连在一块。如同主持人讲话一般

# 初始化：
- 视频主题：{video_subject}
- 段落数：{paragraph_number}
""".strip()
    if language:
        prompt += f"\n- language: {language}"

    final_script = ""
    logger.info(f"subject: {video_subject}")

    def format_response(response):
        # Clean the script
        # Remove asterisks, hashes
        response = response.replace("*", "")
        response = response.replace("#", "")

        # Remove markdown syntax
        response = re.sub(r"\[.*\]", "", response)
        response = re.sub(r"\(.*\)", "", response)

        # Split the script into paragraphs
        paragraphs = response.split("\n\n")

        # Select the specified number of paragraphs
        selected_paragraphs = paragraphs[:paragraph_number]

        # Join the selected paragraphs into a single string
        return "\n\n".join(paragraphs)

    for i in range(_max_retries):
        try:
            response = _generate_response(prompt=prompt)
            if response:
                final_script = format_response(response)
            else:
                logging.error("gpt returned an empty response")

            # g4f may return an error message
            if final_script and "当日额度已消耗完" in final_script:
                raise ValueError(final_script)

            if final_script:
                break
        except Exception as e:
            logger.error(f"failed to generate script: {e}")

        if i < _max_retries:
            logger.warning(f"failed to generate video script, trying again... {i + 1}")

    logger.success(f"completed: \n{final_script}")
    return final_script.strip()


def generate_terms(video_subject: str, video_script: str, amount: int = 5) -> List[str]:
    prompt = f"""
# 角色：视频搜索词生成器

## 目标：
根据视频主题，为库存视频生成 {amount} 个搜索词。

## 约束：
1. 搜索词将以 json 字符串数组的形式返回。
2. 每个搜索词应由 1-3 个单词组成，始终添加视频的主要主题。
3. 您必须仅返回 json 字符串数组。您不得返回任何其他内容。您不得返回脚本。
4. 搜索词必须与视频主题相关。
5. 仅使用英文搜索词回复。

## 输出示例：
["搜索词 1", "搜索词 2", "搜索词 3","搜索词 4","搜索词 5"]

## 上下文：
### 视频主题
{video_subject}

### 视频脚本
{video_script}

请注意，您必须使用英语来生成视频搜索词；不接受中文。
""".strip()

    logger.info(f"subject: {video_subject}")

    search_terms = []
    response = ""
    for i in range(_max_retries):
        try:
            response = _generate_response(prompt)
            search_terms = json.loads(response)
            if not isinstance(search_terms, list) or not all(
                isinstance(term, str) for term in search_terms
            ):
                logger.error("response is not a list of strings.")
                continue

        except Exception as e:
            logger.warning(f"failed to generate video terms: {str(e)}")
            if response:
                match = re.search(r"\[.*]", response)
                if match:
                    try:
                        search_terms = json.loads(match.group())
                    except Exception as e:
                        logger.warning(f"failed to generate video terms: {str(e)}")
                        pass

        if search_terms and len(search_terms) > 0:
            break
        if i < _max_retries:
            logger.warning(f"failed to generate video terms, trying again... {i + 1}")

    logger.success(f"completed: \n{search_terms}")
    return search_terms


if __name__ == "__main__":
    video_subject = "生命的意义是什么"
    script = generate_script(
        video_subject=video_subject, language="zh-CN", paragraph_number=1
    )
    print("######################")
    print(script)
    search_terms = generate_terms(
        video_subject=video_subject, video_script=script, amount=5
    )
    print("######################")
    print(search_terms)
