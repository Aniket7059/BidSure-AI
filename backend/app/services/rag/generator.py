from google import genai

from app.core.config import settings
from app.services.rag.generator_schema import (
    RequirementExtractionResponse,
)


class RequirementGenerator:
    """
    Uses Gemini to extract structured tender requirements
    from retrieved tender-document context.

    The model provides decision-support information only.
    It does not make the final bidder qualification decision.
    """

    SYSTEM_INSTRUCTION = """
You are the tender requirement extraction component
of BidSure AI.

Your task is to identify procurement requirements from
the supplied tender-document context.

Rules:

1. Extract only requirements directly supported by the
   supplied tender context.

2. Never invent a requirement.

3. Preserve the meaning of the original tender clause.

4. Determine whether a requirement is mandatory based on
   the wording of the tender.

5. Use an appropriate canonical requirement_type:
   GST, UDYAM, PAN, INCOME_TAX, EPFO, ESIC,
   STARTUP_INDIA, NSIC, OEM_AUTHORIZATION, MAKE_IN_INDIA,
   MCA21, DIGILOCKER, DEBARMENT, or OTHER.

6. Create validation_config only when the tender provides
   information that can actually be used for validation.

7. Preserve the source document and source chunk IDs.

8. If the context does not provide enough evidence for a
   requirement, do not invent missing details.

9. This output is decision-support data.
   Do not make a final qualification or disqualification
   decision for any bidder.
"""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ):
        self.api_key = (
            api_key
            if api_key is not None
            else settings.GEMINI_API_KEY
        )

        self.model = (
            model
            if model is not None
            else settings.GEMINI_MODEL
        )

        self.client = None

        if self.api_key:
            self.client = genai.Client(
                api_key=self.api_key,
            )

    def generate_requirements(
        self,
        query: str,
        retrieved_context: list[dict],
    ) -> RequirementExtractionResponse:

        if not query or not query.strip():
            raise ValueError(
                "Query cannot be empty."
            )

        if not retrieved_context:
            raise ValueError(
                "Retrieved context cannot be empty."
            )

        if self.client is None:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured."
            )

        context_parts: list[str] = []

        for index, item in enumerate(
            retrieved_context,
            start=1,
        ):
            context_parts.append(
                (
                    f"[CONTEXT {index}]\n"
                    f"Source document: "
                    f"{item.get('source_document', 'unknown')}\n"
                    f"Chunk ID: "
                    f"{item.get('chunk_id', 'unknown')}\n"
                    f"Chunk text:\n"
                    f"{item.get('text', '')}"
                )
            )

        context = "\n\n".join(context_parts)

        prompt = f"""
Identify all tender requirements relevant to
the following query.

QUERY:
{query}

RETRIEVED TENDER CONTEXT:
{context}

Return only requirements that are supported by the
retrieved context.
"""

        interaction = self.client.interactions.create(
            model=self.model,
            input=(
                f"{self.SYSTEM_INSTRUCTION}\n\n"
                f"{prompt}"
            ),
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": (
                    RequirementExtractionResponse
                    .model_json_schema()
                ),
            },
        )

        output_text = interaction.output_text

        if not output_text:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        return (
            RequirementExtractionResponse
            .model_validate_json(output_text)
        )


requirement_generator = RequirementGenerator()