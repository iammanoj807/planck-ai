from typing import Dict, Any

def thinking_tool(thought: str = '', commentary: str = '', **kwargs) -> str:
    """
    Log a thinking step or plan. Returns acknowledgment.
    The content of this tool call will be visible to the user as a part of the reasoning process.
    """
    text = thought or commentary or (list(kwargs.values())[0] if kwargs else '')
    return f'Thought logged: {text[:100]}'

THINKING_TOOL_DEF = {
    'name': 'thinking',
    'description': 'Call this tool FIRST to explain your plan, hypothesis, or reasoning process before taking any action.',
    'parameters': {
        'type': 'object',
        'properties': {
            'thought': {
                'type': 'string',
                'description': 'The detailed reasoning, plan, or analysis of the user\'s request.'
            }
        }
    }
}
