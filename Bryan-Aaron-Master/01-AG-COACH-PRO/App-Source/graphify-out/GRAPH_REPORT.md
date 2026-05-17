# Graph Report - .  (2026-04-25)

## Corpus Check
- Large corpus: 734 files · ~3,622,309 words. Semantic extraction will be expensive (many Claude tokens). Consider running on a subfolder, or use --no-semantic to run AST-only.

## Summary
- 2155 nodes · 3744 edges · 72 communities detected
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 404 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Core UI & Navigation|Core UI & Navigation]]
- [[_COMMUNITY_AI Grading & LDE Analysis|AI Grading & LDE Analysis]]
- [[_COMMUNITY_Admin Teacher Screens|Admin Teacher Screens]]
- [[_COMMUNITY_Quiz & Flashcard Generation|Quiz & Flashcard Generation]]
- [[_COMMUNITY_Platform Architecture & Docs|Platform Architecture & Docs]]
- [[_COMMUNITY_Media & PDF Utilities|Media & PDF Utilities]]
- [[_COMMUNITY_Contest Routing & Screens|Contest Routing & Screens]]
- [[_COMMUNITY_Shared Utilities & Formatters|Shared Utilities & Formatters]]
- [[_COMMUNITY_CRM & Super Admin|CRM & Super Admin]]
- [[_COMMUNITY_Chapter Goals & PPTX Tools|Chapter Goals & PPTX Tools]]
- [[_COMMUNITY_Practice Contest Screens|Practice Contest Screens]]
- [[_COMMUNITY_Multi-Agent AI System|Multi-Agent AI System]]
- [[_COMMUNITY_RAG Quiz Engine|RAG Quiz Engine]]
- [[_COMMUNITY_CDE Materials Management|CDE Materials Management]]
- [[_COMMUNITY_Quiz Engine & Livestock Upload|Quiz Engine & Livestock Upload]]
- [[_COMMUNITY_Farm Business Management|Farm Business Management]]
- [[_COMMUNITY_Forestry Contest Generator|Forestry Contest Generator]]
- [[_COMMUNITY_Creed Speaking & LDE Eval|Creed Speaking & LDE Eval]]
- [[_COMMUNITY_Exam Engine|Exam Engine]]
- [[_COMMUNITY_Livestock Judging & Scoring|Livestock Judging & Scoring]]
- [[_COMMUNITY_Vet Science Flashcards|Vet Science Flashcards]]
- [[_COMMUNITY_FBM Problem Solving|FBM Problem Solving]]
- [[_COMMUNITY_Support System|Support System]]
- [[_COMMUNITY_Study Mode Screens|Study Mode Screens]]
- [[_COMMUNITY_AI Stress Testing|AI Stress Testing]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 79|Community 79]]
- [[_COMMUNITY_Community 80|Community 80]]
- [[_COMMUNITY_Community 81|Community 81]]
- [[_COMMUNITY_Community 116|Community 116]]
- [[_COMMUNITY_Community 117|Community 117]]
- [[_COMMUNITY_Community 240|Community 240]]
- [[_COMMUNITY_Community 241|Community 241]]
- [[_COMMUNITY_Community 242|Community 242]]

## God Nodes (most connected - your core abstractions)
1. `React Native` - 414 edges
2. `Expo Router 4` - 372 edges
3. `Supabase` - 59 edges
4. `generateRAGBatch()` - 56 edges
5. `handleStart()` - 51 edges
6. `loadQuiz()` - 49 edges
7. `Minipass` - 42 edges
8. `setLoading()` - 35 edges
9. `flipCard()` - 30 edges
10. `nextQuestion()` - 29 edges

## Surprising Connections (you probably didn't know these)
- `AgCoachPro Farm Business Management Implementation Roadmap` --conceptually_related_to--> `Skill: scaffold-cde-module`  [INFERRED]
  Texas_FFA_Resources/CDE_Events/Farm_Business_Management/AgCoachPro_FarmBusinessManagement_ContentPack.md → CLAUDE.md
