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
        safe_countries = {"Netherlands":[], "Belgium":["Luxembourg"], "Luxembourg":[]}

        if country_to=="Belgium" or country_from=="Belgium":
            common_border = True

        if country_from in safe_countries[country_to]:
            area_type = "SAFE"
        else:
            area_type = "RISK"


        slots.append(SlotSet("common_border", common_border))
        slots.append(SlotSet("area_type", area_type))
        return slots


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
# ==== ???
class ActionValidateTransit(Action):
    def name(self):
        return 'action_validate_transit'
    def run(self, dispatcher, tracker, domain):
        slots = []
        return slots



class ActionValidateCountries(Action):
    def name(self):
        return 'action_validate_countries'
    def run(self, dispatcher, tracker, domain):
        countries = ["belgium","luxembourg","netherlands"]
        country_main_lettrs = ["bel","lux","nether"]
        slots = [SlotSet("regulations_type", "entry_regulations")]
        common_border=False

        num_country_from = len(list(tracker.get_latest_entity_values(entity_type="country", entity_role="from")))
        num_country_to = len(list(tracker.get_latest_entity_values(entity_type="country", entity_role="to")))
        if num_country_to==1 and num_country_from==1:
            country_from = next(tracker.get_latest_entity_values(entity_type="country", entity_role="from"), None)
            country_to = next(tracker.get_latest_entity_values(entity_type="country", entity_role="to"), None)
            distinct_countries = country_from.lower()!=country_to.lower()

            if country_to.lower() in countries:
                slots.append(SlotSet("country_to", country_to))
            else:
                dispatcher.utter_message(response="utter_wrong_country_to")
                slots.append(SlotSet("country_to", None))

            if country_from.lower() in countries and distinct_countries:
                slots.append(SlotSet("country_from", country_from))
            else:
                dispatcher.utter_message(response="utter_wrong_country_from")
                slots.append(SlotSet("country_from", None))

            if country_to=="Belgium" or country_from=="Belgium":
                common_border=True
            slots.append(SlotSet("common_border", common_border))
        else:
            slots.append(SlotSet("country_to", None))
            slots.append(SlotSet("country_from", None))
            dispatcher.utter_message(response="utter_not_understood")
        return slots




class ActionResetTransportSlot(Action):
    def name(self):
        return 'action_reset_transport_slot'
    def run(self, dispatcher, tracker, domain):
        transit = tracker.get_slot("transit_BE")
        if transit==False:
            plane_travel = "plane"
        else:
            plane_travel = None
        return [SlotSet("plane_travel", plane_travel)]



class ActionUtterDisclaimer(Action):
    def name(self):
        return 'action_utter_disclaimer'
    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(f"| Important: I'm based in Luxembourg and was designed only for people based in and travelling within the BeNeLux countries. |\n")
        return []

#class ActionAskConfirmCollectedInfo(Action):
#    def name(self):
#        return 'action_ask_confirm_collected_info'

#    def run(self, dispatcher, tracker, domain):
#        country_to = tracker.get_slot("country_to")
#        dispatcher.utter_message(f"Here is the trip details that I have collected:\n")
#        if country_to=="Luxembourg":
#            plane_travel = tracker.get_slot("plane_travel")
#            dispatcher.utter_message(f"You are going by {plane_travel}\n")
#            visit_purpose = tracker.get_slot("visit_purpose")
#            if visit_purpose=="work":
#                dispatcher.utter_message(f"You are going for {visit_purpose}-related purposes\n")
#        elif country_to=="Belgium":
#            one_day = tracker.get_slot("<48h")
#            if one_day==True:
#                dispatcher.utter_message(f"You are going for one day\n")
#            visit_purpose = tracker.get_slot("visit_purpose")
#            if visit_purpose!=None:
#                dispatcher.utter_message(f"You are going for {visit_purpose}-related purposes\n")
#            tsw = tracker.get_slot("transport_health_worker")
#            if tsw==True:
#                dispatcher.utter_message(f"You are a transport sector worker\n")
#        elif country_to=="Netherlands":
#            plane_travel = tracker.get_slot("plane_travel")
#            if plane_travel!=None:
#                dispatcher.utter_message(f"You are going by {plane_travel}\n")
#            visit_purpose = tracker.get_slot("visit_purpose")
#            dispatcher.utter_message(f"You are going for {visit_purpose}-related purposes\n")
#            tsw = tracker.get_slot("transport_health_worker")
#            if tsw==True:
#                dispatcher.utter_message(f"You are a transport sector worker\n")
#        return []


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
        self.knowledge_base = InMemoryKnowledgeBase("knowledge_base_data.json")

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


