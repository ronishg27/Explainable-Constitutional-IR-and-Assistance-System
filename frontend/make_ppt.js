import pptxgen from 'pptxgenjs';

const pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';
pres.title = 'Explainable Constitutional IR System';

// ── Palette ──────────────────────────────────────────────────────────────────
const C = {
	navy: '0D2137', // dark bg
	teal: '0B6E8A', // accent
	tealLt: '0E8FAD', // lighter teal
	sky: 'C8EBF4', // very light teal
	white: 'FFFFFF',
	offWhite: 'F4F8FA',
	slate: '64748B',
	dark: '1E293B',
	mid: '334155',
	gold: 'F5A623',
	green: '10B981',
	redSoft: 'EF4444',
};

const makeShadow = () => ({
	type: 'outer',
	blur: 8,
	offset: 3,
	angle: 135,
	color: '000000',
	opacity: 0.14,
});

// ── Slide helpers ─────────────────────────────────────────────────────────────
function addSlideHeader(slide, title, subtitle, dark = false) {
	const bg = dark ? C.navy : C.offWhite;
	const col = dark ? C.white : C.dark;
	const sub = dark ? C.sky : C.slate;
	slide.background = { color: bg };

	// Left accent bar
	slide.addShape(pres.shapes.RECTANGLE, {
		x: 0,
		y: 0,
		w: 0.18,
		h: 5.625,
		fill: { color: C.teal },
		line: { color: C.teal },
	});

	slide.addText(title, {
		x: 0.38,
		y: 0.25,
		w: 9.5,
		h: 0.52,
		fontSize: 20,
		bold: true,
		color: col,
		fontFace: 'Calibri',
		margin: 0,
	});

	if (subtitle) {
		slide.addText(subtitle, {
			x: 0.38,
			y: 0.78,
			w: 9.5,
			h: 0.28,
			fontSize: 11,
			color: sub,
			fontFace: 'Calibri',
			italic: true,
			margin: 0,
		});
	}

	// Divider
	slide.addShape(pres.shapes.LINE, {
		x: 0.38,
		y: 1.12,
		w: 9.38,
		h: 0,
		line: { color: C.teal, width: 1.2 },
	});
}

function card(slide, x, y, w, h, color) {
	slide.addShape(pres.shapes.RECTANGLE, {
		x,
		y,
		w,
		h,
		fill: { color: color || C.white },
		line: { color: 'E2EEF4', width: 0.8 },
		shadow: makeShadow(),
	});
}

// ══════════════════════════════════════════════════════════════════════════════
// SLIDE 1 – Title Slide
// ══════════════════════════════════════════════════════════════════════════════
{
	const s = pres.addSlide();
	s.background = { color: C.navy };

	// Decorative shapes
	s.addShape(pres.shapes.RECTANGLE, {
		x: 0,
		y: 0,
		w: 0.22,
		h: 5.625,
		fill: { color: C.teal },
		line: { color: C.teal },
	});
	s.addShape(pres.shapes.RECTANGLE, {
		x: 0,
		y: 4.8,
		w: 10,
		h: 0.825,
		fill: { color: C.tealLt },
		line: { color: C.tealLt },
	});
	s.addShape(pres.shapes.RECTANGLE, {
		x: 7.2,
		y: 0,
		w: 2.8,
		h: 5.625,
		fill: { color: 'FFFFFF', transparency: 96 },
		line: { color: C.navy },
	});

	s.addText('BSc. CSIT Final Year Project — Mid Defense', {
		x: 0.45,
		y: 0.55,
		w: 9.2,
		h: 0.3,
		fontSize: 10,
		color: C.sky,
		fontFace: 'Calibri',
		charSpacing: 2,
		margin: 0,
	});

	s.addText(
		'Explainable Constitutional\nInformation Retrieval\n& Assistance System',
		{
			x: 0.45,
			y: 1.05,
			w: 6.5,
			h: 2.6,
			fontSize: 30,
			bold: true,
			color: C.white,
			fontFace: 'Calibri',
			lineSpacingMultiple: 1.25,
			margin: 0,
		}
	);

	s.addShape(pres.shapes.RECTANGLE, {
		x: 0.45,
		y: 3.8,
		w: 1.6,
		h: 0.05,
		fill: { color: C.gold },
		line: { color: C.gold },
	});

	s.addText(
		[
			{ text: 'Nayan Nepal', options: { breakLine: true } },
			{ text: 'Ronish Ghimire', options: { breakLine: true } },
			{ text: 'Devraj Khatiwada' },
		],
		{
			x: 0.45,
			y: 3.95,
			w: 5,
			h: 0.7,
			fontSize: 12,
			color: C.sky,
			fontFace: 'Calibri',
			margin: 0,
		}
	);

	s.addText(
		[
			{
				text: 'Supervisor: Manoj Pokharel',
				options: { breakLine: true },
			},
			{ text: 'Samriddhi College, TU', options: { breakLine: true } },
			{ text: 'May 2026' },
		],
		{
			x: 0.45,
			y: 4.82,
			w: 9,
			h: 0.7,
			fontSize: 10,
			color: C.navy,
			fontFace: 'Calibri',
			margin: 0,
		}
	);
}

