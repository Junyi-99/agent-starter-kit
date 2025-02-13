def parse_tag(tag: str, llm_response: str) -> str:
    """
    Parse the tag in LLM's response.

    For example, if `tag` is "REASONING", it will return the text between "<REASONING>" and "</REASONING>".
    """
    pos1 = llm_response.find(f"<{tag}>")
    pos2 = llm_response.find(f"</{tag}>", pos1)
    left = pos1 + len(tag) + 2
    return llm_response[left:pos2]
