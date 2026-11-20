const fs = require('fs');
const path = require('path');
const pptxgen = require('pptxgenjs');

const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = 'Meghana Kantipudi';
pptx.company = 'USC CSCI 599';
pptx.subject = 'DeepTrace capstone technical presentation';
pptx.title = 'DeepTrace — Agentic Research with Approval and Verification';
pptx.lang = 'en-US';
pptx.theme = {
  headFontFace: 'Aptos Display',
  bodyFontFace: 'Aptos',
  lang: 'en-US',
};
pptx.defineSlideMaster({
  title: 'DEEPTRACE_MASTER',
  background: { color: '07111F' },
  objects: [
    { rect: { x: 0, y: 0, w: 0.12, h: 7.5, fill: { color: '32D6C5' }, line: { color: '32D6C5' } } },
    { text: { text: 'DEEPTRACE · CSCI 599 CAPSTONE', options: { x: 0.48, y: 7.15, w: 4.6, h: 0.16, fontFace: 'Aptos', fontSize: 9, color: '7F91A8', bold: true, charSpacing: 1.2, margin: 0 } } },
  ],
  slideNumber: { x: 12.28, y: 7.08, w: 0.45, h: 0.2, fontFace: 'Aptos', fontSize: 10, color: '7F91A8', align: 'right', margin: 0 },
});

const C = {
  bg: '07111F',
  panel: '0F1D2E',
  panel2: '13253A',
  white: 'F7FAFC',
  muted: 'A8B5C7',
  cyan: '32D6C5',
  cyan2: '79F0E3',
  violet: '8A7CFF',
  amber: 'FFBE5C',
  red: 'FF6B7A',
  green: '67D391',
  grid: '23374E',
};

const S = pptx.ShapeType;

function addText(slide, text, x, y, w, h, opts = {}) {
  slide.addText(text, {
    x, y, w, h,
    fontFace: opts.fontFace || 'Aptos',
    fontSize: opts.fontSize || 18,
    color: opts.color || C.white,
    bold: opts.bold || false,
    align: opts.align || 'left',
    valign: opts.valign || 'mid',
    margin: opts.margin === undefined ? 0 : opts.margin,
    breakLine: false,
    fit: 'shrink',
    ...opts,
  });
}

function addSectionTitle(slide, section, title, subtitle) {
  addText(slide, section.toUpperCase(), 0.58, 0.35, 2.9, 0.24, { fontSize: 11, color: C.cyan, bold: true, charSpacing: 1.8 });
  addText(slide, title, 0.58, 0.72, 12.05, 0.56, { fontSize: 30, bold: true });
  if (subtitle) addText(slide, subtitle, 0.58, 1.35, 11.8, 0.42, { fontSize: 15, color: C.muted });
}

function card(slide, x, y, w, h, title, body, accent = C.cyan, options = {}) {
  slide.addShape(S.roundRect, { x, y, w, h, rectRadius: 0.08, fill: { color: options.fill || C.panel }, line: { color: options.line || C.grid, width: 1 } });
  slide.addShape(S.rect, { x, y, w: 0.06, h, fill: { color: accent }, line: { color: accent } });
  addText(slide, title, x + 0.25, y + 0.18, w - 0.45, 0.35, { fontSize: options.titleSize || 18, bold: true, color: options.titleColor || C.white });
  addText(slide, body, x + 0.25, y + 0.62, w - 0.45, h - 0.78, { fontSize: options.bodySize || 14, color: options.bodyColor || C.muted, valign: 'top', breakLine: false, lineSpacingMultiple: 1.05 });
}

function pill(slide, text, x, y, w, color = C.cyan, fill = C.panel2) {
  slide.addShape(S.roundRect, { x, y, w, h: 0.36, fill: { color: fill }, line: { color, width: 1 } });
  addText(slide, text, x + 0.08, y + 0.02, w - 0.16, 0.3, { fontSize: 11, bold: true, color, align: 'center' });
}

function metric(slide, x, y, w, value, label, color = C.cyan) {
  slide.addShape(S.roundRect, { x, y, w, h: 1.22, fill: { color: C.panel }, line: { color: C.grid, width: 1 } });
  addText(slide, value, x + 0.12, y + 0.13, w - 0.24, 0.52, { fontSize: 26, bold: true, color, align: 'center' });
  addText(slide, label, x + 0.12, y + 0.73, w - 0.24, 0.28, { fontSize: 12, color: C.muted, align: 'center' });
}

