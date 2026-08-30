import fs from "node:fs/promises";
import fsSync from "node:fs";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

const W = 1280;
const H = 720;
const TOTAL_SLIDES = 14;
const COLORS = {
  ink: "#14213D",
  muted: "#667085",
  canvas: "#F6F8FF",
  surface: "#FFFFFF",
  line: "#DCE4F2",
  navy: "#10183A",
  navyDeep: "#091127",
  blue: "#4F7CFF",
  cyan: "#23C9D8",
  violet: "#8B5CF6",
  coral: "#FF6B9D",
  amber: "#F6B84B",
  teal: "#2BBBAD",
  white: "#FFFFFF",
};

const SLIDE_STYLE = {
  5: { accent: COLORS.coral, section: "DISTRIBUTION", reverse: true },
  6: { accent: COLORS.violet, section: "PERSISTENCE", reverse: false },
  7: { accent: COLORS.blue, section: "RANKING STABILITY", reverse: true },
};

function parseArgs(argv) {
  const args = { mode: "full" };
  for (let index = 0; index < argv.length; index += 1) {
    const key = argv[index];
    if (!key.startsWith("--")) throw new Error(`Unexpected argument: ${key}`);
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) {
      args[key.slice(2)] = true;
    } else {
      args[key.slice(2)] = value;
      index += 1;
    }
  }
  return args;
}

async function loadArtifactTool() {
  const candidates = [];
  if (process.env.ARTIFACT_TOOL_ENTRYPOINT) {
    candidates.push(process.env.ARTIFACT_TOOL_ENTRYPOINT);
  }
  if (process.env.ARTIFACT_TOOL_PACKAGE_DIR) {
    candidates.push(
      path.join(process.env.ARTIFACT_TOOL_PACKAGE_DIR, "dist", "node", "artifact_tool.mjs"),
      path.join(process.env.ARTIFACT_TOOL_PACKAGE_DIR, "dist", "artifact_tool.mjs"),
    );
  }
  candidates.push(
    path.join(
      os.homedir(),
      ".cache",
      "codex-runtimes",
      "codex-primary-runtime",
      "dependencies",
      "node",
      "node_modules",
      "@oai",
      "artifact-tool",
      "dist",
      "node",
      "artifact_tool.mjs",
    ),
    path.join(
      os.homedir(),
      ".cache",
      "codex-runtimes",
      "codex-primary-runtime",
      "dependencies",
      "node",
      "node_modules",
      "@oai",
      "artifact-tool",
      "dist",
      "artifact_tool.mjs",
    ),
  );
  for (const candidate of candidates) {
    if (candidate && fsSync.existsSync(candidate)) {
      return import(pathToFileURL(candidate).href);
    }
  }
  throw new Error(
    "Could not find @oai/artifact-tool. Set ARTIFACT_TOOL_PACKAGE_DIR or run inside the Codex presentation runtime.",
  );
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const root = path.resolve(args.root || path.join(import.meta.dirname, ".."));
  const output = path.resolve(
    args.output || path.join(root, "outputs", "presentation", "stablecoin_yield_presentation.pptx"),
  );
  const previewDir = path.resolve(
    args["preview-dir"] || path.join(root, "outputs", "presentation", "rendered_preview"),
  );
  const chartAssetDir = path.resolve(
    args["chart-asset-dir"] || path.join(root, "outputs", "presentation", "chart_assets"),
  );
  const { Presentation, PresentationFile } = await loadArtifactTool();
  await fs.mkdir(path.dirname(output), { recursive: true });
  await fs.rm(previewDir, { recursive: true, force: true });
  await fs.mkdir(previewDir, { recursive: true });

  const summary = JSON.parse(
    await fs.readFile(path.join(root, "outputs", "report", "report_summary.json"), "utf8"),
  );
  const slides = JSON.parse(
    await fs.readFile(
      path.join(root, "outputs", "presentation", "stablecoin_yield_slides.json"),
      "utf8",
    ),
  );
  const chartAssets = await buildChartAssets(Presentation, summary, chartAssetDir);
  const deck = Presentation.create({ slideSize: { width: W, height: H } });

  addCover(deck, summary, slides[0]);
  addResearchFrame(deck, slides[1]);
  addDataScope(deck, summary, slides[2], chartAssets.poolTypes);
  addMethods(deck, summary, slides[3]);
  addEvidence(deck, root, slides[4], "Headline APY needs robust summaries", [
    `Pool-day median APY: ${summary.market.median_apy.toFixed(2)}%`,
    `Pool-day mean APY: ${summary.market.mean_apy.toFixed(2)}%`,
    "Extreme observations are flagged and preserved",
  ], SLIDE_STYLE[5], chartAssets.distribution);
  addEvidence(deck, root, slides[5], "High yield usually behaves like a short regime", [
    `${formatInt(summary.episodes.primary_count)} episodes at or above 10% APY`,
    `Median duration: ${summary.episodes.primary_median_duration_days} days`,
    `${pct(summary.episodes.survival_points["30"].survival)} survive beyond 30 days`,
  ], SLIDE_STYLE[6], chartAssets.survival);
  addEvidence(deck, root, slides[6], "Top-yield membership changes with horizon", [
    `1 day: ${pct(summary.ranking.mean_churn_by_horizon["1"])} (n=${formatInt(summary.ranking.comparison_count_by_horizon["1"])})`,
    `7 days: ${pct(summary.ranking.mean_churn_by_horizon["7"])} (n=${formatInt(summary.ranking.comparison_count_by_horizon["7"])})`,
    `30 days: ${pct(summary.ranking.mean_churn_by_horizon["30"])} (n=${formatInt(summary.ranking.comparison_count_by_horizon["30"])})`,
  ], SLIDE_STYLE[7], null, "WEIGHTED AVERAGE");
  addMechanisms(deck, summary, slides[7], chartAssets.mechanisms);
  addEventResponse(deck, summary, slides[8], chartAssets.eventApy, chartAssets.eventTvl);
  addDepeg(deck, summary, slides[9], chartAssets.depegPrice, chartAssets.depegApy);
  addJointScreen(deck, summary, slides[10], chartAssets.jointScreen);
  addRobustness(deck, summary, slides[11], chartAssets.robustness);
  addLimitations(deck, summary, slides[12]);
  addConclusion(deck, summary, slides[13]);

  for (const [index, slide] of deck.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    await writeBlob(
      path.join(previewDir, `${stem}.png`),
      await deck.export({ slide, format: "png", scale: 1 }),
    );
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(path.join(previewDir, `${stem}.layout.json`), await layout.text());
  }
  await writeBlob(
    path.join(previewDir, "deck-montage.webp"),
    await deck.export({ format: "webp", montage: true, scale: 1 }),
  );
  const inspection = await deck.inspect({
    kind: "slide,textbox,shape,image,notes,layout",
    maxChars: 300000,
  });
  await fs.writeFile(`${output}.inspect.ndjson`, inspection.ndjson, "utf8");
  const pptx = await PresentationFile.exportPptx(deck);
  await pptx.save(output);
  console.log(`pptx=${path.relative(root, output)}`);
  console.log(`preview=${path.relative(root, previewDir)}`);
  console.log(`chart_assets=${path.relative(root, chartAssetDir)}`);
  console.log(`inspect=${path.relative(root, `${output}.inspect.ndjson`)}`);
  console.log(`mode=${args.mode}`);
}

