"""
Global Coverage Tool using Telnyx's internal coverage data.

Handles queries like "Do you have local numbers in US?" or "Do you support SMS in Germany?"
Provides conservative responses with references to official coverage documentation.
"""

from langchain_core.tools import tool
from typing import Dict, Any, List
import json
import logging
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

class TelnyxCoverageEngine:
    """Fast in-memory coverage lookup engine"""
    
    def __init__(self):
        self.coverage_df = None
        self.load_coverage_data()
    
    def load_coverage_data(self):
        """Load coverage data from CSV into memory"""
        try:
            # Use relative path from project root for deployment compatibility
            import os
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            csv_path = os.path.join(project_root, "[INTERNAL] Telnyx Global Coverage 2025 - Global Coverage.csv")
            
            # Load CSV with correct header - pandas reads "Country" column at header=6
            # This accounts for how the CSV was exported from Excel
            self.coverage_df = pd.read_csv(csv_path, header=6)
            
            # Clean column names
            self.coverage_df.columns = self.coverage_df.columns.str.strip()
            
            # Standardize data
            self.coverage_df['Country'] = self.coverage_df['Country'].str.strip()
            self.coverage_df['Number Type'] = self.coverage_df['Number Type'].str.strip()
            
            # Convert Y/N to boolean for easier filtering
            bool_columns = ['Inbound Calling', 'Outbound Local', 'Outbound International**', 
                           'Emergency Calling', 'Fax', 'Porting', '2-way SMS']
            
            for col in bool_columns:
                if col in self.coverage_df.columns:
                    self.coverage_df[col] = self.coverage_df[col].str.upper() == 'Y'
            
            logger.info(f"Loaded {len(self.coverage_df)} coverage records from CSV")
            
        except Exception as e:
            logger.error(f"Error loading coverage data: {str(e)}")
            self.coverage_df = pd.DataFrame()
    
    def check_capability(self, countries: List[str], number_types: List[str] = None, 
                        capabilities: List[str] = None) -> Dict[str, Any]:
        """Check if specific capabilities are available in countries"""
        if self.coverage_df.empty:
            return {"status": "error", "message": "Coverage data not available"}
        
        results = {}
        
        for country in countries:
            # Flexible country matching
            country_matches = self.coverage_df[
                self.coverage_df['Country'].str.contains(country, case=False, na=False)
            ]
            
            if country_matches.empty:
                results[country] = {
                    "found": False,
                    "message": f"No coverage data found for {country}"
                }
                continue
            
            country_result = {
                "found": True,
                "number_types": {},
                "capabilities": {},
                "notes": []
            }
            
            # Check number types if specified
            if number_types:
                for number_type in number_types:
                    type_matches = country_matches[
                        country_matches['Number Type'].str.contains(number_type, case=False, na=False)
                    ]
                    
                    country_result["number_types"][number_type] = {
                        "available": not type_matches.empty,
                        "details": []
                    }
                    
                    if not type_matches.empty:
                        for _, row in type_matches.iterrows():
                            country_result["number_types"][number_type]["details"].append({
                                "exact_type": row.get('Number Type', ''),
                                "category": row.get('Numbers Category', ''),
                                "restrictions": self._get_restrictions(row.get('Numbers Category', ''))
                            })
            
            # Check capabilities if specified  
            if capabilities:
                # Get all rows for this country to check capabilities
                for capability in capabilities:
                    capability_available = False
                    capability_details = []
                    
                    for _, row in country_matches.iterrows():
                        if capability.lower() == 'sms' and row.get('2-way SMS', False):
                            capability_available = True
                            capability_details.append(f"SMS available with {row.get('Number Type', 'unknown')} numbers")
                        elif capability.lower() == 'inbound' and row.get('Inbound Calling', False):
                            capability_available = True  
                            capability_details.append(f"Inbound calling with {row.get('Number Type', 'unknown')} numbers")
                        elif capability.lower() == 'outbound' and row.get('Outbound Local', False):
                            capability_available = True
                            capability_details.append(f"Outbound calling with {row.get('Number Type', 'unknown')} numbers")
                        elif capability.lower() == 'emergency' and row.get('Emergency Calling', False):
                            capability_available = True
                            capability_details.append(f"Emergency calling with {row.get('Number Type', 'unknown')} numbers")
                        elif capability.lower() == 'porting' and row.get('Porting', False):
                            capability_available = True
                            capability_details.append(f"Number porting with {row.get('Number Type', 'unknown')} numbers")
                    
                    country_result["capabilities"][capability] = {
                        "available": capability_available,
                        "details": capability_details
                    }
            
            # Add any special notes
            special_notes = []
            categories = country_matches['Numbers Category'].dropna().unique()
            if 'B' in categories or 'C' in categories:
                special_notes.append("Some number types have usage restrictions")
            if 'B/C' in categories:
                special_notes.append("Mixed restrictions - verification needed")
            
            country_result["notes"] = special_notes
            results[country] = country_result
        
        return results
    
    def _get_restrictions(self, category: str) -> str:
        """Get restriction description for category"""
        category_restrictions = {
            'A': 'No restrictions - suitable for all customer types',
            'B': 'Cannot resell - for own business use only',  
            'C': 'Check with numbering team before selling',
            'B/C': 'Mixed restrictions - verify before use'
        }
        return category_restrictions.get(str(category).strip(), 'Contact sales for restrictions')


# Initialize coverage engine
coverage_engine = TelnyxCoverageEngine()


