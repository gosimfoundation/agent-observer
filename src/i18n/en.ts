export default {
  nav: {
    vision: 'Event Brief',
    about: 'Why',
    mission: 'Mission',
    participate: 'Participate',
    leaderboard: 'Leaderboard',
    applyNow: 'Registration coming soon',
  },
  vision: {
    pageTitle: 'Agentic Cosmos',
    pageSubtitle: 'Event Brief · Building agents for the night sky',
    intro:
      'This is a vision document for participants, partners, and the curious. It weaves the 01–07 material into one coherent statement: why we need observing agents, what human job they are taking over, how the challenge is designed, what you build, how scoring works, the little astronomy you need, and the overall schedule.',
    backToHome: 'Back to home',
    sections: [
      {
        kicker: '01 / Why',
        title: 'The observing plan shapes the science sample',
        paragraphs: [
          'A survey telescope maps large areas of sky systematically. It does not spend a whole night on a single object; it visits thousands of tiles across many nights, building up statistically powerful samples of galaxies, quasars, and stars.',
          'Cosmology runs on samples like these: large, uniform, well calibrated. Wide surveys reveal the large-scale structure of the universe, constrain its expansion history, underpin dark energy measurements, and tie galaxy evolution to cosmic time. Spectroscopic surveys add a third dimension — redshift. Position on the sky plus redshift gives you a three-dimensional map of cosmic structure. DESI is one concrete, public example: spectra for large samples of galaxies and quasars, used to map the expanding universe and study dark energy.',
          'But survey operations are hard. Weather changes what a 900-second exposure is worth through seeing, transparency, and sky brightness. Target visibility shifts with airmass and position on the sky. Observing programs prefer different conditions: DARK, BRIGHT, and BACKUP. The footprint has to be covered broadly and evenly for the science to hold up. High-priority tiles, nearly finished tiles, and under-covered regions all compete for the same block of time. One bad tactical choice spends real observing time and changes every plan that follows.',
          'Modern AI systems open a path: an assistant that reads state, calls computational tools, reasons under physical constraints, proposes a plan, monitors quality, and explains every choice. The long-term goal is an observing agent that can genuinely take part in real survey operations. This hackathon narrows that long-term vision into one focused benchmark.',
        ],
        highlight:
          'You build the observer’s logic. We provide the mission definition, tile table, observing constraints, weather scenarios, simulator, and evaluation protocol.',
      },
      {
        kicker: '02 / The Observer',
        title: 'What a human lead observer actually does',
        paragraphs: [
          'A seasoned lead observer makes a full set of decisions every 900-second slot: understand the science goal and decide tonight’s tactical priority; read seeing, transparency, sky brightness, and the short-term forecast; judge whether tonight suits DARK, BRIGHT, or BACKUP observing; keep the tiles that are visible now, legal, and worth the time; trade off science yield, priority, airmass, footprint balance, and wasted time; finish a tile when completing it beats over-exposure; react to sudden downtime and fluctuating efficiency; use fast validation signals to calibrate later decisions; and explain why this action was chosen in this slot.',
          'These duties are what the observing agent is taking over. We do not expect an agent to outperform a human immediately. We expect it to be evaluated objectively against a fixed interface, fixed data, and fixed scoring — so it can become a viable component of real survey operations.',
        ],
        duties: [
          { n: '01', title: 'Night strategy', desc: 'Understand the science goal and decide tonight’s tactical priority.' },
          { n: '02', title: 'Reading the weather', desc: 'Seeing, transparency, sky brightness, and the short-term forecast.' },
          { n: '03', title: 'Program selection', desc: 'Judge whether tonight suits DARK, BRIGHT, or BACKUP observing.' },
          { n: '04', title: 'Candidate filtering', desc: 'Keep the tiles that are visible now, legal, and worth the time.' },
          { n: '05', title: 'Tile ranking', desc: 'Trade off science yield, priority, airmass, footprint balance, and wasted time.' },
          { n: '06', title: 'Completion management', desc: 'Finish a tile when the value of completing it beats the cost of over-exposure.' },
          { n: '07', title: 'Replanning', desc: 'React to sudden downtime and fluctuating observing efficiency.' },
          { n: '08', title: 'Quality monitoring', desc: 'Use fast validation signals to calibrate later decisions.' },
          { n: '09', title: 'Logging the reason', desc: 'Explain why the observer chose this action in this slot.' },
        ],
      },
      {
        kicker: '03 / Format',
        title: 'The Survey Mission Card and the challenge loop',
        paragraphs: [
          'Every challenge instance starts from a Survey Mission Card. It states the science goal, footprint area, time budget, telescope site, available observing programs, target classes, observing constraints, and scoring rules. It also provides public dev data — tile catalogue, example weather scenarios, initial state, and visual reports — plus final evaluation data, an organizer-supplied weather replay.',
          'You submit a Python file containing class MyAgent. The simulator calls MyAgent.act(state) repeatedly, and the method returns either observe(tile_id) or wait. In this competition the only variable is the agent’s strategy. Simulator, weather replay, and scoring function are all fixed.',
        ],
        loopTitle: 'The challenge loop',
        loop: [
          { stage: 'Fixed inputs', items: ['Science goal', 'Tile table', 'Weather'] },
          { stage: 'Agent state', items: ['Forecast', 'Progress', 'Candidates'] },
          { stage: 'Reasoning', items: ['Rank', 'Explain', 'Decide'] },
          { stage: 'Action', items: ['Observe', 'or wait'] },
          { stage: 'Metrics', items: ['Score', 'Uniformity', 'Violations'] },
        ],
      },
      {
        kicker: '04 / What to Build',
        title: 'From a first agent to a competitive design',
        paragraphs: [
          'Your deliverable is one agent file plus a short note explaining the observer’s architecture. Start from one plain utility rule: among the legal tiles, take the one with the highest expected weighted gain. That already is a working observer.',
          'Then add weather, completion, airmass, footprint balance, and a waste term. A competitive agent usually combines immediate science yield with forecast awareness, a completion bonus, footprint balancing, an airmass penalty, and one concise reason string.',
          'Architectures worth trying include utility agents, weather-aware planners, completion managers, footprint balancers, risk-controlled agents, lead/support pairs, and LLM planner plus rule checker. A modular observing agent can be decomposed into weather interpretation, program selection, candidate filtering, tile ranking, footprint balancing, completion management, support/risk checking, and reason logging.',
        ],
        starterCode: `tiles = state["available_tiles"]
if len(tiles) == 0:
    return {"action": "wait"}

best = max(tiles, key=lambda t: t["expected_weighted_gain"])
return {"action": "observe", "tile_id": best["tile_id"]}`,
        archCode: `AgentObserver
  -> WeatherInterpreter
  -> ProgramSelector
  -> CandidateFilter
  -> TileRanker
  -> FootprintBalancer
  -> CompletionManager
  -> SupportObserver / RiskChecker
  -> ReasonLogger`,
      },
      {
        kicker: '05 / Scoring',
        title: 'Scientific, reproducible, inspectable evaluation',
        paragraphs: [
          'The score rewards weighted effective targets and penalizes uneven footprint coverage, wasted time, rule violations, and unfinished high-priority tiles. A good agent trades immediate yield against completion, uniformity, weather risk, and operational discipline.',
          'Evaluation follows open-science principles: fixed seeds, fixed data, fixed scoring; participants see a compact state dictionary and a readable history file; metrics focus on target yield, tile completion, weather response, footprint balance, and waste; development and evaluation weather are separated to support robust comparison.',
          'Visualization turns completed tile fractions into an observed-target map — a 3D spatial sample and a 2D butterfly plot of sky position plus simulated redshift, in the style DESI uses — so different strategies produce visibly different maps.',
        ],
        formula: `score = science_score
  - uniformity_penalty
  - wasted_time_penalty
  - violation_penalty
  - incomplete_priority_penalty`,
      },
      {
        kicker: '06 / Glossary',
        title: 'A little astronomy is enough',
        paragraphs: [
          'You do not need an astronomy background to read the state dictionary and reason about it. A Tile is a small patch of sky the telescope can observe in one pointing. The Footprint is the whole sky area the survey intends to cover. Targets, in this planning benchmark, are the object counts inside each tile.',
          'Seeing describes how blurred the image is — lower is better. Transparency describes how clear the atmosphere is — higher is better. Sky brightness is background noise; for faint targets, darker is usually better. Airmass measures how much atmosphere the light passes through — lower is better. donefrac is tile completion: 0 means just started, 1 means finished.',
          'The state dictionary contains weather (current seeing, transparency, sky brightness, program, observability, and speed), forecast (this slot plus the next four), progress (tiles completed, mean completion, footprint balance, wasted time, and violations), and available_tiles (the legal options right now, with expected gain, expected waste, target counts, priority, and airmass).',
        ],
        actionCode: `return {
    "action": "observe",
    "tile_id": 100123,
    "reason": "highest useful gain",
}`,
      },
      {
        kicker: '07 / Timeline',
        title: 'Three stages from training to awards',
        paragraphs: [
          'The event has three stages: online training, competition, and awards day. Online training runs September 15–30 and is open worldwide to individuals and teams. The goal is to learn CosmosBench, the shared simulator, mission cards, and the observing-agent interface, and to prepare using public weather scenarios.',
          'The hybrid finals run October 1–17 online and at GOSIM Shenzhen under one evaluation protocol. Evaluation, submissions, and live standings are powered by CosmosBench and are open to all registered teams. Final results are announced and prizes presented on October 17.',
        ],
        rounds: [
          { number: '01', name: 'Online Training', dates: 'Sep 15–30', format: 'Online', challenge: 'Learn CosmosBench, the shared simulator, mission cards, and the observing-agent interface, then prepare with public weather scenarios.', participants: 'Open worldwide to individuals and teams.' },
          { number: '02', name: 'Finals', dates: 'Oct 1–17', format: 'Online + GOSIM Shenzhen', challenge: 'Complete the survey task under one evaluation protocol, with online and conference participation. Evaluation, submissions, and live standings are powered by CosmosBench.', participants: 'All registered teams.' },
          { number: '03', name: 'Awards Day', dates: 'Oct 17', format: 'GOSIM Shenzhen', challenge: 'Final results are announced and prizes are presented.', participants: 'Winning teams and invited participants.' },
        ],
      },
    ],
  },
  hero: {
    eyebrow: 'GOSIM Hackathon · Astronomy × Agents',
    system: 'Agentic Cosmos',
    subtitle: '智能体巡天黑客松',
    lede:
      'Build an observing agent for the telescopes to come: read the state of the night sky, reason the way a seasoned observer does, and decide the next observation every 900 seconds.',
    pipeline: [
      { label: 'Online Training', date: 'Sep 15–30' },
      { label: 'Hybrid Finals', date: 'Oct 1–17' },
      { label: 'Awards Day', date: 'Oct 17' },
    ],
    location: ['Online training Sep 15–30 · Hybrid finals Oct 1–17', 'October 17 · Awards Day at GOSIM Shenzhen'],
    cta: 'Mission card coming soon',
  },
  home: {
    vision: {
      kicker: '01 / Vision',
      title: 'Hand the night sky to an agent',
      lede: 'The night sky is too vast and too precious to leave to chance.',
      paragraphs: [
        'Every night a survey telescope faces thousands of observable tiles. Weather changes, target visibility changes, and science priorities change. Every decision a human observer makes shapes the quality of the final cosmic sample.',
        'We are building an open benchmark: an agent reads the state of the night sky, reasons like a seasoned observer, and decides the next observation every 900 seconds. Same mission card, same weather replay, same scoring function — the only variable is your strategy.',
      ],
      link: 'Read the full event brief',
      stats: [
        { value: '900s', label: 'per decision slot' },
        { value: '1', label: 'unified mission card' },
        { value: '∞', label: 'possible strategies' },
      ],
    },
    mission: {
      kicker: '02 / Mission',
      title: 'Design a digital observer',
      lede: 'Your agent takes over the core decisions of a human lead observer.',
      cards: [
        { title: 'Read the night sky', desc: 'Weather, forecast, tile progress, and legal candidates are packed into one compact state dictionary.' },
        { title: 'Decide every 900 seconds', desc: 'At the end of each slot, choose a tile to observe or wait for a better moment.' },
        { title: 'One transparent score', desc: 'Science yield, footprint uniformity, time efficiency, and rule compliance are all fixed and public.' },
      ],
      closing: 'No astronomy background required. Just an agent that reads state, weighs trade-offs, and makes decisions.',
    },
    participate: {
      kicker: '03 / How to participate',
      title: 'Three steps to compete',
      lede: 'From training to awards, the path is clear.',
      steps: [
        { n: '01', title: 'Register & team up', desc: 'Sign up online and create or join a team. Solo developers are welcome too.' },
        { n: '02', title: 'Build your agent', desc: 'Train, test, and iterate on your observing strategy with CosmosBench public data.' },
        { n: '03', title: 'Submit for evaluation', desc: 'During the competition, submit your agent. CosmosBench runs everyone on the same benchmark and updates the live leaderboard.' },
      ],
      timeline: [
        { label: 'Sep 15–30', desc: 'Online training' },
        { label: 'Oct 1–17', desc: 'Online + Shenzhen finals' },
        { label: 'Oct 17', desc: 'Awards at GOSIM Shenzhen' },
      ],
      cta: 'Registration coming soon',
    },
    prizes: {
      kicker: '04 / Awards',
      title: '$5,700 in prizes',
      lede: 'Four award categories recognize the strongest observing agents and the best live presentation at GOSIM Shenzhen.',
      tiers: [
        { place: 'First Prize', amount: '$2,000', count: '1 winner' },
        { place: 'Second Prize', amount: '$1,000', count: '2 winners' },
        { place: 'Third Prize', amount: '$500', count: '3 winners' },
        { place: 'Best Live Presentation', amount: '$200', count: '1 winner' },
      ],
      note: 'The Best Live Presentation award is reserved for teams presenting at the conference venue. The number of teams and participants invited onsite is still to be confirmed.',
    },
    leaderboard: {
      kicker: '05 / Leaderboard',
      title: 'Live standings',
      lede: 'Once the competition starts, the leaderboard updates in real time via CosmosBench.',
    },
  },
  about: {
    kicker: '01 / Why',
    title: 'The observing plan is what shapes the final science sample',
    p1: 'A survey telescope maps large areas of sky systematically. It does not spend a whole night on a single object; it visits thousands of tiles across many nights, building up statistically powerful samples of galaxies, quasars, and stars.',
    p2: 'Cosmology runs on samples like these: large, uniform, well calibrated. Wide surveys reveal the large-scale structure of the universe, constrain its expansion history, underpin dark energy measurements, and tie galaxy evolution to cosmic time. Spectroscopic surveys add a third dimension — redshift. Position on the sky plus redshift gives you a three-dimensional map of cosmic structure.',
    p3: 'DESI is one concrete, public example of exactly this: spectra for large samples of galaxies and quasars, used to map the expanding universe and study dark energy.',
    hardTitle: 'Why survey operations are hard',
    hardItems: [
      { term: 'Weather', desc: 'Changes what a 900-second exposure is worth, through seeing, transparency, and sky brightness.' },
      { term: 'Target visibility', desc: 'Shifts through the night with airmass and position on the sky.' },
      { term: 'Observing programs', desc: 'Each prefers different conditions: DARK, BRIGHT, and BACKUP.' },
      { term: 'The footprint', desc: 'Has to be covered broadly and evenly for the science analysis to hold up.' },
    ],
    hardClosing:
      'High-priority tiles, nearly finished tiles, and under-covered regions all compete for the same block of time. One bad tactical choice spends real observing time and changes every plan that follows. Night operations demand decisions that are both effective and explainable.',
    whyNowTitle: 'Why an observing agent, and why now',
    whyNow:
      'The long-term goal is an observing agent that can genuinely take part in real survey operations. A human lead observer translates science goals, weather, instrument state, tile completion, and candidate fields into a tactical decision, right now. Modern AI systems open a path: an assistant that reads state, calls computational tools, reasons under physical constraints, proposes a plan, monitors quality, and explains every choice.',
    whyNowClosing: 'This hackathon narrows that long-term vision into one focused benchmark.',
    split: [
      { side: 'You build', desc: 'The observer’s logic — the system that decides.' },
      { side: 'We provide', desc: 'The mission definition, tile table, observing constraints, weather scenarios, simulator, and evaluation protocol.' },
    ],
  },
  observer: {
    kicker: '02 / The Observer',
    title: 'What a human lead observer actually does',
    intro: 'These nine jobs are what the observing agent is taking over.',
    duties: [
      { n: '01', title: 'Night strategy', desc: 'Understand the science goal and decide tonight’s tactical priority.' },
      { n: '02', title: 'Reading the weather', desc: 'Seeing, transparency, sky brightness, and the short-term forecast.' },
      { n: '03', title: 'Program selection', desc: 'Judge whether tonight suits DARK, BRIGHT, or BACKUP observing.' },
      { n: '04', title: 'Candidate filtering', desc: 'Keep the tiles that are visible now, legal, and worth the time.' },
      { n: '05', title: 'Tile ranking', desc: 'Trade off science yield, priority, airmass, footprint balance, and wasted time.' },
      { n: '06', title: 'Completion management', desc: 'Finish a tile when the value of completing it beats the cost of over-exposure.' },
      { n: '07', title: 'Replanning', desc: 'React to sudden downtime and fluctuating observing efficiency.' },
      { n: '08', title: 'Quality monitoring', desc: 'Use fast validation signals to calibrate later decisions.' },
      { n: '09', title: 'Logging the reason', desc: 'Explain why the observer chose this action in this slot.' },
    ],
  },
  challenge: {
    kicker: '03 / Format',
    title: 'The Survey Mission Card',
    intro:
      'Every challenge instance starts from a Survey Mission Card. It states the science goal, footprint area, time budget, telescope site, available observing programs, target classes, observing constraints, and scoring rules.',
    cards: [
      { title: 'Mission definition', desc: 'Which sky to cover, which targets matter, how much time you have.' },
      { title: 'Telescope / site', desc: 'Latitude, visibility limits, slot length, airmass constraints.' },
      { title: 'Public dev data', desc: 'Tile catalogue, example weather scenarios, initial state, and visual reports.' },
      { title: 'Final eval data', desc: 'Organizer-supplied weather replay, run in the same simulator.' },
      { title: 'Your deliverable', desc: 'An observing agent that reads state and returns an observing action.' },
      { title: 'One evaluation', desc: 'Every submitted agent runs on the same mission card, the same weather, the same scoring function.' },
    ],
    loopTitle: 'The challenge loop',
    loop: [
      { stage: 'Fixed inputs', items: ['Science goal', 'Tile table', 'Weather'] },
      { stage: 'Agent state', items: ['Forecast', 'Progress', 'Candidates'] },
      { stage: 'Reasoning', items: ['Rank', 'Explain', 'Decide'] },
      { stage: 'Action', items: ['Observe', 'or wait'] },
      { stage: 'Metrics', items: ['Score', 'Uniformity', 'Violations'] },
    ],
    loopNote: 'In this competition the only variable is the agent’s strategy. Simulator, weather replay, and scoring function are all fixed.',
  },
  build: {
    kicker: '04 / What to Build',
    title: 'What participants do',
    intro:
      'Submit a Python file containing class MyAgent. The simulator calls MyAgent.act(state) repeatedly, and that method returns either observe(tile_id) or wait.',
    io: [
      { term: 'Input', desc: 'A small state dictionary: weather, forecast, survey progress, and the legal candidate tiles.' },
      { term: 'Output', desc: 'One action — for this 900-second slot, either observe a tile_id or wait.' },
      { term: 'Scoring', desc: 'Effective targets, tiles completed, evenness of footprint coverage, time efficiency, and action legality.' },
      { term: 'Deliverable', desc: 'One agent file plus a short note explaining the observer’s architecture.' },
    ],
    starterTitle: 'Your first working agent',
    starterIntro:
      'Start from one plain utility rule: among the legal tiles, take the one with the highest expected weighted gain. That already is a working observer.',
    starterCode: `tiles = state["available_tiles"]
if len(tiles) == 0:
    return {"action": "wait"}

best = max(tiles, key=lambda t: t["expected_weighted_gain"])
return {"action": "observe", "tile_id": best["tile_id"]}`,
    starterClosing:
      'Then add weather, completion, airmass, footprint balance, and a waste term. A competitive agent usually combines immediate science yield with forecast awareness, a completion bonus, footprint balancing, an airmass penalty, and one concise reason string.',
    archTitle: 'Architectures worth trying',
    architectures: [
      { name: 'Utility agent', desc: 'Score every candidate tile, take the highest.' },
      { name: 'Weather-aware planner', desc: 'Use the forecast to decide whether to spend or save a high-value tile.' },
      { name: 'Completion manager', desc: 'Spot tiles near donefrac = 1 and manage over-exposure waste.' },
      { name: 'Footprint balancer', desc: 'Up-weight regions that are behind on coverage.' },
      { name: 'Risk-controlled agent', desc: 'Filter out high-waste, high-airmass, or low-value options before ranking.' },
      { name: 'Lead / support pair', desc: 'One module proposes the plan, another checks constraints and explains the risk.' },
      { name: 'LLM planner + rule checker', desc: 'Language reasoning for strategy, deterministic code for legality.' },
    ],
    archCode: `AgentObserver
  -> WeatherInterpreter
  -> ProgramSelector
  -> CandidateFilter
  -> TileRanker
  -> FootprintBalancer
  -> CompletionManager
  -> SupportObserver / RiskChecker
  -> ReasonLogger`,
    scenariosTitle: 'Situations you will meet',
    scenariosIntro: 'A strong agent handles a handful of recurring situations.',
    scenarios: [
      { when: 'Excellent dark night', then: 'Spend the slot on high expected gain, high priority, faint-target programs.' },
      { when: 'Marginal but usable weather', then: 'Prefer robust tiles, completion opportunities, and low-waste options.' },
      { when: 'Forecast improving', then: 'Compare current speed against future speed before spending a high-value tile.' },
      { when: 'Footprint unbalanced', then: 'Give under-covered regions a bonus.' },
      { when: 'Tile near completion', then: 'Finish it when the completion bonus beats the waste cost.' },
      { when: 'High airmass', then: 'Discount the utility of tiles that are harder to observe well.' },
    ],
  },
  scoring: {
    kicker: '05 / Scoring',
    title: 'How the score works',
    intro:
      'The score rewards weighted effective targets and penalizes uneven footprint coverage, wasted time, rule violations, and unfinished high-priority tiles. A good agent trades immediate yield against completion, uniformity, weather risk, and operational discipline.',
    formula: `score = science_score
      - uniformity_penalty
      - wasted_time_penalty
      - violation_penalty
      - incomplete_priority_penalty`,
    principlesTitle: 'Open-science design principles',
    principles: [
      { term: 'Reproducible benchmark', desc: 'Fixed seeds, fixed data, fixed scoring.' },
      { term: 'Inspectable interface', desc: 'Participants see a compact state dictionary and a readable history file.' },
      { term: 'Scientific but light evaluation', desc: 'Target yield, tile completion, weather response, footprint balance, and waste.' },
      { term: 'Clearly bounded scoring', desc: 'Observation-planning metrics inside a fast simulator.' },
      { term: 'Dev and eval weather separated', desc: 'Development weather and final evaluation weather can differ, which supports a robust comparison.' },
    ],
    principlesClosing:
      'Future mission cards can add real survey log replay, z > 5 quasar planning, and LBG planning while keeping the same observing-agent interface.',
    vizTitle: 'Seeing the result',
    viz: [
      'The test data includes a deterministic table of simulated target coordinates. Each tile’s target count is bound to fixed simulated coordinates through the random seed, the tile_id, and the target class.',
      'After a run, the simulator converts completed tile fractions into an observed-target map — how many simulated galaxies and quasars the agent actually reached.',
      'A 3D view keeps the observed simulated universe as a spatial sample; a 2D butterfly plot folds sky position and simulated redshift together, in the style DESI uses.',
      'Different observing strategies produce visibly different maps of cosmic structure. The visualization helps a team explain its strategy, its footprint balance, and what it missed.',
    ],
    vizNote: 'The map is the benchmark’s visualization layer. The scored loop is still the planning task itself.',
  },
  glossary: {
    kicker: '06 / Glossary',
    title: 'A little astronomy is enough',
    intro: 'You do not need an astronomy background to read the state dictionary and reason about it. This much will do.',
    terms: [
      { term: 'Tile', desc: 'A small patch of sky the telescope can observe in one pointing.' },
      { term: 'Footprint', desc: 'The whole sky area the survey intends to cover.' },
      { term: 'Targets', desc: 'In this planning benchmark, the object counts inside each tile.' },
      { term: 'Seeing', desc: 'How blurred the image is. Lower is better.' },
      { term: 'Transparency', desc: 'How clear the atmosphere is. Higher is better.' },
      { term: 'Sky brightness', desc: 'Background noise. For faint targets, darker is usually better.' },
      { term: 'Airmass', desc: 'How much atmosphere the light passes through. Lower is better.' },
      { term: 'donefrac', desc: 'Tile completion: 0 means just started, 1 means finished.' },
    ],
    stateTitle: 'What is in the state',
    state: [
      { field: 'weather', desc: 'Current seeing, transparency, sky brightness, program, observability, and speed.' },
      { field: 'forecast', desc: 'This slot plus the next four, which is what makes replanning possible.' },
      { field: 'progress', desc: 'Tiles completed, mean completion, footprint balance, wasted time, and violations.' },
      { field: 'available_tiles', desc: 'The legal options right now, with expected gain, expected waste, target counts, priority, and airmass.' },
    ],
    actionCode: `return {
    "action": "observe",
    "tile_id": 100123,
    "reason": "highest useful gain",
}`,
  },
  schedule: {
    kicker: '07 / Timeline', title: 'Schedule',
    intro: 'Online training leads into the CosmosBench-powered competition, followed by Awards Day on October 17.',
    challengeLabel: 'Survey task', participantsLabel: 'Who participates',
    rounds: [
      { number: '01', name: 'Online Training', dates: 'Sep 15–30', format: 'Online', challenge: 'Learn CosmosBench, the shared simulator, mission cards, and the observing-agent interface, then prepare with public weather scenarios.', participants: 'Open worldwide to individuals and teams.' },
      { number: '02', name: 'Finals', dates: 'Oct 1–17', format: 'Online + GOSIM Shenzhen', challenge: 'Complete the survey task under one evaluation protocol, with online and conference participation. Evaluation, submissions, and live standings are powered by CosmosBench.', participants: 'All registered teams.' },
      { number: '03', name: 'Awards Day', dates: 'Oct 17', format: 'GOSIM Shenzhen', challenge: 'Final results are announced and prizes are presented.', participants: 'Winning teams and invited participants.' },
    ],
  },
  leaderboard: {
    kicker: '08 / CosmosBench', title: 'Live Leaderboard · Top 20',
    intro: 'One mission card, weather replay, simulator, and scoring function. Evaluation and live standings are powered by CosmosBench.',
    refresh: 'Refresh', full: 'Full board', updated: 'Updated', loading: 'Loading CosmosBench…', empty: 'The leaderboard goes live when the competition opens on October 1.', unavailable: 'The CosmosBench leaderboard is temporarily unavailable. Please try again shortly.',
    team: 'Team / Agent', score: 'Score', science: 'Science', completion: 'Completion', uniformity: 'Uniformity', submissions: 'Submissions',
  },
  cta: {
    title: 'Hand the next move of the night sky to the agent you wrote',
    tagline: 'Same mission card, same weather, same scoring function. The only variable is strategy.',
    location: 'Online development and CosmosBench evaluation · October 17 at GOSIM Shenzhen',
  },
  footer: {
    copyright: '2026 GOSIM · Agentic Cosmos',
    mainSite: 'GOSIM',
    register: 'Mission card coming soon',
  },
  construction: {
    title: 'Site Under Construction',
    desc: 'This site is still being built. Dates, the mission card, and how to register are not final — treat nothing here as settled until announced.',
    ok: 'Got it',
  },
}
