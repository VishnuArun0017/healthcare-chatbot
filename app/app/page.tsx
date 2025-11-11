'use client';

import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Mic, Send, Settings, AlertTriangle, Phone, X } from 'lucide-react';

type LangCode = 'en' | 'hi' | 'ta' | 'te' | 'kn' | 'ml';
type SexOption = 'male' | 'female' | 'other';

const API_BASE = 'http://localhost:8000';

const LANGUAGE_OPTIONS: Array<{
  value: LangCode;
  label: string;
  speechLang: string;
  placeholder: string;
  introTitle: string;
  introSubtitle: string;
}> = [
  {
    value: 'en',
    label: 'English',
    speechLang: 'en-US',
    placeholder: 'Type your health question...',
    introTitle: 'How can I help you today?',
    introSubtitle: 'Ask about symptoms, self-care, or when to see a doctor',
  },
  {
    value: 'hi',
    label: 'हिन्दी',
    speechLang: 'hi-IN',
    placeholder: 'अपना स्वास्थ्य प्रश्न टाइप करें...',
    introTitle: 'आज मैं आपकी कैसे मदद कर सकता हूं?',
    introSubtitle: 'लक्षणों, स्व-देखभाल, या डॉक्टर को कब दिखाना है के बारे में पूछें',
  },
  {
    value: 'ta',
    label: 'தமிழ்',
    speechLang: 'ta-IN',
    placeholder: 'உங்கள் சுகாதார கேள்வியை பதிவு செய்யவும்...',
    introTitle: 'இன்று நான் எப்படி உதவலாம்?',
    introSubtitle: 'அறிகுறிகள், சுய பராமரிப்பு அல்லது டாக்டரை எப்போது பார்க்க வேண்டும் என்று கேளுங்கள்',
  },
  {
    value: 'te',
    label: 'తెలుగు',
    speechLang: 'te-IN',
    placeholder: 'మీ ఆరోగ్య ప్రశ్నను టైప్ చేయండి...',
    introTitle: 'ఈ రోజు నేను ఎలా సహాయం చేయగలను?',
    introSubtitle: 'లక్షణాలు, స్వీయ సంరక్షణ లేదా డాక్టర్‌ని ఎప్పుడు కలవాలో అడగండి',
  },
  {
    value: 'kn',
    label: 'ಕನ್ನಡ',
    speechLang: 'kn-IN',
    placeholder: 'ನಿಮ್ಮ ಆರೋಗ್ಯ ಪ್ರಶ್ನೆಯನ್ನು ಟೈಪ್ ಮಾಡಿ...',
    introTitle: 'ಇಂದು ನಾನು ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?',
    introSubtitle: 'ಲಕ್ಷಣಗಳು, ಸ್ವಚ್ಛ ಆರೈಕೆ ಅಥವಾ ವೈದ್ಯರನ್ನು ಯಾವಾಗ ಭೇಟಿಯಾಗಬೇಕು ಎಂದು ಕೇಳಿ',
  },
  {
    value: 'ml',
    label: 'മലയാളം',
    speechLang: 'ml-IN',
    placeholder: 'നിങ്ങളുടെ ആരോഗ്യ ചോദ്യങ്ങൾ ടൈപ്പ് ചെയ്യുക...',
    introTitle: 'ഇന്ന് ഞാൻ നിങ്ങളെ എങ്ങനെ സഹായിക്കാം?',
    introSubtitle: 'ലക്ഷണങ്ങൾ, സ്വയംപരിചരണം, ഡോക്ടറെ കാണേണ്ട സമയം എന്നിവയെക്കുറിച്ച് ചോദിക്കൂ',
  },
];

const LANGUAGE_SPEECH_MAP: Record<LangCode, string> = LANGUAGE_OPTIONS.reduce(
  (acc, option) => {
    acc[option.value] = option.speechLang;
    return acc;
  },
  {} as Record<LangCode, string>
);

const defaultProfile: Profile = {
  diabetes: false,
  hypertension: false,
  pregnancy: false,
  age: undefined,
  sex: undefined,
  city: '',
};