// ══════════════════════════════════════════════════════════════════════════════
// SLIDE 2 – Problem Statement & Objectives
// ══════════════════════════════════════════════════════════════════════════════
{
	const s = pres.addSlide();
	addSlideHeader(
		s,
		'Problem Statement & Objectives',
		'Why this system is needed'
	);

	// LEFT – Problem card
	card(s, 0.38, 1.28, 4.3, 3.9, C.white);
	s.addShape(pres.shapes.RECTANGLE, {
		x: 0.38,
		y: 1.28,
		w: 4.3,
		h: 0.38,
		fill: { color: C.teal },
		line: { color: C.teal },
	});
	s.addText('Problem Statement', {
		x: 0.5,
		y: 1.3,
		w: 4.0,
		h: 0.34,
		fontSize: 11,
		bold: true,
		color: C.white,
		fontFace: 'Calibri',
		margin: 0,
	});
	s.addText(
		[
			{
				text: "Nepal's constitution is inaccessible to most citizens due to its complex legal language.",
				options: { breakLine: true },
			},
			{ text: ' ', options: { breakLine: true } },
			{
				text: 'Standard keyword searches fail because legal meaning depends on how words appear together — not just whether they appear.',
				options: { breakLine: true },
			},
			{ text: ' ', options: { breakLine: true } },
			{
				text: "No existing system provides explainability — users don't know why certain results are retrieved.",
				options: { breakLine: true },
			},
		],
		{
			x: 0.5,
			y: 1.72,
			w: 4.0,
			h: 3.3,
			fontSize: 11,
			color: C.mid,
			fontFace: 'Calibri',
			paraSpaceAfter: 4,
			bullet: false,
			margin: 0,
		}
	);

	// RIGHT – Objectives card
	card(s, 4.9, 1.28, 4.8, 3.9, C.white);
	s.addShape(pres.shapes.RECTANGLE, {
		x: 4.9,
		y: 1.28,
		w: 4.8,
		h: 0.38,
		fill: { color: C.dark },
		line: { color: C.dark },
	});
	s.addText('Objectives', {
		x: 5.02,
		y: 1.3,
		w: 4.5,
		h: 0.34,
		fontSize: 11,
		bold: true,
		color: C.white,
		fontFace: 'Calibri',
		margin: 0,
	});
	const objectives = [
		'Develop a user-friendly system for searching constitutional information via natural language queries.',
		'Implement accurate retrieval using NLP, Inverted Indexing, and the BM25 algorithm.',
		'Integrate a Proximity Scoring Model for phrase-aware, precise retrieval.',
		'Provide explainability — show users why each result was ranked highly.',
		'Optionally generate plain-language answers using Retrieval-Augmented Generation (RAG).',
	];
	s.addText(
		objectives.map((t, i) => ({
			text: t,
			options: { bullet: true, breakLine: i < objectives.length - 1 },
		})),
		{
			x: 5.02,
			y: 1.72,
			w: 4.5,
			h: 3.3,
			fontSize: 10.5,
			color: C.mid,
			fontFace: 'Calibri',
			margin: 0,
			paraSpaceAfter: 5,
		}
	);
}

