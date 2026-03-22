"""패치: Claude 요약 프롬프트를 구조화된 마크다운으로 변경"""

filepath = "/home/webapp/goldenrabbit/chat_stt/server/claude_service.py"

with open(filepath, "r") as f:
    content = f.read()

# 1) remove_markdown 함수 호출 제거
content = content.replace(
    """        # 마크다운 형식이 있으면 제거
        summary = remove_markdown(summary)""",
    "        # 마크다운 형식 유지 (Flutter에서 렌더링)"
)

# 2) 한국어 프롬프트 변경
old_prompt = '''        if language == 'ko':
            prompt = f"""다음은 전화 통화 녹음을 텍스트로 변환한 내용입니다.
핵심 내용만 간결하게 3-5줄로 요약해주세요.

중요: 마크다운 형식(**, ##, - 등)을 사용하지 마세요. 일반 텍스트로만 작성하세요.

[통화 내용]
{text}

[요약]"""'''

new_prompt = '''        if language == 'ko':
            prompt = f"""다음은 전화 통화 녹음을 텍스트로 변환한 내용입니다.
아래 형식에 맞춰 간결하게 요약해주세요.

### 형식 규칙
- 마크다운 형식을 사용하세요
- 각 항목은 **볼드** 키워드 + 설명 형태로
- 불필요한 인사말/반복 제거
- 핵심만 3~5개 bullet으로

### 출력 형식 예시
**주제**: 한 줄 요약

- **핵심1**: 내용
- **핵심2**: 내용
- **핵심3**: 내용

**결론**: 최종 합의/결과 (있는 경우)

[통화 내용]
{text}"""'''

content = content.replace(old_prompt, new_prompt)

# 3) 영어 프롬프트도 변경
old_en = '''        else:
            prompt = f"""The following is a phone call recording converted to text.
Please summarize the key points in 3-5 lines.

Important: Do not use markdown formatting (**, ##, - etc). Use plain text only.

[Call Content]
{text}

[Summary]"""'''

new_en = '''        else:
            prompt = f"""The following is a phone call recording converted to text.
Summarize concisely using markdown format:

- Use **bold** keywords + description
- 3-5 bullet points max
- Include a one-line **Topic** and **Conclusion** if applicable

[Call Content]
{text}"""'''

content = content.replace(old_en, new_en)

with open(filepath, "w") as f:
    f.write(content)

print("OK - claude_service.py: markdown prompt updated")
