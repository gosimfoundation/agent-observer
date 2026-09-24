/** Explicit current-stage copy; the competition messages stay preserved. */
export function practiceMessages(base: Record<string, any>, chinese: boolean) {
  const result=structuredClone(base)
  const pick=(en:unknown,zh:unknown)=>chinese?zh:en
  const patches:Record<string,unknown>={
    'hero.pipeline':[{label:pick('Playground','练习赛 / Playground'),date:pick('Open now','正在进行'),note:pick('Run, submit, review your score','运行、提交、查看成绩')}],
    'hero.location.0':pick('Online Playground · join from anywhere','线上练习赛 · 随时参与'),
    'home.participate.steps.2.desc':pick('Upload your generated decisions.csv through Submit, then view your score and replay.','在「提交」页上传生成的 decisions.csv，随后查看成绩与回放。'),
    'home.participate.timeline':[{label:'Playground',desc:pick('The current competition','当前练习赛')}],
    'home.prizes.lede':pick('Award details are published in the rules and announcements.','奖项安排见规则与公告。'),
    'home.leaderboard.lede':pick('Scores appear after evaluation. Each scenario has its own Playground standings.','评测完成后显示成绩，每个场景分别排名。'),
    'home.submission.items.0.desc':pick('Upload decisions.csv from your local run. Your team keeps its best score for each scenario.','上传本地运行生成的 decisions.csv，每队保留各场景的最高分。'),
    'home.submission.items.1.desc':pick('Any algorithm is welcome. Model calls are optional. CSV files may be up to 20 MB; each team can submit 50 times a day.','算法不限，不强制调用模型。CSV 最大 20 MB，每队每天可提交 50 次。'),
    'home.quest.levels.3.title':pick('Submit and view your score','提交并查看成绩'),
    'home.quest.levels.3.desc':pick('Upload decisions.csv, then inspect the score breakdown and decision replay.','上传 decisions.csv，查看得分构成和逐步决策回放。'),
    'home.quest.levels.3.desc_gated':pick('Upload decisions.csv and view your results.','上传 decisions.csv 并查看结果。'),
    'home.quest.levels.3.time':pick('Open now','正在开放'),
    'home.quest.levels.3.to':'/compete',
    'vision.intro':pick('Learn the observation task, planning decisions, scoring and submission process.','了解观测任务、规划决策、评分方式与提交流程。'),
    'rules_page.phases_title':pick('Current competition','当前比赛'),
    'dash.phases':pick('Current competition','当前比赛'),
    'vision.sections.2.paragraphs.0':pick('The mission card defines the science goal, tiles, observing constraints, weather, requests and scoring. Download the published scenarios on Resources.','任务卡定义科学目标、天区、观测约束、天气、请求和评分。可在资源页下载公开场景。'),
    'vision.sections.4.paragraphs.1':pick('Run the public scenario locally. The platform scores your submitted decisions using the same published scorer.','在本地运行公开场景，平台使用同一份公开评分器评估你提交的决策。'),
    'vision.sections.5.paragraphs.1':pick('The published data and scoring rules let you reproduce your results and inspect each observation.','公开数据和评分规则让你可以复现成绩并检查每次观测。'),
    'vision.sections.8.title':pick('Take part online','在线参与'),
    'vision.sections.4.paragraphs.0':pick('Use any algorithm to produce decisions.csv. Submit that file for evaluation.','使用任意算法生成 decisions.csv，再提交文件进行评测。'),
    'vision.sections.4.paragraphs.2':pick('Download the starter kit, run public scenarios, study the replay, and improve your decisions.','下载入门包，运行公开场景，查看回放并改进决策。'),
    'vision.sections.8.paragraphs':[pick('The Playground is available online. Registration, teams, submissions and scores are managed on this website.','练习赛在线进行，报名、组队、提交与查分都在本站完成。'),pick('The platform selects the current competition for you. Use Submit whenever you are ready.','平台会自动选择当前比赛，准备好后直接进入「提交」。')],
    'vision.sections.8.rounds':[],
    'schedule.intro':pick('The Playground is open online. Updates appear in announcements.','练习赛在线开放，相关安排通过公告发布。'),
    'schedule.rounds':[],
    'submit.errors.agents_not_allowed':pick('Upload a decisions.csv result file here.','请在这里上传 decisions.csv 结果文件。'),
    'errors.agents_not_allowed':pick('Upload a decisions.csv result file here.','请在这里上传 decisions.csv 结果文件。'),
    'submit.results_public_only':pick('Scenario weather is public, so scores can be reproduced locally.','场景天气公开，可以在本地复现评分。'),
    'resources.scenarios_note':pick('Download the public configuration and data files for the current competition below.','在下方下载当前比赛的公开配置与数据文件。'),
    'resources.flow3_hint':pick('Public scenario files are listed below.','下方列出各场景的公开文件。'),
    'faq.items.3.a':pick('Any implementation language is allowed. Use the starter kit locally and submit decisions.csv.','实现语言不限，在本地运行后提交 decisions.csv。'),
    'faq.items.6.q':pick('What scenario data can I download?','可以下载哪些场景数据？'),
    'faq.items.6.a':pick('Current scenario weather, forecasts and events are public. Use score_decisions.py to reproduce the score.','当前场景的天气、预报和事件公开，可使用 score_decisions.py 复现成绩。'),
    'faq.items.7.a':pick('Each team can submit 50 times a day. Each scenario ranks the team’s best score independently.','每队每天可以提交 50 次，每个场景分别取该队最高分排名。'),
    'faq.items.8.a':pick('Playground standings are for practice and do not determine awards.','练习赛榜单用于练习，不决定奖项。'),
  }
  for (const [path,value] of Object.entries(patches)) {
    const parts=path.split('.');let parent=result
    for(let i=0;i<parts.length-1;i++) { const key=parts[i]!; parent=parent[key]??=(/^\d+$/.test(parts[i+1]??'')?[]:{}) }
    parent[parts.at(-1)!]=value
  }
  return result
}
