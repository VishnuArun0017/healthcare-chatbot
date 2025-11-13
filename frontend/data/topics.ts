export interface TopicSuggestion {
  id: string;
  prompt: string;
  tags?: string[];
}

export interface TopicCategory {
  id: string;
  title: string;
  description: string;
  icon: string;
  suggestions: TopicSuggestion[];
}

export const TOPIC_CATEGORIES: TopicCategory[] = [
  {
    id: "symptom-triage",
    title: "Symptom Triage",
    description: "Spot warning signs and plan your next steps.",
    icon: "alert-triangle",
    suggestions: [
      {
        id: "symptom-chest-pressure",
        prompt: "I'm feeling pressure in my chest—how urgent is this?",
        tags: ["red flag", "cardiac"],
      },
      {
        id: "symptom-shortness-breath",
        prompt: "Shortness of breath started today. What should I watch for?",
        tags: ["breathing", "emergency"],
      },
      {
        id: "symptom-severe-headache",
        prompt: "I suddenly developed the worst headache of my life. What do I do?",
        tags: ["neurology", "urgent"],
      },
      {
        id: "symptom-child-fever",
        prompt: "My child has a fever—when is it time to see a doctor?",
        tags: ["pediatrics", "fever"],
      },
    ],
  },
  {
    id: "self-care",
    title: "At-Home Care",
    description: "Practical routines and relief strategies.",
    icon: "heart",
    suggestions: [
      {
        id: "selfcare-cough",
        prompt: "What are safe home remedies for a lingering cough?",
        tags: ["respiratory"],
      },
      {
        id: "selfcare-food-poisoning",
        prompt: "I think I ate something bad—how should I hydrate and recover?",
        tags: ["digestive", "rehydration"],
      },
      {
        id: "selfcare-joint-pain",
        prompt: "My knees ache after exercise. How can I manage that at home?",
        tags: ["musculoskeletal"],
      },
      {
        id: "selfcare-allergy-flare",
        prompt: "Seasonal allergies are flaring up—any self-care tips?",
        tags: ["allergy"],
      },
    ],
  },
  {
    id: "chronic-conditions",
    title: "Chronic Conditions",
    description: "Daily management and flare prevention.",
    icon: "activity",
    suggestions: [
      {
        id: "chronic-diabetes",
        prompt: "I have diabetes—what should I monitor when I feel dizzy?",
        tags: ["diabetes", "monitoring"],
      },
      {
        id: "chronic-hypertension",
        prompt: "My blood pressure has been high—what steps should I take today?",
        tags: ["hypertension"],
      },
      {
        id: "chronic-pregnancy",
        prompt: "I'm in my third trimester and feel swelling—when should I worry?",
        tags: ["pregnancy", "swelling"],
      },
      {
        id: "chronic-asthma",
        prompt: "Asthma symptoms are increasing at night—How can I adjust my routine?",
        tags: ["asthma", "respiratory"],
      },
    ],
  },
  {
    id: "prevention",
    title: "Prevention & Wellness",
    description: "Build healthier habits and routines.",
    icon: "shield",
    suggestions: [
      {
        id: "prevention-heart-healthy",
        prompt: "How can I create a heart-healthy meal plan this week?",
        tags: ["heart", "nutrition"],
      },
      {
        id: "prevention-stress",
        prompt: "Feeling stressed lately—what daily practices can help?",
        tags: ["mental health", "wellness"],
      },
      {
        id: "prevention-sleep",
        prompt: "I'd like to improve my sleep hygiene. Where should I start?",
        tags: ["sleep", "lifestyle"],
      },
      {
        id: "prevention-checkup",
        prompt: "What preventive screenings should I keep up with this year?",
        tags: ["screening", "annual"],
      },
    ],
  },
  {
    id: "caregiving",
    title: "Caregiving",
    description: "Support loved ones and coordinate care.",
    icon: "users",
    suggestions: [
      {
        id: "caregiving-elderly-fall",
        prompt: "My elderly parent fell—how do I monitor them at home tonight?",
        tags: ["elder care", "safety"],
      },
      {
        id: "caregiving-child-nutrition",
        prompt: "How can I help my child maintain a balanced diet during exams?",
        tags: ["pediatrics", "nutrition"],
      },
      {
        id: "caregiving-post-surgery",
        prompt: "A family member is recovering after surgery—what should I do to support them?",
        tags: ["post-op", "monitoring"],
      },
      {
        id: "caregiving-mental-health",
        prompt: "Someone close to me seems very down—how can I support them gently?",
        tags: ["mental health", "support"],
      },
    ],
  },
];