async function buildChartAssets(Presentation, summary, outputDir) {
  await fs.rm(outputDir, { recursive: true, force: true });
  await fs.mkdir(outputDir, { recursive: true });
  const assets = {
    poolTypes: path.join(outputDir, "slide-03-pool-types.png"),
    distribution: path.join(outputDir, "slide-05-apy-distribution.png"),
    survival: path.join(outputDir, "slide-06-survival-100-days.png"),
    mechanisms: path.join(outputDir, "slide-08-apy-components.png"),
    eventApy: path.join(outputDir, "slide-09-event-apy.png"),
    eventTvl: path.join(outputDir, "slide-09-event-tvl.png"),
    depegPrice: path.join(outputDir, "slide-10-usdc-price.png"),
    depegApy: path.join(outputDir, "slide-10-exposed-apy.png"),
    jointScreen: path.join(outputDir, "slide-11-joint-screen.png"),
    robustness: path.join(outputDir, "slide-12-robustness.png"),
  };

  await renderRasterAsset(Presentation, assets.poolTypes, 630, 320, (slide) => {
    drawPoolTypeBars(slide, summary.pool_types, 630, 320);
  });
  await renderRasterAsset(Presentation, assets.distribution, 798, 374, (slide) => {
    drawApyDistributionAsset(slide, summary.market, 798, 374);
  });
  await renderRasterAsset(Presentation, assets.survival, 798, 374, (slide) => {
    drawSurvivalAsset(slide, summary.episodes, 798, 374);
  });
  await renderRasterAsset(Presentation, assets.mechanisms, 730, 326, (slide) => {
    drawMechanismBars(slide, summary.pool_type_components, 730, 326);
  });

  const eventPoints = summary.event_response.points;
  const eventDays = ["-7", "0", "7", "30"];
  const eventCategories = ["D-7", "D0", "D+7", "D+30"];
  await renderRasterAsset(Presentation, assets.eventApy, 568, 162, (slide) => {
    drawLineChartAsset(slide, 568, 162, {
      categories: eventCategories,
      values: eventDays.map((day) => Number(eventPoints[day].median_apy)),
      color: COLORS.blue,
      numberFormatCode: "0.0",
      min: 4,
      max: 20,
    });
  });
  await renderRasterAsset(Presentation, assets.eventTvl, 568, 170, (slide) => {
    drawLineChartAsset(slide, 568, 170, {
      categories: eventCategories,
      values: eventDays.map((day) => Number(eventPoints[day].median_tvl_index)),
      color: COLORS.teal,
      numberFormatCode: "0.00",
      min: 0.9,
      max: 1.8,
    });
  });

  const depegPoints = summary.depeg.points;
  const depegDays = ["-7", "-1", "0", "1", "7", "30"];
  const depegCategories = ["D-7", "D-1", "D0", "D+1", "D+7", "D+30"];
  await renderRasterAsset(Presentation, assets.depegPrice, 568, 162, (slide) => {
    drawLineChartAsset(slide, 568, 162, {
      categories: depegCategories,
      values: depegDays.map((day) => Number(depegPoints[day].price_usd)),
      color: COLORS.coral,
      numberFormatCode: "0.000",
      min: 0.95,
      max: 1.01,
    });
  });
  await renderRasterAsset(Presentation, assets.depegApy, 568, 170, (slide) => {
    drawLineChartAsset(slide, 568, 170, {
      categories: depegCategories,
      values: depegDays.map((day) => Number(depegPoints[day].median_apy)),
      color: COLORS.blue,
      numberFormatCode: "0.0",
      min: 1.5,
      max: 4.3,
    });
  });
  await renderRasterAsset(Presentation, assets.jointScreen, 770, 360, (slide) => {
    drawJointScreenAsset(slide, summary.joint_screen, 770, 360);
  });
  await renderRasterAsset(Presentation, assets.robustness, 430, 286, (slide) => {
    const rows = summary.robustness.filter((row) => row.family === "apy_threshold");
    drawRobustnessBars(slide, rows, 430, 286);
  });
  return assets;
}

async function renderRasterAsset(Presentation, outputPath, width, height, draw) {
  const presentation = Presentation.create({ slideSize: { width, height } });
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.surface;
  draw(slide);
  await writeBlob(outputPath, await presentation.export({ slide, format: "png", scale: 2 }));
  const layout = await slide.export({ format: "layout" });
  await fs.writeFile(outputPath.replace(/\.png$/u, ".layout.json"), await layout.text());
}

function drawPoolTypeBars(slide, poolTypes, width) {
  const entries = Object.entries(poolTypes).sort((a, b) => Number(a[1]) - Number(b[1]));
  const maxValue = Math.max(...entries.map(([, value]) => Number(value)));
  const labelWidth = 184;
  const barLeft = 194;
  const barWidth = width - barLeft - 58;
  entries.forEach(([name, rawValue], index) => {
    const value = Number(rawValue);
    const y = 18 + index * 58;
    addText(slide, prettyPoolType(name), 0, y + 5, labelWidth, 30, {
      fontSize: 16,
      bold: true,
      color: COLORS.ink,
      alignment: "right",
      verticalAlignment: "middle",
    });
    addPanel(slide, barLeft, y + 7, barWidth, 28, {
      fill: `${COLORS.cyan}/11`,
      radius: 10,
    });
    addPanel(slide, barLeft, y + 7, Math.max(10, (barWidth * value) / maxValue), 28, {
      fill: COLORS.cyan,
      radius: 10,
    });
    addText(slide, formatInt(value), barLeft + barWidth + 10, y + 5, 44, 30, {
      fontSize: 17,
      bold: true,
      color: COLORS.ink,
      verticalAlignment: "middle",
    });
  });
}

function drawApyDistributionAsset(slide, market, width, height) {
  const histogram = market.apy_histogram;
  const bins = histogram?.bins || [];
  if (!bins.length) throw new Error("report_summary.json does not contain market.apy_histogram");
  const plot = { left: 58, top: 58, width: width - 78, height: height - 126 };
  const maxCount = Math.max(...bins.map((row) => Number(row.count)));
  const xMin = Number(histogram.min_value);
  const xMax = Number(histogram.clip_value);
  const xScale = (value) => plot.left + (plot.width * (Number(value) - xMin)) / (xMax - xMin);

  addPill(slide, 10, 4, 192, 30, `POOL-DAY MEDIAN ${market.median_apy.toFixed(2)}%`, COLORS.teal, {
    fill: `${COLORS.teal}/13`,
    textColor: COLORS.teal,
    fontSize: 10,
  });
  addPill(slide, 212, 4, 184, 30, `POOL-DAY MEAN ${market.mean_apy.toFixed(2)}%`, COLORS.coral, {
    fill: `${COLORS.coral}/13`,
    textColor: COLORS.coral,
    fontSize: 10,
  });
  addPill(slide, 406, 4, 224, 30, `DISPLAY CAP P99 ${market.p99_apy.toFixed(2)}%`, COLORS.violet, {
    fill: `${COLORS.violet}/13`,
    textColor: COLORS.violet,
    fontSize: 10,
  });
  addText(slide, "Pool-days", plot.left, 38, 100, 18, {
    fontSize: 11,
    bold: true,
    color: COLORS.muted,
  });

  [0, 0.5, 1].forEach((fraction) => {
    const y = plot.top + plot.height - plot.height * fraction;
    addPanel(slide, plot.left, y, plot.width, 1, { fill: COLORS.line, radius: 0 });
    addText(slide, formatCompactNumber(maxCount * fraction), 2, y - 9, 48, 18, {
      fontSize: 10,
      color: COLORS.muted,
      alignment: "right",
    });
  });

  const slotWidth = plot.width / bins.length;
  bins.forEach((row, index) => {
    const barHeight = (plot.height * Number(row.count)) / maxCount;
    if (barHeight <= 0) return;
    addPanel(
      slide,
      plot.left + index * slotWidth + 1,
      plot.top + plot.height - barHeight,
      Math.max(2, slotWidth - 2),
      barHeight,
      { fill: "linear(0deg, #4F7CFF 0%, #8B5CF6 100%)", radius: 3 },
    );
  });

  addDashedVertical(slide, xScale(market.median_apy), plot.top, plot.height, COLORS.teal);
  addDashedVertical(slide, xScale(market.mean_apy), plot.top, plot.height, COLORS.coral);
  [0, 0.25, 0.5, 0.75, 1].forEach((fraction) => {
    const value = xMin + (xMax - xMin) * fraction;
    const x = xScale(value);
    addText(slide, value.toFixed(fraction === 0 ? 0 : 1), x - 24, plot.top + plot.height + 7, 48, 18, {
      fontSize: 10,
      color: COLORS.muted,
      alignment: "center",
    });
  });
  addText(
    slide,
    `Quoted APY (%) | rightmost bin includes values >= p99=${market.p99_apy.toFixed(2)}%; source extremes remain preserved`,
    96,
    height - 30,
    width - 192,
    20,
    { fontSize: 10, color: COLORS.muted, alignment: "center" },
  );
}

function drawMechanismBars(slide, components, width) {
  const labelWidth = 176;
  const barLeft = 190;
  const barWidth = width - barLeft - 54;
  const maxValue = 6;
  addLegendDot(slide, 190, 4, COLORS.blue, "Base APY", 82);
  addLegendDot(slide, 302, 4, COLORS.coral, "Reward APY", 96);
  addText(slide, "Median APY (%)", width - 140, 3, 136, 22, {
    fontSize: 12,
    bold: true,
    color: COLORS.muted,
    alignment: "right",
  });
  [0, 2, 4, 6].forEach((tick) => {
    const x = barLeft + (barWidth * tick) / maxValue;
    addLine(slide, x, 28, 1, 274, COLORS.line);
    addText(slide, tick.toFixed(0), x - 12, 303, 24, 18, {
      fontSize: 11,
      color: COLORS.muted,
      alignment: "center",
    });
  });
  components.forEach((item, index) => {
    const y = 34 + index * 53;
    const base = Number(item.median_base_apy);
    const reward = Number(item.median_reward_apy);
    addText(slide, prettyPoolType(item.pool_type), 0, y + 5, labelWidth, 36, {
      fontSize: 15,
      bold: true,
      color: COLORS.ink,
      alignment: "right",
      verticalAlignment: "middle",
    });
    const baseWidth = Math.max(4, (barWidth * base) / maxValue);
    addPanel(slide, barLeft, y + 5, baseWidth, 14, { fill: COLORS.blue, radius: 7 });
    addText(slide, base.toFixed(2), barLeft + baseWidth + 7, y + 1, 42, 21, {
      fontSize: 12,
      bold: true,
      color: COLORS.blue,
    });
    if (reward > 0) {
      const rewardWidth = Math.max(4, (barWidth * reward) / maxValue);
      addPanel(slide, barLeft, y + 25, rewardWidth, 14, { fill: COLORS.coral, radius: 7 });
      addText(slide, reward.toFixed(2), barLeft + rewardWidth + 7, y + 21, 42, 21, {
        fontSize: 12,
        bold: true,
        color: COLORS.coral,
      });
    }
  });
}

