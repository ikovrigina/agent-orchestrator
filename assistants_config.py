"""
OpenAI Assistants Configuration
Real assistant IDs from OpenAI Platform
"""

# All existing assistants with their real IDs
ASSISTANTS = {
    "chief_of_staff": {
        "id": "asst_YNkTp9OaRExKr2wiOfEddC9Y",
        "name": "iana-chief-of-staff",
        "role": "coordinator",
        "description": "Главный координатор, распределяет задачи между агентами"
    },
    "deep_listening": {
        "id": "asst_8KgaIIuAcNi8H6KtPr7VWes1",
        "name": "pm-deep-listening",
        "role": "specialist",
        "description": "Deep Listening проекты и практики"
    },
    "lsrc_tech": {
        "id": "asst_VhubS5qiL248WeCTqADu4yBZ",
        "name": "pm-lsrc-tech",
        "role": "specialist",
        "description": "LSRC App техническая разработка"
    },
    "documentary": {
        "id": "asst_wASgEj7SQEDuLkCsQy5voGVL",
        "name": "pm-documentary",
        "role": "specialist",
        "description": "Документальный фильм Berghain"
    },
    "billboards_experiments": {
        "id": "asst_P4bSUVW1kAY3keK3Gt2Jk3Yf",
        "name": "pm-billboardssf-experiments",
        "role": "specialist",
        "description": "Billboards SF и эксперименты"
    },
    "digital_presence": {
        "id": "asst_6Y5LPMYw9guLDgOB7IYr3B4O",
        "name": "pm-digital-presence",
        "role": "specialist",
        "description": "Сайт, соцсети, онлайн присутствие"
    }
}

# Chief of Staff is the main entry point
CHIEF_OF_STAFF_ID = ASSISTANTS["chief_of_staff"]["id"]

# Mapping of project keywords to specialists
PROJECT_TO_SPECIALIST = {
    "deep listening": "deep_listening",
    "dl": "deep_listening",
    "медитация": "deep_listening",
    "listening": "deep_listening",
    
    "lsrc": "lsrc_tech",
    "app": "lsrc_tech",
    "telegram": "lsrc_tech",
    "техника": "lsrc_tech",
    "код": "lsrc_tech",
    
    "film": "documentary",
    "documentary": "documentary",
    "berghain": "documentary",
    "фильм": "documentary",
    "монтаж": "documentary",
    
    "billboard": "billboards_experiments",
    "sf": "billboards_experiments",
    "experiment": "billboards_experiments",
    "ar": "billboards_experiments",
    
    "website": "digital_presence",
    "social": "digital_presence",
    "instagram": "digital_presence",
    "сайт": "digital_presence",
    "соцсети": "digital_presence"
}

from typing import Optional

def get_specialist_for_topic(topic: str) -> Optional[str]:
    """Determine which specialist to use based on topic keywords"""
    topic_lower = topic.lower()
    for keyword, specialist in PROJECT_TO_SPECIALIST.items():
        if keyword in topic_lower:
            return specialist
    return None