@tool
def global_coverage_tool(query: str, countries: str = "", number_types: str = "", capabilities: str = "") -> str:
    """
    Check Telnyx coverage for specific questions like "Do you have local numbers in US?" or "Do you support SMS in Germany?"
    
    Args:
        query: The customer's question about coverage
        countries: Countries to check (e.g., "United States, Germany")  
        number_types: Number types to check (e.g., "local, toll-free")
        capabilities: Capabilities to check (e.g., "sms, inbound, emergency")
        
    Returns:
        JSON string with conservative coverage information and official reference
    """
    try:
        # Parse inputs
        country_list = [c.strip() for c in countries.split(",") if c.strip()] if countries else []
        number_type_list = [nt.strip().lower() for nt in number_types.split(",") if nt.strip()] if number_types else []
        capability_list = [cap.strip().lower() for cap in capabilities.split(",") if cap.strip()] if capabilities else []
        
        # If no specific params provided, try to extract from query
        if not country_list and not number_type_list and not capability_list:
            # Simple extraction from query - could be enhanced
            query_lower = query.lower()
            
            # Common countries
            if 'us' in query_lower or 'united states' in query_lower or 'america' in query_lower:
                country_list = ['United States']
            if 'uk' in query_lower or 'united kingdom' in query_lower or 'britain' in query_lower:
                country_list = ['United Kingdom'] 
            if 'germany' in query_lower:
                country_list = ['Germany']
            if 'canada' in query_lower:
                country_list = ['Canada']
                
            # Common number types
            if 'local' in query_lower:
                number_type_list = ['local']
            if 'toll-free' in query_lower or 'toll free' in query_lower:
                number_type_list = ['toll-free']
            if 'mobile' in query_lower:
                number_type_list = ['mobile']
                
            # Common capabilities
            if 'sms' in query_lower or 'text' in query_lower or 'messaging' in query_lower:
                capability_list = ['sms']
            if 'inbound' in query_lower:
                capability_list = ['inbound']
            if 'outbound' in query_lower:
                capability_list = ['outbound']
            if 'emergency' in query_lower:
                capability_list = ['emergency']
            if 'porting' in query_lower or 'port' in query_lower:
                capability_list = ['porting']
        
        if not country_list:
            return json.dumps({
                "status": "needs_clarification",
                "message": "Please specify which countries you'd like me to check coverage for.",
                "suggestion": "For example: 'Check coverage for United States and Germany'"
            })
        
        logger.info(f"Coverage query: {query} | Countries: {country_list} | Types: {number_type_list} | Capabilities: {capability_list}")
        
        # Check coverage
        results = coverage_engine.check_capability(country_list, number_type_list, capability_list)
        
        # Generate conservative response
        response_parts = []
        
        for country, data in results.items():
            if not data.get("found", False):
                response_parts.append(f"❓ I don't have coverage data for {country} in my current database.")
                continue
            
            country_responses = []
            
            # Report on number types
            if number_type_list and data.get("number_types"):
                for number_type, type_data in data["number_types"].items():
                    if type_data["available"]:
                        details = type_data.get("details", [])
                        if details:
                            categories = [d.get("category", "") for d in details]
                            if any(cat in ["B", "C"] for cat in categories):
                                country_responses.append(f"Based on my research, Telnyx appears to offer {number_type} numbers in {country}, but there may be usage restrictions.")
                            else:
                                country_responses.append(f"Based on my research, Telnyx appears to offer {number_type} numbers in {country}.")
                        else:
                            country_responses.append(f"Based on my research, Telnyx appears to offer {number_type} numbers in {country}.")
                    else:
                        country_responses.append(f"I don't see {number_type} numbers available in {country} in my current data.")
            
            # Report on capabilities  
            if capability_list and data.get("capabilities"):
                for capability, cap_data in data["capabilities"].items():
                    if cap_data["available"]:
                        capability_name = {
                            'sms': 'SMS/text messaging',
                            'inbound': 'inbound calling', 
                            'outbound': 'outbound calling',
                            'emergency': 'emergency calling',
                            'porting': 'number porting'
                        }.get(capability, capability)
                        
                        country_responses.append(f"Based on my research, Telnyx appears to support {capability_name} in {country}.")
                    else:
                        capability_name = {
                            'sms': 'SMS/text messaging',
                            'inbound': 'inbound calling',
                            'outbound': 'outbound calling', 
                            'emergency': 'emergency calling',
                            'porting': 'number porting'
                        }.get(capability, capability)
                        
                        country_responses.append(f"❌ I don't see {capability_name} available in {country} in my current data.")
            
            # Add notes if any
            if data.get("notes"):
                for note in data["notes"]:
                    country_responses.append(f"⚠️ Note: {note}")
            
            if country_responses:
                response_parts.extend(country_responses)
            else:
                response_parts.append(f"✅ Based on my research, Telnyx appears to have coverage in {country}.")
        
        # Always add safety disclaimer
        safety_disclaimer = "\n\n📋 **Please verify this information on Telnyx's official Global Coverage page, as it contains the most up-to-date information. You can search by choosing your country and the number types you're interested in.**"
        
        final_response = {
            "query": query,
            "response": "\n".join(response_parts) + safety_disclaimer,
            "countries_checked": country_list,
            "coverage_details": results,
            "official_reference": "For the most current information, please check the Telnyx Global Coverage page at telnyx.com/global-coverage. ",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Coverage query complete for {len(country_list)} countries")
        return json.dumps(final_response, indent=2)
        
    except Exception as e:
        logger.error(f"Error in global coverage tool: {str(e)}")
        
        error_response = {
            "status": "error",
            "response": "I encountered a technical issue checking coverage information. Please refer to the official Telnyx Global Coverage page in the portal for the most accurate and up-to-date information.",
            "official_reference": "Check the Telnyx Global Coverage page at telnyx.com/global-coverage",
            "error": str(e)
        }
        
        return json.dumps(error_response, indent=2)