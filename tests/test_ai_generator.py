#!/usr/bin/env python3
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass

# Add parent directory and backend directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(parent_dir, 'backend')
sys.path.insert(0, parent_dir)
sys.path.insert(0, backend_dir)

from backend.ai_generator import AIGenerator, SequentialToolTracker, ToolExecutionRound


class MockAnthropicResponse:
    """Mock response object that mimics Anthropic's response structure"""
    
    def __init__(self, content_text=None, content_blocks=None, stop_reason="stop"):
        if content_blocks:
            self.content = content_blocks
        else:
            self.content = [Mock(text=content_text or "Mock response")]
        self.stop_reason = stop_reason


class MockToolUseBlock:
    """Mock tool use content block"""
    
    def __init__(self, name, input_params, tool_id="mock_tool_id"):
        self.type = "tool_use"
        self.name = name
        self.input = input_params
        self.id = tool_id


class TestSequentialToolTracker:
    """Test the SequentialToolTracker class"""
    
    def test_initialization(self):
        """Test tracker initialization with default and custom max rounds"""
        tracker = SequentialToolTracker()
        assert tracker.max_rounds == 2
        assert tracker.current_round == 0
        assert len(tracker.rounds) == 0
        
        tracker_custom = SequentialToolTracker(max_rounds=3)
        assert tracker_custom.max_rounds == 3
    
    def test_can_continue(self):
        """Test can_continue logic"""
        tracker = SequentialToolTracker(max_rounds=2)
        assert tracker.can_continue() is True
        
        # Add one round
        round1 = ToolExecutionRound(1, [], [])
        tracker.add_round(round1)
        assert tracker.current_round == 1
        assert tracker.can_continue() is True
        
        # Add second round
        round2 = ToolExecutionRound(2, [], [])
        tracker.add_round(round2)
        assert tracker.current_round == 2
        assert tracker.can_continue() is False
    
    def test_get_total_tool_calls(self):
        """Test tool call counting"""
        tracker = SequentialToolTracker()
        
        round1 = ToolExecutionRound(1, [{"name": "tool1"}, {"name": "tool2"}], [])
        round2 = ToolExecutionRound(2, [{"name": "tool3"}], [])
        
        tracker.add_round(round1)
        tracker.add_round(round2)
        
        assert tracker.get_total_tool_calls() == 3