function arrow(slide, x1, y1, x2, y2, color = C.cyan, width = 2) {
  slide.addShape(S.line, { x: x1, y: y1, w: x2 - x1, h: y2 - y1, line: { color, width, beginArrowType: 'none', endArrowType: 'triangle' } });
}

function node(slide, x, y, w, label, color = C.cyan, fill = C.panel) {
  slide.addShape(S.roundRect, { x, y, w, h: 0.62, fill: { color: fill }, line: { color, width: 1.3 } });
  addText(slide, label, x + 0.08, y + 0.06, w - 0.16, 0.48, { fontSize: 13, bold: true, align: 'center' });
}

function note(slide, text) {
  if (typeof slide.addNotes === 'function') slide.addNotes(text);
}

// 1 — Cover
{
  const slide = pptx.addSlide('DEEPTRACE_MASTER');
  slide.background = { color: C.bg };
  slide.addShape(S.rect, { x: 8.86, y: 0, w: 4.47, h: 7.5, fill: { color: '0B1728' }, line: { color: '0B1728' } });
  slide.addShape(S.arc, { x: 9.25, y: 1.35, w: 3.05, h: 3.05, adjustPoint: 0.25, rotate: 20, fill: { color: C.bg, transparency: 100 }, line: { color: C.cyan, width: 5, transparency: 8 } });
  slide.addShape(S.arc, { x: 9.72, y: 1.82, w: 2.1, h: 2.1, rotate: 198, fill: { color: C.bg, transparency: 100 }, line: { color: C.violet, width: 5, transparency: 10 } });
  slide.addShape(S.ellipse, { x: 10.42, y: 2.52, w: 0.7, h: 0.7, fill: { color: C.cyan }, line: { color: C.cyan } });
  addText(slide, 'DEEPTRACE', 0.72, 1.15, 6.8, 0.42, { fontSize: 15, color: C.cyan, bold: true, charSpacing: 3.2 });
  addText(slide, 'Agentic research\nwith approval and verification', 0.72, 1.78, 7.55, 1.75, { fontSize: 36, bold: true, breakLine: false, valign: 'top', lineSpacingMultiple: 0.92 });
  addText(slide, 'A bounded LangGraph workflow that pauses for human control, corrects evidence gaps, quarantines retrieved instructions, and closes every citation.', 0.74, 3.82, 7.28, 1.05, { fontSize: 18, color: C.muted, valign: 'top', lineSpacingMultiple: 1.1 });
  pill(slide, 'PLAN', 0.74, 5.24, 1.05);
  pill(slide, 'APPROVE', 1.95, 5.24, 1.38, C.violet);
  pill(slide, 'VERIFY', 3.49, 5.24, 1.22, C.amber);
  pill(slide, 'CORRECT', 4.87, 5.24, 1.35, C.cyan);
  pill(slide, 'CITE', 6.38, 5.24, 0.92, C.green);
  addText(slide, 'Meghana Kantipudi · CSCI 599 Capstone · November 2026', 0.74, 6.25, 7.2, 0.32, { fontSize: 13, color: C.muted });
  addText(slide, '4', 10.05, 5.05, 1.3, 0.78, { fontSize: 44, color: C.cyan, bold: true, align: 'center' });
  addText(slide, 'advanced features\nverified locally', 9.58, 5.82, 2.25, 0.7, { fontSize: 15, color: C.muted, bold: true, align: 'center' });
  note(slide, 'Introduce DeepTrace as an original research-verification agent, not an extension of the Assignment 3 personal assistant.');
}

// 2 — Problem and originality
{
  const slide = pptx.addSlide('DEEPTRACE_MASTER');
  addSectionTitle(slide, 'Problem', 'One-shot research hides consequential failure modes', 'DeepTrace makes evidence and control decisions inspectable instead of trusting a single model response.');
  card(slide, 0.65, 2.05, 3.72, 2.45, 'Evidence gaps', 'A fluent answer can conceal missing plan items, shallow snippets, and unresolved conflicts.', C.amber);
  card(slide, 4.78, 2.05, 3.72, 2.45, 'Unsupported citations', 'Citation labels can look credible even when they do not close over retained source metadata.', C.violet);
  card(slide, 8.91, 2.05, 3.72, 2.45, 'Retrieved instructions', 'Search content can attempt to approve, skip verification, alter budgets, or fabricate source IDs.', C.red);
  slide.addShape(S.roundRect, { x: 0.65, y: 5.04, w: 11.98, h: 1.25, fill: { color: '102A38' }, line: { color: C.cyan, width: 1.5 } });
  addText(slide, 'Original design thesis', 0.92, 5.27, 2.1, 0.28, { fontSize: 14, color: C.cyan, bold: true });
  addText(slide, 'Reliable agentic research is a state-and-policy problem—not only a prompting problem.', 3.05, 5.16, 8.95, 0.46, { fontSize: 22, bold: true });
  addText(slide, 'Distinct from the Assignment 3 personal-assistant workflow.', 3.05, 5.72, 8.5, 0.28, { fontSize: 13, color: C.muted });
  note(slide, 'Frame originality: the application is purpose-built around research verification, not personal assistant tasks.');
}