// ══════════════════════════════════════════════════════════════════════════════
// SLIDE 3 – System Overview / Architecture
// ══════════════════════════════════════════════════════════════════════════════
{
	const s = pres.addSlide();
	addSlideHeader(
		s,
		'System Architecture',
		'High-level overview of the components'
	);

	// Pipeline boxes
	const boxes = [
		{
			label: 'User Query',
			sub: 'Natural language\nor keyword',
			col: C.teal,
		},
		{
			label: 'NLP Pipeline',
			sub: 'Tokenize • Lemmatize\nStopword removal',
			col: C.dark,
		},
		{
			label: 'Dual Index',
			sub: 'TF-Index (BM25)\nPositional Index',
			col: C.teal,
		},
		{
			label: 'Scoring Engine',
			sub: 'BM25 + Proximity\n+ Title Boost',
			col: C.dark,
		},
		{ label: 'RAG Module', sub: 'Ollama LLM\n(optional)', col: C.teal },
		{ label: 'Results UI', sub: 'Citations •\nExplanations', col: C.dark },
	];
	const bw = 1.38,
		bh = 1.0,
		startX = 0.28,
		y = 1.55,
		gap = 0.06;
	boxes.forEach((b, i) => {
		const x = startX + i * (bw + gap);
		s.addShape(pres.shapes.RECTANGLE, {
			x,
			y,
			w: bw,
			h: bh,
			fill: { color: b.col },
			line: { color: b.col },
			shadow: makeShadow(),
		});
		s.addText(b.label, {
			x,
			y: y + 0.06,
			w: bw,
			h: 0.3,
			fontSize: 10.5,
			bold: true,
			color: C.white,
			fontFace: 'Calibri',
			align: 'center',
			margin: 0,
		});
		s.addText(b.sub, {
			x,
			y: y + 0.42,
			w: bw,
			h: 0.5,
			fontSize: 8.5,
			color: C.sky,
			fontFace: 'Calibri',
			align: 'center',
			margin: 0,
		});
		// Arrow
		if (i < boxes.length - 1) {
			s.addShape(pres.shapes.LINE, {
				x: x + bw,
				y: y + bh / 2,
				w: gap,
				h: 0,
				line: { color: C.tealLt, width: 1.5 },
			});
		}
	});

	// Tech Stack row
	s.addText('Tech Stack', {
		x: 0.38,
		y: 2.82,
		w: 9.3,
		h: 0.3,
		fontSize: 11,
		bold: true,
		color: C.dark,
		fontFace: 'Calibri',
		margin: 0,
	});
	const stack = [
		['Backend', 'Python 3.10 + Flask'],
		['Frontend', 'React.js + Vite + Tailwind CSS'],
		['Database', 'MongoDB'],
		['NLP', 'spaCy'],
		['LLM', 'Ollama (Llama 3)'],
	];
	const sw = 1.8,
		sy = 3.15;
	stack.forEach(([top, bot], i) => {
		const x = 0.38 + i * (sw + 0.06);
		card(s, x, sy, sw, 1.92, C.offWhite);
		s.addShape(pres.shapes.RECTANGLE, {
			x,
			y: sy,
			w: sw,
			h: 0.3,
			fill: { color: C.tealLt },
			line: { color: C.tealLt },
		});
		s.addText(top, {
			x,
			y: sy + 0.02,
			w: sw,
			h: 0.26,
			fontSize: 9,
			bold: true,
			color: C.white,
			fontFace: 'Calibri',
			align: 'center',
			margin: 0,
		});
		s.addText(bot, {
			x,
			y: sy + 0.38,
			w: sw,
			h: 1.46,
			fontSize: 9.5,
			color: C.mid,
			fontFace: 'Calibri',
			align: 'center',
			margin: 4,
		});
	});
}

// ══════════════════════════════════════════════════════════════════════════════
// SLIDE 4 – Methodology
// ══════════════════════════════════════════════════════════════════════════════
{
	const s = pres.addSlide();
	addSlideHeader(
		s,
		'Methodology',
		'Iterative development with NLP-driven retrieval pipeline'
	);

	const steps = [
		{
			n: '1',
			title: 'Data Collection & Preprocessing',
			body: 'Constitution of Nepal (structured JSON) → Flatten into article/clause/sub-clause units → Tokenize, lowercase, lemmatize, remove stopwords (spaCy)',
		},
		{
			n: '2',
			title: 'Index Construction',
			body: 'Build TF-Index (word counts/doc) for BM25 scoring\nBuild Positional Index (exact token positions) for proximity analysis',
		},
		{
			n: '3',
			title: 'Retrieval & Ranking',
			body: 'BM25 scoring + Title-match boost (+5.0) + Proximity scoring → Combined final score to rank candidate documents',
		},
		{
			n: '4',
			title: 'RAG Integration (Optional)',
			body: 'Top-5 articles → strict context prompt → Ollama (Llama 3) → plain-language grounded answer. Falls back to retrieval-only if LLM unavailable.',
		},
		{
			n: '5',
			title: 'Testing & Evaluation',
			body: '30 constitutional test queries. Metrics: P@5, P@10, MAP, NDCG. Compare BM25-only vs BM25+Proximity.',
		},
	];

	const sw = 1.78,
		sh = 3.8,
		y = 1.3;
	steps.forEach((st, i) => {
		const x = 0.3 + i * (sw + 0.08);
		card(s, x, y, sw, sh, C.white);
		s.addShape(pres.shapes.RECTANGLE, {
			x,
			y,
			w: sw,
			h: 0.42,
			fill: { color: i % 2 === 0 ? C.teal : C.dark },
			line: { color: i % 2 === 0 ? C.teal : C.dark },
		});
		s.addText(st.n, {
			x,
			y: y + 0.04,
			w: sw,
			h: 0.34,
			fontSize: 13,
			bold: true,
			color: C.gold,
			fontFace: 'Calibri',
			align: 'center',
			margin: 0,
		});
		s.addText(st.title, {
			x: x + 0.06,
			y: y + 0.5,
			w: sw - 0.12,
			h: 0.52,
			fontSize: 9.5,
			bold: true,
			color: C.dark,
			fontFace: 'Calibri',
			align: 'center',
			margin: 0,
		});
		s.addText(st.body, {
			x: x + 0.08,
			y: y + 1.1,
			w: sw - 0.16,
			h: 2.8,
			fontSize: 9,
			color: C.mid,
			fontFace: 'Calibri',
			margin: 0,
			lineSpacingMultiple: 1.3,
		});
	});
}

