const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const {
  FaExclamationTriangle, FaHeart, FaPhone, FaUser, FaUsers,
  FaDatabase, FaComments, FaFileAlt, FaMobileAlt, FaMapMarkerAlt,
  FaCheckCircle, FaTimesCircle, FaArrowRight, FaArrowDown,
  FaShieldAlt, FaBell, FaHandsHelping, FaHome, FaHospital,
  FaClipboardList, FaSearch, FaLightbulb, FaGithub
} = require("react-icons/fa");
const {
  MdSos, MdLocationOn, MdSmartphone, MdSecurity
} = require("react-icons/md");

// ====== COLOR PALETTE ======
// Warm Teal + Emergency Red - welfare/care context
const C = {
  primary:    "1A6B5C",  // Deep teal (trust, care)
  secondary:  "2D9B83",  // Medium teal
  light:      "E8F5F0",  // Very light teal bg
  accent:     "DC2626",  // Emergency red
  accentLight:"FEE2E2",  // Light red bg
  dark:       "1E293B",  // Near-black for text
  gray:       "475569",  // Muted text (improved contrast)
  lightGray:  "F1F5F9",  // Light gray bg
  white:      "FFFFFF",
  warmBg:     "FFF7ED",  // Warm cream bg
  orange:     "EA580C",  // Warning orange
  purple:     "7C3AED",  // Claude purple
  purpleLight:"EDE9FE",  // Light purple
};

// ====== ICON HELPER ======
function renderIconSvg(IconComponent, color, size = 256) {
  return ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComponent, { color, size: String(size) })
  );
}

async function iconToBase64Png(IconComponent, color, size = 256) {
  const svg = renderIconSvg(IconComponent, color, size);
  const pngBuffer = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + pngBuffer.toString("base64");
}

// ====== SHAPE HELPERS ======
const makeShadow = () => ({
  type: "outer", color: "000000", blur: 8, offset: 3, angle: 135, opacity: 0.12
});

const makeCardShadow = () => ({
  type: "outer", color: "000000", blur: 6, offset: 2, angle: 135, opacity: 0.10
});

// ====== PERSON ILLUSTRATION (shapes) ======
function addPersonIllustration(slide, pres, x, y, scale, headColor, bodyColor) {
  const s = scale || 1;
  // Head (circle)
  slide.addShape(pres.shapes.OVAL, {
    x: x + 0.15 * s, y: y, w: 0.5 * s, h: 0.5 * s,
    fill: { color: headColor || "FBBF24" }
  });
  // Body (trapezoid-ish rectangle)
  slide.addShape(pres.shapes.RECTANGLE, {
    x: x, y: y + 0.5 * s, w: 0.8 * s, h: 0.9 * s,
    fill: { color: bodyColor || "3B82F6" },
    rectRadius: 0.08
  });
}

function addDocumentIllustration(slide, pres, x, y, scale, color) {
  const s = scale || 1;
  slide.addShape(pres.shapes.RECTANGLE, {
    x: x, y: y, w: 0.65 * s, h: 0.85 * s,
    fill: { color: color || "FFFFFF" },
    line: { color: "CBD5E1", width: 1 },
    shadow: makeCardShadow()
  });
  // Lines on document
  for (let i = 0; i < 3; i++) {
    slide.addShape(pres.shapes.RECTANGLE, {
      x: x + 0.08 * s, y: y + (0.15 + i * 0.2) * s,
      w: 0.49 * s, h: 0.06 * s,
      fill: { color: "E2E8F0" }
    });
  }
}

function addSmartphoneIllustration(slide, pres, x, y, scale, screenColor) {
  const s = scale || 1;
  // Phone body
  slide.addShape(pres.shapes.RECTANGLE, {
    x: x, y: y, w: 0.55 * s, h: 1.0 * s,
    fill: { color: "374151" },
    rectRadius: 0.06
  });
  // Screen
  slide.addShape(pres.shapes.RECTANGLE, {
    x: x + 0.04 * s, y: y + 0.08 * s,
    w: 0.47 * s, h: 0.78 * s,
    fill: { color: screenColor || "FEE2E2" }
  });
  // Home button
  slide.addShape(pres.shapes.OVAL, {
    x: x + 0.2 * s, y: y + 0.9 * s,
    w: 0.15 * s, h: 0.06 * s,
    fill: { color: "6B7280" }
  });
}