// 3 — Architecture
{
  const slide = pptx.addSlide('DEEPTRACE_MASTER');
  addSectionTitle(slide, 'Architecture', 'A protected boundary before any research begins', 'Typed state and code-owned graph edges separate user control, untrusted evidence, and synthesis.');
  const xs = [0.62, 2.17, 3.72, 5.27, 6.82, 8.37, 9.92, 11.47];
  const labels = ['Question', 'Validate', 'Plan', 'HITL\ninterrupt', 'Query', 'Retrieve', 'Verify', 'Critic'];
  const colors = [C.cyan, C.cyan, C.violet, C.amber, C.cyan, C.cyan, C.green, C.violet];
  for (let i = 0; i < labels.length; i++) {
    node(slide, xs[i], 2.25, 1.22, labels[i], colors[i], i === 3 ? '2A231A' : C.panel);
    if (i < labels.length - 1) arrow(slide, xs[i] + 1.22, 2.56, xs[i + 1] - 0.08, 2.56, C.grid, 1.5);
  }
  node(slide, 9.55, 4.05, 1.58, 'Revise query', C.amber, '2A231A');
  node(slide, 11.33, 4.05, 1.32, 'Synthesize', C.green, '173126');
  arrow(slide, 12.08, 2.88, 12.08, 3.96, C.green, 2);
  arrow(slide, 11.46, 2.88, 10.34, 3.96, C.amber, 2);
  arrow(slide, 9.55, 4.36, 8.98, 3.02, C.amber, 2);
  addText(slide, 'gap + budget remains', 8.53, 3.39, 2.25, 0.25, { fontSize: 11, color: C.amber, bold: true, align: 'center' });
  addText(slide, 'sufficient / bounded stop', 11.07, 3.39, 1.86, 0.28, { fontSize: 11, color: C.green, bold: true, align: 'center' });
  slide.addShape(S.line, { x: 0.65, y: 5.35, w: 11.95, h: 0, line: { color: C.grid, width: 1 } });
  pill(slide, 'FastAPI + Jinja UI', 0.72, 5.72, 2.15, C.cyan);
  pill(slide, 'LangGraph typed state', 3.12, 5.72, 2.2, C.violet);
  pill(slide, 'SQLite checkpoints', 5.57, 5.72, 1.95, C.amber);
  pill(slide, 'Filesystem history', 7.77, 5.72, 1.88, C.green);
  pill(slide, 'Provider interfaces', 9.9, 5.72, 1.9, C.cyan);
  addText(slide, 'No query generation, retrieval, verification, critic, or synthesis can execute before the human checkpoint is crossed.', 1.2, 6.38, 10.85, 0.4, { fontSize: 15, color: C.white, bold: true, align: 'center' });
  note(slide, 'Walk left to right. Emphasize that retrieval is structurally downstream of the LangGraph interrupt.');
}

