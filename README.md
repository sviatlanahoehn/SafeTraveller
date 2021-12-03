# SafeTraveller - A conversational assistant for BeNeLux travellers

This is a prototype of a chatbot presented at the BNAIC conference in November 2021.

The artificial conversational assistant SafeTraveller was created as a Bachelor student project in 2021. In the context of ever-changing COVID-19 regulations, the idea behind the project is to facilitate access to travel-related rules for people living in regions where cross-border traffic is essential. The current implementation covers travel regulations for the Benelux and the Greater Region countries and informs users in English.

The assistant is implemented using RASA and works in Facebook Messenger. The prototype was created considering design recommendations for chatbot usability. A heuristic-based evaluation of the user experience of the prototype showed that the assistant outperforms the results of its colleagues in the eHealth sector on average.

The assistant works by filling slots with user travel details and querying the knowledge base of regulations to provide relevant information. The code for queries is implemented using Python framework. The regulations knowledge base is stored in a <em>knowledge_base_data.json</em> file in the <em>actions</em> directory.

Authors: Kristina Kudryavtseva, Sviatlana Höhn

# Application Snapshot
<img src="SafeTraveller.png" alt="app snapshot" width=200>

# Getting Started

## Talking to the bot in the terminal
1. Download or clone this repository
2. Install [RASA](https://rasa.com/docs/rasa/installation/)
3. Navigate to the project directory in the terminal
4. To talk to the bot in the terminal run two commands in separate windows:
- <em>rasa shell</em>
- <em>rasa run actions</em>

## Talking to the bot in Messenger
1. Install ngrok
2. Generate a link with ngrok
3. Login to Facebook Developers account and add the generated HTTPS link
4. Follow steps 1-4 for running in terminal replacing <em>rasa shell</em> by <em>rasa run</em> command


# Future Work
In the future, we hope to be able to improve this prototype, fulfiling the following points:
- Automation of the COVID-19 regulations collection
- Regulations information in several languages (e.g. English, French, German)
- Handling of contradictions through logic