class TestAIGenerator:
    """Test the AIGenerator class with sequential tool calling"""
    
    @pytest.fixture
    def ai_generator(self):
        """Create AIGenerator instance for testing"""
        return AIGenerator("test_api_key", "test_model")
    
    @pytest.fixture
    def mock_tool_manager(self):
        """Create mock tool manager"""
        mock_manager = Mock()
        mock_manager.execute_tool.return_value = "Mock tool result"
        return mock_manager
    
    def test_initialization(self, ai_generator):
        """Test AIGenerator initialization"""
        assert ai_generator.model == "test_model"
        assert ai_generator.base_params["model"] == "test_model"
        assert ai_generator.base_params["temperature"] == 0
        assert ai_generator.base_params["max_tokens"] == 800
    
    @patch('backend.ai_generator.anthropic.Anthropic')
    def test_generate_response_no_tools(self, mock_anthropic, ai_generator):
        """Test response generation without tools"""
        # Setup mock
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.return_value = MockAnthropicResponse("Test response")
        ai_generator.client = mock_client
        
        # Test
        response = ai_generator.generate_response("Test query")
        
        # Verify
        assert response == "Test response"
        mock_client.messages.create.assert_called_once()
        call_args = mock_client.messages.create.call_args[1]
        assert "tools" not in call_args
    
    @patch('backend.ai_generator.anthropic.Anthropic')
    def test_generate_response_single_tool_round(self, mock_anthropic, ai_generator, mock_tool_manager):
        """Test single round tool execution"""
        # Setup mock
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        ai_generator.client = mock_client
        
        # Mock tool use response
        tool_block = MockToolUseBlock("search_course_content", {"query": "test"})
        tool_response = MockAnthropicResponse(content_blocks=[tool_block], stop_reason="tool_use")
        
        # Mock final response - need to provide same response for final call
        final_response = MockAnthropicResponse("Final answer based on tool results")
        
        # Configure mock to return tool response first, then final response
        # Note: the implementation makes final call in _get_final_response
        mock_client.messages.create.return_value = final_response
        mock_client.messages.create.side_effect = [tool_response, final_response]
        
        # Test
        response = ai_generator.generate_response(
            "Test query", 
            tools=[{"name": "search_course_content"}],
            tool_manager=mock_tool_manager
        )
        
        # Verify
        assert response == "Final answer based on tool results"
        assert mock_client.messages.create.call_count == 2
        mock_tool_manager.execute_tool.assert_called_once_with("search_course_content", query="test")
    
    @patch('backend.ai_generator.anthropic.Anthropic')
    def test_generate_response_two_tool_rounds(self, mock_anthropic, ai_generator, mock_tool_manager):
        """Test two sequential tool rounds"""
        # Setup mock
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        ai_generator.client = mock_client
        
        # Mock first tool use response
        tool_block1 = MockToolUseBlock("get_course_outline", {"course_name": "Python"}, "tool1")
        tool_response1 = MockAnthropicResponse(content_blocks=[tool_block1], stop_reason="tool_use")
        
        # Mock second tool use response
        tool_block2 = MockToolUseBlock("search_course_content", {"query": "lesson 4"}, "tool2")
        tool_response2 = MockAnthropicResponse(content_blocks=[tool_block2], stop_reason="tool_use")
        
        # Mock final response
        final_response = MockAnthropicResponse("Comparison complete")
        
        # Configure mock responses
        mock_client.messages.create.side_effect = [tool_response1, tool_response2, final_response]
        
        # Test
        response = ai_generator.generate_response(
            "Compare Python lesson 4 with another course",
            tools=[{"name": "get_course_outline"}, {"name": "search_course_content"}],
            tool_manager=mock_tool_manager,
            max_tool_rounds=2
        )
        
        # Verify
        assert response == "Comparison complete"
        assert mock_client.messages.create.call_count == 3
        assert mock_tool_manager.execute_tool.call_count == 2
        
        # Verify tool calls
        calls = mock_tool_manager.execute_tool.call_args_list
        assert calls[0][0] == ("get_course_outline",)
        assert calls[0][1] == {"course_name": "Python"}
        assert calls[1][0] == ("search_course_content",)
        assert calls[1][1] == {"query": "lesson 4"}
    
    @patch('backend.ai_generator.anthropic.Anthropic')
    def test_max_rounds_limit(self, mock_anthropic, ai_generator, mock_tool_manager):
        """Test that execution stops at max rounds"""
        # Setup mock
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        ai_generator.client = mock_client
        
        # Mock tool use responses for multiple rounds
        tool_block = MockToolUseBlock("search_course_content", {"query": "test"})
        tool_response = MockAnthropicResponse(content_blocks=[tool_block], stop_reason="tool_use")
        final_response = MockAnthropicResponse("Final response after max rounds")
        
        # Return tool_use response first, then final response for _get_final_response call
        mock_client.messages.create.side_effect = [tool_response, final_response]
        
        # Test with max_tool_rounds=1
        response = ai_generator.generate_response(
            "Test query",
            tools=[{"name": "search_course_content"}],
            tool_manager=mock_tool_manager,
            max_tool_rounds=1
        )
        
        # Verify only one tool round executed plus final response
        assert response == "Final response after max rounds"
        assert mock_client.messages.create.call_count == 2  # Initial + final
        assert mock_tool_manager.execute_tool.call_count == 1
    
    @patch('backend.ai_generator.anthropic.Anthropic')
    def test_early_termination_no_tools(self, mock_anthropic, ai_generator, mock_tool_manager):
        """Test termination when Claude doesn't use tools"""
        # Setup mock
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        ai_generator.client = mock_client
        
        # Mock first tool use, then no tool use
        tool_block = MockToolUseBlock("search_course_content", {"query": "test"})
        tool_response = MockAnthropicResponse(content_blocks=[tool_block], stop_reason="tool_use")
        no_tool_response = MockAnthropicResponse("Direct answer", stop_reason="stop")
        
        mock_client.messages.create.side_effect = [tool_response, no_tool_response]
        
        # Test
        response = ai_generator.generate_response(
            "Test query",
            tools=[{"name": "search_course_content"}],
            tool_manager=mock_tool_manager,
            max_tool_rounds=2
        )
        
        # Verify early termination
        assert response == "Direct answer"
        assert mock_client.messages.create.call_count == 2
        assert mock_tool_manager.execute_tool.call_count == 1
    
    @patch('backend.ai_generator.anthropic.Anthropic')
    def test_tool_execution_error_handling(self, mock_anthropic, ai_generator, mock_tool_manager):
        """Test handling of tool execution errors"""
        # Setup mock
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        ai_generator.client = mock_client
        
        # Mock tool execution error
        mock_tool_manager.execute_tool.side_effect = Exception("Tool execution failed")
        
        # Mock tool use response
        tool_block = MockToolUseBlock("search_course_content", {"query": "test"})
        tool_response = MockAnthropicResponse(content_blocks=[tool_block], stop_reason="tool_use")
        final_response = MockAnthropicResponse("Error handled gracefully")
        
        mock_client.messages.create.side_effect = [tool_response, final_response]
        
        # Test
        response = ai_generator.generate_response(
            "Test query",
            tools=[{"name": "search_course_content"}],
            tool_manager=mock_tool_manager
        )
        
        # Verify graceful error handling
        assert response == "Error handled gracefully"
        mock_tool_manager.execute_tool.assert_called_once()
    
    @patch('backend.ai_generator.anthropic.Anthropic')
    def test_conversation_history_preservation(self, mock_anthropic, ai_generator, mock_tool_manager):
        """Test that conversation history is preserved throughout tool execution"""
        # Setup mock
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        ai_generator.client = mock_client
        
        # Mock responses
        tool_block = MockToolUseBlock("search_course_content", {"query": "test"})
        tool_response = MockAnthropicResponse(content_blocks=[tool_block], stop_reason="tool_use")
        final_response = MockAnthropicResponse("Final response")
        
        mock_client.messages.create.side_effect = [tool_response, final_response]
        
        # Test with conversation history
        conversation_history = "User: Previous question\nAssistant: Previous answer"
        response = ai_generator.generate_response(
            "New question",
            conversation_history=conversation_history,
            tools=[{"name": "search_course_content"}],
            tool_manager=mock_tool_manager
        )
        
        # Verify conversation history is included in system prompt
        calls = mock_client.messages.create.call_args_list
        for call in calls:
            system_content = call[1]["system"]
            assert "Previous conversation:" in system_content
            assert conversation_history in system_content
    
    def test_execute_tool_round(self, ai_generator, mock_tool_manager):
        """Test _execute_tool_round method"""
        # Create mock response with tool use
        tool_block = MockToolUseBlock("search_course_content", {"query": "test"}, "tool123")
        mock_response = MockAnthropicResponse(content_blocks=[tool_block], stop_reason="tool_use")
        
        # Test
        round_result = ai_generator._execute_tool_round(mock_response, mock_tool_manager, 1)
        
        # Verify
        assert round_result.round_number == 1
        assert len(round_result.tool_calls) == 1
        assert len(round_result.tool_results) == 1
        assert round_result.tool_calls[0]["name"] == "search_course_content"
        assert round_result.tool_calls[0]["input"] == {"query": "test"}
        assert round_result.tool_results[0]["tool_use_id"] == "tool123"
        assert round_result.tool_results[0]["content"] == "Mock tool result"
    
    def test_execute_tool_round_with_error(self, ai_generator, mock_tool_manager):
        """Test _execute_tool_round with tool execution error"""
        # Setup tool manager to raise error
        mock_tool_manager.execute_tool.side_effect = Exception("Tool failed")
        
        # Create mock response with tool use
        tool_block = MockToolUseBlock("search_course_content", {"query": "test"}, "tool123")
        mock_response = MockAnthropicResponse(content_blocks=[tool_block], stop_reason="tool_use")
        
        # Test
        round_result = ai_generator._execute_tool_round(mock_response, mock_tool_manager, 1)
        
        # Verify error handling
        assert round_result.round_number == 1
        assert len(round_result.tool_calls) == 1
        assert len(round_result.tool_results) == 1
        assert "Tool execution error" in round_result.tool_results[0]["content"]
        assert round_result.tool_results[0]["is_error"] is True