- `Expo Router 4` --rationale_for--> `Rationale: single codebase for iOS/Android/Web`  [EXTRACTED]
  CLAUDE.md → PROJECT_SUMMARY.md
- `Food Science Module (stub, 851-line monolith)` --conceptually_related_to--> `Practice Module Structure (4-screen pattern)`  [INFERRED]
  BUSINESS_BRAIN.md → CLAUDE.md
- `Ag Advocacy Module (stub)` --conceptually_related_to--> `Practice Module Structure (4-screen pattern)`  [INFERRED]
  BUSINESS_BRAIN.md → CLAUDE.md
- `LDE: Creed Speaking` --conceptually_related_to--> `SOP: Creed Speaking Simulation`  [INFERRED]
  Texas_FFA_Resources/AgCoachPro_Complete_Resource_Audit.md → architecture/creed-speaking-sop.md

## Communities

### Community 0 - "Core UI & Navigation"
Cohesion: 0.01
Nodes (53): goToAdmin(), goToLogin(), goToSignup(), GlassCard(), handleSend(), handleStart(), handleStartQuiz(), startPractice() (+45 more)

### Community 1 - "AI Grading & LDE Analysis"
Cohesion: 0.03
Nodes (99): analyzeAgAdvocacy(), generateAgAdvocacyQuestions(), analyzeAgIssuesPresentation(), generateAgIssuesQuestions(), analyzeSalesPitch(), analyzeAgSkillsVideo(), calculateTimePenalty(), computeAgSkillsScores() (+91 more)

### Community 2 - "Admin Teacher Screens"
Cohesion: 0.02
Nodes (70): loadAudio(), Backend & Data Agent Skill, daysUntil(), getReadinessForEvent(), loadAll(), nextMonth(), prevMonth(), readinessLabel() (+62 more)

### Community 3 - "Quiz & Flashcard Generation"
Cohesion: 0.03
Nodes (96): generateAgCommFlashcards(), generateAgCommQuiz(), generateContestExam(), generateCustomQuiz(), generateAgEngFlashcards(), generateAgEngQuiz(), generateContestExam(), generateCustomQuiz() (+88 more)

### Community 4 - "Platform Architecture & Docs"
Cohesion: 0.03
Nodes (81): Ag Advocacy Module (stub), Ag Skills / LDE Video Scorer (1000-pt rubric), AgCoachPro Platform, AI Engine Agent Skill, Annual Invoice Billing Model, Anthropic Claude API (secondary AI), biz_subscriptions Table, B.L.A.S.T. Protocol (+73 more)

### Community 5 - "Media & PDF Utilities"
Cohesion: 0.04
Nodes (29): download_image(), fetch_photo_url(), main(), generateInvoicePDF(), auditTopic(), checkResources(), runAudit(), extract_deck_content() (+21 more)

### Community 6 - "Contest Routing & Screens"
Cohesion: 0.04
Nodes (53): fmt(), reset(), Contest Routing ID Handshake, finishContest(), isDemoMode(), daysUntil(), getTrainingSchedule(), saveResults() (+45 more)

### Community 7 - "Shared Utilities & Formatters"
Cohesion: 0.04
Nodes (37): ffaYear(), handleLogResult(), loadAll(), loadGrades(), handleApprove(), handleSaveDraft(), provisionTeacher(), guardDemo() (+29 more)

### Community 8 - "CRM & Super Admin"
Cohesion: 0.07
Nodes (29): addCRMNote(), addFollowup(), fetchChapterDetail(), fetchChapters(), fetchChaptersFull(), fetchStruggleHeatmap(), fetchStruggleHeatmapLegacy(), syncChapterFromStripe() (+21 more)

### Community 9 - "Chapter Goals & PPTX Tools"
Cohesion: 0.07
Nodes (33): extractPptxFile(), extractPptxText(), getSlideImageRefs(), getSlideTitle(), listMediaFiles(), listSlides(), loadItems(), main() (+25 more)