function drawLineChartAsset(slide, width, height, options) {
  slide.charts.add("line", {
    position: { left: 0, top: 0, width, height },
    categories: options.categories,
    series: [
      {
        name: "Observed median",
        values: options.values,
        line: { style: "solid", fill: options.color, width: 3 },
        marker: { symbol: "circle", size: 7 },
      },
    ],
    lineOptions: { grouping: "standard", smooth: false },
    hasLegend: false,
    xAxis: {
      textStyle: { fill: COLORS.muted, fontSize: 11 },
      line: { style: "solid", fill: COLORS.line, width: 1 },
      majorGridlines: null,
    },
    yAxis: {
      numberFormatCode: options.numberFormatCode,
      textStyle: { fill: COLORS.muted, fontSize: 10 },
      majorGridlines: { style: "solid", fill: COLORS.line, width: 1 },
      min: options.min,
      max: options.max,
    },
    dataLabels: {
      showValue: false,
      showSeriesName: false,
      showCategoryName: false,
    },
    chartFill: "transparent",
    chartLine: { style: "solid", fill: "transparent", width: 0 },
    plotAreaFill: "transparent",
    plotAreaLine: { style: "solid", fill: "transparent", width: 0 },
  });
}

function drawSurvivalAsset(slide, episodes, width, height) {
  const curve = episodes.survival_curve || [];
  if (!curve.length) throw new Error("report_summary.json does not contain episodes.survival_curve");
  const firstHundred = curve.filter((row) => Number(row.duration_days) <= 100);
  const longTail = curve.filter((row) => Number(row.duration_days) >= 95);
  const day2 = episodes.survival_points["2"]?.survival;
  const day30 = episodes.survival_points["30"]?.survival;
  const tailEnd = curve.at(-1).duration_days;

  slide.charts.add("scatter", {
    position: { left: 0, top: 34, width, height: height - 34 },
    series: [
      {
        name: "Kaplan-Meier estimate",
        xValues: firstHundred.map((row) => Number(row.duration_days)),
        values: firstHundred.map((row) => Number(row.survival)),
        line: { style: "solid", fill: COLORS.violet, width: 4 },
        marker: { symbol: "none", size: 0 },
      },
    ],
    scatterOptions: { style: "line" },
    hasLegend: false,
    xAxis: {
      min: 0,
      max: 100,
      majorUnit: 20,
      title: { text: "Episode duration (days)", textStyle: { fill: COLORS.muted, fontSize: 12 } },
      textStyle: { fill: COLORS.muted, fontSize: 11 },
      majorGridlines: { style: "solid", fill: COLORS.line, width: 1 },
    },
    yAxis: {
      min: 0,
      max: 1,
      majorUnit: 0.2,
      numberFormatCode: "0%",
      textStyle: { fill: COLORS.muted, fontSize: 11 },
      majorGridlines: { style: "solid", fill: COLORS.line, width: 1 },
    },
    dataLabels: { showValue: false, showSeriesName: false, showCategoryName: false },
    chartFill: "transparent",
    chartLine: { style: "solid", fill: "transparent", width: 0 },
    plotAreaFill: "transparent",
    plotAreaLine: { style: "solid", fill: "transparent", width: 0 },
  });

  addPill(slide, 12, 2, 138, 28, "FIRST 100 DAYS", COLORS.violet, {
    fill: `${COLORS.violet}/13`,
    textColor: COLORS.violet,
    fontSize: 11,
  });
  addPill(slide, 160, 2, 198, 28, `SURVIVAL AT DAY 2: ${pct(day2)}`, COLORS.coral, {
    fill: `${COLORS.coral}/13`,
    textColor: COLORS.coral,
    fontSize: 11,
  });
  addPill(slide, 368, 2, 206, 28, `SURVIVAL AT DAY 30: ${pct(day30)}`, COLORS.blue, {
    fill: `${COLORS.blue}/13`,
    textColor: COLORS.blue,
    fontSize: 11,
  });

  addPanel(slide, 574, 52, 208, 128, {
    fill: "#FFFFFF/96",
    line: COLORS.line,
    radius: 14,
    shadow: "shadow-sm",
  });
  addText(slide, `LONG TAIL | to ${formatInt(tailEnd)}d`, 588, 58, 178, 18, {
    fontSize: 10,
    bold: true,
    color: COLORS.cyan,
    alignment: "center",
  });
  const inset = { left: 600, top: 82, width: 166, height: 72 };
  const insetX = (value) => inset.left + (inset.width * (Number(value) - 95)) / (630 - 95);
  const insetY = (value) => inset.top + inset.height - (inset.height * Number(value)) / 0.02;
  [0, 0.01, 0.02].forEach((tick) => {
    const y = insetY(tick);
    addPanel(slide, inset.left, y, inset.width, 1, { fill: COLORS.line, radius: 0 });
    addText(slide, `${(tick * 100).toFixed(0)}%`, 578, y - 7, 18, 14, {
      fontSize: 7,
      color: COLORS.muted,
      alignment: "right",
    });
  });
  for (let index = 1; index < longTail.length; index += 1) {
    const previous = longTail[index - 1];
    const current = longTail[index];
    const x1 = insetX(previous.duration_days);
    const x2 = insetX(current.duration_days);
    const y1 = insetY(previous.survival);
    const y2 = insetY(current.survival);
    addPanel(slide, x1, y1, Math.max(1, x2 - x1), 2, { fill: COLORS.cyan, radius: 0 });
    addPanel(slide, x2, Math.min(y1, y2), 2, Math.max(1, Math.abs(y2 - y1)), {
      fill: COLORS.cyan,
      radius: 0,
    });
  }
  addText(slide, "100d", 600, 158, 40, 14, {
    fontSize: 8,
    color: COLORS.muted,
  });
  addText(slide, `${formatInt(tailEnd)}d`, 726, 158, 40, 14, {
    fontSize: 8,
    color: COLORS.muted,
    alignment: "right",
  });
}

function drawJointScreenAsset(slide, screen, width, height) {
  const plot = { left: 60, top: 30, width: width - 86, height: height - 90 };
  const xMax = 28;
  const yMax = 1;
  const xScale = (value) => plot.left + (plot.width * clamp(Number(value), 0, xMax)) / xMax;
  const yScale = (value) => plot.top + plot.height - (plot.height * clamp(Number(value), 0, yMax)) / yMax;

  [0, 7, 14, 21, 28].forEach((tick) => {
    const x = xScale(tick);
    addLine(slide, x, plot.top, 1, plot.height, COLORS.line);
    addText(slide, tick.toFixed(0), x - 16, plot.top + plot.height + 5, 32, 18, {
      fontSize: 10,
      color: COLORS.muted,
      alignment: "center",
    });
  });
  [0, 0.25, 0.5, 0.75, 1].forEach((tick) => {
    const y = yScale(tick);
    addLine(slide, plot.left, y, plot.width, 1, COLORS.line);
    addText(slide, `${(tick * 100).toFixed(0)}%`, 8, y - 9, 44, 18, {
      fontSize: 10,
      color: COLORS.muted,
      alignment: "right",
    });
  });

  const thresholdX = xScale(screen.median_apy);
  const thresholdY = yScale(screen.median_persistence);
  addDashedVertical(slide, thresholdX, plot.top, plot.height, COLORS.coral);
  addDashedHorizontal(slide, plot.left, thresholdY, plot.width, COLORS.violet);

  const allBubbleSizes = screen.series.flatMap((series) => series.bubble.map(Number));
  const bubbleCap = quantile(allBubbleSizes, 0.95) || 1;
  const drawSeries = (series, fill, line, baseRadius) => {
    series.x.forEach((xValue, index) => {
      const bubble = Math.min(Number(series.bubble[index]), bubbleCap);
      const radius = baseRadius + 6 * Math.sqrt(Math.max(bubble, 0) / bubbleCap);
      addChartPoint(slide, xScale(xValue), yScale(series.y[index]), radius, fill, line);
    });
  };
  drawSeries(screen.series[1], "#A8B4C7/66", "#FFFFFF/70", 2);
  drawSeries(screen.series[0], COLORS.coral, COLORS.white, 2.5);

  addText(slide, "Persistence: share of observed days with APY >= 10%", plot.left, 2, 330, 22, {
    fontSize: 11,
    bold: true,
    color: COLORS.muted,
  });
  addLegendDot(slide, 458, 2, "#A8B4C7", "Other pools", 82);
  addLegendDot(slide, 572, 2, COLORS.coral, "Clears all thresholds", 150);
  addText(slide, "Median APY (%)", plot.left + plot.width / 2 - 70, height - 26, 140, 20, {
    fontSize: 11,
    bold: true,
    color: COLORS.muted,
    alignment: "center",
  });
  addPill(slide, Math.min(thresholdX + 8, 180), 36, 152, 23, `POOL APY ${Number(screen.median_apy).toFixed(2)}%`, COLORS.coral, {
    fill: "#FFFFFF/94",
    textColor: COLORS.coral,
    fontSize: 9,
  });
  addPill(slide, width - 194, thresholdY - 28, 170, 23, `PERSISTENCE ${pct(screen.median_persistence)}`, COLORS.violet, {
    fill: "#FFFFFF/94",
    textColor: COLORS.violet,
    fontSize: 9,
  });
  addText(slide, "Bubble area = median TVL, capped at p95", width - 250, height - 24, 238, 18, {
    fontSize: 9,
    color: COLORS.muted,
    alignment: "right",
  });
}

