# Jobs Applier AI Agent (AIHawk) — Agente IA para Aplicaciones de Empleo

**Repositorio:** https://github.com/feder-cr/Jobs_Applier_AI_Agent_AIHawk  
**Licencia:** AGPL-3.0  
**Estrellas:** ~29,800 | **Forks:** ~4,500 | **Contributors:** 66  
**Lenguajes:** Python 92.6%, CSS 7.4%  
**Última versión:** v11.15.2024  
**⚠️ ESTADO: ARCHIVADO el 16 de Abril de 2026 — Solo lectura**

---

## ⚠️ Aviso Importante

Este repositorio fue **archivado (read-only)** el 16 de Abril de 2026. Ya no recibe actualizaciones ni pull requests. Sin embargo, el código sigue siendo open source bajo AGPL-3.0 y puede usarse como referencia o base para proyectos propios.

**Razón del archivado**: Remoción de plugins de proveedores terceros por problemas de copyright. La arquitectura central permanece abierta.

---

## ¿Qué es Jobs Applier AI Agent?

Es un **agente de IA que automatiza solicitudes de empleo**. Originalmente diseñado para LinkedIn, el agente:

1. Lee tu perfil y CV
2. Busca trabajos según criterios configurados
3. Analiza cada oferta con IA
4. Rellena formularios automáticamente
5. Personaliza la carta de presentación con LLMs
6. Envía aplicaciones

### Menciones en Prensa
- TechCrunch
- Business Insider
- The Verge
- Wired
- Semafor

---

## Arquitectura (Referencia para Proyectos Propios)

### Componentes Principales

```
Jobs_Applier_AI_Agent_AIHawk/
├── main.py                    # Punto de entrada
├── src/
│   ├── ai_hawk/               # Agente principal
│   │   ├── authenticator.py   # Login en plataformas
│   │   ├── job_manager.py     # Gestión de empleos
│   │   ├── llm/               # Integración LLMs
│   │   │   ├── llm_manager.py # Selector de modelo
│   │   │   └── prompts.py     # Prompts para candidaturas
│   │   ├── application_form_filler.py  # Rellena formularios
│   │   └── job_application_profile.py # Perfil del candidato
│   └── config/                # Configuración
├── data_folder/               # Datos de usuario
│   ├── resume.pdf             # CV
│   ├── plain_text_resume.yaml # CV en texto
│   └── config.yaml            # Parámetros de búsqueda
└── tests/                     # Tests
```

---

## Configuración (del código original)

### Perfil del candidato (`plain_text_resume.yaml`)
```yaml
personal_information:
  name: "Juan García"
  email: "juan@email.com"
  phone: "+34 600 000 000"
  location: "Madrid, España"
  linkedin: "linkedin.com/in/juangarcia"
  github: "github.com/juangarcia"

education:
  - degree: "Ingeniería Informática"
    university: "UPM"
    graduation_year: 2020

experience:
  - company: "Tech Company"
    position: "Python Developer"
    duration: "2020-2024"
    description: "Developed trading algorithms..."

skills:
  programming: ["Python", "JavaScript", "MQL5"]
  frameworks: ["FastAPI", "Django", "Next.js"]
  tools: ["Docker", "Git", "MetaTrader 5"]
```

### Parámetros de búsqueda (`config.yaml`)
```yaml
remote: True
experience_level:
  internship: False
  entry: True
  associate: True
  mid_senior_level: True
  director: False
  executive: False

job_types:
  full_time: True
  part_time: False
  contract: True

date:
  all_time: False
  month: True
  week: False
  24_hours: False

positions:
  - "Python Developer"
  - "Quantitative Analyst"
  - "Algo Trader"
  - "Trading Systems Developer"

locations:
  - "Spain"
  - "Remote"

distance: 100

company_blacklist: []
title_blacklist: ["intern", "junior (under 2 years)"]

llm_model_type: openai
llm_model: gpt-4o
```

---

## Módulo LLM (Reutilizable)

El módulo LLM de AIHawk es independiente y reutilizable. Genera respuestas personalizadas para formularios:

```python
# Ejemplo del sistema de prompts para formularios
from src.ai_hawk.llm.llm_manager import LLMManager

llm = LLMManager(model="gpt-4o", api_key="sk-...")

# Generar respuesta a pregunta de formulario
answer = llm.answer_question(
    question="Why do you want to work at our company?",
    resume_data=resume_data,
    job_description=job_desc,
)

# Generar carta de presentación personalizada
cover_letter = llm.generate_cover_letter(
    resume=resume_data,
    job=job_data,
    tone="professional",
)
```

---

## Application Form Filler (Core Reutilizable)

```python
from src.ai_hawk.application_form_filler import ApplicationFormFiller
from playwright.async_api import async_playwright

async def fill_job_application():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        filler = ApplicationFormFiller(
            llm=llm_manager,
            resume=resume_data,
            page=page,
        )
        
        await page.goto("https://jobs.example.com/apply")
        await filler.fill_all_fields()
```

---

## Relevancia para Trading Lab

Aunque este proyecto es para búsqueda de empleo, sus técnicas son aplicables al trading:

### Técnicas Adaptables

| Técnica en AIHawk | Aplicación en Trading |
|-------------------|----------------------|
| Form filling automático | Rellenar órdenes en plataformas web |
| LLM para personalizar respuestas | LLM para analizar contexto de mercado |
| Scraping de ofertas | Scraping de datos de mercado |
| Perfil estructurado en YAML | Perfil de estrategia de trading en YAML |
| Blacklist/whitelist de empresas | Filtros para instrumentos/sesiones |

### Código Reutilizable
1. **Playwright form filler**: Para rellenar formularios de brokers
2. **LLM Manager**: Para análisis de noticias y señales
3. **Config YAML parser**: Para configurar estrategias
4. **Job filter logic**: Adaptable para filtrar señales de trading

---

## Forks Activos Recomendados

Como el repo principal está archivado, considera estos forks activos:

```bash
# Buscar forks activos en GitHub
# https://github.com/feder-cr/Jobs_Applier_AI_Agent_AIHawk/network/members

# O buscar proyectos similares:
# - jobright.ai
# - linkedin-easy-apply-bot (varios)
```

---

## Instalación (Histórica)

```bash
# NOTA: Archivado - solo para referencia
git clone https://github.com/feder-cr/Jobs_Applier_AI_Agent_AIHawk.git
cd Jobs_Applier_AI_Agent_AIHawk
pip install -r requirements.txt

# Configurar perfil y parámetros
cp data_folder/plain_text_resume.yaml.example data_folder/plain_text_resume.yaml
# Editar con tu información

python main.py
```

---

## Lecciones de Arquitectura

Este proyecto demuestra cómo construir un agente de automatización completo:

1. **Separación de responsabilidades**: Autenticación, búsqueda, formularios, LLM — cada uno en su módulo
2. **Configuración YAML**: Parámetros sin hardcoding
3. **LLM abstraction**: Cambiar de GPT a Claude sin refactorizar
4. **Playwright para web**: Browser automation resistente a cambios
5. **Estado persistente**: Registro de aplicaciones enviadas para no duplicar

---

*Última actualización: 2026-05-05 | Extraído de: https://github.com/feder-cr/Jobs_Applier_AI_Agent_AIHawk*  
*⚠️ Repositorio archivado el 16 de Abril de 2026*