### Community 10 - "Practice Contest Screens"
Cohesion: 0.07
Nodes (22): confirmSubmit(), defaultPartI(), formatTime(), getImageForQuestion(), getRating(), getSectionInfo(), handleAnswer(), handleRetry() (+14 more)

### Community 11 - "Multi-Agent AI System"
Cohesion: 0.06
Nodes (43): Agent: AI Engine, Agent: Backend & Data, Agent: Contest Builder, Agent: Orchestrator, Agent: QA & Performance, Agent: UI/UX, Antigravity Agent Skills README, CDE: Farm Business Management (+35 more)

### Community 12 - "RAG Quiz Engine"
Cohesion: 0.2
Nodes (11): generateAgAdvocacyQuiz(), beginExamB(), chapterColor(), finishQuiz(), handleAnswer(), isCorrectAnswer(), loadQuiz(), nextQuestion() (+3 more)

### Community 13 - "CDE Materials Management"
Cohesion: 0.07
Nodes (14): closeCdeModal(), openCde(), resetForms(), saveImage(), saveProblem(), savePrompt(), toggleActive(), buildTraits() (+6 more)

### Community 14 - "Quiz Engine & Livestock Upload"
Cohesion: 0.07
Nodes (15): handleNext(), handleOptionSelect(), handleSubmit(), loadQuiz(), goBack(), handleNextAnimal(), buildEvaluationPrompt(), generateEvaluationDraft() (+7 more)

### Community 15 - "Farm Business Management"
Cohesion: 0.08
Nodes (35): Balance Sheet (Farm Financial Condition), Farm Budgets & Planning Types, Cash Flow Statement, AgCoachPro Farm Business Management Content Pack, Farm Business Management CDE Overview, Farm Business Management Economic Principles, Enterprise Budget, Farm Financial Statement Ratios (+27 more)

### Community 16 - "Forestry Contest Generator"
Cohesion: 0.15
Nodes (24): generateContest(), generateForestryConceptBatch(), generateQ1(), generateQ10(), generateQ11(), generateQ12(), generateQ13(), generateQ2() (+16 more)

### Community 17 - "Creed Speaking & LDE Eval"
Cohesion: 0.11
Nodes (21): analyzePresentation(), evaluateAnswer(), evaluateCreedQA(), extractJson(), backtrackLCS(), calculateAccuracy(), calculateCreedAccuracy(), computeLCSMatrix() (+13 more)

### Community 18 - "Exam Engine"
Cohesion: 0.11
Nodes (9): flipCard(), shuffle(), startContest(), startFlashcard(), startMode(), startStudy(), getPoultryQuestionsByCategory(), getQuestionsByCategory() (+1 more)

### Community 19 - "Livestock Judging & Scoring"
Cohesion: 0.12
Nodes (12): calculateGradeScore(), calculateHormelScore(), scoreFeederAnimal(), scoreFeederFrame(), scoreFeederMuscle(), scoreSlaughterAnimal(), scoreSlaughterQuality(), scoreSlaughterYield() (+4 more)

### Community 20 - "Vet Science Flashcards"
Cohesion: 0.13
Nodes (11): buildFlashCards(), buildStudyQuestions(), shuffle(), getItemImageIndex(), buildQuestion(), generateCDEContest(), generateIDQuiz(), getDistractors() (+3 more)

### Community 21 - "FBM Problem Solving"
Cohesion: 0.16
Nodes (16): generateFBMFlashcards(), generateFBMRagScenario(), generateProblemSolvingQuiz(), generateWrittenQuiz(), inferTolerance(), inferUnits(), parseNumericAnswer(), shuffle() (+8 more)

### Community 22 - "Support System"
Cohesion: 0.15
Nodes (11): formatDate(), getMessages(), getMyTickets(), handleSend(), handleSendReply(), handleSubmit(), loadingTickets(), loadMessages() (+3 more)

