import random
from ast import AST
from typing import List, Optional

from ..i18n import t
from ..instrument import find_nodes, Instrumentor, ProgramData
from ..models import QLC, QLCPrepared
from .options import pick_options, options, random_options, fill_random_options

class LoopEnd(QLCPrepared):
  def __init__(self, type: str, node: AST):
    super().__init__(type)
    self.node = node

  def make(self):
    beg = self.node.lineno
    end = self.node.end_lineno
    return QLC(
      self.type,
      t('q_loop_end', beg),
      pick_options(
        options([end], 'last_line_inside_block', t('o_loop_end_correct'), True),
        options([max(1, beg - 1)], 'line_before_block', t('o_loop_end_before')),
        options([end + 1], 'line_after_block', t('o_loop_end_after')),
        fill_random_options(4, range(beg + 1, end), 'line_inside_block', t('o_loop_end_inside'))
      )
    )

def loop_end(
  type: str,
  tree: AST,
  call: Optional[str],
  ins: Instrumentor
) -> List[LoopEnd]:
  return list(LoopEnd(type, node) for node in find_nodes(tree, ['For', 'While']))

class VariableDeclaration(QLCPrepared):
  def __init__(self, type: str, element: ProgramData.Element):
    super().__init__(type)
    self.variable = element
  
  def make(self):
    decl = self.variable.declaration
    refs = self.variable.references
    # NOTE: if-else structures can easily assign 1st time on 2nd store name, what to do?
    if decl is None or len(refs) == 0:
      return None
    ref = random.choice(refs)
    text_id = {
      'Store': 'q_variable_write_declaration',
      'Load': 'q_variable_read_declaration',
      'Del': 'q_variable_del_declaration',
    }
    return QLC(
      self.type,
      t(text_id[ref.ctx.__class__.__name__], ref.id, ref.lineno),
      pick_options(
        options([decl.lineno], 'declaration_line', t('o_variable_declaration_correct'), True),
        random_options(
          2,
          [r.lineno for r in refs],
          'reference_line',
          t('o_variable_declaration_reference')
        ),
        fill_random_options(
          4,
          range(max(1, decl.lineno - 2), max(r.lineno for r in refs) + 3),
          'random_line',
          t('o_variable_declaration_random')
        )
      )
    )

def variable_declaration(
  type: str,
  tree: AST,
  call: Optional[str],
  ins: Instrumentor
) -> List[VariableDeclaration]:
  return list(VariableDeclaration(type, e) for e in ins.data.elements_for_types('variable'))