function drawRobustnessBars(slide, rows, width, height) {
  const sorted = [...rows].sort((a, b) => Number(a.threshold_percent) - Number(b.threshold_percent));
  const plot = { left: 48, top: 34, width: width - 66, height: height - 84 };
  const maxValue = 4000;
  [0, 2000, 4000].forEach((tick) => {
    const y = plot.top + plot.height - (plot.height * tick) / maxValue;
    addLine(slide, plot.left, y, plot.width, 1, COLORS.line);
    addText(slide, tick === 0 ? "0" : `${tick / 1000}k`, 4, y - 9, 34, 18, {
      fontSize: 10,
      color: COLORS.muted,
      alignment: "right",
    });
  });
  addText(slide, "Episode count", 4, 3, 110, 20, {
    fontSize: 11,
    bold: true,
    color: COLORS.muted,
  });
  sorted.forEach((row, index) => {
    const center = plot.left + ((index + 0.5) * plot.width) / sorted.length;
    const value = Number(row.episode_count);
    const barHeight = (plot.height * value) / maxValue;
    addPanel(slide, center - 34, plot.top + plot.height - barHeight, 68, barHeight, {
      fill: COLORS.violet,
      radius: 12,
    });
    addText(slide, formatInt(value), center - 48, plot.top + plot.height - barHeight - 27, 96, 22, {
      fontSize: 14,
      bold: true,
      color: COLORS.ink,
      alignment: "center",
    });
    addText(slide, `${Number(row.threshold_percent).toFixed(0)}% APY`, center - 48, plot.top + plot.height + 8, 96, 22, {
      fontSize: 12,
      bold: true,
      color: COLORS.muted,
      alignment: "center",
    });
  });
}

function addLegendDot(slide, left, top, color, label, labelWidth = 150) {
  addChartPoint(slide, left + 7, top + 8, 6, color, COLORS.white);
  addText(slide, label, left + 19, top, labelWidth, 18, {
    fontSize: 10,
    bold: true,
    color: COLORS.muted,
    verticalAlignment: "middle",
  });
}

function addChartPoint(slide, x, y, radius, fill, line) {
  slide.shapes.add({
    geometry: "ellipse",
    position: { left: x - radius, top: y - radius, width: radius * 2, height: radius * 2 },
    fill,
    line: { style: "solid", fill: line, width: 0.7 },
  });
}

function addDashedVertical(slide, x, top, height, color) {
  for (let offset = 0; offset < height; offset += 11) {
    addPanel(slide, x, top + offset, 2, Math.min(6, height - offset), {
      fill: color,
      radius: 0,
    });
  }
}

function addDashedHorizontal(slide, left, y, width, color) {
  for (let offset = 0; offset < width; offset += 11) {
    addPanel(slide, left + offset, y, Math.min(6, width - offset), 2, {
      fill: color,
      radius: 0,
    });
  }
}