### Community 23 - "Study Mode Screens"
Cohesion: 0.22
Nodes (7): handleAnswer(), handleNext(), handlePrev(), handleStart(), loadQuestions(), startWith(), toggleMastered()

### Community 24 - "AI Stress Testing"
Cohesion: 0.33
Nodes (12): bar(), colorize(), logResult(), main(), printReport(), testConcurrentUsers(), testJsonParsing(), testQualityDifferentiation() (+4 more)

### Community 25 - "Community 25"
Cohesion: 0.18
Nodes (5): buildOptions(), nextStudy(), shuffle(), getRandomSpecimens(), getSpecimensByRegion()

### Community 26 - "Community 26"
Cohesion: 0.16
Nodes (6): blank(), handleContestSelect(), handleSave(), loadAssessments(), updateCurrent(), updateOption()

### Community 27 - "Community 27"
Cohesion: 0.19
Nodes (14): Builder Agent J-drona23-v5 (50 tool call budget), Builder Agent K-drona23-v6 (30 tool call budget), Write Complete Solution in One Pass, Patterns Reference J-drona23-v5, Patterns Reference K-drona23-v6, Profile J-drona23-v5, Profile K-drona23-v6, Profile M-drona23-v8 (+6 more)

### Community 28 - "Community 28"
Cohesion: 0.21
Nodes (6): generateEvaluationFleeces(), generatePlacingClasses(), formatTime(), handleBack(), handleNext(), startSession()

### Community 29 - "Community 29"
Cohesion: 0.2
Nodes (2): calculateScore(), finishExam()

### Community 30 - "Community 30"
Cohesion: 0.22
Nodes (5): apply(), clear(), equals(), setOperator(), mainMenu()

### Community 31 - "Community 31"
Cohesion: 0.18
Nodes (3): handleSubmit(), handleSubmit(), calculatePlacingScore()

### Community 32 - "Community 32"
Cohesion: 0.31
Nodes (7): analyzeAgCommPracticum(), analyzeAgCommWriting(), formatTime(), getRoleConfig(), return(), startPracticum(), submitContent()

### Community 33 - "Community 33"
Cohesion: 0.31
Nodes (7): getScenario(), handleScenarioAnswer(), loadScenario(), nextScenarioQuestion(), patchScenario(), saveCompleted(), toggleComplete()

### Community 34 - "Community 34"
Cohesion: 0.24
Nodes (4): renderNonVerbalStep(), renderOralStep(), updateNonVerbal(), updateOral()

### Community 35 - "Community 35"
Cohesion: 0.22
Nodes (9): Advisor Intelligence Agent Skill, AuthGate (app/_layout.tsx), Gamification System (XP, levels, streaks), PerformanceGap TypeScript Interface, Student Role, Superadmin Role, Teacher / Ag Advisor Role, Student Dashboard (app/(tabs)/, 6 tabs) (+1 more)

### Community 36 - "Community 36"
Cohesion: 0.46
Nodes (6): handleSubmit(), loadStats(), nextScenario(), saveStats(), toggle(), toggleFactor()

### Community 37 - "Community 37"
Cohesion: 0.5
Nodes (6): advanceQuestion(), advanceStation(), currentStationId(), finishContest(), getStationQuestions(), resetQuestionState()

### Community 38 - "Community 38"
Cohesion: 0.29
Nodes (2): handleAddStudent(), loadData()

### Community 39 - "Community 39"
Cohesion: 0.36
Nodes (4): backtrackWithSwitchDetection(), calculateCreedAccuracy(), computeLCSMatrix(), normalizeText()

### Community 40 - "Community 40"
Cohesion: 0.52
Nodes (5): generateContestExam(), generateCustomQuiz(), generateLivestockJudgingFlashcards(), generateLivestockJudgingQuiz(), shuffle()

### Community 41 - "Community 41"
Cohesion: 0.6
Nodes (4): getStepStatus(), handleStepPress(), isStepUnlocked(), loadProgress()

