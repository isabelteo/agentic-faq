
# Problem Statement

Issues are increasingly complex and inter-related, requiring multiple agencies to work together. Agency silos have been difficult to mitigate with different processes and systems implemented across the public service. 

For citizens:
-  Navigating the labyrinth of public services is confusing and can feel like knocking on countless wrong doors, with each redirection leading to longer resolution times and growing frustration. 

For frontline officers:
- Time Spent on Inter-agency Coordination rather than impactful work: Agencies now carry the load of requests raised wrongly by citizens, who were unclear which agency to direct their concern to. Frontline officers scramble in the background to identify the most relevant agency with domain expertise.Rather than focusing on critical requests that only their agency can handle, frontline officers struggle with interagency coordination

# What the Government has done

To reduce the heavy inter-agency coordination work done by frontline officers, the government has introduced Whole-of-Government service delivery models and digital initiatives that seek to address this issue.

**Implementation approaches:**
- **Coordinating Offices that serve as a central point of contact for citizens and who work to drive strategy for reducing interagency silos:** Municipal Services Office (MND) handles feedback on municipal issues that span multiple agencies.  ServiceSG was also created by PSD to develop one-stop physical and digital shops for WOG. 
- **Digital One-Stop Shops to empower self-service for citizens:**
  - **OneService (MSO):** Focused on municipal issues by MSO, this app handled 38% of 1.7M complaints in 2023. To improve outreach, MSO created OneService Telegram and WhatsApp Chatbot that handled 30,000+ cases a month with 85% accuracy in routing to correct agency. This translated to 2,000 man hours saved and resolution times cut by up to 2 working days.
  - **LifeSG (ServiceSG):** This app integrates 18 systems and 40 APIs to center services around 'Moments of Life'. New parents can complete birth registration, bank account setup, and government benefits applications in 15 minutes (vs. 60 minutes previously).

On top of these initiatives, there are outreach platforms and services to ensure adoption for impact
- **Digital awareness platform that inform the public of what government digital service or contact to use:** GoWhere is a government platform that centralises information and resources for over 20 government campaigns. It has over 61 million visits across 28 government initiatives.
- **Physical concierges that faciltiate outreach enable digital enablement**: 9 ServiceSG centers with cross-trained officers assist citizens with digital and inter-agency transactions. These centers ssisted 306,000+ citizens with 70% being seniors and had 450,000+ transactions in 2024.
  - **For struggling citizens, physical concierges are not enogh. Coordinators are assigned to work closely and long term with them** ComLink+ assigns a dedicated Family Coach as a single point of contact to help families navigate all available social support services based on their needs


## Sources

- [ComLink+](https://www.msf.gov.sg/media-room/article/msf-committee-of-supply-2024-empowering-all-families-to-achieve-their-aspirations)
- [Inter-agency sharing of outcomes and resources](https://www.psd.gov.sg/newsroom/inter-agency-sharing-of-outcomes-and-resources/)
- [LifeSG Case Study](https://journal.govcx.org/case-study-singapore-moments-of-life-service-design/)
- [ServiceSG Article](https://govinsider.asia/intl-en/article/truly-no-wrong-door-servicesg-brings-wog-services-to-less-digitally-ready-citizens)
- [GoWhere](https://www.tech.gov.sg/products-and-services/for-citizens/directories-and-distribution/gowhere/)
---

# What remains to be improved

For citizens, there is still a level of fragmentation - should they call the agency directly? call ServiceSG? Go to OneService or go to LifeSG or go to SupportGoWhere?

For frontline officers of agencies, requests from confused citizens may still land onto agencies who have to take on the coordination work - how can we make it easier for these frontline officers to identify the next step?

For coordinating bodies, how can we effectively onboard generalist frontline officers for the ServiceSG branches and OneService office?

Proposal: 1 Assistant on SuperApp Singpass for all interagency enquireies and in the future, this agent can help to service across multiple platforms

# Competitors

For govtech developers and data scientists, GovTech announced new AI capabilities on its Government on Commercial Cloud (GCC) platform. 

## Platform-as-a-Service: Chatbot Services
- **VICA:** VICA utilises Hybrid AI, combining Natural Language Processing (NLP) and Generative AI (Gen AI) to balance automation with accuracy. Over 60 Singapore government agencies use VICA, hosting 100+ chatbots. Of these, one-fifth serve internal government agency users, while the rest engage with the public. VICA chatbots receive an average of over 800,000 monthly queries.
- **AIBots** from GovTech that can enable public service officers to upload documents to create a RAG then configure an agentic chatbot in less than 15 minutes. It had 40,000 users, 115 agencies, 12,000 bots created, and 1M messages sent between Aug 2024 - Feb 2025.

### Safety & Governance for AI services
- **AI Guardian** — Platform for safety testing and governance
- **Litmus** — Adversarial testing to assess safety/security risks before deployment
- **Sentinel** — Real-time content moderation and output filtering after deployment
- **LionGuard 2** — Open-source multilingual content moderation guardrail (4 Singapore languages, Singlish, code-switching); available as API

## Model-as-a-Service

Govtech is working on
- High-quality, contextualised government datasets for training and fine-tuning models
- Shared platforms and pre-trained models to lower AI adoption barriers

## Infrastructure-as-a-Service: AI on the Cloud
- GovTech's AI infrastructure is built the Artificial Intelligence Government Cloud Cluster (AGCC) with Vertex AI models. It will have AI-optimized infrastructure powered by Nvidia A100 GPUs hosted on Google Cloud. This new partnership allows public officers to develop and deploy AI agents while keeping sensitive data within on-premises data centres that are fully disconnected from the public internet. 

## Where RE:AI Stands Out in the Long Term AI Strategy
- Handle data of higher classification then Confidential: GCC 2.0 handles up to Confidental
- Cost Control: Deploy open-source Mistral Models on-premise or on GCC. No per-query pricing compared to using Vertex AI
- Customization: Fine-tune models on your GovTech's customised dataset efforts

This enquiry assistant handles data that is public so the selling point is less clear. But driving the value of AI can align with the selling of infrastructure-as-as-service instead when compared with GCC.


## Sources
- [CDO Trends: Pilots & System-wide Transformation](https://www.cdotrends.com/story/4907/pilots-system-wide-transformation-sg-governments-next-leap-ai?refresh=auto)
- [Tech.gov.sg: GovTech's Use of AI](https://www.tech.gov.sg/technews/how-govtech-uses-ai-to-enhance-digital-public-services/)
- [Tech.gov.sg: AIBots](https://www.tech.gov.sg/products-and-services/for-government-agencies/productivity-and-marketing/aibots/)
https://www.vica.gov.sg/
- [GCC](https://www.developer.tech.gov.sg/products/categories/infrastructure-and-hosting/gcc/overview)

## Design Considerations and Scoping Judgement

- **Stand-alone vs Superapp:** Singpass integration strategy
- **ServiceSG approach**

---

## POC and Test Results

---

## Scaling in Production and Costs

##