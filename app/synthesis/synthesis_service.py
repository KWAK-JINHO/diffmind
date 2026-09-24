# app/synthesis/synthesis_service.py
import difflib
import json
import logging
import os
import re
import tempfile
from pathlib import Path
from typing import Optional

from app.config import Settings, get_settings, validate_safe_path
from app.schemas.patch import PatchProposal, LLMDecision
from app.synthesis.scanner import scan_knowledge_base, get_file_content

logger = logging.getLogger(__name__)

SYNTHESIS_SYSTEM_PROMPT = """
당신은 마크다운 지식 베이스의 아키텍트이자 수석 테크니컬 라이터입니다.
사용자가 새로 학습한 마크다운 지식을 기존 지식 베이스의 구조(TOC)와 비교 분석하여,
가장 최적의 파일과 헤딩 위치에 지능적으로 병합하는 구조화 결정을 내려야 합니다.

[기존 지식 베이스 목차 맵 (TOC)]
{toc_json}

[새로 병합할 지식 내용]
{content}

[판단 규칙]
1. 기존 지식 베이스의 파일 및 헤딩 중 의미상/문맥상 가장 적합한 위치가 있다면 기존 파일 수정을 제안하세요 (is_new_file = false).
2. 기존 파일에 전혀 어울리지 않거나 지식 베이스가 비어있는 경우, 논리적인 디렉터리와 파일명(예: devops/docker-volume.md)으로 새 파일 생성을 제안하세요 (is_new_file = true).
3. target_heading: 해당 내용이 위치할 헤딩 (예: '## cgroups v2 리소스 격리'). 기존 헤딩이거나 새로 추가할 헤딩이어야 합니다.
4. original_snippet: 기존 내용 중 특정 단락을 수정/대체해야 하는 경우 해당 앵커 텍스트를 정확히 지정하세요. 새 파일이거나 섹션 끝에 추가하는 경우 반드시 빈 문자열("")로 지정하세요.
5. proposed_snippet: 실제 문서에 반영될 완성형 마크다운 문단입니다. 누락 없이 완전한 마크다운으로 작성하세요.
6. reason: 왜 이 파일과 헤딩을 선택했는지에 대한 전문적이고 논리적인 분석 근거를 작성하세요.
""".strip()