### Community 42 - "Community 42"
Cohesion: 0.4
Nodes (2): shuffle(), startSession()

### Community 44 - "Community 44"
Cohesion: 0.33
Nodes (2): generateChapterConductingQuiz(), resetQuiz()

### Community 45 - "Community 45"
Cohesion: 0.47
Nodes (5): convert_pptx_to_pdf(), main(), Use LibreOffice headless to convert .pptx → .pdf, Use pdftoppm to render each PDF page as a PNG., render_pdf_to_pngs()

### Community 46 - "Community 46"
Cohesion: 0.33
Nodes (6): claude-token-efficient Config System, CLAUDE.md Analysis Profile, CLAUDE.md Coding Profile, Rationale: CLAUDE.md token efficiency (input cost offset by output savings), Token Efficiency Benchmark (~63% output reduction), Core Token-Efficient Rules

### Community 47 - "Community 47"
Cohesion: 0.33
Nodes (6): AI Brain Notebook (NotebookLM), NotebookLM CLI (notebooklm-py), Pinecone Index: agcoachpro, Skill: NotebookLM Automation, Skill: pinecone-memory, Skill: Session Wrap-Up

### Community 48 - "Community 48"
Cohesion: 0.7
Nodes (4): backtrackLCS(), calculateSpanishAccuracy(), computeLCSMatrix(), normalizeText()

### Community 49 - "Community 49"
Cohesion: 0.5
Nodes (2): calculateResults(), handleNext()

### Community 51 - "Community 51"
Cohesion: 0.4
Nodes (2): calculateGrainGrade(), handleCalculate()

### Community 52 - "Community 52"
Cohesion: 0.4
Nodes (2): generateProblem(), FormulaEngine()

### Community 53 - "Community 53"
Cohesion: 0.4
Nodes (2): getDeck(), SlideDeckViewer()

### Community 55 - "Community 55"
Cohesion: 0.4
Nodes (5): livestock_contest_sessions Table, Livestock Judging Contest Module, lib/livestock-scoring.ts (scoring engine), Rationale: migrations-only schema changes prevent overwrite on deploy, supabase/migrations/ directory

### Community 56 - "Community 56"
Cohesion: 0.83
Nodes (2): clean_text(), validate_transcription()

### Community 57 - "Community 57"
Cohesion: 0.5
Nodes (2): calculate_creed_score(), Calculates the final Creed Speaking score according to official FFA rubrics.

### Community 58 - "Community 58"
Cohesion: 0.67
Nodes (2): emptyRatings(), startStation()

### Community 60 - "Community 60"
Cohesion: 0.67
Nodes (2): getFoodScienceRulePack(), pickSimulationScenario()

### Community 61 - "Community 61"
Cohesion: 0.5
Nodes (3): AnimatedButton component, Dark Glass Aesthetic (UI theme), Rationale: dark glass aesthetic for premium feel

### Community 62 - "Community 62"
Cohesion: 0.67
Nodes (4): Hallucination Prevention Rule, Parallel Subagent Cap (3 max), Agents Profile (CLAUDE.agents.md), Structured Output Only Rule

### Community 63 - "Community 63"
Cohesion: 0.67
Nodes (1): testGen()

### Community 64 - "Community 64"
Cohesion: 0.67
Nodes (1): verifyHistoryStore()

### Community 65 - "Community 65"
Cohesion: 0.67
Nodes (1): Root()

### Community 68 - "Community 68"
Cohesion: 1.0
Nodes (2): parseCSVLine(), processLineByLine()

### Community 70 - "Community 70"
Cohesion: 1.0
Nodes (2): getAppUrl(), getCallbackUrl()

### Community 79 - "Community 79"
Cohesion: 1.0
Nodes (3): CLAUDE.md File Approach, Rules-in-Prompt Approach, Token Efficiency Rationale (CLAUDE.md vs prompt rules)

