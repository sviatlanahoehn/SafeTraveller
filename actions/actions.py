from typing import Text, Dict, Any, List, Union, Optional

#import rasa_core
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


class ActionGoBack(Action):
    def name(self):
        return 'action_go_back'
    def run(self, dispatcher, tracker, domain):
        return [UserUtteranceReverted(), ActionReverted(), UserUtteranceReverted(), ActionReverted()]


class ActionCheckBorders(Action):
    def name(self):
        return 'action_check_area'

    def run(self, dispatcher, tracker, domain):

        slots = []
        country_to = tracker.get_slot("country_to")
        country_from = tracker.get_slot("country_from")
        common_border = False
        area_type = ""
        safe_countries = {"Netherlands":[], "Belgium":["Luxembourg"], "Luxembourg":[], "Germany":[], "France":[]}

        if country_to=="Belgium" or country_from=="Belgium":
            common_border = True
        if country_from in safe_countries[country_to]:
            area_type = "SAFE"
        else:
            area_type = "RISK"

        slots.append(SlotSet("common_border", common_border))
        slots.append(SlotSet("area_type", area_type))
        return slots

class ValidateKeepContext(Action):
    def name(self):
        return "validate_keep_context"
    def run(self, dispatcher, tracker, domain):
        keep_details = tracker.get_slot("keep_details")
        if keep_details == True:
            return []
        else:
            return [AllSlotsReset()]
class ActionResetRegulationsType(Action):
    def name(self):
        return 'action_reset_regulations_type'
    def run(self, dispatcher, tracker, domain):
        return [SlotSet("regulations_type", None)]
class ActionSetLocal(Action):
    def name(self):
        return 'action_set_local'
    def run(self, dispatcher, tracker, domain):
        return [SlotSet("regulations_type", "local_regulations")]
class ActionSetOpen(Action):
    def name(self):
        return 'action_set_open'
    def run(self, dispatcher, tracker, domain):
        return [SlotSet("want_open_places", True)]
class ActionRepeatLast(Action):
    def name(self):
        return 'action_repeat_last'
    def run(self, dispatcher, tracker, domain):
        return [UserUtteranceReverted(), ActionReverted()]
class ActionValidateTransit(Action):
    def name(self):
        return 'action_validate_transit'
    def run(self, dispatcher, tracker, domain):
        slots = []
        return slots


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
#        countries = tracker.get_latest_entity_values(entity_type="country")
# countries = ['luxembourg', 'netherlands']
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
#                dispatcher.utter_message(response=f"utter_wrong_country_{p}")
#                slots.append(SlotSet(country_role, None))

#        num_country_from = len(list(tracker.get_latest_entity_values(entity_type="country", entity_role="from")))
#        num_country_to = len(list(tracker.get_latest_entity_values(entity_type="country", entity_role="to")))
#        country_from = next(tracker.get_latest_entity_values(entity_type="country", entity_role="from"), None)
#        country_to = next(tracker.get_latest_entity_values(entity_type="country", entity_role="to"), None)

#        if num_country_to==2 or num_country_from==2:
#            dispatcher.utter_message("Sorry, I am still learning and could not understand what countries you mentioned.")

        return slots

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
            if country.lower() not in country_names:
                dispatcher.utter_message(response=f"utter_wrong_country_{p}")
                slots.append(SlotSet(f"country_{p}", None))
                break
#        else:
#            dispatcher.utter_message(response=f"utter_wrong_country_to")

        return slots

#class ActionResetTransportSlot(Action):
#    def name(self):
#        return 'action_reset_transport_slot'
#    def run(self, dispatcher, tracker, domain):
#        transit = tracker.get_slot("transit_BE")
#        if transit==False:
#            plane_travel = "plane"
#        else:
#            plane_travel = None
#        return [SlotSet("plane_travel", plane_travel)]