// 4 — Design decisions
{
  const slide = pptx.addSlide('DEEPTRACE_MASTER');
  addSectionTitle(slide, 'Design decisions', 'Four choices make the workflow auditable', 'Each decision trades maximum autonomy for explicit evidence, bounded execution, and reproducibility.');
  const rows = [
    ['Typed LangGraph state', 'Expose every control transition', 'Retrieved/model text cannot select graph edges'],
    ['Real interrupt + resume', 'Approval must control execution', 'Zero search calls before approval'],
    ['Separate checkpoint + history stores', 'Mutable and terminal state differ', 'Clear persistence and cancellation policy'],
    ['Deterministic submission provider', 'Repeatable grader evidence', 'Simulated retrieval is visibly labeled'],
  ];
  const y0 = 2.08;
  addText(slide, 'DECISION', 0.82, 1.84, 3.2, 0.24, { fontSize: 11, color: C.cyan, bold: true, charSpacing: 1.2 });
  addText(slide, 'RATIONALE', 4.55, 1.84, 3.2, 0.24, { fontSize: 11, color: C.violet, bold: true, charSpacing: 1.2 });
  addText(slide, 'CONSEQUENCE', 8.42, 1.84, 3.5, 0.24, { fontSize: 11, color: C.amber, bold: true, charSpacing: 1.2 });
  rows.forEach((r, i) => {
    const y = y0 + i * 1.08;
    slide.addShape(S.roundRect, { x: 0.65, y, w: 11.95, h: 0.85, fill: { color: i % 2 ? '0C1929' : C.panel }, line: { color: C.grid, width: 1 } });
    addText(slide, r[0], 0.86, y + 0.1, 3.22, 0.62, { fontSize: 16, bold: true });
    addText(slide, r[1], 4.55, y + 0.1, 3.22, 0.62, { fontSize: 15, color: C.muted });
    addText(slide, r[2], 8.42, y + 0.1, 3.78, 0.62, { fontSize: 15, color: C.muted });
  });
  slide.addShape(S.roundRect, { x: 1.45, y: 6.42, w: 10.25, h: 0.48, fill: { color: '102A38' }, line: { color: C.cyan, width: 1 } });
  addText(slide, 'Policy is implemented in graph/state code; model judgments remain advisory structured data.', 1.75, 6.49, 9.65, 0.3, { fontSize: 14, color: C.cyan2, bold: true, align: 'center' });
  note(slide, 'Use the consequence column to connect architecture choices to testable evidence.');
}

// 5 — Capabilities
{
  const slide = pptx.addSlide('DEEPTRACE_MASTER');
  addSectionTitle(slide, 'Capabilities', 'Four advanced features execute end to end', 'All four are verified in the local deterministic deployment; cloud durability is not claimed.');
  card(slide, 0.65, 2.0, 5.75, 1.8, '01 · Planning + self-correction', 'A critic detects evidence gaps and changes the next query. The loop is bounded at two total retrieval passes.', C.violet, { titleSize: 20, bodySize: 15 });
  card(slide, 6.83, 2.0, 5.75, 1.8, '02 · Human-in-the-loop', 'Approve, modify, or cancel resumes the same checkpointed workflow. Duplicate and invalid resumes fail safely.', C.amber, { titleSize: 20, bodySize: 15 });
  card(slide, 0.65, 4.18, 5.75, 1.8, '03 · Agentic RAG', 'Query, retrieve, verify, critique, revise, and synthesize occur in graph execution with citation closure.', C.cyan, { titleSize: 20, bodySize: 15 });
  card(slide, 6.83, 4.18, 5.75, 1.8, '04 · Cross-session memory', 'Completed and cancelled records survive process restarts in bounded filesystem storage; SQLite preserves local checkpoints.', C.green, { titleSize: 20, bodySize: 15 });
  addText(slide, 'Not claimed: browser automation · A2A · hybrid inference', 2.35, 6.48, 8.6, 0.34, { fontSize: 14, color: C.muted, align: 'center' });
  note(slide, 'Name the four selected features exactly as they appear in the README Capability-to-Code Map.');
}

// 6 — HITL and memory
{
  const slide = pptx.addSlide('DEEPTRACE_MASTER');
  addSectionTitle(slide, 'Capability detail', 'HITL approval is a real graph interrupt', 'The same stable workflow ID resumes; terminal outcomes are stored separately from mutable checkpoints.');
  const events = [
    ['1', 'Submit', 'question validated'],
    ['2', 'Plan', 'typed plan created'],
    ['3', 'Interrupt', 'checkpoint saved'],
    ['4', 'Human', 'approve / modify / cancel'],
    ['5', 'Resume', 'same thread continues'],
    ['6', 'Persist', 'terminal record saved'],
  ];
  events.forEach((e, i) => {
    const x = 0.58 + i * 2.08;
    slide.addShape(S.ellipse, { x, y: 2.27, w: 0.54, h: 0.54, fill: { color: i === 3 ? C.amber : C.cyan }, line: { color: i === 3 ? C.amber : C.cyan } });
    addText(slide, e[0], x, 2.31, 0.54, 0.38, { fontSize: 14, color: C.bg, bold: true, align: 'center' });
    if (i < events.length - 1) arrow(slide, x + 0.56, 2.54, x + 1.93, 2.54, C.grid, 2);
    addText(slide, e[1], x - 0.36, 3.03, 1.28, 0.34, { fontSize: 16, bold: true, align: 'center' });
    addText(slide, e[2], x - 0.52, 3.45, 1.62, 0.56, { fontSize: 12, color: C.muted, align: 'center', valign: 'top' });
  });
  slide.addShape(S.roundRect, { x: 0.68, y: 4.58, w: 5.68, h: 1.47, fill: { color: C.panel }, line: { color: C.amber, width: 1.4 } });
  addText(slide, 'Protected boundary', 0.95, 4.82, 2.05, 0.3, { fontSize: 17, color: C.amber, bold: true });
  addText(slide, 'Before approval: query generation = 0 · search calls = 0 · synthesis = 0', 0.95, 5.25, 4.95, 0.45, { fontSize: 15, color: C.white, bold: true });
  slide.addShape(S.roundRect, { x: 6.83, y: 4.58, w: 5.78, h: 1.47, fill: { color: C.panel }, line: { color: C.green, width: 1.4 } });
  addText(slide, 'Persistence behavior', 7.1, 4.82, 2.3, 0.3, { fontSize: 17, color: C.green, bold: true });
  addText(slide, 'Restart → reopen history · cancellation stores no report or citations', 7.1, 5.25, 4.95, 0.45, { fontSize: 15, color: C.white, bold: true });
  pill(slide, 'unknown ID rejected', 1.02, 6.45, 2.05, C.red);
  pill(slide, 'duplicate resume rejected', 3.45, 6.45, 2.35, C.red);
  pill(slide, 'modified plan drives queries', 7.02, 6.45, 2.55, C.violet);
  pill(slide, 'cancel = zero retrieval', 9.92, 6.45, 2.2, C.amber);
  note(slide, 'Demonstrate the pending approval screen, then modify one plan item before approving.');
}

