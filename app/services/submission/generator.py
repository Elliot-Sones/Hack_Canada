import structlog

from app.ai.base import AIProvider
from app.services.submission.templates import DOCUMENT_TEMPLATES

logger = structlog.get_logger()


class SubmissionPackageGenerator:
    """Generates a complete government submission package from pipeline results.

    Takes the results from each pipeline stage (parcel data, policy stack,
    massing, layout, finance, entitlement, precedents) and generates
    professional submission documents using AI + structured templates.
    """

    def __init__(self, ai_provider: AIProvider):
        self.ai = ai_provider

    async def generate_document(self, doc_type: str, context: dict) -> dict:
        """Generate a single submission document.

        Args:
            doc_type: Type of document (planning_rationale, compliance_matrix, etc.)
            context: Pipeline results and parameters

        Returns:
            dict with 'content_text', 'content_json', and 'metadata'
        """
        template = DOCUMENT_TEMPLATES.get(doc_type)
        if not template:
            raise ValueError(f"Unknown document type: {doc_type}")

        logger.info("submission.generating", doc_type=doc_type)

        system_prompt = template["system_prompt"]
        user_prompt = template["user_prompt_template"].format(**self._safe_format(context))

        response = await self.ai.generate(
            prompt=user_prompt,
            system=system_prompt,
            max_tokens=template.get("max_tokens", 4096),
        )

        # For structured documents, also generate JSON
        content_json = None
        if template.get("structured_output"):
            try:
                content_json = await self.ai.generate_structured(
                    prompt=f"Convert this document into structured JSON:\n\n{response.content}",
                    schema=template["structured_output"],
                    system="Extract the key data points into the provided JSON schema.",
                )
            except Exception as e:
                logger.warning("submission.json_extraction_failed", doc_type=doc_type, error=str(e))

        return {
            "content_text": response.content,
            "content_json": content_json,
            "metadata": {
                "ai_provider": "configured",
                "ai_model": response.model,
                "input_tokens": response.usage.get("input_tokens", 0),
                "output_tokens": response.usage.get("output_tokens", 0),
            },
        }

    async def generate_full_package(self, context: dict) -> list[dict]:
        """Generate all submission documents for a development plan.

        Args:
            context: Complete pipeline results

        Returns:
            List of document dicts with doc_type, content_text, content_json
        """
        documents = []
        for doc_type in DOCUMENT_TEMPLATES:
            try:
                result = await self.generate_document(doc_type, context)
                documents.append({"doc_type": doc_type, **result})
            except Exception as e:
                logger.error("submission.document_failed", doc_type=doc_type, error=str(e))
                documents.append({
                    "doc_type": doc_type,
                    "content_text": f"Error generating {doc_type}: {e}",
                    "content_json": None,
                    "metadata": {"error": str(e)},
                })
        return documents

    @staticmethod
    def _safe_format(context: dict) -> dict:
        """Return a defaultdict-like mapping that returns placeholder for missing keys."""
        class SafeDict(dict):
            def __missing__(self, key):
                return f"[{key} — data pending]"
        return SafeDict(context)