### Community 80 - "Community 80"
Cohesion: 0.67
Nodes (3): livestock-judging/basics.tsx Slide Bullets, Skill: Sync Slide Deck Bullets, Slide Decks (lib/data/slide-decks/)

### Community 81 - "Community 81"
Cohesion: 0.67
Nodes (3): FFmpeg (Frame Extraction Tool), Scroll-Driven Video Website Pattern, Skill: 3D Animation Creator (Scroll-Driven Video)

### Community 116 - "Community 116"
Cohesion: 1.0
Nodes (2): lib/prompts/ directory, Rationale: prompts in lib/prompts/ for separation of concerns

### Community 117 - "Community 117"
Cohesion: 1.0
Nodes (2): pdftoppm (PDF to PNG Converter), Skill: Slides to PNG Converter

### Community 240 - "Community 240"
Cohesion: 1.0
Nodes (1): Contest Builder Agent Skill

### Community 241 - "Community 241"
Cohesion: 1.0
Nodes (1): UI/UX Agent Skill

### Community 242 - "Community 242"
Cohesion: 1.0
Nodes (1): Benchmark Profile (CLAUDE.benchmark.md)

## Knowledge Gaps
- **106 isolated node(s):** `Upload PDF to Gemini Files API and OCR all pages in one call.`, `Convert text to embedding via Pinecone Inference API.`, `Upsert vectors to Pinecone.`, `Split text into overlapping chunks.`, `Ingest a single file into Pinecone.` (+101 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 29`** (11 nodes): `simulator.tsx`, `calculateScore()`, `confirmSubmit()`, `finishExam()`, `formatTime()`, `handleAnswer()`, `jumpTo()`, `next()`, `prev()`, `startMode()`, `toggleFlag()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 38`** (8 nodes): `students.tsx`, `copyToClipboard()`, `handleAddStudent()`, `handleDeactivate()`, `handleModalUpdate()`, `handleShareLink()`, `handleViewProfile()`, `loadData()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 42`** (6 nodes): `plant-preference.tsx`, `nextPlant()`, `scorePlant()`, `setAnswer()`, `shuffle()`, `startSession()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 44`** (6 nodes): `quiz.tsx`, `generateChapterConductingQuiz()`, `chapter-conducting-questions.ts`, `handleGrade()`, `handleReveal()`, `resetQuiz()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 49`** (5 nodes): `contest.tsx`, `calculateResults()`, `handleNext()`, `handleSelectCategory()`, `handleSelectName()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 51`** (5 nodes): `grain-grading.tsx`, `calculateGrainGrade()`, `handleCalculate()`, `reset()`, `grain-grading.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 52`** (5 nodes): `generateProblem()`, `generateRandomVariable()`, `FormulaEngine.tsx`, `FormulaEngine()`, `ag-tech-formulas.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 53`** (5 nodes): `slidedeck-viewer.tsx`, `getAllDecks()`, `getDeck()`, `index.ts`, `SlideDeckViewer()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 56`** (4 nodes): `whisper_transcription_validator.py`, `whisper_transcription_validator.py`, `clean_text()`, `validate_transcription()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 57`** (4 nodes): `calculate_creed_score()`, `Calculates the final Creed Speaking score according to official FFA rubrics.`, `rubric_calculator.py`, `rubric_calculator.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 58`** (4 nodes): `habitat-eval.tsx`, `emptyRatings()`, `setRating()`, `startStation()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 60`** (4 nodes): `getFoodScienceRulePack()`, `listFoodScienceRulePackYears()`, `pickSimulationScenario()`, `food-science.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 63`** (3 nodes): `testGen()`, `test-chapter-prompt.ts`, `test-chapter-prompt.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 64`** (3 nodes): `verify_store.ts`, `verifyHistoryStore()`, `verify_store.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 65`** (3 nodes): `+html.tsx`, `Root()`, `+html.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 68`** (3 nodes): `parseCSVLine()`, `processLineByLine()`, `parse-entomology.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 70`** (3 nodes): `redirect.ts`, `getAppUrl()`, `getCallbackUrl()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 116`** (2 nodes): `lib/prompts/ directory`, `Rationale: prompts in lib/prompts/ for separation of concerns`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 117`** (2 nodes): `pdftoppm (PDF to PNG Converter)`, `Skill: Slides to PNG Converter`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 240`** (1 nodes): `Contest Builder Agent Skill`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 241`** (1 nodes): `UI/UX Agent Skill`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 242`** (1 nodes): `Benchmark Profile (CLAUDE.benchmark.md)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `React Native` connect `Core UI & Navigation` to `AI Grading & LDE Analysis`, `Admin Teacher Screens`, `Platform Architecture & Docs`, `Media & PDF Utilities`, `Contest Routing & Screens`, `Shared Utilities & Formatters`, `CRM & Super Admin`, `Chapter Goals & PPTX Tools`, `Practice Contest Screens`, `RAG Quiz Engine`, `CDE Materials Management`, `Quiz Engine & Livestock Upload`, `Forestry Contest Generator`, `Creed Speaking & LDE Eval`, `Exam Engine`, `Livestock Judging & Scoring`, `Vet Science Flashcards`, `FBM Problem Solving`, `Support System`, `Study Mode Screens`, `Community 25`, `Community 26`, `Community 28`, `Community 29`, `Community 30`, `Community 31`, `Community 32`, `Community 33`, `Community 34`, `Community 36`, `Community 37`, `Community 38`, `Community 41`, `Community 42`, `Community 44`, `Community 49`, `Community 50`, `Community 51`, `Community 52`, `Community 53`, `Community 58`, `Community 67`, `Community 70`?**
  _High betweenness centrality (0.384) - this node is a cross-community bridge._
- **Why does `Expo Router 4` connect `Core UI & Navigation` to `AI Grading & LDE Analysis`, `Admin Teacher Screens`, `Platform Architecture & Docs`, `Contest Routing & Screens`, `Shared Utilities & Formatters`, `CRM & Super Admin`, `Chapter Goals & PPTX Tools`, `Practice Contest Screens`, `RAG Quiz Engine`, `CDE Materials Management`, `Quiz Engine & Livestock Upload`, `Forestry Contest Generator`, `Creed Speaking & LDE Eval`, `Exam Engine`, `Livestock Judging & Scoring`, `Vet Science Flashcards`, `FBM Problem Solving`, `Support System`, `Study Mode Screens`, `Community 25`, `Community 28`, `Community 29`, `Community 31`, `Community 32`, `Community 33`, `Community 34`, `Community 36`, `Community 37`, `Community 38`, `Community 41`, `Community 42`, `Community 44`, `Community 49`, `Community 51`, `Community 53`, `Community 58`?**
  _High betweenness centrality (0.195) - this node is a cross-community bridge._
- **Why does `Supabase` connect `Admin Teacher Screens` to `Core UI & Navigation`, `AI Grading & LDE Analysis`, `Platform Architecture & Docs`, `Contest Routing & Screens`, `Shared Utilities & Formatters`, `Chapter Goals & PPTX Tools`, `CDE Materials Management`, `Quiz Engine & Livestock Upload`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Are the 54 inferred relationships involving `generateRAGBatch()` (e.g. with `loadScenario()` and `generateCustomQuiz()`) actually correct?**
  _`generateRAGBatch()` has 54 INFERRED edges - model-reasoned connections that need verification._
- **Are the 22 inferred relationships involving `handleStart()` (e.g. with `setLoading()` and `generateEnvFlashcards()`) actually correct?**
  _`handleStart()` has 22 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Upload PDF to Gemini Files API and OCR all pages in one call.`, `Convert text to embedding via Pinecone Inference API.`, `Upsert vectors to Pinecone.` to the rest of the system?**
  _106 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Core UI & Navigation` be split into smaller, more focused modules?**
  _Cohesion score 0.01 - nodes in this community are weakly interconnected._