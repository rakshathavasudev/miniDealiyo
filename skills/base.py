"""
Dealyo Skills — Base Class
All skills inherit from this. Handles versioning, logging, retries,
and enforces a consistent interface across every Claude-powered skill.
"""

import os
import json
import time
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
import anthropic
from dotenv import load_dotenv
load_dotenv()

log = logging.getLogger("dealyo.skills")

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

DEFAULT_MODEL = "claude-sonnet-4-20250514"


@dataclass
class SkillResult:
    """Wrapper returned by every skill call."""
    skill_name: str
    skill_version: str
    success: bool
    data: dict = field(default_factory=dict)
    error: str = ""
    latency_ms: int = 0
    input_tokens: int = 0
    output_tokens: int = 0

    def __str__(self):
        if self.success:
            return f"[{self.skill_name} v{self.skill_version}] OK ({self.latency_ms}ms)"
        return f"[{self.skill_name} v{self.skill_version}] FAILED: {self.error}"


class BaseSkill(ABC):
    """
    Base class for all Dealyo Claude skills.

    A skill is a versioned, testable, single-responsibility prompt module.
    Each skill owns exactly one Claude call and returns a typed SkillResult.

    To create a new skill:
        1. Subclass BaseSkill
        2. Set name, version, system_prompt
        3. Implement build_prompt(inputs) -> str
        4. Implement parse_response(raw) -> dict
    """

    name: str = "base"
    version: str = "1.0"
    model: str = DEFAULT_MODEL
    max_tokens: int = 1024
    max_retries: int = 2

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """The system prompt for this skill. Define in subclass."""
        ...

    @abstractmethod
    def build_prompt(self, inputs: dict) -> str:
        """Build the user-turn prompt from inputs. Define in subclass."""
        ...

    @abstractmethod
    def parse_response(self, raw: str) -> dict:
        """Parse Claude's raw text response into a typed dict. Define in subclass."""
        ...

    def run(self, inputs: dict) -> SkillResult:
        """
        Execute the skill. Handles retries, timing, token tracking.
        Call this from your API endpoints — never call Claude directly.
        """
        start = time.time()
        prompt = self.build_prompt(inputs)
        last_error = ""

        for attempt in range(self.max_retries + 1):
            try:
                message = client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    system=self.system_prompt,
                    messages=[{"role": "user", "content": prompt}],
                )
                raw = message.content[0].text.strip()
                parsed = self.parse_response(raw)
                latency = int((time.time() - start) * 1000)

                log.info(f"[{self.name} v{self.version}] OK — {latency}ms | "
                         f"in={message.usage.input_tokens} out={message.usage.output_tokens}")

                return SkillResult(
                    skill_name=self.name,
                    skill_version=self.version,
                    success=True,
                    data=parsed,
                    latency_ms=latency,
                    input_tokens=message.usage.input_tokens,
                    output_tokens=message.usage.output_tokens,
                )

            except Exception as e:
                last_error = str(e)
                log.warning(f"[{self.name}] attempt {attempt+1} failed: {e}")
                if attempt < self.max_retries:
                    time.sleep(1.5 ** attempt)

        return SkillResult(
            skill_name=self.name,
            skill_version=self.version,
            success=False,
            error=last_error,
            latency_ms=int((time.time() - start) * 1000),
        )

    @staticmethod
    def clean_json(raw: str) -> str:
        """Strip markdown fences from Claude's response before JSON parsing."""
        return re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()

    def __repr__(self):
        return f"<Skill: {self.name} v{self.version}>"