// 7 — RAG correction
{
  const slide = pptx.addSlide('DEEPTRACE_MASTER');
  addSectionTitle(slide, 'Capability detail', 'Self-correction changes downstream execution', 'The deterministic demo creates one recoverable evidence gap and one instruction-like source.');
  slide.addShape(S.roundRect, { x: 0.65, y: 2.02, w: 5.57, h: 3.88, fill: { color: C.panel }, line: { color: C.red, width: 1.5 } });
  addText(slide, 'PASS 1', 0.95, 2.27, 1.08, 0.27, { fontSize: 12, color: C.red, bold: true, charSpacing: 1.3 });
  addText(slide, 'Gap detected', 0.95, 2.7, 4.6, 0.46, { fontSize: 25, bold: true });
  addText(slide, '• Initial bounded queries execute\n• Retrieved instruction attempts to skip verification\n• Source is quarantined and rejected\n• Critic returns insufficient coverage', 0.95, 3.35, 4.8, 1.65, { fontSize: 16, color: C.muted, valign: 'top', lineSpacingMultiple: 1.05 });
  pill(slide, 'route → revise_queries', 1.03, 5.25, 2.42, C.amber, '2A231A');
  slide.addShape(S.chevron, { x: 6.37, y: 3.28, w: 0.58, h: 1.3, fill: { color: C.amber }, line: { color: C.amber } });
  slide.addShape(S.roundRect, { x: 7.1, y: 2.02, w: 5.5, h: 3.88, fill: { color: C.panel }, line: { color: C.green, width: 1.5 } });
  addText(slide, 'PASS 2', 7.4, 2.27, 1.08, 0.27, { fontSize: 12, color: C.green, bold: true, charSpacing: 1.3 });
  addText(slide, 'Coverage recovered', 7.4, 2.7, 4.6, 0.46, { fontSize: 25, bold: true });
  addText(slide, '• Revised query targets the recorded gap\n• Independent safe evidence is retrieved\n• Verification accepts supporting evidence\n• Critic returns sufficient; synthesis runs', 7.4, 3.35, 4.75, 1.65, { fontSize: 16, color: C.muted, valign: 'top', lineSpacingMultiple: 1.05 });
  pill(slide, 'route → synthesize', 7.48, 5.25, 2.05, C.green, '173126');
  addText(slide, 'Bounded invariant: 1 initial pass + at most 1 correction pass', 2.12, 6.42, 9.1, 0.38, { fontSize: 17, color: C.cyan2, bold: true, align: 'center' });
  note(slide, 'Show that the malicious source is visible in the UI but never cited.');
}

