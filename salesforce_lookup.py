from simple_salesforce import Salesforce
import logging
from typing import Dict, Any, Optional
import re
import asyncio
from functools import lru_cache

logger = logging.getLogger(__name__)


class SalesforceLookup:
    """Optimized Salesforce client focused on fast phone number lookup for dynamic variables"""

    def __init__(
        self, username: str, password: str, security_token: str, domain: str = "login"
    ):
        self.username = username
        self.password = password
        self.security_token = security_token
        self.domain = domain
        self.sf = None
        self._connect()

    def _connect(self):
        """Initialize Salesforce connection"""
        try:
            self.sf = Salesforce(
                username=self.username,
                password=self.password,
                security_token=self.security_token,
                domain=self.domain,
            )
            logger.info("Successfully connected to Salesforce for phone lookup")
        except Exception as e:
            logger.error(f"Failed to connect to Salesforce: {str(e)}")
            raise

    @lru_cache(maxsize=1000)
    def _normalize_phone(self, phone_number: str) -> str:
        """Normalize phone number for Salesforce lookup with caching"""
        # Remove all non-digit characters
        digits_only = re.sub(r"\D", "", phone_number)

        # Handle US numbers
        if len(digits_only) == 11 and digits_only.startswith("1"):
            return f"+{digits_only}"
        elif len(digits_only) == 10:
            return f"+1{digits_only}"
        else:
            return f"+{digits_only}"

    async def lookup_phone_number(self, phone_number: str) -> Dict[str, Any]:
        """
        Look up a phone number in Salesforce across Contacts and Leads with optimizations
        Returns simplified data structure for dynamic variables
        """
        try:
            normalized_phone = self._normalize_phone(phone_number)
            logger.info(f"Looking up phone number: {normalized_phone}")

            # Run contact and lead searches in parallel
            contact_task = asyncio.create_task(
                asyncio.to_thread(self._search_contacts_optimized, normalized_phone)
            )
            lead_task = asyncio.create_task(
                asyncio.to_thread(self._search_leads_optimized, normalized_phone)
            )

            # Wait for both searches to complete
            contact_result, lead_result = await asyncio.gather(contact_task, lead_task)

            # Prefer contact over lead if both found
            if contact_result:
                logger.info(f"Found existing contact: {contact_result.get('Name')}")
                result = {"found": True, "type": "contact", "record": contact_result}
            elif lead_result:
                logger.info(f"Found existing lead: {lead_result.get('Name')}")
                result = {"found": True, "type": "lead", "record": lead_result}
            else:
                logger.info(f"No existing record found for {normalized_phone}")
                result = {"found": False, "type": None, "record": None}

            return result

        except Exception as e:
            logger.error(f"Error looking up phone number {phone_number}: {str(e)}")
            return {"found": False, "type": None, "record": None, "error": str(e)}

    def _search_contacts_optimized(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Optimized contact search using single query with OR conditions"""
        try:
            # Single query with all phone fields combined using OR
            query = f"""
                SELECT Id, Name, Email, Phone, MobilePhone, Account.Name, Account.Id,
                       Phone_Number_Aggregated__c, Phone_Number_Aggregated_Plain_Text__c,
                       Form_Phone__c, ZoomInfo_Mobile_Phone__c,
                       Account.Owner.Name
                FROM Contact 
                WHERE Phone = '{phone_number}' 
                   OR MobilePhone = '{phone_number}'
                   OR Phone_Number_Aggregated__c = '{phone_number}'
                   OR Phone_Number_Aggregated_Plain_Text__c = '{phone_number}'
                   OR Form_Phone__c = '{phone_number}'
                   OR ZoomInfo_Mobile_Phone__c = '{phone_number}'
                LIMIT 1
            """
            
            result = self.sf.query(query)

            if result["records"]:
                contact = result["records"][0]

                # Flatten the response for easier access
                flattened = {
                    "Id": contact.get("Id"),
                    "Name": contact.get("Name"),
                    "Email": contact.get("Email"),
                    "Phone": contact.get("Phone"),
                    "MobilePhone": contact.get("MobilePhone"),
                }

                # Add account information if available
                if contact.get("Account"):
                    account = contact["Account"]
                    flattened["Company"] = account.get("Name")
                    flattened["AccountId"] = account.get("Id")

                    # Add account owner name if available
                    if account.get("Owner"):
                        flattened["AE_Name"] = account["Owner"].get("Name")

                return flattened

            return None

        except Exception as e:
            logger.error(f"Error searching contacts: {str(e)}")
            return None

    def _search_leads_optimized(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Optimized lead search using single query with OR conditions"""
        try:
            # Single query with all phone fields combined using OR
            query = f"""
                SELECT Id, Name, Email, Phone, MobilePhone, Company, Status,
                       Phone_Number_Aggregated__c, Phone_Number_Aggregated_Plain_Text__c,
                       Form_Phone__c, ZoomInfo_Mobile_Phone__c,
                       Owner.Name
                FROM Lead 
                WHERE (Phone = '{phone_number}' 
                   OR MobilePhone = '{phone_number}'
                   OR Phone_Number_Aggregated__c = '{phone_number}'
                   OR Phone_Number_Aggregated_Plain_Text__c = '{phone_number}'
                   OR Form_Phone__c = '{phone_number}'
                   OR ZoomInfo_Mobile_Phone__c = '{phone_number}')
                AND IsConverted = false 
                LIMIT 1
            """
            
            result = self.sf.query(query)

            if result["records"]:
                lead = result["records"][0]

                # Flatten the response
                flattened = {
                    "Id": lead.get("Id"),
                    "Name": lead.get("Name"),
                    "Email": lead.get("Email"),
                    "Phone": lead.get("Phone"),
                    "MobilePhone": lead.get("MobilePhone"),
                    "Company": lead.get("Company"),
                    "Status": lead.get("Status"),
                }

                # Add owner information if available
                if lead.get("Owner"):
                    owner = lead["Owner"]
                    flattened["AE_Name"] = owner.get("Name")

                return flattened

            return None

        except Exception as e:
            logger.error(f"Error searching leads: {str(e)}")
            return None