import json
import os
import logging
from tqdm import tqdm
from multiprocessing.pool import ThreadPool
import shutil
from collections import defaultdict
from datetime import datetime

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
        def extract_name_info(data):
            # Check if 'aggregateReviewData' is None or missing and handle it gracefully
            name_data = data.get("name")  # Will return None if not found
            if name_data is not None:
                return  name_data
            else:
                return ""
        def extract_personal_statements(data):
            # Check if 'about' is None or missing and handle it gracefully
            about_data = data.get("about")  # Will return None if not found
            if about_data is None:
                return  ""
            else:           
                return {
                    "key_1 : about": about_data
                }
        def extract_specialties_info(data):
            specialties = data.get("specialties") or []
            return [{"name": s.get("name", "")} for s in specialties if s.get("name")]      
        def extract_rating_info(data):
            # Check if 'aggregateReviewData' is None or missing and handle it gracefully
            review_data = data.get("aggregateReviewData")  # Will return None if not found
            if review_data is None:
                return {
                    "rating": 0,
                    "rating_count": 0
                }

            # If the data is present, proceed with extracting values safely
            rating = review_data.get("averageRating", 0)  # Default to 0 if missing
            rating_count = review_data.get("dataPoints", 0)  # Default to 0 if missing

            return {
                "rating": rating,
                "rating_count": rating_count
            }
        def extract_education_info(data):
            metadata = data.get("metadata") or {}
            education_list = metadata.get("education") or []

            formatted_education = []

            for edu in education_list:
                degree = edu.get("degree", "").strip()
                institution = edu.get("institution", "").strip()
                year = edu.get("year", "")

                # Skip if all fields are empty
                if not (degree or institution or year):
                    continue

                formatted_education.append(f"{degree}, {institution}, {year}")

            return formatted_education
        def extract_awards_info(data):
            providers = data.get("providers", [])

            for provider in providers:
                clinic = provider.get("clinic", {})
                if not clinic:
                    continue
                award_data = clinic.get("awardData", {}) or {}    

 
            return award_data
        def extract_payment_methods(data):
            providers = data.get("providers", [])
            clinic_payment_methods = []

            for provider in providers:
                clinic = provider.get("clinic", {})
                if not clinic:
                    continue

                payment_methods = clinic.get("paymentMethods") or []

                clinic_payment_methods.append({
                    "paymentMethods": payment_methods if isinstance(payment_methods, list) else []
                })

            return clinic_payment_methods
        def extract_canonicalPath_info(data):
                # Check if 'aggregateReviewData' is None or missing and handle it gracefully
            canonicalPath_data = data.get("canonicalPath")  # Will return None if not found
            if canonicalPath_data is not None:
                return  canonicalPath_data
            else:
                return ""
        def extract_gender_info(data):
            # Check if 'aggregateReviewData' is None or missing and handle it gracefully
            gender_data = data.get("gender")  # Will return None if not found
            if gender_data is not None:
                return  gender_data
            else:
                return ""
        def extract_npi_info(data):
            # Check if 'aggregateReviewData' is None or missing and handle it gracefully
            npi_data = data.get("npi")  # Will return None if not found
            if npi_data is not None:
                return  npi_data
            else:
                return ""
        def extract_fax_info(data):
            # Check if 'aggregateReviewData' is None or missing and handle it gracefully
            fax_data = data.get("fax")  # Will return None if not found
            if fax_data is not None:
                return  fax_data
            else:
                return ""
        def extract_languages_info(data):
            languages = data.get("languages", [])
            if languages is None:
                return  []
            else:
                return [{"name": s.get("name", "")} for s in languages if s.get("name")]
        def extract_insurances(data):
            insurance_plans = data.get("insurancePlans") or []
            grouped = defaultdict(list)

            for plan in insurance_plans:
                if not plan:
                    continue

                provider = plan.get("provider") or {}
                provider_name = provider.get("name") or ""
                plan_name = plan.get("name") or ""

                provider_name = provider_name.strip()
                plan_name = plan_name.strip()

                if provider_name and plan_name:
                    grouped[provider_name].append({"name": plan_name})

            return [{"name": provider, "plans": plans} for provider, plans in grouped.items()]
        def extract_reviews(data, source_number=1):
            reviews_data = data.get("reviews", [])
            formatted_reviews = []

            for review in reviews_data:
                rating = review.get("overallRating")
                text = review.get("description", "")
                date_raw = review.get("createdAt", "")
                reviewer_first = review.get("patientFirstName", "")
                reviewer_last = review.get("patientLastInitial", "")

                # Skip if rating or text or reviewer is missing
                if rating is None or not text.strip() or not reviewer_first.strip():
                    continue

                # Format date
                date = ""
                if date_raw:
                    try:
                        date = datetime.fromisoformat(date_raw.replace("Z", "+00:00")).date().isoformat()
                    except ValueError:
                        pass

                reviewer = f"{reviewer_first} {reviewer_last}".strip()

                formatted_reviews.append({
                    "source": int(source_number),
                    "rating": rating,
                    "text": text.strip(),
                    "date": date,
                    "reviewer": reviewer,
                })

            return formatted_reviews
        def extract_providers_info(data):
            providers = data.get("providers", [])
            locations = []

            for provider in providers:
                clinic = provider.get("clinic", {})
                if not clinic:
                    continue
                def format_phone_number(phone: str) -> str:
                    if phone and phone.startswith("+1") and len(phone) == 12:
                        area_code = phone[2:5]
                        first_part = phone[5:8]
                        second_part = phone[8:]
                        return f"({area_code}) {first_part}-{second_part}"
                    return phone  # return as-is if null, empty, or invalid format
       
                address = clinic.get("address", {}) or {}
                fax = clinic.get("fax", "")
                name = clinic.get("name", "").strip()
                phone = clinic.get("phone", "")
                formatted_phone = format_phone_number(phone)
                website = clinic.get("website", "")
                latitude = clinic.get("latitude", "")
                longitude = clinic.get("longitude", "")
                instant_book = clinic.get("instantBookConfiguration", {})

                # Extract booking info from rooms
                booking_info = []
                for room in instant_book.get("rooms", []):
                    provider_id = room.get("providerId")
                    for mapping in room.get("mappings", []):
                        booking_info.append({
                            "provider_id": provider_id,
                            "room_id": mapping.get("roomId"),
                            "appointment_duration": mapping.get("appointmentDuration"),
                            "sync_strategy": room.get("syncStrategy"),
                            "double_booking_enabled": room.get("doubleBookingEnabled"),
                            "mappings_order_reversible": room.get("mappingsOrderReversible")
                        })

                location = {
                    "phone_numbers": {
                        "location_phone": {
                            "number": formatted_phone,
                            "visible_in_frontend": True,
                        }
                      
                    },
                    "fax": fax,
                    "name": name,
                    "city": address.get("locality", ""),
                    "state": address.get("administrative_area_level_1_short", ""),
                    "zip_code": address.get("postal_code", ""),
                    "latitude": latitude,
                    "longitude": longitude,
                    "is_virtual": False,
                    "is_in_person": True,
                    "county": address.get("administrative_area_level_2", ""),
                    "website": website,
                    "medicare_accepted": True,
                    "medicaid_accepted": True,
                    "accepts_new_patients": True,
                    "state_full_name": address.get("administrative_area_level_1", ""),
                    "state_slug": "",  # Optional slugify(state)
                    "city_slug": "",   # Optional slugify(city)
                    "directions_url": "",  # Optional Google Maps link
                    "nation": address.get("country", ""),
                    "street": f"{address.get('street_number', '')} {address.get('route', '')}".strip(),
                    "booking_info": booking_info,
                    "external_urls": {
                        "form_urls": [""],
                        "chat_urls": [""],
                        "telemedicine_urls": [""],
                    },
                }

                locations.append(location)

            return locations
        def extract_services_info(data):
            providers = data.get("providers", [])
            services = []

            for provider in providers:
                offered_services = provider.get("offeredServices", [])
                for item in offered_services:
                    service = item.get("service")
                    if service and isinstance(service, dict):
                        name = service.get("name")
                        if name:
                            # Remove forward slashes and strip whitespace
                            cleaned_name = name.replace("/", "").strip()
                            services.append(cleaned_name)

            return services          
        def extract_claimed_at_info(data):
            providers = data.get("providers", [])

            for provider in providers:
                clinic = provider.get("clinic", {})
                if not clinic:
                    continue

                claimed_at = clinic.get("claimedAt")

                is_claimed = bool(claimed_at)  # True if claimed_at is not None or empty
                 

            return is_claimed
        def extract_images(data):
            base_url = "https://images.opencare.com/"
            providers = data.get("providers", [])
            clinics_images = []

            for provider in providers:
                clinic = provider.get("clinic", {})
                if not clinic:
                    continue

                images = []

                # Handle 'primaryPhoto'
                primary = data.get("primaryPhoto")
                if primary:
                    name = primary.get("name")
                    ext = primary.get("extension")
                    if name and ext:
                        images.append(f"{base_url}{name}-200x200.{ext}")
                
                photos = data.get("photos", [])
                for photo in photos:
                    name = photo.get("name")
                    ext = photo.get("extension")
                    if name and ext:
                        images.append(f"{base_url}{name}-700x700.{ext}")

                # Handle 'photos'
                photos = clinic.get("photos", [])
                for photo in photos:
                    name = photo.get("name")
                    ext = photo.get("extension")
                    if name and ext:
                        images.append(f"{base_url}{name}-700x700.{ext}")

                clinics_images.append({
                    "images": images
                })

            return clinics_images
        name_info  = extract_name_info(input)
        rating_info = extract_rating_info(input)
        education_data_info = extract_education_info(input)
        canonicalPath_data_info = extract_canonicalPath_info(input)
        gender_data_info = extract_gender_info(input)
        npi_data_info = extract_npi_info(input)
        personal_statements_data_info = extract_personal_statements(input)
        fax_data_info = extract_fax_info(input)
        insurances = extract_insurances(input)
        reviews = extract_reviews(input)
        locations = extract_providers_info(input)
        clamied_at= extract_claimed_at_info(input)
        images = extract_images(input)
        awards = extract_awards_info(input)
        payments = extract_payment_methods(input)
        services = extract_services_info(input)
        def clean_data(value):
            """Recursively remove keys with empty, null, or default-empty values."""
            if isinstance(value, dict):
                cleaned = {
                    k: clean_data(v) for k, v in value.items()
                    if v not in [None, "", [], {}, ["", ""], {"": ""},0]
                    and not (isinstance(v, (list, dict)) and clean_data(v) in [[], {}])
                }
                return cleaned
            elif isinstance(value, list):
                cleaned_list = [clean_data(v) for v in value if v not in [None, "", {}, []]]
                return [item for item in cleaned_list if item not in [None, "", {}, [], [""]]]
            return value
        """Formats the input JSON into the desired structure."""
        formatted = {
            "version": "1.0.1",
            "name": name_info,
            "is_claimed": clamied_at,
            "mpc_type": "mpc_cache",
            "specialties": [d['name'] for d in extract_specialties_info(input)] or [],
            "years_of_experience": input.get("yearsExperience", "") or 0,
            "rating":rating_info["rating"] ,
            "rating_count": rating_info["rating_count"],
            "url": "https://www.opencare.com" + canonicalPath_data_info ,
            "images": images,
            "gender":gender_data_info ,     
            "npi":npi_data_info ,
            "personal_statements": personal_statements_data_info,
            "languages": [d['name'] for d in extract_languages_info(input)] or [],  # Flatten the languages list,
            "locations":  locations,            
            "education": education_data_info,
            "offerdservices":services,
            "issues_treated_and_procedures_performed": {
                "issues_treated": ["", ""],
                "procedures_performed": ["", ""],
                "issues_treated_and_procedures_performed": ["", ""],
            },
            "insurances":insurances,
            "licenses": ["", ""],
            "review_summary": {
                "key_1 ex: over_all_summary": "",
                "key_2 ex: positive_summary": "",
                "key_3 ex: negative_summary": "",
                "key_4": "",
            },
            "reviews":  reviews,
            "age_ranges": ["", ""],
            "awards_and_publications": {
                "publications": [
                    {"title": "", "url": "", "date": "", "authors": ["", ""]},
                    {},
                ],
                "awards": awards,
                "awards_and_publications": [awards, ""],
            },
            "hospital_affiliations": [
                {"name": "", "address": "", "city": "", "state": ""}
            ],
            "professional_memberships": ["", ""],
            "payment_descriptions": payments,
        }
        # Remove keys with empty values
        formatted_cleaned = clean_data(formatted)

        # Log missing or invalid fields
        if formatted_cleaned["name"] == "Unknown Name":
            logging.warning(f"Missing or invalid 'approvedFullName' in input: {input}")
        if not formatted_cleaned.get("npi") or formatted_cleaned.get("npi") == "Unknown NPI":
            logging.warning(f"Missing or invalid 'npi' in input: {input}")
        return formatted_cleaned

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