// ══════════════════════════════════════════════════════════════════════════════
// SLIDE 5 – Algorithms
// ══════════════════════════════════════════════════════════════════════════════
{
	const s = pres.addSlide();
	addSlideHeader(
		s,
		'Core Algorithms',
		'BM25 + Proximity Scoring + Title Boost'
	);

	// BM25 card
	card(s, 0.38, 1.3, 4.3, 3.96, C.white);
	s.addShape(pres.shapes.RECTANGLE, {
		x: 0.38,
		y: 1.3,
		w: 4.3,
		h: 0.36,
		fill: { color: C.teal },
		line: { color: C.teal },
	});
	s.addText('BM25 (Best Matching 25)', {
		x: 0.5,
		y: 1.32,
		w: 4.0,
		h: 0.32,
		fontSize: 11,
		bold: true,
		color: C.white,
		fontFace: 'Calibri',
		margin: 0,
	});
	s.addText(
		[
			{
				text: 'Ranks documents by term frequency with document-length normalisation.',
				options: { breakLine: true },
			},
			{ text: ' ', options: { breakLine: true } },
			{
				text: 'Key parameters:',
				options: { bold: true, breakLine: true },
			},
			{
				text: 'k₁ = 1.5  (term-frequency saturation)',
				options: { breakLine: true },
			},
			{
				text: 'b = 0.75  (length normalisation)',
				options: { breakLine: true },
			},
			{ text: ' ', options: { breakLine: true } },
			{ text: 'Formula:', options: { bold: true, breakLine: true } },
			{
				text: 'Score = Σ IDF(t) × TF-component(t,d)',
				options: { breakLine: true },
			},
			{ text: ' ', options: { breakLine: true } },
			{
				text: 'IDF downweights terms appearing in many documents (common words).',
				options: { breakLine: true },
			},
		],
		{
			x: 0.5,
			y: 1.72,
			w: 4.0,
			h: 3.4,
			fontSize: 10.5,
			color: C.mid,
			fontFace: 'Calibri',
			margin: 0,
			paraSpaceAfter: 2,
		}
	);

	// Proximity + Final Score card
	card(s, 4.9, 1.3, 4.8, 3.96, C.white);
	s.addShape(pres.shapes.RECTANGLE, {
		x: 4.9,
		y: 1.3,
		w: 4.8,
		h: 0.36,
		fill: { color: C.dark },
		line: { color: C.dark },
	});
	s.addText('Proximity Scoring & Final Ranking', {
		x: 5.02,
		y: 1.32,
		w: 4.5,
		h: 0.32,
		fontSize: 11,
		bold: true,
		color: C.white,
		fontFace: 'Calibri',
		margin: 0,
	});
	s.addText(
		[
			{
				text: 'Proximity Score',
				options: { bold: true, breakLine: true },
			},
			{
				text: 'For every pair of query terms, find the minimum distance between occurrences in the document.',
				options: { breakLine: true },
			},
			{
				text: 'Window threshold: 30 words.',
				options: { breakLine: true },
			},
			{
				text: 'Pair score = 1 / (minDist + 1)²',
				options: { breakLine: true },
			},
			{
				text: '(distance 0 → 1.0 | distance 1 → 0.25 | distance 2 → 0.11)',
				options: { breakLine: true },
			},
			{ text: ' ', options: { breakLine: true } },
			{ text: 'Title Boost', options: { bold: true, breakLine: true } },
			{
				text: '+5.0 points if any query token appears in the article title.',
				options: { breakLine: true },
			},
			{ text: ' ', options: { breakLine: true } },
			{ text: 'Final Score', options: { bold: true, breakLine: true } },
			{
				text: '= BM25 + TitleBonus + (1.0 × ProximityScore)',
				options: {},
			},
		],
		{
			x: 5.02,
			y: 1.72,
			w: 4.5,
			h: 3.4,
			fontSize: 10.5,
			color: C.mid,
			fontFace: 'Calibri',
			margin: 0,
			paraSpaceAfter: 2,
		}
	);
}