// 8 — Safety
{
  const slide = pptx.addSlide('DEEPTRACE_MASTER');
  addSectionTitle(slide, 'Safety + guardrails', 'Defense in depth across every trust boundary', 'Prompt filtering is only one layer; graph, schema, budget, and citation controls enforce invariants.');
  const layers = [
    ['1', 'Normalize + bound input', C.cyan],
    ['2', 'Inspect question + plan edits', C.violet],
    ['3', 'Explicit human approval', C.amber],
    ['4', 'Quarantine retrieved instructions', C.red],
    ['5', 'Fixed routes + trusted budgets', C.cyan],
    ['6', 'Citation closure + typed memory', C.green],
  ];
  layers.forEach((l, i) => {
    const x = 0.72 + (i % 3) * 4.13;
    const y = 2.05 + Math.floor(i / 3) * 1.42;
    slide.addShape(S.roundRect, { x, y, w: 3.7, h: 1.05, fill: { color: C.panel }, line: { color: l[2], width: 1.2 } });
    slide.addShape(S.ellipse, { x: x + 0.18, y: y + 0.23, w: 0.58, h: 0.58, fill: { color: l[2] }, line: { color: l[2] } });
    addText(slide, l[0], x + 0.18, y + 0.29, 0.58, 0.35, { fontSize: 14, bold: true, color: C.bg, align: 'center' });
    addText(slide, l[1], x + 0.94, y + 0.2, 2.48, 0.62, { fontSize: 16, bold: true });
  });
  slide.addShape(S.roundRect, { x: 0.72, y: 5.13, w: 11.63, h: 1.25, fill: { color: '171D2E' }, line: { color: C.violet, width: 1.4 } });
  addText(slide, 'Retrieved content cannot:', 1.0, 5.3, 3.0, 0.3, { fontSize: 16, color: C.violet, bold: true });
  addText(slide, 'approve · change graph edges · increase budgets · skip verification · create citation IDs · alter permissions', 1.0, 5.72, 10.95, 0.42, { fontSize: 15, bold: true, align: 'center' });
  addText(slide, 'Redacted safety events retain stage, action, rule IDs, and identifiers—not prompts, secrets, or evidence bodies.', 1.2, 6.57, 10.85, 0.32, { fontSize: 13, color: C.muted, align: 'center' });
  note(slide, 'Explain why structural controls remain effective even if lexical injection detection misses a novel phrase.');
}

// 9 — Attacks
{
  const slide = pptx.addSlide('DEEPTRACE_MASTER');
  addSectionTitle(slide, 'Safety evidence', 'Three prompt-injection attacks against the operating workflow', 'Exact injection points, traces, outcomes, and responsible controls are preserved in JSON evidence.');
  const attacks = [
    ['PI-001', 'User question', 'Override + prompt exfiltration', 'Rejected before workflow; 0 searches', C.red],
    ['PI-002', 'Retrieved source', 'Trust escalation + skip verification', 'Quarantined; safe pass 2; not cited', C.amber],
    ['PI-003', 'Retrieved source', 'Alter approval, counter, critic, citation', 'Approval retained; S999 absent', C.violet],
  ];
  addText(slide, 'ATTACK', 0.72, 1.91, 1.0, 0.22, { fontSize: 10, color: C.muted, bold: true });
  addText(slide, 'INJECTION POINT', 1.83, 1.91, 2.0, 0.22, { fontSize: 10, color: C.muted, bold: true });
  addText(slide, 'OBJECTIVE', 4.05, 1.91, 3.45, 0.22, { fontSize: 10, color: C.muted, bold: true });
  addText(slide, 'ACTUAL RESULT', 8.05, 1.91, 4.0, 0.22, { fontSize: 10, color: C.muted, bold: true });
  attacks.forEach((a, i) => {
    const y = 2.18 + i * 1.18;
    slide.addShape(S.roundRect, { x: 0.65, y, w: 11.98, h: 0.95, fill: { color: C.panel }, line: { color: a[4], width: 1.2 } });
    addText(slide, a[0], 0.82, y + 0.18, 0.78, 0.46, { fontSize: 16, color: a[4], bold: true });
    addText(slide, a[1], 1.83, y + 0.18, 1.85, 0.46, { fontSize: 15, bold: true });
    addText(slide, a[2], 4.05, y + 0.13, 3.42, 0.56, { fontSize: 14, color: C.muted });
    addText(slide, a[3], 8.05, y + 0.13, 4.12, 0.56, { fontSize: 14, color: C.white, bold: true });
  });
  metric(slide, 1.05, 5.82, 2.15, '3 / 3', 'attacks mitigated', C.green);
  metric(slide, 3.55, 5.82, 2.15, '0', 'unsafe objectives', C.green);
  metric(slide, 6.05, 5.82, 2.15, '3', 'guardrail triggers', C.cyan);
  metric(slide, 8.55, 5.82, 2.75, '1 / 1', 'benign control accepted', C.violet);
  note(slide, 'Do not generalize 3/3 to universal safety. State the small-corpus limitation.');
}