# ------  UNNECESSARY ATTRIBUTE "location" ------ !!!
    def run(self, dispatcher, tracker, domain):
        regulations_type = tracker.get_slot("regulations_type")
        country_to = tracker.get_slot("country_to")
        attribute = "conditions"
        key_attribute = "id"
        case_id_transit= None
        case_id_children = None
        case_id_open_places = None
        children_travel = tracker.get_slot("travelling_with_children")
        case_id_details = None
        case_id_indoors = None
        case_id_outdoors = None
        case_id = None
        case_id_VV = None
        case_id_AV = None

        if regulations_type == "entry_regulations":
            plane_travel = tracker.get_slot("plane_travel")
#            transport_health_worker = tracker.get_slot("transport_health_worker")
#            NL_worker = tracker.get_slot("NL_worker")
            less_than_48h = tracker.get_slot("<48h")
            transit_BE = tracker.get_slot("transit_BE")
            area_type = tracker.get_slot("area_type")

            if country_to=="Luxembourg":
                if plane_travel==True:
                    case_id_children = 2
                if plane_travel==False or transport_health_worker==True:
                    case_id = 0
                elif plane_travel==True and transport_health_worker==False:
                    case_id = 1.0
                else:
                    dispatcher.utter_message(response="utter_query_failed")
                    dispatcher.utter_message(response="utter_restart_please")

            elif country_to=="Netherlands":
                case_id_children = 4
                if area_type=="SAFE":
                    if plane_travel==False:
                        case_id = 0
                    else:
                        case_id = 2
                elif area_type=="RISK":
                    if plane_travel==False:
                        case_id = 0
                    else:
                        case_id = 3
                else:
                    dispatcher.utter_message(response="utter_query_failed")
                    dispatcher.utter_message(response="utter_restart_please")

            elif country_to=="Belgium":
                case_id_children = 0
                if area_type=="SAFE":
                    if less_than_48h==True and plane_travel==False:
                        case_id = 0
                    elif plane_travel==True or less_than_48h==False:
                        case_id = 4
                elif area_type=="RISK":
                    if less_than_48h==True and plane_travel==False:
                        case_id = 1.1
                    elif plane_travel==True or less_than_48h==False:
                        case_id = 5
                else:
                    dispatcher.utter_message(response="utter_query_failed")
                    dispatcher.utter_message(response="utter_restart_please")

            else:
                dispatcher.utter_message(response="utter_did_not_find_the_country")

            if transit_BE == True:
                case_id_transit = 0
                country_to_transit = "Belgium"

        elif regulations_type == "local_regulations":
            place = tracker.get_slot("indoors/outdoors")
            location = tracker.get_slot("country_to")
            #going_from = tracker.get_slot("visit_purpose")
            different_household = tracker.get_slot("different_household")
            open_places = tracker.get_slot("want_open_places")
            LRT = tracker.get_slot("local_regulations_type")


            if LRT=="open_places":
                if location=="Belgium":
                    case_id_open_places = 12
                elif location=="Luxembourg":
                    case_id_open_places = 13
                elif location=="Netherlands":
                    case_id_open_places = 14

            else:
                if location=="Belgium":
                    case_id_children = 1
                    if LRT=="both":
                        case_id_open_places = 12
                    if place=="outdoors":
                        if different_household == False:
                            case_id_outdoors = 0
                        else:
                            case_id_outdoors = 1
                    elif place=="indoors":
                        if different_household == False:
                            case_id_indoors = 2
                        else:
                            case_id_indoors = 3
                    elif place=="both":
                        if different_household==False:
                            case_id_outdoors = 0
                            case_id_indoors = 2
                        else:
                            case_id_indoors = 1
                            case_id_outdoors = 3
                    #else:
                    #    dispatcher.utter_message(response="utter_query_failed")
                    #    dispatcher.utter_message(response="utter_restart_please")
                elif location=="Luxembourg":
                    case_id_children = 3
                    if LRT=="both":
                        case_id_open_places = 13
                    if place=="outdoors":
                        if different_household == False:
                            case_id_outdoors = 4
                        else:
                            case_id_outdoors = 5
                    elif place=="indoors":
                        if different_household == False:
                            case_id_indoors = 6
                        else:
                            case_id_indoors = 7
                    elif place=="both":
                        if different_household==False:
                            case_id_outdoors = 4
                            case_id_indoors = 6
                        else:
                            case_id_indoors = 5
                            case_id_outdoors = 7
                elif location=="Netherlands":
                    if LRT=="both":
                        case_id_open_places = 14
                    if place=="outdoors":
                        if different_household == False:
                            case_id_outdoors = 8
                        else:
                            case_id_outdoors = 9
                    elif place=="indoors":
                        if different_household == False:
                            case_id_indoors = 10
                        else:
                            case_id_indoors = 11
                    elif place=="both":
                        if different_household==False:
                            case_id_outdoors = 8
                            case_id_indoors = 10
                        else:
                            case_id_indoors = 9
                            case_id_outdoors = 11

        elif regulations_type == "vaccine_regulations":
            country = tracker.get_slot("country_to")
            choice=tracker.get_slot("vaccine_regulations_type")

            if country=="Belgium":
                if choice=="vaccine_validity":
                    case_id_VV = 0
                elif choice=="approved_vaccines":
                    case_id_AV = 1
                elif choice=="both":
                    case_id_VV = 0
                    case_id_AV = 1
            elif country=="Luxembourg":
                if choice=="vaccine_validity":
                    case_id_VV = 2
                elif choice=="approved_vaccines":
                    case_id_AV = 3
                elif choice=="both":
                    case_id_VV = 2
                    case_id_AV = 3
            elif country=="Netherlands":
                if choice=="vaccine_validity":
                    case_id_VV = 4
                elif choice=="approved_vaccines":
                    case_id_AV = 5
                elif choice=="both":
                    case_id_VV = 4
                    case_id_AV = 5
        else:
            dispatcher.utter_message(response="utter_query_failed")
            dispatcher.utter_message(response="utter_restart_please")

            return []