class SynthesisService:
    """
    Intelligent knowledge synthesis, unified diff calculation, and atomic patch application.
    """

    def __init__(self, kb_path: Optional[Path] = None, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.kb_path = (kb_path or self.settings.resolved_kb_path).resolve()

    def compute_modified_content(
        self,
        original_content: str,
        is_new_file: bool,
        target_heading: str,
        original_snippet: str,
        proposed_snippet: str
    ) -> str:
        """
        Computes the target file content after applying the proposed patch snippet.
        Handles replacement, heading insertion, and new file initialization.
        """
        clean_original = original_content.strip()

        # Case 1: New file creation or empty original content
        if is_new_file or not clean_original:
            proposed_clean = proposed_snippet.strip()
            heading_clean = target_heading.strip()
            # Avoid repeating heading if snippet already starts with it
            if heading_clean and not proposed_clean.startswith("#"):
                return f"{heading_clean}\n\n{proposed_clean}\n"
            return f"{proposed_clean}\n"

        # Case 2: Exact snippet replacement
        if original_snippet and original_snippet.strip() in original_content:
            return original_content.replace(
                original_snippet.strip(),
                proposed_snippet.strip(),
                1
            )

        # Case 3: Insertion under target_heading
        lines = original_content.splitlines()
        target_idx = -1
        heading_clean = target_heading.strip().lower()

        for idx, line in enumerate(lines):
            if line.strip().lower() == heading_clean:
                target_idx = idx
                break

        if target_idx == -1:
            # Heading not found in existing document; append heading and content to the end
            return original_content.rstrip() + f"\n\n{target_heading.strip()}\n\n{proposed_snippet.strip()}\n"

        # Determine level of target heading (e.g. ## -> level 2)
        match = re.match(r"^(#+)", lines[target_idx].strip())
        target_level = len(match.group(1)) if match else 1

        # Avoid repeating the target heading if snippet already starts with it
        snippet_to_insert = proposed_snippet.strip()
        if snippet_to_insert.lower().startswith(target_heading.strip().lower()):
            snippet_to_insert = snippet_to_insert[len(target_heading.strip()):].lstrip()

        # Locate boundary of current section (next heading with level <= target_level, or EOF)
        insert_idx = len(lines)
        for idx in range(target_idx + 1, len(lines)):
            line_str = lines[idx].strip()
            m_curr = re.match(r"^(#+)\s+", line_str)
            if m_curr:
                curr_level = len(m_curr.group(1))
                if curr_level <= target_level:
                    insert_idx = idx
                    break

        new_lines = (
            lines[:insert_idx]
            + ["", snippet_to_insert, ""]
            + lines[insert_idx:]
        )
        combined = "\n".join(new_lines).strip() + "\n"
        # Normalize triple+ blank lines into clean double blank lines
        return re.sub(r"\n{3,}", "\n\n", combined)

    def generate_unified_diff(
        self,
        rel_path: str,
        original_content: str,
        modified_content: str,
        is_new_file: bool
    ) -> str:
        """
        Generates standard Git Unified Diff using Python standard library difflib.
        """
        from_file = "/dev/null" if is_new_file else f"a/{rel_path}"
        to_file = f"b/{rel_path}"

        orig_lines = original_content.splitlines() if original_content else []
        mod_lines = modified_content.splitlines() if modified_content else []

        diff_lines = list(difflib.unified_diff(
            orig_lines,
            mod_lines,
            fromfile=from_file,
            tofile=to_file,
            lineterm=""
        ))
        return "\n".join(diff_lines)

    async def decide_patch_with_llm(
        self,
        content: str,
        toc_map: dict[str, list[str]]
    ) -> LLMDecision:
        """
        Invokes LLM to analyze content against knowledge base TOC and return structured decision.
        Falls back to intelligent heuristic if no API key is provided.
        """
        provider = self.settings.LLM_PROVIDER.lower()
        has_gemini = bool(self.settings.GEMINI_API_KEY)
        has_openai = bool(self.settings.OPENAI_API_KEY)

        if not has_gemini and not has_openai:
            logger.info("No LLM API key detected; employing heuristic decision engine.")
            return self._heuristic_decision(content, toc_map)

        toc_json = json.dumps(toc_map, ensure_ascii=False, indent=2)
        prompt = SYNTHESIS_SYSTEM_PROMPT.format(toc_json=toc_json, content=content)

        if (provider == "google" and has_gemini) or (not has_openai and has_gemini):
            return await self._call_gemini_structured(prompt)
        elif (provider == "openai" and has_openai) or has_openai:
            return await self._call_openai_structured(prompt)
        else:
            return self._heuristic_decision(content, toc_map)

    async def _call_gemini_structured(self, prompt: str) -> LLMDecision:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=self.settings.GEMINI_MODEL,
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=LLMDecision,
                temperature=0.1,
            ),
        )
        return LLMDecision.model_validate_json(response.text)

    async def _call_openai_structured(self, prompt: str) -> LLMDecision:
        import openai

        client = openai.OpenAI(api_key=self.settings.OPENAI_API_KEY)
        response = client.beta.chat.completions.parse(
            model=self.settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format=LLMDecision,
            temperature=0.1,
        )
        parsed = response.choices[0].message.parsed
        if not parsed:
            raise ValueError("Failed to parse structured output from OpenAI.")
        return parsed

    def _heuristic_decision(self, content: str, toc_map: dict[str, list[str]]) -> LLMDecision:
        """
        Deterministic, offline heuristic fallback when LLM API keys are not supplied.
        Ensures tests and offline operation function flawlessly.
        """
        # Extract title from content if present
        first_heading_match = re.search(r"^(#{1,3})\s+(.+)$", content, re.MULTILINE)
        content_heading = first_heading_match.group(0) if first_heading_match else "# Notes"
        heading_title = first_heading_match.group(2).strip() if first_heading_match else "Notes"

        if not toc_map:
            # KB is empty -> propose new file
            slug = re.sub(r"[^a-zA-Z0-9_\-\uac00-\ud7a3]+", "_", heading_title.lower()).strip("_")
            target_path = f"{slug or 'note'}.md"
            return LLMDecision(
                is_new_file=True,
                target_file_path=target_path,
                target_heading=content_heading,
                original_snippet="",
                proposed_snippet=content,
                reason="Knowledge base is currently empty. Proposing initial root markdown file."
            )

        STOPWORDS = {
            "systems", "system", "the", "and", "in", "of", "to", "a", "is", "for",
            "on", "with", "as", "by", "an", "at", "or", "from", "overview", "guide",
            "notes", "md", "details"
        }
        content_words = {
            w for w in re.findall(r"\w+", content.lower())
            if w not in STOPWORDS and len(w) > 2
        }
        best_file: Optional[str] = None
        best_heading: Optional[str] = None
        best_score = 0

        for file_path, headings in toc_map.items():
            file_words = {
                w for w in re.findall(r"\w+", file_path.lower())
                if w not in STOPWORDS and len(w) > 2
            }
            overlap = len(content_words & file_words) * 3
            if overlap > best_score:
                best_score = overlap
                best_file = file_path
                best_heading = headings[0] if headings else "# " + Path(file_path).stem

            for h in headings:
                h_words = {
                    w for w in re.findall(r"\w+", h.lower())
                    if w not in STOPWORDS and len(w) > 2
                }
                h_overlap = len(content_words & h_words) * 2
                if h_overlap > best_score:
                    best_score = h_overlap
                    best_file = file_path
                    best_heading = h

        # Require a meaningful match score of at least 4 (e.g. 2 heading words or 1 strong file word + 1 heading word)
        if best_file and best_score >= 4:
            return LLMDecision(
                is_new_file=False,
                target_file_path=best_file,
                target_heading=best_heading or "## Details",
                original_snippet="",
                proposed_snippet=content,
                reason=f"Found high topical relevance with existing file '{best_file}' under heading '{best_heading}'."
            )

        # No sufficient match found -> propose new file
        slug = re.sub(r"[^a-zA-Z0-9_\-\uac00-\ud7a3]+", "_", heading_title.lower()).strip("_")
        return LLMDecision(
            is_new_file=True,
            target_file_path=f"topics/{slug or 'new_topic'}.md",
            target_heading=content_heading,
            original_snippet="",
            proposed_snippet=content,
            reason="Content introduces a distinct topic that does not match existing headings."
        )

    async def propose_patch(self, content: str) -> PatchProposal:
        """
        High-level pipeline:
        1. Scan current KB TOC
        2. Solicit LLM (or heuristic) decision
        3. Read original file content
        4. Compute modified content
        5. Generate difflib Unified Diff
        6. Return PatchProposal
        """
        clean_content = content.strip()
        if not clean_content:
            raise ValueError("Input knowledge content is empty.")

        toc_map = scan_knowledge_base(self.kb_path)
        decision = await self.decide_patch_with_llm(clean_content, toc_map)

        # Validate target file path security
        validate_safe_path(decision.target_file_path, self.kb_path)

        original_content = ""
        if not decision.is_new_file:
            existing = get_file_content(self.kb_path, decision.target_file_path)
            if existing is not None:
                original_content = existing
            else:
                # If target was marked existing but doesn't exist, treat as new file
                decision.is_new_file = True

        modified_content = self.compute_modified_content(
            original_content=original_content,
            is_new_file=decision.is_new_file,
            target_heading=decision.target_heading,
            original_snippet=decision.original_snippet,
            proposed_snippet=decision.proposed_snippet
        )

        unified_diff = self.generate_unified_diff(
            rel_path=decision.target_file_path,
            original_content=original_content,
            modified_content=modified_content,
            is_new_file=decision.is_new_file
        )

        return PatchProposal(
            is_new_file=decision.is_new_file,
            target_file_path=decision.target_file_path,
            target_heading=decision.target_heading,
            original_snippet=decision.original_snippet,
            proposed_snippet=decision.proposed_snippet,
            unified_diff=unified_diff,
            reason=decision.reason
        )

    def apply_patch(self, proposal: PatchProposal) -> Path:
        """
        Safely applies patch to target file with atomic replacement:
        1. Validates path security against Path Traversal.
        2. Computes modified content.
        3. Writes to a NamedTemporaryFile in the SAME directory.
        4. Flushes and fsyncs to disk.
        5. Performs atomic os.replace onto target file.
        """
        safe_path = validate_safe_path(proposal.target_file_path, self.kb_path)
        safe_path.parent.mkdir(parents=True, exist_ok=True)

        original_content = ""
        if safe_path.is_file():
            original_content = safe_path.read_text(encoding="utf-8", errors="replace")

        new_content = self.compute_modified_content(
            original_content=original_content,
            is_new_file=proposal.is_new_file,
            target_heading=proposal.target_heading,
            original_snippet=proposal.original_snippet,
            proposed_snippet=proposal.proposed_snippet
        )

        # Atomic replacement pattern in the same directory
        temp_file = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(safe_path.parent),
            delete=False
        )
        temp_path = Path(temp_file.name)

        try:
            temp_file.write(new_content)
            temp_file.flush()
            os.fsync(temp_file.fileno())
            temp_file.close()
            os.replace(temp_path, safe_path)
        except Exception:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            raise

        return safe_path