// 10 — Evaluation methodology
{
  const slide = pptx.addSlide('DEEPTRACE_MASTER');
  addSectionTitle(slide, 'Evaluation', 'A versioned custom harness tests graph-policy correctness', 'Every case executes the real local workflow with deterministic providers and schema-validated expectations.');
  const cats = [
    ['6', 'initially sufficient', C.green],
    ['5', 'correction required', C.cyan],
    ['4', 'bounded insufficiency', C.amber],
    ['4', 'citation integrity', C.violet],
    ['3', 'safety attacks', C.red],
    ['5', 'HITL policies', C.cyan],
  ];
  cats.forEach((c, i) => {
    const x = 0.7 + (i % 3) * 4.12;
    const y = 2.03 + Math.floor(i / 3) * 1.45;
    slide.addShape(S.roundRect, { x, y, w: 3.68, h: 1.1, fill: { color: C.panel }, line: { color: C.grid, width: 1 } });
    addText(slide, c[0], x + 0.22, y + 0.12, 0.72, 0.62, { fontSize: 27, bold: true, color: c[2], align: 'center' });
    addText(slide, c[1], x + 1.08, y + 0.24, 2.25, 0.48, { fontSize: 16, bold: true });
  });
  slide.addShape(S.roundRect, { x: 0.7, y: 5.1, w: 11.62, h: 1.2, fill: { color: '0C1929' }, line: { color: C.grid, width: 1 } });
  addText(slide, 'Measures', 0.98, 5.35, 1.1, 0.28, { fontSize: 14, color: C.cyan, bold: true });
  addText(slide, 'termination · correction · plan coverage · citations · approval policy · safety · latency · resource use', 2.05, 5.23, 9.82, 0.5, { fontSize: 16, bold: true, align: 'center' });
  addText(slide, 'Scope boundary: deterministic workflow behavior—not live-web truth, semantic relevance, or public-service reliability.', 1.08, 6.58, 11.05, 0.3, { fontSize: 13, color: C.muted, align: 'center' });
  note(slide, 'Describe the complete 27-case enumeration and why deterministic state assertions fit the selected capabilities.');
}

// 11 — Evaluation results
{
  const slide = pptx.addSlide('DEEPTRACE_MASTER');
  addSectionTitle(slide, 'Evaluation results', 'Correct control behavior—with designed insufficiency left visible', 'Regenerated 2026-11-19 America/Los_Angeles from the submission-candidate worktree.');
  metric(slide, 0.7, 2.0, 2.2, '27 / 27', 'tasks passed', C.green);
  metric(slide, 3.12, 2.0, 2.2, '5 / 5', 'corrections succeeded', C.cyan);
  metric(slide, 5.54, 2.0, 2.2, '5 / 5', 'HITL policies', C.amber);
  metric(slide, 7.96, 2.0, 2.2, '39 / 39', 'valid citations', C.violet);
  metric(slide, 10.38, 2.0, 2.2, '0', 'unsupported citations', C.green);
  addText(slide, 'Evidence coverage', 0.78, 3.78, 2.2, 0.32, { fontSize: 17, bold: true });
  slide.addShape(S.roundRect, { x: 2.72, y: 3.84, w: 8.95, h: 0.34, fill: { color: C.grid }, line: { color: C.grid } });
  slide.addShape(S.roundRect, { x: 2.72, y: 3.84, w: 8.08, h: 0.34, fill: { color: C.cyan }, line: { color: C.cyan } });
  addText(slide, '90.244% · 37 / 41 plan items', 9.55, 4.25, 2.15, 0.28, { fontSize: 13, color: C.cyan2, bold: true, align: 'right' });
  slide.addShape(S.roundRect, { x: 0.72, y: 4.9, w: 11.88, h: 1.25, fill: { color: '2A231A' }, line: { color: C.amber, width: 1.2 } });
  addText(slide, 'Why coverage is not 100%', 1.0, 5.12, 3.25, 0.3, { fontSize: 17, color: C.amber, bold: true });
  addText(slide, 'Four deliberately persistent gaps remained unsupported. The workflow stopped at its budget and disclosed uncertainty—so safe termination passed.', 1.0, 5.5, 11.0, 0.46, { fontSize: 15, color: C.white, bold: true });
  addText(slide, 'Average local workflow latency: 1.213 ms · p95: 2.298 ms · external model calls: 0', 1.55, 6.58, 10.3, 0.3, { fontSize: 13, color: C.muted, align: 'center' });
  note(slide, 'Emphasize that evidence coverage intentionally includes designed gaps in the denominator.');
}

