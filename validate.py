from pydantic import BaseModel, Field
from typing import List, Optional

class Additional(BaseModel):
    brandTone: str
    references: str
    scalability: str

class Behavior(BaseModel):
    attitude: str
    keyTraits: str
    personalityType: str
    proactivity: str
    tone: str

class General(BaseModel):
    audience: str
    format: str
    language: str
    name: str
    role: str

class Restrictions(BaseModel):
    behaviorRestrictions: str
    contentFilter: str
    forbiddenTopics: str
    stopWords: str

class Scenarios(BaseModel):
    contextMemory: str
    mainTasks: str
    scenarioExamples: str

class Style(BaseModel):
    complexity: str
    emojiExamples: str
    emojiUsage: str
    memeExamples: str
    memeUsage: str
    phraseExamples: str
    communication_register: str = Field(alias="register")
    stickerUsage: str

class Technical(BaseModel):
    aiComponent: str
    buttonsMenu: str
    integrations: str
    platforms: str
    timeouts: str

class Visual(BaseModel):
    ageGender: str
    avatar: str
    clothingStyle: str
    colorPalette: str
    gestures: str
    visualType: str

class CharacterData(BaseModel):
    additional: Additional
    behavior: Behavior
    general: General
    restrictions: Restrictions
    scenarios: Scenarios
    style: Style
    technical: Technical
    visual: Visual

class CharacterModel(BaseModel):
    characterData: CharacterData
