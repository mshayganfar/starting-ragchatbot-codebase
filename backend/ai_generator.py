from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import anthropic


@dataclass
class ToolExecutionRound:
    """Tracks tool execution for a single round"""

    round_number: int
    tool_calls: List[Dict]
    tool_results: List[Dict]
    ai_response: Optional[str] = None
    error: Optional[str] = None


class SequentialToolTracker:
    """Tracks state across multiple tool execution rounds"""

    def __init__(self, max_rounds: int = 2):
        self.max_rounds = max_rounds
        self.rounds: List[ToolExecutionRound] = []
        self.current_round = 0

    def can_continue(self) -> bool:
        """Check if we can continue to the next round"""
        return self.current_round < self.max_rounds

    def add_round(self, round_data: ToolExecutionRound):
        """Add a completed round to the tracker"""
        self.rounds.append(round_data)
        self.current_round += 1

    def get_total_tool_calls(self) -> int:
        """Get total number of tool calls across all rounds"""
        return sum(len(round.tool_calls) for round in self.rounds)


class AIGenerator:
    """Handles interactions with Anthropic's Claude API for generating responses"""

    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to comprehensive search tools for course information.

Available Tools:
- **search_course_content**: For searching specific course content and educational materials
- **get_course_outline**: For retrieving course structure (title, instructor, course link, and complete lesson list)

Tool Usage Guidelines:
- **Sequential tool usage**: You can make up to 2 rounds of tool calls per user query
- **Round 1**: Make initial tool calls to gather information
- **Round 2**: Make additional tool calls if needed based on initial results to refine or expand search
- **Content questions**: Use search_course_content for questions about specific topics, concepts, or detailed course materials
- **Outline questions**: Use get_course_outline for questions about course structure, lesson lists, or course overview
- **Multi-step queries**: Use first round for broad search, second round for specific follow-up searches
- **Comparison queries**: First search for one item, then search for another to compare
- Synthesize all tool results into accurate, fact-based responses
- If tools yield no results, state this clearly without offering alternatives

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without searching
- **Course-specific questions**: Use appropriate tools, then answer
- **Complex queries**: Use sequential tool calls to gather comprehensive information
- **Outline requests**: Always include course title, course link, and complete lesson breakdown with numbers and titles
- **No meta-commentary**:
 - Provide direct answers only — no reasoning process, search explanations, or question-type analysis
 - Do not mention "based on the search results" or "using the tool"

All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Example-supported** - Include relevant examples when they aid understanding
Provide only the direct answer to what was asked.
"""

    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

        # Pre-build base API parameters
        self.base_params = {"model": self.model, "temperature": 0, "max_tokens": 800}

    def generate_response(
        self,
        query: str,
        conversation_history: Optional[str] = None,
        tools: Optional[List] = None,
        tool_manager=None,
        max_tool_rounds: int = 2,
    ) -> str:
        """
        Generate AI response with optional sequential tool usage and conversation context.

        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools
            max_tool_rounds: Maximum number of sequential tool execution rounds (default: 2)

        Returns:
            Generated response as string
        """

        # Build system content efficiently - avoid string ops when possible
        system_content = (
            f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
            if conversation_history
            else self.SYSTEM_PROMPT
        )

        # Prepare API call parameters efficiently
        api_params = {
            **self.base_params,
            "messages": [{"role": "user", "content": query}],
            "system": system_content,
        }

        # Add tools if available
        if tools:
            api_params["tools"] = tools
            api_params["tool_choice"] = {"type": "auto"}

        # Get response from Claude
        response = self.client.messages.create(**api_params)

        # Handle sequential tool execution if needed
        if response.stop_reason == "tool_use" and tool_manager:
            return self._handle_tool_execution(
                response, api_params, tool_manager, max_tool_rounds
            )

        # Return direct response
        return response.content[0].text

    def _handle_tool_execution(
        self,
        initial_response,
        base_params: Dict[str, Any],
        tool_manager,
        max_rounds: int = 2,
    ):
        """
        Handle sequential execution of tool calls across multiple rounds.

        Args:
            initial_response: The response containing tool use requests
            base_params: Base API parameters
            tool_manager: Manager to execute tools
            max_rounds: Maximum number of tool execution rounds

        Returns:
            Final response text after tool execution
        """
        # Initialize tracking
        tracker = SequentialToolTracker(max_rounds)
        messages = base_params["messages"].copy()
        current_response = initial_response

        # Process sequential tool rounds
        while tracker.can_continue() and current_response.stop_reason == "tool_use":
            try:
                # Execute current round
                round_result = self._execute_tool_round(
                    current_response, tool_manager, tracker.current_round + 1
                )
                tracker.add_round(round_result)

                # Update messages with AI response and tool results
                messages.append(
                    {"role": "assistant", "content": current_response.content}
                )
                if round_result.tool_results:
                    messages.append(
                        {"role": "user", "content": round_result.tool_results}
                    )

                # Check if we can continue to next round
                if tracker.can_continue():
                    # Get next response with tools available
                    next_params = {
                        **self.base_params,
                        "messages": messages,
                        "system": base_params["system"],
                        "tools": base_params.get("tools", []),
                        "tool_choice": {"type": "auto"},
                    }
                    current_response = self.client.messages.create(**next_params)
                else:
                    # Max rounds reached, break and get final response
                    current_response = None
                    break

            except Exception as e:
                # Handle tool execution errors
                error_round = ToolExecutionRound(
                    round_number=tracker.current_round + 1,
                    tool_calls=[],
                    tool_results=[],
                    error=str(e),
                )
                tracker.add_round(error_round)
                break

        # Get final response
        if current_response and current_response.stop_reason != "tool_use":
            # Claude provided a final response without tools
            return current_response.content[0].text
        else:
            # Need to get final response without tools
            final_response = self._get_final_response(messages, base_params)
            return final_response

    def _execute_tool_round(
        self, response, tool_manager, round_number: int
    ) -> ToolExecutionRound:
        """Execute all tool calls in a single round."""

        tool_calls = []
        tool_results = []

        for content_block in response.content:
            if content_block.type == "tool_use":
                tool_calls.append(
                    {
                        "name": content_block.name,
                        "input": content_block.input,
                        "id": content_block.id,
                    }
                )

                try:
                    tool_result = tool_manager.execute_tool(
                        content_block.name, **content_block.input
                    )

                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": tool_result,
                        }
                    )

                except Exception as e:
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": f"Tool execution error: {str(e)}",
                            "is_error": True,
                        }
                    )

        return ToolExecutionRound(
            round_number=round_number, tool_calls=tool_calls, tool_results=tool_results
        )

    def _get_final_response(
        self, messages: List[Dict], base_params: Dict[str, Any]
    ) -> str:
        """Get final response without tools."""

        final_params = {
            **self.base_params,
            "messages": messages,
            "system": base_params["system"],
            # Note: no tools parameter for final call
        }

        final_response = self.client.messages.create(**final_params)
        return final_response.content[0].text
