import json
import os
import logging
from tqdm import tqdm
from multiprocessing.pool import ThreadPool
import shutil
from collections import defaultdict

class JSONFormatter:
    def __init__(
        self, output_dir, raw_data_dir="raw_data", formatted_dir="formatted", threads=10
    ):
        self.output_dir = output_dir
        self.raw_data_dir = os.path.join(output_dir, raw_data_dir)
        self.formatted_dir = os.path.join(output_dir, formatted_dir)
        self.errors_dir = os.path.join(output_dir, "Error_Formatting")
        self.log_file = os.path.join(output_dir, "formatting.log")
        self.threads = threads
        os.makedirs(self.formatted_dir, exist_ok=True)
        os.makedirs(self.errors_dir, exist_ok=True)

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(self.log_file, encoding="utf-8"),
            ],
        )

    def format_json(self, input):
        def extract_providers_info(data):
            results = []
            providers = data.get("providers", [])

            for provider in providers:
                doctor = provider.get("doctor", {})
                gender = doctor.get("gender") or ""
                name = doctor.get("name", "") or ""
                about = doctor.get("about", "") or ""
                photo_info = doctor.get("primaryPhoto", {}) or {}
                photo_name = photo_info.get("name", "") or ""
                photo_ext = photo_info.get("extension", "") or ""
                npi = doctor.get("npi", "") or ""
                languages = doctor.get("languages", [])  # Ensure it's an empty list if no languages
                # Extract just the names of the languages (if any)
                language_names = list(set(language.get("name", "") for language in languages))  # Access  
                metadata = doctor.get("metadata", {})
                raw_education = metadata.get("education", [])
                education = [
                    f"{e.get('degree', '')}, {e.get('institution', '')}, {e.get('year', '')}"
                    for e in raw_education
                    if e.get('degree') or e.get('institution') or e.get('year')
                ]
                insurances_raw = doctor.get("insurancePlans", [])               
                # Group plans by provider name
                insurance_groups = defaultdict(list)

                for ins in insurances_raw:
                    provider_name = ins.get("provider", {}).get("name", "")
                    plan_name = ins.get("name", "")
                    if provider_name and plan_name:
                        insurance_groups[provider_name].append({"name": plan_name})

                # Convert grouped data into desired format
                insurances = [
                    {"name": provider, "plans": plans}
                    for provider, plans in insurance_groups.items()
                ]
                print(insurances)
                results.append({
                    "doctor_name": name,
                    "gender": gender,
                    "about": about,
                    "photo": f"{photo_name}.{photo_ext}" if photo_name and photo_ext else None,
                    "npi":npi,
                    "languages":language_names,
                    "education":education,
                    "insurances":insurances
                })

            return results
        def extract_personal_statements(data):
            # Get the personal_statements data from the input                   
                return {
                    "about": data.get("description") or ""
                }
                  
        """Formats the input JSON into the desired structure."""
        formatted = {
            "version": "1.0.1",
            "name": input.get("name", "").strip() or "",
            "is_claimed": True,
            "mpc_type": "mpc_cache",
            "specialties": input.get("primarySpecialty", {}).get("name", ""),
            "years_of_experience": 0,
            "rating": input.get("aggregateReviewData", {}).get("averageRating", 0),
            "rating_count": input.get("aggregateReviewData", {}).get("dataPoints", 0),
            "url": "https://www.opencare.com" + input.get("canonicalPath", "").strip() or "",
            "images": ["https:// (or the protocol of the source)", ""],
            "gender": [d['gender'] for d in extract_providers_info(input)],     
            "npi": [d['npi'] for d in extract_providers_info(input)],
            "personal_statements": extract_personal_statements(input),
            "languages": [lang for d in extract_providers_info(input) for lang in d['languages']],  # Flatten the languages list,
            "locations": [
                {
                    "phone_numbers": {
                        "location_phone": {
                            "number": input.get("phone", "").strip() or "",
                            "visible_in_frontend": False,
                        },
                        "spnosor_phone": {
                            "number": "(123) 456-7890",
                            "visible_in_frontend": False,
                        },
                    },
                    "fax": input.get("fax", "") or "",
                    "name": input.get("name", "") or "",
                    "city": input.get("address", {}).get("locality", ""),
                    "state": input.get("address", {}).get("administrative_area_level_1", ""),
                    "zip_code": input.get("address", {}).get("postal_code", ""),
                    "latitude": input.get("latitude"),
                    "longitude": input.get("longitude"),
                    "is_virtual": True,
                    "is_in_person": False,
                    "county": input.get("address", {}).get("administrative_area_level_2", ""),
                    "website": input.get("website"),
                    "medicare_accepted": True,
                    "medicaid_accepted": True,
                    "accepts_new_patients": True,
                    "state_full_name": input.get("address", {}).get("administrative_area_level_1", ""),
                    "state_slug": input.get("address", {}).get("administrative_area_level_1_short", "").lower(),
                    "city_slug": "",
                    "directions_url": "",
                    "nation": "",
                    "street": f'{input.get("address", {}).get("street_number", "")} {input.get("address", {}).get("route", "")}'.strip(),
                    "booking_info": [{}, {}],
                    "external_urls": {
                        "form_urls": [""],
                        "chat_urls": [""],
                        "telemedicine_urls": [""],
                    },
                }
            ],
            "education": [d['education'] for d in extract_providers_info(input)],
            "issues_treated_and_procedures_performed": {
                "issues_treated": ["", ""],
                "procedures_performed": ["", ""],
                "issues_treated_and_procedures_performed": ["", ""],
            },
            "insurances":[d['insurances'] for d in extract_providers_info(input)],
            "licenses": ["", ""],
            "review_summary": {
                "key_1 ex: over_all_summary": "",
                "key_2 ex: positive_summary": "",
                "key_3 ex: negative_summary": "",
                "key_4": "",
            },
            "reviews": [
                {
                    "source": "source number from map as int not string",
                    "rating": 0,
                    "text": "",
                    "date": "yyyy-mm-dd",
                    "reviewer": "",
                },
                {
                    "source": "source number from map as int not string",
                    "rating": 0,
                    "text": "",
                    "date": "",
                    "reviewer": "",
                },
            ],
            "age_ranges": ["", ""],
            "awards_and_publications": {
                "publications": [
                    {"title": "", "url": "", "date": "", "authors": ["", ""]},
                    {},
                ],
                "awards": [{"title": "", "date": ""}, {}],
                "awards_and_publications": ["", ""],
            },
            "hospital_affiliations": [
                {"name": "", "address": "", "city": "", "state": ""}
            ],
            "professional_memberships": ["", ""],
            "payment_descriptions": ["", ""],
        }
        def extract_provider_genders(data):
            genders = []
            providers = data.get("providers", [])

            for provider in providers:
                doctor = provider.get("doctor", {})
                gender = doctor.get("gender") or ""
                genders.append(gender)

            return genders
        # Log missing or invalid fields
        if formatted["name"] == "Unknown Name":
            logging.warning(f"Missing or invalid 'approvedFullName' in input: {input}")
        if formatted["npi"] == "Unknown NPI":
            logging.warning(f"Missing or invalid 'npi' in input: {input}")

        return formatted

    def process_file(self, file, progress_bar):
        """Formats a single JSON file and saves the result."""
        input_path = os.path.join(self.raw_data_dir, file)
        output_path = os.path.join(self.formatted_dir, file)

        # Skip files already processed
        if os.path.exists(output_path):
            logging.info(f"Skipping {file} as it has already been formatted.")
            return

        try:
            with open(input_path, "r", encoding="utf-8") as infile:
                raw_data = json.load(infile)

            # Validate input structure
            if isinstance(raw_data, list):
                # If the input is a list, process each object individually
                logging.warning(
                    f"Input file {file} contains a list of objects. Processing each object."
                )
                formatted_data_list = [self.format_json(item) for item in raw_data]
                formatted_data = formatted_data_list[0] if formatted_data_list else {}
            elif isinstance(raw_data, dict):
                # If the input is a dictionary, process it directly
                formatted_data = self.format_json(raw_data)
            else:
                raise ValueError(
                    f"Unexpected input type: {type(raw_data)}. Expected a dictionary or list."
                )

            # Save the formatted data
            progress_bar.update(1)
            with open(output_path, "w", encoding="utf-8") as outfile:
                json.dump(formatted_data, outfile, indent=2)

            logging.info(f"Successfully formatted: {file}")

        except Exception as e:
            logging.error(f"Error formatting file {file}: {e}")
            error_path = os.path.join(self.errors_dir, file)
            shutil.copy(input_path, error_path)
            logging.info(f"Copied {file} to Error_Formatting directory")

    def process_directory(self):
        """Processes all JSON files in the raw_data directory and saves formatted results."""
        files = os.listdir(self.raw_data_dir)
        with tqdm(total=len(files), desc="Formatting Data") as progress_bar:
            pool = ThreadPool(processes=self.threads)
            pool.map(lambda file: self.process_file(file, progress_bar), files)
            pool.close()
            pool.join()