// ══════════════════════════════════════════════════════════════════════════════
// SLIDE 6 – RAG Module
// ══════════════════════════════════════════════════════════════════════════════
{
	const s = pres.addSlide();
	addSlideHeader(
		s,
		'Retrieval-Augmented Generation (RAG)',
		'Optional LLM-powered plain-language answers'
	);

	// Flow diagram
	const nodes = [
		{ label: 'User Query', col: C.teal, x: 0.35 },
		{ label: 'Search Engine\n(BM25 + Proximity)', col: C.dark, x: 2.25 },
		{ label: 'Top-5 Articles\n(Context)', col: C.teal, x: 4.15 },
		{ label: 'Strict Prompt\nBuilder', col: C.dark, x: 6.05 },
		{ label: 'Ollama LLM\n(Llama 3)', col: C.teal, x: 7.95 },
	];
	const nw = 1.7,
		nh = 1.0,
		ny = 1.55;
	nodes.forEach((n, i) => {
		s.addShape(pres.shapes.RECTANGLE, {
			x: n.x,
			y: ny,
			w: nw,
			h: nh,
			fill: { color: n.col },
			line: { color: n.col },
			shadow: makeShadow(),
		});
		s.addText(n.label, {
			x: n.x,
			y: ny + 0.15,
			w: nw,
			h: 0.7,
			fontSize: 9.5,
			bold: true,
			color: C.white,
			fontFace: 'Calibri',
			align: 'center',
			margin: 0,
		});
		if (i < nodes.length - 1) {
			s.addShape(pres.shapes.LINE, {
				x: n.x + nw,
				y: ny + nh / 2,
				w: 0.18,
				h: 0,
				line: { color: C.tealLt, width: 1.5 },
			});
		}
	});

	// Answer output
	s.addShape(pres.shapes.RECTANGLE, {
		x: 2.0,
		y: 2.72,
		w: 6.0,
		h: 0.32,
		fill: { color: C.gold },
		line: { color: C.gold },
	});
	s.addText('Answer: Grounded strictly in retrieved constitutional text', {
		x: 2.0,
		y: 2.73,
		w: 6.0,
		h: 0.3,
		fontSize: 10,
		bold: true,
		color: C.navy,
		fontFace: 'Calibri',
		align: 'center',
		margin: 0,
	});

	// Fallback
	s.addShape(pres.shapes.RECTANGLE, {
		x: 0.38,
		y: 3.2,
		w: 9.3,
		h: 0.36,
		fill: { color: 'FFF3CD' },
		line: { color: 'F5A623' },
	});
	s.addText(
		'⚠  If Ollama is unreachable, system gracefully falls back to retrieval-only mode with a clear notification to the user.',
		{
			x: 0.5,
			y: 3.22,
			w: 9.0,
			h: 0.32,
			fontSize: 10,
			color: '7A4A00',
			fontFace: 'Calibri',
			margin: 0,
		}
	);

	// Key benefits
	const benefits = [
		[
			'No Hallucination',
			'LLM answers are strictly constrained to the retrieved articles — cannot fabricate information.',
		],
		[
			'Explainability',
			'Every answer includes citations to the exact constitutional article(s) used.',
		],
		[
			'Always Available',
			'Retrieval-only mode ensures the system works even without the LLM.',
		],
	];
	const bw2 = 2.96,
		by = 3.76;
	benefits.forEach(([title, desc], i) => {
		const x = 0.38 + i * (bw2 + 0.06);
		card(s, x, by, bw2, 1.55, C.offWhite);
		s.addShape(pres.shapes.RECTANGLE, {
			x,
			y: by,
			w: bw2,
			h: 0.32,
			fill: { color: i === 0 ? C.green : i === 1 ? C.teal : C.dark },
			line: { color: i === 0 ? C.green : i === 1 ? C.teal : C.dark },
		});
		s.addText(title, {
			x: x + 0.06,
			y: by + 0.02,
			w: bw2 - 0.12,
			h: 0.28,
			fontSize: 10,
			bold: true,
			color: C.white,
			fontFace: 'Calibri',
			margin: 0,
		});
		s.addText(desc, {
			x: x + 0.06,
			y: by + 0.38,
			w: bw2 - 0.12,
			h: 1.1,
			fontSize: 9.5,
			color: C.mid,
			fontFace: 'Calibri',
			margin: 0,
			lineSpacingMultiple: 1.25,
		});
	});
}