class ActionUtterDisclaimer(Action):
    def name(self):
        return 'action_utter_disclaimer'
    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(f"| Important: I'm based in Luxembourg and was designed only for people based in and travelling within the BeNeLux countries. |\n")
        return []


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

        current_slots = []
        country_from = tracker.get_slot("country_from")
        current_slots.append(country_from)
        country_to = tracker.get_slot("country_to")
        current_slots.append(country_to)
        regulations_type = tracker.get_slot("regulations_type")
        current_slots.append(regulations_type)
        plane_travel = tracker.get_slot("plane_travel")
        current_slots.append(plane_travel)
        #visit_purpose = tracker.get_slot("visit_purpose")
        #current_slots.append(visit_purpose)
        one_day = tracker.get_slot("<48h")
        current_slots.append(one_day)

        dispatcher.utter_message(f"I could not undersatnd that, sorry.")
        dispatcher.utter_message(f"Please rephrase, so that we can continue.")

        return [UserUtteranceReverted()]


class ActionClearCountries(Action):
    def name(self) -> Text:
        return "action_clear_countries"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "DomainDict",
    ) -> List[Dict[Text, Any]]:
        slots = []
        correct_countries = tracker.get_slot("correct_countries")
        if correct_countries==False:
            slots.append(SlotSet("country_to", None))
            slots.append(SlotSet("country_from", None))
            slots.append(SlotSet("correct_countries", None))
        return slots


class ValidateWantLocalInfoForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_want_local_info_form"

    async def required_slots(
        self,
        slots_mapped_in_domain: List[Text],
        dispatcher: "CollectingDispatcher",
        tracker: "Tracker",
        domain: "DomainDict",
    ) -> Optional[List[Text]]:
        required_slots = slots_mapped_in_domain + ["regulations_type"]
        return required_slots

    async def extract_regulations_type(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> Dict[Text, Any]:

        last_intent = tracker.get_intent_of_latest_message()
        regulations_type = "entry_regulations"
        if last_intent == "affirm":
            regulations_type = "local_regulations"

        return {"regulations_type": regulations_type}


class ActionAskCorrectCountries(Action):
    def name(self):
        return "action_ask_correct_countries"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "DomainDict",
    ) -> List[Dict[Text, Any]]:
        country_to = tracker.get_slot("country_to")
        country_from = tracker.get_slot("country_from")
        dispatcher.utter_message(f"I am going to look for regulations on travel from {country_from} to {country_to}. Is that what you are looking for?")
        return []


# =========== Adaptation of ActionQueryAttribute class from tutorial-knowledge-base.actions
class CustomActionQueryKB(Action):

    def name(self):
        return "action_query_knowledgebase_cases"

    def __init__(self):
        #self.knowledge_base = InMemoryKnowledgeBase("/app/actions/knowledge_base_data.json")
        self.knowledge_base = InMemoryKnowledgeBase("actions/knowledge_base_data.json")

    def custom_get_attribute_of(
        self, regulations_type: Text, key_attribute: Text, entity: Text, attribute: Text
    ) -> List[Any]:
        if regulations_type not in self.knowledge_base.data:
            return []
        entities = self.knowledge_base.data[regulations_type]
        entity_of_interest = list(
            filter(lambda e: e[key_attribute] == entity, entities)
        )
       # if not entity_of_interest or len(entity_of_interest) > 1:
        if not entity_of_interest:
            return []
        return [entity_of_interest[0][attribute]]


    #def update_counter(self, dispatcher, tracker, domain):
    def entry_regulations_case_IDs(self, plane_travel, less_than_48h, area_type, country_to, transport_health_worker):
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
                    case_IDs.append(0)
                else:
                    case_IDs.append(3)

        elif country_to=="Belgium":
            if area_type=="SAFE":
                if less_than_48h==True:
                    if plane_travel==False:
                        case_IDs.append(0)
                else:
                    case_IDs.append(4)
            elif area_type=="RISK":
                if less_than_48h==True:
                    if plane_travel==False:
                        case_IDs.append(0)
                    else:
                        case_IDs.append(4)
                else:
                    case_IDs.append(5)

        if country_to=="France":
            if area_type=="SAFE":
                if cross_border_resident==True or transport_health_worker==True:
                    case_IDs.append(0)
                else:
                    case_IDs.append(6)
            elif area_type=="RISK":
                if plane_travel==False:
                    case_IDs.append(0)
                else:
                    case_IDs.append(7)


        elif country_to=="Germany":
            if less_than_48h==True or transport_health_worker==True:
                case_IDs.append(0)
            else:
                case_IDs.append(1.0)


        return case_IDs

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

    def transit_regulations_case_ID(self, country_to, transit):
        case_IDs = []
        if transit == True:
            case_IDs.append(0)
        return case_IDs

    def query_KB_rules(self, case_IDs, regulations_type):
        rules = []
        for case_ID in case_IDs:
            if case_ID != None:
                rules.append(self.custom_get_attribute_of(regulations_type, "ID", case_ID, "conditions")[0])
        return rules
    def query_KB_form_details(self, case_IDs, regulations_type):
        form_details = []
        for case_ID in case_IDs:
            if case_ID != None:
                form_details.append(self.custom_get_attribute_of(regulations_type, "ID", case_ID, "title")[0])
                form_details.append(self.custom_get_attribute_of(regulations_type, "ID", case_ID, "payload")[0])
        return form_details

    def slots_to_return(self):