// ====== MAIN ======
async function createPresentation() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = "nest - 親亡き後支援データベース";
  pres.title = "親亡き後、この子の情報をどう託しますか？";

  // Pre-render icons
  const icons = {
    warning:    await iconToBase64Png(FaExclamationTriangle, "#DC2626"),
    heart:      await iconToBase64Png(FaHeart, "#DC2626"),
    phone:      await iconToBase64Png(FaPhone, "#1A6B5C"),
    user:       await iconToBase64Png(FaUser, "#1A6B5C"),
    users:      await iconToBase64Png(FaUsers, "#1A6B5C"),
    database:   await iconToBase64Png(FaDatabase, "#7C3AED"),
    comments:   await iconToBase64Png(FaComments, "#7C3AED"),
    fileAlt:    await iconToBase64Png(FaFileAlt, "#64748B"),
    mobile:     await iconToBase64Png(FaMobileAlt, "#DC2626"),
    mapMarker:  await iconToBase64Png(FaMapMarkerAlt, "#DC2626"),
    check:      await iconToBase64Png(FaCheckCircle, "#16A34A"),
    times:      await iconToBase64Png(FaTimesCircle, "#DC2626"),
    arrowRight: await iconToBase64Png(FaArrowRight, "#1A6B5C"),
    arrowDown:  await iconToBase64Png(FaArrowDown, "#1A6B5C"),
    shield:     await iconToBase64Png(FaShieldAlt, "#1A6B5C"),
    bell:       await iconToBase64Png(FaBell, "#EA580C"),
    hands:      await iconToBase64Png(FaHandsHelping, "#1A6B5C"),
    home:       await iconToBase64Png(FaHome, "#1A6B5C"),
    hospital:   await iconToBase64Png(FaHospital, "#DC2626"),
    clipboard:  await iconToBase64Png(FaClipboardList, "#1A6B5C"),
    search:     await iconToBase64Png(FaSearch, "#64748B"),
    lightbulb:  await iconToBase64Png(FaLightbulb, "#FBBF24"),
    github:     await iconToBase64Png(FaGithub, "#FFFFFF"),
    userWhite:  await iconToBase64Png(FaUser, "#FFFFFF"),
    heartWhite: await iconToBase64Png(FaHeart, "#FFFFFF"),
    handsWhite: await iconToBase64Png(FaHandsHelping, "#FFFFFF"),
    dbWhite:    await iconToBase64Png(FaDatabase, "#FFFFFF"),
    mobileW:    await iconToBase64Png(FaMobileAlt, "#FFFFFF"),
    bellW:      await iconToBase64Png(FaBell, "#FFFFFF"),
    arrowRW:    await iconToBase64Png(FaArrowRight, "#FFFFFF"),
    arrowDW:    await iconToBase64Png(FaArrowDown, "#FFFFFF"),
    shieldW:    await iconToBase64Png(FaShieldAlt, "#FFFFFF"),
    checkW:     await iconToBase64Png(FaCheckCircle, "#FFFFFF"),
    phoneW:     await iconToBase64Png(FaPhone, "#FFFFFF"),
    warningO:   await iconToBase64Png(FaExclamationTriangle, "#EA580C"),
    commentsT:  await iconToBase64Png(FaComments, "#1A6B5C"),
    userGray:   await iconToBase64Png(FaUser, "#94A3B8"),
  };

  // ============================================================
  // SLIDE 1: TITLE
  // ============================================================
  let s1 = pres.addSlide();
  s1.background = { color: C.dark };

  // Decorative teal bar at top
  s1.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.08, fill: { color: C.secondary }
  });

  // Person illustrations (silhouettes)
  // Mother figure (left)
  addPersonIllustration(s1, pres, 1.2, 1.5, 1.2, "FBBF24", "EC4899");
  // Child figure (right of mother)
  addPersonIllustration(s1, pres, 2.3, 1.8, 1.0, "FBBF24", "3B82F6");
  // Support staff figure (far right)
  addPersonIllustration(s1, pres, 7.5, 1.8, 1.0, "FBBF24", C.secondary);

  // Question mark between them
  s1.addText("?", {
    x: 4.2, y: 1.8, w: 1.5, h: 1.5,
    fontSize: 72, fontFace: "Georgia", color: C.accent,
    bold: true, align: "center", valign: "middle"
  });

  // Title
  s1.addText("親亡き後、\nこの子の情報を\nどう託しますか？", {
    x: 0.8, y: 2.8, w: 8.4, h: 2.0,
    fontSize: 36, fontFace: "Georgia", color: C.white,
    bold: true, align: "center", valign: "middle",
    lineSpacingMultiple: 1.3
  });

  // Subtitle
  s1.addText("nest ― 親亡き後支援データベース", {
    x: 0.8, y: 4.9, w: 8.4, h: 0.5,
    fontSize: 16, fontFace: "Calibri", color: "94A3B8",
    align: "center"
  });

  // Speaker notes
  s1.addNotes("【ナレーション】\nある日、お母さんが倒れました。息子のたけしさんは28歳、知的障害があります。たけしさんの支援を引き継いでください、と言われたとき…あなたはすぐに対応できますか？\n\nたけしさんは何が苦手ですか？パニックになったらどうすればいいですか？絶対にしてはいけないことは？\n\n紙のファイルから探すのに、何分かかりますか？");

  // ============================================================
  // SLIDE 2: THE PROBLEM - Mother collapses
  // ============================================================
  let s2 = pres.addSlide();
  s2.background = { color: C.white };

  // Left: red emergency panel
  s2.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 4.5, h: 5.625, fill: { color: C.accentLight }
  });

  // Emergency icon
  s2.addImage({ data: icons.warning, x: 1.7, y: 0.6, w: 0.8, h: 0.8 });

  s2.addText("緊急事態", {
    x: 0.5, y: 1.5, w: 3.5, h: 0.6,
    fontSize: 28, fontFace: "Georgia", color: C.accent,
    bold: true, align: "center"
  });

  // Mother figure (collapsed - horizontal)
  s2.addShape(pres.shapes.OVAL, {
    x: 1.0, y: 2.8, w: 0.5, h: 0.5, fill: { color: "FBBF24" }
  });
  s2.addShape(pres.shapes.RECTANGLE, {
    x: 1.5, y: 2.85, w: 1.2, h: 0.4, fill: { color: "EC4899" }, rectRadius: 0.05
  });

  s2.addText("お母さんが倒れました", {
    x: 0.5, y: 3.5, w: 3.5, h: 0.5,
    fontSize: 18, fontFace: "Calibri", color: C.accent,
    bold: true, align: "center"
  });

  // Son figure
  addPersonIllustration(s2, pres, 1.6, 4.0, 0.8, "FBBF24", "3B82F6");
  s2.addText("たけしさん（28歳）", {
    x: 0.5, y: 4.7, w: 3.5, h: 0.4,
    fontSize: 14, fontFace: "Calibri", color: C.gray, align: "center"
  });

  // Right: questions
  s2.addText("引き継ぎに必要な情報", {
    x: 5.0, y: 0.5, w: 4.5, h: 0.6,
    fontSize: 22, fontFace: "Georgia", color: C.dark, bold: true
  });

  const questions = [
    { icon: icons.times, text: "絶対にしてはいけないことは？", color: C.accent },
    { icon: icons.heart, text: "パニック時の対応方法は？", color: "EC4899" },
    { icon: icons.phone, text: "緊急連絡先は誰？順番は？", color: C.primary },
    { icon: icons.hospital, text: "かかりつけ医はどこ？", color: C.accent },
    { icon: icons.fileAlt, text: "手帳や受給者証の更新日は？", color: C.gray },
  ];

  questions.forEach((q, i) => {
    const yPos = 1.4 + i * 0.75;
    s2.addShape(pres.shapes.RECTANGLE, {
      x: 5.0, y: yPos, w: 4.3, h: 0.6,
      fill: { color: C.lightGray }, rectRadius: 0.05
    });
    s2.addImage({ data: q.icon, x: 5.15, y: yPos + 0.1, w: 0.4, h: 0.4 });
    s2.addText(q.text, {
      x: 5.7, y: yPos, w: 3.5, h: 0.6,
      fontSize: 16, fontFace: "Calibri", color: C.dark, valign: "middle", margin: 0
    });
  });

  s2.addText("紙のファイルから探すのに、何分かかりますか？", {
    x: 5.0, y: 5.0, w: 4.5, h: 0.5,
    fontSize: 14, fontFace: "Calibri", color: C.accent, italic: true
  });

  s2.addNotes("【ナレーション】\nある日突然、お母さんが倒れました。息子のたけしさんは28歳、知的障害があります。\n\nたけしさんの支援を引き継ぐには、これだけの情報が必要です。\n絶対にしてはいけないこと、パニック時の対応、緊急連絡先の優先順位、かかりつけ医、手帳の更新日…\n\n紙のファイルから探していたら、何分かかるでしょうか？");

  // ============================================================
  // SLIDE 3: THE SOLUTION - Claude Desktop retrieves info
  // ============================================================
  let s3 = pres.addSlide();
  s3.background = { color: C.lightGray };

  s3.addText("30秒で、命に関わる情報が出ます", {
    x: 0.5, y: 0.3, w: 9, h: 0.7,
    fontSize: 28, fontFace: "Georgia", color: C.dark, bold: true, margin: 0
  });

  s3.addText("Claude Desktop に聞くだけ", {
    x: 0.5, y: 0.9, w: 9, h: 0.4,
    fontSize: 16, fontFace: "Calibri", color: C.gray, margin: 0
  });

  // Chat input simulation
  s3.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.5, w: 9, h: 0.6,
    fill: { color: C.white }, line: { color: "CBD5E1", width: 1 },
    rectRadius: 0.05
  });
  s3.addImage({ data: icons.commentsT, x: 0.7, y: 1.6, w: 0.35, h: 0.35 });
  s3.addText("たけしさんの緊急対応を教えてください", {
    x: 1.2, y: 1.5, w: 8, h: 0.6,
    fontSize: 16, fontFace: "Calibri", color: C.dark, valign: "middle", margin: 0
  });

  // Response cards - 3 columns
  // Card 1: Prohibited actions (red)
  s3.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 2.4, w: 2.85, h: 2.7,
    fill: { color: C.white }, shadow: makeCardShadow()
  });
  s3.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 2.4, w: 2.85, h: 0.06, fill: { color: C.accent }
  });
  s3.addImage({ data: icons.times, x: 0.7, y: 2.6, w: 0.4, h: 0.4 });
  s3.addText("禁忌事項", {
    x: 1.2, y: 2.6, w: 2, h: 0.4,
    fontSize: 16, fontFace: "Calibri", color: C.accent, bold: true, valign: "middle", margin: 0
  });
  s3.addText([
    { text: "大きな声で指示しない", options: { bullet: true, breakLine: true, color: C.dark, fontSize: 12 } },
    { text: "（パニック悪化）", options: { breakLine: true, color: C.gray, fontSize: 10 } },
    { text: "無理に移動させない", options: { bullet: true, breakLine: true, color: C.dark, fontSize: 12 } },
    { text: "（転倒リスク）", options: { breakLine: true, color: C.gray, fontSize: 10 } },
    { text: "急な予定変更を伝えない", options: { bullet: true, color: C.dark, fontSize: 12 } },
  ], { x: 0.65, y: 3.2, w: 2.6, h: 1.8, valign: "top" });

  // Card 2: Care methods (green)
  s3.addShape(pres.shapes.RECTANGLE, {
    x: 3.55, y: 2.4, w: 2.85, h: 2.7,
    fill: { color: C.white }, shadow: makeCardShadow()
  });
  s3.addShape(pres.shapes.RECTANGLE, {
    x: 3.55, y: 2.4, w: 2.85, h: 0.06, fill: { color: C.primary }
  });
  s3.addImage({ data: icons.check, x: 3.75, y: 2.6, w: 0.4, h: 0.4 });
  s3.addText("推奨ケア", {
    x: 4.25, y: 2.6, w: 2, h: 0.4,
    fontSize: 16, fontFace: "Calibri", color: C.primary, bold: true, valign: "middle", margin: 0
  });
  s3.addText([
    { text: "静かな場所に誘導する", options: { bullet: true, breakLine: true, color: C.dark, fontSize: 13 } },
    { text: "好きな音楽を聞かせる", options: { bullet: true, breakLine: true, color: C.dark, fontSize: 13 } },
    { text: "タイマーを見せて", options: { bullet: true, breakLine: true, color: C.dark, fontSize: 13 } },
    { text: "「あと5分」と伝える", options: { color: C.gray, fontSize: 12 } },
  ], { x: 3.75, y: 3.2, w: 2.5, h: 1.8, valign: "top" });

  // Card 3: Emergency contacts (blue)
  s3.addShape(pres.shapes.RECTANGLE, {
    x: 6.6, y: 2.4, w: 2.85, h: 2.7,
    fill: { color: C.white }, shadow: makeCardShadow()
  });
  s3.addShape(pres.shapes.RECTANGLE, {
    x: 6.6, y: 2.4, w: 2.85, h: 0.06, fill: { color: "3B82F6" }
  });
  s3.addImage({ data: icons.phone, x: 6.8, y: 2.6, w: 0.4, h: 0.4 });
  s3.addText("緊急連絡先", {
    x: 7.3, y: 2.6, w: 2, h: 0.4,
    fontSize: 16, fontFace: "Calibri", color: "3B82F6", bold: true, valign: "middle", margin: 0
  });
  s3.addText([
    { text: "1. 母・山田花子", options: { breakLine: true, bold: true, color: C.dark, fontSize: 13 } },
    { text: "   090-xxxx-xxxx", options: { breakLine: true, color: C.gray, fontSize: 12 } },
    { text: "2. 相談支援・佐藤", options: { breakLine: true, bold: true, color: C.dark, fontSize: 13 } },
    { text: "   080-xxxx-xxxx", options: { breakLine: true, color: C.gray, fontSize: 12 } },
    { text: "3. GH・田中", options: { breakLine: true, bold: true, color: C.dark, fontSize: 13 } },
    { text: "   070-xxxx-xxxx", options: { color: C.gray, fontSize: 12 } },
  ], { x: 6.8, y: 3.2, w: 2.5, h: 1.8, valign: "top" });

  s3.addNotes("【ナレーション】\nもし、こう聞けたらどうでしょうか？\n「たけしさんの緊急対応を教えてください」\n\nClaude Desktopに入力するだけで、30秒以内に、命に関わる3つの情報が出ます。\n\n1つ目、禁忌事項。絶対にやってはいけないこと。大きな声で指示しない、無理に移動させない。\n2つ目、推奨ケア。パニックになったら静かな場所に誘導し、好きな音楽を聞かせる。\n3つ目、緊急連絡先。優先順位付きで、すぐに電話できます。");

  // ============================================================
  // SLIDE 4: DATA REGISTRATION - Raw text to structured
  // ============================================================
  let s4 = pres.addSlide();
  s4.background = { color: C.white };

  s4.addText("お母さんの言葉が、そのままデータになる", {
    x: 0.5, y: 0.3, w: 9, h: 0.7,
    fontSize: 26, fontFace: "Georgia", color: C.dark, bold: true, margin: 0
  });
  s4.addText("専門知識もITスキルも不要", {
    x: 0.5, y: 0.9, w: 9, h: 0.4,
    fontSize: 15, fontFace: "Calibri", color: C.gray, margin: 0
  });

  // Left: Raw text input (before)
  s4.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.5, w: 4.2, h: 3.5,
    fill: { color: C.warmBg }, shadow: makeCardShadow()
  });
  s4.addImage({ data: icons.commentsT, x: 0.7, y: 1.65, w: 0.35, h: 0.35 });
  s4.addText("お母さんの言葉", {
    x: 1.15, y: 1.6, w: 3, h: 0.4,
    fontSize: 15, fontFace: "Calibri", color: C.primary, bold: true, valign: "middle", margin: 0
  });

  // Mother illustration
  addPersonIllustration(s4, pres, 3.5, 1.6, 0.6, "FBBF24", "EC4899");

  // Speech bubble content
  s4.addShape(pres.shapes.RECTANGLE, {
    x: 0.7, y: 2.2, w: 3.8, h: 2.5,
    fill: { color: C.white }, rectRadius: 0.08
  });
  s4.addText(
    "たけしは大きな音が苦手です。\nスーパーのレジの音で\nパニックになることがあります。\n\nそのときは静かな場所に連れて行って、\n好きなトーマスの動画を見せると\n落ち着きます。", {
    x: 0.85, y: 2.3, w: 3.5, h: 2.3,
    fontSize: 12, fontFace: "Calibri", color: C.dark,
    lineSpacingMultiple: 1.4
  });

  // Arrow in middle
  s4.addImage({ data: icons.arrowRight, x: 4.85, y: 2.9, w: 0.5, h: 0.5 });
  s4.addText("自動\n構造化", {
    x: 4.7, y: 3.4, w: 0.8, h: 0.6,
    fontSize: 11, fontFace: "Calibri", color: C.primary, bold: true, align: "center"
  });

  // Right: Structured output (after)
  s4.addShape(pres.shapes.RECTANGLE, {
    x: 5.5, y: 1.5, w: 4.2, h: 3.5,
    fill: { color: C.light }, shadow: makeCardShadow()
  });
  s4.addImage({ data: icons.database, x: 5.7, y: 1.65, w: 0.35, h: 0.35 });
  s4.addText("構造化データ", {
    x: 6.15, y: 1.6, w: 3, h: 0.4,
    fontSize: 15, fontFace: "Calibri", color: C.purple, bold: true, valign: "middle", margin: 0
  });

  // Structured cards
  const structItems = [
    { label: "禁忌事項", value: "大きな音のある場所に長時間いさせない", color: C.accent },
    { label: "ケア方法", value: "パニック時：静かな場所 → トーマスの動画", color: C.primary },
    { label: "トリガー", value: "スーパーのレジの音", color: C.orange },
  ];

  structItems.forEach((item, i) => {
    const yPos = 2.2 + i * 0.85;
    s4.addShape(pres.shapes.RECTANGLE, {
      x: 5.7, y: yPos, w: 3.8, h: 0.7,
      fill: { color: C.white }, rectRadius: 0.05
    });
    s4.addShape(pres.shapes.RECTANGLE, {
      x: 5.7, y: yPos, w: 0.06, h: 0.7,
      fill: { color: item.color }
    });
    s4.addText(item.label, {
      x: 5.9, y: yPos + 0.02, w: 3.4, h: 0.3,
      fontSize: 11, fontFace: "Calibri", color: item.color, bold: true, margin: 0
    });
    s4.addText(item.value, {
      x: 5.9, y: yPos + 0.3, w: 3.4, h: 0.35,
      fontSize: 12, fontFace: "Calibri", color: C.dark, margin: 0
    });
  });

  s4.addNotes("【ナレーション】\nデータはどうやって作るのでしょうか？\n\n答えは簡単です。お母さんや支援者の言葉を、そのままClaude Desktopに貼り付けるだけ。\n\n「たけしは大きな音が苦手です。パニックになったら静かな場所に連れて行って…」\n\nこの自然な言葉を、AIが自動的に構造化します。禁忌事項、ケア方法、トリガーに分類されて、データベースに蓄積されます。\n\n専門知識もITスキルも必要ありません。お母さんの言葉がそのままデータになるのです。");

  // ============================================================
  // SLIDE 5: SOS BUTTON - Smartphone emergency
  // ============================================================
  let s5 = pres.addSlide();
  s5.background = { color: C.white };

  s5.addText("緊急時、ワンタップで助けを呼べる", {
    x: 0.5, y: 0.3, w: 9, h: 0.7,
    fontSize: 26, fontFace: "Georgia", color: C.dark, bold: true, margin: 0
  });
  s5.addText("本人も支援者もスマホから即座に発信", {
    x: 0.5, y: 0.9, w: 9, h: 0.4,
    fontSize: 15, fontFace: "Calibri", color: C.gray, margin: 0
  });

  // Step 1: Phone with SOS button
  s5.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.6, w: 2.7, h: 3.5,
    fill: { color: C.accentLight }, rectRadius: 0.1
  });
  s5.addText("STEP 1", {
    x: 0.5, y: 1.7, w: 2.7, h: 0.35,
    fontSize: 12, fontFace: "Calibri", color: C.accent, bold: true, align: "center", margin: 0
  });
  // Smartphone illustration
  addSmartphoneIllustration(s5, pres, 1.35, 2.1, 1.6, "FEE2E2");
  // SOS text on phone screen
  s5.addText("SOS", {
    x: 1.3, y: 2.6, w: 1.0, h: 0.6,
    fontSize: 24, fontFace: "Arial Black", color: C.accent, bold: true,
    align: "center", valign: "middle", margin: 0
  });
  s5.addText("ボタンを押す", {
    x: 0.5, y: 4.55, w: 2.7, h: 0.4,
    fontSize: 14, fontFace: "Calibri", color: C.dark, bold: true, align: "center"
  });

  // Arrow 1
  s5.addImage({ data: icons.arrowRight, x: 3.35, y: 3.1, w: 0.45, h: 0.45 });

  // Step 2: Processing
  s5.addShape(pres.shapes.RECTANGLE, {
    x: 3.95, y: 1.6, w: 2.3, h: 3.5,
    fill: { color: C.purpleLight }, rectRadius: 0.1
  });
  s5.addText("STEP 2", {
    x: 3.95, y: 1.7, w: 2.3, h: 0.35,
    fontSize: 12, fontFace: "Calibri", color: C.purple, bold: true, align: "center", margin: 0
  });
  s5.addImage({ data: icons.database, x: 4.65, y: 2.3, w: 0.7, h: 0.7 });
  s5.addImage({ data: icons.mapMarker, x: 4.3, y: 3.2, w: 0.4, h: 0.4 });
  s5.addText("位置情報", {
    x: 4.7, y: 3.2, w: 1.2, h: 0.4,
    fontSize: 12, fontFace: "Calibri", color: C.dark, valign: "middle", margin: 0
  });
  s5.addImage({ data: icons.times, x: 4.3, y: 3.6, w: 0.4, h: 0.4 });
  s5.addText("禁忌事項", {
    x: 4.7, y: 3.6, w: 1.2, h: 0.4,
    fontSize: 12, fontFace: "Calibri", color: C.dark, valign: "middle", margin: 0
  });
  s5.addImage({ data: icons.phone, x: 4.3, y: 4.0, w: 0.4, h: 0.4 });
  s5.addText("連絡先", {
    x: 4.7, y: 4.0, w: 1.2, h: 0.4,
    fontSize: 12, fontFace: "Calibri", color: C.dark, valign: "middle", margin: 0
  });
  s5.addText("自動取得・統合", {
    x: 3.95, y: 4.55, w: 2.3, h: 0.4,
    fontSize: 14, fontFace: "Calibri", color: C.dark, bold: true, align: "center"
  });

  // Arrow 2
  s5.addImage({ data: icons.arrowRight, x: 6.4, y: 3.1, w: 0.45, h: 0.45 });

  // Step 3: LINE notification
  s5.addShape(pres.shapes.RECTANGLE, {
    x: 7.0, y: 1.6, w: 2.5, h: 3.5,
    fill: { color: "DCFCE7" }, rectRadius: 0.1
  });
  s5.addText("STEP 3", {
    x: 7.0, y: 1.7, w: 2.5, h: 0.35,
    fontSize: 12, fontFace: "Calibri", color: "16A34A", bold: true, align: "center", margin: 0
  });
  // Multiple people icons
  s5.addImage({ data: icons.users, x: 7.75, y: 2.2, w: 0.7, h: 0.7 });
  // LINE-like message bubble
  s5.addShape(pres.shapes.RECTANGLE, {
    x: 7.15, y: 3.1, w: 2.2, h: 1.3,
    fill: { color: C.white }, rectRadius: 0.08,
    line: { color: "06C755", width: 2 }
  });
  s5.addText("🆘 たけしさんSOS\n📍 現在地: Google Maps\n⚠️ 大きな声NG\n📞 母: 090-xxxx", {
    x: 7.25, y: 3.15, w: 2.0, h: 1.2,
    fontSize: 10, fontFace: "Calibri", color: C.dark, lineSpacingMultiple: 1.3
  });
  s5.addText("LINE通知が届く", {
    x: 7.0, y: 4.55, w: 2.5, h: 0.4,
    fontSize: 14, fontFace: "Calibri", color: C.dark, bold: true, align: "center"
  });

  s5.addNotes("【ナレーション】\nもうひとつ、大切な機能があります。緊急時にワンタップで助けを呼べるSOSボタンです。\n\nSTEP 1：本人や支援者がスマホのSOSボタンを押します。大きな赤いボタンがひとつだけ。知的障害のある方でも直感的に操作できます。\n\nSTEP 2：システムが自動的に、位置情報、その方の禁忌事項、緊急連絡先をデータベースから取得します。\n\nSTEP 3：これらの情報がまとめられて、LINEグループに即座に届きます。支援者は、場所も注意事項も、すぐに確認できます。");

  // ============================================================
  // SLIDE 6: LINE NOTIFICATION DETAIL
  // ============================================================
  let s6 = pres.addSlide();
  s6.background = { color: C.lightGray };

  s6.addText("支援者のスマホに届くメッセージ", {
    x: 0.5, y: 0.3, w: 9, h: 0.7,
    fontSize: 26, fontFace: "Georgia", color: C.dark, bold: true, margin: 0
  });

  // Left: Supporters receiving notification
  // Supporter 1
  addPersonIllustration(s6, pres, 0.8, 1.5, 0.9, "FBBF24", C.secondary);
  s6.addText("相談支援員", {
    x: 0.5, y: 2.7, w: 1.5, h: 0.3,
    fontSize: 11, fontFace: "Calibri", color: C.gray, align: "center"
  });
  // Supporter 2
  addPersonIllustration(s6, pres, 0.8, 3.2, 0.9, "FBBF24", "3B82F6");
  s6.addText("GH職員", {
    x: 0.5, y: 4.4, w: 1.5, h: 0.3,
    fontSize: 11, fontFace: "Calibri", color: C.gray, align: "center"
  });

  // Bell icons
  s6.addImage({ data: icons.bell, x: 1.9, y: 1.8, w: 0.4, h: 0.4 });
  s6.addImage({ data: icons.bell, x: 1.9, y: 3.5, w: 0.4, h: 0.4 });

  // LINE message (large, detailed)
  s6.addShape(pres.shapes.RECTANGLE, {
    x: 2.8, y: 1.2, w: 6.7, h: 4.0,
    fill: { color: C.white }, shadow: makeShadow(),
    line: { color: "06C755", width: 2 }, rectRadius: 0.1
  });

  // LINE header
  s6.addShape(pres.shapes.RECTANGLE, {
    x: 2.8, y: 1.2, w: 6.7, h: 0.5,
    fill: { color: "06C755" }, rectRadius: 0
  });
  s6.addText("LINE グループ通知", {
    x: 2.8, y: 1.2, w: 6.7, h: 0.5,
    fontSize: 14, fontFace: "Calibri", color: C.white, bold: true, align: "center", valign: "middle"
  });

  s6.addText([
    { text: "🆘 緊急SOS: たけしさんからの発信", options: { fontSize: 16, bold: true, color: C.accent, breakLine: true } },
    { text: "", options: { fontSize: 8, breakLine: true } },
    { text: "⏰ 発信時刻: 2026/02/21 14:30", options: { fontSize: 13, color: C.dark, breakLine: true } },
    { text: "", options: { fontSize: 8, breakLine: true } },
    { text: "📍 現在地:", options: { fontSize: 13, bold: true, color: C.dark, breakLine: true } },
    { text: "https://www.google.com/maps?q=35.xxx,139.xxx", options: { fontSize: 11, color: "3B82F6", breakLine: true } },
    { text: "", options: { fontSize: 8, breakLine: true } },
    { text: "⚠️ 対応時の注意:", options: { fontSize: 13, bold: true, color: C.accent, breakLine: true } },
    { text: "🔴 大きな声で指示しない（パニック悪化）", options: { fontSize: 12, color: C.dark, breakLine: true } },
    { text: "🔴 無理に移動させない（転倒リスク）", options: { fontSize: 12, color: C.dark, breakLine: true } },
    { text: "", options: { fontSize: 8, breakLine: true } },
    { text: "📞 緊急連絡先:", options: { fontSize: 13, bold: true, color: C.primary, breakLine: true } },
    { text: "  1. 母・山田花子  090-xxxx-xxxx", options: { fontSize: 12, color: C.dark, breakLine: true } },
    { text: "  2. GH・田中     070-xxxx-xxxx", options: { fontSize: 12, color: C.dark } },
  ], { x: 3.1, y: 1.85, w: 6.1, h: 3.2 });

  s6.addNotes("【ナレーション】\n支援者のスマホに、このようなメッセージが届きます。\n\nLINEのグループ通知として、SOSの発信時刻、Googleマップへのリンク付きの現在地、対応時に絶対やってはいけないこと、そして緊急連絡先が一目でわかります。\n\n駆けつける前に、注意事項を確認できる。これが二次被害を防ぎます。");

  // ============================================================
  // SLIDE 7: SYSTEM OVERVIEW
  // ============================================================
  let s7 = pres.addSlide();
  s7.background = { color: C.white };

  s7.addText("システム全体像", {
    x: 0.5, y: 0.2, w: 9, h: 0.6,
    fontSize: 26, fontFace: "Georgia", color: C.dark, bold: true, margin: 0
  });

  // Top row: Data sources
  // Mother/Family
  s7.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.1, w: 2.0, h: 1.0,
    fill: { color: C.warmBg }, shadow: makeCardShadow(), rectRadius: 0.05
  });
  s7.addImage({ data: icons.user, x: 0.65, y: 1.2, w: 0.35, h: 0.35 });
  s7.addText("保護者の言葉\n支援記録", {
    x: 1.05, y: 1.15, w: 1.3, h: 0.9,
    fontSize: 12, fontFace: "Calibri", color: C.dark, valign: "middle", margin: 0
  });

  // Documents
  s7.addShape(pres.shapes.RECTANGLE, {
    x: 2.8, y: 1.1, w: 2.0, h: 1.0,
    fill: { color: C.warmBg }, shadow: makeCardShadow(), rectRadius: 0.05
  });
  s7.addImage({ data: icons.fileAlt, x: 2.95, y: 1.2, w: 0.35, h: 0.35 });
  s7.addText("Word/Excel\nPDF", {
    x: 3.35, y: 1.15, w: 1.3, h: 0.9,
    fontSize: 12, fontFace: "Calibri", color: C.dark, valign: "middle", margin: 0
  });

  // Supporter notes
  s7.addShape(pres.shapes.RECTANGLE, {
    x: 5.1, y: 1.1, w: 2.0, h: 1.0,
    fill: { color: C.warmBg }, shadow: makeCardShadow(), rectRadius: 0.05
  });
  s7.addImage({ data: icons.clipboard, x: 5.25, y: 1.2, w: 0.35, h: 0.35 });
  s7.addText("日々の\n支援メモ", {
    x: 5.65, y: 1.15, w: 1.3, h: 0.9,
    fontSize: 12, fontFace: "Calibri", color: C.dark, valign: "middle", margin: 0
  });

  // Arrows down
  s7.addImage({ data: icons.arrowDown, x: 1.3, y: 2.2, w: 0.35, h: 0.35 });
  s7.addImage({ data: icons.arrowDown, x: 3.6, y: 2.2, w: 0.35, h: 0.35 });
  s7.addImage({ data: icons.arrowDown, x: 5.9, y: 2.2, w: 0.35, h: 0.35 });

  // Center: Claude Desktop + Neo4j
  s7.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 2.7, w: 6.6, h: 1.2,
    fill: { color: C.purpleLight }, shadow: makeShadow(), rectRadius: 0.08
  });
  s7.addImage({ data: icons.comments, x: 0.8, y: 2.9, w: 0.55, h: 0.55 });
  s7.addText("Claude Desktop", {
    x: 1.4, y: 2.8, w: 2.5, h: 0.5,
    fontSize: 18, fontFace: "Georgia", color: C.purple, bold: true, valign: "middle", margin: 0
  });
  s7.addText("自動構造化 + 知識蓄積", {
    x: 1.4, y: 3.3, w: 2.5, h: 0.4,
    fontSize: 13, fontFace: "Calibri", color: C.gray, margin: 0
  });

  // Neo4j database icon
  s7.addShape(pres.shapes.OVAL, {
    x: 5.2, y: 2.85, w: 1.6, h: 0.9,
    fill: { color: C.primary }
  });
  s7.addText("Neo4j\n知識DB", {
    x: 5.2, y: 2.85, w: 1.6, h: 0.9,
    fontSize: 13, fontFace: "Calibri", color: C.white, bold: true,
    align: "center", valign: "middle"
  });

  // Bottom row: 3 outputs
  s7.addImage({ data: icons.arrowDown, x: 1.5, y: 4.0, w: 0.35, h: 0.35 });
  s7.addImage({ data: icons.arrowDown, x: 3.7, y: 4.0, w: 0.35, h: 0.35 });
  s7.addImage({ data: icons.arrowDown, x: 5.9, y: 4.0, w: 0.35, h: 0.35 });

  // Output 1: Query
  s7.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 4.5, w: 2.0, h: 0.9,
    fill: { color: C.light }, shadow: makeCardShadow(), rectRadius: 0.05
  });
  s7.addImage({ data: icons.search, x: 0.65, y: 4.6, w: 0.3, h: 0.3 });
  s7.addText("質問・相談", {
    x: 1.0, y: 4.55, w: 1.3, h: 0.4,
    fontSize: 13, fontFace: "Calibri", color: C.dark, bold: true, valign: "middle", margin: 0
  });
  s7.addText("「この子のこと教えて」", {
    x: 0.65, y: 4.95, w: 1.7, h: 0.35,
    fontSize: 10, fontFace: "Calibri", color: C.gray, margin: 0
  });

  // Output 2: Proposal
  s7.addShape(pres.shapes.RECTANGLE, {
    x: 2.8, y: 4.5, w: 2.0, h: 0.9,
    fill: { color: C.light }, shadow: makeCardShadow(), rectRadius: 0.05
  });
  s7.addImage({ data: icons.lightbulb, x: 2.95, y: 4.6, w: 0.3, h: 0.3 });
  s7.addText("提案・分析", {
    x: 3.3, y: 4.55, w: 1.3, h: 0.4,
    fontSize: 13, fontFace: "Calibri", color: C.dark, bold: true, valign: "middle", margin: 0
  });
  s7.addText("「次の支援計画は」", {
    x: 2.95, y: 4.95, w: 1.7, h: 0.35,
    fontSize: 10, fontFace: "Calibri", color: C.gray, margin: 0
  });

  // Output 3: SOS
  s7.addShape(pres.shapes.RECTANGLE, {
    x: 5.1, y: 4.5, w: 2.0, h: 0.9,
    fill: { color: C.accentLight }, shadow: makeCardShadow(), rectRadius: 0.05
  });
  s7.addImage({ data: icons.mobile, x: 5.25, y: 4.6, w: 0.3, h: 0.3 });
  s7.addText("SOS通知", {
    x: 5.6, y: 4.55, w: 1.3, h: 0.4,
    fontSize: 13, fontFace: "Calibri", color: C.accent, bold: true, valign: "middle", margin: 0
  });
  s7.addText("ワンタップで緊急連絡", {
    x: 5.25, y: 4.95, w: 1.7, h: 0.35,
    fontSize: 10, fontFace: "Calibri", color: C.gray, margin: 0
  });

  // Right side: Features list
  s7.addShape(pres.shapes.RECTANGLE, {
    x: 7.5, y: 1.1, w: 2.2, h: 4.3,
    fill: { color: C.dark }, rectRadius: 0.1
  });
  s7.addText("必要なもの", {
    x: 7.5, y: 1.25, w: 2.2, h: 0.4,
    fontSize: 14, fontFace: "Calibri", color: C.white, bold: true, align: "center"
  });

  const features = [
    { icon: icons.commentsT, label: "Claude Desktop", sub: "無料" },
    { icon: icons.database, label: "Docker", sub: "無料" },
    { icon: icons.shield, label: "Neo4j", sub: "無料" },
  ];

  features.forEach((f, i) => {
    const yy = 1.85 + i * 0.85;
    s7.addShape(pres.shapes.RECTANGLE, {
      x: 7.7, y: yy, w: 1.8, h: 0.7,
      fill: { color: "475569" }, rectRadius: 0.05
    });
    s7.addText(f.label, {
      x: 7.7, y: yy + 0.05, w: 1.8, h: 0.35,
      fontSize: 13, fontFace: "Calibri", color: C.white, bold: true, align: "center", margin: 0
    });
    s7.addText(f.sub, {
      x: 7.7, y: yy + 0.38, w: 1.8, h: 0.25,
      fontSize: 12, fontFace: "Calibri", color: "4ADE80", bold: true, align: "center", margin: 0
    });
  });

  s7.addText("すべて無料", {
    x: 7.5, y: 4.6, w: 2.2, h: 0.5,
    fontSize: 18, fontFace: "Georgia", color: "16A34A", bold: true, align: "center"
  });

  s7.addNotes("【ナレーション】\nシステムの全体像です。\n\n上から、保護者の言葉、Word・Excel・PDFの書類、日々の支援メモ。これらの生のデータがClaude Desktopに入力されます。\n\nClaude Desktopが自動的にデータを構造化し、Neo4jという知識データベースに蓄積します。\n\nそこから3つのことができます。質問・相談、提案・分析、そしてSOSの緊急通知です。\n\n必要なものは、Claude Desktop、Docker、Neo4j。すべて無料です。");

  // ============================================================
  // SLIDE 8: CLOSING
  // ============================================================
  let s8 = pres.addSlide();
  s8.background = { color: C.dark };

  // Decorative teal bar
  s8.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.secondary }
  });

  // Heart icon
  s8.addImage({ data: icons.heartWhite, x: 4.55, y: 0.5, w: 0.9, h: 0.9 });

  s8.addText("親がいなくなっても\nこの子のことを知っている\n「記憶」が残る。", {
    x: 1, y: 1.2, w: 8, h: 1.8,
    fontSize: 30, fontFace: "Georgia", color: C.white,
    bold: true, align: "center", lineSpacingMultiple: 1.5
  });

  s8.addText("それが、このシステムの目的です。", {
    x: 1, y: 3.2, w: 8, h: 0.6,
    fontSize: 18, fontFace: "Calibri", color: "94A3B8", align: "center"
  });

  // Divider
  s8.addShape(pres.shapes.RECTANGLE, {
    x: 3.5, y: 4.0, w: 3, h: 0.02, fill: { color: "475569" }
  });

  // Open source badge
  s8.addText("オープンソース・無償提供", {
    x: 1, y: 4.15, w: 8, h: 0.5,
    fontSize: 16, fontFace: "Calibri", color: C.secondary, bold: true, align: "center"
  });

  s8.addImage({ data: icons.github, x: 2.8, y: 4.65, w: 0.35, h: 0.35 });
  s8.addText("github.com/kazumasakawahara/neo4j-agno-agent", {
    x: 3.2, y: 4.65, w: 5.5, h: 0.35,
    fontSize: 14, fontFace: "Calibri", color: C.white, valign: "middle", margin: 0,
    hyperlink: { url: "https://github.com/kazumasakawahara/neo4j-agno-agent" }
  });

  s8.addText("導入サポート（無償）もお気軽にご連絡ください", {
    x: 1, y: 5.05, w: 8, h: 0.35,
    fontSize: 13, fontFace: "Calibri", color: "94A3B8", align: "center"
  });

  s8.addNotes("【ナレーション】\n親がいなくなっても、この子のことを知っている「記憶」が残る。\n\nそれが、このシステムの目的です。\n\nオープンソースで、無償で提供しています。導入のサポートも無償で行っています。\n\nGitHubからダウンロードできます。ぜひ、必要としている方に届けてください。");

  // ============================================================
  // WRITE FILE
  // ============================================================
  const outputPath = "/Users/k-kawahara/Dev-Work/neo4j-agno-agent/docs/demo_video.pptx";
  await pres.writeFile({ fileName: outputPath });
  console.log(`✅ Presentation saved to: ${outputPath}`);
}

createPresentation().catch(err => {
  console.error("❌ Error:", err);
  process.exit(1);
});
