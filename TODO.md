# Healthcare Chatbot - Remaining Tasks Checklist

## ✅ Completed
- [x] Backend API structure (FastAPI)
- [x] Vector RAG pipeline (ChromaDB)
- [x] Graph database integration (Neo4j with fallback)
- [x] Safety/red-flag detection
- [x] Routing logic (Graph vs Vector)
- [x] Frontend UI (Next.js + Tailwind)
- [x] Speech-to-text integration (Whisper)
- [x] Basic profile management
- [x] Requirements.txt and dependency setup

## 📋 Phase 1: Data Ingestion (Priority: HIGH)

### 1.1 Markdown Files Organization
- [x] Create directory structure in `api/rag/data/`:
  - `triage/`
  - `general/`
  - `respiratory/`
  - `gi/`
  - `gu/`
  - `skin/`
  - `msk/`
  - `neuro/`
  - `cardio/`
  - `endocrine/`
  - `ent/`
  - `eye/`
  - `oral/`
  - `women/`
  - `men/`
  - `pregnancy/`
  - `mental/`
  - `peds/`
  - `firstaid/`
  - `prevention/`
  - `tests/`
  - `screening/`

-### 1.2 Content Collection
- [x] Collect all ~110 markdown files following the catalog
- [x] Ensure each file has YAML frontmatter with:
  - `id`, `title`, `last_reviewed`, `reviewer`
  - `sources` (array with name, url, license, accessed date)
  - `disclaimer`
- [x] Verify all sources are authoritative and properly licensed
- [x] Place files in appropriate subdirectories

### 1.3 Build Index
- [x] Run `python api/rag/build_index.py` after adding files
- [x] Verify all files are processed (check output for file count)
- [x] Test retrieval with sample queries
- [x] Verify metadata (title, category, source) is preserved

## 📋 Phase 2: Graph Database Expansion (Priority: HIGH)

### 2.1 Expand seed.csv
- [x] Add mental health red flags:
  - Suicidal thoughts → Mental health crisis
  - Self-harm → Mental health crisis
  - Severe depression → Mental health crisis
  - Panic attacks → Anxiety disorder
- [x] Add pediatric-specific symptoms:
  - High fever in child < 3 months → Sepsis risk
  - No tears when crying → Severe dehydration
  - Bulging fontanelle → Meningitis
- [x] Add women's health red flags:
  - Heavy vaginal bleeding → Miscarriage/Ectopic
  - Severe abdominal pain in pregnancy → Ectopic/Pre-eclampsia
- [x] Add more contraindications:
  - Pregnancy → NSAIDs, Alcohol, Smoking
  - Kidney disease → Ibuprofen, Contrast dye
  - Liver disease → Alcohol, Paracetamol (high dose)
- [x] Add safe actions for various conditions
- [x] Expand provider data (more cities, more providers)

### 2.2 Neo4j Setup
- [x] Set up Neo4j (Docker or Aura Free tier)
- [x] Run `python api/graph/ingest.py` to load seed.csv
- [x] Verify all triples are loaded (check node/relationship counts)
- [x] Test Cypher queries manually
- [x] Update `.env` with Neo4j credentials

## 📋 Phase 3: Backend Enhancements (Priority: MEDIUM)

### 3.1 Safety & Routing Improvements
- [x] Expand red-flag keywords (Hindi + English)
- [x] Add mental health crisis detection
- [x] Improve symptom extraction (use NLP if needed)
- [x] Add pregnancy-specific red flags
- [x] Improve graph routing heuristics (better pattern matching)

### 3.2 Personalization
- [x] Enhance profile handling (age, sex, pregnancy status)
- [x] Add age-based recommendations (children vs adults)
- [x] Add pregnancy-aware responses
- [x] Improve contraindication filtering based on profile

### 3.3 Response Quality
- [x] Improve LLM prompts (better structure, clearer guidelines)
- [x] Add Hindi language support in responses (not just UI)
- [x] Extend translation pipeline to Tamil, Kannada, Malayalam, and Telugu
- [x] Add automatic language detection & translation pipeline (Whisper → English → target language)
- [x] Add source citations in responses (link to original sources)
- [x] Improve fact integration (better formatting of graph facts)

