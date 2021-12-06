from typing import Text, Dict, Any, List, Union, Optional

from rasa_sdk.events import UserUtteranceReverted, ActionReverted
from rasa_sdk.events import SlotSet
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.knowledge_base.storage import InMemoryKnowledgeBase
from rasa_sdk.events import EventType
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.forms import FormAction
from rasa_sdk.events import AllSlotsReset
from rasa_sdk.events import FollowupAction


""" Action to ckeck if the two countries have a common border. """
class ActionCheckBorders(Action):
    def name(self):
        return 'action_check_borders'

    def run(self, dispatcher, tracker, domain):

        neighbours = {"Luxembourg":["France", "Belgium", "Germany"], "Germany":["Netherlands", "France", "Luxembourg", "Belgium"], "France":["Belgium", "Luxembourg", "Germany"], "Belgium":["Luxembourg", "Germany", "Netherlands", "France"], "Netherlands":["Germany", "Belgium"]}
        country_to = tracker.get_slot("country_to")
        country_from = tracker.get_slot("country_from")

        common_border = False
        if country_to in neighbours[country_from]:
            common_border = True

        return [SlotSet("common_border", common_border)]


""" Action executed after queries to keep or discard context collected for the last query. """
class ValidateKeepContext(Action):
    def name(self):
        return "validate_keep_context"
    def run(self, dispatcher, tracker, domain):
        keep_details = tracker.get_slot("keep_details")
        if keep_details == True:
            return []
        else:
            return [AllSlotsReset()]


""" Action executed when a new regulations type should be entered by the user. """
class ActionResetRegulationsType(Action):
    def name(self):
        return 'action_reset_regulations_type'
    def run(self, dispatcher, tracker, domain):
        return [SlotSet("regulations_type", None)]


""" Action executed after confirmation of local regualations intent by the user. """
class ActionSetLocal(Action):
    def name(self):
        return 'action_set_local'
    def run(self, dispatcher, tracker, domain):
        return [SlotSet("regulations_type", "local_regulations")]


""" Action to fill in the boolean slot that records whether open places information is wanted by the user. """
class ActionSetOpen(Action):
    def name(self):
        return 'action_set_open'
    def run(self, dispatcher, tracker, domain):
        return [SlotSet("want_open_places", True)]


""" Action to extract country values from the latest user message. """
class ActionExtractCountries(Action):
    def name(self):
        return 'action_extract_countries'
    def run(self, dispatcher, tracker, domain):
        country_names = {"Germany":['cologne', 'berlin', 'frankfurt', 'germany', 'deutchland', 'de', 'german'], "France":['paris', 'metz' 'france', 'fr', 'french'], "Belgium":['brussels', 'belgium'],"Luxembourg":['lu', 'lux', 'luxembourg'],"Netherlands":['holland', 'nl', 'netherlands', 'netherlands', 'the']}
        slots = [] #SlotSet("regulations_type", "entry_regulations")]

        country_from = []
        country_to = []
        prepositions = ["to", "from"]
        sentence = list(tracker.latest_message['text'].split(" "))
        for p in prepositions:
            if p in sentence:
                index = sentence.index(p)
                index += 1
                country_role = f"country_{p}"
                country = sentence[index]
                countries = country_names.keys()
                for country_key in countries:
                    if country.lower() in country_names.get(country_key):
                        slots.append(SlotSet(country_role, country_key))
                        break

        return slots


"""Action to validate that valid country values were extracted."""
class ActionValidateCountries(Action):
    def name(self):
        return 'action_validate_countries'
    def run(self, dispatcher, tracker, domain):
        country_names = ["france", "germany", "belgium", "luxembourg","netherlands"]
        slots = [] #SlotSet("regulations_type", "entry_regulations")]
        prepositions = ["to", "from"]
        regulations_type = tracker.get_slot("regulations_type")
        for p in prepositions:
            if regulations_type=="vaccine_regulations" or regulations_type=="local_regulations":
                p = "to"
            country = tracker.get_slot(f"country_{p}")
            if country != None:
                if country.lower() not in country_names:
                    dispatcher.utter_message(response=f"utter_wrong_country_{p}")
                    slots.append(SlotSet(f"country_{p}", None))
                    break

        return slots