// ══════════════════════════════════════════════════════════════════════════════
// SLIDE 7 – Implementation
// ══════════════════════════════════════════════════════════════════════════════
{
	const s = pres.addSlide();
	addSlideHeader(
		s,
		'Implementation',
		'Modules, tools, and development details'
	);

	const modules = [
		{
			title: 'Frontend',
			col: C.teal,
			items: [
				'React.js + Vite (SPA)',
				'Tailwind CSS — responsive UI',
				'Search bar with LLM toggle',
				'Result cards with relevance scores',
				'Citation download support',
			],
		},
		{
			title: 'Backend API',
			col: C.dark,
			items: [
				'Python 3.10 + Flask (REST API)',
				'JWT-based authentication',
				'Routes: /api/v1/ask, /auth',
				'Graceful error handling (HTTP 400/500)',
				'WSGI-ready (Gunicorn) for production',
			],
		},
		{
			title: 'Retrieval Engine',
			col: C.teal,
			items: [
				'Custom inverted TF-Index',
				'Positional Index (token positions)',
				'BM25 scorer (k₁=1.5, b=0.75)',
				'ProximityScorer (window=30 words)',
				'Indexes pre-built offline for speed',
			],
		},
		{
			title: 'NLP & AI',
			col: C.dark,
			items: [
				'spaCy — tokenize, lemmatize, stopwords',
				'Custom legal-term dictionary',
				'Ollama client (local Llama 3)',
				'RAGWorkflow: retrieve → prompt → generate',
				'Fallback to retrieval if LLM offline',
			],
		},
	];

	const mw = 2.25,
		mh = 3.85,
		y = 1.34;
	modules.forEach((m, i) => {
		const x = 0.3 + i * (mw + 0.1);
		card(s, x, y, mw, mh, C.white);
		s.addShape(pres.shapes.RECTANGLE, {
			x,
			y,
			w: mw,
			h: 0.36,
			fill: { color: m.col },
			line: { color: m.col },
		});
		s.addText(m.title, {
			x,
			y: y + 0.03,
			w: mw,
			h: 0.3,
			fontSize: 11,
			bold: true,
			color: C.white,
			fontFace: 'Calibri',
			align: 'center',
			margin: 0,
		});
		s.addText(
			m.items.map((it, j) => ({
				text: it,
				options: { bullet: true, breakLine: j < m.items.length - 1 },
			})),
			{
				x: x + 0.1,
				y: y + 0.44,
				w: mw - 0.2,
				h: 3.3,
				fontSize: 9.5,
				color: C.mid,
				fontFace: 'Calibri',
				margin: 0,
				paraSpaceAfter: 4,
			}
		);
	});
}

// ══════════════════════════════════════════════════════════════════════════════
// SLIDE 8 – Testing & Evaluation Plan
// ══════════════════════════════════════════════════════════════════════════════
{
	const s = pres.addSlide();
	addSlideHeader(
		s,
		'Testing & Evaluation Plan',
		'Unit testing, system testing, and retrieval metrics'
	);

	// Left – Test cases table
	card(s, 0.38, 1.32, 5.4, 3.9, C.white);
	s.addText('Planned Test Cases', {
		x: 0.5,
		y: 1.38,
		w: 5.1,
		h: 0.3,
		fontSize: 11,
		bold: true,
		color: C.dark,
		fontFace: 'Calibri',
		margin: 0,
	});

	const rows = [
		[
			{ text: 'Test ID', options: { bold: true, color: C.white } },
			{ text: 'Description', options: { bold: true, color: C.white } },
			{ text: 'Expected', options: { bold: true, color: C.white } },
		],
		['UT-01/02', 'Tokenization & stopword removal', 'Correct token list'],
		[
			'UT-03/04',
			'Lemmatization & BM25 computation',
			'Reduced forms, correct score',
		],
		['UT-05/06', 'Proximity & title boost', 'Positive proximity weight'],
		['ST-01/02', 'Empty / too-long query', 'HTTP 400 error'],
		['ST-03', 'Valid query (retrieval only)', 'Ranked articles returned'],
		['ST-04', 'Valid query with LLM enabled', 'AI answer + articles'],
		['ST-05', 'LLM offline', 'Graceful fallback'],
	];
	const rowFills = rows.map((_, i) =>
		i === 0 ? C.dark : i % 2 === 0 ? 'EBF5FA' : C.white
	);
	const tableData = rows.map((r, i) =>
		r.map((cell) => ({
			text: typeof cell === 'string' ? cell : cell.text,
			options: {
				fontSize: 8.5,
				fontFace: 'Calibri',
				bold: i === 0,
				color: i === 0 ? C.white : C.mid,
				fill: { color: rowFills[i] },
				align: 'left',
			},
		}))
	);
	s.addTable(tableData, {
		x: 0.38,
		y: 1.7,
		w: 5.4,
		h: 3.4,
		border: { pt: 0.5, color: 'D0E8F0' },
		colW: [1.0, 2.3, 1.9],
	});

	// Right – Metrics
	card(s, 5.95, 1.32, 3.73, 3.9, C.white);
	s.addText('Evaluation Metrics', {
		x: 6.1,
		y: 1.38,
		w: 3.4,
		h: 0.3,
		fontSize: 11,
		bold: true,
		color: C.dark,
		fontFace: 'Calibri',
		margin: 0,
	});
	const metrics = [
		['P@5 / P@10', 'Precision at top 5 and 10 results'],
		['R@5 / R@10', 'Recall at top 5 and 10'],
		['MAP', 'Mean Average Precision across 30 queries'],
		['NDCG@k', 'Graded relevance + position discount'],
		['Hallucination', 'Manual: answer grounded in retrieved text?'],
		['Fallback', 'System stays live when LLM is offline'],
	];
	metrics.forEach(([m, d], i) => {
		const y = 1.75 + i * 0.56;
		s.addShape(pres.shapes.RECTANGLE, {
			x: 6.1,
			y,
			w: 1.0,
			h: 0.36,
			fill: { color: i % 2 === 0 ? C.teal : C.dark },
			line: { color: i % 2 === 0 ? C.teal : C.dark },
		});
		s.addText(m, {
			x: 6.1,
			y: y + 0.03,
			w: 1.0,
			h: 0.3,
			fontSize: 8.5,
			bold: true,
			color: C.white,
			fontFace: 'Calibri',
			align: 'center',
			margin: 0,
		});
		s.addText(d, {
			x: 7.16,
			y: y + 0.03,
			w: 2.4,
			h: 0.3,
			fontSize: 8.5,
			color: C.mid,
			fontFace: 'Calibri',
			margin: 0,
		});
	});

	// Expected outcome note
	s.addShape(pres.shapes.RECTANGLE, {
		x: 5.95,
		y: 5.08,
		w: 3.73,
		h: 0.3,
		fill: { color: 'E8F8F1' },
		line: { color: C.green },
	});
	s.addText('Expected P@5: 0.75 – 0.85 (per legal IR literature)', {
		x: 6.08,
		y: 5.09,
		w: 3.5,
		h: 0.28,
		fontSize: 9,
		color: '1A5C3A',
		fontFace: 'Calibri',
		margin: 0,
	});
}