function quantile(values, probability) {
  const sorted = values.filter(Number.isFinite).sort((a, b) => a - b);
  if (!sorted.length) return 0;
  return sorted[Math.floor((sorted.length - 1) * probability)];
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function addCover(deck, summary, slideData) {
  const slide = deck.slides.add();
  slide.background.fill = "linear(135deg, #091127 0%, #172B66 58%, #5B3CC4 100%)";
  addPanel(slide, 0, 0, W, 12, {
    fill: "linear(0deg, #23C9D8 0%, #4F7CFF 48%, #FF6B9D 100%)",
    radius: 0,
  });
  addPill(slide, 54, 48, 294, 38, "DATA VISUALIZATION / DEFI", COLORS.cyan, {
    fill: "#FFFFFF/12",
    textColor: COLORS.white,
    fontSize: 14,
  });
  addText(slide, "Stablecoin Yield", 54, 126, 660, 94, {
    fontSize: 72,
    bold: true,
    color: COLORS.white,
    name: "cover-title",
  });
  addText(
    slide,
    "The price of yield: persistence, mechanisms and TVL response in stablecoin DeFi",
    56,
    230,
    635,
    84,
    { fontSize: 28, color: "#DDE6FF" },
  );
  addPanel(slide, 54, 342, 620, 116, {
    fill: "#FFFFFF/10",
    line: "#FFFFFF/16",
    radius: 26,
  });
  addText(slide, "CENTRAL CLAIM", 82, 366, 200, 24, {
    fontSize: 14,
    bold: true,
    color: COLORS.cyan,
  });
  addText(
    slide,
    "Stablecoin APY becomes interpretable only when duration, TVL, mechanism and peg context are shown together.",
    82,
    399,
    554,
    52,
    { fontSize: 22, color: COLORS.white },
  );

  addPanel(slide, 746, 76, 472, 500, {
    fill: "#FFFFFF/11",
    line: "#FFFFFF/18",
    radius: 34,
    shadow: "shadow-lg",
  });
  addText(slide, "Evidence snapshot", 782, 110, 360, 40, {
    fontSize: 26,
    bold: true,
    color: COLORS.white,
  });
  addText(slide, "A compact view of the analytical scale", 782, 154, 360, 30, {
    fontSize: 17,
    color: "#DDE6FF",
  });
  addLine(slide, 782, 205, 400, 1, "#FFFFFF/20");
  addLine(slide, 982, 218, 1, 302, "#FFFFFF/16");
  addLine(slide, 782, 366, 400, 1, "#FFFFFF/16");
  addMetricCell(slide, 792, 232, `${summary.market.pool_count}`, "POOLS", COLORS.cyan);
  addMetricCell(
    slide,
    1008,
    232,
    `${Math.round(summary.market.pool_day_count / 1000)}k`,
    "POOL-DAYS",
    COLORS.coral,
  );
  addMetricCell(
    slide,
    792,
    392,
    `${summary.market.median_apy.toFixed(1)}%`,
    "POOL-DAY MEDIAN APY",
    COLORS.amber,
  );
  addMetricCell(
    slide,
    1008,
    392,
    `${summary.episodes.primary_median_duration_days}`,
    "MEDIAN EPISODE DURATION",
    COLORS.cyan,
  );
  addText(slide, "Yield as a regime, not a ranking.", 56, 524, 620, 38, {
    fontSize: 24,
    bold: true,
    color: COLORS.coral,
  });
  addText(slide, "Educational analysis only. No financial advice, no pool ranking.", 56, 636, 720, 28, {
    fontSize: 16,
    color: "#C7D2FE",
  });
  addText(slide, `01 / ${TOTAL_SLIDES}`, 1110, 636, 106, 28, {
    fontSize: 16,
    bold: true,
    color: COLORS.white,
    alignment: "right",
  });
  setSpeakerNotes(slide, slideData);
}

function addResearchFrame(deck, slideData) {
  const slide = baseLightSlide(deck, 2, slideData, COLORS.violet, "RESEARCH FRAME");
  addText(slide, "Yield is a regime, not a rank", 44, 86, 900, 60, {
    fontSize: 44,
    bold: true,
  });
  addText(
    slide,
    "Five questions turn a volatile pool universe into evidence that can be defended without making recommendations.",
    44,
    148,
    1010,
    42,
    { fontSize: 21, color: COLORS.muted },
  );

  addPanel(slide, 44, 214, 410, 390, {
    fill: "linear(145deg, #4F7CFF 0%, #6B63E8 58%, #8B5CF6 100%)",
    radius: 30,
    shadow: "shadow-md",
  });
  addText(slide, "ONE ANALYTICAL GRAIN", 76, 248, 300, 24, {
    fontSize: 14,
    bold: true,
    color: "#DDE6FF",
  });
  addText(slide, "POOL × DAY", 76, 292, 330, 64, {
    fontSize: 48,
    bold: true,
    color: COLORS.white,
  });
  addText(
    slide,
    "Each observation connects yield level, capacity, mechanism and market context at a defensible temporal resolution.",
    76,
    380,
    318,
    100,
    { fontSize: 21, color: COLORS.white },
  );
  addLine(slide, 76, 506, 318, 2, "#FFFFFF/28");
  addText(
    slide,
    "Boundary: APY is quoted annualized APY. TVL change is an observed proxy, not direct wallet-level flow.",
    76,
    526,
    318,
    58,
    { fontSize: 16, color: "#E9E7FF" },
  );

  addPanel(slide, 492, 214, 742, 390, {
    fill: COLORS.surface,
    line: COLORS.line,
    radius: 30,
    shadow: "shadow-sm",
  });
  const questions = [
    "How long do episodes at or above 10% APY last?",
    "Which mechanisms explain headline APY?",
    "How stable are top-yield rankings?",
    "What changes during peg stress?",
    "Which pools clear all three thresholds?",
  ];
  const accents = [COLORS.violet, COLORS.cyan, COLORS.blue, COLORS.coral, COLORS.teal];
  questions.forEach((question, index) => {
    const y = 232 + index * 70;
    addPill(slide, 522, y + 10, 52, 38, String(index + 1).padStart(2, "0"), accents[index], {
      fill: `${accents[index]}/14`,
      textColor: accents[index],
      fontSize: 15,
    });
    addText(slide, question, 596, y + 8, 580, 42, { fontSize: 20, bold: index === 0 });
    if (index < questions.length - 1) {
      addLine(slide, 522, y + 65, 674, 1, COLORS.line);
    }
  });
}

function addDataScope(deck, summary, slideData, chartAsset) {
  const accent = COLORS.cyan;
  const slide = baseLightSlide(deck, 3, slideData, accent, "DATA SCOPE");
  addText(slide, "The sample is broad, but deliberately selected", 44, 80, 1020, 60, {
    fontSize: 40,
    bold: true,
  });
  addText(
    slide,
    `${summary.market.date_min} to ${summary.market.date_max} | ${formatInt(summary.market.pool_day_count)} pool-days | unbalanced panel`,
    44,
    140,
    1060,
    30,
    { fontSize: 18, color: COLORS.muted },
  );

  addPanel(slide, 44, 188, 692, 424, {
    fill: COLORS.surface,
    line: COLORS.line,
    radius: 26,
    shadow: "shadow-sm",
  });
  addText(slide, "Selected pools by analytical type", 72, 210, 500, 34, {
    fontSize: 24,
    bold: true,
  });
  addImage(slide, chartAsset, 70, 252, 630, 320, "Selected pools by analytical type");

  addPanel(slide, 770, 188, 464, 424, {
    fill: `linear(145deg, ${accent}/15 0%, #FFFFFF 78%)`,
    line: `${accent}/28`,
    radius: 26,
    shadow: "shadow-sm",
  });
  addPill(slide, 798, 212, 188, 32, "SELECTION LOGIC", accent, {
    fill: `${accent}/15`,
    textColor: accent,
    fontSize: 13,
  });
  const selectionRows = [
    {
      label: "Eligibility",
      body: "Stablecoin pool, TVL >= USD 1M, at least 180 provider history observations.",
    },
    {
      label: "Cap of 250",
      body: "70% highest TVL; remaining capacity highest current APY. No random sampling claim.",
    },
    {
      label: "Entry and exit",
      body: "Observed pool-specific dates only. No synthetic backfill or balanced-panel imputation.",
    },
  ];
  selectionRows.forEach((item, index) => {
    const y = 266 + index * 88;
    addText(slide, item.label, 800, y, 132, 28, {
      fontSize: 17,
      bold: true,
      color: COLORS.ink,
    });
    addText(slide, item.body, 944, y - 2, 254, 58, {
      fontSize: 16,
      color: COLORS.ink,
    });
    if (index < selectionRows.length - 1) {
      addLine(slide, 800, y + 68, 398, 1, `${accent}/24`);
    }
  });
  addPanel(slide, 798, 532, 398, 54, { fill: "#FFFFFF/72", line: COLORS.line, radius: 16 });
  addText(slide, "Data quality", 814, 545, 110, 24, { fontSize: 15, bold: true });
  addText(slide, "26 missing TVL rows | 32 APY > 1,000% flagged, not hidden", 930, 545, 250, 28, {
    fontSize: 13,
    color: COLORS.muted,
  });
}

function addMethods(deck, summary, slideData) {
  const accent = COLORS.blue;
  const slide = baseLightSlide(deck, 4, slideData, accent, "METHODS");
  addText(slide, "Four definitions make the analysis auditable", 44, 80, 1020, 60, {
    fontSize: 40,
    bold: true,
  });
  addText(
    slide,
    "Each result has an explicit threshold, comparison window and interpretation boundary.",
    44,
    140,
    1040,
    30,
    { fontSize: 18, color: COLORS.muted },
  );

  addPanel(slide, 44, 188, 1190, 424, {
    fill: COLORS.surface,
    line: COLORS.line,
    radius: 28,
    shadow: "shadow-sm",
  });
  const methodRows = [
    {
      number: "01",
      title: "High-yield episode",
      body: `APY at or above ${summary.methodology.episode.threshold_percent.toFixed(0)}%; contiguous observed run; one missing calendar day tolerated; active runs right-censored.`,
      boundary: "Kaplan-Meier retains censored episodes.",
      color: COLORS.violet,
    },
    {
      number: "02",
      title: "Ranking churn",
      body: "1 - intersection share of top-k sets at t and t+h; k = 10 or 20; h = 1, 7 or 30 days.",
      boundary: "Stability diagnostic, not a leaderboard.",
      color: COLORS.blue,
    },
    {
      number: "03",
      title: "APY-jump event",
      body: "Daily APY increase of at least 5 percentage points and level at or above 10%; maximum 3 events per pool; window -7 to +30 days.",
      boundary: `${summary.event_response.event_count_max} events at day 0; TVL remains observational.`,
      color: COLORS.amber,
    },
    {
      number: "04",
      title: "Joint threshold screen",
      body: "Above the sample medians for pool-level APY, persistence and TVL at the same time.",
      boundary: "Descriptive three-threshold screen; not a Pareto frontier.",
      color: COLORS.teal,
    },
  ];
  methodRows.forEach((item, index) => {
    const y = 210 + index * 94;
    addPill(slide, 72, y + 6, 58, 40, item.number, item.color, {
      fill: `${item.color}/15`,
      textColor: item.color,
      fontSize: 15,
    });
    addText(slide, item.title, 154, y, 260, 30, { fontSize: 21, bold: true });
    addText(slide, item.body, 430, y - 2, 470, 56, { fontSize: 16 });
    addText(slide, item.boundary, 930, y - 2, 260, 56, {
      fontSize: 15,
      bold: true,
      color: item.color,
    });
    if (index < methodRows.length - 1) {
      addLine(slide, 72, y + 72, 1118, 1, COLORS.line);
    }
  });
}

function addEvidence(
  deck,
  root,
  slideData,
  title,
  bullets,
  style,
  visualOverride = null,
  insightLabel = "WHAT THE CHART SAYS",
) {
  const slide = baseLightSlide(deck, slideData.slide, slideData, style.accent, style.section);
  addText(slide, title, 44, 80, 1120, 60, { fontSize: 40, bold: true });
  addText(slide, slideData.question, 44, 140, 980, 30, {
    fontSize: 18,
    color: COLORS.muted,
  });

  const chartX = style.reverse ? 400 : 44;
  const insightX = style.reverse ? 44 : 906;
  const chartWidth = 834;
  const insightWidth = 328;
  const contentTop = 186;
  const contentHeight = 426;

  addPanel(slide, chartX, contentTop, chartWidth, contentHeight, {
    fill: COLORS.surface,
    line: COLORS.line,
    radius: 26,
    shadow: "shadow-sm",
  });
  addPanel(slide, chartX + 22, contentTop + 18, 86, 6, {
    fill: `linear(0deg, ${style.accent} 0%, ${COLORS.cyan} 100%)`,
    radius: 6,
  });
  const visualPath = visualOverride || (slideData.visual ? path.join(root, slideData.visual) : null);
  if (visualPath) {
    addImage(
      slide,
      visualPath,
      chartX + 18,
      contentTop + 34,
      chartWidth - 36,
      contentHeight - 52,
      slideData.title,
    );
  }

  addPanel(slide, insightX, contentTop, insightWidth, contentHeight, {
    fill: `linear(145deg, ${style.accent}/17 0%, #FFFFFF 74%)`,
    line: `${style.accent}/28`,
    radius: 26,
    shadow: "shadow-sm",
  });
  addPill(slide, insightX + 24, contentTop + 22, 182, 32, insightLabel, style.accent, {
    fill: `${style.accent}/15`,
    textColor: style.accent,
    fontSize: 13,
  });
  addText(slide, slideData.takeaway, insightX + 24, contentTop + 74, insightWidth - 48, 122, {
    fontSize: 23,
    bold: true,
    color: COLORS.ink,
  });
  addLine(slide, insightX + 24, contentTop + 210, insightWidth - 48, 1, `${style.accent}/30`);
  bullets.forEach((bullet, index) => {
    const y = contentTop + 232 + index * 58;
    addPanel(slide, insightX + 26, y + 8, 10, 10, {
      fill: style.accent,
      radius: 10,
    });
    addText(slide, bullet, insightX + 50, y, insightWidth - 72, 48, {
      fontSize: 17,
      color: COLORS.ink,
    });
  });
  addText(
    slide,
    "Source: DeFiLlama, CoinGecko fallback checks and protocol documentation. APY is quoted, not realized return.",
    44,
    628,
    1060,
    22,
    { fontSize: 11, color: COLORS.muted },
  );
}

function addMechanisms(deck, summary, slideData, chartAsset) {
  const accent = COLORS.teal;
  const slide = baseLightSlide(deck, 8, slideData, accent, "MECHANISMS");
  addText(slide, "Mechanism changes what headline APY means", 44, 80, 1050, 60, {
    fontSize: 40,
    bold: true,
  });
  addText(slide, slideData.question, 44, 140, 940, 30, {
    fontSize: 18,
    color: COLORS.muted,
  });

  addPanel(slide, 44, 186, 790, 426, {
    fill: COLORS.surface,
    line: COLORS.line,
    radius: 26,
    shadow: "shadow-sm",
  });
  addText(slide, "Median APY components by pool type", 72, 208, 560, 32, {
    fontSize: 23,
    bold: true,
  });
  addImage(slide, chartAsset, 70, 248, 730, 326, "Median APY components by pool type");

  addPanel(slide, 860, 186, 374, 426, {
    fill: `linear(145deg, ${accent}/18 0%, #FFFFFF 78%)`,
    line: `${accent}/28`,
    radius: 26,
    shadow: "shadow-sm",
  });
  addPill(slide, 886, 210, 184, 32, "INTERPRETATION", accent, {
    fill: `${accent}/15`,
    textColor: accent,
    fontSize: 13,
  });
  addText(slide, "Components prevent false equivalence", 886, 264, 302, 66, {
    fontSize: 25,
    bold: true,
  });
  addLine(slide, 886, 348, 302, 1, `${accent}/28`);
  addMetricRow(slide, 888, 374, "90.3%", "Base APY coverage", COLORS.blue);
  addMetricRow(slide, 888, 440, "61.6%", "Reward APY coverage", COLORS.coral);
  addText(
    slide,
    "Reward-heavy pools and lending pools should not be read as the same yield mechanism.",
    888,
    514,
    296,
    72,
    { fontSize: 17, color: COLORS.ink },
  );
  addSourceNote(slide);
}

function addEventResponse(deck, summary, slideData, apyChartAsset, tvlChartAsset) {
  const accent = COLORS.amber;
  const slide = baseLightSlide(deck, 9, slideData, accent, "EVENT STUDY");
  addText(slide, "APY falls faster than TVL responds", 44, 80, 1020, 60, {
    fontSize: 40,
    bold: true,
  });
  addText(slide, slideData.question, 44, 140, 920, 30, {
    fontSize: 18,
    color: COLORS.muted,
  });
  addPanel(slide, 44, 186, 808, 198, {
    fill: COLORS.surface,
    line: COLORS.line,
    radius: 24,
    shadow: "shadow-sm",
  });
  addText(slide, "Median quoted\nAPY", 70, 204, 170, 54, { fontSize: 21, bold: true });
  addImage(slide, apyChartAsset, 252, 198, 568, 162, "Median quoted APY around APY jumps");

  addPanel(slide, 44, 404, 808, 208, {
    fill: COLORS.surface,
    line: COLORS.line,
    radius: 24,
    shadow: "shadow-sm",
  });
  addText(slide, "Median normalized\nTVL", 70, 424, 170, 54, { fontSize: 21, bold: true });
  addImage(slide, tvlChartAsset, 252, 416, 568, 170, "Median normalized TVL around APY jumps");

  addPanel(slide, 880, 186, 354, 426, {
    fill: `linear(145deg, ${accent}/20 0%, #FFFFFF 80%)`,
    line: `${accent}/30`,
    radius: 26,
    shadow: "shadow-sm",
  });
  addPill(slide, 906, 210, 176, 32, "OBSERVED RESULT", accent, {
    fill: `${accent}/18`,
    textColor: "#A76500",
    fontSize: 13,
  });
  addText(slide, "18.24% → 8.33%", 906, 266, 286, 48, {
    fontSize: 30,
    bold: true,
    color: COLORS.ink,
  });
  addText(slide, "Median APY from event day to day 30", 906, 318, 284, 46, {
    fontSize: 16,
    color: COLORS.muted,
  });
  addLine(slide, 906, 382, 282, 1, `${accent}/32`);
  addMetricRow(slide, 908, 406, "453", "Events observed at day 0", COLORS.amber);
  addMetricRow(slide, 908, 472, "1.69x", "Median normalized TVL at day 30", COLORS.teal);
  addText(
    slide,
    "Observed TVL response, not a causal capital-flow estimate.",
    908,
    548,
    278,
    48,
    { fontSize: 16, bold: true, color: COLORS.coral },
  );
  addText(slide, "Trigger: 1-day APY increase of at least 5 pp and APY at or above 10%; max 3 events per pool.", 44, 628, 1010, 22, {
    fontSize: 11,
    color: COLORS.muted,
  });
}

function addDepeg(deck, summary, slideData, priceChartAsset, apyChartAsset) {
  const accent = COLORS.coral;
  const slide = baseLightSlide(deck, 10, slideData, accent, "PEG STRESS");
  addText(slide, "Peg stress changes the denominator behind yield", 44, 80, 1080, 60, {
    fontSize: 40,
    bold: true,
  });
  addText(slide, slideData.question, 44, 140, 940, 30, {
    fontSize: 18,
    color: COLORS.muted,
  });
  addPanel(slide, 44, 186, 808, 198, {
    fill: COLORS.surface,
    line: COLORS.line,
    radius: 24,
    shadow: "shadow-sm",
  });
  addText(slide, "USDC price", 70, 204, 170, 30, { fontSize: 21, bold: true });
  addImage(slide, priceChartAsset, 252, 198, 568, 162, "USDC price around the selected stress date");

  addPanel(slide, 44, 404, 808, 208, {
    fill: COLORS.surface,
    line: COLORS.line,
    radius: 24,
    shadow: "shadow-sm",
  });
  addText(slide, "Median exposed-pool\nAPY (%)", 70, 424, 170, 54, { fontSize: 21, bold: true });
  addImage(slide, apyChartAsset, 252, 416, 568, 170, "Median exposed-pool APY around the selected stress date");

  addPanel(slide, 880, 186, 354, 426, {
    fill: `linear(145deg, ${accent}/20 0%, #FFFFFF 80%)`,
    line: `${accent}/30`,
    radius: 26,
    shadow: "shadow-sm",
  });
  addPill(slide, 906, 210, 178, 32, "USDC / 12 MAR 2023", accent, {
    fill: `${accent}/17`,
    textColor: accent,
    fontSize: 12,
  });
  addText(slide, "$0.9611", 906, 266, 286, 48, {
    fontSize: 34,
    bold: true,
  });
  addText(slide, "Minimum observed USDC price", 906, 318, 282, 42, {
    fontSize: 16,
    color: COLORS.muted,
  });
  addLine(slide, 906, 382, 282, 1, `${accent}/32`);
  addMetricRow(
    slide,
    908,
    406,
    `+${summary.depeg.apy_change_pp_day_minus_1_to_0.toFixed(2)} pp`,
    "Median APY, day -1 to day 0",
    COLORS.coral,
  );
  addMetricRow(slide, 908, 480, `${summary.depeg.max_pool_count}`, "Exposed pools in the window", COLORS.blue);
  addText(
    slide,
    "One reviewed case study; descriptive context, not a general depeg causal estimate.",
    908,
    548,
    278,
    50,
    { fontSize: 15, bold: true, color: COLORS.ink },
  );
  addSourceNote(slide);
}

function addJointScreen(deck, summary, slideData, chartAsset) {
  const accent = COLORS.violet;
  const slide = baseLightSlide(deck, 11, slideData, accent, "JOINT SCREEN");
  addText(slide, "Only 15.2% clear all three descriptive thresholds", 44, 80, 1120, 60, {
    fontSize: 40,
    bold: true,
  });
  addText(slide, slideData.question, 44, 140, 940, 30, {
    fontSize: 18,
    color: COLORS.muted,
  });

  addPanel(slide, 44, 186, 330, 426, {
    fill: `linear(145deg, ${accent}/20 0%, #FFFFFF 78%)`,
    line: `${accent}/30`,
    radius: 26,
    shadow: "shadow-sm",
  });
  addPill(slide, 68, 210, 190, 32, "THREE-MEDIAN SCREEN", accent, {
    fill: `${accent}/16`,
    textColor: accent,
    fontSize: 12,
  });
  addText(slide, "38 of 250 pools", 68, 266, 258, 48, {
    fontSize: 31,
    bold: true,
  });
  addText(slide, "clear APY, persistence and TVL thresholds simultaneously", 68, 318, 258, 72, {
    fontSize: 18,
    color: COLORS.ink,
  });
  addLine(slide, 68, 412, 258, 1, `${accent}/30`);
  addMetricRow(slide, 70, 438, `${summary.joint_screen.median_apy.toFixed(2)}%`, "Pool-level median APY threshold", COLORS.coral);
  addMetricRow(slide, 70, 496, pct(summary.joint_screen.median_persistence), "Persistence threshold", COLORS.violet);
  addText(slide, "Bubble size = median TVL. This is not a Pareto frontier.", 70, 558, 250, 38, {
    fontSize: 14,
    bold: true,
    color: COLORS.muted,
  });

  addPanel(slide, 400, 186, 834, 426, {
    fill: COLORS.surface,
    line: COLORS.line,
    radius: 26,
    shadow: "shadow-sm",
  });
  addImage(slide, chartAsset, 430, 210, 770, 360, "Joint APY and persistence threshold screen");
  addSourceNote(slide);
}

function addRobustness(deck, summary, slideData, chartAsset) {
  const accent = COLORS.violet;
  const slide = baseLightSlide(deck, 12, slideData, accent, "ROBUSTNESS");
  addText(slide, "The main duration result survives alternative thresholds", 44, 80, 1130, 60, {
    fontSize: 40,
    bold: true,
  });
  addText(slide, slideData.question, 44, 140, 960, 30, {
    fontSize: 18,
    color: COLORS.muted,
  });
  const thresholdRows = summary.robustness.filter((row) => row.family === "apy_threshold");

  addPanel(slide, 44, 186, 760, 426, {
    fill: COLORS.surface,
    line: COLORS.line,
    radius: 26,
    shadow: "shadow-sm",
  });
  addText(slide, "Episode count changes; median duration does not", 72, 210, 610, 32, {
    fontSize: 23,
    bold: true,
  });
  addImage(slide, chartAsset, 84, 260, 430, 286, "Episode counts under alternative APY thresholds");
  addText(slide, "2 days", 552, 310, 200, 62, {
    fontSize: 48,
    bold: true,
    color: accent,
    alignment: "center",
  });
  addText(slide, "median duration at 5%, 10% and 20% APY thresholds", 550, 382, 204, 82, {
    fontSize: 18,
    bold: true,
    alignment: "center",
  });
  addText(slide, `Counts: ${thresholdRows.map((row) => formatInt(row.episode_count)).join(" | ")}`, 548, 486, 210, 30, {
    fontSize: 15,
    color: COLORS.muted,
    alignment: "center",
  });

  addPanel(slide, 834, 186, 400, 426, {
    fill: `linear(145deg, ${accent}/18 0%, #FFFFFF 80%)`,
    line: `${accent}/30`,
    radius: 26,
    shadow: "shadow-sm",
  });
  addPill(slide, 860, 210, 182, 32, "FIVE CHECK FAMILIES", accent, {
    fill: `${accent}/16`,
    textColor: accent,
    fontSize: 12,
  });
  const families = [
    ["APY threshold", "5%, 10%, 20%"],
    ["Minimum TVL", "USD 0.5M, 1M, 5M"],
    ["History length", "90, 180, 365 days"],
    ["Episode gap", "0, 1, 3 days"],
    ["Winsorization", "p1 to p99"],
  ];
  families.forEach(([label, value], index) => {
    const y = 270 + index * 61;
    addText(slide, label, 862, y, 156, 28, { fontSize: 17, bold: true });
    addText(slide, value, 1024, y, 170, 28, { fontSize: 16, color: COLORS.muted });
    if (index < families.length - 1) addLine(slide, 862, y + 42, 332, 1, `${accent}/24`);
  });
  addText(slide, "Robustness changes sample size and episode count; it does not turn quoted APY into realized return.", 862, 566, 330, 40, {
    fontSize: 14,
    bold: true,
    color: COLORS.coral,
  });
}

function addLimitations(deck, summary, slideData) {
  const accent = COLORS.coral;
  const slide = baseLightSlide(deck, 13, slideData, accent, "LIMITS / ETHICS");
  addText(slide, "Market context is not total protocol risk", 44, 80, 1080, 60, {
    fontSize: 40,
    bold: true,
  });
  addText(slide, slideData.question, 44, 140, 960, 30, {
    fontSize: 18,
    color: COLORS.muted,
  });

  addPanel(slide, 44, 196, 562, 394, {
    fill: `linear(145deg, ${COLORS.teal}/16 0%, #FFFFFF 82%)`,
    line: `${COLORS.teal}/28`,
    radius: 28,
    shadow: "shadow-sm",
  });
  addPill(slide, 72, 222, 170, 34, "MEASURED HERE", COLORS.teal, {
    fill: `${COLORS.teal}/16`,
    textColor: COLORS.teal,
    fontSize: 13,
  });
  addText(slide, "What the evidence supports", 72, 278, 430, 40, {
    fontSize: 27,
    bold: true,
  });
  const measured = [
    "Quoted APY level and persistence",
    "Observed TVL and reward components",
    "Top-k membership stability",
    "Stablecoin peg context",
    "Data quality and sensitivity checks",
  ];
  measured.forEach((item, index) => addCheckRow(slide, 76, 342 + index * 46, item, COLORS.teal));

  addPanel(slide, 628, 196, 606, 394, {
    fill: `linear(145deg, ${accent}/17 0%, #FFFFFF 82%)`,
    line: `${accent}/28`,
    radius: 28,
    shadow: "shadow-sm",
  });
  addPill(slide, 656, 222, 206, 34, "NOT MEASURED HERE", accent, {
    fill: `${accent}/16`,
    textColor: accent,
    fontSize: 13,
  });
  addText(slide, "What the project cannot rank", 656, 278, 470, 40, {
    fontSize: 27,
    bold: true,
  });
  const unmeasured = [
    "Smart-contract and oracle failure",
    "Counterparty and collateral quality",
    "Bridge, chain and governance risk",
    "Executable liquidity and slippage",
    "Investor-specific realized return",
  ];
  unmeasured.forEach((item, index) => addCheckRow(slide, 660, 342 + index * 46, item, accent));
  addPanel(slide, 154, 614, 972, 42, { fill: "#FFFFFF", line: COLORS.line, radius: 18 });
  addText(slide, "Ethical consequence: no pool ranking, no hidden safety score and no financial recommendation.", 180, 624, 920, 24, {
    fontSize: 17,
    bold: true,
    color: COLORS.ink,
    alignment: "center",
  });
}

function addConclusion(deck, summary, slideData) {
  const slide = deck.slides.add();
  slide.background.fill = "linear(135deg, #091127 0%, #14275A 58%, #3A2A78 100%)";
  addPill(slide, 54, 42, 196, 36, "FINAL SYNTHESIS", COLORS.cyan, {
    fill: "#FFFFFF/12",
    textColor: COLORS.white,
    fontSize: 14,
  });
  addText(slide, "Stablecoin yield is best shown as trade-offs", 54, 100, 1050, 66, {
    fontSize: 48,
    bold: true,
    color: COLORS.white,
  });
  addText(
    slide,
    "The project closes on three lenses that keep a volatile number interpretable.",
    56,
    172,
    850,
    36,
    { fontSize: 21, color: "#DDE6FF" },
  );

  addPanel(slide, 54, 238, 430, 278, {
    fill: "linear(145deg, #4F7CFF/25 0%, #8B5CF6/18 100%)",
    line: "#FFFFFF/18",
    radius: 30,
  });
  addText(slide, "ONE SENTENCE DEFENSE", 84, 270, 300, 24, {
    fontSize: 14,
    bold: true,
    color: COLORS.cyan,
  });
  addText(
    slide,
    "High stablecoin yield is common in snapshots. Persistent high yield with capacity and interpretable risk context is rarer.",
    84,
    314,
    342,
    148,
    { fontSize: 28, bold: true, color: COLORS.white },
  );

  addPanel(slide, 520, 238, 704, 278, {
    fill: "#FFFFFF/10",
    line: "#FFFFFF/18",
    radius: 30,
  });
  const takeaways = [
    {
      label: "PERSISTENCE",
      body: `Under the main 10% definition, the median episode lasts ${summary.episodes.primary_median_duration_days} days, so duration matters as much as level.`,
      accent: COLORS.cyan,
    },
    {
      label: "CONTEXT",
      body: "Mechanism, reward dependence and peg stress change what a nominal APY number means.",
      accent: COLORS.coral,
    },
    {
      label: "RESPONSIBLE DESIGN",
      body: "The joint screen keeps APY, persistence and capacity visible without encoding a recommendation.",
      accent: COLORS.amber,
    },
  ];
  takeaways.forEach((item, index) => {
    const y = 260 + index * 82;
    addPill(slide, 548, y, 178, 30, item.label, item.accent, {
      fill: `${item.accent}/16`,
      textColor: item.accent,
      fontSize: 12,
    });
    addText(slide, item.body, 746, y - 2, 432, 54, {
      fontSize: 17,
      color: COLORS.white,
    });
    if (index < takeaways.length - 1) {
      addLine(slide, 548, y + 64, 630, 1, "#FFFFFF/16");
    }
  });

  addPanel(slide, 54, 552, 1170, 82, {
    fill: "linear(0deg, #23C9D8/22 0%, #4F7CFF/22 48%, #FF6B9D/22 100%)",
    line: "#FFFFFF/16",
    radius: 24,
  });
  addText(
    slide,
    "Reproducible by design: raw envelopes, canonical tables, quality checks, figures, report and deck are regenerated by one pipeline.",
    82,
    573,
    1040,
    38,
    { fontSize: 19, color: COLORS.white },
  );
  addText(slide, "Educational analysis only. No financial advice.", 56, 662, 560, 24, {
    fontSize: 14,
    color: "#C7D2FE",
  });
  addText(slide, `${TOTAL_SLIDES} / ${TOTAL_SLIDES}`, 1110, 658, 108, 28, {
    fontSize: 16,
    bold: true,
    color: COLORS.white,
    alignment: "right",
  });
  setSpeakerNotes(slide, slideData);
}

function baseLightSlide(deck, slideNumber, slideData, accent, section) {
  const slide = deck.slides.add();
  slide.background.fill = "linear(135deg, #FBFCFF 0%, #F4F7FF 64%, #EEF2FF 100%)";
  addPill(slide, 44, 30, 214, 34, section, accent, {
    fill: `${accent}/13`,
    textColor: accent,
    fontSize: 13,
  });
  addPill(slide, 1182, 28, 52, 38, String(slideNumber).padStart(2, "0"), accent, {
    fill: accent,
    textColor: COLORS.white,
    fontSize: 15,
  });
  addFooter(slide, slideNumber, accent);
  setSpeakerNotes(slide, slideData);
  return slide;
}

function addFooter(slide, slideNumber, accent) {
  addText(slide, "STABLECOIN YIELD", 44, 675, 210, 18, {
    fontSize: 11,
    bold: true,
    color: COLORS.muted,
  });
  addPanel(slide, 884, 681, 350, 4, { fill: "#DCE4F2", radius: 4 });
  addPanel(slide, 884, 681, (350 * slideNumber) / TOTAL_SLIDES, 4, { fill: accent, radius: 4 });
}

function addMetricCell(slide, left, top, value, label, accent) {
  addText(slide, value, left, top, 166, 64, {
    fontSize: 48,
    bold: true,
    color: COLORS.white,
  });
  addPanel(slide, left, top + 72, 42, 5, { fill: accent, radius: 5 });
  addText(slide, label, left, top + 88, 170, 34, {
    fontSize: 13,
    bold: true,
    color: "#DDE6FF",
  });
}

function addMetricRow(slide, left, top, value, label, accent) {
  addText(slide, value, left, top, 118, 34, {
    fontSize: 23,
    bold: true,
    color: accent,
  });
  addText(slide, label, left + 124, top + 2, 176, 38, {
    fontSize: 15,
    color: COLORS.ink,
  });
}

function addCheckRow(slide, left, top, value, accent) {
  addPanel(slide, left, top + 5, 12, 12, { fill: accent, radius: 12 });
  addText(slide, value, left + 28, top, 430, 30, {
    fontSize: 18,
    color: COLORS.ink,
  });
}

function addSourceNote(slide) {
  addText(
    slide,
    "Sources: DeFiLlama, CoinGecko and selected official protocol documentation. APY is quoted, not realized return.",
    44,
    628,
    1080,
    22,
    { fontSize: 11, color: COLORS.muted },
  );
}

function prettyPoolType(value) {
  const labels = {
    single_stable_lending: "Single-stable lending",
    incentive_driven: "Incentive-driven",
    stable_stable_lp: "Stable-stable LP",
    yield_bearing_stablecoin: "Yield-bearing stablecoin",
    vault_aggregator: "Vault aggregator",
  };
  return labels[value] ?? String(value).replaceAll("_", " ");
}

function addText(slide, value, left, top, width, height, style = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    name: style.name,
    position: { left, top, width, height },
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = String(value);
  shape.text.style = {
    fontSize: style.fontSize ?? 18,
    bold: style.bold ?? false,
    color: style.color ?? COLORS.ink,
    alignment: style.alignment ?? "left",
    verticalAlignment: style.verticalAlignment ?? "top",
    autoFit: style.autoFit ?? "shrinkText",
    insets: style.insets ?? { top: 0, right: 0, bottom: 0, left: 0 },
    typeface: style.typeface ?? "Aptos",
  };
  return shape;
}

function addPanel(slide, left, top, width, height, options = {}) {
  return slide.shapes.add({
    geometry: "roundRect",
    name: options.name,
    position: { left, top, width, height },
    fill: options.fill ?? COLORS.surface,
    line: {
      style: "solid",
      fill: options.line ?? options.fill ?? COLORS.surface,
      width: options.lineWidth ?? (options.line ? 1 : 0),
    },
    borderRadius: options.radius ?? 20,
    shadow: options.shadow ?? "shadow-none",
  });
}

function addPill(slide, left, top, width, height, value, accent, options = {}) {
  addPanel(slide, left, top, width, height, {
    fill: options.fill ?? `${accent}/14`,
    line: options.line ?? `${accent}/22`,
    radius: "rounded-full",
  });
  return addText(slide, value, left + 12, top + 1, width - 24, height - 2, {
    fontSize: options.fontSize ?? 13,
    bold: true,
    color: options.textColor ?? accent,
    alignment: "center",
    verticalAlignment: "middle",
  });
}

function addLine(slide, left, top, width, height, color) {
  return slide.shapes.add({
    geometry: "line",
    position: { left, top, width, height },
    fill: "none",
    line: { style: "solid", fill: color, width: Math.max(Math.min(width, height), 1) },
  });
}

function addImage(slide, imagePath, left, top, width, height, alt) {
  slide.images.add({
    blob: fsSync.readFileSync(imagePath),
    contentType: "image/png",
    alt,
    fit: "contain",
    geometry: "roundRect",
    borderRadius: 16,
    position: { left, top, width, height },
  });
}

function setSpeakerNotes(slide, slideData) {
  if (slideData?.speaker_note) {
    slide.speakerNotes.textFrame.setText(slideData.speaker_note);
    slide.speakerNotes.setVisible(true);
  }
}

async function writeBlob(outputPath, blob) {
  await fs.writeFile(outputPath, new Uint8Array(await blob.arrayBuffer()));
}

function pct(value) {
  if (value === undefined || value === null || Number.isNaN(Number(value))) return "n/a";
  return `${(Number(value) * 100).toFixed(1)}%`;
}

function formatInt(value) {
  return Number(value).toLocaleString("en-US", { maximumFractionDigits: 0 });
}

function formatCompactNumber(value) {
  const number = Number(value);
  if (number >= 1_000_000) return `${(number / 1_000_000).toFixed(1)}M`;
  if (number >= 10_000) return `${Math.round(number / 1_000)}k`;
  if (number >= 1_000) return `${(number / 1_000).toFixed(1)}k`;
  return Math.round(number).toString();
}

function plural(count, singular) {
  return Number(count) === 1 ? singular : `${singular}s`;
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