""" Action to utter the conversation beginning disclaimer. """
class ActionUtterDisclaimer(Action):
    def name(self):
        return 'action_utter_disclaimer'
    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(f"| Important: I'm based in Luxembourg and was designed only for people based in and travelling within the BeNeLux countries. |\n")
        return []


""" Overwrite of default fallback action with a new utterance."""
class ActionDefaultFallback(Action):

    def name(self) -> Text:
        return "action_default_fallback_custom"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response="utter_custom_fallback")

        dispatcher.utter_message(f"I could not undersatnd that, sorry.")
        dispatcher.utter_message(f"Please rephrase, so that we can continue.")

        return [UserUtteranceReverted()]


""" Action to empty context of user countries. Empties slots country_to, country_from, correct_countries."""
class ActionClearCountries(Action):
    def name(self) -> Text:
        return "action_clear_countries"

    def run(self, dispatcher, tracker: Tracker, domain: "DomainDict",) -> List[Dict[Text, Any]]:

        slots = []
        correct_countries = tracker.get_slot("correct_countries")
        if correct_countries==False:
            slots.append(SlotSet("country_to", None))
            slots.append(SlotSet("country_from", None))
            slots.append(SlotSet("correct_countries", None))

        return slots


""" Action to validate the local regultions intent."""
class ValidateWantLocalInfoForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_want_local_info_form"


"""Adds regulations_type slot to the required slots."""
    async def required_slots(
        self,
        slots_mapped_in_domain: List[Text],
        dispatcher: "CollectingDispatcher",
        tracker: "Tracker",
        domain: "DomainDict",
    ) -> Optional[List[Text]]:
        required_slots = domain_slots + ["regulations_type"]
        return required_slots


