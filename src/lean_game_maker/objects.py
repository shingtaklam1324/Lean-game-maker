#!/usr/bin/env python3
from typing import List
from dataclasses import dataclass, field
import sys

import regex

from lean_game_maker.line_reader import LineReader, dismiss_line, LeanLines


############
#  Objects #
############
@dataclass
class Text:
    name: str = 'text'
    content: str = ''

    def append(self, line):
        self.content = self.content + line

    
@dataclass
class Bilingual:
    """
    Base class for objects that contains both text and Lean code.
    """
    text: str = ''
    lean: str = ''

    def text_append(self, line):
        self.text = self.text + line

    def lean_append(self, line):
        self.lean = self.lean + line


@dataclass
class Definition(Bilingual):
    name: str = 'definition'


@dataclass
class ProofLine:
    name: str = 'proof_line'
    lean: str = ''


@dataclass
class ProofItem:
    name: str = 'proof-item'
    text: str = ''
    lines: List[ProofLine] = field(default_factory=list)

    def text_append(self, line):
        self.text = self.text + line

@dataclass
class Proof:
    name: str = 'proof'
    items: List[ProofItem] = field(default_factory=list)


@dataclass
class Lemma(Bilingual):
    name: str = 'lemma'
    proof: Proof = field(default_factory=Proof)

    def proof_append(self, item):
        self.proof.items.append(item)


@dataclass
class Theorem(Bilingual):
    name: str = 'theorem'
    proof: Proof = field(default_factory=Proof)

    def proof_append(self, item):
        self.proof.items.append(item)


@dataclass
class Example(Bilingual):
    name: str = 'example'
    proof: Proof = field(default_factory=Proof)

    def proof_append(self, item):
        self.proof.items.append(item)
#################
#  Line readers #
#################
class HiddenLine(LineReader):
    regex = regex.compile(r'^[\s\S]*--\s*hide\s*$')

    def run(self, m, file_reader):
        hidden_line = LeanLines()
        hidden_line.append(m.string)
        hidden_line.hidden = True
        self.output.append(hidden_line)
        return True


class HiddenBegin(LineReader):
    regex = regex.compile(r'-- begin hide\s*')

    def run(self, m, file_reader):
        file_reader.status = 'hidden'
        lean_lines = LeanLines()
        file_reader.output.append(lean_lines)
        def normal_line(file_reader, line):
            lean_lines.append(line)
        file_reader.normal_line_handler = normal_line
        return True

class HiddenEnd(LineReader):
    regex = regex.compile(r'-- end hide\s*')

    def run(self, m, file_reader):
        if file_reader.status is not 'hidden':
            return False
        file_reader.reset()
        return True



class TextBegin(LineReader):
    regex = regex.compile(r'\s*/-\s*$')

    def run(self, m, file_reader):
        if file_reader.status is not '':
            return False
        file_reader.status = 'text'
        text = Text()
        file_reader.output.append(text)
        def normal_line(file_reader, line):
            text.append(line)
        file_reader.normal_line_handler = normal_line
        file_reader.blank_line_handler = normal_line
        return True


class TextEnd(LineReader):
    regex = regex.compile(r'-/')

    def run(self, m, file_reader):
        if file_reader.status is not 'text':
            return False
        file_reader.reset()
        return True


class DefinitionBegin(LineReader):
    regex = regex.compile(r'\s*/-\s*Definition\s*$')

    def run(self, m, file_reader):
        file_reader.status = 'definition_text'
        defi = Definition()
        file_reader.output.append(defi)
        def normal_line(file_reader, line):
            defi.text_append(line)
        file_reader.normal_line_handler = normal_line
        return True


class DefinitionEnd(LineReader):
    regex = regex.compile(r'-/')

    def run(self, m, file_reader):
        if file_reader.status is not 'definition_text':
            return False
        file_reader.status = 'definition_lean'
        defi = file_reader.output[-1]
        def normal_line(file_reader, line):
            defi.lean_append(line)
        file_reader.normal_line_handler = normal_line
        def blank_line(file_reader, line):
            file_reader.reset()
        file_reader.blank_line_handler = blank_line
        return True


class LemmaBegin(LineReader):
    regex = regex.compile(r'\s*/-\s*Lemma\s*$')

    def run(self, m, file_reader):
        file_reader.status = 'lemma_text'
        lemma = Lemma()
        file_reader.output.append(lemma)
        def normal_line(file_reader, line):
            lemma.text_append(line)
        file_reader.normal_line_handler = normal_line
        return True


class LemmaEnd(LineReader):
    regex = regex.compile(r'-/')

    def run(self, m, file_reader):
        if file_reader.status is not 'lemma_text':
            return False
        file_reader.status = 'lemma_lean'
        lemma = file_reader.output[-1]
        def normal_line(file_reader, line):
            lemma.lean_append(line)
        file_reader.normal_line_handler = normal_line
        return True


class TheoremBegin(LineReader):
    regex = regex.compile(r'\s*/-\s*Theorem\s*$')

    def run(self, m, file_reader):
        file_reader.status = 'theorem_text'
        theorem = Theorem()
        file_reader.output.append(theorem)
        def normal_line(file_reader, line):
            theorem.text_append(line)
        file_reader.normal_line_handler = normal_line
        return True


class TheoremEnd(LineReader):
    regex = regex.compile(r'-/')

    def run(self, m, file_reader):
        if file_reader.status is not 'theorem_text':
            return False
        file_reader.status = 'theorem_lean'
        theorem = file_reader.output[-1]
        def normal_line(file_reader, line):
            theorem.lean_append(line)
        file_reader.normal_line_handler = normal_line
        return True


class ExampleBegin(LineReader):
    regex = regex.compile(r'\s*/-\s*Example\s*$')

    def run(self, m, file_reader):
        file_reader.status = 'example_text'
        example = Example()
        file_reader.output.append(example)
        def normal_line(file_reader, line):
            example.text_append(line)
        file_reader.normal_line_handler = normal_line
        return True


class ExampleEnd(LineReader):
    regex = regex.compile(r'-/')

    def run(self, m, file_reader):
        if file_reader.status is not 'example_text':
            return False
        file_reader.status = 'example_lean'
        example = file_reader.output[-1]
        def normal_line(file_reader, line):
            example.lean_append(line)
        file_reader.normal_line_handler = normal_line
        return True


class ProofBegin(LineReader):
    regex = regex.compile(r'^begin\s*') # NOTE : this does not require begin to be on a separate line

    def run(self, m, file_reader):
        file_reader.status = 'proof'
        file_reader.normal_line_handler = dismiss_line # Proofs shouldn't start with normal line
        return True


class ProofEnd(LineReader):
    regex = regex.compile(r'^end\s*$')  # Beware of match end

    def run(self, m, file_reader):
        if file_reader.status is not 'proof':
            return False
        file_reader.reset()
        return True

