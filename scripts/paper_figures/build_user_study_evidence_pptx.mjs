#!/usr/bin/env node
import {
  Presentation,
  PresentationFile,
} from "/Users/zilongzeng/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const OUT = "/Users/zilongzeng/Research/Drone/docs/paper_sensys2027/figures/source/user_study_evidence.pptx";

const colors = {
  ink: "1B2A34",
  muted: "5F6F7A",
  blue: "4477AA",
  teal: "228A8D",
  green: "66A61E",
  orange: "D55E00",
  gray: "D8DEE6",
  paper: "FBFBF7",
  white: "FFFFFF",
};

function addBox(slide, name, x, y, w, h, text, lineColor = colors.blue, fillColor = "F7FAFC") {
  const shape = slide.shapes.add({
    geometry: "roundRect",
    position: { left: x, top: y, width: w, height: h },
    fill: { type: "solid", color: fillColor },
    line: { style: "solid", fill: lineColor, width: 1.1 },
  });
  shape.name = name;
  shape.text = text;
  return shape;
}

function addText(slide, name, x, y, w, h, text, fontSize = 12, color = colors.ink) {
  const shape = slide.shapes.add({
    geometry: "rect",
    position: { left: x, top: y, width: w, height: h },
    fill: { color: "transparent" },
    line: { width: 0, fill: "transparent" },
  });
  shape.name = name;
  shape.text = text;
  return shape;
}

function connect(slide, from, to, color = colors.blue) {
  slide.shapes.connect(from, to, {
    kind: "straight",
    fromSide: "right",
    toSide: "left",
    line: { style: "solid", fill: color, width: 1.2, endArrowType: "triangle" },
  });
}

const deck = Presentation.create();
const slide = deck.slides.add();
slide.background.fill = { type: "solid", color: colors.white };

addText(slide, "title", 28, 18, 640, 28, "Participant-level controlled prompt evidence", 18);
addText(
  slide,
  "subtitle",
  28,
  48,
  690,
  24,
  "Prompt trials produce saved audio, embedded/reference predictions, and auditable event logs.",
  10,
  colors.muted,
);

addText(slide, "panel-a", 46, 88, 220, 20, "A. participant/session pipeline", 11);
const p1 = addBox(slide, "participant", 48, 126, 86, 56, "participant", colors.blue);
const p2 = addBox(slide, "prompt-list", 158, 126, 86, 56, "prompt\nlist", colors.blue);
const p3 = addBox(slide, "embedded-capture", 268, 126, 104, 56, "embedded\ncapture/infer", colors.teal);
const p4 = addBox(slide, "saved-logs", 396, 126, 96, 56, "saved audio\n+ logs", colors.green);
connect(slide, p1, p2, colors.blue);
connect(slide, p2, p3, colors.teal);
connect(slide, p3, p4, colors.green);

addText(slide, "panel-b", 46, 250, 250, 20, "B. intent/keyword/repeat matrix", 11);
const mx = 50;
const my = 288;
const mw = 430;
const mh = 72;
addBox(slide, "matrix-shell", mx, my, mw, mh, "", colors.ink, colors.paper);
const headers = ["participants", "3 intents", "5 keywords", "10 repeats"];
for (let i = 0; i < headers.length; i += 1) {
  addText(slide, `matrix-${i}`, mx + i * (mw / 4) + 8, my + 18, mw / 4 - 16, 28, headers[i], 10);
  if (i === 0) {
    addText(slide, "matrix-participants-placeholder", mx + 8, my + 42, mw / 4 - 16, 18, "XXX", 10, colors.muted);
  }
}
addText(slide, "prompt-factor-note", 50, 368, 430, 24, "Prompt factors only: participant, intent, keyword, repeat.", 9, colors.muted);

addText(slide, "panel-c", 532, 88, 170, 20, "C. result summary", 11);
const metrics = [
  ["accuracy", "XXX"],
  ["emergency recall", "XXX"],
  ["unknown false event rate", "XXX"],
  ["embedded/ref. disagreement", "XXX"],
];
for (let i = 0; i < metrics.length; i += 1) {
  const y = 126 + i * 38;
  addText(slide, `metric-name-${i}`, 536, y, 260, 22, metrics[i][0], 10, colors.ink);
  addText(slide, `metric-value-${i}`, 802, y, 54, 22, metrics[i][1], 10, colors.muted);
}

addText(slide, "panel-d", 532, 250, 180, 20, "D. demo/log evidence strip", 11);
const d1 = addBox(slide, "speech-event", 536, 290, 74, 54, "speech\nevent", colors.blue);
const d2 = addBox(slide, "intent-event", 632, 290, 74, 54, "intent\nevent", colors.teal);
const d3 = addBox(slide, "bridge-decision", 728, 290, 74, 54, "bridge\ndecision", colors.green);
const d4 = addBox(slide, "outcome-log", 824, 290, 74, 54, "outcome\nlog", colors.orange);
connect(slide, d1, d2, colors.blue);
connect(slide, d2, d3, colors.teal);
connect(slide, d3, d4, colors.green);

addText(
  slide,
  "takeaway",
  532,
  368,
  380,
  32,
  "Takeaway: participant variability is evaluated through controlled prompts and auditable logs.",
  9,
  colors.ink,
);

const pptx = await PresentationFile.exportPptx(deck);
await pptx.save(OUT);
console.log(OUT);
