"""
Prompt handlers for NAVMED 6470/13 MCP server.

This module handles all prompt operations for radiation medical examinations.
"""

from typing import Dict, List, Optional
import logging

from mcp import types

logger = logging.getLogger(__name__)

class PromptHandlers:
    """Handles all MCP prompt operations for the NAVMED server."""
    
    def __init__(self, notes: Dict[str, str]):
        """Initialize with required dependencies."""
        self.notes = notes
    
    async def list_prompts(self) -> List[types.Prompt]:
        """
        List available prompts.
        Each prompt can have optional arguments to customize its behavior.
        """
        return [
            types.Prompt(
                name="summarize-notes",
                description="Creates a summary of all notes",
                arguments=[
                    types.PromptArgument(
                        name="style",
                        description="Style of the summary (brief/detailed)",
                        required=False,
                    )
                ],
            ),
            types.Prompt(
                name="explain-procedure",
                description="Explain a radiation medical exam procedure from the documentation",
                arguments=[
                    types.PromptArgument(
                        name="procedure",
                        description="Name of the procedure to explain",
                        required=True,
                    )
                ],
            ),
            types.Prompt(
                name="create-exam-template",
                description="Create a template for a radiation medical examination",
                arguments=[
                    types.PromptArgument(
                        name="exam_type",
                        description="Type of examination (PE, RE, SE, TE)",
                        required=True,
                    )
                ],
            ),
            types.Prompt(
                name="review-examination",
                description="Review a completed examination for compliance with NAVMED 6470/13",
                arguments=[
                    types.PromptArgument(
                        name="exam_id",
                        description="Examination ID to review",
                        required=True,
                    ),
                    types.PromptArgument(
                        name="review_type",
                        description="Type of review (medical/administrative/complete)",
                        required=False,
                    )
                ],
            )
        ]
    
    async def get_prompt(
        self, name: str, arguments: Optional[Dict[str, str]]
    ) -> types.GetPromptResult:
        """
        Generate a prompt by combining arguments with server state.
        The prompt includes all current notes and can be customized via arguments.
        """
        if name == "summarize-notes":
            style = (arguments or {}).get("style", "brief")
            detail_prompt = " Give extensive details." if style == "detailed" else ""

            return types.GetPromptResult(
                description="Summarize the current notes",
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text",
                            text=f"Here are the current notes to summarize:{detail_prompt}\n\n"
                            + "\n".join(
                                f"- {name}: {content}"
                                for name, content in self.notes.items()
                            ),
                        ),
                    )
                ],
            )
        
        elif name == "explain-procedure":
            procedure = (arguments or {}).get("procedure", "")
            if not procedure:
                raise ValueError("Procedure name is required")

            return types.GetPromptResult(
                description=f"Explain the {procedure} radiation medical exam procedure",
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text",
                            text=f"Based on the radiation medical exam documentation available as resources, please explain the {procedure} procedure in detail. Include any relevant safety protocols, equipment requirements, and step-by-step instructions.",
                        ),
                    )
                ],
            )
        
        elif name == "create-exam-template":
            exam_type = (arguments or {}).get("exam_type", "")
            if not exam_type:
                raise ValueError("Exam type is required")
            
            if exam_type not in ["PE", "RE", "SE", "TE"]:
                raise ValueError("Exam type must be PE (Physical), RE (Re-examination), SE (Special), or TE (Termination)")

            exam_type_descriptions = {
                "PE": "Physical Examination - Initial examination for radiation workers",
                "RE": "Re-examination - Periodic follow-up examination",
                "SE": "Special Examination - Examination due to specific concerns or incidents",
                "TE": "Termination Examination - Final examination when leaving radiation work"
            }

            return types.GetPromptResult(
                description=f"Create a template for {exam_type_descriptions[exam_type]}",
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text",
                            text=f"Create a comprehensive NAVMED 6470/13 examination template for a {exam_type_descriptions[exam_type]}. Include all required sections, fields, and provide guidance on completing each section according to radiation medical examination standards. Format the template as a structured document that can be used by medical personnel.",
                        ),
                    )
                ],
            )
        
        elif name == "review-examination":
            exam_id = (arguments or {}).get("exam_id", "")
            review_type = (arguments or {}).get("review_type", "complete")
            
            if not exam_id:
                raise ValueError("Examination ID is required")
            
            review_focus = {
                "medical": "Focus on medical findings, assessments, and clinical compliance",
                "administrative": "Focus on documentation completeness, signatures, and procedural compliance",
                "complete": "Comprehensive review of both medical and administrative aspects"
            }.get(review_type, "Comprehensive review of both medical and administrative aspects")

            return types.GetPromptResult(
                description=f"Review examination {exam_id} for NAVMED 6470/13 compliance",
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text",
                            text=f"Please review examination ID {exam_id} for compliance with NAVMED 6470/13 requirements. {review_focus}. First retrieve the complete examination data, then provide a detailed review including:\n\n"
                                 f"1. Completeness assessment - Are all required fields filled?\n"
                                 f"2. Data validation - Are values within expected ranges and formats?\n"
                                 f"3. Medical assessment - Are findings properly documented and categorized?\n"
                                 f"4. Compliance check - Does the examination meet NAVMED 6470/13 standards?\n"
                                 f"5. Recommendations - Any actions needed for completion or correction?\n\n"
                                 f"Use the get-complete-exam tool to retrieve the examination data first.",
                        ),
                    )
                ],
            )
        
        else:
            raise ValueError(f"Unknown prompt: {name}") 