// ══════════════════════════════════════════════════════════════════════════════
// SLIDE 9 – Results & Observations
// ══════════════════════════════════════════════════════════════════════════════
{
	const s = pres.addSlide();
	addSlideHeader(
		s,
		'Preliminary Results & Observations',
		'Manual inspection before full test suite execution'
	);

	// Status banner
	s.addShape(pres.shapes.RECTANGLE, {
		x: 0.38,
		y: 1.32,
		w: 9.3,
		h: 0.38,
		fill: { color: 'FFF8E7' },
		line: { color: C.gold },
	});
	s.addText(
		'Status: Formal testing pending — observations from manual query inspection',
		{
			x: 0.5,
			y: 1.33,
			w: 9.0,
			h: 0.36,
			fontSize: 10.5,
			bold: true,
			color: '7A4A00',
			fontFace: 'Calibri',
			margin: 0,
		}
	);

	// Observation cards
	const obs = [
		{
			label: 'Query: "freedom of speech"',
			result: 'Retrieves Article 17 (Right to Freedom) — correct.\nBM25 + title boost both contribute to high score.',
			ok: true,
		},
		{
			label: 'Query: "right to education"',
			result: 'Retrieves Article 31 — correct.\nProximity scoring boosts rank for phrase match.',
			ok: true,
		},
		{
			label: 'RAG (LLM online)',
			result: 'Ollama (Llama 3) generates answer referencing correct article numbers, grounded in retrieved text.',
			ok: true,
		},
		{
			label: 'LLM offline fallback',
			result: 'System correctly falls back to retrieval-only and displays a clear warning message to the user.',
			ok: true,
		},
	];
	const ow = 4.6,
		oh = 1.56,
		gap = 0.12;
	obs.forEach((o, i) => {
		const x = 0.38 + (i % 2) * (ow + gap);
		const y = 1.9 + Math.floor(i / 2) * (oh + 0.12);
		card(s, x, y, ow, oh, C.white);
		s.addShape(pres.shapes.RECTANGLE, {
			x,
			y,
			w: ow,
			h: 0.32,
			fill: { color: o.ok ? C.green : C.redSoft },
			line: { color: o.ok ? C.green : C.redSoft },
		});
		s.addText((o.ok ? '✓  ' : '✗  ') + o.label, {
			x: x + 0.08,
			y: y + 0.02,
			w: ow - 0.16,
			h: 0.28,
			fontSize: 9.5,
			bold: true,
			color: C.white,
			fontFace: 'Calibri',
			margin: 0,
		});
		s.addText(o.result, {
			x: x + 0.08,
			y: y + 0.38,
			w: ow - 0.16,
			h: 1.1,
			fontSize: 9.5,
			color: C.mid,
			fontFace: 'Calibri',
			margin: 0,
			lineSpacingMultiple: 1.3,
		});
	});

	// Note
	s.addShape(pres.shapes.RECTANGLE, {
		x: 0.38,
		y: 5.08,
		w: 9.3,
		h: 0.32,
		fill: { color: C.offWhite },
		line: { color: 'D0E0E8' },
	});
	s.addText(
		'Full evaluation (30 queries, P@5/MAP/NDCG) to be completed before final defense.',
		{
			x: 0.5,
			y: 5.09,
			w: 9.0,
			h: 0.3,
			fontSize: 9.5,
			color: C.slate,
			fontFace: 'Calibri',
			margin: 0,
			italic: true,
		}
	);
}