class TestIntegration:
    """Integration tests for the complete sequential tool calling flow"""
    
    @patch('backend.ai_generator.anthropic.Anthropic')
    def test_end_to_end_sequential_search(self, mock_anthropic):
        """Test complete sequential search scenario"""
        # This test simulates the real-world scenario described in requirements:
        # "Search for a course that discusses the same topic as lesson 4 of course X"
        
        ai_generator = AIGenerator("test_key", "test_model")
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        ai_generator.client = mock_client
        
        # Mock tool manager
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.side_effect = [
            "Course X has lesson 4: Advanced Python Decorators",  # First tool call result
            "Course Y also covers Advanced Python Decorators in lesson 3"  # Second tool call result
        ]
        
        # Mock API responses
        tool_block1 = MockToolUseBlock("get_course_outline", {"course_name": "Course X"}, "tool1")
        response1 = MockAnthropicResponse(content_blocks=[tool_block1], stop_reason="tool_use")
        
        tool_block2 = MockToolUseBlock("search_course_content", {"query": "Advanced Python Decorators"}, "tool2")
        response2 = MockAnthropicResponse(content_blocks=[tool_block2], stop_reason="tool_use")
        
        final_response = MockAnthropicResponse("Course Y discusses the same topic as lesson 4 of Course X")
        
        mock_client.messages.create.side_effect = [response1, response2, final_response]
        
        # Execute test
        result = ai_generator.generate_response(
            "Search for a course that discusses the same topic as lesson 4 of course X",
            tools=[{"name": "get_course_outline"}, {"name": "search_course_content"}],
            tool_manager=mock_tool_manager,
            max_tool_rounds=2
        )
        
        # Verify
        assert result == "Course Y discusses the same topic as lesson 4 of Course X"
        assert mock_client.messages.create.call_count == 3
        assert mock_tool_manager.execute_tool.call_count == 2
        
        # Verify the sequence of tool calls
        tool_calls = mock_tool_manager.execute_tool.call_args_list
        assert tool_calls[0][0] == ("get_course_outline",)
        assert tool_calls[1][0] == ("search_course_content",)


if __name__ == "__main__":
    pytest.main([__file__])