#        slots = [SlotSet("indoors/outdoors", None), SlotSet("different_household", None)]
        # SlotSet("transit_BE", None), SlotSet("plane_travel", None)]
                # SlotSet("transit", None)
#        counter = tracker.get_slot("query_counter")
#        if counter==None:
#            counter = 1
#        elif counter==1:
#            pass
#        slots.append(SlotSet("query_counter", counter))
        slots = [SlotSet("want_to_continue", None), SlotSet("keep_details", None)]
        return slots


    def run(self, dispatcher, tracker, domain):

        regulations_type = tracker.get_slot("regulations_type")
        country_to = tracker.get_slot("country_to")
        country_from = tracker.get_slot("country_from")
        travel_with_children = tracker.get_slot("travelling_with_children")
        plane_travel = tracker.get_slot("plane_travel")
        transport_health_worker = tracker.get_slot("transport_health_worker")
        less_than_48h = tracker.get_slot("<48h")
#        transit_BE = tracker.get_slot("transit_BE")
        area_type = tracker.get_slot("area_type")
        different_household = tracker.get_slot("different_household")
#        choice=tracker.get_slot("vaccine_regulations_type")
        case_IDs = []
        buttons = []


        slots = self.slots_to_return()


        if regulations_type=="local_regulations":
            case_IDs = self.local_regulations_case_IDs(country_to, different_household)
            rule_indoors = self.query_KB_rules(case_IDs, regulations_type)[2]
            rule_outdoors = self.query_KB_rules(case_IDs, regulations_type)[1]
            rule_open_places = self.query_KB_rules(case_IDs, regulations_type)[0]
            dispatcher.utter_message(f"The following regulations apply in {country_to} : \n {rule_indoors} \n {rule_outdoors} \n {rule_open_places} \n ")

        elif regulations_type=="entry_regulations":
            case_IDs = self.entry_regulations_case_IDs(plane_travel, less_than_48h, area_type, country_to, transport_health_worker)
            rule_entry = self.query_KB_rules(case_IDs, regulations_type)[0]
            dispatcher.utter_message(f"{country_to} considers {country_from} a {area_type} area. The following regulations apply: \n {rule_entry}")
#            form_details = self.query_KB_form_details(case_IDs, regulations_type)
#            if form_details[0]:
#                title = form_details[0]
#                payload = form_details[1]
#                buttons.append(
#                    {"title": title, "payload": payload})
#                dispatcher.utter_message(buttons)

            #rule_transit = query_KB_rules(case_ID_transit)
            #if rule_transit:
            #    dispatcher.utter_message(f"The following regulations apply for transitting through {country_to_transit}: \n {rule_transit}\n")
            case_IDs = self.children_regulations_case_ID(country_to, regulations_type, travel_with_children)
            if case_IDs[0]!=None:
                rule_child = self.query_KB_rules(case_IDs, "children_exceptions")[0]
                if rule_child:
                    dispatcher.utter_message(f"The exceptions for children are: \n {rule_child}\n")

        elif regulations_type=="vaccine_regulations":
            case_IDs = self.vaccine_regulations_case_ID(country_to)
            vaccination_validity = self.query_KB_rules(case_IDs, regulations_type)[0]
            approved_vaccines = self.query_KB_rules(case_IDs, regulations_type)[1]
            dispatcher.utter_message(f"The following applies in {country_to} : \n {vaccination_validity} \n\n {approved_vaccines} \n ")

        else:
            dispatcher.utter_message(response="utter_query_failed")
            dispatcher.utter_message(response="utter_restart_please")
            return []

        return slots