### 3.4 Error Handling & Logging
- [x] Add proper error handling for all endpoints
- [x] Add logging (use Python's logging module)
- [x] Add rate limiting (optional, for demo)
- [x] Add request validation
- [x] Handle OpenAI API errors gracefully
- [x] Handle Neo4j connection failures gracefully

### 3.5 Voice Loop & Latency
- [x] Implement end-to-end voice pipeline (audio upload → STT → RAG → translation → TTS)
- [x] Optimize latency (instrument safety/routing timings, prep for streaming)
- [x] Integrate TTS provider (ElevenLabs with gTTS fallback)
- [x] Add graceful fallbacks when TTS/STT services are unavailable
- [x] Expand Whisper STT config to support English, Hindi, Tamil, Kannada, Malayalam, Telugu
- [x] Configure multi-language TTS voices (English, Hindi, Tamil, Kannada, Malayalam, Telugu)

### 3.6 Romanized Multilingual Text Pipeline
- [x] Detect and normalize romanized Tamil/Hindi/Telugu/Kannada/Malayalam inputs typed with English keyboards
- [x] Transliterate to native script and translate to English before RAG/graph processing
- [x] Reinforce DeepSeek prompts to strictly use supplied RAG/Neo4j context (no hallucinations)
- [x] Return localized responses in user-preferred script or romanized form
- [x] Add tests covering romanized queries across supported languages


## 📋 Phase 4: Frontend Improvements (Priority: MEDIUM)

### 4.1 UI/UX Enhancements
- [x] Improve styling (modern, professional look)
- [x] Add loading states (skeleton loaders)
- [x] Add error states (user-friendly error messages)
- [x] Improve mobile responsiveness
- [x] Add animations/transitions
- [x] Improve chat bubble styling
 - [x] Add markdown rendering for responses (formatting, links)

### 4.2 Features
- [ ] Add topic categories/sidebar (browse by category)
- [ ] Add search functionality
- [ ] Add "suggested questions" feature
- [ ] Improve citation display (clickable links to sources)
- [ ] Add "share" functionality
- [ ] Add chat history (localStorage or backend)
- [ ] Add export chat history

### 4.3 Profile & Settings
- [ ] Expand profile modal (age, sex, pregnancy, children)
- [ ] Add profile validation
- [ ] Add profile import/export
- [ ] Add settings (preferences, language, theme)

### 4.4 Accessibility
- [ ] Add ARIA labels
- [ ] Improve keyboard navigation
- [ ] Add screen reader support
- [ ] Improve color contrast
- [ ] Add focus indicators

## 📋 Phase 5: Testing & Validation (Priority: HIGH)

### 5.1 Backend Testing
- [ ] Test all endpoints (`/health`, `/stt`, `/chat`)
- [ ] Test red-flag detection (various scenarios)
- [ ] Test graph routing vs vector routing
- [ ] Test personalization (diabetes, hypertension, pregnancy)
- [ ] Test error handling
- [ ] Test with Hindi queries
- [ ] Test with voice input (STT)

### 5.2 Frontend Testing
- [ ] Test all UI components
- [ ] Test chat functionality
- [ ] Test profile management
- [ ] Test language toggle
- [ ] Test voice recording
- [ ] Test on different browsers
- [ ] Test on mobile devices

### 5.3 Integration Testing
- [ ] End-to-end test (voice → STT → chat → response)
- [ ] Test red-flag escalation flow
- [ ] Test graph queries with real Neo4j
- [ ] Test RAG retrieval with full dataset
- [ ] Test personalization end-to-end

## 📋 Phase 6: Documentation (Priority: MEDIUM)

### 6.1 README
- [ ] Add project overview
- [ ] Add setup instructions (backend + frontend)
- [ ] Add environment variables documentation
- [ ] Add API documentation
- [ ] Add data ingestion instructions
- [ ] Add Neo4j setup instructions
- [ ] Add deployment instructions

### 6.2 Code Documentation
- [ ] Add docstrings to all functions
- [ ] Add type hints where missing
- [ ] Add inline comments for complex logic
- [ ] Document API endpoints
- [ ] Document data models

### 6.3 User Documentation
- [ ] Add user guide (how to use the bot)
- [ ] Add FAQ
- [ ] Add disclaimer/terms of use
- [ ] Add privacy policy

## 📋 Phase 7: Deployment Preparation (Priority: LOW)

### 7.1 Backend Deployment
- [ ] Set up production environment variables
- [ ] Set up database (Neo4j Aura or self-hosted)
- [ ] Set up vector database (ChromaDB persistence)
- [ ] Add health checks
- [ ] Add monitoring (optional)
- [ ] Set up CI/CD (optional)

### 7.2 Frontend Deployment
- [ ] Build production bundle
- [ ] Set up environment variables
- [ ] Configure API endpoints
- [ ] Add error tracking (optional)
- [ ] Add analytics (optional)

### 7.3 Security
- [ ] Review security best practices
- [ ] Add input sanitization
- [ ] Add CORS configuration
- [ ] Add rate limiting
- [ ] Review API key security
- [ ] Add HTTPS (for production)

## 📋 Phase 8: Demo Preparation (Priority: HIGH)

### 8.1 Demo Script
- [ ] Prepare demo scenarios:
  - Normal query (fever, cough)
  - Red-flag query (chest pain, shortness of breath)
  - Personalization (diabetes + diarrhea)
  - Graph query (list contraindications)
  - Mental health query (depression, suicide)
  - Pediatric query (fever in child)
  - Pregnancy query (red flags)
  - Hindi query
  - Voice input

### 8.2 Presentation
- [ ] Prepare slides (architecture, features, safety)
- [ ] Prepare video demo
- [ ] Prepare screenshots
- [ ] Prepare architecture diagram
- [ ] Prepare data flow diagram

### 8.3 Testing for Demo
- [ ] Test all demo scenarios
- [ ] Verify all features work
- [ ] Verify all safety features work
- [ ] Verify citations are displayed
- [ ] Verify personalization works
- [ ] Verify Hindi support works

## 🎯 Quick Win Priorities (Do These First)

1. **Collect and organize all markdown files** → Place in `api/rag/data/` subdirectories
2. **Run build_index.py** → Verify all files are indexed
3. **Expand seed.csv** → Add mental health, pediatric, pregnancy red flags
4. **Set up Neo4j** → Run ingestion script
5. **Test end-to-end** → Verify everything works with new data
6. **Implement low-latency voice roundtrip** → STT → RAG → Translation → TTS
7. **Improve frontend styling** → Make it look professional
8. **Add Hindi response support** → Backend should respond in Hindi when requested
9. **Prepare demo scenarios** → Test all key features
10. **Mute Chroma telemetry warnings** → Set `CHROMADB_DISABLE_TELEMETRY=1`

## 📝 Notes

- **Data Sources**: Ensure all markdown files have proper citations and licenses
- **Safety First**: Always prioritize safety features (red-flag detection, disclaimers)
- **User Experience**: Focus on making the UI intuitive and responsive
- **Documentation**: Keep documentation updated as you add features
- **Testing**: Test thoroughly before demo (especially safety features)

## 🔗 Resources

- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Neo4j Documentation](https://neo4j.com/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [OpenAI API Documentation](https://platform.openai.com/docs/)