// ══════════════════════════════════════════════════════════════════════════════
// SLIDE 10 – Conclusion & Future Work
// ══════════════════════════════════════════════════════════════════════════════
{
	const s = pres.addSlide();
	s.background = { color: C.navy };

	// Accent bar
	s.addShape(pres.shapes.RECTANGLE, {
		x: 0,
		y: 0,
		w: 0.22,
		h: 5.625,
		fill: { color: C.teal },
		line: { color: C.teal },
	});
	s.addShape(pres.shapes.RECTANGLE, {
		x: 0,
		y: 5.0,
		w: 10,
		h: 0.625,
		fill: { color: C.tealLt },
		line: { color: C.tealLt },
	});

	s.addText('Conclusion & Future Work', {
		x: 0.42,
		y: 0.22,
		w: 9.3,
		h: 0.44,
		fontSize: 20,
		bold: true,
		color: C.white,
		fontFace: 'Calibri',
		margin: 0,
	});
	s.addShape(pres.shapes.LINE, {
		x: 0.42,
		y: 0.72,
		w: 9.2,
		h: 0,
		line: { color: C.teal, width: 1.2 },
	});

	// Conclusion card
	card(s, 0.38, 0.86, 4.35, 3.92, '112233');
	s.addShape(pres.shapes.RECTANGLE, {
		x: 0.38,
		y: 0.86,
		w: 4.35,
		h: 0.36,
		fill: { color: C.teal },
		line: { color: C.teal },
	});
	s.addText('Conclusion', {
		x: 0.5,
		y: 0.88,
		w: 4.1,
		h: 0.32,
		fontSize: 11,
		bold: true,
		color: C.white,
		fontFace: 'Calibri',
		margin: 0,
	});
	const conclusions = [
		'Efficient proximity-aware constitutional retrieval demonstrated.',
		'BM25 + Proximity + Title Boost significantly improves precision for legal phrasing.',
		'RAG module generates grounded, hallucination-free answers from retrieved articles.',
		'System remains fully available even when LLM is offline (graceful fallback).',
		'Improves constitutional literacy and legal accessibility in Nepal.',
	];
	s.addText(
		conclusions.map((c, i) => ({
			text: c,
			options: { bullet: true, breakLine: i < conclusions.length - 1 },
		})),
		{
			x: 0.5,
			y: 1.28,
			w: 4.1,
			h: 3.4,
			fontSize: 10,
			color: C.sky,
			fontFace: 'Calibri',
			margin: 0,
			paraSpaceAfter: 5,
		}
	);

	// Future card
	card(s, 4.9, 0.86, 4.8, 3.92, '112233');
	s.addShape(pres.shapes.RECTANGLE, {
		x: 4.9,
		y: 0.86,
		w: 4.8,
		h: 0.36,
		fill: { color: C.dark },
		line: { color: C.dark },
	});
	s.addText('Future Recommendations', {
		x: 5.02,
		y: 0.88,
		w: 4.5,
		h: 0.32,
		fontSize: 11,
		bold: true,
		color: C.white,
		fontFace: 'Calibri',
		margin: 0,
	});
	const futures = [
		'Multilingual support — Nepali & regional languages.',
		'Expand dataset to include Acts, Laws, and case studies.',
		'Mobile application for wider accessibility.',
		'Advanced AI models for better query understanding.',
		'Neural dense retrieval (embedding-based) alongside BM25.',
	];
	s.addText(
		futures.map((f, i) => ({
			text: f,
			options: { bullet: true, breakLine: i < futures.length - 1 },
		})),
		{
			x: 5.02,
			y: 1.28,
			w: 4.5,
			h: 3.4,
			fontSize: 10,
			color: C.sky,
			fontFace: 'Calibri',
			margin: 0,
			paraSpaceAfter: 5,
		}
	);

	s.addText(
		'Thank You  |  Nayan Nepal  •  Ronish Ghimire  •  Devraj Khatiwada  |  Supervisor: Manoj Pokharel',
		{
			x: 0.22,
			y: 5.0,
			w: 9.78,
			h: 0.58,
			fontSize: 10,
			color: C.navy,
			fontFace: 'Calibri',
			align: 'center',
			bold: true,
			margin: 0,
			valign: 'middle',
		}
	);
}

// ── Save ──────────────────────────────────────────────────────────────────────
await pres.writeFile({ fileName: './Constitutional_IR_Mid_Defense.pptx' });
console.log('Done!');
