import re

from docutils import nodes
from myst_parser.parsers.sphinx_ import MystParser


class GoogleStyleDocstringParser(MystParser):
    def parse(self, inputstring: str, document: nodes.document) -> None:
        parsed_content = self._parse_google_style_docstring(inputstring)
        return super().parse(parsed_content, document)

    def _parse_google_style_docstring(self, docstring: str) -> str:
        description, params, returns, raises, examples = self._extract_sections(docstring)
        myst_docstring = description + "\n\n"

        if params:
            myst_docstring += "```{eval-rst}\n"
            for param in params:
                myst_docstring += f":param {param[0]}: {param[1]}\n"
            myst_docstring += "```\n\n"

        if returns:
            myst_docstring += "```{eval-rst}\n"
            myst_docstring += f":returns: {returns[0]}\n"
            myst_docstring += "```\n\n"

        if raises:
            myst_docstring += "```{eval-rst}\n"
            for exc in raises:
                myst_docstring += f":raises {exc[0]}: {exc[1]}\n"
            myst_docstring += "```\n\n"

        if examples:
            myst_docstring += "**Examples**\n"
            myst_docstring += "```\n"
            myst_docstring += examples
            myst_docstring += "\n```\n\n"

        return myst_docstring.strip()

    def _extract_sections(self, docstring: str) -> tuple[
        str,
        list[tuple[str, str]],
        tuple[str, str] | None,
        list[tuple[str, str]],
        str,
    ]:
        description = self._extract_description(docstring)
        params = self._extract_params(docstring)
        returns = self._extract_returns(docstring)
        raises = self._extract_raises(docstring)
        examples = self._extract_examples(docstring)
        return description, params, returns, raises, examples

    def _extract_description(self, docstring: str) -> str:
        match = re.match(r"(.*?)(?=\n[A-Z][a-z]+:|\n\n|$)", docstring, re.S)
        return match.group(0).strip() if match else ""

    def _extract_params(self, docstring: str) -> list[tuple[str, str]]:
        params = []
        param_section = re.search(r"Args:\n(.*?)(?=\n[A-Z][a-z]+:|\n\n|$)", docstring, re.S)
        if param_section:
            param_matches = re.findall(
                r"\s*([\w_]+):\s*(.*?)\s*(?=\n\s*[\w_]+:|\n\n|$)", param_section.group(1), re.S
            )
            params.extend(param_matches)
        return params

    def _extract_returns(self, docstring: str) -> tuple[str, str] | None:
        return_section = re.search(r"Returns:\n(.*?)(?=\n[A-Z][a-z]+:|\n\n|$)", docstring, re.S)
        if return_section:
            match = re.match(r"\s*(.*?)\s*(?=\n\n|$)", return_section.group(1), re.S)
            if match:
                return match.groups()
        return None

    def _extract_raises(self, docstring: str) -> list[tuple[str, str]]:
        raises = []
        raises_section = re.search(r"Raises:\n(.*?)(?=\n[A-Z][a-z]+:|\n\n|$)", docstring, re.S)
        if raises_section:
            raise_matches = re.findall(
                r"\s*([\w_]+):\s*(.*?)\s*(?=\n\s*[\w_]+:|\n\n|$)", raises_section.group(1), re.S
            )
            for match in raise_matches:
                raises = [*raises, match]
        return raises

    def _extract_examples(self, docstring: str) -> str:
        examples_section = re.search(r"Examples?:\n(.*)", docstring, re.S)
        return examples_section.group(1).strip() if examples_section else ""


Parser = GoogleStyleDocstringParser
