import unittest
import re
from typing import Any, List, Dict

from qlcpy import generate, QLCRequest, QLC

class TestQuestions(unittest.TestCase):
  RE_EM = '<em>([^<]+)</em>'
  RE_LINE = 'line (\d+)'

  @staticmethod
  def _get_part(question: str, regex: str) -> str:
    m = re.search(regex, question, re.IGNORECASE)
    return m.group(1) if m else None

  def _gen_qlcs(self, type: str, count: int = 100) -> List[QLC]:
    return generate(self.src, [QLCRequest(count, types=[type])], self.call)

  def _gen_a_qlc(self, type: str) -> QLC:
    qlcs = self._gen_qlcs(type, 1)
    self.assertEqual(len(qlcs), 1)
    return qlcs[0]
  
  def _test_qlcs(
    self,
    type: str,
    correct: Dict[Any, Any],
    question_regex: str,
    answer_types: bool = False
  ) -> None:
    qlcs = self._gen_qlcs(type)
    self.assertEqual(len(qlcs), len(correct.keys()))
    for qlc in qlcs:
      key = self._get_part(qlc.question, question_regex)
      answer = correct.get(self._get_part(qlc.question, question_regex))
      self.assertIsNotNone(answer, f'{qlc.question} -> {key}')
      for o in qlc.options:
        if o.correct:
          self.assertEqual(o.type if answer_types else o.answer, answer)
        else:
          self.assertNotEqual(o.type if answer_types else o.answer, answer)

  def setUp(self) -> None:
    with open('test/sample_code.py', 'r') as f:
      self.src = f.read()
    self.call = 'find_first(["lorem", "ipsum", "dolor", "sit", "amet"], "s")'

  def test_variable_names(self):
    qlc = self._gen_a_qlc('VariableNames')
    for t in ['variable', 'reserved_word', 'builtin_function', 'unused_word']:
      self.assertTrue(any(o.type == t and o.correct == (t == 'variable') for o in qlc.options))

  def test_loop_end(self):
    self._test_qlcs('LoopEnd', { '4': 6, '12': 18 }, self.RE_LINE)

  def test_variable_declaration(self):
    self._test_qlcs('VariableDeclaration', { 'i': 4, 's': 9, 'n': 10, 'word': 11 }, self.RE_EM)

  def test_except_source(self):
    self._test_qlcs('ExceptSource', { '17': 15 }, self.RE_LINE)

  def test_line_purpose(self):
    correct_types = { '12': 'end_condition', '13': 'read_input', '19': 'zero_div_guard' }
    self._test_qlcs('LinePurpose', correct_types, self.RE_LINE, answer_types=True)

  def test_loop_count(self):
    self._test_qlcs('LoopCount', { '4': 4, '12': 0 }, self.RE_LINE)

  def test_variable_trace(self):
    self._test_qlcs('VariableTrace', { 'i': '0, 1, 2, 3'}, self.RE_EM)