#-----------RETREIVING INFOR FROM THE KB---------
        rule_transit = ""
        if case_id_transit != None:
            rule_transit = self.custom_get_attribute_of(regulations_type, key_attribute, case_id_transit, attribute)[0]

        rule_child = ""
        if children_travel == True and case_id_children != None:
            rule_child = self.custom_get_attribute_of("children_exceptions", key_attribute, case_id_children, attribute)[0]

        rule_open_pl = ""
        if case_id_open_places != None:
            rule_open_pl = self.custom_get_attribute_of(regulations_type, key_attribute, case_id_open_places, attribute)[0]

        if regulations_type=="local_regulations":

            rule_indoors = ""
            if case_id_indoors!=None:
                rule_indoors = self.custom_get_attribute_of(regulations_type, key_attribute, case_id_indoors, attribute)[0]

            rule_outdoors = ""
            if case_id_outdoors!=None:
                rule_outdoors = self.custom_get_attribute_of(regulations_type, key_attribute, case_id_outdoors, attribute)[0]
            dispatcher.utter_message(f"The following regulations apply in {location} : \n {rule_indoors} \n {rule_outdoors} \n {rule_open_pl} \n ")
            rule_open_pl = ""

        elif regulations_type=="entry_regulations":
            rule_entry = self.custom_get_attribute_of(regulations_type, key_attribute, case_id, attribute)[0]
            dispatcher.utter_message(f"The following regulations apply in {country_to} : \n {rule_entry}")
            #dispatcher.utter_message(f"rule_transit: {rule_transit}")
            if rule_transit:
                dispatcher.utter_message(f"The following regulations apply for transitting through {country_to_transit}: \n {rule_transit}\n")
            if rule_child:
                dispatcher.utter_message(f"The following exceptions for children apply in {country_to} : \n {rule_child}\n")

        elif regulations_type=="vaccine_regulations":

            vaccination_validity = ""
            if case_id_VV!=None:
                vaccination_validity = self.custom_get_attribute_of(regulations_type, key_attribute, case_id_VV, attribute)[0]

            approved_vaccines = ""
            if case_id_AV!=None:
                approved_vaccines = self.custom_get_attribute_of(regulations_type, key_attribute, case_id_AV, attribute)[0]

            dispatcher.utter_message(f"The following applies in {country_to} : \n {vaccination_validity} \n\n {approved_vaccines} \n ")


        slots = [SlotSet("indoors/outdoors", None), SlotSet("different_household", None)]
        # SlotSet("transit_BE", None), SlotSet("plane_travel", None)]
                # SlotSet("transit", None)
        if regulations_type=="local_regulations":
            slots.append(SlotSet("want_open_places", False))
        counter = tracker.get_slot("query_counter")
#===== counting queries
        if counter==None:
            counter = 1
        elif counter==1:
            counter = 2
        else:
            pass
        slots.append(SlotSet("query_counter", counter))

        return slots