interface Message {
  role: 'user' | 'assistant';
  content: string;
  facts?: any[];
  citations?: any[];
  safety?: any;
}

interface Profile {
  diabetes: boolean;
  hypertension: boolean;
  pregnancy: boolean;
  age?: number;
  sex?: SexOption;
  city?: string;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [lang, setLang] = useState<LangCode>('en');
  const [showProfile, setShowProfile] = useState(false);
  const [profile, setProfile] = useState<Profile>(defaultProfile);

  const currentLanguage =
    LANGUAGE_OPTIONS.find((option) => option.value === lang) ?? LANGUAGE_OPTIONS[0];

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Load profile from localStorage
    const saved = localStorage.getItem('healthProfile');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setProfile({ ...defaultProfile, ...parsed });
      } catch (error) {
        console.error('Error parsing saved profile', error);
        setProfile(defaultProfile);
      }
    }
  }, []);

  useEffect(() => {
    // Save profile to localStorage
    localStorage.setItem('healthProfile', JSON.stringify(profile));
  }, [profile]);

  useEffect(() => {
    // Scroll to bottom
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await transcribeAudio(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert('Could not access microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const transcribeAudio = async (audioBlob: Blob) => {
    try {
      const formData = new FormData();
      formData.append('file', audioBlob, 'audio.webm');

      const response = await axios.post(`${API_BASE}/stt`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      const text = response.data.text;
      setInput(text);
      // Auto-submit after transcription
      setTimeout(() => handleSend(text), 500);
    } catch (error) {
      console.error('Transcription error:', error);
      alert('Speech recognition failed. Please type your message.');
    }
  };

  const handleSend = async (text?: string) => {
    const messageText = text || input;
    if (!messageText.trim()) return;

    // Add user message
    const userMessage: Message = { role: 'user', content: messageText };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await axios.post(`${API_BASE}/chat`, {
        text: messageText,
        lang,
        profile
      });

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.answer,
        facts: response.data.facts,
        citations: response.data.citations,
        safety: response.data.safety
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Text-to-speech for response
      if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(response.data.answer);
        utterance.lang = LANGUAGE_SPEECH_MAP[lang] ?? 'en-US';
        utterance.rate = 0.9;
        window.speechSynthesis.speak(utterance);
      }
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-md px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-indigo-600">Health Assistant</h1>
          <p className="text-sm text-gray-500">AI-powered health information - Not medical advice</p>
        </div>
        <div className="flex items-center gap-4">
          {/* Language Picker */}
          <div className="flex items-center gap-2">
            <label htmlFor="language-select" className="text-sm text-gray-600">
              Language:
            </label>
            <select
              id="language-select"
              value={lang}
              onChange={(e) => setLang(e.target.value as LangCode)}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {LANGUAGE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {/* Profile Button */}
          <button
            onClick={() => setShowProfile(true)}
            className="p-2 rounded-full hover:bg-gray-100 transition"
          >
            <Settings className="w-6 h-6 text-gray-600" />
          </button>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center mt-20">
            <div className="inline-block p-6 bg-white rounded-2xl shadow-lg">
              <h2 className="text-xl font-semibold text-gray-800 mb-2">
                {currentLanguage.introTitle}
              </h2>
              <p className="text-gray-600">
                {currentLanguage.introSubtitle}
              </p>
            </div>
          </div>
        )}

        {messages.map((message, index) => {
          const mentalFact = message.facts?.find(f => f.type === 'mental_health_crisis');
          const pregnancyFact = message.facts?.find(f => f.type === 'pregnancy_alert');
          const personalizationFact = message.facts?.find(f => f.type === 'personalization');

          return (
            <div key={index}>
              {/* Message Bubble */}
              <div className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-2xl rounded-2xl px-6 py-4 ${
                    message.role === 'user'
                      ? 'bg-indigo-600 text-white'
                      : 'bg-white text-gray-800 shadow-md'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{message.content}</p>

                  {/* Citations */}
                  {message.citations && message.citations.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <p className="text-xs text-gray-500 mb-1">Sources:</p>
                      <div className="flex flex-wrap gap-2">
                        {message.citations.map((cite, i) => (
                          <span key={i} className="text-xs bg-gray-100 px-2 py-1 rounded">
                            {cite.topic ? `${cite.topic} (${cite.source})` : cite.source}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Red Flag Alert */}
              {message.safety?.red_flag && (
                <div className="mt-4 bg-red-50 border-2 border-red-500 rounded-xl p-6 shadow-lg">
                  <div className="flex items-start gap-4">
                    <AlertTriangle className="w-8 h-8 text-red-600 flex-shrink-0" />
                    <div className="flex-1 space-y-4">
                      <div>
                        <h3 className="text-lg font-bold text-red-800 mb-2">
                          ⚠️ {lang === 'en' ? 'URGENT: Seek Immediate Medical Care' : 'तत्काल: तुरंत चिकित्सा सहायता लें'}
                        </h3>
                        <p className="text-red-700">
                          {lang === 'en'
                            ? 'Your symptoms may indicate a serious condition requiring immediate attention.'
                            : 'आपके लक्षण एक गंभीर स्थिति का संकेत हो सकते हैं जिसके लिए तत्काल ध्यान देने की आवश्यकता है।'}
                        </p>
                      </div>

                      {/* Red Flag Facts */}
                      {message.facts?.find(f => f.type === 'red_flags') && (
                        <div className="bg-white rounded-lg p-4">
                          <p className="font-semibold text-red-800 mb-2">Possible conditions:</p>
                          {message.facts
                            .find(f => f.type === 'red_flags')
                            .data.map((rf: any, i: number) => (
                              <div key={i} className="mb-2">
                                <span className="font-medium">{rf.symptom}:</span>{' '}
                                <span className="text-gray-700">{rf.conditions.join(', ')}</span>
                              </div>
                            ))}
                        </div>
                      )}

                      {mentalFact && (
                        <div className="bg-white rounded-lg p-4 border border-red-200">
                          <p className="font-semibold text-red-800 mb-2">🧠 Mental health crisis support</p>
                          {mentalFact.data.matched?.length > 0 && (
                            <p className="text-sm text-gray-700 mb-2">
                              {lang === 'en'
                                ? `Detected phrases: ${mentalFact.data.matched.join(', ')}`
                                : `पहचाने गए वाक्यांश: ${mentalFact.data.matched.join(', ')}`}
                            </p>
                          )}
                          <ul className="list-disc list-inside text-gray-700 space-y-1">
                            {mentalFact.data.actions?.map((action: string, j: number) => (
                              <li key={j}>{action}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {pregnancyFact && (
                        <div className="bg-white rounded-lg p-4 border border-red-200">
                          <p className="font-semibold text-red-800 mb-2">🤰 Pregnancy alert</p>
                          {pregnancyFact.data.matched?.length > 0 && (
                            <p className="text-sm text-gray-700 mb-2">
                              {lang === 'en'
                                ? `Detected: ${pregnancyFact.data.matched.join(', ')}`
                                : `पहचाने गए संकेत: ${pregnancyFact.data.matched.join(', ')}`}
                            </p>
                          )}
                          <ul className="list-disc list-inside text-gray-700 space-y-1">
                            {pregnancyFact.data.guidance?.map((tip: string, j: number) => (
                              <li key={j}>{tip}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {personalizationFact && (
                        <div className="bg-white rounded-lg p-4 border border-yellow-200">
                          <p className="font-semibold text-yellow-700 mb-2">👤 Personalization notes</p>
                          <ul className="list-disc list-inside text-gray-700 space-y-1">
                            {personalizationFact.data.map((note: string, j: number) => (
                              <li key={j}>{note}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      <button
                        onClick={() => window.open('tel:108')}
                        className="flex items-center gap-2 bg-red-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-red-700 transition"
                      >
                        <Phone className="w-5 h-5" />
                        {lang === 'en' ? 'Call Emergency (108)' : 'आपातकालीन कॉल करें (108)'}
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Facts Panel */}
              {message.facts && message.facts.length > 0 && !message.safety?.red_flag && (
                <div className="mt-4 bg-blue-50 rounded-xl p-4 shadow">
                  <h4 className="font-semibold text-blue-900 mb-3">📊 Additional Information</h4>
                  {message.facts.map((fact, i) => (
                    <div key={i} className="mb-3">
                      {fact.type === 'contraindications' && fact.data.length > 0 && (
                        <div>
                          <p className="font-medium text-blue-800 mb-1">⛔ Things to avoid:</p>
                          <div className="space-y-2">
                            {fact.data.map((group: any, j: number) => (
                              <div key={j} className="bg-white rounded-lg px-3 py-2 border border-blue-100">
                                <p className="text-sm font-semibold text-blue-700">{group.condition}</p>
                                <ul className="list-disc list-inside text-gray-700 text-sm">
                                  {group.avoid.map((item: string, k: number) => (
                                    <li key={k}>{item}</li>
                                  ))}
                                </ul>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {fact.type === 'safe_actions' && fact.data.length > 0 && (
                        <div>
                          <p className="font-medium text-blue-800 mb-1">✅ Generally safe self-care:</p>
                          <div className="space-y-2">
                            {fact.data.map((group: any, j: number) => (
                              <div key={j} className="bg-white rounded-lg px-3 py-2 border border-blue-100">
                                <p className="text-sm font-semibold text-blue-700">{group.condition}</p>
                                <ul className="list-disc list-inside text-gray-700 text-sm">
                                  {group.actions.map((item: string, k: number) => (
                                    <li key={k}>{item}</li>
                                  ))}
                                </ul>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {fact.type === 'providers' && (
                        <div>
                          <p className="font-medium text-blue-800 mb-1">🏥 Healthcare providers:</p>
                          <ul className="space-y-1 text-gray-700">
                            {fact.data.map((p: any, j: number) => (
                              <li key={j}>
                                <strong>{p.provider}</strong>
                                {p.mode ? ` • ${p.mode}` : ''}
                                {p.phone ? ` – ${p.phone}` : ''}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {fact.type === 'mental_health_crisis' && (
                        <div>
                          <p className="font-medium text-blue-800 mb-1">🧠 Mental health support:</p>
                          {fact.data.matched?.length > 0 && (
                            <p className="text-sm text-gray-700">
                              {lang === 'en'
                                ? `Detected phrases: ${fact.data.matched.join(', ')}`
                                : `पहचाने गए वाक्यांश: ${fact.data.matched.join(', ')}`}
                            </p>
                          )}
                          <ul className="list-disc list-inside text-gray-700 text-sm mt-1 space-y-1">
                            {fact.data.actions?.map((action: string, j: number) => (
                              <li key={j}>{action}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {fact.type === 'pregnancy_alert' && (
                        <div>
                          <p className="font-medium text-blue-800 mb-1">🤰 Pregnancy guidance:</p>
                          {fact.data.matched?.length > 0 && (
                            <p className="text-sm text-gray-700">
                              {lang === 'en'
                                ? `Detected: ${fact.data.matched.join(', ')}`
                                : `पहचाने गए संकेत: ${fact.data.matched.join(', ')}`}
                            </p>
                          )}
                          <ul className="list-disc list-inside text-gray-700 text-sm mt-1 space-y-1">
                            {fact.data.guidance?.map((tip: string, j: number) => (
                              <li key={j}>{tip}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {fact.type === 'personalization' && (
                        <div>
                          <p className="font-medium text-blue-800 mb-1">👤 Personalization notes:</p>
                          <ul className="list-disc list-inside text-gray-700 text-sm space-y-1">
                            {fact.data.map((note: string, j: number) => (
                              <li key={j}>{note}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white rounded-2xl px-6 py-4 shadow-md">
              <div className="flex gap-2">
                <div className="w-2 h-2 bg-indigo-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-indigo-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-indigo-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="bg-white border-t border-gray-200 px-6 py-4">
        <div className="max-w-4xl mx-auto flex gap-3">
          <button
            onClick={isRecording ? stopRecording : startRecording}
            className={`p-4 rounded-full transition ${
              isRecording
                ? 'bg-red-500 hover:bg-red-600 animate-pulse'
                : 'bg-indigo-600 hover:bg-indigo-700'
            }`}
          >
            <Mic className="w-6 h-6 text-white" />
          </button>

          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={currentLanguage.placeholder}
            className="flex-1 px-6 py-4 rounded-full border-2 border-gray-200 focus:border-indigo-500 focus:outline-none text-gray-800"
            disabled={isLoading}
          />

          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || isLoading}
            className="p-4 rounded-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition"
          >
            <Send className="w-6 h-6 text-white" />
          </button>
        </div>
      </div>

      {/* Profile Modal */}
      {showProfile && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-800">
                {lang === 'en' ? 'Health Profile' : 'स्वास्थ्य प्रोफ़ाइल'}
              </h2>
              <button onClick={() => setShowProfile(false)} className="p-2 hover:bg-gray-100 rounded-full">
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="space-y-4">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={profile.diabetes}
                  onChange={(e) => setProfile({ ...profile, diabetes: e.target.checked })}
                  className="w-5 h-5 text-indigo-600 rounded"
                />
                <span className="text-gray-700">
                  {lang === 'en' ? 'I have Diabetes' : 'मुझे मधुमेह है'}
                </span>
              </label>

              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={profile.hypertension}
                  onChange={(e) => setProfile({ ...profile, hypertension: e.target.checked })}
                  className="w-5 h-5 text-indigo-600 rounded"
                />
                <span className="text-gray-700">
                  {lang === 'en' ? 'I have Hypertension' : 'मुझे उच्च रक्तचाप है'}
                </span>
              </label>

              {(profile.sex !== 'male') && (
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={profile.pregnancy}
                    onChange={(e) => setProfile({ ...profile, pregnancy: e.target.checked })}
                    className="w-5 h-5 text-indigo-600 rounded"
                  />
                  <span className="text-gray-700">
                    {lang === 'en' ? 'I am currently pregnant' : 'मैं वर्तमान में गर्भवती हूं'}
                  </span>
                </label>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {lang === 'en' ? 'Age (years)' : 'उम्र (वर्ष)'}
                  </label>
                  <input
                    type="number"
                    min={0}
                    value={profile.age ?? ''}
                    onChange={(e) =>
                      setProfile({
                        ...profile,
                        age: e.target.value ? Number(e.target.value) : undefined,
                      })
                    }
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {lang === 'en' ? 'Sex' : 'लिंग'}
                  </label>
                  <select
                    value={profile.sex ?? ''}
                    onChange={(e) =>
                      setProfile({
                        ...profile,
                        sex: e.target.value ? (e.target.value as SexOption) : undefined,
                        pregnancy:
                          e.target.value === 'female'
                            ? profile.pregnancy
                            : false,
                      })
                    }
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  >
                    <option value="">{lang === 'en' ? 'Select' : 'चुनें'}</option>
                    <option value="male">{lang === 'en' ? 'Male' : 'पुरुष'}</option>
                    <option value="female">{lang === 'en' ? 'Female' : 'महिला'}</option>
                    <option value="other">{lang === 'en' ? 'Other' : 'अन्य'}</option>
                  </select>
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {lang === 'en' ? 'City (optional)' : 'शहर (वैकल्पिक)'}
                  </label>
                  <input
                    type="text"
                    value={profile.city ?? ''}
                    onChange={(e) => setProfile({ ...profile, city: e.target.value })}
                    placeholder={lang === 'en' ? 'e.g., Mumbai' : 'उदाहरण: मुंबई'}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="pt-4 border-t">
                <p className="text-sm text-gray-500">
                  {lang === 'en'
                    ? 'This information helps provide personalized health advice.'
                    : 'यह जानकारी व्यक्तिगत स्वास्थ्य सलाह प्रदान करने में मदद करती है।'}
                </p>
              </div>
            </div>

            <button
              onClick={() => setShowProfile(false)}
              className="mt-6 w-full bg-indigo-600 text-white py-3 rounded-lg font-semibold hover:bg-indigo-700 transition"
            >
              {lang === 'en' ? 'Save' : 'सहेजें'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}