"""Fills in the regulations_type slot."""
    async def extract_regulations_type(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> Dict[Text, Any]:

        last_intent = tracker.get_intent_of_latest_message()
        regulations_type = "entry_regulations"
        if last_intent == "affirm":
            regulations_type = "local_regulations"

        return {"regulations_type": regulations_type}



# =========== Adaptation of ActionQueryAttribute class from tutorial-knowledge-base.actions
class CustomActionQueryKB(Action):

    def name(self):
        return "action_query_knowledgebase_cases"

    def __init__(self):
        self.knowledge_base = InMemoryKnowledgeBase("actions/knowledge_base_data.json")

"""Retrieves attribute value with key_attribute corresponding to entity value."""
    def custom_get_attribute_of(
        self, regulations_type: Text, key_attribute: Text, entity: Text, attribute: Text
    ) -> List[Any]:
        if regulations_type not in self.knowledge_base.data:
            return []
        entities = self.knowledge_base.data[regulations_type]
        entity_of_interest = list(
            filter(lambda e: e[key_attribute] == entity, entities)
        )
        if not entity_of_interest:
            return []
        return [entity_of_interest[0][attribute]]

"""Based on the slot values filled in by user, defines the entry regulations case ID passed for the knowledge base query."""
    def entry_regulations_case_IDs(self, cross_border_resident, plane_travel, less_than_48h, area_type, country_to, transport_health_worker, transit):
        case_IDs = []

        if country_to=="Luxembourg":
            if plane_travel==False or transport_health_worker==True:
                case_IDs.append(0)
            else: #plane_travel==True and transport_health_worker==False:
                case_IDs.append(1.0)

        elif country_to=="Netherlands":
            if area_type=="SAFE":
                if plane_travel==False:
                    case_IDs.append(0)
                else:
                    case_IDs.append(2)
            elif area_type=="RISK":
                if plane_travel==False:
                    case_IDs.append(1.0)
                else:
                    if transit==True:
                        case_IDs.append(2)
                    else: case_IDs.append(3)

        elif country_to=="Belgium":
            if area_type=="SAFE":
                if less_than_48h==True:
                    if plane_travel==False:
                        case_IDs.append(0)
                    else:
                        case_IDs.append(4)
                else:
                    case_IDs.append(5)
            elif area_type=="RISK":
                if transit==True:
                    if plane_travel==True:
                        case_IDs.append(5.0)
                    else:
                        case_IDs.append(0)
                else:
                    if less_than_48h==True:
                        if plane_travel==False:
                            case_IDs.append(1.0)
                        else:
                            case_IDs.append(5)
                    else:
                        case_IDs.append(5)

        if country_to=="France":
            if area_type=="SAFE":
                if cross_border_resident==True or transport_health_worker==True:
                    case_IDs.append(0)
                else:
                    case_IDs.append(6)
            elif area_type=="RISK":
                case_IDs.append(7)


        elif country_to=="Germany":
            if transit==True:
                if plane_travel==False:
                    case_IDs.append(1.0)
                else:
                    case_IDs.append(1.2)
            else:
                if less_than_48h==True or transport_health_worker==True:
                    case_IDs.append(0)
                else:
                    case_IDs.append(1.0)


        return case_IDs

"""Based on the slot values filled in by user, defines the local regulations case ID passed for the knowledge base query."""
    def local_regulations_case_IDs(self, country_to, different_household):
        case_IDs = []

        if country_to=="Belgium":
            case_IDs.append(12) #open_places
            if different_household==False:
                case_IDs.append(0) #outdoors
                case_IDs.append(2) #indoors
            else:
                case_IDs.append(1)
                case_IDs.append(3)

        elif country_to=="Luxembourg":
            case_IDs.append(13)
            if different_household==False:
                case_IDs.append(4)
                case_IDs.append(6)
            else:
                case_IDs.append(5)
                case_IDs.append(7)

        elif country_to=="Netherlands":
            case_IDs.append(14)
            if different_household==False:
                case_IDs.append(8)
                case_IDs.append(10)
            else:
                case_IDs.append(9)
                case_IDs.append(11)

        elif country_to=="France":
            case_IDs.append(17)
            case_IDs.append(15)
            case_IDs.append(16)

        elif country_to=="Germany":
            case_IDs.append(20)
            case_IDs.append(18)
            case_IDs.append(19)

        return case_IDs

"""Based on the slot values filled in by user, defines the vaccination regulations case ID passed for the knowledge base query."""
    def vaccine_regulations_case_ID(self, country_to):
        case_IDs = []

        if country_to=="Belgium":
                case_IDs.append(0)
                case_IDs.append(1)
        elif country_to=="Luxembourg":
                case_IDs.append(2)
                case_IDs.append(3)
        elif country_to=="Netherlands":
                case_IDs.append(4)
                case_IDs.append(5)
        elif country_to=="France":
                case_IDs.append(6)
                case_IDs.append(7)
        elif country_to=="Germany":
                case_IDs.append(8)
                case_IDs.append(9)

        return case_IDs

"""Based on the slot values filled in by user, defines the children exceptions regulations case ID passed for the knowledge base query."""
    def children_regulations_case_ID(self, country_to, regulations_type, travel_with_children):
        case_IDs = [None]
        if travel_with_children==True:
            case_IDs.remove(None)
            if regulations_type=="entry_regulations":
                if country_to=="Belgium":
                    case_IDs.append(0)
                elif country_to=="Luxembourg":
                    case_IDs.append(2)
                elif country_to=="Netherlands":
                    case_IDs.append(4)
                elif country_to=="France":
                    case_IDs.append(5)
                elif country_to=="Germany":
                    case_IDs.append(7)
            elif regulations_type=="local_regulations":
                if country_to=="Belgium":
                    case_IDs.append(1)
                elif country_to=="Luxembourg":
                    case_IDs.append(3)
                elif country_to=="France":
                    case_IDs.append(6)
                elif country_to=="Germany":
                    case_IDs.append(8)

        return case_IDs

"""Based on the slot values filled in by user, defines the transit regulations case ID passed for the knowledge base query."""
    def transit_regulations_case_ID(self, country_to, transit):
        case_IDs = []
        if transit == True:
            case_IDs.append(0)
        return case_IDs

"""Calls custom_get_attribute_of for each applicable regulations case ID."""
    def query_KB_rules(self, case_IDs, regulations_type):
        rules = []
        for case_ID in case_IDs:
            if case_ID != None:
                rules.append(self.custom_get_attribute_of(regulations_type, "ID", case_ID, "conditions")[0])
        return rules

"""Fills in the area_type slot based on the status of the country corresponding to the country_from value."""
    def area_check(self, country_to, country_from):

        safe_countries = {"Netherlands":[], "Belgium":["France"], "Luxembourg":["Germany", "Netherlands", "France", "Belgium"], "Germany":["France", "Netherlands", "France", "Belgium"], "France":["Germany", "Netherlands", "Luxembourg", "Belgium"]}
        area_type = None
        if country_from in safe_countries[country_to]:
            area_type = "SAFE"
        else:
            area_type = "RISK"
        return area_type

"""Extracts collected slot values.
   Based on the regulations_type value, calls a regulations_case_ID function
   and queries the knowledge_base by calling query_KB_rules.
   Sends a message to the user with generic text and the regulations from the knowledge_base."""
    def run(self, dispatcher, tracker, domain):

        neighbours = {"Luxembourg":["France", "Belgium", "Germany"], "Germany":["Netherlands", "France", "Luxembourg", "Belgium"], "France":["Belgium", "Luxembourg", "Germany"], "Belgium":["Luxembourg", "Germany", "Netherlands", "France"], "Netherlands":["Germany", "Belgium"]}

        regulations_type = tracker.get_slot("regulations_type")
        country_to = tracker.get_slot("country_to")
        country_from = tracker.get_slot("country_from")
        travel_with_children = tracker.get_slot("travelling_with_children")
        plane_travel = tracker.get_slot("plane_travel")
        transport_health_worker = tracker.get_slot("transport_health_worker")
        less_than_48h = tracker.get_slot("<48h")
        area_type = self.area_check(country_to, country_from)
        different_household = tracker.get_slot("different_household")
        third_country = tracker.get_slot("third_country")
        common_border = tracker.get_slot("common_border")
        transit = tracker.get_slot("transit")
        cross_border_resident = tracker.get_slot("cross_border_resident")
        case_IDs = []
        buttons = []

        slots = [SlotSet("want_to_continue", None), SlotSet("keep_details", None), SlotSet("third_country", None)]

        if regulations_type=="local_regulations":
            case_IDs = self.local_regulations_case_IDs(country_to, different_household)
            rule_indoors = self.query_KB_rules(case_IDs, regulations_type)[2]
            rule_outdoors = self.query_KB_rules(case_IDs, regulations_type)[1]
            rule_open_places = self.query_KB_rules(case_IDs, regulations_type)[0]
            dispatcher.utter_message(f"The following regulations apply in {country_to} : \n\n {rule_indoors} \n\n {rule_outdoors} \n\n {rule_open_places} \n ")

        elif regulations_type=="entry_regulations":
            case_IDs = self.entry_regulations_case_IDs(cross_border_resident, plane_travel, less_than_48h, area_type, country_to, transport_health_worker, transit)
            rule_entry = self.query_KB_rules(case_IDs, regulations_type)[0]
            dispatcher.utter_message(f"{country_to} considers {country_from} a {area_type} area: \n {rule_entry}")

            if (common_border==False or third_country==True) and plane_travel==False:

                dispatcher.utter_message("The following regulations apply to transit travellers in the neighbouring countries:\n")

                options = neighbours[country_from]
                if country_to in options:
                    options.remove(country_to)
                less_than_48h = True

                for neighbour in options:
                    area_type = self.area_check(neighbour, country_from)
                    case_IDs = self.entry_regulations_case_IDs(cross_border_resident, plane_travel, less_than_48h, area_type, neighbour, transport_health_worker, transit)
                    rule_entry = self.query_KB_rules(case_IDs, regulations_type)[0]
                    dispatcher.utter_message(f"{neighbour} considers {country_from} a {area_type} area: \n {rule_entry}")

            case_IDs = self.children_regulations_case_ID(country_to, regulations_type, travel_with_children)
            if case_IDs[0]!=None:
                rule_child = self.query_KB_rules(case_IDs, "children_exceptions")[0]
                if rule_child:
                    dispatcher.utter_message(f"\n{rule_child}\n")

        elif regulations_type=="vaccine_regulations":
            case_IDs = self.vaccine_regulations_case_ID(country_to)
            vaccination_validity = self.query_KB_rules(case_IDs, regulations_type)[0]
            approved_vaccines = self.query_KB_rules(case_IDs, regulations_type)[1]
            dispatcher.utter_message(f"The following rules apply in {country_to} : \n {vaccination_validity} \n\n {approved_vaccines} \n ")

        else:
            dispatcher.utter_message(response="utter_query_failed")
            dispatcher.utter_message(response="utter_restart_please")
            return []

        return slots