// 12 — Deployment and cost
{
  const slide = pptx.addSlide('DEEPTRACE_MASTER');
  addSectionTitle(slide, 'Deployment + cost', 'A reproducible local topology matches the grading boundary', 'The recorded system behavior—not a public URL—is the submission evidence.');
  card(slide, 0.65, 2.0, 5.72, 2.42, 'Local FastAPI deployment', 'scripts/run_demo.ps1 pins deterministic planning, the correction demo provider, SQLite checkpoints, filesystem history, and bounded rate limits. Research history survives a process restart.', C.cyan, { titleSize: 21, bodySize: 16 });
  card(slide, 6.82, 2.0, 5.78, 2.42, 'Measured live provider evidence', 'One Vertex structured-planning call used gemini-3.5-flash-lite at global: 415 input + 248 output = 663 total tokens, 6061.887 ms latency.', C.violet, { titleSize: 21, bodySize: 16 });
  metric(slide, 0.85, 5.0, 2.55, '$0.00', 'deterministic evaluation', C.green);
  metric(slide, 3.72, 5.0, 2.55, '$0.000372', 'measured planning estimate', C.cyan);
  metric(slide, 6.59, 5.0, 2.55, '$0.0372', '100 similar calls / week', C.violet);
  metric(slide, 9.46, 5.0, 2.55, '$0 / week', 'billed local infrastructure', C.amber);
  addText(slide, 'Pricing snapshot: 2026-11-19 · estimate covers planning only · live Tavily cost not measured', 1.18, 6.57, 10.98, 0.32, { fontSize: 12, color: C.muted, align: 'center' });
  note(slide, 'Clarify that the Vertex measurement verifies structured planning only, not live end-to-end research.');
}

// 13 — Limitations and future
{
  const slide = pptx.addSlide('DEEPTRACE_MASTER');
  addSectionTitle(slide, 'Limitations + future work', 'Strong local semantics; intentionally narrow production claims', 'The next improvements target research quality and multi-user operations—not more unverified feature breadth.');
  slide.addShape(S.roundRect, { x: 0.65, y: 2.0, w: 5.72, h: 3.85, fill: { color: C.panel }, line: { color: C.amber, width: 1.4 } });
  addText(slide, 'CURRENT LIMITATIONS', 0.95, 2.28, 2.25, 0.26, { fontSize: 12, color: C.amber, bold: true, charSpacing: 1.3 });
  addText(slide, '• Simulated submission retrieval; live Tavily unverified\n• Snippet-level evidence and heuristic verification\n• Two-pass correction ceiling\n• Single-machine, single-user persistence\n• No authentication or distributed concurrency', 0.95, 2.8, 4.9, 2.35, { fontSize: 17, color: C.white, valign: 'top', lineSpacingMultiple: 1.1 });
  slide.addShape(S.roundRect, { x: 6.83, y: 2.0, w: 5.78, h: 3.85, fill: { color: C.panel }, line: { color: C.cyan, width: 1.4 } });
  addText(slide, 'PRIORITIZED FUTURE WORK', 7.13, 2.28, 2.75, 0.26, { fontSize: 12, color: C.cyan, bold: true, charSpacing: 1.3 });
  addText(slide, '1. Human-judged live-web benchmark\n2. Claim conflict and stance representation\n3. Authenticated multi-user service\n4. Shared persistence and idempotency\n5. Broader obfuscation/adversarial corpus', 7.13, 2.8, 4.9, 2.35, { fontSize: 17, color: C.white, valign: 'top', lineSpacingMultiple: 1.1 });
  slide.addShape(S.roundRect, { x: 1.28, y: 6.27, w: 10.8, h: 0.68, fill: { color: '102A38' }, line: { color: C.cyan, width: 1.5 } });
  addText(slide, 'DeepTrace demonstrates 4 end-to-end agentic capabilities with measurable safety and evaluation evidence.', 1.58, 6.39, 10.2, 0.38, { fontSize: 17, color: C.cyan2, bold: true, align: 'center' });
  note(slide, 'Close with the verified claims, then transition to the live application demonstration.');
}

const outputDir = path.resolve(__dirname, '..', 'deliverables');
fs.mkdirSync(outputDir, { recursive: true });
const outputPath = path.join(outputDir, 'DeepTrace_Capstone_Presentation.pptx');

pptx.writeFile({ fileName: outputPath }).then(() => {
  console.log(outputPath);
});
